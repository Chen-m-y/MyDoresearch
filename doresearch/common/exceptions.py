"""
DoResearch 项目的异常处理系统
定义所有自定义异常类和错误处理工具
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Type
from enum import Enum
import traceback
import json
from datetime import datetime


class ErrorCode(Enum):
    """错误代码枚举"""
    # 通用错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    
    # 数据库错误
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_CONSTRAINT_ERROR = "DATABASE_CONSTRAINT_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    
    # 业务逻辑错误
    PAPER_NOT_FOUND = "PAPER_NOT_FOUND"
    FEED_NOT_FOUND = "FEED_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    INVALID_PAPER_STATUS = "INVALID_PAPER_STATUS"
    INVALID_TASK_STATUS = "INVALID_TASK_STATUS"
    
    # 外部服务错误
    NETWORK_ERROR = "NETWORK_ERROR"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_UNAUTHORIZED = "API_UNAUTHORIZED"
    DEEPSEEK_API_ERROR = "DEEPSEEK_API_ERROR"
    PDF_DOWNLOAD_ERROR = "PDF_DOWNLOAD_ERROR"
    
    # 文件系统错误
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"
    DISK_SPACE_ERROR = "DISK_SPACE_ERROR"
    
    # 配置错误
    CONFIG_ERROR = "CONFIG_ERROR"
    MISSING_CONFIG = "MISSING_CONFIG"
    INVALID_CONFIG = "INVALID_CONFIG"


class DoResearchError(Exception):
    """DoResearch基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc() if cause else None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback_info
        }
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        context_str = f" (Context: {self.context})" if self.context else ""
        return f"[{self.error_code.value}] {self.message}{context_str}"


