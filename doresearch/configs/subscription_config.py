"""
新订阅管理系统配置
外部微服务连接配置和相关设置
"""
import os
from typing import Dict, Any

# 外部微服务配置 - 从主配置文件导入
try:
    from config import EXTERNAL_SERVICE_CONFIG
except ImportError:
    # 如果主配置文件不存在，使用环境变量默认值
    EXTERNAL_SERVICE_CONFIG = {
        'base_url': os.getenv('PAPER_FETCHER_SERVICE_URL', 'http://localhost:8000'),
        'timeout': int(os.getenv('PAPER_FETCHER_TIMEOUT', '30')),
        'api_version': 'v1',
        'retry_attempts': int(os.getenv('PAPER_FETCHER_RETRY', '3')),
        'retry_delay': float(os.getenv('PAPER_FETCHER_RETRY_DELAY', '2.0')),
    }

# 同步服务配置
SYNC_SERVICE_CONFIG = {
    'check_interval': int(os.getenv('SYNC_CHECK_INTERVAL', '60')),  # 秒
    'batch_size': int(os.getenv('SYNC_BATCH_SIZE', '10')),         # 每次处理的订阅数量
    'max_retry_attempts': int(os.getenv('SYNC_MAX_RETRY', '3')),   # 最大重试次数
    'default_sync_frequency': int(os.getenv('DEFAULT_SYNC_FREQ', '86400')),  # 默认同步频率(24小时)
}

# 订阅限制配置
SUBSCRIPTION_LIMITS = {
    'max_subscriptions_per_user': int(os.getenv('MAX_SUBSCRIPTIONS_PER_USER', '50')),
    'max_sync_frequency': int(os.getenv('MAX_SYNC_FREQUENCY', '3600')),      # 最快1小时
    'min_sync_frequency': int(os.getenv('MIN_SYNC_FREQUENCY', '86400')),     # 最慢24小时
}

# 参数验证配置
VALIDATION_CONFIG = {
    'strict_mode': os.getenv('VALIDATION_STRICT_MODE', 'true').lower() == 'true',
    'allow_additional_properties': os.getenv('ALLOW_ADDITIONAL_PROPERTIES', 'false').lower() == 'true',
}

# 日志配置
LOGGING_CONFIG = {
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_sync_details': os.getenv('LOG_SYNC_DETAILS', 'true').lower() == 'true',
    'log_external_requests': os.getenv('LOG_EXTERNAL_REQUESTS', 'false').lower() == 'true',
}

def get_external_service_config() -> Dict[str, Any]:
    """获取外部服务配置"""
    return EXTERNAL_SERVICE_CONFIG.copy()

def get_sync_service_config() -> Dict[str, Any]:
    """获取同步服务配置"""
    return SYNC_SERVICE_CONFIG.copy()

def get_subscription_limits() -> Dict[str, Any]:
    """获取订阅限制配置"""
    return SUBSCRIPTION_LIMITS.copy()

def get_validation_config() -> Dict[str, Any]:
    """获取验证配置"""
    return VALIDATION_CONFIG.copy()

def get_logging_config() -> Dict[str, Any]:
    """获取日志配置"""
    return LOGGING_CONFIG.copy()

# 预定义的源类型配置
SOURCE_TYPE_CONFIGS = {
    'ieee': {
        'display_name': 'IEEE期刊',
        'description': 'IEEE数据库期刊论文',
        'recommended_sync_frequency': 86400,  # 24小时
        'parameter_hints': {
            'pnumber': '期刊的Publication Number，可在IEEE官网找到'
        }
    },
    'elsevier': {
        'display_name': 'Elsevier期刊',
        'description': 'Elsevier出版社期刊论文',
        'recommended_sync_frequency': 86400,  # 24小时
        'parameter_hints': {
            'pnumber': '期刊的ISSN或期刊标识符'
        }
    },
    'dblp': {
        'display_name': 'DBLP会议',
        'description': 'DBLP数据库会议论文',
        'recommended_sync_frequency': 604800,  # 7天（会议论文更新较少）
        'parameter_hints': {
            'dblp_id': '会议在DBLP中的标识符，如icse、nips等',
            'year': '会议年份'
        }
    }
}

def get_source_type_config(source_type: str) -> Dict[str, Any]:
    """获取特定源类型的配置"""
    return SOURCE_TYPE_CONFIGS.get(source_type, {})

def get_all_source_types() -> Dict[str, Dict[str, Any]]:
    """获取所有源类型配置"""
    return SOURCE_TYPE_CONFIGS.copy()