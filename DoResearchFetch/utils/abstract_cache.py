"""
摘要缓存管理器（SQLite版本）
用于存储和管理已抓取的完整摘要，避免重复请求
使用SQLite3数据库提供高性能存储和查询
"""

import sqlite3
import time
import hashlib
import threading
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from contextlib import contextmanager


@dataclass
class AbstractCacheEntry:
    """摘要缓存条目"""
    article_id: str
    url: str
    title: str
    abstract: str
    cached_time: float
    source: str = "ieee"
    abstract_hash: str = ""  # 用于检测摘要变化
    
    def __post_init__(self):
        if not self.abstract_hash and self.abstract:
            self.abstract_hash = hashlib.md5(self.abstract.encode('utf-8')).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'article_id': self.article_id,
            'url': self.url,
            'title': self.title,
            'abstract': self.abstract,
            'cached_time': self.cached_time,
            'source': self.source,
            'abstract_hash': self.abstract_hash
        }


class SQLiteAbstractCache:
    """基于SQLite的摘要缓存管理器"""
    
    def __init__(self, db_file: str = "abstract_cache.db", max_age_days: int = 30):
        """
        初始化SQLite摘要缓存
        
        Args:
            db_file: 数据库文件路径
            max_age_days: 缓存最大保存天数
        """
        self.db_file = Path(db_file)
        self.max_age_seconds = max_age_days * 24 * 3600
        self._lock = threading.RLock()  # 线程安全锁
        
        # 确保数据库目录存在
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库表
        self._init_database()
        
        # 启动时清理过期数据
        self._cleanup_expired()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS abstract_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    abstract_hash TEXT NOT NULL,
                    cached_time REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(article_id, source)
                )
            """)
            
            # 创建索引提高查询性能
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_source 
                ON abstract_cache(article_id, source)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_time 
                ON abstract_cache(cached_time)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source 
                ON abstract_cache(source)
            """)
            
            conn.commit()
            print(f"✓ Abstract cache database initialized: {self.db_file}")
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_file), timeout=30)
        conn.row_factory = sqlite3.Row  # 支持按列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def get(self, article_id: str, source: str = "ieee") -> Optional[str]:
        """
        获取缓存的摘要
        
        Args:
            article_id: 文章ID（如IEEE的文章编号）
            source: 数据源
            
        Returns:
            缓存的摘要文本，如果不存在或过期则返回None
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT abstract, cached_time FROM abstract_cache 
                        WHERE article_id = ? AND source = ?
                    """, (article_id, source))
                    
                    row = cursor.fetchone()
                    if row:
                        abstract, cached_time = row['abstract'], row['cached_time']
                        
                        # 检查是否过期
                        if time.time() - cached_time < self.max_age_seconds:
                            return abstract
                        else:
                            # 删除过期条目
                            conn.execute("""
                                DELETE FROM abstract_cache 
                                WHERE article_id = ? AND source = ?
                            """, (article_id, source))
                            conn.commit()
                            print(f"Removed expired cache entry: {source}:{article_id}")
                
                return None
                
            except Exception as e:
                print(f"Error getting cached abstract: {e}")
                return None
    
    def set(self, article_id: str, url: str, title: str, abstract: str, source: str = "ieee") -> bool:
        """
        设置摘要缓存
        
        Args:
            article_id: 文章ID
            url: 文章URL
            title: 文章标题
            abstract: 摘要文本
            source: 数据源
            
        Returns:
            是否成功缓存
        """
        if not abstract or len(abstract) < 50:  # 过滤太短的摘要
            return False
        
        with self._lock:
            try:
                entry = AbstractCacheEntry(
                    article_id=article_id,
                    url=url,
                    title=title,
                    abstract=abstract,
                    cached_time=time.time(),
                    source=source
                )
                
                with self._get_connection() as conn:
                    # 使用 INSERT OR REPLACE 语句
                    conn.execute("""
                        INSERT OR REPLACE INTO abstract_cache 
                        (article_id, source, url, title, abstract, abstract_hash, cached_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.article_id, entry.source, entry.url, entry.title,
                        entry.abstract, entry.abstract_hash, entry.cached_time
                    ))
                    
                    conn.commit()
                    print(f"✓ Cached abstract for {source}:{article_id} ({len(abstract)} chars)")
                    return True
                    
            except Exception as e:
                print(f"Error caching abstract: {e}")
                return False
    
    def has(self, article_id: str, source: str = "ieee") -> bool:
        """
        检查是否有缓存的摘要
        
        Args:
            article_id: 文章ID
            source: 数据源
            
        Returns:
            是否存在有效缓存
        """
        return self.get(article_id, source) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    # 总记录数
                    cursor = conn.execute("SELECT COUNT(*) as count FROM abstract_cache")
                    total_entries = cursor.fetchone()['count']
                    
                    # 按来源分组统计
                    cursor = conn.execute("""
                        SELECT source, COUNT(*) as count 
                        FROM abstract_cache 
                        GROUP BY source
                    """)
                    sources = {row['source']: row['count'] for row in cursor.fetchall()}
                    
                    # 数据库文件大小
                    db_size = self.db_file.stat().st_size if self.db_file.exists() else 0
                    
                    # 最新和最旧的缓存时间
                    cursor = conn.execute("""
                        SELECT MIN(cached_time) as oldest, MAX(cached_time) as newest 
                        FROM abstract_cache
                    """)
                    time_range = cursor.fetchone()
                    
                    return {
                        'total_entries': total_entries,
                        'sources': sources,
                        'db_file': str(self.db_file),
                        'db_size_bytes': db_size,
                        'db_size_mb': round(db_size / (1024 * 1024), 2),
                        'max_age_days': self.max_age_seconds // (24 * 3600),
                        'oldest_cache': time_range['oldest'] if time_range['oldest'] else None,
                        'newest_cache': time_range['newest'] if time_range['newest'] else None
                    }
                    
            except Exception as e:
                print(f"Error getting cache stats: {e}")
                return {'error': str(e)}
    
    def clean_expired(self) -> int:
        """清理过期条目"""
        with self._lock:
            try:
                cutoff_time = time.time() - self.max_age_seconds
                
                with self._get_connection() as conn:
                    cursor = conn.execute("""
                        DELETE FROM abstract_cache 
                        WHERE cached_time < ?
                    """, (cutoff_time,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        print(f"✓ Cleaned {deleted_count} expired cache entries")
                        
                        # 清理后优化数据库
                        conn.execute("VACUUM")
                    
                    return deleted_count
                    
            except Exception as e:
                print(f"Error cleaning expired cache: {e}")
                return 0
    
    def _cleanup_expired(self) -> None:
        """启动时清理过期数据"""
        try:
            cleaned = self.clean_expired()
            if cleaned > 0:
                print(f"Startup cleanup: removed {cleaned} expired entries")
        except Exception as e:
            print(f"Error during startup cleanup: {e}")
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("DELETE FROM abstract_cache")
                    conn.commit()
                    conn.execute("VACUUM")  # 优化数据库文件
                    
                print("✓ Cleared all abstract cache")
                
            except Exception as e:
                print(f"Error clearing cache: {e}")
    
    def export_to_json(self, output_file: str) -> None:
        """导出缓存到JSON文件"""
        import json
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT article_id, source, url, title, abstract, 
                               abstract_hash, cached_time, created_at
                        FROM abstract_cache 
                        ORDER BY cached_time DESC
                    """)
                    
                    data = {}
                    for row in cursor.fetchall():
                        key = f"{row['source']}:{row['article_id']}"
                        data[key] = {
                            'article_id': row['article_id'],
                            'source': row['source'],
                            'url': row['url'],
                            'title': row['title'],
                            'abstract': row['abstract'],
                            'abstract_hash': row['abstract_hash'],
                            'cached_time': row['cached_time'],
                            'created_at': row['created_at']
                        }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"✓ Exported {len(data)} abstracts to {output_file}")
                
            except Exception as e:
                print(f"Error exporting cache: {e}")
                raise
    
    def get_entries_by_source(self, source: str, limit: Optional[int] = None) -> List[AbstractCacheEntry]:
        """按数据源获取缓存条目"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    sql = """
                        SELECT article_id, source, url, title, abstract, 
                               abstract_hash, cached_time
                        FROM abstract_cache 
                        WHERE source = ?
                        ORDER BY cached_time DESC
                    """
                    params = [source]
                    
                    if limit:
                        sql += " LIMIT ?"
                        params.append(limit)
                    
                    cursor = conn.execute(sql, params)
                    
                    entries = []
                    for row in cursor.fetchall():
                        entry = AbstractCacheEntry(
                            article_id=row['article_id'],
                            source=row['source'],
                            url=row['url'],
                            title=row['title'],
                            abstract=row['abstract'],
                            cached_time=row['cached_time'],
                            abstract_hash=row['abstract_hash']
                        )
                        entries.append(entry)
                    
                    return entries
                    
            except Exception as e:
                print(f"Error getting entries by source: {e}")
                return []


# 全局缓存实例
abstract_cache = SQLiteAbstractCache()


# 工具函数
def get_cached_abstract(article_id: str, source: str = "ieee") -> Optional[str]:
    """获取缓存的摘要"""
    return abstract_cache.get(article_id, source)


def cache_abstract(article_id: str, url: str, title: str, abstract: str, source: str = "ieee") -> bool:
    """缓存摘要"""
    return abstract_cache.set(article_id, url, title, abstract, source)


def has_cached_abstract(article_id: str, source: str = "ieee") -> bool:
    """检查是否有缓存摘要"""
    return abstract_cache.has(article_id, source)