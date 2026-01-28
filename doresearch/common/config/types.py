"""
配置系统类型定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Type, Any, Optional


class Environment(Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ConfigSource(Enum):
    """配置源类型"""
    ENVIRONMENT = "environment"
    FILE = "file"
    DEFAULT = "default"


@dataclass
class ConfigField:
    """配置字段描述"""
    name: str
    type: Type
    default: Any
    required: bool
    env_var: Optional[str] = None
    description: Optional[str] = None
    validator: Optional[callable] = None