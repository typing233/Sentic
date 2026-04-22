from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class DataSourceType(str, Enum):
    DATABASE = "database"
    CSV = "csv"


class DatabaseConfig(BaseModel):
    db_type: str = Field(..., description="数据库类型，如 sqlite, mysql, postgresql")
    host: Optional[str] = Field(None, description="数据库主机")
    port: Optional[int] = Field(None, description="数据库端口")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    database: str = Field(..., description="数据库名称")
    table_name: Optional[str] = Field(None, description="表名")


class CSVConfig(BaseModel):
    file_path: str = Field(..., description="CSV文件路径")
    delimiter: str = Field(default=",", description="分隔符")
    encoding: str = Field(default="utf-8", description="编码格式")
    has_header: bool = Field(default=True, description="是否有表头")


class DataSourceConfig(BaseModel):
    name: str = Field(..., description="数据源名称")
    type: DataSourceType = Field(..., description="数据源类型")
    database_config: Optional[DatabaseConfig] = Field(None, description="数据库配置")
    csv_config: Optional[CSVConfig] = Field(None, description="CSV配置")


class DataSourceResponse(BaseModel):
    id: str = Field(..., description="数据源ID")
    name: str = Field(..., description="数据源名称")
    type: DataSourceType = Field(..., description="数据源类型")
    status: str = Field(..., description="连接状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    columns: Optional[List[str]] = Field(None, description="数据列名")
    row_count: Optional[int] = Field(None, description="数据行数")
    project_id: Optional[str] = Field(None, description="所属项目ID")


class InsightType(str, Enum):
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    TREND = "trend"
    CORRELATION = "correlation"


class InsightCard(BaseModel):
    id: str = Field(..., description="洞察ID")
    title: str = Field(..., description="洞察标题")
    type: InsightType = Field(..., description="洞察类型")
    description: str = Field(..., description="详细描述")
    severity: str = Field(..., description="严重程度/重要性")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="相关指标数据")
    suggestion: str = Field(..., description="增长建议")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="证据数据")
    created_at: datetime = Field(default_factory=datetime.now, description="生成时间")


class InsightsResponse(BaseModel):
    data_source_id: str = Field(..., description="数据源ID")
    insights: List[InsightCard] = Field(..., description="洞察卡片列表")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")


class ChatRequest(BaseModel):
    data_source_id: str = Field(..., description="数据源ID")
    query: str = Field(..., description="自然语言查询")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    project_id: Optional[str] = Field(None, description="项目ID")


class SQLQuery(BaseModel):
    sql: str = Field(..., description="生成的SQL查询")
    explanation: str = Field(..., description="SQL解释")
    suggested_chart_type: str = Field(..., description="建议的图表类型")


class ChatResponse(BaseModel):
    conversation_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="原始查询")
    sql_query: SQLQuery = Field(..., description="SQL查询")
    execution_result: Dict[str, Any] = Field(..., description="执行结果")
    chart_config: Dict[str, Any] = Field(..., description="图表配置")
    response_text: str = Field(..., description="自然语言回答")


class VisualizationRequest(BaseModel):
    data_source_id: str = Field(..., description="数据源ID")
    query: str = Field(..., description="SQL查询或数据引用")
    chart_type: str = Field(..., description="图表类型")
    x_axis: Optional[str] = Field(None, description="X轴字段")
    y_axis: Optional[List[str]] = Field(None, description="Y轴字段")
    title: Optional[str] = Field(None, description="图表标题")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class VisualizationResponse(BaseModel):
    chart_type: str = Field(..., description="图表类型")
    data: Dict[str, Any] = Field(..., description="图表数据")
    config: Dict[str, Any] = Field(..., description="图表配置")
    html: Optional[str] = Field(None, description="HTML格式的图表")
    json: Optional[Dict[str, Any]] = Field(None, description="JSON格式的图表数据")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class WidgetType(str, Enum):
    CHART = "chart"
    INSIGHT = "insight"
    TEXT = "text"
    TABLE = "table"


class ShareType(str, Enum):
    DASHBOARD = "dashboard"
    CHART = "chart"
    DATA_SOURCE = "data_source"


class UserCreate(BaseModel):
    email: str = Field(..., description="邮箱")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    full_name: Optional[str] = Field(None, description="姓名")


