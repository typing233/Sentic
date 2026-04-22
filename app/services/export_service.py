import io
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.io import to_image, write_image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from sqlalchemy.orm import Session
from PIL import Image as PILImage

from app.models.models import ShareLink, Dashboard, DashboardWidget
from app.models.schemas import ShareType
from app.services.data_source_service import data_source_service
from app.services.dashboard_service import dashboard_service
from config import settings


class ExportService:
    def export_chart_to_png(
        self,
        chart_config: Dict[str, Any],
        width: int = 1200,
        height: int = 800
    ) -> bytes:
        fig = self._create_plotly_figure(chart_config)
        fig.update_layout(width=width, height=height)
        
        img_bytes = to_image(fig, format='png', engine='kaleido')
        return img_bytes
    
    def export_chart_to_pdf(
        self,
        chart_config: Dict[str, Any],
        title: str = "Chart",
        width: int = 1200,
        height: int = 800
    ) -> bytes:
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=20
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        img_bytes = self.export_chart_to_png(chart_config, width, height)
        img_buffer = io.BytesIO(img_bytes)
        
        pil_img = PILImage.open(img_buffer)
        img_width, img_height = pil_img.size
        aspect_ratio = img_height / img_width
        
        pdf_width = 7 * inch
        pdf_height = pdf_width * aspect_ratio
        
        img_buffer.seek(0)
        img = Image(img_buffer, width=pdf_width, height=pdf_height)
        story.append(img)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_data_to_csv(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        df = pd.DataFrame(data)
        if columns:
            df = df[columns]
        return df.to_csv(index=False, encoding='utf-8')
    
    def export_dashboard_to_pdf(
        self,
        dashboard: Dashboard,
        db: Session
    ) -> bytes:
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=10
        )
        
        story.append(Paragraph(dashboard.name, title_style))
        
        if dashboard.description:
            desc_style = ParagraphStyle(
                'Description',
                parent=styles['BodyText'],
                fontSize=12,
                textColor=colors.gray
            )
            story.append(Paragraph(dashboard.description, desc_style))
        
        story.append(Spacer(1, 20))
        
        widgets = sorted(dashboard.widgets, key=lambda w: w.position)
        
        for widget in widgets:
            widget_title = widget.title or f"Widget {widget.id[:8]}"
            story.append(Paragraph(widget_title, styles['Heading2']))
            story.append(Spacer(1, 10))
            
            if widget.widget_type == 'chart' and widget.chart_config:
                try:
                    chart_config = json.loads(widget.chart_config)
                    img_bytes = self.export_chart_to_png(chart_config, 800, 500)
                    img_buffer = io.BytesIO(img_bytes)
                    
                    pil_img = PILImage.open(img_buffer)
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_height / img_width
                    
                    pdf_width = 6 * inch
                    pdf_height = pdf_width * aspect_ratio
                    
                    img_buffer.seek(0)
                    img = Image(img_buffer, width=pdf_width, height=pdf_height)
                    story.append(img)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    story.append(Paragraph(f"图表渲染失败: {str(e)}", styles['BodyText']))
                    story.append(Spacer(1, 10))
            
            elif widget.widget_type == 'text' and widget.content:
                content_style = ParagraphStyle(
                    'WidgetContent',
                    parent=styles['BodyText'],
                    fontSize=11,
                    leftIndent=10
                )
                story.append(Paragraph(widget.content, content_style))
                story.append(Spacer(1, 15))
            
            elif widget.widget_type == 'table' and widget.query and widget.data_source_id:
                try:
                    result_df = data_source_service.execute_query(
                        widget.data_source_id, widget.query
                    )
                    
                    table_data = [list(result_df.columns)]
                    for _, row in result_df.head(20).iterrows():
                        table_data.append([str(cell) for cell in row])
                    
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 15))
                    
                    if len(result_df) > 20:
                        story.append(Paragraph(f"显示前20行，共{len(result_df)}行", styles['Italic']))
                        story.append(Spacer(1, 10))
                except Exception as e:
                    story.append(Paragraph(f"表格数据加载失败: {str(e)}", styles['BodyText']))
                    story.append(Spacer(1, 10))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Italic'],
            fontSize=10,
            textColor=colors.gray,
            alignment=1
        )
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_plotly_figure(self, chart_config: Dict[str, Any]) -> go.Figure:
        chart_type = chart_config.get('chart_type', 'bar')
        data = chart_config.get('data', {})
        config = chart_config.get('config', {})
        
        fig = go.Figure()
        
        if chart_type == 'bar':
            labels = data.get('labels', [])
            datasets = data.get('datasets', [])
            
            for dataset in datasets:
                fig.add_trace(go.Bar(
                    x=labels,
                    y=dataset.get('data', []),
                    name=dataset.get('label', 'Series')
                ))
        
        elif chart_type == 'line':
            labels = data.get('labels', [])
            datasets = data.get('datasets', [])
            
            for dataset in datasets:
                fig.add_trace(go.Scatter(
                    x=labels,
                    y=dataset.get('data', []),
                    mode='lines+markers',
                    name=dataset.get('label', 'Series')
                ))
        
        elif chart_type == 'pie':
            labels = data.get('labels', [])
            values = data.get('values', [])
            
            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                textinfo='label+percent'
            ))
        
        elif chart_type == 'scatter':
            datasets = data.get('datasets', [])
            
            for dataset in datasets:
                points = dataset.get('data', [])
                x_vals = [p.get('x', p[0] if isinstance(p, list) else 0) for p in points]
                y_vals = [p.get('y', p[1] if isinstance(p, list) else 0) for p in points]
                
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='markers',
                    name=dataset.get('label', 'Series')
                ))
        
        elif chart_type == 'histogram':
            labels = data.get('labels', [])
            datasets = data.get('datasets', [])
            
            for dataset in datasets:
                fig.add_trace(go.Bar(
                    x=labels,
                    y=dataset.get('data', []),
                    name=dataset.get('label', 'Series')
                ))
        
        fig.update_layout(
            title=config.get('title', 'Chart'),
            xaxis_title=config.get('x_axis', 'X'),
            yaxis_title=config.get('y_axis', 'Y'),
            showlegend=True
        )
        
        return fig


