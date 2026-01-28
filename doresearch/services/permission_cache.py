"""
权限验证缓存服务
用于缓存用户权限验证结果，减少重复的数据库查询
"""
import time
from typing import Optional, Dict, Any
from functools import lru_cache


class PermissionCache:
    """简单的内存权限缓存"""
    
    def __init__(self, ttl: int = 300):  # 5分钟TTL
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_cache_key(self, user_id: int, resource_type: str, resource_id: int) -> str:
        """生成缓存键"""
        return f"perm:{user_id}:{resource_type}:{resource_id}"
    
    def get(self, user_id: int, resource_type: str, resource_id: int) -> Optional[Any]:
        """获取缓存的权限验证结果"""
        key = self._get_cache_key(user_id, resource_type, resource_id)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['result']
            else:
                # 过期删除
                del self.cache[key]
        
        return None
    
    def set(self, user_id: int, resource_type: str, resource_id: int, result: Any):
        """设置权限验证结果缓存"""
        key = self._get_cache_key(user_id, resource_type, resource_id)
        self.cache[key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def invalidate(self, user_id: int, resource_type: str = None, resource_id: int = None):
        """清除指定用户或资源的缓存"""
        if resource_type and resource_id:
            # 清除特定资源的缓存
            key = self._get_cache_key(user_id, resource_type, resource_id)
            if key in self.cache:
                del self.cache[key]
        else:
            # 清除用户所有缓存
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(f"perm:{user_id}:")]
            for key in keys_to_delete:
                del self.cache[key]
    
    def clear_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        keys_to_delete = []
        
        for key, entry in self.cache.items():
            if current_time - entry['timestamp'] >= self.ttl:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for entry in self.cache.values():
            if current_time - entry['timestamp'] < self.ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'ttl_seconds': self.ttl
        }


# 全局权限缓存实例
permission_cache = PermissionCache(ttl=300)  # 5分钟缓存


def cached_permission_check(user_id: int, resource_type: str, resource_id: int, check_func):
    """
    带缓存的权限检查装饰器函数
    
    Args:
        user_id: 用户ID
        resource_type: 资源类型 ('subscription', 'feed', 'paper')
        resource_id: 资源ID
        check_func: 实际的权限检查函数
    
    Returns:
        权限检查结果
    """
    # 先检查缓存
    cached_result = permission_cache.get(user_id, resource_type, resource_id)
    if cached_result is not None:
        return cached_result
    
    # 缓存未命中，执行实际检查
    result = check_func()
    
    # 缓存结果（只缓存成功的结果）
    if result:
        permission_cache.set(user_id, resource_type, resource_id, result)
    
    return result


def invalidate_user_permissions(user_id: int):
    """清除用户所有权限缓存（用于用户权限变更时）"""
    permission_cache.invalidate(user_id)


def invalidate_resource_permissions(resource_type: str, resource_id: int):
    """清除特定资源的权限缓存（用于资源变更时）"""
    # 清除所有用户对该资源的权限缓存
    keys_to_delete = []
    for key in permission_cache.cache.keys():
        if key.endswith(f":{resource_type}:{resource_id}"):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        if key in permission_cache.cache:
            del permission_cache.cache[key]