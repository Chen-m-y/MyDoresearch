"""
DoResearch 项目的统一日志系统
提供结构化日志记录和监控功能
"""
import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from enum import Enum
import threading
import traceback
from contextvars import ContextVar

from common.types import LogLevel
from common.exceptions import DoResearchError


# 上下文变量用于跟踪请求ID
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class LogFormat(Enum):
    """日志格式枚举"""
    JSON = "json"
    TEXT = "text"
    COLORED = "colored"


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, config: Optional['LoggingConfig'] = None):
        self.name = name
        self.config = config or LoggingConfig()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        self.logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 添加控制台处理器
        if self.config.console_enabled:
            console_handler = self._create_console_handler()
            self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        if self.config.file_enabled and self.config.log_dir:
            file_handler = self._create_file_handler()
            self.logger.addHandler(file_handler)
        
        # 添加错误文件处理器
        if self.config.error_file_enabled and self.config.log_dir:
            error_handler = self._create_error_handler()
            self.logger.addHandler(error_handler)
        
        # 防止重复日志
        self.logger.propagate = False
    
    def _create_console_handler(self) -> logging.Handler:
        """创建控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        
        if self.config.format == LogFormat.JSON:
            formatter = JSONFormatter()
        elif self.config.format == LogFormat.COLORED:
            formatter = ColoredFormatter()
        else:
            formatter = StandardFormatter()
        
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config.console_level.upper()))
        return handler
    
    def _create_file_handler(self) -> logging.handlers.RotatingFileHandler:
        """创建文件处理器"""
        log_file = Path(self.config.log_dir) / f"{self.name}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        formatter = JSONFormatter() if self.config.format == LogFormat.JSON else StandardFormatter()
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config.file_level.upper()))
        return handler
    
    def _create_error_handler(self) -> logging.handlers.RotatingFileHandler:
        """创建错误文件处理器"""
        error_file = Path(self.config.log_dir) / f"{self.name}_error.log"
        error_file.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(error_file),
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)
        return handler
    
    def _get_context_data(self) -> Dict[str, Any]:
        """获取上下文数据"""
        context = {}
        
        request_id = request_id_context.get()
        if request_id:
            context['request_id'] = request_id
        
        user_id = user_id_context.get()
        if user_id:
            context['user_id'] = user_id
        
        context['thread_id'] = threading.get_ident()
        context['thread_name'] = threading.current_thread().name
        
        return context
    
    def _log(self, level: str, message: str, **kwargs):
        """内部日志方法"""
        extra_data = {
            'logger_name': self.name,
            'context': self._get_context_data(),
            **kwargs
        }
        
        # 处理异常信息
        if 'exc_info' in kwargs and kwargs['exc_info']:
            extra_data['traceback'] = traceback.format_exc()
        
        self.logger.log(
            level=getattr(logging, level.upper()),
            msg=message,
            extra=extra_data
        )
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self._log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self._log('ERROR', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._log('CRITICAL', message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """异常日志（自动包含异常信息）"""
        kwargs['exc_info'] = True
        self._log('ERROR', message, **kwargs)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """记录异常"""
        if isinstance(error, DoResearchError):
            self.error(
                message=error.message,
                error_code=error.error_code.value,
                error_context=error.context,
                additional_context=context,
                exc_info=True
            )
        else:
            self.error(
                message=str(error),
                error_type=type(error).__name__,
                additional_context=context,
                exc_info=True
            )
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """记录性能信息"""
        self.info(
            message=f"Performance: {operation}",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_business_event(self, event: str, entity_type: str, entity_id: Any, **kwargs):
        """记录业务事件"""
        self.info(
            message=f"Business Event: {event}",
            event=event,
            entity_type=entity_type,
            entity_id=str(entity_id),
            **kwargs
        )


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外数据
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # 添加其他自定义字段
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'stack_info', 'exc_info',
                          'exc_text', 'context', 'logger_name'):
                log_data[key] = value
        
        # 处理异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class StandardFormatter(logging.Formatter):
    """标准文本格式化器"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        record.levelname = f"{color}{record.levelname}{reset}"
        record.name = f"\033[34m{record.name}{reset}"  # 蓝色
        
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        return formatter.format(record)


