from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from config import settings
from app.models.database import get_db
from app.models.models import User, Project, project_members
from app.models.schemas import UserRole

SECRET_KEY = "sentic-secret-key-2024-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权，请登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class PermissionChecker:
    def __init__(self, required_roles: list = None):
        self.required_roles = required_roles or [UserRole.EDITOR, UserRole.ADMIN]
    
    def __call__(
        self,
        user: User = Depends(get_current_user_required),
        db: Session = Depends(get_db)
    ):
        return self
    
    def check_project_permission(
        self,
        project_id: str,
        user: User,
        db: Session,
        required_roles: list = None
    ) -> bool:
        roles = required_roles or self.required_roles
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.is_public and UserRole.VIEWER in roles:
            return True
        
        if project.owner_id == user.id:
            return True
        
        from sqlalchemy import text
        stmt = text("""
            SELECT role FROM project_members 
            WHERE project_id = :project_id AND user_id = :user_id
        """)
        result = db.execute(stmt, {"project_id": project_id, "user_id": user.id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=403, detail="没有权限访问此项目")
        
        user_role = result[0]
        
        if UserRole.ADMIN in roles and user_role == UserRole.ADMIN:
            return True
        if UserRole.EDITOR in roles and user_role in [UserRole.ADMIN, UserRole.EDITOR]:
            return True
        if UserRole.VIEWER in roles and user_role in [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER]:
            return True
        
        raise HTTPException(status_code=403, detail="权限不足")
    
    def check_dashboard_permission(
        self,
        dashboard,
        user: User,
        db: Session,
        required_roles: list = None
    ) -> bool:
        if dashboard.is_public and UserRole.VIEWER in (required_roles or self.required_roles):
            return True
        
        if dashboard.owner_id == user.id:
            return True
        
        return self.check_project_permission(
            dashboard.project_id, user, db, required_roles
        )


auth_checker = PermissionChecker()
