"""
简单的内存缓存实现
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional
from threading import RLock


class SimpleCache:
    """简单的线程安全内存缓存"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        初始化缓存
        
        Args:
            default_ttl: 默认TTL（秒）
            max_size: 最大缓存条目数
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()
    
    def _generate_key(self, source: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        key_data = f"{source}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, source: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Args:
            source: 数据源名称
            params: 查询参数
            
        Returns:
            缓存的数据，如果不存在或已过期返回None
        """
        key = self._generate_key(source, params)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            cache_entry = self._cache[key]
            
            # 检查是否过期
            if time.time() > cache_entry['expires_at']:
                del self._cache[key]
                return None
            
            # 更新访问时间
            cache_entry['accessed_at'] = time.time()
            return cache_entry['data']
    
    def set(self, source: str, params: Dict[str, Any], data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        设置缓存数据
        
        Args:
            source: 数据源名称
            params: 查询参数
            data: 要缓存的数据
            ttl: TTL（秒），如果不指定则使用默认值
        """
        key = self._generate_key(source, params)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            # 如果缓存已满，删除最旧的条目
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = {
                'data': data,
                'created_at': time.time(),
                'accessed_at': time.time(),
                'expires_at': time.time() + ttl,
                'source': source
            }
    
    def _evict_oldest(self):
        """删除最旧的缓存条目"""
        if not self._cache:
            return
        
        # 找到访问时间最早的条目
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['accessed_at']
        )
        del self._cache[oldest_key]
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def clean_expired(self):
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if current_time > entry['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            current_time = time.time()
            active_count = sum(
                1 for entry in self._cache.values()
                if current_time <= entry['expires_at']
            )
            
            source_counts = {}
            for entry in self._cache.values():
                source = entry['source']
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                'total_entries': len(self._cache),
                'active_entries': active_count,
                'expired_entries': len(self._cache) - active_count,
                'max_size': self.max_size,
                'source_distribution': source_counts,
                'memory_usage_estimate': len(str(self._cache))  # 粗略估计
            }


# 全局缓存实例
cache = SimpleCache(default_ttl=3600, max_size=1000)


def get_cached_result(source: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    获取缓存结果的便捷函数
    
    Args:
        source: 数据源名称
        params: 查询参数
        
    Returns:
        缓存的结果，包含cache_hit标记
    """
    result = cache.get(source, params)
    if result:
        # 标记为缓存命中
        result = result.copy()
        result['cache_hit'] = True
        return result
    return None


def cache_result(source: str, params: Dict[str, Any], result: Dict[str, Any], ttl: Optional[int] = None) -> None:
    """
    缓存结果的便捷函数
    
    Args:
        source: 数据源名称
        params: 查询参数
        result: 要缓存的结果
        ttl: TTL（秒）
    """
    # 确保不缓存cache_hit标记
    result_to_cache = result.copy()
    result_to_cache.pop('cache_hit', None)
    
    cache.set(source, params, result_to_cache, ttl)