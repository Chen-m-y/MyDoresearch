"""
数据库备份管理模块
"""
import shutil
import os
from datetime import datetime
from typing import Optional


class BackupManager:
    """数据库备份管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_path: Optional[str] = None
    
    def backup_database(self) -> bool:
        """备份数据库"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = f"{self.db_path}.backup_{timestamp}"

        try:
            shutil.copy2(self.db_path, self.backup_path)
            print(f"✅ 数据库已备份到: {self.backup_path}")
            return True
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False
    
    def get_backup_path(self) -> Optional[str]:
        """获取备份路径"""
        return self.backup_path