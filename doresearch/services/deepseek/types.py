"""
DeepSeek分析器类型定义
"""
from enum import Enum
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import PDFExtractionConfig


class PDFExtractorType(Enum):
    """PDF提取器类型"""
    PDFPLUMBER = "pdfplumber"
    PYPDF2 = "pypdf2"
    PYMUPDF = "pymupdf"


class PDFExtractorProtocol(Protocol):
    """PDF提取器接口"""
    
    def extract_text(self, pdf_path: str, config: 'PDFExtractionConfig') -> str:
        """提取PDF文本"""
        ...
    
    def is_available(self) -> bool:
        """检查提取器是否可用"""
        ...