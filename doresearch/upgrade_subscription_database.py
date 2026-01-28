"""
数据库升级脚本
为新订阅管理系统添加必要的字段和索引
"""
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DATABASE_PATH


def upgrade_papers_table():
    """升级papers表，添加新订阅系统需要的字段"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    print("🔧 升级papers表...")
    
    # 检查并添加新字段
    new_columns = [
        ('subscription_id', 'INTEGER', '订阅ID字段'),
        ('keywords', 'TEXT', '关键词字段（JSON格式）'),
        ('citations', 'INTEGER DEFAULT 0', '引用数字段'),
        ('metadata', 'TEXT', '元数据字段（JSON格式）')
    ]
    
    for column_name, column_type, description in new_columns:
        try:
            c.execute(f'ALTER TABLE papers ADD COLUMN {column_name} {column_type}')
            print(f"✅ 添加{description}: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⚠️ {description}已存在: {column_name}")
            else:
                print(f"❌ 添加{description}失败: {e}")
    
    # 创建索引
    indexes = [
        ('idx_papers_subscription_id', 'papers(subscription_id)', '订阅ID索引'),
        ('idx_papers_status_changed_at', 'papers(status_changed_at)', '状态变更时间索引'),
        ('idx_papers_created_at', 'papers(created_at)', '创建时间索引')
    ]
    
    for index_name, index_def, description in indexes:
        try:
            c.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}')
            print(f"✅ 创建{description}: {index_name}")
        except sqlite3.OperationalError as e:
            print(f"❌ 创建{description}失败: {e}")
    
    conn.commit()
    conn.close()
    print("✅ papers表升级完成")


def check_foreign_keys():
    """检查并修复外键关系"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    print("\n🔧 检查外键关系...")
    
    # 检查subscription_id字段的数据完整性
    c.execute('''SELECT COUNT(*) FROM papers 
                WHERE subscription_id IS NOT NULL 
                AND subscription_id NOT IN (SELECT id FROM user_subscriptions)''')
    
    orphaned_count = c.fetchone()[0]
    if orphaned_count > 0:
        print(f"⚠️ 发现 {orphaned_count} 条论文记录的subscription_id无效")
        # 可以选择清理这些记录或者设置为NULL
        c.execute('UPDATE papers SET subscription_id = NULL WHERE subscription_id NOT IN (SELECT id FROM user_subscriptions)')
        conn.commit()
        print("✅ 已清理无效的subscription_id")
    else:
        print("✅ 所有subscription_id都有效")
    
    conn.close()


def optimize_database():
    """优化数据库性能"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    print("\n🔧 优化数据库...")
    
    try:
        # 分析表统计信息
        c.execute('ANALYZE')
        print("✅ 已更新表统计信息")
        
        # 清理未使用的空间
        c.execute('VACUUM')
        print("✅ 已清理数据库空间")
        
    except Exception as e:
        print(f"⚠️ 数据库优化过程中出现问题: {e}")
    
    conn.close()


def verify_tables():
    """验证所有表的完整性"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    print("\n🔧 验证表结构...")
    
    # 检查新订阅系统的表
    required_tables = [
        'subscription_templates',
        'user_subscriptions', 
        'subscription_sync_history'
    ]
    
    for table in required_tables:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if c.fetchone():
            print(f"✅ 表 {table} 存在")
            
            # 获取记录数
            c.execute(f'SELECT COUNT(*) FROM {table}')
            count = c.fetchone()[0]
            print(f"   - 记录数: {count}")
        else:
            print(f"❌ 表 {table} 不存在")
    
    # 检查papers表的新字段
    c.execute('PRAGMA table_info(papers)')
    columns = [row[1] for row in c.fetchall()]
    
    required_columns = ['subscription_id', 'keywords', 'citations', 'metadata']
    print(f"\n📋 papers表字段检查:")
    for column in required_columns:
        if column in columns:
            print(f"✅ {column} 字段存在")
        else:
            print(f"❌ {column} 字段缺失")
    
    conn.close()


def main():
    """主升级函数"""
    print("🚀 新订阅管理系统数据库升级开始\n")
    
    try:
        # 备份数据库
        import shutil
        backup_path = f"{DATABASE_PATH}.backup"
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"📋 数据库已备份到: {backup_path}")
        
        # 执行升级步骤
        upgrade_papers_table()
        check_foreign_keys()
        verify_tables()
        optimize_database()
        
        print(f"\n{'='*50}")
        print("🎉 数据库升级完成！")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"\n❌ 升级过程中出现错误: {e}")
        print("💡 如有问题，可以从备份文件恢复数据库")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)