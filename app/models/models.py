from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Enum, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.models.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class WidgetType(str, enum.Enum):
    CHART = "chart"
    INSIGHT = "insight"
    TEXT = "text"
    TABLE = "table"


class ShareType(str, enum.Enum):
    DASHBOARD = "dashboard"
    CHART = "chart"
    DATA_SOURCE = "data_source"


team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", String(36), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(20), default="viewer"),
    Column("joined_at", DateTime, default=datetime.utcnow)
)


project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(20), default="viewer"),
    Column("joined_at", DateTime, default=datetime.utcnow)
)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owned_teams = relationship("Team", back_populates="owner")
    owned_projects = relationship("Project", back_populates="owner")
    teams = relationship("Team", secondary=team_members, back_populates="members")
    projects = relationship("Project", secondary=project_members, back_populates="members")


class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="owned_teams")
    members = relationship("User", secondary=team_members, back_populates="teams")
    projects = relationship("Project", back_populates="team")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="owned_projects")
    team = relationship("Team", back_populates="projects")
    members = relationship("User", secondary=project_members, back_populates="projects")
    dashboards = relationship("Dashboard", back_populates="project")


class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(String(36), ForeignKey("projects.id"))
    owner_id = Column(String(36), ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    layout_config = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="dashboards")
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="dashboard")


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dashboard_id = Column(String(36), ForeignKey("dashboards.id", ondelete="CASCADE"))
    title = Column(String(255))
    widget_type = Column(String(50), nullable=False)
    position = Column(Integer, default=0)
    width = Column(Integer, default=12)
    height = Column(Integer, default=4)
    
    data_source_id = Column(String(36), nullable=True)
    query = Column(Text, nullable=True)
    chart_config = Column(Text, nullable=True)
    chart_type = Column(String(50), nullable=True)
    insight_id = Column(String(36), nullable=True)
    content = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dashboard = relationship("Dashboard", back_populates="widgets")


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token = Column(String(64), unique=True, index=True, nullable=False)
    share_type = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=False)
    
    dashboard_id = Column(String(36), ForeignKey("dashboards.id"), nullable=True)
    
    created_by = Column(String(36), ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    dashboard = relationship("Dashboard", back_populates="share_links")
