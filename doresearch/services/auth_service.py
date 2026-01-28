"""
用户认证服务
提供用户注册、登录、会话管理等功能
"""
import sqlite3
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from models.database import Database
from config import DATABASE_PATH

# 会话存储文件路径
SESSIONS_FILE = 'data/sessions.json'

def _load_sessions():
    """从文件加载会话"""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将字符串时间转换回datetime对象
                for session_data in data.values():
                    session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
                    session_data['expires_at'] = datetime.fromisoformat(session_data['expires_at'])
                return data
    except Exception as e:
        print(f"⚠️ 加载会话文件失败: {e}")
    return {}

def _save_sessions(sessions):
    """保存会话到文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        
        # 将datetime对象转换为字符串
        data_to_save = {}
        for token, session_data in sessions.items():
            data_to_save[token] = {
                **session_data,
                'created_at': session_data['created_at'].isoformat(),
                'expires_at': session_data['expires_at'].isoformat()
            }
        
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 保存会话文件失败: {e}")

# 全局会话存储（持久化到文件）
_global_sessions = _load_sessions()

class AuthService:
    """用户认证服务"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        # 使用全局会话存储
        self.sessions = _global_sessions
        self.session_timeout = timedelta(hours=24)
    
    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """密码哈希"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000  # 迭代次数
        )
        return password_hash.hex(), salt
    
    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        password_hash, _ = self._hash_password(password, salt)
        return password_hash == stored_hash
    
    def register_user(self, username: str, email: str, password: str) -> Dict:
        """用户注册"""
        if not username or not email or not password:
            return {'success': False, 'error': '用户名、邮箱和密码不能为空'}
        
        if len(password) < 6:
            return {'success': False, 'error': '密码长度至少6位'}
        
        conn = self.get_db()
        try:
            c = conn.cursor()
            
            # 检查用户名和邮箱是否已存在
            c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if c.fetchone():
                return {'success': False, 'error': '用户名或邮箱已存在'}
            
            # 哈希密码
            password_hash, salt = self._hash_password(password)
            full_hash = f"{salt}:{password_hash}"
            
            # 创建用户
            c.execute('''INSERT INTO users (username, email, password_hash, created_at, active) 
                        VALUES (?, ?, ?, ?, ?)''',
                     (username, email, full_hash, datetime.now(), 1))
            
            user_id = c.lastrowid
            conn.commit()
            
            return {
                'success': True, 
                'user_id': user_id,
                'message': '注册成功'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'注册失败: {str(e)}'}
        finally:
            conn.close()
    
    def login_user(self, username: str, password: str) -> Dict:
        """用户登录"""
        if not username or not password:
            return {'success': False, 'error': '用户名和密码不能为空'}
        
        conn = self.get_db()
        try:
            c = conn.cursor()
            
            # 通过用户名或邮箱查找用户
            c.execute('''SELECT id, username, email, password_hash, active 
                        FROM users WHERE (username = ? OR email = ?) AND active = 1''',
                     (username, username))
            
            user = c.fetchone()
            if not user:
                return {'success': False, 'error': '用户不存在或已被禁用'}
            
            # 验证密码
            stored_hash = user['password_hash']
            if ':' not in stored_hash:
                return {'success': False, 'error': '密码格式错误，请联系管理员'}
            
            salt, password_hash = stored_hash.split(':', 1)
            if not self._verify_password(password, password_hash, salt):
                return {'success': False, 'error': '密码错误'}
            
            # 更新最后登录时间
            c.execute('UPDATE users SET last_login = ? WHERE id = ?',
                     (datetime.now(), user['id']))
            conn.commit()
            
            # 创建会话
            session_token = secrets.token_urlsafe(32)
            session_data = {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': datetime.now(),
                'expires_at': datetime.now() + self.session_timeout
            }
            
            self.sessions[session_token] = session_data
            _save_sessions(self.sessions)  # 保存到文件
            print(f"✅ DEBUG: Created session for user {user['username']}, token = {session_token[:20]}...")
            print(f"✅ DEBUG: Session expires at {session_data['expires_at']}")
            print(f"✅ DEBUG: Total sessions: {len(self.sessions)}")
            
            return {
                'success': True,
                'session_token': session_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'登录失败: {str(e)}'}
        finally:
            conn.close()
    
    def logout_user(self, session_token: str) -> Dict:
        """用户登出"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            _save_sessions(self.sessions)  # 保存到文件
            return {'success': True, 'message': '登出成功'}
        return {'success': False, 'error': '会话不存在'}
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """验证会话"""
        print(f"🔍 DEBUG: verify_session called with token = {session_token[:20] if session_token else None}...")
        
        if not session_token or session_token not in self.sessions:
            print(f"❌ DEBUG: Token not found in sessions. Available sessions: {len(self.sessions)}")
            if session_token:
                print(f"❌ DEBUG: Token {session_token[:20]}... not in sessions")
            return None
        
        session_data = self.sessions[session_token]
        print(f"🔍 DEBUG: Found session data: {session_data}")
        
        # 检查会话是否过期
        if datetime.now() > session_data['expires_at']:
            print(f"❌ DEBUG: Session expired at {session_data['expires_at']}")
            del self.sessions[session_token]
            return None
        
        # 续期会话
        session_data['expires_at'] = datetime.now() + self.session_timeout
        print(f"✅ DEBUG: Session renewed until {session_data['expires_at']}")
        
        return {
            'user_id': session_data['user_id'],
            'username': session_data['username'],
            'email': session_data['email']
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户信息"""
        conn = self.get_db()
        try:
            c = conn.cursor()
            c.execute('''SELECT id, username, email, created_at, last_login, active 
                        FROM users WHERE id = ? AND active = 1''', (user_id,))
            user = c.fetchone()
            return dict(user) if user else None
        finally:
            conn.close()
    
    def create_default_user(self) -> Dict:
        """创建默认管理员用户"""
        conn = self.get_db()
        try:
            c = conn.cursor()
            
            # 检查是否已有用户
            c.execute('SELECT COUNT(*) FROM users')
            user_count = c.fetchone()[0]
            
            if user_count > 0:
                return {'success': False, 'message': '已存在用户，无需创建默认用户'}
            
            # 创建默认管理员用户
            result = self.register_user('admin', 'admin@doresearch.com', 'admin123')
            if result['success']:
                return {'success': True, 'message': '默认管理员用户已创建 (admin/admin123)'}
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'创建默认用户失败: {str(e)}'}
        finally:
            conn.close()
    
    def change_email(self, user_id: int, new_email: str, password: str) -> Dict:
        """修改邮箱"""
        import re
        
        # 验证邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, new_email):
            return {'success': False, 'error': '邮箱格式不正确'}
        
        conn = self.get_db()
        try:
            c = conn.cursor()
            
            # 获取用户当前信息
            c.execute('SELECT email, password_hash FROM users WHERE id = ? AND active = 1', (user_id,))
            user = c.fetchone()
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 检查新邮箱是否已被使用
            c.execute('SELECT id FROM users WHERE email = ? AND id != ?', (new_email, user_id))
            if c.fetchone():
                return {'success': False, 'error': '该邮箱已被其他用户使用'}
            
            # 验证当前密码
            stored_hash = user['password_hash']
            if ':' not in stored_hash:
                return {'success': False, 'error': '密码格式错误，请联系管理员'}
            
            salt, password_hash = stored_hash.split(':', 1)
            if not self._verify_password(password, password_hash, salt):
                return {'success': False, 'error': '当前密码错误'}
            
            # 更新邮箱
            c.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, user_id))
            conn.commit()
            
            return {'success': True, 'message': '邮箱修改成功', 'new_email': new_email}
            
        except Exception as e:
            return {'success': False, 'error': f'修改邮箱失败: {str(e)}'}
        finally:
            conn.close()
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict:
        """修改密码"""
        if len(new_password) < 6:
            return {'success': False, 'error': '新密码长度至少6位'}
        
        conn = self.get_db()
        try:
            c = conn.cursor()
            
            # 获取用户当前密码
            c.execute('SELECT password_hash FROM users WHERE id = ? AND active = 1', (user_id,))
            user = c.fetchone()
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 验证旧密码
            stored_hash = user['password_hash']
            if ':' not in stored_hash:
                return {'success': False, 'error': '密码格式错误，请联系管理员'}
            
            salt, password_hash = stored_hash.split(':', 1)
            if not self._verify_password(old_password, password_hash, salt):
                return {'success': False, 'error': '旧密码错误'}
            
            # 生成新密码哈希
            new_password_hash, new_salt = self._hash_password(new_password)
            full_hash = f"{new_salt}:{new_password_hash}"
            
            # 更新密码
            c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (full_hash, user_id))
            conn.commit()
            
            return {'success': True, 'message': '密码修改成功'}
            
        except Exception as e:
            return {'success': False, 'error': f'修改密码失败: {str(e)}'}
        finally:
            conn.close()
    
    def change_username(self, user_id: int, new_username: str, password: str) -> Dict:
        """修改用户名"""
        import re
        
        # 验证用户名格式
        if not new_username or len(new_username.strip()) < 3:
            return {'success': False, 'error': '用户名长度至少3位'}
        
        new_username = new_username.strip()
        
        # 用户名只能包含字母、数字、下划线
        username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
        if not re.match(username_pattern, new_username):
            return {'success': False, 'error': '用户名只能包含字母、数字和下划线，长度3-20位'}
        
        conn = self.get_db()
        try:
            c = conn.cursor()
            
            # 获取用户当前信息
            c.execute('SELECT username, password_hash FROM users WHERE id = ? AND active = 1', (user_id,))
            user = c.fetchone()
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 检查新用户名是否已被使用
            c.execute('SELECT id FROM users WHERE username = ? AND id != ?', (new_username, user_id))
            if c.fetchone():
                return {'success': False, 'error': '该用户名已被其他用户使用'}
            
            # 验证当前密码
            stored_hash = user['password_hash']
            if ':' not in stored_hash:
                return {'success': False, 'error': '密码格式错误，请联系管理员'}
            
            salt, password_hash = stored_hash.split(':', 1)
            if not self._verify_password(password, password_hash, salt):
                return {'success': False, 'error': '当前密码错误'}
            
            # 更新用户名
            c.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
            conn.commit()
            
            return {'success': True, 'message': '用户名修改成功', 'new_username': new_username}
            
        except Exception as e:
            return {'success': False, 'error': f'修改用户名失败: {str(e)}'}
        finally:
            conn.close()
    
    def clean_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        expired_tokens = []
        
        for token, session_data in self.sessions.items():
            if current_time > session_data['expires_at']:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
        
        return len(expired_tokens)