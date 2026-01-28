"""
新订阅管理系统的数据库模型
支持管理员维护订阅源模板，用户基于模板创建订阅
"""
import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from models.database import Database


class SubscriptionDatabase:
    """新订阅管理系统数据库类"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """初始化新订阅管理相关表"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # 订阅源模板表 (管理员维护)
        c.execute('''CREATE TABLE IF NOT EXISTS subscription_templates
                     (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,                    -- 模板名称，如"IEEE期刊订阅"
                         source_type TEXT NOT NULL,             -- 订阅类型: ieee, elsevier, dblp
                         description TEXT,                      -- 模板描述
                         parameter_schema TEXT NOT NULL,        -- JSON格式的参数模式定义
                         example_params TEXT,                   -- 示例参数
                         active BOOLEAN DEFAULT 1,             -- 是否可用
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         created_by INTEGER,                    -- 创建者ID (管理员)
                         
                         UNIQUE(name, source_type)
                     )''')
        
        # 用户订阅表 (用户基于模板创建的订阅)
        c.execute('''CREATE TABLE IF NOT EXISTS user_subscriptions
                     (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER NOT NULL,
                         template_id INTEGER NOT NULL,          -- 关联的模板ID
                         name TEXT NOT NULL,                    -- 用户自定义订阅名称
                         source_params TEXT NOT NULL,          -- JSON格式的订阅参数
                         status TEXT DEFAULT 'active',         -- active, paused, error
                         sync_frequency INTEGER DEFAULT 86400, -- 同步频率(秒)，默认24小时
                         last_sync_at TIMESTAMP,               -- 最后同步时间
                         next_sync_at TIMESTAMP,               -- 下次同步时间
                         error_message TEXT,                   -- 最后的错误信息
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         
                         FOREIGN KEY (user_id) REFERENCES users(id),
                         FOREIGN KEY (template_id) REFERENCES subscription_templates(id),
                         UNIQUE(user_id, template_id, source_params)  -- 防止重复订阅
                     )''')
        
        # 订阅同步历史表
        c.execute('''CREATE TABLE IF NOT EXISTS subscription_sync_history
                     (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         subscription_id INTEGER NOT NULL,
                         sync_started_at TIMESTAMP NOT NULL,
                         sync_completed_at TIMESTAMP,
                         status TEXT NOT NULL,                  -- success, error, running
                         papers_found INTEGER DEFAULT 0,       -- 找到的论文数
                         papers_new INTEGER DEFAULT 0,         -- 新增的论文数
                         error_details TEXT,                   -- 错误详情
                         external_service_response TEXT,      -- 外部服务响应数据
                         
                         FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(id)
                     )''')
        
        # 为papers表添加subscription_id字段（如果不存在）
        try:
            c.execute('ALTER TABLE papers ADD COLUMN subscription_id INTEGER')
            c.execute('CREATE INDEX IF NOT EXISTS idx_papers_subscription_id ON papers(subscription_id)')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        conn.commit()
        conn.close()
        
        # 初始化默认数据
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认的订阅模板"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # 检查是否已经有模板
        c.execute('SELECT COUNT(*) FROM subscription_templates')
        if c.fetchone()[0] > 0:
            conn.close()
            return
        
        # 默认订阅模板
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
                'description': '订阅Elsevier期刊最新论文',
                'parameter_schema': json.dumps({
                    "type": "object",
                    "required": ["pnumber"],
                    "properties": {
                        "pnumber": {
                            "type": "string",
                            "description": "Elsevier期刊的ISSN或期刊ID"
                        }
                    }
                }),
                'example_params': json.dumps({"pnumber": "0164-1212"})
            },
            {
                'name': 'DBLP会议订阅',
                'source_type': 'dblp',
                'description': '订阅DBLP会议论文（获取指定年份的所有论文）',
                'parameter_schema': json.dumps({
                    "type": "object",
                    "required": ["dblp_id", "year"],
                    "properties": {
                        "dblp_id": {
                            "type": "string",
                            "description": "DBLP会议ID，如icse、nips、aaai等"
                        },
                        "year": {
                            "type": "integer",
                            "minimum": 2000,
                            "maximum": 2030,
                            "description": "会议年份（必填）"
                        }
                    }
                }),
                'example_params': json.dumps({"dblp_id": "icse", "year": 2024})
            }
        ]
        
        for template in templates:
            c.execute('''INSERT OR IGNORE INTO subscription_templates 
                        (name, source_type, description, parameter_schema, example_params)
                        VALUES (?, ?, ?, ?, ?)''',
                     (template['name'], template['source_type'], template['description'],
                      template['parameter_schema'], template['example_params']))
        
        conn.commit()
        conn.close()


