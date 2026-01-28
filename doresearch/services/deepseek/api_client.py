"""
DeepSeek API客户端模块
"""
import requests
from typing import Dict

from common.exceptions import ExternalServiceError, ErrorCode
from common.logging import get_logger, log_performance
from .config import AnalysisConfig


class DeepSeekAPIClient:
    """DeepSeek API客户端"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = get_logger(f"{__name__}.DeepSeekAPIClient")
    
    def _build_analysis_prompt(self, text: str) -> str:
        """构建分析提示"""
        return f"""请分析以下学术论文内容，并提供以下信息：
1. 论文主要内容摘要
2. 关键技术点或方法
3. 主要贡献和创新点
4. 研究领域分类
5. 实用价值评估

论文内容：
{text}

请用中文回答，格式要求：
- 摘要：[简洁的内容总结]
- 关键点：[列出3-5个要点]
- 创新点：[主要贡献]
- 领域：[研究领域]
- 价值：[实用性评估]"""
    
    def _create_request_payload(self, prompt: str) -> Dict:
        """创建请求载荷"""
        return {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": False
        }
    
    def _make_api_request(self, payload: Dict) -> Dict:
        """发起API请求"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.config.api_base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            raise ExternalServiceError(
                service="DeepSeek API",
                message="Request timeout",
                error_code=ErrorCode.NETWORK_ERROR,
                cause=e
            )
        except requests.exceptions.RequestException as e:
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            
            if status_code == 401:
                error_code = ErrorCode.API_UNAUTHORIZED
                message = "Invalid API key"
            elif status_code == 429:
                error_code = ErrorCode.API_RATE_LIMIT
                message = "Rate limit exceeded"
            else:
                error_code = ErrorCode.DEEPSEEK_API_ERROR
                message = f"API request failed: {str(e)}"
            
            raise ExternalServiceError(
                service="DeepSeek API",
                message=message,
                error_code=error_code,
                status_code=status_code,
                cause=e
            )
    
    def _extract_response_content(self, response_data: Dict) -> str:
        """提取响应内容"""
        try:
            choices = response_data.get('choices', [])
            if not choices:
                raise ExternalServiceError(
                    service="DeepSeek API",
                    message="No choices in API response",
                    error_code=ErrorCode.DEEPSEEK_API_ERROR
                )
            
            message = choices[0].get('message', {})
            content = message.get('content', '')
            
            if not content:
                raise ExternalServiceError(
                    service="DeepSeek API",
                    message="Empty content in API response",
                    error_code=ErrorCode.DEEPSEEK_API_ERROR
                )
            
            return content.strip()
            
        except (KeyError, IndexError, TypeError) as e:
            raise ExternalServiceError(
                service="DeepSeek API",
                message=f"Invalid API response format: {str(e)}",
                error_code=ErrorCode.DEEPSEEK_API_ERROR,
                cause=e
            )
    
    @log_performance("deepseek_api")
    def analyze_text(self, text: str) -> str:
        """分析文本"""
        prompt = self._build_analysis_prompt(text)
        payload = self._create_request_payload(prompt)
        
        self.logger.info(f"Sending analysis request to DeepSeek API (text length: {len(text)})")
        
        response_data = self._make_api_request(payload)
        result = self._extract_response_content(response_data)
        
        self.logger.info(f"Received analysis result (length: {len(result)})")
        return result