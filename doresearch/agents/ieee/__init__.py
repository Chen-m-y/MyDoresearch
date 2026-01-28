"""
IEEE Agent模块
提供IEEE论文下载的分布式Agent功能
"""

from .agent import IEEEAgent
from .config import AgentConfig, ConnectionConfig
from .types import AgentStatus, TaskType

__all__ = [
    'IEEEAgent',
    'AgentConfig',
    'ConnectionConfig', 
    'AgentStatus',
    'TaskType'
]