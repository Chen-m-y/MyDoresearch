"""
认证相关路由
提供用户注册、登录、登出等API接口
"""
from flask import request, jsonify, make_response
from middleware.auth_middleware import auth_required, get_current_user

def setup_auth_routes(app):
    """设置认证相关路由"""
    
    @app.route('/api/auth/register', methods=['POST'])
    def api_register():
        """用户注册"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            result = auth_service.register_user(username, email, password)
            
            if result['success']:
                return jsonify(result), 201
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'注册失败: {str(e)}'}), 500
    
    @app.route('/api/auth/login', methods=['POST'])
    def api_login():
        """用户登录"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            result = auth_service.login_user(username, password)
            
            if result['success']:
                # 创建响应并设置cookie
                response = make_response(jsonify({
                    'success': True,
                    'user': result['user'],
                    'session_token': result['session_token'],  # 在响应中包含session_token
                    'message': '登录成功'
                }))
                
                # 设置session cookies
                # HttpOnly cookie用于服务器端验证
                response.set_cookie(
                    'session_token', 
                    result['session_token'],
                    max_age=24*60*60,  # 24小时
                    httponly=True,
                    secure=False,  # 生产环境应设为True
                    samesite='Lax',  # 允许跨站点请求携带cookie
                    domain=None  # 不限制域名
                )
                
                # 非HttpOnly cookie用于前端JavaScript访问
                response.set_cookie(
                    'auth_token',
                    result['session_token'], 
                    max_age=24*60*60,  # 24小时
                    httponly=False,  # 允许JavaScript访问
                    secure=False,  # 生产环境应设为True
                    samesite='Lax',  # 允许跨站点请求携带cookie
                    domain=None  # 不限制域名
                )
                
                return response
            else:
                return jsonify(result), 401
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'登录失败: {str(e)}'}), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    @auth_required
    def api_logout():
        """用户登出"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            # 从cookie或header获取session token
            session_token = request.cookies.get('session_token')
            if not session_token:
                session_token = request.cookies.get('auth_token')
            if not session_token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    session_token = auth_header[7:]
            
            if session_token:
                auth_service.logout_user(session_token)
            
            # 清除cookies
            response = make_response(jsonify({
                'success': True,
                'message': '登出成功'
            }))
            response.set_cookie('session_token', '', expires=0)
            response.set_cookie('auth_token', '', expires=0)  # 清除非HttpOnly cookie
            
            return response
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'登出失败: {str(e)}'}), 500
    
    @app.route('/api/auth/profile', methods=['GET'])
    @auth_required
    def api_profile():
        """获取用户资料"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            user = get_current_user()
            user_detail = auth_service.get_user_by_id(user['user_id'])
            
            if user_detail:
                return jsonify({
                    'success': True,
                    'user': user_detail
                })
            else:
                return jsonify({'success': False, 'error': '用户不存在'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'获取用户资料失败: {str(e)}'}), 500
    
    @app.route('/api/auth/change-email', methods=['POST'])
    @auth_required
    def api_change_email():
        """修改邮箱"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            new_email = data.get('new_email', '').strip()
            password = data.get('password', '')  # 需要密码验证
            
            if not new_email:
                return jsonify({'success': False, 'error': '新邮箱不能为空'}), 400
            
            if not password:
                return jsonify({'success': False, 'error': '请输入当前密码进行验证'}), 400
            
            user = get_current_user()
            result = auth_service.change_email(user['user_id'], new_email, password)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'修改邮箱失败: {str(e)}'}), 500
    
    @app.route('/api/auth/change-password', methods=['POST'])
    @auth_required
    def api_change_password():
        """修改密码"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            
            user = get_current_user()
            result = auth_service.change_password(user['user_id'], old_password, new_password)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'修改密码失败: {str(e)}'}), 500
    
    @app.route('/api/auth/change-username', methods=['POST'])
    @auth_required
    def api_change_username():
        """修改用户名"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            new_username = data.get('new_username', '').strip()
            password = data.get('password', '')  # 需要密码验证
            
            if not new_username:
                return jsonify({'success': False, 'error': '新用户名不能为空'}), 400
            
            if not password:
                return jsonify({'success': False, 'error': '请输入当前密码进行验证'}), 400
            
            user = get_current_user()
            result = auth_service.change_username(user['user_id'], new_username, password)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'修改用户名失败: {str(e)}'}), 500
    
    @app.route('/api/auth/check', methods=['GET'])
    def api_auth_check():
        """检查认证状态"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            # 从cookie或header获取session token
            session_token = request.cookies.get('session_token')
            if not session_token:
                session_token = request.cookies.get('auth_token')
            if not session_token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    session_token = auth_header[7:]
            
            user_info = auth_service.verify_session(session_token) if session_token else None
            
            if user_info:
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': user_info
                })
            else:
                return jsonify({
                    'success': True,
                    'authenticated': False,
                    'user': None
                })
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'检查认证状态失败: {str(e)}'}), 500
    
    @app.route('/api/auth/debug', methods=['GET'])
    def api_auth_debug():
        """调试认证信息"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            debug_info = {
                'cookies': dict(request.cookies),
                'headers': dict(request.headers),
                'session_tokens': {
                    'session_token_cookie': request.cookies.get('session_token'),
                    'auth_token_cookie': request.cookies.get('auth_token'),
                    'authorization_header': request.headers.get('Authorization')
                }
            }
            
            # 检查各种token的有效性
            tokens_to_check = [
                request.cookies.get('session_token'),
                request.cookies.get('auth_token'),
                request.headers.get('Authorization', '').replace('Bearer ', '') if request.headers.get('Authorization', '').startswith('Bearer ') else None
            ]
            
            debug_info['token_validation'] = {}
            for i, token in enumerate(tokens_to_check):
                if token:
                    user_info = auth_service.verify_session(token)
                    debug_info['token_validation'][f'token_{i}'] = {
                        'token': token[:20] + '...' if len(token) > 20 else token,
                        'valid': bool(user_info),
                        'user': user_info.get('username') if user_info else None
                    }
            
            return jsonify({
                'success': True,
                'debug_info': debug_info
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'调试失败: {str(e)}'}), 500
    
    @app.route('/api/auth/init', methods=['POST'])
    def api_init_default_user():
        """初始化默认用户（仅在无用户时可用）"""
        try:
            from services.auth_service import AuthService
            auth_service = AuthService()
            
            result = auth_service.create_default_user()
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': f'初始化失败: {str(e)}'}), 500