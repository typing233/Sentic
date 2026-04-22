from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db
from app.models.models import User, Project
from app.models.schemas import (
    DashboardCreate, DashboardUpdate, DashboardResponse,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidgetResponse,
    UserRole, ErrorResponse
)
from app.services.auth_service import get_current_user_required, auth_checker
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.post("/", response_model=DashboardResponse, responses={403: {"model": ErrorResponse}})
async def create_dashboard(
    dashboard_data: DashboardCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == dashboard_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    auth_checker.check_project_permission(
        dashboard_data.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
    )
    
    dashboard = dashboard_service.create_dashboard(db, dashboard_data, user.id)
    
    return dashboard_service.to_dashboard_response(dashboard)


@router.get("/", response_model=List[DashboardResponse])
async def list_dashboards(
    project_id: Optional[str] = None,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    dashboards = dashboard_service.list_dashboards(db, project_id, user.id)
    
    return [dashboard_service.to_dashboard_response(d) for d in dashboards]


@router.get("/{dashboard_id}", response_model=DashboardResponse, responses={404: {"model": ErrorResponse}})
async def get_dashboard(
    dashboard_id: str,
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
    
    return dashboard_service.to_dashboard_response(dashboard)


@router.put("/{dashboard_id}", response_model=DashboardResponse, responses={404: {"model": ErrorResponse}})
async def update_dashboard(
    dashboard_id: str,
    dashboard_data: DashboardUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    dashboard = dashboard_service.get_dashboard(db, dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="看板不存在")
    
    auth_checker.check_project_permission(
        dashboard.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
    )
    
    updated = dashboard_service.update_dashboard(db, dashboard_id, dashboard_data)
    
    return dashboard_service.to_dashboard_response(updated)


@router.delete("/{dashboard_id}", responses={404: {"model": ErrorResponse}})
async def delete_dashboard(
    dashboard_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    dashboard = dashboard_service.get_dashboard(db, dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="看板不存在")
    
    auth_checker.check_project_permission(
        dashboard.project_id, user, db, [UserRole.ADMIN]
    )
    
    success = dashboard_service.delete_dashboard(db, dashboard_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    return {"message": "看板已删除", "id": dashboard_id}


@router.post("/{dashboard_id}/widgets", response_model=DashboardWidgetResponse, responses={404: {"model": ErrorResponse}})
async def add_widget(
    dashboard_id: str,
    widget_data: DashboardWidgetCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    dashboard = dashboard_service.get_dashboard(db, dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="看板不存在")
    
    auth_checker.check_project_permission(
        dashboard.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
    )
    
    widget = dashboard_service.add_widget(db, dashboard_id, widget_data)
    
    return dashboard_service.to_widget_response(widget)


@router.put("/widgets/{widget_id}", response_model=DashboardWidgetResponse, responses={404: {"model": ErrorResponse}})
async def update_widget(
    widget_id: str,
    widget_data: DashboardWidgetUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    widget = dashboard_service.get_widget(db, widget_id)
    
    if not widget:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    dashboard = dashboard_service.get_dashboard(db, widget.dashboard_id)
    
    auth_checker.check_project_permission(
        dashboard.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
    )
    
    updated = dashboard_service.update_widget(db, widget_id, widget_data)
    
    return dashboard_service.to_widget_response(updated)


@router.delete("/widgets/{widget_id}", responses={404: {"model": ErrorResponse}})
async def delete_widget(
    widget_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    widget = dashboard_service.get_widget(db, widget_id)
    
    if not widget:
        raise HTTPException(status_code=404, detail="组件不存在")
    
    dashboard = dashboard_service.get_dashboard(db, widget.dashboard_id)
    
    auth_checker.check_project_permission(
        dashboard.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
    )
    
    success = dashboard_service.delete_widget(db, widget_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    return {"message": "组件已删除", "id": widget_id}


@router.post("/{dashboard_id}/reorder", responses={404: {"model": ErrorResponse}})
async def reorder_widgets(
    dashboard_id: str,
    widget_order: list[str],
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    dashboard = dashboard_service.get_dashboard(db, dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="看板不存在")
    
    auth_checker.check_project_permission(
        dashboard.project_id, user, db, [UserRole.EDITOR, UserRole.ADMIN]
    )
    
    success = dashboard_service.reorder_widgets(db, dashboard_id, widget_order)
    
    return {"message": "组件已重新排序", "success": success}
