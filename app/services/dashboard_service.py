from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.models.models import Dashboard, DashboardWidget
from app.models.schemas import (
    DashboardCreate, DashboardUpdate, DashboardResponse,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidgetResponse,
    UserRole
)


class DashboardService:
    def create_dashboard(
        self,
        db: Session,
        dashboard_data: DashboardCreate,
        owner_id: str
    ) -> Dashboard:
        dashboard = Dashboard(
            name=dashboard_data.name,
            description=dashboard_data.description,
            project_id=dashboard_data.project_id,
            owner_id=owner_id,
            is_public=dashboard_data.is_public,
            layout_config=json.dumps(dashboard_data.layout_config) if dashboard_data.layout_config else None
        )
        
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        
        return dashboard
    
    def get_dashboard(self, db: Session, dashboard_id: str) -> Optional[Dashboard]:
        return db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    
    def list_dashboards(
        self,
        db: Session,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dashboard]:
        query = db.query(Dashboard)
        
        if project_id:
            query = query.filter(Dashboard.project_id == project_id)
        
        if user_id:
            query = query.filter(
                (Dashboard.owner_id == user_id) | (Dashboard.is_public == True)
            )
        
        return query.order_by(Dashboard.updated_at.desc()).all()
    
    def update_dashboard(
        self,
        db: Session,
        dashboard_id: str,
        dashboard_data: DashboardUpdate
    ) -> Optional[Dashboard]:
        dashboard = self.get_dashboard(db, dashboard_id)
        
        if not dashboard:
            return None
        
        if dashboard_data.name is not None:
            dashboard.name = dashboard_data.name
        if dashboard_data.description is not None:
            dashboard.description = dashboard_data.description
        if dashboard_data.is_public is not None:
            dashboard.is_public = dashboard_data.is_public
        if dashboard_data.layout_config is not None:
            dashboard.layout_config = json.dumps(dashboard_data.layout_config)
        
        db.commit()
        db.refresh(dashboard)
        
        return dashboard
    
    def delete_dashboard(self, db: Session, dashboard_id: str) -> bool:
        dashboard = self.get_dashboard(db, dashboard_id)
        
        if not dashboard:
            return False
        
        db.delete(dashboard)
        db.commit()
        
        return True
    
    def add_widget(
        self,
        db: Session,
        dashboard_id: str,
        widget_data: DashboardWidgetCreate
    ) -> DashboardWidget:
        max_position = db.query(DashboardWidget.position).filter(
            DashboardWidget.dashboard_id == dashboard_id
        ).order_by(DashboardWidget.position.desc()).first()
        
        next_position = (max_position[0] + 1) if max_position else 0
        
        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            title=widget_data.title,
            widget_type=widget_data.widget_type,
            position=widget_data.position if widget_data.position is not None else next_position,
            width=widget_data.width,
            height=widget_data.height,
            data_source_id=widget_data.data_source_id,
            query=widget_data.query,
            chart_config=json.dumps(widget_data.chart_config) if widget_data.chart_config else None,
            chart_type=widget_data.chart_type,
            insight_id=widget_data.insight_id,
            content=widget_data.content
        )
        
        db.add(widget)
        db.commit()
        db.refresh(widget)
        
        return widget
    
    def get_widget(self, db: Session, widget_id: str) -> Optional[DashboardWidget]:
        return db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    
    def update_widget(
        self,
        db: Session,
        widget_id: str,
        widget_data: DashboardWidgetUpdate
    ) -> Optional[DashboardWidget]:
        widget = self.get_widget(db, widget_id)
        
        if not widget:
            return None
        
        if widget_data.title is not None:
            widget.title = widget_data.title
        if widget_data.position is not None:
            widget.position = widget_data.position
        if widget_data.width is not None:
            widget.width = widget_data.width
        if widget_data.height is not None:
            widget.height = widget_data.height
        if widget_data.chart_config is not None:
            widget.chart_config = json.dumps(widget_data.chart_config)
        if widget_data.content is not None:
            widget.content = widget_data.content
        
        db.commit()
        db.refresh(widget)
        
        return widget
    
    def delete_widget(self, db: Session, widget_id: str) -> bool:
        widget = self.get_widget(db, widget_id)
        
        if not widget:
            return False
        
        db.delete(widget)
        db.commit()
        
        return True
    
    def reorder_widgets(
        self,
        db: Session,
        dashboard_id: str,
        widget_order: List[str]
    ) -> bool:
        for index, widget_id in enumerate(widget_order):
            widget = self.get_widget(db, widget_id)
            if widget and widget.dashboard_id == dashboard_id:
                widget.position = index
        
        db.commit()
        return True
    
    def to_dashboard_response(self, dashboard: Dashboard) -> DashboardResponse:
        layout_config = None
        if dashboard.layout_config:
            try:
                layout_config = json.loads(dashboard.layout_config)
            except:
                layout_config = None
        
        widgets = []
        for widget in sorted(dashboard.widgets, key=lambda w: w.position):
            widgets.append(self.to_widget_response(widget))
        
        return DashboardResponse(
            id=dashboard.id,
            name=dashboard.name,
            description=dashboard.description,
            project_id=dashboard.project_id,
            owner_id=dashboard.owner_id,
            is_public=dashboard.is_public,
            layout_config=layout_config,
            widgets=widgets,
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at
        )
    
    def to_widget_response(self, widget: DashboardWidget) -> DashboardWidgetResponse:
        chart_config = None
        if widget.chart_config:
            try:
                chart_config = json.loads(widget.chart_config)
            except:
                chart_config = None
        
        return DashboardWidgetResponse(
            id=widget.id,
            dashboard_id=widget.dashboard_id,
            title=widget.title,
            widget_type=widget.widget_type,
            position=widget.position,
            width=widget.width,
            height=widget.height,
            data_source_id=widget.data_source_id,
            query=widget.query,
            chart_config=chart_config,
            chart_type=widget.chart_type,
            insight_id=widget.insight_id,
            content=widget.content,
            created_at=widget.created_at,
            updated_at=widget.updated_at
        )


dashboard_service = DashboardService()