class ValidationError(DoResearchError):
    """验证错误"""
    
    def __init__(
        self,
        field: str,
        message: str,
        value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        self.value = value
        validation_context = {"field": field, "value": str(value) if value is not None else None}
        if context:
            validation_context.update(context)
        
        super().__init__(
            message=f"Validation failed for field '{field}': {message}",
            error_code=ErrorCode.VALIDATION_ERROR,
            context=validation_context
        )


class MultipleValidationErrors(DoResearchError):
    """多个验证错误"""
    
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        self.field_errors = {error.field: error for error in errors}
        
        error_summary = ", ".join([f"{error.field}: {error.message}" for error in errors])
        super().__init__(
            message=f"Multiple validation errors: {error_summary}",
            error_code=ErrorCode.VALIDATION_ERROR,
            context={"error_count": len(errors), "fields": list(self.field_errors.keys())}
        )
    
    def get_field_error(self, field: str) -> Optional[ValidationError]:
        """获取特定字段的错误"""
        return self.field_errors.get(field)
    
    def has_field_error(self, field: str) -> bool:
        """检查是否有特定字段的错误"""
        return field in self.field_errors


class DatabaseError(DoResearchError):
    """数据库错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_QUERY_ERROR,
        query: Optional[str] = None,
        params: Optional[Any] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if query:
            context["query"] = query[:500]  # 限制长度
        if params:
            context["params"] = str(params)[:200]
        
        super().__init__(
            message=message,
            error_code=error_code,
            context=context,
            cause=cause
        )
        self.query = query
        self.params = params


class ExternalServiceError(DoResearchError):
    """外部服务错误"""
    
    def __init__(
        self,
        service: str,
        message: str,
        error_code: ErrorCode = ErrorCode.NETWORK_ERROR,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
        cause: Optional[Exception] = None
    ):
        context = {"service": service}
        if status_code:
            context["status_code"] = status_code
        if response_data:
            context["response_data"] = str(response_data)[:500]
        
        super().__init__(
            message=f"{service} error: {message}",
            error_code=error_code,
            context=context,
            cause=cause
        )
        self.service = service
        self.status_code = status_code
        self.response_data = response_data


class BusinessLogicError(DoResearchError):
    """业务逻辑错误"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        entity_type: Optional[str] = None,
        entity_id: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        business_context = context or {}
        if entity_type:
            business_context["entity_type"] = entity_type
        if entity_id:
            business_context["entity_id"] = str(entity_id)
        
        super().__init__(
            message=message,
            error_code=error_code,
            context=business_context
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConfigurationError(DoResearchError):
    """配置错误"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[Type] = None,
        actual_value: Optional[Any] = None
    ):
        context = {}
        if config_key:
            context["config_key"] = config_key
        if expected_type:
            context["expected_type"] = expected_type.__name__
        if actual_value is not None:
            context["actual_value"] = str(actual_value)
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIG_ERROR,
            context=context
        )


class FileSystemError(DoResearchError):
    """文件系统错误"""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation
        
        super().__init__(
            message=message,
            error_code=ErrorCode.FILE_NOT_FOUND,
            context=context,
            cause=cause
        )


# 特定业务异常
class PaperNotFoundError(BusinessLogicError):
    """论文未找到错误"""
    
    def __init__(self, paper_id: int):
        super().__init__(
            message=f"Paper with ID {paper_id} not found",
            error_code=ErrorCode.PAPER_NOT_FOUND,
            entity_type="paper",
            entity_id=paper_id
        )


class FeedNotFoundError(BusinessLogicError):
    """论文源未找到错误"""
    
    def __init__(self, feed_id: int):
        super().__init__(
            message=f"Feed with ID {feed_id} not found",
            error_code=ErrorCode.FEED_NOT_FOUND,
            entity_type="feed",
            entity_id=feed_id
        )


class TaskNotFoundError(BusinessLogicError):
    """任务未找到错误"""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task with ID {task_id} not found",
            error_code=ErrorCode.TASK_NOT_FOUND,
            entity_type="task",
            entity_id=task_id
        )


class InvalidStatusError(BusinessLogicError):
    """无效状态错误"""
    
    def __init__(self, entity_type: str, current_status: str, target_status: str):
        super().__init__(
            message=f"Cannot change {entity_type} status from '{current_status}' to '{target_status}'",
            error_code=ErrorCode.INVALID_PAPER_STATUS if entity_type == "paper" else ErrorCode.INVALID_TASK_STATUS,
            entity_type=entity_type,
            context={
                "current_status": current_status,
                "target_status": target_status
            }
        )


# 异常处理工具
class ErrorHandler:
    """错误处理工具类"""
    
    @staticmethod
    def handle_database_error(e: Exception, query: Optional[str] = None) -> DatabaseError:
        """处理数据库异常"""
        error_message = str(e).lower()
        
        if "timeout" in error_message:
            error_code = ErrorCode.DATABASE_TIMEOUT
        elif "constraint" in error_message or "unique" in error_message:
            error_code = ErrorCode.DATABASE_CONSTRAINT_ERROR
        elif "connection" in error_message:
            error_code = ErrorCode.DATABASE_CONNECTION_ERROR
        else:
            error_code = ErrorCode.DATABASE_QUERY_ERROR
        
        return DatabaseError(
            message=str(e),
            error_code=error_code,
            query=query,
            cause=e
        )
    
    @staticmethod
    def handle_external_service_error(
        service: str, 
        e: Exception, 
        status_code: Optional[int] = None
    ) -> ExternalServiceError:
        """处理外部服务异常"""
        if status_code == 401:
            error_code = ErrorCode.API_UNAUTHORIZED
        elif status_code == 429:
            error_code = ErrorCode.API_RATE_LIMIT
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
            error_code = ErrorCode.NETWORK_ERROR
        else:
            error_code = ErrorCode.NETWORK_ERROR
        
        return ExternalServiceError(
            service=service,
            message=str(e),
            error_code=error_code,
            status_code=status_code,
            cause=e
        )
    
    @staticmethod
    def create_validation_error_response(errors: List[ValidationError]) -> Dict[str, Any]:
        """创建验证错误响应"""
        return {
            "success": False,
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "message": "Validation failed",
            "errors": [
                {
                    "field": error.field,
                    "message": error.message,
                    "value": error.value
                }
                for error in errors
            ]
        }
    
    @staticmethod
    def create_error_response(error: DoResearchError) -> Dict[str, Any]:
        """创建标准错误响应"""
        return {
            "success": False,
            "error_code": error.error_code.value,
            "message": error.message,
            "context": error.context,
            "timestamp": error.timestamp.isoformat()
        }