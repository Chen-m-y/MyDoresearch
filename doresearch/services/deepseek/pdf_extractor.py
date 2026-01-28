"""
PDF文本提取管理器模块
"""
import os
from typing import List, Tuple

from common.exceptions import ValidationError, FileSystemError, ExternalServiceError, ErrorCode
from common.logging import get_logger, log_performance
from .config import PDFExtractionConfig
from .types import PDFExtractorType, PDFExtractorProtocol
from .extractors import PDFPlumberExtractor, PyPDF2Extractor, PyMuPDFExtractor


class PDFTextExtractor:
    """PDF文本提取管理器"""
    
    def __init__(self, config: PDFExtractionConfig = None):
        self.config = config or PDFExtractionConfig()
        self.logger = get_logger(f"{__name__}.PDFTextExtractor")
        
        # 初始化提取器
        self.extractors = {
            PDFExtractorType.PDFPLUMBER: PDFPlumberExtractor(),
            PDFExtractorType.PYPDF2: PyPDF2Extractor(),
            PDFExtractorType.PYMUPDF: PyMuPDFExtractor()
        }
    
    def _validate_pdf_file(self, pdf_path: str) -> None:
        """验证PDF文件"""
        if not pdf_path:
            raise ValidationError(
                field="pdf_path",
                message="PDF path is required"
            )
        
        if not os.path.exists(pdf_path):
            raise FileSystemError(
                message=f"PDF file not found: {pdf_path}",
                file_path=pdf_path,
                operation="read"
            )
        
        if not pdf_path.lower().endswith('.pdf'):
            raise ValidationError(
                field="pdf_path",
                message="File must be a PDF",
                value=pdf_path
            )
    
    def _get_available_extractors(self) -> List[Tuple[PDFExtractorType, PDFExtractorProtocol]]:
        """获取可用的提取器"""
        available = []
        for extractor_type in self.config.fallback_extractors:
            extractor = self.extractors.get(extractor_type)
            if extractor and extractor.is_available():
                available.append((extractor_type, extractor))
        
        if not available:
            raise ExternalServiceError(
                service="PDF extractors",
                message="No PDF extraction libraries available",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
        
        return available
    
    @log_performance("pdf_extraction")
    def extract_text(self, pdf_path: str) -> str:
        """提取PDF文本"""
        self._validate_pdf_file(pdf_path)
        
        available_extractors = self._get_available_extractors()
        
        last_error = None
        for extractor_type, extractor in available_extractors:
            try:
                self.logger.info(f"Attempting PDF extraction with {extractor_type.value}")
                text = extractor.extract_text(pdf_path, self.config)
                
                if text.strip():
                    self.logger.info(f"Successfully extracted text with {extractor_type.value}")
                    return text
                else:
                    self.logger.warning(f"No text extracted with {extractor_type.value}")
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"Failed to extract with {extractor_type.value}: {str(e)}")
                continue
        
        # 所有提取器都失败
        raise ExternalServiceError(
            service="PDF extractors",
            message="All PDF extraction attempts failed",
            error_code=ErrorCode.PDF_DOWNLOAD_ERROR,
            cause=last_error
        )