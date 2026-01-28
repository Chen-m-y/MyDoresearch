"""
数据库模型和初始化 - 包含稍后阅读表
"""
import sqlite3
import os
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()  # 使用统一的连接方法
        c = conn.cursor()

        # 用户表
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         username
                         TEXT
                         NOT
                         NULL
                         UNIQUE,
                         email
                         TEXT
                         NOT
                         NULL
                         UNIQUE,
                         password_hash
                         TEXT
                         NOT
                         NULL,
                         created_at
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         last_login
                         TIMESTAMP,
                         active
                         BOOLEAN
                         DEFAULT
                         1
                     )''')

        # 论文源表
        c.execute('''CREATE TABLE IF NOT EXISTS feeds
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         user_id
                         INTEGER
                         NOT
                         NULL,
                         name
                         TEXT
                         NOT
                         NULL,
                         url
                         TEXT
                         NOT
                         NULL,
                         journal
                         TEXT,
                         created_at
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         last_updated
                         TIMESTAMP,
                         active
                         BOOLEAN
                         DEFAULT
                         1,
                         FOREIGN
                         KEY
                         (user_id)
                         REFERENCES
                         users(id),
                         UNIQUE(user_id, url)
                     )''')

        # 论文表
        c.execute('''CREATE TABLE IF NOT EXISTS papers
        (
            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,
            feed_id
            INTEGER,
            title
            TEXT
            NOT
            NULL,
            abstract
            TEXT,
            abstract_cn
            TEXT,
            authors
            TEXT,
            journal
            TEXT,
            published_date
            TIMESTAMP,
            url
            TEXT,
            pdf_url
            TEXT,
            doi
            TEXT,
            status
            TEXT
            DEFAULT
            'unread',
            status_changed_at
            TIMESTAMP
            DEFAULT
            CURRENT_TIMESTAMP,
            created_at
            TIMESTAMP
            DEFAULT
            CURRENT_TIMESTAMP,
            hash
            TEXT
            UNIQUE,
            external_id
            TEXT,
            ieee_article_number
            TEXT,
            pdf_path
            TEXT,
            analysis_result
            TEXT,
            analysis_at
            TIMESTAMP,
            FOREIGN
            KEY
                     (
            feed_id
                     ) REFERENCES feeds
                     (
                         id
                     )
            )''')

        # 稍后阅读表
        c.execute('''CREATE TABLE IF NOT EXISTS read_later
        (
            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,
            user_id
            INTEGER
            NOT
            NULL,
            paper_id
            INTEGER
            NOT
            NULL,
            marked_at
            TIMESTAMP
            DEFAULT
            CURRENT_TIMESTAMP,
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
            TIMESTAMP
            DEFAULT
            CURRENT_TIMESTAMP,
            updated_at
            TIMESTAMP
            DEFAULT
            CURRENT_TIMESTAMP,
            FOREIGN
            KEY
            (user_id)
            REFERENCES
            users(id),
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
                         user_id, paper_id
                     )
            )''')

        # Agent管理表
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
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         metadata
                         TEXT
                     )''')

        # 任务队列表
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
        (
            id
            TEXT
            PRIMARY
            KEY,
            user_id
            INTEGER
            NOT
            NULL,
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
            TIMESTAMP
            DEFAULT
            CURRENT_TIMESTAMP,
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
            (user_id)
            REFERENCES
            users(id),
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

        # 任务步骤表
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

        # 创建优化的索引
        indexes = [
            # 用户表索引
            'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)',
            
            # Feed表索引
            'CREATE INDEX IF NOT EXISTS idx_feeds_user_id ON feeds(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_feeds_user_active ON feeds(user_id, active)',
            
            # 论文表基础索引
            'CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status)',
            'CREATE INDEX IF NOT EXISTS idx_papers_feed_id ON papers(feed_id)',
            'CREATE INDEX IF NOT EXISTS idx_papers_ieee_article ON papers(ieee_article_number)',
            'CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date)',
            'CREATE INDEX IF NOT EXISTS idx_papers_status_changed ON papers(status_changed_at)',
            
            # 论文表复合索引（性能优化）
            'CREATE INDEX IF NOT EXISTS idx_papers_status_feed_published ON papers(status, feed_id, published_date DESC)',
            'CREATE INDEX IF NOT EXISTS idx_papers_feed_published ON papers(feed_id, published_date DESC)',
            'CREATE INDEX IF NOT EXISTS idx_papers_status_changed_range ON papers(status, status_changed_at DESC)',
            'CREATE INDEX IF NOT EXISTS idx_papers_status_published ON papers(status, published_date DESC)',
            'CREATE INDEX IF NOT EXISTS idx_papers_hash_unique ON papers(hash)',
            
            # 统计查询优化索引
            'CREATE INDEX IF NOT EXISTS idx_papers_read_status_time ON papers(status, status_changed_at) WHERE status = "read"',
            'CREATE INDEX IF NOT EXISTS idx_papers_published_date_range ON papers(published_date, status)',

            # 稍后阅读表索引
            'CREATE INDEX IF NOT EXISTS idx_read_later_user_id ON read_later(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_read_later_paper_id ON read_later(paper_id)',
            'CREATE INDEX IF NOT EXISTS idx_read_later_user_marked ON read_later(user_id, marked_at DESC)',
            'CREATE INDEX IF NOT EXISTS idx_read_later_priority_marked ON read_later(priority DESC, marked_at DESC)',

            # 任务表索引
            'CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_paper_id ON tasks(paper_id)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_type_status ON tasks(task_type, status)',

            # 任务步骤表索引
            'CREATE INDEX IF NOT EXISTS idx_task_steps_task_id ON task_steps(task_id)',
            'CREATE INDEX IF NOT EXISTS idx_task_steps_status ON task_steps(status)',

            # Agent表索引
            'CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)',
            'CREATE INDEX IF NOT EXISTS idx_agents_last_heartbeat ON agents(last_heartbeat)',
            'CREATE INDEX IF NOT EXISTS idx_agents_status_heartbeat ON agents(status, last_heartbeat)',
        ]

        # 检查并添加新字段（兼容性处理）
        self._add_missing_columns(c)

        # 在添加字段后创建索引
        for index_sql in indexes:
            try:
                c.execute(index_sql)
            except sqlite3.OperationalError as e:
                if "no such column" in str(e):
                    print(f"⚠️ 跳过索引创建（列不存在）: {index_sql}")
                else:
                    raise e

        conn.commit()
        conn.close()

    def _add_missing_columns(self, cursor):
        """添加缺失的列"""
        # 检查用户表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("✅ 用户表不存在，创建中...")
            # 手动创建用户表（如果IF NOT EXISTS失败）
            cursor.execute('''CREATE TABLE users
                             (
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 username TEXT NOT NULL UNIQUE,
                                 email TEXT NOT NULL UNIQUE,
                                 password_hash TEXT NOT NULL,
                                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                 last_login TIMESTAMP,
                                 active BOOLEAN DEFAULT 1
                             )''')
            print("✅ 用户表创建完成")
        
        # 检查feeds表
        cursor.execute("PRAGMA table_info(feeds)")
        feed_columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in feed_columns:
            cursor.execute('ALTER TABLE feeds ADD COLUMN user_id INTEGER')
            print("✅ 添加feeds表列: user_id")
            # 为现有feeds设置默认用户ID为1（需要先创建默认用户）
            cursor.execute('UPDATE feeds SET user_id = 1 WHERE user_id IS NULL')
        
        # 检查papers表
        cursor.execute("PRAGMA table_info(papers)")
        paper_columns = [column[1] for column in cursor.fetchall()]

        new_paper_columns = [
            ('abstract_cn', 'TEXT'),
            ('ieee_article_number', 'TEXT'),
            ('pdf_path', 'TEXT'),
            ('analysis_result', 'TEXT'),
            ('analysis_at', 'TIMESTAMP'),
            ('status_changed_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]

        for col_name, col_type in new_paper_columns:
            if col_name not in paper_columns:
                cursor.execute(f'ALTER TABLE papers ADD COLUMN {col_name} {col_type}')
                print(f"✅ 添加papers表列: {col_name}")

        # 检查read_later表
        cursor.execute("PRAGMA table_info(read_later)")
        read_later_columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in read_later_columns:
            cursor.execute('ALTER TABLE read_later ADD COLUMN user_id INTEGER')
            print("✅ 添加read_later表列: user_id")
            # 为现有read_later设置默认用户ID为1
            cursor.execute('UPDATE read_later SET user_id = 1 WHERE user_id IS NULL')

        # 检查tasks表
        cursor.execute("PRAGMA table_info(tasks)")
        task_columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in task_columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN user_id INTEGER')
            print("✅ 添加tasks表列: user_id")
            # 为现有tasks设置默认用户ID为1
            cursor.execute('UPDATE tasks SET user_id = 1 WHERE user_id IS NULL')

    def migrate_read_later_status(self):
        """迁移现有的read_later状态到新表"""
        conn = self.get_connection()
        try:
            c = conn.cursor()

            # 检查是否有使用read_later状态的论文
            c.execute("SELECT id FROM papers WHERE status = 'read_later'")
            read_later_papers = c.fetchall()

            if read_later_papers:
                print(f"🔄 发现 {len(read_later_papers)} 篇标记为稍后阅读的论文，开始迁移...")

                for paper in read_later_papers:
                    paper_id = paper[0]

                    # 插入到read_later表
                    c.execute('''INSERT OR IGNORE INTO read_later (paper_id, marked_at) 
                                VALUES (?, CURRENT_TIMESTAMP)''', (paper_id,))

                    # 将论文状态改回unread
                    c.execute("UPDATE papers SET status = 'unread' WHERE id = ?", (paper_id,))

                conn.commit()
                print(f"✅ 迁移完成，已将 {len(read_later_papers)} 篇论文移至稍后阅读表")

        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            conn.rollback()
        finally:
            conn.close()