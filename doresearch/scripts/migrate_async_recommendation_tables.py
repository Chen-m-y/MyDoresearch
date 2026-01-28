#!/usr/bin/env python3
"""
异步推荐系统数据库迁移脚本
添加缓存和任务管理相关表
"""
import os
import sys
import shutil
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from models.database import Database
from config import DATABASE_PATH


def backup_database():
    """备份现有数据库"""
    try:
        if os.path.exists(DATABASE_PATH):
            backup_path = f"{DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(DATABASE_PATH, backup_path)
            print(f"✅ 数据库已备份到: {backup_path}")
            return backup_path
        else:
            print("⚠️ 数据库文件不存在，跳过备份")
            return None
    except Exception as e:
        print(f"❌ 备份数据库失败: {e}")
        return None


def migrate_tables():
    """迁移异步推荐相关表"""
    try:
        print("🔄 开始创建异步推荐系统表...")
        
        db = Database(DATABASE_PATH)
        conn = db.get_connection()
        c = conn.cursor()
        
        # 推荐缓存表
        print("📦 创建推荐缓存表...")
        c.execute('''CREATE TABLE IF NOT EXISTS recommendation_cache
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL UNIQUE,
            paper_id INTEGER NOT NULL,
            recommendation_type TEXT NOT NULL,
            reference_paper_id INTEGER,
            recommendation_score REAL DEFAULT 0.0,
            ai_reason TEXT,
            rank_position INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (paper_id) REFERENCES papers (id),
            FOREIGN KEY (reference_paper_id) REFERENCES papers (id)
        )''')
        
        # 创建索引优化查询性能
        c.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON recommendation_cache (cache_key)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_cache_type ON recommendation_cache (recommendation_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON recommendation_cache (expires_at)')
        
        # 推荐任务表
        print("📋 创建推荐任务表...")
        c.execute('''CREATE TABLE IF NOT EXISTS recommendation_jobs
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_type TEXT NOT NULL,
            job_status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 5,
            reference_data TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 创建任务相关索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_job_status ON recommendation_jobs (job_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_job_priority ON recommendation_jobs (priority DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_job_type ON recommendation_jobs (job_type)')
        
        # 用户兴趣快照表
        print("📸 创建用户兴趣快照表...")
        c.execute('''CREATE TABLE IF NOT EXISTS user_interest_snapshots
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_hash TEXT NOT NULL UNIQUE,
            liked_papers_count INTEGER DEFAULT 0,
            interests_summary TEXT,
            snapshot_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_current BOOLEAN DEFAULT TRUE
        )''')
        
        # 创建快照相关索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_hash ON user_interest_snapshots (snapshot_hash)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_current ON user_interest_snapshots (is_current)')
        
        conn.commit()
        conn.close()
        
        print("✅ 异步推荐系统表创建完成")
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False


def verify_tables():
    """验证表是否创建成功"""
    try:
        print("🔍 验证表结构...")
        
        db = Database(DATABASE_PATH)
        conn = db.get_connection()
        c = conn.cursor()
        
        # 检查表是否存在
        required_tables = [
            'recommendation_cache',
            'recommendation_jobs', 
            'user_interest_snapshots'
        ]
        
        for table in required_tables:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            result = c.fetchone()
            
            if result:
                print(f"✅ 表 {table} 存在")
                
                # 检查表结构
                c.execute(f"PRAGMA table_info({table})")
                columns = c.fetchall()
                print(f"   - 字段数: {len(columns)}")
                
            else:
                print(f"❌ 表 {table} 不存在")
                return False
        
        conn.close()
        print("✅ 表结构验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 验证表结构失败: {e}")
        return False


def create_initial_warmup_job():
    """创建初始预热任务"""
    try:
        print("🔥 创建初始缓存预热任务...")
        
        db = Database(DATABASE_PATH)
        conn = db.get_connection()
        c = conn.cursor()
        
        # 检查是否已有预热任务
        c.execute("SELECT COUNT(*) FROM recommendation_jobs WHERE job_type = 'full_recompute'")
        existing_jobs = c.fetchone()[0]
        
        if existing_jobs == 0:
            # 创建初始预热任务
            import json
            reference_data = json.dumps({
                'trigger_reason': 'initial_migration',
                'created_by': 'migration_script',
                'description': '系统初始化后的首次缓存预热'
            })
            
            c.execute('''
                INSERT INTO recommendation_jobs
                (job_type, priority, reference_data)
                VALUES ('full_recompute', 6, ?)
            ''', (reference_data,))
            
            conn.commit()
            print("✅ 初始预热任务已创建")
        else:
            print("⚠️ 已存在预热任务，跳过创建")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建初始任务失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始异步推荐系统数据库迁移...")
    print(f"📍 数据库路径: {DATABASE_PATH}")
    
    # 1. 备份数据库
    backup_path = backup_database()
    
    # 2. 迁移表结构
    if not migrate_tables():
        print("❌ 表迁移失败，程序退出")
        return False
    
    # 3. 验证表结构
    if not verify_tables():
        print("❌ 表验证失败，程序退出")
        return False
    
    # 4. 创建初始任务
    if not create_initial_warmup_job():
        print("⚠️ 创建初始任务失败，但迁移继续")
    
    print("🎉 异步推荐系统数据库迁移完成！")
    print("\n📋 迁移总结:")
    print("   ✅ 推荐缓存表 (recommendation_cache)")
    print("   ✅ 推荐任务表 (recommendation_jobs)")
    print("   ✅ 用户兴趣快照表 (user_interest_snapshots)")
    print("   ✅ 相关索引")
    print("   ✅ 初始预热任务")
    
    if backup_path:
        print(f"\n💾 数据库备份: {backup_path}")
    
    print("\n🎯 下一步:")
    print("   1. 重启应用以启动异步推荐系统")
    print("   2. 访问 /api/recommendations/system/status 检查系统状态")
    print("   3. 访问 /api/recommendations/cache/warm-up 手动预热缓存")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 迁移过程中发生未知错误: {e}")
        sys.exit(1)