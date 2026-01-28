"""
智能推荐系统路由模块
基于用户行为的个性化推荐API
"""
from flask import Flask, request, jsonify
from services.interaction_tracker import InteractionTracker
from services.ai_based_recommender import AIBasedRecommender
from services.recommendation_cache_manager import cache_manager
from services.async_recommendation_processor import recommendation_processor
from services.recommendation_scheduler import scheduler
import uuid
from datetime import datetime


def setup_recommendation_routes(app: Flask):
    """设置推荐系统相关路由"""
    
    interaction_tracker = InteractionTracker()
    ai_recommender = AIBasedRecommender()
    
    @app.route('/api/interactions/track', methods=['POST'])
    def api_track_interaction():
        """记录用户与论文的交互行为"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            paper_id = data.get('paper_id')
            interaction_type = data.get('interaction_type')
            
            if not paper_id or not interaction_type:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400
            
            # 生成会话ID（如果没有提供）
            session_id = data.get('session_id') or str(uuid.uuid4())
            
            success = interaction_tracker.track_interaction(
                paper_id=paper_id,
                interaction_type=interaction_type,
                duration_seconds=data.get('duration_seconds', 0),
                scroll_depth_percent=data.get('scroll_depth_percent', 0),
                click_count=data.get('click_count', 0),
                session_id=session_id,
                user_agent=request.headers.get('User-Agent'),
                metadata=data.get('metadata')
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '交互记录成功',
                    'session_id': session_id
                })
            else:
                return jsonify({'success': False, 'error': '记录交互失败'}), 500
                
        except Exception as e:
            print(f"❌ 记录交互失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/track-view', methods=['POST'])
    def api_track_paper_view():
        """记录论文查看行为（带智能兴趣分析）"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            paper_id = data.get('paper_id')
            duration_seconds = data.get('duration_seconds', 0)
            scroll_depth_percent = data.get('scroll_depth_percent', 0)
            
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数'}), 400
            
            session_id = data.get('session_id') or str(uuid.uuid4())
            
            # 记录查看行为并分析兴趣
            result = interaction_tracker.track_paper_view(
                paper_id=paper_id,
                duration_seconds=duration_seconds,
                scroll_depth_percent=scroll_depth_percent,
                session_id=session_id
            )
            
            return jsonify({
                'success': True,
                'data': result,
                'session_id': session_id
            })
            
        except Exception as e:
            print(f"❌ 记录论文查看失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/papers/<int:paper_id>/interest-score')
    def api_get_paper_interest_score(paper_id):
        """获取论文的兴趣评分详情"""
        try:
            score_data = interaction_tracker.get_paper_interest_score(paper_id)
            
            if score_data:
                return jsonify({
                    'success': True,
                    'data': score_data
                })
            else:
                return jsonify({
                    'success': True,
                    'data': {
                        'paper_id': paper_id,
                        'interest_score': 0,
                        'interaction_count': 0,
                        'message': '该论文暂无交互记录'
                    }
                })
                
        except Exception as e:
            print(f"❌ 获取兴趣评分失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/personalized')
    def api_get_personalized_recommendations():
        """获取个性化推荐论文（优先使用缓存）"""
        try:
            limit = request.args.get('limit', default=10, type=int)
            limit = min(max(limit, 1), 50)  # 限制在1-50之间
            
            # 使用缓存管理器获取推荐
            result = cache_manager.get_personalized_recommendations(limit=limit)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            print(f"❌ 获取个性化推荐失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/similar/<int:paper_id>')
    def api_get_similar_recommendations(paper_id):
        """根据指定论文查找相似论文（优先使用缓存）"""
        try:
            limit = request.args.get('limit', default=5, type=int)
            limit = min(max(limit, 1), 20)  # 限制在1-20之间
            
            # 使用缓存管理器获取相似推荐
            result = cache_manager.get_similar_recommendations(paper_id, limit=limit)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            print(f"❌ 查找相似论文失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/explain/<int:paper_id>')
    def api_explain_recommendation(paper_id):
        """解释为什么推荐这篇论文（优先使用缓存）"""
        try:
            # 使用缓存管理器获取推荐解释
            explanation = cache_manager.get_recommendation_explanation(paper_id)
            
            return jsonify({
                'success': True,
                'data': explanation
            })
            
        except Exception as e:
            print(f"❌ 生成推荐解释失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/high-interest-papers')
    def api_get_high_interest_papers():
        """获取高兴趣度的论文列表"""
        try:
            min_score = request.args.get('min_score', default=60, type=int)
            limit = request.args.get('limit', default=50, type=int)
            
            high_interest_papers = interaction_tracker.get_high_interest_papers(
                min_score=min_score,
                limit=limit
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'papers': high_interest_papers,
                    'count': len(high_interest_papers),
                    'min_score': min_score,
                    'limit': limit
                }
            })
            
        except Exception as e:
            print(f"❌ 获取高兴趣论文失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/user-patterns')
    def api_analyze_user_patterns():
        """分析用户的兴趣模式（包含时间衰减权重信息）"""
        try:
            # 获取基础模式分析
            basic_patterns = interaction_tracker.analyze_user_patterns()
            
            # 获取AI分析的用户兴趣总结
            ai_summary = ai_recommender.get_user_interests_summary()
            
            return jsonify({
                'success': True,
                'data': {
                    'basic_patterns': basic_patterns,
                    'ai_interests_summary': ai_summary,
                    'analysis_info': {
                        'method': 'AI-based semantic analysis',
                        'description': '基于DeepSeek大模型的语义分析，理解用户真实兴趣偏好'
                    }
                }
            })
            
        except Exception as e:
            print(f"❌ 分析用户模式失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/stats')
    def api_get_interaction_stats():
        """获取交互统计信息"""
        try:
            days = request.args.get('days', default=30, type=int)
            days = min(max(days, 1), 365)  # 限制在1-365天之间
            
            stats = interaction_tracker.get_interaction_stats(days=days)
            
            return jsonify({
                'success': True,
                'data': {
                    'stats': stats,
                    'period_days': days
                }
            })
            
        except Exception as e:
            print(f"❌ 获取交互统计失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/mark-interest', methods=['POST'])
    def api_mark_explicit_interest():
        """明确标记对论文的兴趣（喜欢/不喜欢）"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            paper_id = data.get('paper_id')
            interest_type = data.get('interest_type')  # 'like' or 'dislike'
            
            if not paper_id or interest_type not in ['like', 'dislike']:
                return jsonify({
                    'success': False, 
                    'error': '参数错误，interest_type必须是like或dislike'
                }), 400
            
            interaction_type = (InteractionTracker.INTERACTION_TYPES['EXPLICIT_LIKE'] 
                              if interest_type == 'like' 
                              else InteractionTracker.INTERACTION_TYPES['EXPLICIT_DISLIKE'])
            
            session_id = data.get('session_id') or str(uuid.uuid4())
            
            success = interaction_tracker.track_interaction(
                paper_id=paper_id,
                interaction_type=interaction_type,
                session_id=session_id,
                user_agent=request.headers.get('User-Agent')
            )
            
            if success:
                # 🔄 触发增量更新 - 用户兴趣发生重要变化
                _trigger_incremental_update('explicit_interest_marking', {
                    'paper_id': paper_id,
                    'interest_type': interest_type,
                    'session_id': session_id
                })
                
                return jsonify({
                    'success': True,
                    'message': f'已标记为{"感兴趣" if interest_type == "like" else "不感兴趣"}',
                    'paper_id': paper_id,
                    'interest_type': interest_type,
                    'cache_update': '推荐系统正在后台更新中'
                })
            else:
                return jsonify({'success': False, 'error': '标记失败'}), 500
                
        except Exception as e:
            print(f"❌ 标记兴趣失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/ai-analysis-info')
    def api_get_ai_analysis_info():
        """获取AI分析算法的详细信息"""
        try:
            return jsonify({
                'success': True,
                'data': {
                    'algorithm_description': '基于DeepSeek大模型的语义分析推荐算法',
                    'analysis_method': {
                        'step1': '提取用户明确喜爱论文的标题和摘要',
                        'step2': '使用大模型分析用户的研究兴趣和偏好',
                        'step3': '对候选论文进行语义相似度评估',
                        'step4': '生成推荐分数和详细理由'
                    },
                    'advantages': [
                        '语义理解：能理解论文的深层含义，不只是关键词匹配',
                        '避免噪音：自动过滤停用词和无意义词汇',
                        '上下文感知：考虑词汇在特定语境中的含义',
                        '可解释性：为每个推荐提供详细的匹配理由'
                    ],
                    'model_info': {
                        'provider': 'DeepSeek',
                        'model': 'deepseek-chat',
                        'temperature': 0.1,
                        'max_tokens': 2000
                    },
                    'generated_at': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ 获取AI分析信息失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/dashboard')
    def api_recommendation_dashboard():
        """推荐系统仪表板数据"""
        try:
            # 获取各种统计数据
            stats = interaction_tracker.get_interaction_stats(days=30)
            patterns = interaction_tracker.analyze_user_patterns()
            # 获取用户喜爱的论文作为高兴趣论文
            liked_papers = ai_recommender._get_user_liked_papers()
            recommendations = ai_recommender.get_personalized_recommendations(limit=5)
            
            dashboard_data = {
                'recent_stats': stats,
                'interest_patterns': {
                    'top_keywords': list(patterns.get('keyword_patterns', {}).keys())[:10],
                    'total_analyzed_papers': patterns.get('total_analyzed_papers', 0)
                },
                'liked_papers': {
                    'count': len(liked_papers),
                    'papers': liked_papers[:5]  # 只返回前5篇
                },
                'latest_recommendations': {
                    'count': len(recommendations),
                    'papers': recommendations
                },
                'system_health': {
                    'has_liked_papers': len(liked_papers) > 0,
                    'has_patterns': len(patterns.get('keyword_patterns', {})) > 0,
                    'can_recommend': len(recommendations) > 0,
                    'ai_service_available': True
                },
                'generated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            print(f"❌ 获取推荐仪表板数据失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ================== 异步推荐缓存管理API ==================
    
    @app.route('/api/recommendations/cache/status')
    def api_get_cache_status():
        """获取推荐缓存系统状态"""
        try:
            status = cache_manager.get_cache_status()
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            print(f"❌ 获取缓存状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/cache/warm-up', methods=['POST'])
    def api_warm_up_cache():
        """手动预热推荐缓存"""
        try:
            cache_manager.warm_up_cache()
            
            return jsonify({
                'success': True,
                'message': '缓存预热任务已启动，推荐数据将在后台计算'
            })
            
        except Exception as e:
            print(f"❌ 缓存预热失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/cache/clear', methods=['POST'])
    def api_clear_cache():
        """清理过期缓存"""
        try:
            deleted_count = cache_manager.clear_expired_cache()
            
            return jsonify({
                'success': True,
                'message': f'已清理 {deleted_count} 条过期缓存',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            print(f"❌ 清理缓存失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/cache/refresh', methods=['POST'])
    def api_force_refresh_cache():
        """强制刷新所有推荐缓存"""
        try:
            cache_manager.force_refresh_cache()
            
            return jsonify({
                'success': True,
                'message': '推荐缓存已强制刷新，新数据将在后台重新计算'
            })
            
        except Exception as e:
            print(f"❌ 强制刷新缓存失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/jobs', methods=['POST'])
    def api_create_recommendation_job():
        """手动创建推荐计算任务"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            job_type = data.get('job_type')  # 'full_recompute', 'similar'
            priority = data.get('priority', 5)
            
            if job_type == 'full_recompute':
                recommendation_processor.create_full_recompute_job(priority)
                message = '全量重计算任务已创建'
                
            elif job_type == 'similar':
                paper_id = data.get('paper_id')
                limit = data.get('limit', 5)
                
                if not paper_id:
                    return jsonify({'success': False, 'error': '相似推荐任务需要paper_id参数'}), 400
                
                recommendation_processor.create_similar_job(paper_id, limit, priority)
                message = f'论文 {paper_id} 的相似推荐任务已创建'
                
            else:
                return jsonify({'success': False, 'error': '不支持的任务类型'}), 400
            
            return jsonify({
                'success': True,
                'message': message,
                'job_type': job_type
            })
            
        except Exception as e:
            print(f"❌ 创建推荐任务失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/jobs/status')
    def api_get_job_status():
        """获取推荐任务处理状态"""
        try:
            status = recommendation_processor.get_job_status()
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            print(f"❌ 获取任务状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ================== 内部辅助函数 ==================
    
    def _trigger_incremental_update(trigger_reason: str, context_data: dict = None):
        """触发增量更新的内部函数"""
        try:
            import json
            
            reference_data = json.dumps({
                'trigger_reason': trigger_reason,
                'context': context_data or {},
                'triggered_at': datetime.now().isoformat(),
                'triggered_by': 'user_interaction'
            })
            
            # 创建增量更新任务
            conn = Database(DATABASE_PATH).get_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO recommendation_jobs
                (job_type, priority, reference_data)
                VALUES ('incremental', 8, ?)
            ''', (reference_data,))
            
            conn.commit()
            conn.close()
            
            print(f"🔄 已触发增量更新: {trigger_reason}")
            
        except Exception as e:
            print(f"❌ 触发增量更新失败: {e}")
    
    # 添加其他关键交互的触发器
    
    @app.route('/api/interactions/bookmark', methods=['POST'])
    def api_mark_bookmark():
        """标记收藏论文（会触发推荐更新）"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            paper_id = data.get('paper_id')
            action = data.get('action', 'add')  # 'add' or 'remove'
            
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数'}), 400
            
            interaction_type = (InteractionTracker.INTERACTION_TYPES['BOOKMARK'] 
                              if action == 'add' 
                              else InteractionTracker.INTERACTION_TYPES['UNBOOKMARK'])
            
            session_id = data.get('session_id') or str(uuid.uuid4())
            
            success = interaction_tracker.track_interaction(
                paper_id=paper_id,
                interaction_type=interaction_type,
                session_id=session_id,
                user_agent=request.headers.get('User-Agent')
            )
            
            if success:
                # 触发增量更新
                _trigger_incremental_update('bookmark_action', {
                    'paper_id': paper_id,
                    'action': action,
                    'session_id': session_id
                })
                
                return jsonify({
                    'success': True,
                    'message': f'已{"收藏" if action == "add" else "取消收藏"}论文',
                    'paper_id': paper_id,
                    'action': action,
                    'cache_update': '推荐系统正在后台更新中'
                })
            else:
                return jsonify({'success': False, 'error': '操作失败'}), 500
                
        except Exception as e:
            print(f"❌ 收藏操作失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/interactions/pdf-click', methods=['POST'])
    def api_track_pdf_click():
        """记录PDF点击（表示深度兴趣，会触发推荐更新）"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            paper_id = data.get('paper_id')
            
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数'}), 400
            
            session_id = data.get('session_id') or str(uuid.uuid4())
            
            success = interaction_tracker.track_interaction(
                paper_id=paper_id,
                interaction_type=InteractionTracker.INTERACTION_TYPES['CLICK_PDF'],
                session_id=session_id,
                user_agent=request.headers.get('User-Agent')
            )
            
            if success:
                # PDF点击表示用户对该论文有深度兴趣，触发增量更新
                _trigger_incremental_update('pdf_click', {
                    'paper_id': paper_id,
                    'session_id': session_id,
                    'deep_interest': True
                })
                
                return jsonify({
                    'success': True,
                    'message': 'PDF点击已记录',
                    'paper_id': paper_id,
                    'cache_update': '推荐系统正在后台更新中'
                })
            else:
                return jsonify({'success': False, 'error': '记录失败'}), 500
                
        except Exception as e:
            print(f"❌ 记录PDF点击失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ================== 推荐系统管理API ==================
    
    @app.route('/api/recommendations/system/status')
    def api_get_system_status():
        """获取推荐系统整体状态"""
        try:
            status = scheduler.get_system_status()
            
            return jsonify({
                'success': True,
                'data': status
            })
            
        except Exception as e:
            print(f"❌ 获取系统状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/system/health')
    def api_health_check():
        """推荐系统健康检查"""
        try:
            health = scheduler.health_check()
            
            # 根据健康状态设置HTTP状态码
            status_code = 200 if health.get('overall_health') == 'healthy' else 503
            
            return jsonify({
                'success': health.get('overall_health') == 'healthy',
                'data': health
            }), status_code
            
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/system/start', methods=['POST'])
    def api_start_system():
        """启动推荐系统服务"""
        try:
            scheduler.start_services()
            
            return jsonify({
                'success': True,
                'message': '推荐系统服务已启动'
            })
            
        except Exception as e:
            print(f"❌ 启动系统失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/system/stop', methods=['POST'])
    def api_stop_system():
        """停止推荐系统服务"""
        try:
            scheduler.stop_services()
            
            return jsonify({
                'success': True,
                'message': '推荐系统服务已停止'
            })
            
        except Exception as e:
            print(f"❌ 停止系统失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/system/restart', methods=['POST'])
    def api_restart_system():
        """重启推荐系统服务"""
        try:
            scheduler.restart_services()
            
            return jsonify({
                'success': True,
                'message': '推荐系统服务已重启'
            })
            
        except Exception as e:
            print(f"❌ 重启系统失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/system/emergency-warmup', methods=['POST'])
    def api_emergency_warmup():
        """紧急缓存预热"""
        try:
            scheduler.emergency_warmup()
            
            return jsonify({
                'success': True,
                'message': '紧急缓存预热已触发，推荐数据将在后台重新计算'
            })
            
        except Exception as e:
            print(f"❌ 紧急预热失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/recommendations/system/configure', methods=['POST'])
    def api_configure_system():
        """配置推荐系统参数"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            success = scheduler.configure(**data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '推荐系统配置已更新'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '配置更新失败'
                }), 400
                
        except Exception as e:
            print(f"❌ 配置系统失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500