class ShareService:
    def create_share_link(
        self,
        db: Session,
        share_type: str,
        target_id: str,
        created_by: str,
        expires_in_hours: Optional[int] = None
    ) -> ShareLink:
        token = self._generate_token()
        
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        share_link = ShareLink(
            token=token,
            share_type=share_type,
            target_id=target_id,
            dashboard_id=target_id if share_type == ShareType.DASHBOARD else None,
            created_by=created_by,
            expires_at=expires_at,
            is_active=True,
            view_count=0
        )
        
        db.add(share_link)
        db.commit()
        db.refresh(share_link)
        
        return share_link
    
    def get_share_link(
        self,
        db: Session,
        token: str
    ) -> Optional[ShareLink]:
        share_link = db.query(ShareLink).filter(
            ShareLink.token == token,
            ShareLink.is_active == True
        ).first()
        
        if not share_link:
            return None
        
        if share_link.expires_at and share_link.expires_at < datetime.utcnow():
            share_link.is_active = False
            db.commit()
            return None
        
        share_link.view_count += 1
        db.commit()
        
        return share_link
    
    def deactivate_share_link(
        self,
        db: Session,
        share_id: str,
        user_id: str
    ) -> bool:
        share_link = db.query(ShareLink).filter(
            ShareLink.id == share_id,
            ShareLink.created_by == user_id
        ).first()
        
        if not share_link:
            return False
        
        share_link.is_active = False
        db.commit()
        
        return True
    
    def list_share_links(
        self,
        db: Session,
        user_id: str,
        target_id: Optional[str] = None
    ) -> List[ShareLink]:
        query = db.query(ShareLink).filter(ShareLink.created_by == user_id)
        
        if target_id:
            query = query.filter(ShareLink.target_id == target_id)
        
        return query.order_by(ShareLink.created_at.desc()).all()
    
    def _generate_token(self) -> str:
        return str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', '')[:16]


export_service = ExportService()
share_service = ShareService()