class UserLogin(BaseModel):
    email: str = Field(..., description="邮箱或用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="邮箱")
    username: str = Field(..., description="用户名")
    full_name: Optional[str] = Field(None, description="姓名")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")


class Token(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")


class TeamCreate(BaseModel):
    name: str = Field(..., description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")


class TeamResponse(BaseModel):
    id: str = Field(..., description="团队ID")
    name: str = Field(..., description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")
    owner_id: str = Field(..., description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    member_count: int = Field(default=0, description="成员数量")


class ProjectCreate(BaseModel):
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    team_id: Optional[str] = Field(None, description="所属团队ID")
    is_public: bool = Field(default=False, description="是否公开")


class ProjectResponse(BaseModel):
    id: str = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    team_id: Optional[str] = Field(None, description="所属团队ID")
    owner_id: str = Field(..., description="创建者ID")
    is_public: bool = Field(default=False, description="是否公开")
    created_at: datetime = Field(..., description="创建时间")


class DashboardWidgetCreate(BaseModel):
    title: Optional[str] = Field(None, description="组件标题")
    widget_type: str = Field(..., description="组件类型")
    position: int = Field(default=0, description="位置")
    width: int = Field(default=12, description="宽度")
    height: int = Field(default=4, description="高度")
    data_source_id: Optional[str] = Field(None, description="数据源ID")
    query: Optional[str] = Field(None, description="查询语句")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="图表配置")
    chart_type: Optional[str] = Field(None, description="图表类型")
    insight_id: Optional[str] = Field(None, description="洞察ID")
    content: Optional[str] = Field(None, description="文本内容")


class DashboardWidgetUpdate(BaseModel):
    title: Optional[str] = Field(None, description="组件标题")
    position: Optional[int] = Field(None, description="位置")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="图表配置")
    content: Optional[str] = Field(None, description="文本内容")


class DashboardWidgetResponse(BaseModel):
    id: str = Field(..., description="组件ID")
    dashboard_id: str = Field(..., description="看板ID")
    title: Optional[str] = Field(None, description="组件标题")
    widget_type: str = Field(..., description="组件类型")
    position: int = Field(default=0, description="位置")
    width: int = Field(default=12, description="宽度")
    height: int = Field(default=4, description="高度")
    data_source_id: Optional[str] = Field(None, description="数据源ID")
    query: Optional[str] = Field(None, description="查询语句")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="图表配置")
    chart_type: Optional[str] = Field(None, description="图表类型")
    insight_id: Optional[str] = Field(None, description="洞察ID")
    content: Optional[str] = Field(None, description="文本内容")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DashboardCreate(BaseModel):
    name: str = Field(..., description="看板名称")
    description: Optional[str] = Field(None, description="看板描述")
    project_id: str = Field(..., description="所属项目ID")
    is_public: bool = Field(default=False, description="是否公开")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="布局配置")


class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, description="看板名称")
    description: Optional[str] = Field(None, description="看板描述")
    is_public: Optional[bool] = Field(None, description="是否公开")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="布局配置")


class DashboardResponse(BaseModel):
    id: str = Field(..., description="看板ID")
    name: str = Field(..., description="看板名称")
    description: Optional[str] = Field(None, description="看板描述")
    project_id: str = Field(..., description="所属项目ID")
    owner_id: str = Field(..., description="创建者ID")
    is_public: bool = Field(default=False, description="是否公开")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="布局配置")
    widgets: List[DashboardWidgetResponse] = Field(default_factory=list, description="组件列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ShareLinkCreate(BaseModel):
    share_type: str = Field(..., description="分享类型")
    target_id: str = Field(..., description="目标ID")
    expires_in_hours: Optional[int] = Field(None, description="过期时间（小时），None表示永不过期")


class ShareLinkResponse(BaseModel):
    id: str = Field(..., description="分享链接ID")
    token: str = Field(..., description="分享令牌")
    share_type: str = Field(..., description="分享类型")
    target_id: str = Field(..., description="目标ID")
    share_url: str = Field(..., description="分享链接")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否激活")
    view_count: int = Field(default=0, description="访问次数")
    created_at: datetime = Field(..., description="创建时间")


class ExportRequest(BaseModel):
    format: str = Field(..., description="导出格式: png, pdf, csv")
    data_source_id: Optional[str] = Field(None, description="数据源ID（用于CSV导出）")
    query: Optional[str] = Field(None, description="查询语句（用于CSV导出）")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="图表配置（用于图片导出）")
    width: int = Field(default=1200, description="图片宽度")
    height: int = Field(default=800, description="图片高度")


class ProjectMemberAdd(BaseModel):
    user_id: str = Field(..., description="用户ID")
    role: str = Field(default="viewer", description="角色: admin, editor, viewer")


class ProjectMemberResponse(BaseModel):
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    role: str = Field(..., description="角色")
    joined_at: datetime = Field(..., description="加入时间")
