"""
任务队列路由模块
"""
from flask import Flask, request, jsonify
from services.task_manager import TaskManager
from services.agent_manager import AgentManager
from services.task_processor import TaskProcessor
from services.sse_manager import sse_manager
from models.database import Database
from config import DATABASE_PATH


def setup_task_routes(app: Flask):
    """设置任务队列相关路由"""

    task_manager = TaskManager()
    agent_manager = AgentManager()
    db = Database(DATABASE_PATH)

    @app.route('/api/agents/register', methods=['POST'])
    def api_register_agent():
        """注册Agent"""
        data = request.get_json()
        result = agent_manager.register_agent(
            data.get('agent_id'),
            data.get('name'),
            data.get('type'),
            data.get('capabilities', []),
            data.get('endpoint'),
            data.get('metadata', {})
        )
        return jsonify(result)

    @app.route('/api/agents/<agent_id>/heartbeat', methods=['POST'])
    def api_agent_heartbeat(agent_id):
        """Agent心跳"""
        result = agent_manager.heartbeat(agent_id)
        return jsonify(result)

    @app.route('/api/agents/<agent_id>/status', methods=['PUT'])
    def api_update_agent_status(agent_id):
        """更新Agent状态"""
        data = request.get_json()
        result = agent_manager.update_agent_status(agent_id, data.get('status'))
        return jsonify(result)

    @app.route('/api/agents')
    def api_list_agents():
        """获取Agent列表（SSE Agent）"""
        # 获取SSE Agent状态，替代传统Agent
        sse_agents = sse_manager.get_active_agents()
        
        # 转换为统一格式，兼容前端显示
        agents = []
        for agent in sse_agents:
            agents.append({
                'id': agent['agent_id'],
                'name': agent['name'],
                'capabilities': agent['capabilities'],
                'status': 'online',  # SSE Agent活跃即为在线
                'type': 'sse_agent',
                'last_heartbeat': agent['last_seen'],
                'last_seen_ago': agent['last_seen_ago'],
                'endpoint': 'SSE连接',
                'metadata': {}
            })
        
        return jsonify(agents)

    @app.route('/api/tasks')
    def api_list_tasks():
        """获取任务列表"""
        status = request.args.get('status')
        task_type = request.args.get('task_type')
        limit = int(request.args.get('limit', 100))
        include_steps = request.args.get('include_steps', 'true').lower() == 'true'
        
        tasks = task_manager.get_all_tasks(status, limit, task_type, include_steps)
        return jsonify(tasks)

    @app.route('/api/tasks/<task_id>')
    def api_get_task(task_id):
        """获取单个任务详情"""
        task = task_manager.get_task_by_id(task_id)
        if task:
            return jsonify(task)
        else:
            return jsonify({'error': '任务不存在'}), 404

    @app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
    def api_cancel_task(task_id):
        """取消任务"""
        result = task_manager.cancel_task(task_id)
        return jsonify(result)

    @app.route('/api/papers/<int:paper_id>/analyze', methods=['POST'])
    def api_create_analysis_task(paper_id):
        """为论文创建深度分析任务"""
        data = request.get_json() or {}
        priority = data.get('priority', 5)

        result = task_manager.create_analysis_task(paper_id, priority)
        return jsonify(result)

    @app.route('/api/papers/<int:paper_id>/analysis')
    def api_get_paper_analysis(paper_id):
        """获取论文分析结果"""
        conn = db.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT p.*,
                                t.id     as task_id,
                                t.status as task_status,
                                t.progress,
                                t.error_message
                         FROM papers p
                                  LEFT JOIN tasks t ON p.id = t.paper_id AND t.task_type = 'deep_analysis'
                         WHERE p.id = ?
                         ORDER BY t.created_at DESC LIMIT 1''', (paper_id,))

            result = c.fetchone()
            if result:
                paper_dict = dict(result)

                if paper_dict.get('task_id'):
                    # 获取任务步骤
                    steps = task_manager.get_task_steps(paper_dict['task_id'])
                    paper_dict['analysis_steps'] = steps

                print(paper_dict)
                return jsonify(paper_dict)
            else:
                return jsonify({'error': '论文不存在'}), 404

        finally:
            conn.close()

    @app.route('/api/tasks/stats')
    def api_task_stats():
        """获取任务统计信息"""
        conn = db.get_connection()
        try:
            c = conn.cursor()

            # 统计各状态的任务数量
            c.execute('''SELECT status, COUNT(*) as count
                         FROM tasks
                         GROUP BY status''')
            status_counts = {row['status']: row['count'] for row in c.fetchall()}

            # 统计Agent数量
            c.execute('''SELECT status, COUNT(*) as count
                         FROM agents
                         GROUP BY status''')
            agent_counts = {row['status']: row['count'] for row in c.fetchall()}

            # 最近完成的任务
            c.execute('''SELECT t.*, p.title
                         FROM tasks t
                                  JOIN papers p ON t.paper_id = p.id
                         WHERE t.status = 'completed'
                         ORDER BY t.completed_at DESC LIMIT 5''')
            recent_completed = [dict(row) for row in c.fetchall()]

            return jsonify({
                'task_status_counts': status_counts,
                'agent_status_counts': agent_counts,
                'recent_completed_tasks': recent_completed
            })

        finally:
            conn.close()