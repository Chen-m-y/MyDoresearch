#!/usr/bin/env python3
"""
智能推荐系统数据库迁移脚本
为现有数据库添加智能交互追踪和推荐功能所需的表结构
"""
import sqlite3
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH


def migrate_recommendation_tables():
    """迁移推荐系统所需的数据库表"""
    
    print("🚀 开始智能推荐系统数据库迁移...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ 数据库文件不存在: {DATABASE_PATH}")
        return False
    
    try:
        # 备份原数据库
        backup_path = f"{DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with open(DATABASE_PATH, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print(f"✅ 数据库已备份到: {backup_path}")
        
        # 连接数据库
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # 检查表是否已存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in c.fetchall()}
        
        tables_to_create = []
        
        # 1. 论文交互记录表
        if 'paper_interactions' not in existing_tables:
            tables_to_create.append(('paper_interactions', '''
                CREATE TABLE paper_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    interaction_type TEXT NOT NULL,
                    duration_seconds INTEGER DEFAULT 0,
                    scroll_depth_percent INTEGER DEFAULT 0,  
                    click_count INTEGER DEFAULT 0,
                    session_id TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES papers (id)
                )
            '''))
        
        # 2. 论文兴趣评分表
        if 'paper_interest_scores' not in existing_tables:
            tables_to_create.append(('paper_interest_scores', '''
                CREATE TABLE paper_interest_scores (
                    paper_id INTEGER PRIMARY KEY,
                    interest_score INTEGER DEFAULT 0,
                    interaction_count INTEGER DEFAULT 0,
                    total_view_time INTEGER DEFAULT 0,
                    max_scroll_depth INTEGER DEFAULT 0,
                    last_interaction_at TIMESTAMP,
                    bookmark_count INTEGER DEFAULT 0,
                    explicit_interest INTEGER DEFAULT 0,  -- 1: 明确感兴趣, -1: 明确不感兴趣, 0: 中性
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES papers (id)
                )
            '''))
        
        # 3. 用户兴趣模式表
        if 'user_interest_patterns' not in existing_tables:
            tables_to_create.append(('user_interest_patterns', '''
                CREATE TABLE user_interest_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,  -- 'keyword', 'author', 'journal', 'topic'
                    pattern_value TEXT NOT NULL,
                    interest_strength REAL DEFAULT 0.0,  -- 0.0-1.0 兴趣强度
                    occurrence_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pattern_type, pattern_value)
                )
            '''))
        
        # 创建新表
        for table_name, create_sql in tables_to_create:
            print(f"📝 创建表: {table_name}")
            c.execute(create_sql)
        
        # 创建索引以优化查询性能
        indices_to_create = [
            ("idx_paper_interactions_paper_id", "CREATE INDEX IF NOT EXISTS idx_paper_interactions_paper_id ON paper_interactions (paper_id)"),
            ("idx_paper_interactions_type", "CREATE INDEX IF NOT EXISTS idx_paper_interactions_type ON paper_interactions (interaction_type)"),
            ("idx_paper_interactions_created", "CREATE INDEX IF NOT EXISTS idx_paper_interactions_created ON paper_interactions (created_at)"),
            ("idx_paper_interest_scores_score", "CREATE INDEX IF NOT EXISTS idx_paper_interest_scores_score ON paper_interest_scores (interest_score)"),
            ("idx_user_patterns_type_value", "CREATE INDEX IF NOT EXISTS idx_user_patterns_type_value ON user_interest_patterns (pattern_type, pattern_value)"),
        ]
        
        print("📊 创建性能优化索引...")
        for index_name, create_sql in indices_to_create:
            try:
                c.execute(create_sql)
                print(f"  ✅ {index_name}")
            except sqlite3.Error as e:
                print(f"  ⚠️ {index_name}: {e}")
        
        # 提交更改
        conn.commit()
        
        # 验证迁移结果
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        final_tables = {row[0] for row in c.fetchall()}
        
        expected_new_tables = {'paper_interactions', 'paper_interest_scores', 'user_interest_patterns'}
        created_tables = expected_new_tables & final_tables
        
        print(f"\n✅ 迁移完成！")
        print(f"📋 新创建的表: {', '.join(created_tables)}")
        
        if len(created_tables) == len(expected_new_tables):
            print("🎉 所有推荐系统表已成功创建")
            
            # 插入一些示例数据（可选）
            if input("\n是否要插入示例交互数据用于测试？(y/N): ").lower() == 'y':
                insert_sample_data(c)
                conn.commit()
                print("✅ 示例数据已插入")
            
            return True
        else:
            missing_tables = expected_new_tables - created_tables
            print(f"⚠️ 以下表创建失败: {', '.join(missing_tables)}")
            return False
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False
    finally:
        conn.close()


