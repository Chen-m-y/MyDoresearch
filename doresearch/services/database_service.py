"""
数据库服务层 - 统一连接池管理和查询优化
解决数据库连接重复创建和查询性能问题
"""
import sqlite3
import threading
import time
from typing import Optional, Dict, List, Any, Union
from contextlib import contextmanager
from queue import Queue, Empty
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接包装器"""
    
    def __init__(self, connection: sqlite3.Connection, pool: 'ConnectionPool'):
        self.connection = connection
        self.pool = pool
        self.in_use = True
        self.created_at = time.time()
        self.last_used = time.time()
    
    def __enter__(self):
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.return_connection(self)


class ConnectionPool:
    """SQLite连接池"""
    
    def __init__(self, db_path: str, max_connections: int = 10, 
                 connection_timeout: int = 300, check_interval: int = 60):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.check_interval = check_interval
        
        self._pool = Queue(maxsize=max_connections)
        self._active_connections = {}
        self._lock = threading.RLock()
        self._closed = False
        
        # 启动连接清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_connections, daemon=True)
        self._cleanup_thread.start()
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建新的数据库连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        
        # 优化SQLite设置
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA cache_size=10000')
        conn.execute('PRAGMA temp_store=MEMORY')
        conn.execute('PRAGMA mmap_size=268435456')  # 256MB
        conn.execute('PRAGMA foreign_keys=ON')
        
        return conn
    
    def get_connection(self, timeout: float = 5.0) -> DatabaseConnection:
        """获取数据库连接"""
        if self._closed:
            raise RuntimeError("连接池已关闭")
        
        start_time = time.time()
        
        with self._lock:
            # 首先尝试从池中获取连接
            try:
                while time.time() - start_time < timeout:
                    try:
                        conn_wrapper = self._pool.get_nowait()
                        if self._is_connection_valid(conn_wrapper.connection):
                            conn_wrapper.in_use = True
                            conn_wrapper.last_used = time.time()
                            thread_id = threading.get_ident()
                            self._active_connections[thread_id] = conn_wrapper
                            return conn_wrapper
                        else:
                            # 连接无效，关闭并创建新的
                            conn_wrapper.connection.close()
                    except Empty:
                        break
            except Exception as e:
                logger.error(f"从连接池获取连接失败: {e}")
            
            # 如果池中没有可用连接，创建新连接
            if len(self._active_connections) < self.max_connections:
                try:
                    conn = self._create_connection()
                    conn_wrapper = DatabaseConnection(conn, self)
                    thread_id = threading.get_ident()
                    self._active_connections[thread_id] = conn_wrapper
                    return conn_wrapper
                except Exception as e:
                    logger.error(f"创建新数据库连接失败: {e}")
                    raise
            
            raise RuntimeError(f"无法在{timeout}秒内获取数据库连接")
    
    def return_connection(self, conn_wrapper: DatabaseConnection):
        """归还连接到池中"""
        if self._closed:
            conn_wrapper.connection.close()
            return
        
        with self._lock:
            thread_id = threading.get_ident()
            if thread_id in self._active_connections:
                del self._active_connections[thread_id]
            
            conn_wrapper.in_use = False
            conn_wrapper.last_used = time.time()
            
            if self._is_connection_valid(conn_wrapper.connection):
                try:
                    self._pool.put_nowait(conn_wrapper)
                except:
                    # 池已满，关闭连接
                    conn_wrapper.connection.close()
            else:
                conn_wrapper.connection.close()
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """检查连接是否有效"""
        try:
            conn.execute('SELECT 1')
            return True
        except:
            return False
    
    def _cleanup_connections(self):
        """清理过期连接"""
        while not self._closed:
            try:
                time.sleep(self.check_interval)
                current_time = time.time()
                
                with self._lock:
                    # 清理池中的过期连接
                    expired_connections = []
                    while not self._pool.empty():
                        try:
                            conn_wrapper = self._pool.get_nowait()
                            if current_time - conn_wrapper.last_used > self.connection_timeout:
                                expired_connections.append(conn_wrapper)
                            else:
                                self._pool.put_nowait(conn_wrapper)
                        except Empty:
                            break
                    
                    for conn_wrapper in expired_connections:
                        conn_wrapper.connection.close()
                    
                    if expired_connections:
                        logger.info(f"清理了{len(expired_connections)}个过期数据库连接")
                        
            except Exception as e:
                logger.error(f"清理数据库连接时出错: {e}")
    
    def close(self):
        """关闭连接池"""
        self._closed = True
        
        with self._lock:
            # 关闭所有活跃连接
            for conn_wrapper in self._active_connections.values():
                try:
                    conn_wrapper.connection.close()
                except:
                    pass
            self._active_connections.clear()
            
            # 关闭池中的连接
            while not self._pool.empty():
                try:
                    conn_wrapper = self._pool.get_nowait()
                    conn_wrapper.connection.close()
                except Empty:
                    break
    
    def get_stats(self) -> Dict:
        """获取连接池统计信息"""
        with self._lock:
            return {
                'active_connections': len(self._active_connections),
                'pool_size': self._pool.qsize(),
                'max_connections': self.max_connections,
                'total_created': len(self._active_connections) + self._pool.qsize()
            }


class DatabaseService:
    """统一数据库服务"""
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self._pool = ConnectionPool(db_path, max_connections)
        self._query_cache = {}
        self._cache_lock = threading.RLock()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn_wrapper = self._pool.get_connection()
        try:
            yield conn_wrapper.connection
        finally:
            self._pool.return_connection(conn_wrapper)
    
    def execute_query(self, query: str, params: tuple = None, 
                     fetch_one: bool = False, fetch_all: bool = True) -> Union[Dict, List[Dict], None]:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                return None
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作并返回受影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """执行插入操作并返回新插入的ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
    
    def execute_batch(self, query: str, param_list: List[tuple]) -> int:
        """批量执行操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            conn.commit()
            return cursor.rowcount
    
    def get_cached_query(self, cache_key: str, query: str, params: tuple = None, 
                        cache_duration: int = 300) -> List[Dict]:
        """执行带缓存的查询"""
        with self._cache_lock:
            current_time = time.time()
            
            # 检查缓存
            if cache_key in self._query_cache:
                cached_data, cached_time = self._query_cache[cache_key]
                if current_time - cached_time < cache_duration:
                    return cached_data
            
            # 执行查询
            result = self.execute_query(query, params, fetch_all=True)
            
            # 更新缓存
            self._query_cache[cache_key] = (result, current_time)
            return result
    
    def clear_cache(self, cache_key: str = None):
        """清理查询缓存"""
        with self._cache_lock:
            if cache_key:
                self._query_cache.pop(cache_key, None)
            else:
                self._query_cache.clear()
    
    def get_statistics(self) -> Dict:
        """获取数据库服务统计信息"""
        pool_stats = self._pool.get_stats()
        
        with self._cache_lock:
            cache_stats = {
                'cache_size': len(self._query_cache),
                'cached_queries': list(self._query_cache.keys())
            }
        
        return {
            'connection_pool': pool_stats,
            'query_cache': cache_stats
        }
    
    def close(self):
        """关闭数据库服务"""
        self._pool.close()
        self.clear_cache()


# 全局数据库服务实例
_db_service = None
_db_service_lock = threading.Lock()


def get_database_service(db_path: str = None) -> DatabaseService:
    """获取全局数据库服务实例"""
    global _db_service
    
    if _db_service is None:
        with _db_service_lock:
            if _db_service is None:
                from config import DATABASE_PATH
                _db_service = DatabaseService(db_path or DATABASE_PATH)
    
    return _db_service


def close_database_service():
    """关闭全局数据库服务"""
    global _db_service
    
    if _db_service:
        with _db_service_lock:
            if _db_service:
                _db_service.close()
                _db_service = None