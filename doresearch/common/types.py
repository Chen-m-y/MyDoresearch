"""
DoResearch 项目的类型定义
定义所有数据结构和接口的类型注解
"""
from __future__ import annotations
from typing import Dict, List, Optional, Union, Any, Callable, Protocol, TypedDict, Literal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import sqlite3


# 基础类型别名
DatabaseRow = sqlite3.Row
JSONData = Dict[str, Any]
QueryParams = Union[tuple, List[Any]]


# 枚举类型
class PaperStatus(Enum):
    """论文状态枚举"""
    UNREAD = "unread"
    READING = "reading"
    READ = "read"
    ARCHIVED = "archived"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """任务类型枚举"""
    DEEP_ANALYSIS = "deep_analysis"
    PDF_DOWNLOAD = "pdf_download"
    TRANSLATION = "translation"
    FEED_UPDATE = "feed_update"


class AgentStatus(Enum):
    """Agent状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# TypedDict 定义
class PaperDict(TypedDict, total=False):
    """论文数据结构"""
    id: int
    feed_id: int
    title: str
    abstract: Optional[str]
    abstract_cn: Optional[str]
    authors: Optional[str]
    journal: Optional[str]
    published_date: Optional[str]
    url: Optional[str]
    pdf_url: Optional[str]
    pdf_path: Optional[str]
    doi: Optional[str]
    status: str
    status_changed_at: Optional[str]
    created_at: str
    hash: str
    external_id: Optional[str]
    ieee_article_number: Optional[str]
    analysis_result: Optional[str]
    analysis_at: Optional[str]


class FeedDict(TypedDict, total=False):
    """论文源数据结构"""
    id: int
    name: str
    url: str
    journal: Optional[str]
    created_at: str
    last_updated: Optional[str]
    active: bool


class TaskDict(TypedDict, total=False):
    """任务数据结构"""
    id: str
    paper_id: int
    task_type: str
    status: str
    priority: int
    assigned_agent: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    progress: int
    metadata: Optional[str]
    result: Optional[str]


class AgentDict(TypedDict, total=False):
    """Agent数据结构"""
    id: str
    name: str
    type: str
    capabilities: Optional[str]
    endpoint: str
    status: str
    last_heartbeat: Optional[str]
    created_at: str
    metadata: Optional[str]


class StatisticsDict(TypedDict, total=False):
    """统计数据结构"""
    total_papers: int
    read_papers: int
    unread_papers: int
    reading_streak_days: int
    generated_at: str


class APIResponse(TypedDict, total=False):
    """API响应结构"""
    success: bool
    data: Optional[Any]
    error: Optional[str]
    message: Optional[str]


# 数据类定义
@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str
    max_connections: int = 10
    connection_timeout: int = 300
    check_interval: int = 60


@dataclass
class AppConfig:
    """应用配置"""
    secret_key: str
    database_path: str
    pdf_dir: str
    log_dir: str
    deepseek_api_key: str
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    task_check_interval: int = 5
    agent_heartbeat_timeout: int = 300


@dataclass
class PerformanceMetrics:
    """性能指标"""
    query_count: int
    slow_queries: int
    avg_response_time: float
    active_connections: int
    cache_hit_rate: float
    timestamp: datetime


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    value: Optional[Any] = None


# 协议定义（接口）
class DatabaseServiceProtocol(Protocol):
    """数据库服务接口"""
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[QueryParams] = None,
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """执行查询"""
        ...
    
    def execute_update(self, query: str, params: Optional[QueryParams] = None) -> int:
        """执行更新"""
        ...
    
    def execute_insert(self, query: str, params: Optional[QueryParams] = None) -> int:
        """执行插入"""
        ...


class PaperManagerProtocol(Protocol):
    """论文管理服务接口"""
    
    def get_paper(self, paper_id: int) -> Optional[PaperDict]:
        """获取论文"""
        ...
    
    def update_paper_status(self, paper_id: int, status: str) -> APIResponse:
        """更新论文状态"""
        ...
    
    def get_papers_by_feed(self, feed_id: int, status: Optional[str] = None) -> List[PaperDict]:
        """按订阅源获取论文"""
        ...


class StatisticsServiceProtocol(Protocol):
    """统计服务接口"""
    
    def get_quick_stats(self) -> StatisticsDict:
        """获取快速统计"""
        ...
    
    def get_reading_statistics(self) -> Dict[str, Any]:
        """获取完整统计"""
        ...


class TaskManagerProtocol(Protocol):
    """任务管理接口"""
    
    def create_task(self, task_type: str, paper_id: int, **kwargs) -> str:
        """创建任务"""
        ...
    
    def get_task(self, task_id: str) -> Optional[TaskDict]:
        """获取任务"""
        ...
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """更新任务状态"""
        ...


class LoggerProtocol(Protocol):
    """日志接口"""
    
    def debug(self, message: str, **kwargs) -> None:
        """调试日志"""
        ...
    
    def info(self, message: str, **kwargs) -> None:
        """信息日志"""
        ...
    
    def warning(self, message: str, **kwargs) -> None:
        """警告日志"""
        ...
    
    def error(self, message: str, **kwargs) -> None:
        """错误日志"""
        ...


# 函数类型定义
ValidationFunction = Callable[[Any], List[ValidationError]]
QueryBuilder = Callable[..., tuple[str, QueryParams]]
EventHandler = Callable[[str, Dict[str, Any]], None]


# 常量类型
HTTP_METHOD = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
CONTENT_TYPE = Literal["application/json", "text/html", "text/plain", "application/pdf"]


# 复合类型
class PaginatedResponse(TypedDict):
    """分页响应"""
    data: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class SearchQuery(TypedDict, total=False):
    """搜索查询"""
    keyword: Optional[str]
    status: Optional[str]
    feed_id: Optional[int]
    start_date: Optional[str]
    end_date: Optional[str]
    limit: int
    offset: int


class AnalysisResult(TypedDict, total=False):
    """分析结果"""
    summary: str
    key_points: List[str]
    categories: List[str]
    confidence: float
    processing_time: float
    model_version: str


# 异常类型
class DoResearchError(Exception):
    """DoResearch基础异常"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class ValidationException(DoResearchError):
    """验证异常"""
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        message = f"Validation failed: {len(errors)} errors"
        super().__init__(message, "VALIDATION_ERROR")


class DatabaseException(DoResearchError):
    """数据库异常"""
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR")
        self.query = query


class ExternalServiceException(DoResearchError):
    """外部服务异常"""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service}: {message}", "EXTERNAL_SERVICE_ERROR")
        self.service = service


# 工具类型
class DateRange(TypedDict):
    """日期范围"""
    start: datetime
    end: datetime


class ConnectionPoolStats(TypedDict):
    """连接池统计"""
    active_connections: int
    pool_size: int
    max_connections: int
    total_created: int