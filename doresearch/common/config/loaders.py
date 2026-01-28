"""
配置加载器模块
"""
import os
import json
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, Union, List

from common.exceptions import ConfigurationError


class ConfigLoader(ABC):
    """配置加载器抽象基类"""
    
    @abstractmethod
    def load(self, source: str) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def can_load(self, source: str) -> bool:
        """检查是否可以加载指定源"""
        pass


class JSONConfigLoader(ConfigLoader):
    """JSON配置加载器"""
    
    def can_load(self, source: str) -> bool:
        return source.endswith(('.json', '.jsonc'))
    
    def load(self, source: str) -> Dict[str, Any]:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ConfigurationError(
                message=f"Failed to load JSON config from {source}",
                config_key=source
            ) from e


class YAMLConfigLoader(ConfigLoader):
    """YAML配置加载器"""
    
    def can_load(self, source: str) -> bool:
        return source.endswith(('.yaml', '.yml'))
    
    def load(self, source: str) -> Dict[str, Any]:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError) as e:
            raise ConfigurationError(
                message=f"Failed to load YAML config from {source}",
                config_key=source
            ) from e


class EnvironmentConfigLoader(ConfigLoader):
    """环境变量配置加载器"""
    
    def __init__(self, prefix: str = "DORESEARCH_"):
        self.prefix = prefix
    
    def can_load(self, source: str) -> bool:
        return source == "environment"
    
    def load(self, source: str) -> Dict[str, Any]:
        config = {}
        prefix_len = len(self.prefix)
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[prefix_len:].lower()
                config[config_key] = self._parse_env_value(value)
        
        return config
    
    def _parse_env_value(self, value: str) -> Union[str, int, float, bool, List]:
        """解析环境变量值"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 列表（逗号分隔）
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # 字符串
        return value