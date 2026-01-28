"""
配置管理器模块
"""
from typing import Dict, Any, Optional, Type, TypeVar, List, get_type_hints
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Union

from common.exceptions import ConfigurationError
from common.logging import get_logger
from .types import Environment, ConfigField
from .loaders import JSONConfigLoader, YAMLConfigLoader, EnvironmentConfigLoader
from .validator import ConfigValidator

T = TypeVar('T')


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_class: Type[T], config_dir: Optional[str] = None):
        self.config_class = config_class
        self.config_dir = Path(config_dir) if config_dir else Path.cwd()
        self.logger = get_logger(f"{__name__}.ConfigManager")
        
        # 初始化加载器
        self.loaders = [
            JSONConfigLoader(),
            YAMLConfigLoader(),
            EnvironmentConfigLoader()
        ]
        
        self.validator = ConfigValidator()
        self._config_fields = self._extract_config_fields()
    
    def _extract_config_fields(self) -> Dict[str, ConfigField]:
        """提取配置字段信息"""
        fields_dict = {}
        
        if is_dataclass(self.config_class):
            type_hints = get_type_hints(self.config_class)
            dataclass_fields = fields(self.config_class)
            
            for field in dataclass_fields:
                field_type = type_hints.get(field.name, str)
                
                # 检查是否为Optional类型
                is_optional = (
                    hasattr(field_type, '__origin__') and 
                    field_type.__origin__ is Union and
                    type(None) in field_type.__args__
                )
                
                # 从字段元数据中获取额外信息
                metadata = getattr(field, 'metadata', {})
                env_var = metadata.get('env_var')
                description = metadata.get('description')
                validator = metadata.get('validator')
                
                from dataclasses import MISSING
                fields_dict[field.name] = ConfigField(
                    name=field.name,
                    type=field_type,
                    default=field.default if field.default != MISSING else None,
                    required=not is_optional and field.default == MISSING,
                    env_var=env_var,
                    description=description,
                    validator=validator
                )
        
        return fields_dict
    
    def load_config(self, config_files: Optional[List[str]] = None, 
                   environment: Environment = Environment.DEVELOPMENT) -> T:
        """加载配置"""
        self.logger.info(f"Loading configuration for {environment.value} environment")
        
        # 合并配置数据
        merged_config = {}
        
        # 1. 加载默认配置
        default_config = self._get_default_config()
        merged_config.update(default_config)
        self.logger.debug(f"Loaded default config: {len(default_config)} fields")
        
        # 2. 加载文件配置
        if config_files:
            for config_file in config_files:
                file_config = self._load_config_file(config_file)
                merged_config.update(file_config)
                self.logger.debug(f"Loaded config from {config_file}: {len(file_config)} fields")
        
        # 3. 加载环境变量配置
        env_config = self._load_environment_config()
        merged_config.update(env_config)
        self.logger.debug(f"Loaded environment config: {len(env_config)} fields")
        
        # 4. 验证和构建配置对象
        validated_config = self._validate_config(merged_config)
        
        try:
            config_instance = self.config_class(**validated_config)
            self.logger.info("Configuration loaded successfully")
            return config_instance
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to create config instance: {str(e)}"
            ) from e
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        defaults = {}
        for field_name, field_info in self._config_fields.items():
            if field_info.default is not None:
                defaults[field_name] = field_info.default
        return defaults
    
    def _load_config_file(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        file_path = self.config_dir / config_file
        
        if not file_path.exists():
            self.logger.warning(f"Config file not found: {file_path}")
            return {}
        
        for loader in self.loaders:
            if loader.can_load(str(file_path)):
                return loader.load(str(file_path))
        
        raise ConfigurationError(
            message=f"No loader available for config file: {config_file}",
            config_key=config_file
        )
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """加载环境变量配置"""
        env_loader = EnvironmentConfigLoader()
        return env_loader.load("environment")
    
    def _validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置数据"""
        validated = {}
        
        for field_name, field_info in self._config_fields.items():
            value = config_data.get(field_name)
            
            try:
                validated[field_name] = self.validator.validate_field(field_info, value)
            except ValidationError as e:
                self.logger.error(f"Validation failed for field {field_name}: {e.message}")
                raise
        
        return validated