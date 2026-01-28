"""
配置验证器模块
"""
from typing import Any, Type, Union
from pathlib import Path
from enum import Enum

from common.exceptions import ValidationError
from common.logging import get_logger
from .types import ConfigField


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.ConfigValidator")
    
    def validate_field(self, field: ConfigField, value: Any) -> Any:
        """验证单个字段"""
        # 检查必需字段
        if field.required and value is None:
            raise ValidationError(
                field=field.name,
                message=f"Required field '{field.name}' is missing"
            )
        
        # 如果值为None且字段不是必需的，返回默认值
        if value is None:
            return field.default
        
        # 类型转换和验证
        validated_value = self._convert_type(value, field.type, field.name)
        
        # 自定义验证器
        if field.validator:
            try:
                field.validator(validated_value)
            except Exception as e:
                raise ValidationError(
                    field=field.name,
                    message=f"Validation failed: {str(e)}",
                    value=validated_value
                )
        
        return validated_value
    
    def _convert_type(self, value: Any, target_type: Type, field_name: str) -> Any:
        """类型转换"""
        if isinstance(value, target_type):
            return value
        
        try:
            # 特殊类型处理
            if target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            
            elif target_type == Path:
                return Path(str(value))
            
            elif hasattr(target_type, '__origin__') and target_type.__origin__ is Union:
                # 处理 Optional[Type] 类型
                args = target_type.__args__
                if len(args) == 2 and type(None) in args:
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    return self._convert_type(value, non_none_type, field_name)
            
            elif isinstance(target_type, type) and issubclass(target_type, Enum):
                if isinstance(value, str):
                    return target_type(value)
                return target_type(value)
            
            else:
                return target_type(value)
                
        except (ValueError, TypeError) as e:
            raise ValidationError(
                field=field_name,
                message=f"Cannot convert {type(value).__name__} to {target_type.__name__}",
                value=value
            ) from e