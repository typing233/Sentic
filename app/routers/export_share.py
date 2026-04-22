from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import io
import json

from app.models.database import get_db
from app.models.models import User, Project
from app.models.schemas import (
    ExportRequest, ShareLinkCreate, ShareLinkResponse,
    UserRole, ErrorResponse
)
from app.services.auth_service import get_current_user_required, auth_checker
from app.services.export_service import export_service, share_service
from app.services.dashboard_service import dashboard_service
from app.services.data_source_service import data_source_service
from config import settings

router = APIRouter()


@router.post("/export/chart")
async def export_chart(
    export_request: ExportRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    export_format = export_request.format.lower()
    
    if export_format == 'png':
        if not export_request.chart_config:
            raise HTTPException(status_code=400, detail="缺少图表配置")
        
        img_bytes = export_service.export_chart_to_png(
            export_request.chart_config,
            export_request.width,
            export_request.height
        )
        
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=chart.png"}
        )
    
    elif export_format == 'pdf':
        if not export_request.chart_config:
            raise HTTPException(status_code=400, detail="缺少图表配置")
        
        pdf_bytes = export_service.export_chart_to_pdf(
            export_request.chart_config,
            title="Chart Export"
        )
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=chart.pdf"}
        )
    
    elif export_format == 'csv':
        if not export_request.data_source_id:
            raise HTTPException(status_code=400, detail="缺少数据源ID")
        
        try:
            if export_request.query:
                df = data_source_service.execute_query(
                    export_request.data_source_id,
                    export_request.query
                )
            else:
                df = data_source_service.get_dataframe(export_request.data_source_id)
            
            csv_content = df.to_csv(index=False, encoding='utf-8')
            
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=data.csv"}
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")


@router.get("/export/dashboard/{dashboard_id}")
async def export_dashboard(
    dashboard_id: str,
    format: str = "pdf",
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    dashboard = dashboard_service.get_dashboard(db, dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="看板不存在")
    
    if not dashboard.is_public:
        auth_checker.check_project_permission(
            dashboard.project_id, user, db, [UserRole.VIEWER, UserRole.EDITOR, UserRole.ADMIN]
        )
    
    export_format = format.lower()
    
    if export_format == 'pdf':
        pdf_bytes = export_service.export_dashboard_to_pdf(dashboard, db)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=dashboard_{dashboard_id}.pdf"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")


@router.post("/share", response_model=ShareLinkResponse, responses={404: {"model": ErrorResponse}})
async def create_share_link(
    share_data: ShareLinkCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    if share_data.share_type == "dashboard":
        dashboard = dashboard_service.get_dashboard(db, share_data.target_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="看板不存在")
        
        auth_checker.check_project_permission(
            dashboard.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
        )
    
    share_link = share_service.create_share_link(
        db,
        share_data.share_type,
        share_data.target_id,
        user.id,
        share_data.expires_in_hours
    )
    
    share_url = f"{settings.host}:{settings.port}/share/{share_link.token}"
    
    return ShareLinkResponse(
        id=share_link.id,
        token=share_link.token,
        share_type=share_link.share_type,
        target_id=share_link.target_id,
        share_url=share_url,
        expires_at=share_link.expires_at,
        is_active=share_link.is_active,
        view_count=share_link.view_count,
        created_at=share_link.created_at
    )


@router.get("/share/{token}")
async def access_shared_content(
    token: str,
    db: Session = Depends(get_db)
):
    share_link = share_service.get_share_link(db, token)
    
    if not share_link:
        raise HTTPException(status_code=404, detail="分享链接不存在或已过期")
    
    if share_link.share_type == "dashboard":
        dashboard = dashboard_service.get_dashboard(db, share_link.target_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="看板不存在")
        
        return dashboard_service.to_dashboard_response(dashboard)
    
    elif share_link.share_type == "chart":
        return {
            "share_type": "chart",
            "target_id": share_link.target_id,
            "message": "图表分享功能需要配合具体的图表ID使用"
        }
    
    elif share_link.share_type == "data_source":
        return {
            "share_type": "data_source",
            "target_id": share_link.target_id,
            "message": "数据源分享功能需要配合具体的数据源ID使用"
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的分享类型: {share_link.share_type}")


@router.delete("/share/{share_id}")
async def deactivate_share_link(
    share_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    success = share_service.deactivate_share_link(db, share_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="分享链接不存在或无权限")
    
    return {"message": "分享链接已失效", "id": share_id}


@router.get("/shares", response_model=List[ShareLinkResponse])
async def list_share_links(
    target_id: Optional[str] = None,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    share_links = share_service.list_share_links(db, user.id, target_id)
    
    result = []
    for sl in share_links:
        share_url = f"{settings.host}:{settings.port}/share/{sl.token}"
        result.append(ShareLinkResponse(
            id=sl.id,
            token=sl.token,
            share_type=sl.share_type,
            target_id=sl.target_id,
            share_url=share_url,
            expires_at=sl.expires_at,
            is_active=sl.is_active,
            view_count=sl.view_count,
            created_at=sl.created_at
        ))
    
    return result
