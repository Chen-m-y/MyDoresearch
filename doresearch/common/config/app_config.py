"""
应用配置定义模块
"""
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

from common.exceptions import ValidationError, ConfigurationError
from .types import Environment
from .manager import ConfigManager


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "papers.db"
    max_connections: int = 10
    connection_timeout: int = 300
    check_interval: int = 60


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    console_enabled: bool = True
    file_enabled: bool = True
    log_dir: str = "data/logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class APIConfig:
    """API配置"""
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com/chat/completions"
    request_timeout: int = 60
    max_retries: int = 3


@dataclass
class TaskConfig:
    """任务配置"""
    check_interval: int = 5
    agent_heartbeat_timeout: int = 300
    max_concurrent_tasks: int = 10


@dataclass
class AppConfig:
    """主应用配置"""
    # 应用基础配置
    secret_key: str = "dev-secret-key-change-in-production"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    environment: Environment = Environment.DEVELOPMENT
    
    # 文件系统配置
    data_dir: str = "data"
    pdf_dir: str = "data/pdfs"
    
    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()
    api: APIConfig = APIConfig()
    task: TaskConfig = TaskConfig()
    
    def __post_init__(self):
        """后处理初始化"""
        # 确保目录存在
        Path(self.data_dir).mkdir(exist_ok=True)
        Path(self.pdf_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logging.log_dir).mkdir(parents=True, exist_ok=True)
    
    def validate(self):
        """验证配置"""
        errors = []
        
        # 验证必需的API密钥
        if self.environment == Environment.PRODUCTION and not self.api.deepseek_api_key:
            errors.append(ValidationError(
                field="api.deepseek_api_key",
                message="DeepSeek API key is required in production"
            ))
        
        # 验证端口范围
        if not (1 <= self.port <= 65535):
            errors.append(ValidationError(
                field="port",
                message="Port must be between 1 and 65535",
                value=self.port
            ))
        
        if errors:
            from common.exceptions import MultipleValidationErrors
            raise MultipleValidationErrors(errors)


# 全局配置实例
_app_config: Optional[AppConfig] = None
_config_manager: Optional[ConfigManager] = None


def load_app_config(
    config_files: Optional[List[str]] = None,
    environment: Environment = Environment.DEVELOPMENT,
    config_dir: Optional[str] = None
) -> AppConfig:
    """加载应用配置"""
    global _app_config, _config_manager
    
    _config_manager = ConfigManager(AppConfig, config_dir)
    
    # 默认配置文件
    if config_files is None:
        config_files = [
            "config.yaml",
            "config.yml",
            "config.json",
            f"config.{environment.value}.yaml",
            f"config.{environment.value}.yml",
            f"config.{environment.value}.json"
        ]
    
    _app_config = _config_manager.load_config(config_files, environment)
    _app_config.validate()
    
    return _app_config


def get_app_config() -> AppConfig:
    """获取应用配置"""
    if _app_config is None:
        raise ConfigurationError(
            message="App config not loaded. Call load_app_config() first."
        )
    return _app_config


def reload_config():
    """重新加载配置"""
    global _app_config
    if _config_manager:
        _app_config = _config_manager.load_config()
        _app_config.validate()
    else:
        raise ConfigurationError(
            message="Config manager not initialized"
        )