class LoggingConfig:
    """日志配置类"""
    
    def __init__(
        self,
        level: str = "INFO",
        format: LogFormat = LogFormat.JSON,
        console_enabled: bool = True,
        console_level: str = "INFO",
        file_enabled: bool = True,
        file_level: str = "DEBUG",
        error_file_enabled: bool = True,
        log_dir: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.level = level
        self.format = format
        self.console_enabled = console_enabled
        self.console_level = console_level
        self.file_enabled = file_enabled
        self.file_level = file_level
        self.error_file_enabled = error_file_enabled
        self.log_dir = log_dir or "data/logs"
        self.max_file_size = max_file_size
        self.backup_count = backup_count


# 全局日志配置
_global_config: Optional[LoggingConfig] = None
_loggers: Dict[str, StructuredLogger] = {}
_lock = threading.Lock()


def setup_logging(config: LoggingConfig):
    """设置全局日志配置"""
    global _global_config
    _global_config = config
    
    # 设置根日志记录器
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # 为现有记录器应用新配置
    with _lock:
        for logger in _loggers.values():
            logger.config = config
            logger._setup_logger()


def get_logger(name: str) -> StructuredLogger:
    """获取日志记录器"""
    with _lock:
        if name not in _loggers:
            _loggers[name] = StructuredLogger(name, _global_config)
        return _loggers[name]


def set_request_context(request_id: str, user_id: Optional[str] = None):
    """设置请求上下文"""
    request_id_context.set(request_id)
    if user_id:
        user_id_context.set(user_id)


def clear_request_context():
    """清除请求上下文"""
    request_id_context.set(None)
    user_id_context.set(None)


# 性能监控装饰器
def log_performance(logger_name: str = "performance"):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.log_performance(
                    operation=f"{func.__module__}.{func.__name__}",
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.log_performance(
                    operation=f"{func.__module__}.{func.__name__}",
                    duration=duration,
                    success=False,
                    error=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


# 错误记录装饰器
def log_errors(logger_name: str = "errors"):
    """错误记录装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log_error(
                    error=e,
                    context={
                        "function": f"{func.__module__}.{func.__name__}",
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
                raise
        
        return wrapper
    return decorator


# 业务事件记录工具
class BusinessEventLogger:
    """业务事件日志记录器"""
    
    def __init__(self, logger_name: str = "business_events"):
        self.logger = get_logger(logger_name)
    
    def paper_created(self, paper_id: int, feed_id: int, title: str):
        """记录论文创建事件"""
        self.logger.log_business_event(
            event="paper_created",
            entity_type="paper",
            entity_id=paper_id,
            feed_id=feed_id,
            title=title[:100]
        )
    
    def paper_status_changed(self, paper_id: int, old_status: str, new_status: str):
        """记录论文状态变更事件"""
        self.logger.log_business_event(
            event="paper_status_changed",
            entity_type="paper",
            entity_id=paper_id,
            old_status=old_status,
            new_status=new_status
        )
    
    def feed_updated(self, feed_id: int, new_papers_count: int):
        """记录订阅源更新事件"""
        self.logger.log_business_event(
            event="feed_updated",
            entity_type="feed",
            entity_id=feed_id,
            new_papers_count=new_papers_count
        )
    
    def task_created(self, task_id: str, task_type: str, paper_id: int):
        """记录任务创建事件"""
        self.logger.log_business_event(
            event="task_created",
            entity_type="task",
            entity_id=task_id,
            task_type=task_type,
            paper_id=paper_id
        )
    
    def task_completed(self, task_id: str, duration: float, success: bool):
        """记录任务完成事件"""
        self.logger.log_business_event(
            event="task_completed",
            entity_type="task",
            entity_id=task_id,
            duration=duration,
            success=success
        )