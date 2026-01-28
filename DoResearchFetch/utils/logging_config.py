"""
日志和监控配置模块
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any
from flask import request, g
import time


class LogConfig:
    """日志配置类"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用的日志配置"""
        
        # 创建logs目录
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 设置日志级别
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
        
        # 配置根logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建应用logger
        self.setup_app_logger(app, log_level)
        
        # 设置访问日志
        if app.config.get('ENABLE_ACCESS_LOG', True):
            self.setup_access_logger(app)
        
        # 设置错误日志
        if app.config.get('ENABLE_ERROR_LOG', True):
            self.setup_error_logger(app)
        
        # 注册请求钩子
        self.register_request_hooks(app)
    
    def setup_app_logger(self, app, log_level):
        """设置应用日志"""
        app_logger = logging.getLogger('do_research_fetch')
        app_logger.setLevel(log_level)
        
        # 文件处理器
        log_file = app.config.get('LOG_FILE', 'logs/app.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        app_logger.addHandler(file_handler)
        app_logger.addHandler(console_handler)
        
        # 防止重复日志
        app_logger.propagate = False
        
        # 将logger附加到app
        app.logger = app_logger
    
    def setup_access_logger(self, app):
        """设置访问日志"""
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        
        # 访问日志文件处理器
        access_handler = logging.handlers.RotatingFileHandler(
            'logs/access.log',
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        
        # 访问日志格式
        access_formatter = logging.Formatter(
            '%(asctime)s - %(remote_addr)s - "%(method)s %(url)s %(protocol)s" '
            '%(status_code)s %(response_size)s "%(user_agent)s" %(response_time)sms',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        access_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False
        
        # 保存到app
        app.access_logger = access_logger
    
    def setup_error_logger(self, app):
        """设置错误日志"""
        error_logger = logging.getLogger('error')
        error_logger.setLevel(logging.ERROR)
        
        # 错误日志文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/error.log',
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=5
        )
        
        # 错误日志格式
        error_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s\n'
            'Request: %(method)s %(url)s\n'
            'Remote Address: %(remote_addr)s\n'
            'User Agent: %(user_agent)s\n'
            'Request Data: %(request_data)s\n'
            '%(traceback)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        error_handler.setFormatter(error_formatter)
        error_logger.addHandler(error_handler)
        error_logger.propagate = False
        
        # 保存到app
        app.error_logger = error_logger
    
    def register_request_hooks(self, app):
        """注册请求钩子"""
        
        @app.before_request
        def before_request():
            g.start_time = time.time()
            g.request_id = self.generate_request_id()
        
        @app.after_request
        def after_request(response):
            if hasattr(app, 'access_logger') and app.config.get('ENABLE_ACCESS_LOG', True):
                self.log_access(app, response)
            return response
        
        @app.errorhandler(Exception)
        def log_exception(error):
            if hasattr(app, 'error_logger') and app.config.get('ENABLE_ERROR_LOG', True):
                self.log_error(app, error)
            # 重新抛出异常，让Flask处理
            raise error
    
    def generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def log_access(self, app, response):
        """记录访问日志"""
        try:
            response_time = int((time.time() - g.start_time) * 1000)
            
            log_data = {
                'remote_addr': request.remote_addr,
                'method': request.method,
                'url': request.url,
                'protocol': request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1'),
                'status_code': response.status_code,
                'response_size': response.calculate_content_length() or 0,
                'user_agent': request.headers.get('User-Agent', ''),
                'response_time': response_time
            }
            
            app.access_logger.info('', extra=log_data)
            
        except Exception as e:
            app.logger.error(f"Failed to log access: {e}")
    
    def log_error(self, app, error):
        """记录错误日志"""
        try:
            import traceback
            
            log_data = {
                'method': request.method if request else 'N/A',
                'url': request.url if request else 'N/A',
                'remote_addr': request.remote_addr if request else 'N/A',
                'user_agent': request.headers.get('User-Agent', '') if request else 'N/A',
                'request_data': str(request.get_json() if request and request.is_json else ''),
                'traceback': traceback.format_exc()
            }
            
            app.error_logger.error(str(error), extra=log_data)
            
        except Exception as e:
            app.logger.error(f"Failed to log error: {e}")


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.reset_metrics()
    
    def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'response_times': [],
            'source_requests': {},
            'error_types': {},
            'start_time': time.time()
        }
    
    def record_request(self, source: str = None, success: bool = True, response_time: float = 0, error_type: str = None):
        """记录请求指标"""
        self.metrics['requests_total'] += 1
        
        if success:
            self.metrics['requests_success'] += 1
        else:
            self.metrics['requests_error'] += 1
            if error_type:
                self.metrics['error_types'][error_type] = self.metrics['error_types'].get(error_type, 0) + 1
        
        if response_time > 0:
            self.metrics['response_times'].append(response_time)
            # 只保留最近1000个响应时间
            if len(self.metrics['response_times']) > 1000:
                self.metrics['response_times'] = self.metrics['response_times'][-1000:]
        
        if source:
            self.metrics['source_requests'][source] = self.metrics['source_requests'].get(source, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        uptime = time.time() - self.metrics['start_time']
        
        response_times = self.metrics['response_times']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        success_rate = (self.metrics['requests_success'] / self.metrics['requests_total']) * 100 if self.metrics['requests_total'] > 0 else 0
        
        return {
            'uptime_seconds': int(uptime),
            'requests_total': self.metrics['requests_total'],
            'requests_success': self.metrics['requests_success'],
            'requests_error': self.metrics['requests_error'],
            'success_rate_percent': round(success_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'source_requests': self.metrics['source_requests'],
            'error_types': self.metrics['error_types'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


# 全局指标收集器实例
metrics_collector = MetricsCollector()


def log_api_call(source: str, params: dict, success: bool, response_time: float, papers_count: int = 0, error: str = None):
    """记录API调用日志"""
    logger = logging.getLogger('do_research_fetch')
    
    log_data = {
        'source': source,
        'params': params,
        'success': success,
        'response_time_ms': int(response_time * 1000),
        'papers_count': papers_count,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if success:
        logger.info(f"API call successful: {source}", extra=log_data)
    else:
        log_data['error'] = error
        logger.error(f"API call failed: {source} - {error}", extra=log_data)
    
    # 记录指标
    metrics_collector.record_request(
        source=source,
        success=success,
        response_time=response_time * 1000,  # 转换为毫秒
        error_type=type(error).__name__ if error else None
    )