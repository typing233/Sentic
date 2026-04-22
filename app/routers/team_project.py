from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
import json

from app.models.database import get_db
from app.models.models import User, Team, Project, team_members, project_members
from app.models.schemas import (
    TeamCreate, TeamResponse, ProjectCreate, ProjectResponse,
    ProjectMemberAdd, ProjectMemberResponse, UserRole, ErrorResponse
)
from app.services.auth_service import get_current_user_required

router = APIRouter()


@router.post("/teams", response_model=TeamResponse, responses={400: {"model": ErrorResponse}})
async def create_team(
    team_data: TeamCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    team = Team(
        name=team_data.name,
        description=team_data.description,
        owner_id=user.id
    )
    
    db.add(team)
    db.flush()
    
    stmt = text("""
        INSERT INTO team_members (team_id, user_id, role, joined_at)
        VALUES (:team_id, :user_id, :role, :joined_at)
    """)
    db.execute(stmt, {
        "team_id": team.id,
        "user_id": user.id,
        "role": UserRole.ADMIN,
        "joined_at": datetime.utcnow()
    })
    
    db.commit()
    db.refresh(team)
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        created_at=team.created_at,
        member_count=1
    )


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    stmt = text("""
        SELECT t.*, 
               (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) as member_count
        FROM teams t
        JOIN team_members tm ON t.id = tm.team_id
        WHERE tm.user_id = :user_id
    """)
    result = db.execute(stmt, {"user_id": user.id}).fetchall()
    
    teams = []
    for row in result:
        teams.append(TeamResponse(
            id=row.id,
            name=row.name,
            description=row.description,
            owner_id=row.owner_id,
            created_at=row.created_at,
            member_count=row.member_count
        ))
    
    return teams


