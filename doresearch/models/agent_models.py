"""
Agent相关模型
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

class AgentStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

class AgentType(Enum):
    IEEE_DOWNLOADER = "ieee_downloader"
    PDF_PROCESSOR = "pdf_processor"
    ANALYZER = "analyzer"

@dataclass
class Agent:
    id: str
    name: str
    type: str
    capabilities: List[str]
    endpoint: str
    status: str = AgentStatus.OFFLINE.value
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict] = None