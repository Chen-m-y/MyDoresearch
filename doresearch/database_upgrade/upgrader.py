"""
数据库升级主控制器
"""
import sqlite3
import os
from typing import Dict, Any

from .version_manager import VersionManager
from .backup_manager import BackupManager
from .migration_scripts import MigrationScripts
from .validator import UpgradeValidator


class DatabaseUpgrader:
    """数据库升级器主类"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.version_manager = VersionManager(db_path)
        self.backup_manager = BackupManager(db_path)
        self.validator = UpgradeValidator(db_path)
        self.migration_scripts = MigrationScripts()
        
        self.version_info = {
            'current_version': None,
            'target_version': '2.0.0'
        }
    
    def run_upgrade(self) -> bool:
        """执行完整的升级流程"""
        print("🚀 开始数据库升级流程")
        print("=" * 60)

        # 1. 检查数据库文件
        if not os.path.exists(self.db_path):
            print(f"❌ 数据库文件不存在: {self.db_path}")
            return False

        # 2. 获取当前版本
        current_version = self.version_manager.get_current_version()
        self.version_info['current_version'] = current_version
        print(f"📍 当前数据库版本: {current_version}")
        print(f"🎯 目标版本: {self.version_info['target_version']}")

        if current_version == self.version_info['target_version']:
            print("✅ 数据库已经是最新版本，无需升级")
            return True

        # 3. 备份数据库
        if not self.backup_manager.backup_database():
            return False

        # 4. 开始升级
        conn = sqlite3.connect(self.db_path)

        try:
            # 创建版本管理表
            self.version_manager.create_version_table(conn)

            # 根据当前版本执行相应的升级
            if current_version == '1.0.0':
                self.migration_scripts.upgrade_from_1_0_0(conn)
                self.migration_scripts.upgrade_from_1_2_0(conn)
                self.migration_scripts.upgrade_from_1_5_0(conn)

            elif current_version == '1.2.0':
                self.migration_scripts.upgrade_from_1_2_0(conn)
                self.migration_scripts.upgrade_from_1_5_0(conn)

            elif current_version == '1.5.0':
                self.migration_scripts.upgrade_from_1_5_0(conn)

            # 更新版本信息
            self.version_manager.update_version_info(
                conn, 
                self.version_info['target_version'],
                f"从 {current_version} 升级"
            )

            # 提交所有更改
            conn.commit()

            # 验证升级结果
            if self.validator.verify_upgrade(conn):
                print("\n✅ 数据库升级成功完成！")
                return True
            else:
                print("\n❌ 升级验证失败")
                conn.rollback()
                return False

        except Exception as e:
            print(f"\n❌ 升级过程中发生错误: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()
    
    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.version_manager.get_current_version()
    
    def get_upgrade_summary(self) -> Dict[str, Any]:
        """获取升级摘要"""
        summary = self.validator.get_upgrade_summary()
        summary['backup_path'] = self.backup_manager.get_backup_path()
        return summary