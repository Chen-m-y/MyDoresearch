"""
自定义异常类
"""


class FetchError(Exception):
    """数据抓取失败异常"""
    
    def __init__(self, message: str, error_code: str = 'FETCH_ERROR', details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ValidationError(Exception):
    """参数验证失败异常"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class RateLimitError(Exception):
    """API限流异常"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class SourceUnavailableError(Exception):
    """数据源不可用异常"""
    
    def __init__(self, message: str, source: str, details: dict = None):
        super().__init__(message)
        self.source = source
        self.details = details or {}