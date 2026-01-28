"""
论文阅读网站 - 增强版Flask后端
集成高性能统计API和统一的SSE系统
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import requests
from datetime import datetime
import re
import hashlib
import os
import json
import threading
import atexit

# 导入搜索路由
from routes.search_routes import setup_search_routes

# 导入服务模块
from services.task_manager import TaskManager
from services.agent_manager import AgentManager
from services.paper_manager import PaperManager
from services.statistics_service import StatisticsService
from services.auth_service import AuthService
from models.database import Database

# 导入配置
from config import DATABASE_PATH, PDF_DIR, DEEPSEEK_API_KEY, CORS_ORIGINS

# 导入统一的SSE和任务服务
from services.sse_manager import sse_manager
from services.task_service import task_service

# 导入翻译器
try:
    from DeepSeekTranslator import DeepSeekTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    print("⚠️ 未找到DeepSeekTranslator模块，翻译功能将被禁用")
    TRANSLATOR_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 配置CORS - 允许前端跨域访问，优化预检请求
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True,  # 允许携带cookie
        "max_age": 86400,  # 预检请求缓存24小时
        "expose_headers": ["Content-Range", "X-Content-Range"]  # 暴露分页相关头部
    }
})

@app.route('/api/v1/health')
def health_check():
    """健康检查端点 - 供 Docker 健康检查使用"""
    return jsonify({
        'status': 'healthy',
        'service': 'doresearch-backend',
        'timestamp': datetime.now().isoformat()
    }), 200


# 全局变量
translator = None
task_processor = None
db = None
paper_manager = None
statistics_service = None
auth_service = None

def init_translator():
    """初始化翻译器"""
    global translator
    if not TRANSLATOR_AVAILABLE:
        print("⚠️ DeepSeekTranslator模块不可用，翻译功能已禁用")
        return

    try:
        translator = DeepSeekTranslator(DEEPSEEK_API_KEY)
        print("✅ 翻译功能已启用")
    except Exception as e:
        print(f"⚠️ 翻译功能初始化失败: {e}")

def init_task_processor():
    """初始化任务处理器"""
    global task_processor
    try:
        # 使用统一的任务处理器
        from services.task_processor import TaskProcessor
        task_processor = TaskProcessor()
        task_processor.start()
        print("✅ 任务处理器已启用（统一SSE版本）")
    except Exception as e:
        print(f"⚠️ 任务处理器初始化失败: {e}")

def init_paper_manager():
    """初始化论文管理器"""
    global paper_manager
    try:
        paper_manager = PaperManager()
        print("✅ 论文管理器已初始化")
    except Exception as e:
        print(f"⚠️ 论文管理器初始化失败: {e}")

def init_statistics_service():
    """初始化统计服务"""
    global statistics_service
    try:
        statistics_service = StatisticsService()
        print("✅ 统计服务已初始化")
    except Exception as e:
        print(f"⚠️ 统计服务初始化失败: {e}")

def init_auth_service():
    """初始化认证服务"""
    global auth_service
    try:
        auth_service = AuthService()
        # 创建默认用户（如果需要）
        auth_service.create_default_user()
        print("✅ 认证服务已初始化")
    except Exception as e:
        print(f"⚠️ 认证服务初始化失败: {e}")

def init_task_service():
    """初始化任务服务"""
    try:
        task_service.start()
        print("✅ 任务服务已启动")
    except Exception as e:
        print(f"⚠️ 任务服务初始化失败: {e}")

# 设置路由
from routes import (
    setup_task_routes,
    setup_statistics_routes, 
    setup_read_later_routes,
    setup_sse_routes
)
from routes.auth_routes import setup_auth_routes
from routes.subscription_routes import setup_subscription_routes

# 健康检查路由
@app.route('/api/health')
def api_health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': 'ok',
            'translator': 'ok' if translator else 'disabled',
            'task_processor': 'ok' if task_processor else 'disabled',
            'paper_manager': 'ok' if paper_manager else 'disabled',
            'statistics_service': 'ok' if statistics_service else 'disabled',
            'auth_service': 'ok' if auth_service else 'disabled',
            'sse_manager': 'ok',
            'task_service': 'ok' if task_service.running else 'stopped'
        }
    })

from middleware.auth_middleware import auth_required, get_current_user_id

@app.route('/api/feeds')
@auth_required
def api_feeds():
    """获取所有论文源（支持扩展信息）"""
    try:
        # 解析include参数
        include_param = request.args.get('include', '')
        include = [item.strip() for item in include_param.split(',') if item.strip()] if include_param else []
        
        user_id = get_current_user_id()
        feeds = paper_manager.get_all_feeds(include, user_id)
        return jsonify(feeds)
    except Exception as e:
        print(f"❌ 获取论文源失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feeds', methods=['POST'])
@auth_required
def api_add_feed():
    """添加论文源"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400

        user_id = get_current_user_id()
        result = paper_manager.add_feed(
            data.get('name', ''),
            data.get('url', ''),
            data.get('journal', ''),
            user_id
        )
        return jsonify(result)
    except Exception as e:
        print(f"❌ 添加论文源失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feeds/<int:feed_id>/update', methods=['POST'])
@auth_required
def api_update_feed(feed_id):
    """更新论文源"""
    try:
        user_id = get_current_user_id()
        result = paper_manager.update_feed(feed_id, user_id)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 更新论文源失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feeds/<int:feed_id>/papers')
@auth_required
def api_feed_papers(feed_id):
    """获取指定订阅的论文列表（带分页和统计）"""
    try:
        status = request.args.get('status', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        # 限制每页最大数量，防止过大请求
        per_page = min(per_page, 100)
        
        result = paper_manager.get_papers_by_feed(feed_id, status, page, per_page, include_stats)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 获取论文列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/papers/<int:paper_id>')
@auth_required
def api_paper_detail(paper_id):
    """获取论文详情（支持扩展信息）"""
    try:
        # 解析expand参数
        expand_param = request.args.get('expand', '')
        expand = [item.strip() for item in expand_param.split(',') if item.strip()] if expand_param else []
        
        user_id = get_current_user_id()
        paper = paper_manager.get_paper(paper_id, expand, user_id)
        if not paper:
            return jsonify({'error': '论文不存在'}), 404

        feed_id = request.args.get('feed_id')
        if feed_id:
            nav = paper_manager.get_paper_navigation(paper_id, int(feed_id))
            paper['navigation'] = nav

        return jsonify(paper)
    except Exception as e:
        print(f"❌ 获取论文详情失败: {e}")
        return jsonify({'error': str(e)}), 500

# Feed统计相关路由
@app.route('/api/feeds/<int:feed_id>/stats')
def api_feed_stats(feed_id):
    """获取单个feed的完整统计"""
    try:
        stats = paper_manager.get_feed_stats(feed_id)
        if not stats:
            return jsonify({'error': 'Feed不存在'}), 404
        return jsonify(stats)
    except Exception as e:
        print(f"❌ 获取Feed统计失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feeds/stats')
def api_feeds_batch_stats():
    """批量获取多个feed的统计"""
    try:
        feed_ids_str = request.args.get('feed_ids', '')
        if not feed_ids_str:
            return jsonify({'error': 'feed_ids参数不能为空'}), 400
        
        try:
            feed_ids = [int(id.strip()) for id in feed_ids_str.split(',') if id.strip()]
        except ValueError:
            return jsonify({'error': 'feed_ids格式错误'}), 400
        
        stats = paper_manager.get_feeds_batch_stats(feed_ids)
        return jsonify(stats)
    except Exception as e:
        print(f"❌ 批量获取Feed统计失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/papers/<int:paper_id>/status', methods=['PUT'])
@auth_required
def api_update_paper_status(paper_id):
    """更新论文状态（支持返回统计变化）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400

        status = data.get('status', 'unread')
        return_stats = data.get('return_stats', False)
        user_id = get_current_user_id()
        
        # 首先检查用户是否有权限访问该论文
        paper = paper_manager.get_paper(paper_id, user_id=user_id)
        if not paper:
            return jsonify({'success': False, 'error': '论文不存在或无权限访问'}), 404
        
        result = paper_manager.update_paper_status(paper_id, status, return_stats)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 更新论文状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 批量操作相关路由
@app.route('/api/papers/batch', methods=['POST'])
def api_papers_batch():
    """批量获取论文信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        
        paper_ids = data.get('paper_ids', [])
        expand = data.get('expand', [])
        
        if not paper_ids:
            return jsonify({'error': 'paper_ids不能为空'}), 400
        
        papers = paper_manager.get_papers_batch(paper_ids, expand)
        return jsonify({'papers': papers})
    except Exception as e:
        print(f"❌ 批量获取论文失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/papers/batch/status', methods=['POST'])
def api_papers_batch_status():
    """批量更新论文状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        
        updates = data.get('updates', [])
        if not updates:
            return jsonify({'error': 'updates不能为空'}), 400
        
        result = paper_manager.update_papers_batch_status(updates)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 批量更新论文状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/papers/<int:paper_id>/translate', methods=['POST'])
def api_translate_abstract(paper_id):
    """翻译论文摘要"""
    try:
        result = paper_manager.translate_abstract(paper_id)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 翻译摘要失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/papers/<int:paper_id>/status-history')
def api_paper_status_history(paper_id):
    """获取论文状态变化历史"""
    try:
        history = paper_manager.get_status_change_history(paper_id)
        if history:
            return jsonify(history)
        else:
            return jsonify({'error': '论文不存在'}), 404
    except Exception as e:
        print(f"❌ 获取状态历史失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/papers/by-status-change')
def api_papers_by_status_change():
    """根据状态变化时间获取论文列表（带分页）"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 限制每页最大数量，防止过大请求
        per_page = min(per_page, 100)
        
        result = paper_manager.get_papers_by_status_change_time(start_time, end_time, page, per_page)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 获取论文列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/papers/<int:paper_id>/read-later', methods=['POST'])
def api_add_to_read_later(paper_id):
    """添加到稍后阅读并创建深度分析任务"""
    try:
        task_manager = TaskManager()
        result = task_manager.create_analysis_task(paper_id)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 创建分析任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 文件下载路由
@app.route('/data/pdfs/<filename>')
def download_pdf(filename):
    """下载PDF文件"""
    try:
        return send_from_directory(PDF_DIR, filename)
    except Exception as e:
        print(f"❌ 下载PDF失败: {e}")
        return jsonify({'error': str(e)}), 404

# 测试路由
@app.route('/api/test/papers')
def test_papers():
    """测试路由 - 返回新格式的示例论文数据"""
    sample_papers = [
        {
            "title": "KeAD: Knowledge-enhanced Graph Attention Network for Accurate Anomaly Detection",
            "abstract": "Anomaly detection has emerged as one of the core research topics...",
            "status": "unread",
            "journal": "IEEE Transactions on Services Computing",
            "published_at": "2025-06-26T05:12:34.780456Z",
            "url": "https://ieeexplore.ieee.org/document/11050989/",
            "author": "Yi Li, Zhangbing Zhou, Pu Sun, Shuiguang Deng, Xiao Sun, Xiao Xue, Sami Yangui, Walid Gaaloul"
        },
        {
            "title": "Hyper-Parameter Optimization for Wireless Network Traffic Prediction Models",
            "abstract": "This paper proposes a novel meta-learning based framework...",
            "status": "unread",
            "journal": "IEEE Internet of Things Journal",
            "published_at": "2024-01-15T10:00:00Z",
            "url": "https://ieeexplore.ieee.org/document/1234567",
            "author": "John Doe, Jane Smith"
        }
    ]
    return jsonify(sample_papers)

@app.route('/api/test/feed-update', methods=['POST'])
def test_feed_update():
    """测试论文源更新功能"""
    try:
        mock_paper_data = {
            "title": "Test Paper with New Format",
            "abstract": "This is a test abstract for the new format parsing.",
            "status": "unread",
            "journal": "Test Journal",
            "published_at": "2025-06-28T10:00:00.000Z",
            "url": "https://ieeexplore.ieee.org/document/12345678/",
            "author": "Test Author 1, Test Author 2",
            "doi": "10.1109/TEST.2025.12345678"
        }

        parsed_date = paper_manager._parse_date_from_json(mock_paper_data)
        ieee_number = paper_manager._extract_ieee_number(mock_paper_data)

        return jsonify({
            "success": True,
            "original_data": mock_paper_data,
            "parsed_date": parsed_date,
            "ieee_number": ieee_number,
            "authors": mock_paper_data.get('author', mock_paper_data.get('authors', ''))
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 新增：统计相关的快捷路由
@app.route('/api/stats')
def api_stats_quick():
    """快捷统计路由（重定向到统计服务）"""
    try:
        stats = statistics_service.get_quick_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        print(f"❌ 获取快捷统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 优化OPTIONS预检请求处理
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        # 快速响应，避免不必要的处理
        response = app.make_default_options_response()
        # 设置预检缓存时间
        response.headers['Access-Control-Max-Age'] = '86400'  # 24小时
        return response

# 设置路由
setup_task_routes(app)
setup_statistics_routes(app)
setup_read_later_routes(app)
setup_search_routes(app)
setup_sse_routes(app)
setup_auth_routes(app)
setup_subscription_routes(app)


def cleanup():
    """清理函数"""
    if task_processor:
        task_processor.stop()
    task_service.stop()


if __name__ == '__main__':
    # 确保目录存在
    os.makedirs('data/pdfs', exist_ok=True)
    os.makedirs('data/logs', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    # 初始化数据库
    db = Database(DATABASE_PATH)

    # 初始化服务
    init_translator()
    init_auth_service()       # 初始化认证服务
    init_task_service()      # 初始化任务服务
    init_task_processor()    # 初始化任务处理器
    init_paper_manager()
    init_statistics_service()

    # 注册清理函数
    atexit.register(cleanup)

    print("🚀 论文阅读器增强版启动")
    print("📋 任务队列系统已激活（统一SSE版本）")
    print("📊 高性能统计服务已启用")
    print("🌐 CORS已配置，支持跨域访问")
    print("📝 支持新格式论文解析和状态时间记录")
    print("🤖 等待Agent连接...")

    # 显示SSE管理器状态
    print(f"\n🔧 SSE管理器状态:")
    print(f"   数据库路径: {sse_manager.db_path}")
    print(f"   已注册Agent数量: {len(sse_manager.active_agents)}")

    # 显示可用的API
    print("\n📡 主要API接口:")
    print("   === 用户认证 ===")
    print("   POST /api/auth/register           - 用户注册")
    print("   POST /api/auth/login              - 用户登录")
    print("   POST /api/auth/logout             - 用户登出")
    print("   GET  /api/auth/profile            - 获取用户资料")
    print("   POST /api/auth/change-password    - 修改密码")
    print("   POST /api/auth/change-email       - 修改邮箱")
    print("   POST /api/auth/change-username    - 修改用户名")
    print("   GET  /api/auth/check              - 检查认证状态")
    print("   POST /api/auth/init               - 初始化默认用户")
    print("   === SSE Agent管理 ===")
    print("   POST /api/agent/register           - Agent注册")
    print("   GET  /api/agent/<id>/events        - SSE事件流")
    print("   POST /api/agent/task-result        - 提交任务结果")
    print("   GET  /api/sse/status               - SSE系统状态")
    print("   GET  /api/sse/agents               - 活跃Agent列表")
    print("   POST /api/sse/test-download        - 测试下载")

    print("\n   === 下载服务 ===")
    print("   POST /api/download/ieee            - 同步下载IEEE论文")
    print("   POST /api/download/async           - 异步下载任务")
    print("   POST /api/download/pdf             - 创建PDF下载任务")
    print("   GET  /api/agents/status            - Agent状态")

    print("\n   === 统计服务 ===")
    print("   GET  /api/statistics/summary       - 完整统计汇总")
    print("   GET  /api/statistics/quick         - 快速统计")
    print("   GET  /api/statistics/overview      - 详细统计概览")
    print("   GET  /api/statistics/calendar      - 阅读日历")
    print("   GET  /api/statistics/trends        - 阅读趋势")
    print("   GET  /api/statistics/dashboard     - 仪表盘数据")
    print("   GET  /api/stats                    - 快捷统计（别名）")

    print("\n   === 论文管理 ===")
    print("   GET  /api/feeds                    - 获取论文源")
    print("   POST /api/feeds                    - 添加论文源")
    print("   GET  /api/papers/<id>              - 论文详情")
    print("   PUT  /api/papers/<id>/status       - 更新状态")
    print("   POST /api/papers/<id>/translate    - 翻译摘要")

    print("\n   === 搜索功能 ===")
    print("   GET  /api/search                   - 搜索论文")
    print("   POST /api/search/advanced          - 高级搜索")
    print("   GET  /api/search/suggestions       - 搜索建议")

    print("\n   === 稍后阅读 ===")
    print("   POST /api/read-later               - 标记稍后阅读")
    print("   GET  /api/read-later               - 获取列表")
    print("   PUT  /api/read-later/<id>          - 更新信息")
    print("   DELETE /api/read-later/<id>        - 取消标记")

    print("\n   === 任务队列 ===")
    print("   GET  /api/tasks                    - 任务列表")
    print("   GET  /api/tasks/<id>               - 任务详情")
    print("   POST /api/papers/<id>/analyze      - 创建分析任务 (旧版)")
    print("   POST /api/tasks/analysis           - 创建完整分析任务")

    print("\n   === 系统状态 ===")
    print("   GET  /api/health                   - 健康检查")

    # 启动应用
    app.run(host='0.0.0.0', port=5000)