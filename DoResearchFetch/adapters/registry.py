"""
适配器注册器
管理所有数据源适配器的注册和获取
"""

from typing import Dict, Optional
from .base import BaseAdapter


class SourceRegistry:
    """数据源适配器注册器"""
    
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """初始化所有适配器"""
        from config import Config

        # IEEE适配器
        try:
            from .ieee_adapter import IEEEAdapter
            ieee_config = {
                'base_url': Config.IEEE_BASE_URL,
                'api_key': Config.IEEE_API_KEY,
                'timeout': Config.REQUEST_TIMEOUT,
                'max_retries': Config.MAX_RETRIES
            }
            self.register('ieee', IEEEAdapter(ieee_config))
        except ImportError:
            print("Warning: IEEE adapter not available")

        # Elsevier适配器（预留）
        try:
            from .elsevier_adapter import ElsevierAdapter
            elsevier_config = {
                'base_url': Config.ELSEVIER_BASE_URL,
                'api_key': Config.ELSEVIER_API_KEY,
                'timeout': Config.REQUEST_TIMEOUT,
                'max_retries': Config.MAX_RETRIES
            }
            self.register('elsevier', ElsevierAdapter(elsevier_config))
        except ImportError:
            print("Warning: Elsevier adapter not available")

        # DBLP适配器（预留）
        try:
            from .dblp_adapter import DBLPAdapter
            dblp_config = {
                'base_url': Config.DBLP_BASE_URL,
                'timeout': Config.REQUEST_TIMEOUT,
                'max_retries': Config.MAX_RETRIES
            }
            self.register('dblp', DBLPAdapter(dblp_config))
        except ImportError:
            print("Warning: DBLP adapter not available")

        # 新闻适配器

        # 科技部适配器
        try:
            from .most_adapter import MOSTAdapter
            most_config = {
                'base_url': 'https://service.most.gov.cn',
                'timeout': Config.REQUEST_TIMEOUT,
                'max_retries': Config.MAX_RETRIES
            }
            self.register('most', MOSTAdapter(most_config))
            print("✅ MOST (科技部) news adapter registered")
        except ImportError as e:
            print(f"Warning: MOST adapter not available: {e}")
        except Exception as e:
            print(f"Error initializing MOST adapter: {e}")

        # 自然科学基金委适配器
        try:
            from .nsfc_adapter import NSFCAdapter
            nsfc_config = {
                'base_url': 'https://www.nsfc.gov.cn',
                'timeout': Config.REQUEST_TIMEOUT,
                'max_retries': Config.MAX_RETRIES
            }
            self.register('nsfc', NSFCAdapter(nsfc_config))
            print("✅ NSFC (基金委) news adapter registered")
        except ImportError as e:
            print(f"Warning: NSFC adapter not available: {e}")
        except Exception as e:
            print(f"Error initializing NSFC adapter: {e}")
    
    def register(self, name: str, adapter: BaseAdapter):
        """
        注册适配器
        
        Args:
            name: 适配器名称
            adapter: 适配器实例
        """
        self._adapters[name] = adapter
    
    def get_adapter(self, name: str) -> Optional[BaseAdapter]:
        """
        获取适配器
        
        Args:
            name: 适配器名称
            
        Returns:
            适配器实例，如果不存在返回None
        """
        return self._adapters.get(name)
    
    def list_sources(self) -> Dict[str, BaseAdapter]:
        """
        列出所有已注册的适配器
        
        Returns:
            适配器字典 {name: adapter}
        """
        return self._adapters.copy()
    
    def is_source_supported(self, name: str) -> bool:
        """
        检查是否支持指定的数据源
        
        Args:
            name: 数据源名称
            
        Returns:
            是否支持
        """
        return name in self._adapters