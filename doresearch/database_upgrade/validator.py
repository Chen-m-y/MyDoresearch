"""
数据库升级验证模块
"""
import sqlite3
from typing import Dict, Any


class UpgradeValidator:
    """数据库升级验证器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def verify_upgrade(self, conn: sqlite3.Connection) -> bool:
        """验证升级结果"""
        print("🔍 验证升级结果...")
        c = conn.cursor()

        # 检查必要的表是否存在
        required_tables = ['papers', 'feeds', 'read_later', 'agents', 'tasks', 'task_steps', 'db_version']

        for table in required_tables:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not c.fetchone():
                print(f"❌ 表 {table} 不存在")
                return False
            else:
                print(f"   ✅ 表 {table} 存在")

        # 检查papers表的关键字段
        c.execute("PRAGMA table_info(papers)")
        paper_columns = [col[1] for col in c.fetchall()]

        required_paper_columns = ['status_changed_at', 'ieee_article_number', 'abstract_cn']
        for col in required_paper_columns:
            if col in paper_columns:
                print(f"   ✅ papers表字段 {col} 存在")
            else:
                print(f"   ❌ papers表字段 {col} 不存在")
                return False

        # 检查数据完整性
        c.execute("SELECT COUNT(*) FROM papers")
        paper_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM read_later")
        read_later_count = c.fetchone()[0]

        print(f"   📊 数据统计:")
        print(f"      论文总数: {paper_count}")
        print(f"      稍后阅读: {read_later_count}")

        return True
    
    def get_upgrade_summary(self) -> Dict[str, Any]:
        """获取升级摘要"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            # 统计信息
            c.execute("SELECT COUNT(*) FROM papers")
            total_papers = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM read_later")
            read_later_count = c.fetchone()[0]

            c.execute("SELECT COUNT(DISTINCT status) FROM papers")
            status_count = c.fetchone()[0]

            # 检查表数量
            c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = c.fetchone()[0]

            # 检查索引数量
            c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            index_count = c.fetchone()[0]

            return {
                'total_papers': total_papers,
                'read_later_count': read_later_count,
                'status_types': status_count,
                'table_count': table_count,
                'index_count': index_count
            }

        finally:
            conn.close()