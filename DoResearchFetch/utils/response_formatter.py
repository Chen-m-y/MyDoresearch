"""
响应格式化工具
"""

from datetime import datetime
from typing import Dict, Any, Optional


def format_response(data: Dict[str, Any], source_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    格式化成功响应
    
    Args:
        data: 响应数据
        source_info: 可选的数据源信息
        
    Returns:
        格式化后的响应
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    if source_info:
        response["source_info"] = source_info
    
    return response


def format_error(error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    格式化错误响应
    
    Args:
        error_code: 错误代码
        message: 错误消息
        details: 可选的错误详情
        
    Returns:
        格式化后的错误响应
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return response


def format_validation_error(field: str, message: str, value: Any = None) -> Dict[str, Any]:
    """
    格式化参数验证错误
    
    Args:
        field: 字段名
        message: 错误消息
        value: 无效的值（可选）
        
    Returns:
        格式化后的验证错误响应
    """
    details = {"field": field}
    if value is not None:
        details["invalid_value"] = value
    
    return format_error(
        "VALIDATION_ERROR",
        f"参数验证失败: {field} - {message}",
        details
    )