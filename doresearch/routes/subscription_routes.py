"""
新订阅管理系统API路由
提供管理员模板管理和用户订阅管理的API接口
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Dict, Any

from configs.subscription_config import get_external_service_config
from services.subscription_service import NewSubscriptionService
from services.permission_cache import cached_permission_check
from middleware.auth_middleware import auth_required, get_current_user_id
from config import DATABASE_PATH


# 初始化服务
external_config = get_external_service_config()
subscription_service = NewSubscriptionService(
    DATABASE_PATH, 
    external_config['base_url']
)

# 创建蓝图
subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/v2')
admin_bp = Blueprint('subscription_admin', __name__, url_prefix='/api/admin')


def admin_required(f):
    """管理员权限装饰器（简化版，实际应该检查用户角色）"""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        # TODO: 实际项目中应该检查用户是否为管理员
        # 这里简化处理，假设所有认证用户都可以管理模板
        return f(*args, **kwargs)
    return decorated_function


def handle_api_error(func):
    """API错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return wrapper


# ===== 用户API路由 =====

@subscription_bp.route('/subscription-templates')
@auth_required
@handle_api_error
def get_subscription_templates():
    """获取可用的订阅模板"""
    templates = subscription_service.get_templates()
    return jsonify({
        'success': True,
        'data': templates
    })


@subscription_bp.route('/subscription-templates/<int:template_id>')
@auth_required
@handle_api_error
def get_subscription_template(template_id: int):
    """获取单个订阅模板详情"""
    template = subscription_service.get_template(template_id)
    if not template:
        return jsonify({
            'success': False,
            'error': '模板不存在'
        }), 404
    
    return jsonify({
        'success': True,
        'data': template
    })


