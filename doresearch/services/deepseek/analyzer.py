"""
重构后的DeepSeek分析器主类
"""
from typing import List

from common.types import AnalysisResult
from common.exceptions import ValidationError, ExternalServiceError, ErrorCode
from common.logging import get_logger, log_performance
from .config import AnalysisConfig, PDFExtractionConfig
from .pdf_extractor import PDFTextExtractor
from .text_processor import TextProcessor
from .api_client import DeepSeekAPIClient


class RefactoredDeepSeekAnalyzer:
    """重构后的DeepSeek分析器主类"""
    
    def __init__(self, api_key: str, analysis_config: AnalysisConfig = None, 
                 pdf_config: PDFExtractionConfig = None):
        
        if not api_key:
            raise ValidationError(
                field="api_key",
                message="DeepSeek API key is required"
            )
        
        self.analysis_config = analysis_config or AnalysisConfig(api_key=api_key)
        self.pdf_config = pdf_config or PDFExtractionConfig()
        
        # 初始化组件
        self.pdf_extractor = PDFTextExtractor(self.pdf_config)
        self.text_processor = TextProcessor()
        self.api_client = DeepSeekAPIClient(self.analysis_config)
        
        self.logger = get_logger(f"{__name__}.RefactoredDeepSeekAnalyzer")
    
    @log_performance("full_analysis")
    def analyze_with_pdf_text(self, pdf_path: str) -> AnalysisResult:
        """使用PDF文本进行分析"""
        self.logger.info(f"Starting PDF analysis for: {pdf_path}")
        
        try:
            # 1. 提取PDF文本
            raw_text = self.pdf_extractor.extract_text(pdf_path)
            
            if not raw_text.strip():
                raise ExternalServiceError(
                    service="PDF extraction",
                    message="No text could be extracted from PDF",
                    error_code=ErrorCode.PDF_DOWNLOAD_ERROR
                )
            
            # 2. 处理文本
            processed_text = self.text_processor.prepare_for_analysis(
                raw_text, 
                self.analysis_config.max_text_length
            )
            
            # 3. 调用API分析
            analysis_result = self.api_client.analyze_text(processed_text)
            
            # 4. 构建结果
            result: AnalysisResult = {
                "summary": self._extract_summary(analysis_result),
                "key_points": self._extract_key_points(analysis_result),
                "categories": self._extract_categories(analysis_result),
                "confidence": 0.85,  # 可以根据实际情况调整
                "processing_time": 0.0,  # 由装饰器记录
                "model_version": self.analysis_config.model_name
            }
            
            self.logger.info("PDF analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"PDF analysis failed: {str(e)}")
            raise
    
    def translate_text(self, text: str) -> str:
        """翻译文本"""
        if not text.strip():
            raise ValidationError(
                field="text",
                message="Text to translate cannot be empty"
            )
        
        prompt = f"请将以下英文文本翻译成中文，保持学术性和准确性：\n\n{text}"
        payload = self.api_client._create_request_payload(prompt)
        
        response_data = self.api_client._make_api_request(payload)
        return self.api_client._extract_response_content(response_data)
    
    def _extract_summary(self, analysis_text: str) -> str:
        """从分析结果中提取摘要"""
        lines = analysis_text.split('\n')
        for line in lines:
            if line.startswith('摘要：') or line.startswith('- 摘要：'):
                return line.split('：', 1)[1].strip()
        
        # 如果没有找到标准格式，返回前100个字符
        return analysis_text[:100].strip()
    
    def _extract_key_points(self, analysis_text: str) -> List[str]:
        """从分析结果中提取关键点"""
        lines = analysis_text.split('\n')
        points = []
        
        for line in lines:
            if line.startswith('关键点：') or line.startswith('- 关键点：'):
                points_text = line.split('：', 1)[1].strip()
                # 简单分割，实际可以更复杂
                points = [p.strip() for p in points_text.split('，') if p.strip()]
                break
        
        return points[:5]  # 最多返回5个关键点
    
    def _extract_categories(self, analysis_text: str) -> List[str]:
        """从分析结果中提取分类"""
        lines = analysis_text.split('\n')
        for line in lines:
            if line.startswith('领域：') or line.startswith('- 领域：'):
                category_text = line.split('：', 1)[1].strip()
                return [cat.strip() for cat in category_text.split('，') if cat.strip()]
        
        return ["未分类"]