def insert_sample_data(cursor):
    """插入示例数据用于测试"""
    try:
        # 获取一些论文ID
        cursor.execute("SELECT id FROM papers LIMIT 5")
        paper_ids = [row[0] for row in cursor.fetchall()]
        
        if not paper_ids:
            print("⚠️ 没有找到论文数据，跳过示例数据插入")
            return
        
        print("📝 插入示例交互数据...")
        
        # 插入一些示例交互记录
        sample_interactions = [
            (paper_ids[0], 'view_end', 120, 80, 'session_1'),  # 深度阅读
            (paper_ids[0], 'bookmark', 0, 0, 'session_1'),     # 收藏
            (paper_ids[1], 'view_end', 30, 40, 'session_2'),   # 简单浏览
            (paper_ids[2], 'view_end', 5, 10, 'session_3'),    # 快速跳过
            (paper_ids[3], 'view_end', 180, 95, 'session_4'),  # 长时间研究
            (paper_ids[3], 'click_pdf', 0, 0, 'session_4'),    # 点击PDF
            (paper_ids[4], 'explicit_dislike', 0, 0, 'session_5'),  # 明确不喜欢
        ]
        
        for paper_id, interaction_type, duration, scroll_depth, session_id in sample_interactions:
            cursor.execute('''
                INSERT INTO paper_interactions 
                (paper_id, interaction_type, duration_seconds, scroll_depth_percent, session_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (paper_id, interaction_type, duration, scroll_depth, session_id, datetime.now()))
        
        # 插入一些示例兴趣评分
        sample_scores = [
            (paper_ids[0], 85, 2, 120, 80, 1, 1),  # 高兴趣
            (paper_ids[1], 35, 1, 30, 40, 0, 0),   # 中等兴趣
            (paper_ids[2], 10, 1, 5, 10, 0, 0),    # 低兴趣
            (paper_ids[3], 90, 2, 180, 95, 0, 1),  # 很高兴趣
            (paper_ids[4], 5, 1, 0, 0, 0, -1),     # 不感兴趣
        ]
        
        for score_data in sample_scores:
            cursor.execute('''
                INSERT INTO paper_interest_scores 
                (paper_id, interest_score, interaction_count, total_view_time, 
                 max_scroll_depth, bookmark_count, explicit_interest, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*score_data, datetime.now()))
        
        # 插入一些示例兴趣模式
        sample_patterns = [
            ('keyword', 'machine learning', 0.8, 5),
            ('keyword', 'neural network', 0.7, 3),
            ('keyword', 'deep learning', 0.9, 4),
            ('author', 'John Smith', 0.6, 2),
            ('journal', 'IEEE Transactions', 0.7, 3),
        ]
        
        for pattern_type, pattern_value, strength, count in sample_patterns:
            cursor.execute('''
                INSERT OR IGNORE INTO user_interest_patterns 
                (pattern_type, pattern_value, interest_strength, occurrence_count, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (pattern_type, pattern_value, strength, count, datetime.now()))
        
        print("✅ 示例数据插入完成")
        
    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")


def check_migration_status():
    """检查迁移状态"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in c.fetchall()}
        
        required_tables = {'paper_interactions', 'paper_interest_scores', 'user_interest_patterns'}
        missing_tables = required_tables - existing_tables
        
        if not missing_tables:
            print("✅ 推荐系统数据库表已存在，无需迁移")
            
            # 检查数据量
            for table in required_tables:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"📊 {table}: {count} 条记录")
            
            return True
        else:
            print(f"⚠️ 缺少以下表: {', '.join(missing_tables)}")
            return False
            
    except Exception as e:
        print(f"❌ 检查迁移状态失败: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("🤖 智能推荐系统数据库迁移工具")
    print("=" * 50)
    
    # 检查当前状态
    if check_migration_status():
        if input("表已存在，是否要重新创建？(y/N): ").lower() != 'y':
            print("✅ 迁移已完成，退出")
            sys.exit(0)
    
    # 执行迁移
    success = migrate_recommendation_tables()
    
    if success:
        print("\n🎉 智能推荐系统迁移成功！")
        print("\n📋 现在你可以使用以下新功能：")
        print("   • 智能交互追踪")
        print("   • 基于行为的个性化推荐") 
        print("   • 论文兴趣评分")
        print("   • 用户兴趣模式分析")
        print("\n🌐 新的API接口：")
        print("   • POST /api/interactions/track - 记录交互")
        print("   • GET  /api/recommendations/personalized - 个性化推荐")
        print("   • GET  /api/recommendations/similar/<paper_id> - 相似论文")
        print("   • GET  /api/interactions/stats - 交互统计")
        print("   • GET  /api/recommendations/dashboard - 推荐仪表板")
    else:
        print("\n❌ 迁移失败，请检查错误信息")
        sys.exit(1)