@router.get("/teams/{team_id}", response_model=TeamResponse, responses={404: {"model": ErrorResponse}})
async def get_team(
    team_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    stmt = text("""
        SELECT t.*, 
               (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) as member_count
        FROM teams t
        JOIN team_members tm ON t.id = tm.team_id
        WHERE t.id = :team_id AND tm.user_id = :user_id
    """)
    result = db.execute(stmt, {"team_id": team_id, "user_id": user.id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="团队不存在或无权限访问")
    
    return TeamResponse(
        id=result.id,
        name=result.name,
        description=result.description,
        owner_id=result.owner_id,
        created_at=result.created_at,
        member_count=result.member_count
    )


@router.post("/projects", response_model=ProjectResponse, responses={400: {"model": ErrorResponse}})
async def create_project(
    project_data: ProjectCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    if project_data.team_id:
        stmt = text("""
            SELECT * FROM team_members 
            WHERE team_id = :team_id AND user_id = :user_id
        """)
        team_member = db.execute(stmt, {
            "team_id": project_data.team_id,
            "user_id": user.id
        }).fetchone()
        
        if not team_member:
            raise HTTPException(status_code=403, detail="不是该团队成员，无法创建项目")
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        team_id=project_data.team_id,
        owner_id=user.id,
        is_public=project_data.is_public
    )
    
    db.add(project)
    db.flush()
    
    stmt = text("""
        INSERT INTO project_members (project_id, user_id, role, joined_at)
        VALUES (:project_id, :user_id, :role, :joined_at)
    """)
    db.execute(stmt, {
        "project_id": project.id,
        "user_id": user.id,
        "role": UserRole.ADMIN,
        "joined_at": datetime.utcnow()
    })
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        team_id=project.team_id,
        owner_id=project.owner_id,
        is_public=project.is_public,
        created_at=project.created_at
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    include_public: bool = False,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    query = """
        SELECT p.* FROM projects p
        LEFT JOIN project_members pm ON p.id = pm.project_id
        WHERE pm.user_id = :user_id
    """
    params = {"user_id": user.id}
    
    if include_public:
        query += " OR p.is_public = TRUE"
    
    stmt = text(query)
    result = db.execute(stmt, params).fetchall()
    
    projects = []
    for row in result:
        projects.append(ProjectResponse(
            id=row.id,
            name=row.name,
            description=row.description,
            team_id=row.team_id,
            owner_id=row.owner_id,
            is_public=row.is_public,
            created_at=row.created_at
        ))
    
    return projects


@router.get("/projects/{project_id}", response_model=ProjectResponse, responses={404: {"model": ErrorResponse}})
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    stmt = text("""
        SELECT p.* FROM projects p
        LEFT JOIN project_members pm ON p.id = pm.project_id
        WHERE p.id = :project_id 
        AND (pm.user_id = :user_id OR p.is_public = TRUE)
    """)
    result = db.execute(stmt, {"project_id": project_id, "user_id": user.id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="项目不存在或无权限访问")
    
    return ProjectResponse(
        id=result.id,
        name=result.name,
        description=result.description,
        team_id=result.team_id,
        owner_id=result.owner_id,
        is_public=result.is_public,
        created_at=result.created_at
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse, responses={404: {"model": ErrorResponse}})
async def update_project(
    project_id: str,
    project_data: ProjectCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.owner_id != user.id:
        stmt = text("""
            SELECT role FROM project_members 
            WHERE project_id = :project_id AND user_id = :user_id
        """)
        result = db.execute(stmt, {"project_id": project_id, "user_id": user.id}).fetchone()
        
        if not result or result[0] != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="只有项目管理员可以编辑项目")
    
    project.name = project_data.name
    project.description = project_data.description
    project.is_public = project_data.is_public
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        team_id=project.team_id,
        owner_id=project.owner_id,
        is_public=project.is_public,
        created_at=project.created_at
    )


@router.delete("/projects/{project_id}", responses={404: {"model": ErrorResponse}})
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.owner_id != user.id:
        stmt = text("""
            SELECT role FROM project_members 
            WHERE project_id = :project_id AND user_id = :user_id
        """)
        result = db.execute(stmt, {"project_id": project_id, "user_id": user.id}).fetchone()
        
        if not result or result[0] != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="只有项目管理员可以删除项目")
    
    db.delete(project)
    db.commit()
    
    return {"message": "项目已删除", "id": project_id}


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: str,
    member_data: ProjectMemberAdd,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    stmt = text("""
        SELECT role FROM project_members 
        WHERE project_id = :project_id AND user_id = :user_id
    """)
    result = db.execute(stmt, {"project_id": project_id, "user_id": user.id}).fetchone()
    
    if not result or result[0] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有项目管理员可以添加成员")
    
    new_user = db.query(User).filter(User.id == member_data.user_id).first()
    if not new_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    existing_stmt = text("""
        SELECT * FROM project_members 
        WHERE project_id = :project_id AND user_id = :user_id
    """)
    existing = db.execute(existing_stmt, {"project_id": project_id, "user_id": member_data.user_id}).fetchone()
    
    if existing:
        raise HTTPException(status_code=400, detail="用户已是项目成员")
    
    join_time = datetime.utcnow()
    insert_stmt = text("""
        INSERT INTO project_members (project_id, user_id, role, joined_at)
        VALUES (:project_id, :user_id, :role, :joined_at)
    """)
    db.execute(insert_stmt, {
        "project_id": project_id,
        "user_id": member_data.user_id,
        "role": member_data.role,
        "joined_at": join_time
    })
    db.commit()
    
    return ProjectMemberResponse(
        user_id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=member_data.role,
        joined_at=join_time
    )


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
async def list_project_members(
    project_id: str,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    stmt = text("""
        SELECT pm.user_id, pm.role, pm.joined_at, u.username, u.email
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id = :project_id
    """)
    result = db.execute(stmt, {"project_id": project_id}).fetchall()
    
    members = []
    for row in result:
        members.append(ProjectMemberResponse(
            user_id=row.user_id,
            username=row.username,
            email=row.email,
            role=row.role,
            joined_at=row.joined_at
        ))
    
    return members


@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    stmt = text("""
        SELECT role FROM project_members 
        WHERE project_id = :project_id AND user_id = :user_id
    """)
    result = db.execute(stmt, {"project_id": project_id, "user_id": current_user.id}).fetchone()
    
    if not result or result[0] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有项目管理员可以移除成员")
    
    if project.owner_id == user_id:
        raise HTTPException(status_code=400, detail="不能移除项目所有者")
    
    delete_stmt = text("""
        DELETE FROM project_members 
        WHERE project_id = :project_id AND user_id = :user_id
    """)
    db.execute(delete_stmt, {"project_id": project_id, "user_id": user_id})
    db.commit()
    
    return {"message": "成员已移除"}
