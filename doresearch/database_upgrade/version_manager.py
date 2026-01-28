"""
数据库版本管理模块
"""
import sqlite3
from typing import Optional


class VersionManager:
    """数据库版本管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_current_version(self) -> str:
        """获取当前数据库版本"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            # 检查是否有版本表
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            if c.fetchone():
                c.execute("SELECT version FROM db_version ORDER BY created_at DESC LIMIT 1")
                result = c.fetchone()
                return result[0] if result else '1.0.0'
            else:
                # 检查表结构来判断版本
                c.execute("PRAGMA table_info(papers)")
                columns = [col[1] for col in c.fetchall()]

                if 'status_changed_at' in columns:
                    return '1.5.0'
                elif 'ieee_article_number' in columns:
                    return '1.2.0'
                else:
                    return '1.0.0'
        except Exception as e:
            print(f"⚠️ 检测版本失败: {e}")
            return '1.0.0'
        finally:
            conn.close()
    
    def create_version_table(self, conn: sqlite3.Connection):
        """创建版本管理表"""
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS db_version
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         version
                         TEXT
                         NOT
                         NULL,
                         upgrade_date
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         created_at
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         notes
                         TEXT
                     )''')

        print("✅ 版本管理表已创建")
    
    def update_version_info(self, conn: sqlite3.Connection, version: str, notes: str = None):
        """更新版本信息"""
        c = conn.cursor()
        c.execute('INSERT INTO db_version (version, notes) VALUES (?, ?)',
                  (version, notes))
        print(f"✅ 版本信息已更新为: {version}")