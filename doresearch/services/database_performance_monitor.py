"""
数据库性能监控服务
监控查询性能、连接池状态和系统资源使用
"""
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from contextlib import contextmanager
from services.database_service import get_database_service
import logging

logger = logging.getLogger(__name__)


class QueryProfiler:
    """查询性能分析器"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_queries = []
        self.lock = threading.RLock()
        self.slow_query_threshold = 1.0  # 1秒
    
    @contextmanager
    def profile_query(self, query: str, params: tuple = None):
        """查询性能分析上下文管理器"""
        start_time = time.time()
        query_key = self._normalize_query(query)
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._record_query_stats(query_key, duration, query, params)
    
    def _normalize_query(self, query: str) -> str:
        """标准化查询语句（去除参数，保留结构）"""
        # 简单的查询标准化
        normalized = query.strip().upper()
        
        # 替换常见的参数占位符
        import re
        normalized = re.sub(r'\?', 'PARAM', normalized)
        normalized = re.sub(r'\d+', 'NUM', normalized)
        normalized = re.sub(r"'[^']*'", 'STR', normalized)
        
        return normalized[:200]  # 限制长度
    
    def _record_query_stats(self, query_key: str, duration: float, 
                          original_query: str, params: tuple):
        """记录查询统计信息"""
        with self.lock:
            if query_key not in self.query_stats:
                self.query_stats[query_key] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0,
                    'example_query': original_query[:500]
                }
            
            stats = self.query_stats[query_key]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # 记录慢查询
            if duration > self.slow_query_threshold:
                self.slow_queries.append({
                    'query': original_query,
                    'params': str(params) if params else None,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 只保留最近的100个慢查询
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
                
                logger.warning(f"慢查询检测: {duration:.3f}s - {original_query[:200]}")
    
    def get_stats(self) -> Dict:
        """获取查询统计信息"""
        with self.lock:
            # 排序查询统计
            sorted_stats = sorted(
                self.query_stats.items(),
                key=lambda x: x[1]['total_time'],
                reverse=True
            )
            
            return {
                'total_queries': sum(stats['count'] for stats in self.query_stats.values()),
                'unique_queries': len(self.query_stats),
                'slow_queries_count': len(self.slow_queries),
                'top_time_consuming': sorted_stats[:10],
                'recent_slow_queries': self.slow_queries[-10:],
                'stats_by_query': dict(sorted_stats)
            }
    
    def reset_stats(self):
        """重置统计信息"""
        with self.lock:
            self.query_stats.clear()
            self.slow_queries.clear()


class DatabasePerformanceMonitor:
    """数据库性能监控器"""
    
    def __init__(self):
        self.db_service = get_database_service()
        self.profiler = QueryProfiler()
        self.monitoring = False
        self.monitor_thread = None
        self.performance_history = []
        self.lock = threading.RLock()
    
    def start_monitoring(self, interval: int = 60):
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("数据库性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("数据库性能监控已停止")
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集性能数据
                perf_data = self._collect_performance_data()
                
                with self.lock:
                    self.performance_history.append(perf_data)
                    
                    # 只保留最近24小时的数据
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.performance_history = [
                        data for data in self.performance_history
                        if datetime.fromisoformat(data['timestamp']) > cutoff_time
                    ]
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"性能监控出错: {e}")
                time.sleep(interval)
    
    def _collect_performance_data(self) -> Dict:
        """收集性能数据"""
        timestamp = datetime.now().isoformat()
        
        # 获取连接池统计
        db_stats = self.db_service.get_statistics()
        
        # 获取数据库大小
        db_size = self._get_database_size()
        
        # 获取表统计信息
        table_stats = self._get_table_statistics()
        
        # 获取查询统计
        query_stats = self.profiler.get_stats()
        
        return {
            'timestamp': timestamp,
            'connection_pool': db_stats['connection_pool'],
            'query_cache': db_stats['query_cache'],
            'database_size_mb': db_size,
            'table_statistics': table_stats,
            'query_performance': {
                'total_queries': query_stats['total_queries'],
                'slow_queries_count': query_stats['slow_queries_count'],
                'unique_queries': query_stats['unique_queries']
            }
        }
    
    def _get_database_size(self) -> float:
        """获取数据库文件大小（MB）"""
        try:
            import os
            size_bytes = os.path.getsize(self.db_service.db_path)
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0
    
    def _get_table_statistics(self) -> Dict:
        """获取表统计信息"""
        try:
            tables = ['papers', 'feeds', 'tasks', 'agents', 'read_later', 'task_steps']
            stats = {}
            
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                for table in tables:
                    try:
                        # 获取行数
                        cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                        count = cursor.fetchone()['count']
                        
                        # 获取表页数（近似大小）
                        cursor.execute(f'PRAGMA table_info({table})')
                        columns = len(cursor.fetchall())
                        
                        stats[table] = {
                            'row_count': count,
                            'column_count': columns
                        }
                    except Exception as e:
                        stats[table] = {'error': str(e)}
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        with self.lock:
            current_stats = self.db_service.get_statistics()
            query_stats = self.profiler.get_stats()
            
            # 计算趋势（如果有历史数据）
            trends = {}
            if len(self.performance_history) >= 2:
                recent = self.performance_history[-1]
                previous = self.performance_history[-2]
                
                trends = {
                    'database_size_trend': recent['database_size_mb'] - previous['database_size_mb'],
                    'query_count_trend': recent['query_performance']['total_queries'] - previous['query_performance']['total_queries']
                }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'connection_pool_status': current_stats['connection_pool'],
                'query_cache_status': current_stats['query_cache'],
                'query_performance': query_stats,
                'database_size_mb': self._get_database_size(),
                'table_statistics': self._get_table_statistics(),
                'performance_trends': trends,
                'monitoring_active': self.monitoring,
                'history_points': len(self.performance_history)
            }
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        # 分析查询性能
        query_stats = self.profiler.get_stats()
        
        if query_stats['slow_queries_count'] > 10:
            suggestions.append(f"检测到 {query_stats['slow_queries_count']} 个慢查询，建议优化查询或添加索引")
        
        # 分析连接池状态
        db_stats = self.db_service.get_statistics()
        pool_stats = db_stats['connection_pool']
        
        if pool_stats['active_connections'] == pool_stats['max_connections']:
            suggestions.append("连接池已满，建议增加最大连接数或优化连接使用")
        
        # 分析缓存效果
        cache_stats = db_stats['query_cache']
        if cache_stats['cache_size'] == 0:
            suggestions.append("查询缓存为空，建议启用查询缓存以提高性能")
        
        # 分析数据库大小
        db_size = self._get_database_size()
        if db_size > 100:  # 超过100MB
            suggestions.append(f"数据库大小为 {db_size}MB，建议考虑数据归档或分表")
        
        return suggestions
    
    def execute_with_profiling(self, func: Callable, query: str, params: tuple = None):
        """执行带性能分析的数据库操作"""
        with self.profiler.profile_query(query, params):
            return func()


# 全局性能监控实例
_performance_monitor = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> DatabasePerformanceMonitor:
    """获取全局性能监控实例"""
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = DatabasePerformanceMonitor()
    
    return _performance_monitor


def start_performance_monitoring(interval: int = 60):
    """启动性能监控"""
    monitor = get_performance_monitor()
    monitor.start_monitoring(interval)


def stop_performance_monitoring():
    """停止性能监控"""
    global _performance_monitor
    
    if _performance_monitor:
        _performance_monitor.stop_monitoring()


# 装饰器：为数据库操作添加性能监控
def profile_query(query: str):
    """查询性能分析装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.profiler.profile_query(query):
                return func(*args, **kwargs)
        return wrapper
    return decorator