class SubscriptionTemplateManager:
    """订阅模板管理器"""
    
    def __init__(self, db_path: str):
        self.db = SubscriptionDatabase(db_path)
    
    def get_connection(self):
        """获取数据库连接"""
        return self.db.get_connection()
    
    def get_all_templates(self, active_only: bool = True) -> List[Dict]:
        """获取所有订阅模板"""
        conn = self.get_connection()
        c = conn.cursor()
        
        query = 'SELECT * FROM subscription_templates'
        params = []
        
        if active_only:
            query += ' WHERE active = 1'
        
        query += ' ORDER BY source_type, name'
        
        c.execute(query, params)
        templates = [dict(row) for row in c.fetchall()]
        
        # 解析JSON字段
        for template in templates:
            if template['parameter_schema']:
                template['parameter_schema'] = json.loads(template['parameter_schema'])
            if template['example_params']:
                template['example_params'] = json.loads(template['example_params'])
        
        conn.close()
        return templates
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """获取单个订阅模板"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('SELECT * FROM subscription_templates WHERE id = ?', (template_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return None
        
        template = dict(row)
        
        # 解析JSON字段
        if template['parameter_schema']:
            template['parameter_schema'] = json.loads(template['parameter_schema'])
        if template['example_params']:
            template['example_params'] = json.loads(template['example_params'])
        
        conn.close()
        return template
    
    def create_template(self, name: str, source_type: str, description: str,
                       parameter_schema: Dict, example_params: Dict, 
                       created_by: Optional[int] = None) -> Dict:
        """创建订阅模板"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''INSERT INTO subscription_templates 
                        (name, source_type, description, parameter_schema, example_params, created_by)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (name, source_type, description,
                      json.dumps(parameter_schema), json.dumps(example_params), created_by))
            
            template_id = c.lastrowid
            conn.commit()
            
            return {'success': True, 'template_id': template_id}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': '模板名称和类型组合已存在'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def update_template(self, template_id: int, **kwargs) -> Dict:
        """更新订阅模板"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            for field in ['name', 'source_type', 'description', 'active']:
                if field in kwargs:
                    update_fields.append(f'{field} = ?')
                    update_values.append(kwargs[field])
            
            if 'parameter_schema' in kwargs:
                update_fields.append('parameter_schema = ?')
                update_values.append(json.dumps(kwargs['parameter_schema']))
            
            if 'example_params' in kwargs:
                update_fields.append('example_params = ?')
                update_values.append(json.dumps(kwargs['example_params']))
            
            if not update_fields:
                return {'success': False, 'error': '没有要更新的字段'}
            
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            update_values.append(template_id)
            
            query = f'UPDATE subscription_templates SET {", ".join(update_fields)} WHERE id = ?'
            c.execute(query, update_values)
            
            if c.rowcount == 0:
                return {'success': False, 'error': '模板不存在'}
            
            conn.commit()
            return {'success': True}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': '模板名称和类型组合已存在'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def delete_template(self, template_id: int) -> Dict:
        """删除订阅模板（软删除）"""
        return self.update_template(template_id, active=0)


class UserSubscriptionManager:
    """用户订阅管理器"""
    
    def __init__(self, db_path: str):
        self.db = SubscriptionDatabase(db_path)
    
    def get_connection(self):
        """获取数据库连接"""
        return self.db.get_connection()
    
    def create_subscription(self, user_id: int, template_id: int, 
                          name: str, source_params: Dict) -> Dict:
        """创建用户订阅"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # 检查模板是否存在且可用
            c.execute('SELECT * FROM subscription_templates WHERE id = ? AND active = 1', 
                     (template_id,))
            template = c.fetchone()
            if not template:
                return {'success': False, 'error': '订阅模板不存在或已禁用'}
            
            # 计算下次同步时间（默认24小时后）
            next_sync = datetime.now() + timedelta(seconds=86400)
            
            c.execute('''INSERT INTO user_subscriptions 
                        (user_id, template_id, name, source_params, next_sync_at)
                        VALUES (?, ?, ?, ?, ?)''',
                     (user_id, template_id, name, json.dumps(source_params), 
                      next_sync.isoformat()))
            
            subscription_id = c.lastrowid
            conn.commit()
            
            return {'success': True, 'subscription_id': subscription_id}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': '相同参数的订阅已存在'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_user_subscriptions(self, user_id: int, include_template: bool = True) -> List[Dict]:
        """获取用户的所有订阅"""
        conn = self.get_connection()
        c = conn.cursor()
        
        if include_template:
            query = '''
                SELECT us.*, st.name as template_name, st.source_type, st.description
                FROM user_subscriptions us
                JOIN subscription_templates st ON us.template_id = st.id
                WHERE us.user_id = ?
                ORDER BY us.created_at DESC
            '''
        else:
            query = 'SELECT * FROM user_subscriptions WHERE user_id = ? ORDER BY created_at DESC'
        
        c.execute(query, (user_id,))
        subscriptions = [dict(row) for row in c.fetchall()]
        
        # 解析JSON字段
        for subscription in subscriptions:
            if subscription['source_params']:
                subscription['source_params'] = json.loads(subscription['source_params'])
        
        conn.close()
        return subscriptions
    
    def get_subscription(self, subscription_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        """获取单个订阅详情"""
        conn = self.get_connection()
        c = conn.cursor()
        
        query = '''
            SELECT us.*, st.name as template_name, st.source_type, st.description,
                   st.parameter_schema, st.example_params
            FROM user_subscriptions us
            JOIN subscription_templates st ON us.template_id = st.id
            WHERE us.id = ?
        '''
        params = [subscription_id]
        
        if user_id is not None:
            query += ' AND us.user_id = ?'
            params.append(user_id)
        
        c.execute(query, params)
        row = c.fetchone()
        
        if not row:
            conn.close()
            return None
        
        subscription = dict(row)
        
        # 解析JSON字段
        if subscription['source_params']:
            subscription['source_params'] = json.loads(subscription['source_params'])
        if subscription.get('parameter_schema'):
            subscription['parameter_schema'] = json.loads(subscription['parameter_schema'])
        if subscription.get('example_params'):
            subscription['example_params'] = json.loads(subscription['example_params'])
        
        conn.close()
        return subscription
    
    def update_subscription(self, subscription_id: int, user_id: int, **kwargs) -> Dict:
        """更新用户订阅"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            for field in ['name', 'status', 'sync_frequency']:
                if field in kwargs:
                    update_fields.append(f'{field} = ?')
                    update_values.append(kwargs[field])
            
            if 'source_params' in kwargs:
                update_fields.append('source_params = ?')
                update_values.append(json.dumps(kwargs['source_params']))
            
            if not update_fields:
                return {'success': False, 'error': '没有要更新的字段'}
            
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            update_values.extend([subscription_id, user_id])
            
            query = f'''UPDATE user_subscriptions SET {", ".join(update_fields)} 
                       WHERE id = ? AND user_id = ?'''
            c.execute(query, update_values)
            
            if c.rowcount == 0:
                return {'success': False, 'error': '订阅不存在或无权限'}
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def delete_subscription(self, subscription_id: int, user_id: int) -> Dict:
        """删除用户订阅"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('DELETE FROM user_subscriptions WHERE id = ? AND user_id = ?',
                     (subscription_id, user_id))
            
            if c.rowcount == 0:
                return {'success': False, 'error': '订阅不存在或无权限'}
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_subscriptions_for_sync(self, limit: int = 10) -> List[Dict]:
        """获取需要同步的订阅"""
        conn = self.get_connection()
        c = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        query = '''
            SELECT us.*, st.source_type
            FROM user_subscriptions us
            JOIN subscription_templates st ON us.template_id = st.id
            WHERE us.status = 'active' 
            AND (us.next_sync_at IS NULL OR us.next_sync_at <= ?)
            AND st.active = 1
            ORDER BY us.next_sync_at ASC
            LIMIT ?
        '''
        
        c.execute(query, (current_time, limit))
        subscriptions = [dict(row) for row in c.fetchall()]
        
        # 解析JSON字段
        for subscription in subscriptions:
            if subscription['source_params']:
                subscription['source_params'] = json.loads(subscription['source_params'])
        
        conn.close()
        return subscriptions
    
    def update_sync_status(self, subscription_id: int, **kwargs) -> Dict:
        """更新订阅的同步状态"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            update_fields = []
            update_values = []
            
            for field in ['last_sync_at', 'next_sync_at', 'error_message', 'status']:
                if field in kwargs:
                    update_fields.append(f'{field} = ?')
                    update_values.append(kwargs[field])
            
            if not update_fields:
                return {'success': False, 'error': '没有要更新的字段'}
            
            update_values.append(subscription_id)
            query = f'UPDATE user_subscriptions SET {", ".join(update_fields)} WHERE id = ?'
            
            c.execute(query, update_values)
            conn.commit()
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()


class SyncHistoryManager:
    """同步历史管理器"""
    
    def __init__(self, db_path: str):
        self.db = SubscriptionDatabase(db_path)
    
    def get_connection(self):
        """获取数据库连接"""
        return self.db.get_connection()
    
    def create_sync_record(self, subscription_id: int) -> int:
        """创建同步记录"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''INSERT INTO subscription_sync_history 
                        (subscription_id, sync_started_at, status)
                        VALUES (?, ?, 'running')''',
                     (subscription_id, datetime.now().isoformat()))
            
            sync_id = c.lastrowid
            conn.commit()
            return sync_id
        finally:
            conn.close()
    
    def update_sync_record(self, sync_id: int, status: str, 
                          papers_found: int = 0, papers_new: int = 0,
                          error_details: str = None, 
                          service_response: str = None) -> Dict:
        """更新同步记录"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''UPDATE subscription_sync_history 
                        SET sync_completed_at = ?, status = ?, papers_found = ?, 
                            papers_new = ?, error_details = ?, external_service_response = ?
                        WHERE id = ?''',
                     (datetime.now().isoformat(), status, papers_found, papers_new,
                      error_details, service_response, sync_id))
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_subscription_history(self, subscription_id: int, limit: int = 20) -> List[Dict]:
        """获取订阅的同步历史"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT * FROM subscription_sync_history 
                    WHERE subscription_id = ? 
                    ORDER BY sync_started_at DESC 
                    LIMIT ?''', (subscription_id, limit))
        
        history = [dict(row) for row in c.fetchall()]
        conn.close()
        return history