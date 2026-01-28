"""
数据库迁移脚本模块
包含各个版本之间的升级脚本
"""
import sqlite3
from datetime import datetime


class MigrationScripts:
    """数据库迁移脚本集合"""
    
    @staticmethod
    def upgrade_from_1_0_0(conn: sqlite3.Connection):
        """从1.0.0升级"""
        print("🔄 执行1.0.0 -> 1.2.0升级...")
        c = conn.cursor()

        # 添加缺失的字段
        new_columns = [
            ('abstract_cn', 'TEXT'),
            ('ieee_article_number', 'TEXT'),
            ('pdf_path', 'TEXT'),
            ('analysis_result', 'TEXT'),
            ('analysis_at', 'TIMESTAMP')
        ]

        # 检查现有列
        c.execute("PRAGMA table_info(papers)")
        existing_columns = [col[1] for col in c.fetchall()]

        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                c.execute(f'ALTER TABLE papers ADD COLUMN {col_name} {col_type}')
                print(f"   ✅ 添加列: {col_name}")

        # 添加新索引
        new_indexes = [
            'CREATE INDEX IF NOT EXISTS idx_papers_ieee_article ON papers(ieee_article_number)',
            'CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date)'
        ]

        for index_sql in new_indexes:
            c.execute(index_sql)

        print("✅ 1.0.0 -> 1.2.0 升级完成")
    
    @staticmethod
    def upgrade_from_1_2_0(conn: sqlite3.Connection):
        """从1.2.0升级"""
        print("🔄 执行1.2.0 -> 1.5.0升级...")
        c = conn.cursor()

        # 添加状态变化时间字段
        c.execute("PRAGMA table_info(papers)")
        existing_columns = [col[1] for col in c.fetchall()]

        if 'status_changed_at' not in existing_columns:
            # SQLite不支持带有CURRENT_TIMESTAMP的ALTER TABLE，需要分两步
            print("   ✅ 添加列: status_changed_at")
            c.execute('ALTER TABLE papers ADD COLUMN status_changed_at TIMESTAMP')

            # 为现有记录设置状态变化时间（使用created_at或当前时间）
            print("   🔄 更新现有记录的状态变化时间...")
            c.execute('''UPDATE papers
                         SET status_changed_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                         WHERE status_changed_at IS NULL''')
            print("   ✅ 更新现有记录的状态变化时间完成")

        # 添加状态变化时间索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_papers_status_changed_at ON papers(status_changed_at)')

        print("✅ 1.2.0 -> 1.5.0 升级完成")
    
    @staticmethod
    def upgrade_from_1_5_0(conn: sqlite3.Connection):
        """从1.5.0升级到2.0.0"""
        print("🔄 执行1.5.0 -> 2.0.0升级...")
        c = conn.cursor()

        # 1. 创建稍后阅读表
        print("   📚 创建稍后阅读表...")
        c.execute('''CREATE TABLE IF NOT EXISTS read_later
        (
            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,
            paper_id
            INTEGER
            NOT
            NULL,
            marked_at
            TIMESTAMP,
            priority
            INTEGER
            DEFAULT
            5,
            notes
            TEXT,
            tags
            TEXT,
            estimated_read_time
            INTEGER,
            created_at
            TIMESTAMP,
            updated_at
            TIMESTAMP,
            FOREIGN
            KEY
                     (
            paper_id
                     ) REFERENCES papers
                     (
                         id
                     ),
            UNIQUE
                     (
                         paper_id
                     )
            )''')

        # 2. 创建Agent管理表
        print("   🤖 创建Agent管理表...")
        c.execute('''CREATE TABLE IF NOT EXISTS agents
                     (
                         id
                         TEXT
                         PRIMARY
                         KEY,
                         name
                         TEXT
                         NOT
                         NULL,
                         type
                         TEXT
                         NOT
                         NULL,
                         capabilities
                         TEXT,
                         endpoint
                         TEXT
                         NOT
                         NULL,
                         status
                         TEXT
                         DEFAULT
                         'offline',
                         last_heartbeat
                         TIMESTAMP,
                         created_at
                         TIMESTAMP,
                         metadata
                         TEXT
                     )''')

        # 3. 创建任务队列表
        print("   📋 创建任务队列表...")
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
        (
            id
            TEXT
            PRIMARY
            KEY,
            paper_id
            INTEGER
            NOT
            NULL,
            task_type
            TEXT
            NOT
            NULL,
            status
            TEXT
            DEFAULT
            'pending',
            priority
            INTEGER
            DEFAULT
            5,
            assigned_agent
            TEXT,
            created_at
            TIMESTAMP,
            started_at
            TIMESTAMP,
            completed_at
            TIMESTAMP,
            error_message
            TEXT,
            progress
            INTEGER
            DEFAULT
            0,
            metadata
            TEXT,
            result
            TEXT,
            FOREIGN
            KEY
                     (
            paper_id
                     ) REFERENCES papers
                     (
                         id
                     ),
            FOREIGN KEY
                     (
                         assigned_agent
                     ) REFERENCES agents
                     (
                         id
                     )
            )''')

        # 4. 创建任务步骤表
        print("   📝 创建任务步骤表...")
        c.execute('''CREATE TABLE IF NOT EXISTS task_steps
        (
            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,
            task_id
            TEXT
            NOT
            NULL,
            step_name
            TEXT
            NOT
            NULL,
            status
            TEXT
            DEFAULT
            'pending',
            started_at
            TIMESTAMP,
            completed_at
            TIMESTAMP,
            error_message
            TEXT,
            result
            TEXT,
            FOREIGN
            KEY
                     (
            task_id
                     ) REFERENCES tasks
                     (
                         id
                     )
            )''')

        # 5. 创建所有必要的索引
        print("   🔍 创建优化索引...")
        new_indexes = [
            # 稍后阅读表索引
            'CREATE INDEX IF NOT EXISTS idx_read_later_paper_id ON read_later(paper_id)',
            'CREATE INDEX IF NOT EXISTS idx_read_later_marked_at ON read_later(marked_at)',
            'CREATE INDEX IF NOT EXISTS idx_read_later_priority ON read_later(priority)',
            'CREATE INDEX IF NOT EXISTS idx_read_later_priority_marked ON read_later(priority DESC, marked_at DESC)',

            # 论文表新索引（用于统计优化）
            'CREATE INDEX IF NOT EXISTS idx_papers_status_date ON papers(status, status_changed_at)',
            'CREATE INDEX IF NOT EXISTS idx_papers_published_date_desc ON papers(published_date DESC)',
            'CREATE INDEX IF NOT EXISTS idx_papers_status_stats ON papers(status, status_changed_at, published_date)',

            # 任务表索引
            'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_paper_id ON tasks(paper_id)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)',

            # Agent表索引
            'CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)',
            'CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type)',

            # 任务步骤表索引
            'CREATE INDEX IF NOT EXISTS idx_task_steps_task_id ON task_steps(task_id)'
        ]

        for index_sql in new_indexes:
            c.execute(index_sql)

        # 6. 迁移现有的read_later状态
        print("   🔄 迁移现有的稍后阅读状态...")
        c.execute("SELECT id FROM papers WHERE status = 'read_later'")
        read_later_papers = c.fetchall()

        if read_later_papers:
            print(f"      发现 {len(read_later_papers)} 篇稍后阅读论文")

            current_time = datetime.now().isoformat()

            for paper in read_later_papers:
                paper_id = paper[0]

                # 插入到read_later表，手动设置时间戳
                c.execute('''INSERT
                OR IGNORE INTO read_later 
                            (paper_id, marked_at, created_at, updated_at) 
                            VALUES (?, ?, ?, ?)''',
                          (paper_id, current_time, current_time, current_time))

                # 将论文状态改回unread，并更新状态变化时间
                c.execute('''UPDATE papers
                             SET status            = 'unread',
                                 status_changed_at = ?
                             WHERE id = ?''', (current_time, paper_id))

            print(f"      ✅ 已迁移 {len(read_later_papers)} 篇论文到稍后阅读表")
        else:
            print("      ✅ 没有需要迁移的稍后阅读论文")

        # 7. 为新表的时间戳字段设置默认值（对于新插入的记录）
        print("   ⏰ 设置新表的时间戳默认值...")

        # 对于read_later表，设置现有记录的时间戳
        current_time = datetime.now().isoformat()
        c.execute('UPDATE read_later SET marked_at = ? WHERE marked_at IS NULL', (current_time,))
        c.execute('UPDATE read_later SET created_at = ? WHERE created_at IS NULL', (current_time,))
        c.execute('UPDATE read_later SET updated_at = ? WHERE updated_at IS NULL', (current_time,))

        # 对于agents表
        c.execute('UPDATE agents SET created_at = ? WHERE created_at IS NULL', (current_time,))

        # 对于tasks表
        c.execute('UPDATE tasks SET created_at = ? WHERE created_at IS NULL', (current_time,))

        print("✅ 1.5.0 -> 2.0.0 升级完成")