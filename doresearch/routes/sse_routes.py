"""
SSE (Server-Sent Events) 路由模块
"""
from flask import Flask, request, jsonify, Response
import json
import time

# 使用统一的SSE管理器
from services.sse_manager import sse_manager
from services.task_service import task_service
from services.task_manager import TaskManager


def setup_sse_routes(app: Flask):
    """设置SSE相关路由"""
    
    # 初始化任务管理器
    task_manager = TaskManager()
    
    @app.route('/api/agent/register', methods=['POST'])
    def register_agent():
        """Agent注册"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            agent_id = data.get('agent_id')
            name = data.get('name')
            capabilities = data.get('capabilities', [])
            
            if not agent_id or not name:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400
            
            success = sse_manager.register_agent(agent_id, name, capabilities)
            return jsonify({'success': success, 'message': 'Agent注册成功'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/agent/<agent_id>/events')
    def agent_events(agent_id):
        """Agent SSE事件流"""
        def event_stream():
            try:
                # 连接确认
                yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE连接成功', 'agent_id': agent_id})}\n\n"
                
                loop_count = 0
                max_loops = 3600  # 最多1小时 (3秒 * 1200)
                
                while loop_count < max_loops:
                    try:
                        loop_count += 1
                        
                        # 更新心跳
                        if not sse_manager.update_heartbeat(agent_id):
                            yield f"data: {json.dumps({'type': 'error', 'message': 'Agent需要重新注册'})}\n\n"
                            break
                        
                        # 获取待处理任务
                        tasks = sse_manager.get_pending_tasks(agent_id)
                        
                        for task in tasks:
                            event_data = {
                                'type': 'task',
                                'task_id': task['task_id'],
                                'task_type': task['task_type'],
                                'task_data': task['task_data'],
                                'timestamp': time.time()
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                        
                        # 定期心跳 (每30秒)
                        if loop_count % 10 == 0:
                            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                        
                        time.sleep(3)  # 3秒检查一次
                        
                    except GeneratorExit:
                        print(f"🔌 SSE客户端断开: {agent_id}")
                        # 通知SSE管理器清理该agent
                        sse_manager.remove_agent(agent_id)
                        break
                    except Exception as e:
                        print(f"❌ SSE流内部异常: {e}")
                        yield f"data: {json.dumps({'type': 'error', 'message': f'内部错误: {str(e)}'})}\n\n"
                        break
                
                # 连接结束 - 清理agent
                print(f"🔌 SSE连接正常结束，清理Agent: {agent_id}")
                sse_manager.remove_agent(agent_id)
                yield f"data: {json.dumps({'type': 'disconnect', 'message': 'SSE连接结束'})}\n\n"
                
            except Exception as e:
                print(f"❌ SSE流异常: {e}")
                # 异常情况也要清理agent
                sse_manager.remove_agent(agent_id)
                yield f"data: {json.dumps({'type': 'error', 'message': 'SSE连接异常'})}\n\n"
        
        # 设置SSE响应头
        response = Response(event_stream(), mimetype="text/plain")
        response.headers.update({
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control',
            'X-Accel-Buffering': 'no'
        })
        
        return response
    
    @app.route('/api/agent/task-result', methods=['POST'])
    def submit_task_result():
        """提交任务结果"""
        try:
            data = request.get_json()
            task_id = data.get('task_id')
            result = data.get('result')
            success = data.get('success', True)
            
            if not task_id:
                return jsonify({'success': False, 'error': '缺少task_id'}), 400
            
            sse_manager.submit_result(task_id, result, success)
            return jsonify({'success': True, 'message': '结果提交成功'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/sse/status')
    def sse_status():
        """SSE系统状态"""
        try:
            status = sse_manager.get_status()
            return jsonify({'success': True, **status})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/sse/agents')
    def sse_agents():
        """获取活跃Agent列表"""
        try:
            agents = sse_manager.get_active_agents()
            return jsonify({
                'success': True,
                'agents': agents,
                'total': len(agents)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/sse/test-download', methods=['POST'])
    def test_download():
        """测试下载功能"""
        try:
            data = request.get_json()
            article_number = data.get('article_number')
            
            if not article_number:
                return jsonify({'success': False, 'error': '缺少article_number'}), 400
            
            # 使用任务服务的测试下载功能
            result = task_service.test_download(article_number, timeout=60)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/sse/debug')
    def debug_sse_system():
        """调试SSE系统状态"""
        try:
            agents = sse_manager.get_active_agents()
            
            debug_info = {
                'total_agents': len(agents),
                'agents': [],
                'active_agents_dict': dict(sse_manager.active_agents) if hasattr(sse_manager, 'active_agents') else {},
                'pending_tasks_count': sum(len(tasks) for tasks in sse_manager.pending_tasks.values()) if hasattr(sse_manager, 'pending_tasks') else 0,
                'task_results_count': len(sse_manager.task_results) if hasattr(sse_manager, 'task_results') else 0
            }
            
            for agent in agents:
                debug_info['agents'].append({
                    'agent_id': agent['agent_id'],
                    'name': agent['name'],
                    'capabilities': agent['capabilities'],
                    'last_seen': agent['last_seen'],
                    'last_seen_ago': time.time() - agent['last_seen']
                })
            
            ieee_agents = [agent for agent in agents
                          if 'ieee_download' in agent.get('capabilities', [])]
            
            debug_info['ieee_agents'] = len(ieee_agents)
            debug_info['ieee_agent_details'] = ieee_agents
            
            return jsonify({
                'success': True,
                'debug_info': debug_info
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/sse/force-cleanup', methods=['POST'])
    def force_cleanup_sse():
        """强制清理过期的Agent"""
        try:
            current_time = time.time()
            expired_agents = []
            
            with sse_manager.lock:
                for agent_id, agent_data in list(sse_manager.active_agents.items()):
                    if current_time - agent_data['last_seen'] > 300:  # 5分钟
                        expired_agents.append(agent_id)
                        del sse_manager.active_agents[agent_id]
                        
                        # 清理相关任务
                        if agent_id in sse_manager.pending_tasks:
                            del sse_manager.pending_tasks[agent_id]
            
            return jsonify({
                'success': True,
                'cleaned_agents': expired_agents,
                'remaining_agents': len(sse_manager.active_agents)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/download/ieee', methods=['POST'])
    def download_ieee():
        """下载IEEE论文（通过任务服务）"""
        try:
            data = request.get_json()
            article_number = data.get('article_number')
            
            if not article_number:
                return jsonify({'success': False, 'error': '缺少article_number参数'}), 400
            
            result = task_service.download_ieee_paper(article_number)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/download/async', methods=['POST'])
    def download_async():
        """异步下载任务"""
        try:
            data = request.get_json()
            paper_id = data.get('paper_id')
            article_number = data.get('article_number')
            priority = data.get('priority', 5)
            
            if not paper_id or not article_number:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400
            
            # 创建任务记录
            task_result = task_manager.create_pdf_download_task(paper_id, article_number, priority)
            
            if not task_result['success']:
                return jsonify(task_result), 400
            
            # 启动异步下载（保持原有功能）
            download_result = task_service.create_download_task(paper_id, article_number)
            
            # 返回任务ID和下载状态
            return jsonify({
                'success': True,
                'task_id': task_result['task_id'],
                'message': '已创建PDF下载任务',
                'download_started': download_result.get('success', False)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/download/pdf', methods=['POST'])
    def create_pdf_download_task():
        """创建PDF下载任务"""
        try:
            data = request.get_json()
            paper_id = data.get('paper_id')
            article_number = data.get('article_number')
            priority = data.get('priority', 5)
            
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数'}), 400
            
            if not article_number:
                return jsonify({'success': False, 'error': '缺少article_number参数'}), 400
            
            # 创建PDF下载任务
            result = task_manager.create_pdf_download_task(paper_id, article_number, priority)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tasks/analysis', methods=['POST'])
    def create_full_analysis_task():
        """创建完整分析任务（下载PDF + AI分析）"""
        try:
            data = request.get_json()
            paper_id = data.get('paper_id')
            priority = data.get('priority', 5)
            
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数', 'task_id': None}), 400
            
            # 创建完整分析任务
            result = task_manager.create_full_analysis_task(paper_id, priority)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'task_id': None}), 500
    
    @app.route('/api/agents/status')
    def agents_status():
        """获取Agent状态（包含SSE和传统Agent）"""
        try:
            status = task_service.get_agent_status()
            return jsonify({'success': True, **status})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500