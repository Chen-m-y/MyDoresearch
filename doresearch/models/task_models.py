"""
任务相关模型
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    # 仅下载PDF文件
    PDF_DOWNLOAD_ONLY = "pdf_download_only"
    
    # 完整分析（包含下载PDF + AI分析）
    FULL_ANALYSIS = "full_analysis"
    
    # 深度分析（兼容旧版本）
    DEEP_ANALYSIS = "deep_analysis"
    
    # 单独的PDF下载（兼容性）
    PDF_DOWNLOAD = "pdf_download"
    
    # 翻译任务
    TRANSLATION = "translation"

@dataclass
class Task:
    id: str
    paper_id: int
    task_type: str
    status: str = TaskStatus.PENDING.value
    priority: int = 5
    assigned_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: int = 0
    metadata: Optional[Dict] = None
    result: Optional[str] = None

@dataclass
class TaskStep:
    id: int
    task_id: str
    step_name: str
    status: str = TaskStatus.PENDING.value
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[str] = None