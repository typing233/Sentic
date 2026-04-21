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