@subscription_bp.route('/subscriptions', methods=['POST'])
@auth_required
@handle_api_error
def create_subscription():
    """创建新订阅"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    required_fields = ['template_id', 'name', 'source_params']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'缺少必填字段: {field}'
            }), 400
    
    user_id = get_current_user_id()
    result = subscription_service.create_subscription(
        user_id=user_id,
        template_id=data['template_id'],
        name=data['name'],
        source_params=data['source_params']
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@subscription_bp.route('/subscriptions')
@auth_required
@handle_api_error
def get_user_subscriptions():
    """获取用户的所有订阅"""
    user_id = get_current_user_id()
    subscriptions = subscription_service.get_user_subscriptions(user_id)
    
    return jsonify({
        'success': True,
        'data': subscriptions
    })


@subscription_bp.route('/subscriptions/<int:subscription_id>')
@auth_required
@handle_api_error
def get_subscription_detail(subscription_id: int):
    """获取订阅详情（带权限缓存）"""
    user_id = get_current_user_id()
    
    # 使用缓存的权限检查
    subscription = cached_permission_check(
        user_id, 'subscription', subscription_id,
        lambda: subscription_service.get_subscription(subscription_id, user_id)
    )
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': '订阅不存在或无权限访问'
        }), 404
    
    return jsonify({
        'success': True,
        'data': subscription
    })


@subscription_bp.route('/subscriptions/<int:subscription_id>', methods=['PUT'])
@auth_required
@handle_api_error
def update_subscription(subscription_id: int):
    """更新订阅配置"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    user_id = get_current_user_id()
    
    # 只允许更新特定字段
    allowed_fields = ['name', 'source_params', 'status', 'sync_frequency']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({
            'success': False,
            'error': '没有可更新的字段'
        }), 400
    
    result = subscription_service.update_subscription(
        subscription_id, user_id, **update_data
    )
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@subscription_bp.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
@auth_required
@handle_api_error
def delete_subscription(subscription_id: int):
    """删除订阅"""
    user_id = get_current_user_id()
    result = subscription_service.delete_subscription(subscription_id, user_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@subscription_bp.route('/subscriptions/<int:subscription_id>/sync', methods=['POST'])
@auth_required
@handle_api_error
def manual_sync_subscription(subscription_id: int):
    """手动触发订阅同步"""
    user_id = get_current_user_id()
    result = subscription_service.manual_sync(subscription_id, user_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@subscription_bp.route('/subscriptions/<int:subscription_id>/history')
@auth_required
@handle_api_error
def get_subscription_sync_history(subscription_id: int):
    """获取订阅同步历史"""
    user_id = get_current_user_id()
    
    # 验证用户是否有权限访问该订阅
    subscription = subscription_service.get_subscription(subscription_id, user_id)
    if not subscription:
        return jsonify({
            'success': False,
            'error': '订阅不存在或无权限访问'
        }), 404
    
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)  # 限制最大返回数量
    
    history = subscription_service.get_sync_history(subscription_id, limit)
    
    return jsonify({
        'success': True,
        'data': history
    })


@subscription_bp.route('/subscriptions/<int:subscription_id>/stats')
@auth_required
@handle_api_error
def get_subscription_stats(subscription_id: int):
    """获取单个订阅的完整统计信息（对等feeds统计）"""
    user_id = get_current_user_id()
    
    # 验证用户是否有权限访问该订阅
    subscription = subscription_service.get_subscription(subscription_id, user_id)
    if not subscription:
        return jsonify({
            'success': False,
            'error': '订阅不存在或无权限访问'
        }), 404
    
    conn = subscription_service.subscription_manager.get_connection()
    try:
        c = conn.cursor()
        
        # 基础统计
        c.execute('SELECT COUNT(*) FROM papers WHERE subscription_id = ?', (subscription_id,))
        total_papers = c.fetchone()[0]
        
        # 按状态统计
        c.execute('''SELECT status, COUNT(*) as count 
                    FROM papers WHERE subscription_id = ? 
                    GROUP BY status''', (subscription_id,))
        status_counts = {row['status']: row['count'] for row in c.fetchall()}
        
        # 最新论文信息
        c.execute('''SELECT MAX(published_date) as latest_date, 
                           MAX(created_at) as last_added
                    FROM papers WHERE subscription_id = ?''', (subscription_id,))
        dates = c.fetchone()
        
        # 同步统计
        c.execute('''SELECT COUNT(*) as total_syncs,
                           SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_syncs,
                           AVG(papers_new) as avg_new_papers,
                           MAX(sync_started_at) as last_sync
                    FROM subscription_sync_history 
                    WHERE subscription_id = ?''', (subscription_id,))
        sync_stats = c.fetchone()
        
        stats = {
            'subscription_info': {
                'id': subscription['id'],
                'name': subscription['name'],
                'source_type': subscription['source_type'],
                'template_name': subscription['template_name'],
                'status': subscription['status'],
                'created_at': subscription['created_at']
            },
            'paper_stats': {
                'total_papers': total_papers,
                'status_counts': {
                    'read': status_counts.get('read', 0),
                    'unread': status_counts.get('unread', 0),
                    'reading': status_counts.get('reading', 0)
                },
                'latest_paper_date': dates['latest_date'],
                'last_added': dates['last_added']
            },
            'sync_stats': {
                'total_syncs': sync_stats['total_syncs'] or 0,
                'successful_syncs': sync_stats['successful_syncs'] or 0,
                'success_rate': round((sync_stats['successful_syncs'] or 0) / max(sync_stats['total_syncs'] or 1, 1) * 100, 2),
                'avg_new_papers': round(sync_stats['avg_new_papers'] or 0, 2),
                'last_sync': sync_stats['last_sync'],
                'next_sync': subscription['next_sync_at']
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    finally:
        conn.close()


@subscription_bp.route('/subscriptions/stats')
@auth_required
@handle_api_error
def get_subscriptions_batch_stats():
    """批量获取多个订阅的统计（对等feeds批量统计）"""
    subscription_ids_str = request.args.get('subscription_ids', '')
    if not subscription_ids_str:
        return jsonify({
            'success': False,
            'error': 'subscription_ids参数不能为空'
        }), 400
    
    try:
        subscription_ids = [int(id.strip()) for id in subscription_ids_str.split(',') if id.strip()]
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'subscription_ids格式错误'
        }), 400
    
    user_id = get_current_user_id()
    
    # 获取用户有权限的订阅列表
    user_subscriptions = subscription_service.get_user_subscriptions(user_id)
    user_subscription_ids = {sub['id'] for sub in user_subscriptions}
    
    # 过滤出有权限的订阅ID
    valid_subscription_ids = [id for id in subscription_ids if id in user_subscription_ids]
    
    if not valid_subscription_ids:
        return jsonify({
            'success': True,
            'data': {}
        })
    
    conn = subscription_service.subscription_manager.get_connection()
    try:
        c = conn.cursor()
        
        stats_result = {}
        
        for subscription_id in valid_subscription_ids:
            # 基础统计
            c.execute('SELECT COUNT(*) FROM papers WHERE subscription_id = ?', (subscription_id,))
            total_papers = c.fetchone()[0]
            
            # 状态统计
            c.execute('''SELECT status, COUNT(*) as count 
                        FROM papers WHERE subscription_id = ? 
                        GROUP BY status''', (subscription_id,))
            status_counts = {row['status']: row['count'] for row in c.fetchall()}
            
            # 最近同步状态
            c.execute('''SELECT status, sync_started_at, papers_new
                        FROM subscription_sync_history 
                        WHERE subscription_id = ? 
                        ORDER BY sync_started_at DESC LIMIT 1''', (subscription_id,))
            last_sync = c.fetchone()
            
            stats_result[str(subscription_id)] = {
                'total_papers': total_papers,
                'unread_count': status_counts.get('unread', 0),
                'status_counts': {
                    'read': status_counts.get('read', 0),
                    'unread': status_counts.get('unread', 0),
                    'reading': status_counts.get('reading', 0)
                },
                'last_sync_status': last_sync['status'] if last_sync else None,
                'last_sync_time': last_sync['sync_started_at'] if last_sync else None,
                'last_sync_new_papers': last_sync['papers_new'] if last_sync else 0
            }
        
        return jsonify({
            'success': True,
            'data': stats_result
        })
    finally:
        conn.close()


@subscription_bp.route('/subscriptions/<int:subscription_id>/papers')
@auth_required
@handle_api_error
def get_subscription_papers(subscription_id: int):
    """获取订阅的论文列表（优化权限检查）"""
    user_id = get_current_user_id()
    
    # 使用缓存的权限检查
    subscription = cached_permission_check(
        user_id, 'subscription', subscription_id,
        lambda: subscription_service.get_subscription(subscription_id, user_id)
    )
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': '订阅不存在或无权限访问'
        }), 404
    
    # 获取查询参数
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # 限制每页最大数量
    
    # 解析expand参数
    expand_param = request.args.get('expand', '')
    expand = [item.strip() for item in expand_param.split(',') if item.strip()] if expand_param else []
    
    # 调用现有的论文管理服务获取论文列表
    # 这里需要修改现有的paper_manager以支持subscription_id查询
    from services.paper_manager import PaperManager
    paper_manager = PaperManager()
    
    # 临时实现：通过subscription_id获取论文
    conn = paper_manager.get_db()
    try:
        c = conn.cursor()
        
        # 构建查询条件
        where_conditions = ['subscription_id = ?']
        params = [subscription_id]
        
        if status != 'all':
            where_conditions.append('status = ?')
            params.append(status)
        
        # 计算总数
        count_query = f"SELECT COUNT(*) FROM papers WHERE {' AND '.join(where_conditions)}"
        c.execute(count_query, params)
        total = c.fetchone()[0]
        
        # 获取论文列表
        offset = (page - 1) * per_page
        papers_query = f"""
            SELECT * FROM papers 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY published_date DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        
        c.execute(papers_query, params)
        papers = [dict(row) for row in c.fetchall()]
        
        # 扩展论文信息（默认或者请求了expand参数）
        if papers and (expand or not expand_param):
            for paper in papers:
                paper_id = paper['id']
                
                # 获取稍后阅读信息（默认包含）
                if 'read_later' in expand or not expand_param:
                    c.execute('''SELECT * FROM read_later WHERE paper_id = ? AND user_id = ?''', 
                             (paper_id, user_id))
                    read_later = c.fetchone()
                    paper['read_later'] = dict(read_later) if read_later else None
                
                # 获取分析任务信息
                if 'analysis' in expand:
                    c.execute('''SELECT * FROM tasks 
                                WHERE paper_id = ? AND user_id = ? AND task_type = 'deep_analysis'
                                ORDER BY created_at DESC LIMIT 1''', 
                             (paper_id, user_id))
                    task = c.fetchone()
                    paper['analysis_task'] = dict(task) if task else None
        
        return jsonify({
            'success': True,
            'data': {
                'papers': papers,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    finally:
        conn.close()


# ===== 管理员API路由 =====

@admin_bp.route('/subscription-templates')
@admin_required
@handle_api_error
def admin_get_templates():
    """管理员获取所有订阅模板（包括非激活的）"""
    templates = subscription_service.template_manager.get_all_templates(active_only=False)
    return jsonify({
        'success': True,
        'data': templates
    })


@admin_bp.route('/subscription-templates', methods=['POST'])
@admin_required
@handle_api_error
def admin_create_template():
    """管理员创建订阅模板"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    required_fields = ['name', 'source_type', 'description', 'parameter_schema']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'缺少必填字段: {field}'
            }), 400
    
    user_id = get_current_user_id()
    result = subscription_service.create_template(
        name=data['name'],
        source_type=data['source_type'],
        description=data['description'],
        parameter_schema=data['parameter_schema'],
        example_params=data.get('example_params', {}),
        created_by=user_id
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@admin_bp.route('/subscription-templates/<int:template_id>', methods=['PUT'])
@admin_required
@handle_api_error
def admin_update_template(template_id: int):
    """管理员更新订阅模板"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    # 允许更新的字段
    allowed_fields = ['name', 'source_type', 'description', 'parameter_schema', 
                     'example_params', 'active']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({
            'success': False,
            'error': '没有可更新的字段'
        }), 400
    
    result = subscription_service.update_template(template_id, **update_data)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@admin_bp.route('/subscription-templates/<int:template_id>', methods=['DELETE'])
@admin_required
@handle_api_error
def admin_delete_template(template_id: int):
    """管理员删除（禁用）订阅模板"""
    result = subscription_service.delete_template(template_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@admin_bp.route('/external-service/health')
@admin_required
@handle_api_error
def check_external_service_health():
    """检查外部微服务健康状态"""
    result = subscription_service.check_external_service()
    return jsonify(result)


@admin_bp.route('/external-service/sources')
@admin_required
@handle_api_error
def get_external_service_sources():
    """获取外部微服务支持的数据源"""
    result = subscription_service.get_supported_sources()
    return jsonify(result)


@admin_bp.route('/subscriptions/stats')
@admin_required
@handle_api_error
def get_subscription_stats():
    """获取订阅统计信息（管理员视图）"""
    conn = subscription_service.template_manager.get_connection()
    try:
        c = conn.cursor()
        
        # 获取各种统计数据
        stats = {}
        
        # 总订阅数
        c.execute('SELECT COUNT(*) FROM user_subscriptions')
        stats['total_subscriptions'] = c.fetchone()[0]
        
        # 活跃订阅数
        c.execute("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'")
        stats['active_subscriptions'] = c.fetchone()[0]
        
        # 按源类型分组统计
        c.execute('''
            SELECT st.source_type, COUNT(*) as count
            FROM user_subscriptions us
            JOIN subscription_templates st ON us.template_id = st.id
            GROUP BY st.source_type
        ''')
        stats['by_source_type'] = dict(c.fetchall())
        
        # 按状态分组统计
        c.execute('SELECT status, COUNT(*) as count FROM user_subscriptions GROUP BY status')
        stats['by_status'] = dict(c.fetchall())
        
        # 最近24小时同步统计
        c.execute('''
            SELECT COUNT(*) FROM subscription_sync_history 
            WHERE sync_started_at > datetime('now', '-1 day')
        ''')
        stats['syncs_last_24h'] = c.fetchone()[0]
        
        # 同步成功率
        c.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
            FROM subscription_sync_history 
            WHERE sync_started_at > datetime('now', '-7 days')
        ''')
        result = c.fetchone()
        total, success = result[0], result[1]
        stats['success_rate'] = round(success / total * 100, 2) if total > 0 else 0
        
        return jsonify({
            'success': True,
            'data': stats
        })
    finally:
        conn.close()


@admin_bp.route('/cache/stats')
@admin_required
@handle_api_error
def get_cache_stats():
    """获取权限缓存统计信息"""
    from services.permission_cache import permission_cache
    
    stats = permission_cache.get_stats()
    
    return jsonify({
        'success': True,
        'data': {
            'permission_cache': stats,
            'cache_hit_rate': round((stats['valid_entries'] / max(stats['total_entries'], 1)) * 100, 2)
        }
    })


@admin_bp.route('/cache/clear', methods=['POST'])
@admin_required
@handle_api_error
def clear_cache():
    """清理过期缓存"""
    from services.permission_cache import permission_cache
    
    old_stats = permission_cache.get_stats()
    permission_cache.clear_expired()
    new_stats = permission_cache.get_stats()
    
    return jsonify({
        'success': True,
        'data': {
            'before': old_stats,
            'after': new_stats,
            'cleared_entries': old_stats['total_entries'] - new_stats['total_entries']
        }
    })


def setup_subscription_routes(app):
    """注册订阅管理路由到Flask应用"""
    app.register_blueprint(subscription_bp)
    app.register_blueprint(admin_bp)
    
    # 启动订阅同步服务
    subscription_service.start()
    
    print("✅ 新订阅管理系统路由已注册")
    print(f"   用户API: {subscription_bp.url_prefix}")
    print(f"   管理员API: {admin_bp.url_prefix}")
    
    # 注册应用关闭时的清理函数
    import atexit
    atexit.register(subscription_service.stop)