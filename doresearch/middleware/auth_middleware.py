"""
认证中间件
提供路由保护和用户身份验证
"""
from functools import wraps
from flask import request, jsonify, g

def auth_required(f):
    """要求认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 延迟导入避免循环依赖
        from services.auth_service import AuthService
        auth_service = AuthService()
        
        print(f"🔍 DEBUG: Current sessions count = {len(auth_service.sessions)}")
        
        # 从请求头获取session token
        session_token = request.headers.get('Authorization')
        print(f"🔍 DEBUG: Authorization header = {session_token}")
        
        # 支持Bearer token格式
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]  # 移除 'Bearer ' 前缀
            print(f"🔍 DEBUG: Extracted token = {session_token[:20]}...")
        
        # 也支持从cookie获取token (用于web界面)
        if not session_token:
            session_token = request.cookies.get('session_token')
            print(f"🔍 DEBUG: Cookie session_token = {session_token[:20] if session_token else None}...")
        
        # 如果HttpOnly cookie不可用，尝试非HttpOnly cookie
        if not session_token:
            session_token = request.cookies.get('auth_token')
            print(f"🔍 DEBUG: Cookie auth_token = {session_token[:20] if session_token else None}...")
        
        print(f"🔍 DEBUG: Final token to verify = {session_token[:20] if session_token else None}...")
        
        # 验证会话
        user_info = auth_service.verify_session(session_token) if session_token else None
        print(f"🔍 DEBUG: User info = {user_info}")
        
        if not user_info:
            print(f"❌ DEBUG: Authentication failed for token {session_token[:20] if session_token else None}...")
            return jsonify({
                'success': False,
                'error': '未授权访问，请先登录',
                'code': 'UNAUTHORIZED'
            }), 401
        
        print(f"✅ DEBUG: Authentication successful for user {user_info.get('username')}")
        
        # 将用户信息存储到Flask的g对象中，供路由使用
        g.current_user = user_info
        g.user_id = user_info['user_id']
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """可选认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 延迟导入避免循环依赖
        from services.auth_service import AuthService
        auth_service = AuthService()
        
        # 尝试获取用户信息，但不强制要求
        session_token = request.headers.get('Authorization')
        
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]
        
        if not session_token:
            session_token = request.cookies.get('session_token')
        
        # 如果HttpOnly cookie不可用，尝试非HttpOnly cookie
        if not session_token:
            session_token = request.cookies.get('auth_token')
        
        user_info = auth_service.verify_session(session_token) if session_token else None
        
        # 设置用户信息（可能为None）
        g.current_user = user_info
        g.user_id = user_info['user_id'] if user_info else None
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """获取当前登录用户信息"""
    return getattr(g, 'current_user', None)

def get_current_user_id():
    """获取当前登录用户ID"""
    return getattr(g, 'user_id', None)

def is_authenticated():
    """检查是否已认证"""
    return get_current_user() is not None