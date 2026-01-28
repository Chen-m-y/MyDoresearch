"""
PDF文本提取器模块
"""
from common.exceptions import ExternalServiceError, ErrorCode
from common.logging import get_logger, log_errors
from .config import PDFExtractionConfig


class PDFPlumberExtractor:
    """PDFPlumber文本提取器"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.PDFPlumberExtractor")
    
    def is_available(self) -> bool:
        """检查是否可用"""
        try:
            import pdfplumber
            return True
        except ImportError:
            return False
    
    @log_errors("pdf_extraction")
    def extract_text(self, pdf_path: str, config: PDFExtractionConfig) -> str:
        """使用pdfplumber提取文本"""
        if not self.is_available():
            raise ExternalServiceError(
                service="pdfplumber",
                message="pdfplumber library not available",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
        
        import pdfplumber
        
        text_parts = []
        total_chars = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    if total_chars >= config.max_total_chars:
                        break
                    
                    page_text = page.extract_text() or ""
                    
                    # 限制单页字符数
                    if len(page_text) > config.max_chars_per_page:
                        page_text = page_text[:config.max_chars_per_page]
                    
                    text_parts.append(page_text)
                    total_chars += len(page_text)
                    
                    self.logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
        
        except Exception as e:
            raise ExternalServiceError(
                service="pdfplumber",
                message=f"Failed to extract text: {str(e)}",
                error_code=ErrorCode.PDF_DOWNLOAD_ERROR,
                cause=e
            )
        
        result = "\n".join(text_parts)
        self.logger.info(f"PDFPlumber extracted {len(result)} total characters")
        return result


class PyPDF2Extractor:
    """PyPDF2文本提取器"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.PyPDF2Extractor")
    
    def is_available(self) -> bool:
        """检查是否可用"""
        try:
            import PyPDF2
            return True
        except ImportError:
            return False
    
    @log_errors("pdf_extraction")
    def extract_text(self, pdf_path: str, config: PDFExtractionConfig) -> str:
        """使用PyPDF2提取文本"""
        if not self.is_available():
            raise ExternalServiceError(
                service="PyPDF2",
                message="PyPDF2 library not available",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
        
        import PyPDF2
        
        text_parts = []
        total_chars = 0
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages, 1):
                    if total_chars >= config.max_total_chars:
                        break
                    
                    page_text = page.extract_text() or ""
                    
                    # 限制单页字符数
                    if len(page_text) > config.max_chars_per_page:
                        page_text = page_text[:config.max_chars_per_page]
                    
                    text_parts.append(page_text)
                    total_chars += len(page_text)
                    
                    self.logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
        
        except Exception as e:
            raise ExternalServiceError(
                service="PyPDF2",
                message=f"Failed to extract text: {str(e)}",
                error_code=ErrorCode.PDF_DOWNLOAD_ERROR,
                cause=e
            )
        
        result = "\n".join(text_parts)
        self.logger.info(f"PyPDF2 extracted {len(result)} total characters")
        return result


class PyMuPDFExtractor:
    """PyMuPDF文本提取器"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.PyMuPDFExtractor")
    
    def is_available(self) -> bool:
        """检查是否可用"""
        try:
            import fitz  # PyMuPDF
            return True
        except ImportError:
            return False
    
    @log_errors("pdf_extraction")
    def extract_text(self, pdf_path: str, config: PDFExtractionConfig) -> str:
        """使用PyMuPDF提取文本"""
        if not self.is_available():
            raise ExternalServiceError(
                service="PyMuPDF",
                message="PyMuPDF library not available",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
        
        import fitz
        
        text_parts = []
        total_chars = 0
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    if total_chars >= config.max_total_chars:
                        break
                    
                    page = doc[page_num]
                    page_text = page.get_text() or ""
                    
                    # 限制单页字符数
                    if len(page_text) > config.max_chars_per_page:
                        page_text = page_text[:config.max_chars_per_page]
                    
                    text_parts.append(page_text)
                    total_chars += len(page_text)
                    
                    self.logger.debug(f"Extracted {len(page_text)} chars from page {page_num + 1}")
        
        except Exception as e:
            raise ExternalServiceError(
                service="PyMuPDF",
                message=f"Failed to extract text: {str(e)}",
                error_code=ErrorCode.PDF_DOWNLOAD_ERROR,
                cause=e
            )
        
        result = "\n".join(text_parts)
        self.logger.info(f"PyMuPDF extracted {len(result)} total characters")
        return result