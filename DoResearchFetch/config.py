import os
from datetime import timedelta


class Config:
    """应用配置类"""
    
    # 服务配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API密钥配置
    IEEE_API_KEY = os.getenv('IEEE_API_KEY')
    ELSEVIER_API_KEY = os.getenv('ELSEVIER_API_KEY')
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
    
    # 缓存配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1小时
    
    # 数据源配置
    IEEE_BASE_URL = os.getenv('IEEE_BASE_URL', 'https://ieeexplore.ieee.org')
    ELSEVIER_BASE_URL = os.getenv('ELSEVIER_BASE_URL', 'https://api.elsevier.com')
    DBLP_BASE_URL = os.getenv('DBLP_BASE_URL', 'https://dblp.org/search/publ/api')
    
    # 超时配置
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))  # 30秒
    
    # 重试配置
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', 1))  # 秒
    
    # 默认分页配置
    DEFAULT_LIMIT = int(os.getenv('DEFAULT_LIMIT', 50))
    MAX_LIMIT = int(os.getenv('MAX_LIMIT', 100))
    
    # 并发抓取配置
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 6))
    ABSTRACT_REQUEST_DELAY = float(os.getenv('ABSTRACT_REQUEST_DELAY_MS', '150')) / 1000  # 转换为秒
    ABSTRACT_TIMEOUT = int(os.getenv('ABSTRACT_TIMEOUT_SECONDS', 15))
    ENABLE_PARALLEL_ABSTRACT = os.getenv('ENABLE_PARALLEL_ABSTRACT', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    # 使用内存缓存进行测试
    REDIS_URL = None


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}