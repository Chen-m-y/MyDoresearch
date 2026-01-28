#!/usr/bin/env python3
"""
DoResearch 数据库升级脚本
用于将现有生产数据库安全升级到支持新订阅管理系统

版本要求：
- 从版本：任何现有版本
- 到版本：v2.0.0 (新订阅系统)

使用方法：
python database_upgrade.py [--dry-run] [--backup]
"""

import sqlite3
import os
import json
import shutil
from datetime import datetime
import argparse
import sys


class DatabaseUpgrader:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.backup_path = None
        self.current_version = None
        self.target_version = "v2.0.0"
        
    def log(self, message: str, level: str = "INFO"):
        """记录升级日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = "🔍 [DRY-RUN]" if self.dry_run else "🔧"
        print(f"{prefix} [{level}] {timestamp} - {message}")
    
    def create_backup(self) -> bool:
        """创建数据库备份"""
        if not os.path.exists(self.db_path):
            self.log(f"数据库文件不存在: {self.db_path}", "ERROR")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            if not self.dry_run:
                shutil.copy2(self.db_path, self.backup_path)
            self.log(f"数据库备份已创建: {self.backup_path}")
            return True
        except Exception as e:
            self.log(f"创建备份失败: {e}", "ERROR")
            return False
    
    def get_current_version(self) -> str:
        """获取当前数据库版本（基于实际结构检查）"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 检查新订阅系统的关键表和字段是否存在
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscription_templates'")
            has_subscription_tables = c.fetchone() is not None
            
            if has_subscription_tables:
                # 进一步检查papers表是否有subscription_id字段
                c.execute("PRAGMA table_info(papers)")
                papers_columns = [col[1] for col in c.fetchall()]
                has_subscription_fields = 'subscription_id' in papers_columns
                
                if has_subscription_fields:
                    conn.close()
                    return "v2.0.0"  # 完整的新订阅系统
            
            # 检查版本表是否存在
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_version'")
            if c.fetchone():
                # 有版本表但缺少新功能，认为是需要升级的版本
                conn.close()
                return "v1.5.0"
            
            conn.close()
            return "v1.0.0"  # 最初版本
                
        except Exception as e:
            self.log(f"获取数据库版本失败: {e}", "ERROR")
            return "unknown"
    
    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            exists = c.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            self.log(f"检查表 {table_name} 失败: {e}", "ERROR")
            return False
    
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """检查表中是否存在指定列"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in c.fetchall()]
            conn.close()
            return column_name in columns
        except Exception as e:
            self.log(f"检查列 {table_name}.{column_name} 失败: {e}", "ERROR")
            return False
    
    def execute_sql(self, sql: str, description: str = "", params: tuple = None):
        """执行SQL语句"""
        if self.dry_run:
            self.log(f"[DRY-RUN] {description}: {sql}")
            return True
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            if params:
                c.execute(sql, params)
            else:
                c.execute(sql)
            conn.commit()
            conn.close()
            self.log(f"✅ {description}")
            return True
        except Exception as e:
            self.log(f"❌ {description} 失败: {e}", "ERROR")
            return False
    
    def create_version_table(self):
        """创建版本管理表"""
        if self.check_table_exists('db_version'):
            self.log("版本表已存在，跳过创建")
            return True
        
        sql = '''
        CREATE TABLE db_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            upgrade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        '''
        return self.execute_sql(sql, "创建版本管理表")
    
    def create_subscription_tables(self):
        """创建订阅管理相关表"""
        success = True
        
        # 1. 订阅模板表
        if not self.check_table_exists('subscription_templates'):
            sql = '''
            CREATE TABLE subscription_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                description TEXT,
                parameter_schema TEXT NOT NULL,
                example_params TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            '''
            success &= self.execute_sql(sql, "创建订阅模板表")
        else:
            self.log("订阅模板表已存在，跳过创建")
        
        # 2. 用户订阅表
        if not self.check_table_exists('user_subscriptions'):
            sql = '''
            CREATE TABLE user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                template_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                source_params TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                sync_frequency INTEGER DEFAULT 86400,
                last_sync_at TIMESTAMP,
                next_sync_at TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (template_id) REFERENCES subscription_templates(id)
            )
            '''
            success &= self.execute_sql(sql, "创建用户订阅表")
        else:
            self.log("用户订阅表已存在，跳过创建")
        
        # 3. 订阅同步历史表
        if not self.check_table_exists('subscription_sync_history'):
            sql = '''
            CREATE TABLE subscription_sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER NOT NULL,
                sync_started_at TIMESTAMP NOT NULL,
                sync_completed_at TIMESTAMP,
                status TEXT NOT NULL,
                papers_found INTEGER DEFAULT 0,
                papers_new INTEGER DEFAULT 0,
                error_details TEXT,
                external_service_response TEXT,
                FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(id)
            )
            '''
            success &= self.execute_sql(sql, "创建订阅同步历史表")
        else:
            self.log("订阅同步历史表已存在，跳过创建")
        
        return success
    
    def update_papers_table(self):
        """更新papers表以支持订阅系统"""
        success = True
        
        # 添加subscription_id字段（如果不存在）
        if not self.check_column_exists('papers', 'subscription_id'):
            sql = 'ALTER TABLE papers ADD COLUMN subscription_id INTEGER'
            success &= self.execute_sql(sql, "在papers表添加subscription_id字段")
        else:
            self.log("papers表subscription_id字段已存在，跳过添加")
        
        # 添加keywords字段（如果不存在）
        if not self.check_column_exists('papers', 'keywords'):
            sql = 'ALTER TABLE papers ADD COLUMN keywords TEXT'
            success &= self.execute_sql(sql, "在papers表添加keywords字段")
        else:
            self.log("papers表keywords字段已存在，跳过添加")
        
        # 添加citations字段（如果不存在）
        if not self.check_column_exists('papers', 'citations'):
            sql = 'ALTER TABLE papers ADD COLUMN citations INTEGER DEFAULT 0'
            success &= self.execute_sql(sql, "在papers表添加citations字段")
        else:
            self.log("papers表citations字段已存在，跳过添加")
        
        # 添加metadata字段（如果不存在）
        if not self.check_column_exists('papers', 'metadata'):
            sql = 'ALTER TABLE papers ADD COLUMN metadata TEXT'
            success &= self.execute_sql(sql, "在papers表添加metadata字段")
        else:
            self.log("papers表metadata字段已存在，跳过添加")
        
        return success
    
    def create_indexes(self):
        """创建性能优化索引"""
        indexes = [
            # 订阅系统索引
            ("idx_user_subscriptions_user_id", "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)"),
            ("idx_user_subscriptions_template_id", "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_template_id ON user_subscriptions(template_id)"),
            ("idx_subscription_sync_history_subscription_id", "CREATE INDEX IF NOT EXISTS idx_subscription_sync_history_subscription_id ON subscription_sync_history(subscription_id)"),
            ("idx_subscription_sync_history_started_at", "CREATE INDEX IF NOT EXISTS idx_subscription_sync_history_started_at ON subscription_sync_history(sync_started_at)"),
            
            # Papers表性能索引
            ("idx_papers_subscription_id", "CREATE INDEX IF NOT EXISTS idx_papers_subscription_id ON papers(subscription_id)"),
            ("idx_papers_subscription_published_created", "CREATE INDEX IF NOT EXISTS idx_papers_subscription_published_created ON papers(subscription_id, published_date DESC, created_at DESC)"),
            
            # 其他重要索引
            ("idx_papers_feed_id", "CREATE INDEX IF NOT EXISTS idx_papers_feed_id ON papers(feed_id)"),
            ("idx_papers_status", "CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status)"),
            ("idx_papers_published_date", "CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date)"),
            ("idx_papers_created_at", "CREATE INDEX IF NOT EXISTS idx_papers_created_at ON papers(created_at)"),
        ]
        
        success = True
        for index_name, sql in indexes:
            success &= self.execute_sql(sql, f"创建索引 {index_name}")
        
        return success
    
    def insert_default_templates(self):
        """插入默认的订阅模板"""
        # 检查是否已有模板
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM subscription_templates")
            count = c.fetchone()[0]
            conn.close()
            
            if count > 0:
                self.log("已存在订阅模板，跳过插入默认模板")
                return True
        except:
            pass
        
        templates = [
            {
                'name': 'IEEE期刊订阅',
                'source_type': 'ieee',
                'description': '订阅IEEE期刊最新论文（自动获取最新发表的论文）',
                'parameter_schema': json.dumps({
                    "type": "object",
                    "required": ["punumber"],
                    "properties": {
                        "punumber": {
                            "type": "string",
                            "description": "IEEE期刊的publication number",
                            "pattern": "^[0-9]+$"
                        }
                    }
                }),
                'example_params': json.dumps({"punumber": "32"})
            },
            {
                'name': 'Elsevier期刊订阅',
                'source_type': 'elsevier',
                'description': '订阅Elsevier旗下期刊最新论文',
                'parameter_schema': json.dumps({
                    "type": "object",
                    "required": ["pnumber"],
                    "properties": {
                        "pnumber": {
                            "type": "string",
                            "description": "期刊ISSN或期刊ID",
                            "pattern": "^[0-9X-]+$"
                        }
                    }
                }),
                'example_params': json.dumps({"pnumber": "0164-1212"})
            },
            {
                'name': 'DBLP会议订阅',
                'source_type': 'dblp',
                'description': '订阅DBLP数据库中的会议论文',
                'parameter_schema': json.dumps({
                    "type": "object",
                    "required": ["dblp_id"],
                    "properties": {
                        "dblp_id": {
                            "type": "string",
                            "description": "DBLP会议ID"
                        },
                        "year": {
                            "type": "integer",
                            "description": "年份",
                            "minimum": 2000,
                            "maximum": 2030
                        }
                    }
                }),
                'example_params': json.dumps({"dblp_id": "icse", "year": 2024})
            }
        ]
        
        success = True
        for template in templates:
            if not self.dry_run:
                try:
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO subscription_templates 
                        (name, source_type, description, parameter_schema, example_params, active)
                        VALUES (?, ?, ?, ?, ?, 1)
                    ''', (
                        template['name'],
                        template['source_type'], 
                        template['description'],
                        template['parameter_schema'],
                        template['example_params']
                    ))
                    conn.commit()
                    conn.close()
                    self.log(f"✅ 插入默认模板: {template['name']}")
                except Exception as e:
                    self.log(f"❌ 插入模板失败 {template['name']}: {e}", "ERROR")
                    success = False
            else:
                self.log(f"[DRY-RUN] 插入默认模板: {template['name']}")
        
        return success
    
    def record_upgrade(self):
        """记录升级信息"""
        notes = f"从 {self.current_version} 升级到 {self.target_version}，添加新订阅管理系统支持"
        
        if not self.dry_run:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO db_version (version, notes)
                    VALUES (?, ?)
                ''', (self.target_version, notes))
                conn.commit()
                conn.close()
                self.log(f"✅ 记录升级信息: {self.target_version}")
                return True
            except Exception as e:
                self.log(f"❌ 记录升级信息失败: {e}", "ERROR")
                return False
        else:
            self.log(f"[DRY-RUN] 记录升级信息: {self.target_version}")
            return True
    
    def verify_upgrade(self):
        """验证升级结果"""
        self.log("🔍 验证升级结果...")
        
        required_tables = [
            'subscription_templates',
            'user_subscriptions', 
            'subscription_sync_history'
        ]
        
        required_columns = [
            ('papers', 'subscription_id'),
            ('papers', 'keywords'),
            ('papers', 'citations'),
            ('papers', 'metadata')
        ]
        
        all_good = True
        
        # 检查表
        for table in required_tables:
            if self.check_table_exists(table):
                self.log(f"✅ 表 {table} 存在")
            else:
                self.log(f"❌ 表 {table} 不存在", "ERROR")
                all_good = False
        
        # 检查列
        for table, column in required_columns:
            if self.check_column_exists(table, column):
                self.log(f"✅ 列 {table}.{column} 存在")
            else:
                self.log(f"❌ 列 {table}.{column} 不存在", "ERROR")
                all_good = False
        
        # 检查模板数据
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM subscription_templates WHERE active = 1")
            template_count = c.fetchone()[0]
            conn.close()
            
            if template_count >= 3:
                self.log(f"✅ 找到 {template_count} 个活跃订阅模板")
            else:
                self.log(f"⚠️ 只找到 {template_count} 个活跃订阅模板，预期至少3个", "WARNING")
        except Exception as e:
            self.log(f"❌ 检查订阅模板失败: {e}", "ERROR")
            all_good = False
        
        return all_good
    
    def upgrade(self):
        """执行完整的数据库升级"""
        self.log("🚀 开始数据库升级...")
        self.log(f"数据库路径: {self.db_path}")
        self.log(f"目标版本: {self.target_version}")
        
        # 获取当前版本
        self.current_version = self.get_current_version()
        self.log(f"当前版本: {self.current_version}")
        
        if self.current_version == self.target_version:
            self.log("数据库已是最新版本，无需升级")
            return True
        
        steps = [
            ("创建数据库备份", self.create_backup),
            ("创建版本管理表", self.create_version_table),
            ("创建订阅管理表", self.create_subscription_tables),
            ("更新papers表", self.update_papers_table),
            ("创建性能索引", self.create_indexes),
            ("插入默认模板", self.insert_default_templates),
            ("记录升级信息", self.record_upgrade),
            ("验证升级结果", self.verify_upgrade)
        ]
        
        for step_name, step_func in steps:
            self.log(f"📝 执行步骤: {step_name}")
            if not step_func():
                self.log(f"❌ 步骤失败: {step_name}", "ERROR")
                if self.backup_path:
                    self.log(f"可以使用备份恢复: {self.backup_path}")
                return False
        
        self.log("🎉 数据库升级完成！")
        if self.backup_path:
            self.log(f"备份文件保存在: {self.backup_path}")
        
        return True


def main():
    parser = argparse.ArgumentParser(description='DoResearch数据库升级脚本')
    parser.add_argument('--db-path', default='papers.db', help='数据库文件路径')
    parser.add_argument('--dry-run', action='store_true', help='只显示要执行的操作，不实际修改数据库')
    parser.add_argument('--no-backup', action='store_true', help='跳过备份步骤（不推荐）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db_path):
        print(f"❌ 数据库文件不存在: {args.db_path}")
        sys.exit(1)
    
    upgrader = DatabaseUpgrader(args.db_path, args.dry_run)
    
    if args.dry_run:
        print("🔍 DRY-RUN模式：只显示操作，不会实际修改数据库")
    elif args.no_backup:
        print("⚠️ 警告：跳过备份步骤，直接升级数据库")
        upgrader.create_backup = lambda: True  # 跳过备份
    
    success = upgrader.upgrade()
    
    if success:
        print("✅ 升级成功完成")
        sys.exit(0)
    else:
        print("❌ 升级失败")
        sys.exit(1)


if __name__ == '__main__':
    main()