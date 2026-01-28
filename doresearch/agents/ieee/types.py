"""
IEEE Agent类型定义
"""
from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class AgentStatus(Enum):
    """Agent状态"""
    OFFLINE = "offline"
    ONLINE = "online" 
    CONNECTING = "connecting"
    ERROR = "error"


class TaskType(Enum):
    """任务类型"""
    IEEE_DOWNLOAD = "ieee_download"
    PDF_DOWNLOAD = "pdf_download"


@dataclass
class TaskData:
    """任务数据"""
    task_id: str
    task_type: str
    data: Dict[str, Any]
    created_at: str = None
    
    
@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    result: Dict[str, Any] = None
    error: str = None
    processing_time: float = 0.0