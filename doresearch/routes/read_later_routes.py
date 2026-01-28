"""
稍后阅读路由模块
"""
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from services.read_later_service import ReadLaterService
from middleware.auth_middleware import auth_required, get_current_user_id
import csv
import io


def setup_read_later_routes(app: Flask):
    """设置稍后阅读相关路由"""
    
    read_later_service = ReadLaterService()
    
    @app.route('/api/read-later', methods=['POST'])
    @auth_required
    def api_mark_read_later():
        """标记论文为稍后阅读"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            paper_id = data.get('paper_id')
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数'}), 400
            
            priority = data.get('priority', 5)
            notes = data.get('notes')
            tags = data.get('tags')
            estimated_read_time = data.get('estimated_read_time')
            
            # 验证priority范围
            if not (1 <= priority <= 10):
                return jsonify({'success': False, 'error': '优先级必须在1-10之间'}), 400
            
            user_id = get_current_user_id()
            result = read_later_service.mark_read_later(
                paper_id=paper_id,
                user_id=user_id,
                priority=priority,
                notes=notes,
                tags=tags,
                estimated_read_time=estimated_read_time
            )
            
            return jsonify(result), 200 if result['success'] else 400
            
        except Exception as e:
            print(f"❌ 标记稍后阅读失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/<int:paper_id>', methods=['DELETE'])
    @auth_required
    def api_unmark_read_later(paper_id):
        """取消标记稍后阅读"""
        try:
            user_id = get_current_user_id()
            result = read_later_service.unmark_read_later(paper_id, user_id)
            return jsonify(result), 200 if result['success'] else 400
            
        except Exception as e:
            print(f"❌ 取消标记稍后阅读失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/<int:paper_id>', methods=['PUT'])
    @auth_required
    def api_update_read_later(paper_id):
        """更新稍后阅读信息"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            priority = data.get('priority')
            notes = data.get('notes')
            tags = data.get('tags')
            estimated_read_time = data.get('estimated_read_time')
            
            # 验证priority范围
            if priority is not None and not (1 <= priority <= 10):
                return jsonify({'success': False, 'error': '优先级必须在1-10之间'}), 400
            
            user_id = get_current_user_id()
            result = read_later_service.update_read_later(
                paper_id=paper_id,
                user_id=user_id,
                priority=priority,
                notes=notes,
                tags=tags,
                estimated_read_time=estimated_read_time
            )
            
            return jsonify(result), 200 if result['success'] else 400
            
        except Exception as e:
            print(f"❌ 更新稍后阅读失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later')
    @auth_required
    def api_get_read_later_list():
        """获取稍后阅读列表"""
        try:
            # 获取查询参数
            order_by = request.args.get('order_by', 'priority')
            
            # 支持page/per_page分页参数
            page = request.args.get('page', type=int)
            per_page = request.args.get('per_page', type=int)
            
            # 支持原有的limit/offset参数（向后兼容）
            limit = request.args.get('limit', type=int)
            offset = request.args.get('offset', default=0, type=int)
            
            # 如果提供了page和per_page，转换为limit和offset
            if page is not None and per_page is not None:
                limit = per_page
                offset = (page - 1) * per_page
            
            # 验证排序参数
            valid_orders = ['priority', 'marked_at', 'title', 'published_date']
            if order_by not in valid_orders:
                return jsonify({
                    'success': False,
                    'error': f'无效的排序参数，支持: {valid_orders}'
                }), 400
            
            user_id = get_current_user_id()
            read_later_list = read_later_service.get_read_later_list(
                user_id=user_id,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            
            # 获取总数（用于分页）
            total_count = read_later_service.get_read_later_count(user_id)
            
            # 计算分页信息
            if page is not None and per_page is not None:
                has_more = (page * per_page) < total_count
                current_page = page
                total_pages = (total_count + per_page - 1) // per_page
                
                return jsonify({
                    'success': True,
                    'data': {
                        'items': read_later_list,
                        'total_count': total_count,
                        'current_page': current_page,
                        'per_page': per_page,
                        'total_pages': total_pages,
                        'has_more': has_more
                    }
                })
            else:
                # 原有格式（向后兼容）
                return jsonify({
                    'success': True,
                    'data': {
                        'items': read_later_list,
                        'total_count': total_count,
                        'offset': offset,
                        'limit': limit,
                        'has_more': limit and (offset + limit) < total_count
                    }
                })
            
        except Exception as e:
            print(f"❌ 获取稍后阅读列表失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/<int:paper_id>/check')
    @auth_required
    def api_check_read_later_status(paper_id):
        """检查论文是否标记为稍后阅读"""
        try:
            is_marked = read_later_service.is_marked_read_later(paper_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'paper_id': paper_id,
                    'is_marked': is_marked
                }
            })
            
        except Exception as e:
            print(f"❌ 检查稍后阅读状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/stats')
    @auth_required
    def api_read_later_stats():
        """获取稍后阅读统计信息"""
        try:
            stats = read_later_service.get_read_later_stats()
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            print(f"❌ 获取稍后阅读统计失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/search')
    @auth_required
    def api_search_read_later():
        """搜索稍后阅读列表"""
        try:
            query = request.args.get('q')
            if not query:
                return jsonify({'success': False, 'error': '缺少搜索查询参数q'}), 400
            
            search_in = request.args.getlist('search_in')
            if not search_in:
                search_in = ['title', 'abstract', 'authors', 'notes', 'tags']
            
            results = read_later_service.search_read_later(query, search_in)
            
            return jsonify({
                'success': True,
                'data': {
                    'query': query,
                    'search_in': search_in,
                    'results': results,
                    'count': len(results)
                }
            })
            
        except Exception as e:
            print(f"❌ 搜索稍后阅读列表失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/bulk-update', methods=['POST'])
    def api_bulk_update_read_later():
        """批量更新稍后阅读"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            action = data.get('action')
            paper_ids = data.get('paper_ids', [])
            
            if not paper_ids:
                return jsonify({'success': False, 'error': '缺少paper_ids参数'}), 400
            
            if not isinstance(paper_ids, list):
                return jsonify({'success': False, 'error': 'paper_ids必须是数组'}), 400
            
            if action == 'update_priority':
                priority = data.get('priority')
                if priority is None:
                    return jsonify({'success': False, 'error': '缺少priority参数'}), 400
                
                if not (1 <= priority <= 10):
                    return jsonify({'success': False, 'error': '优先级必须在1-10之间'}), 400
                
                result = read_later_service.bulk_update_priority(paper_ids, priority)
                
            elif action == 'remove':
                success_count = 0
                failed_count = 0
                
                for paper_id in paper_ids:
                    result = read_later_service.unmark_read_later(paper_id)
                    if result['success']:
                        success_count += 1
                    else:
                        failed_count += 1
                
                result = {
                    'success': True,
                    'message': f'成功移除 {success_count} 篇，失败 {failed_count} 篇',
                    'success_count': success_count,
                    'failed_count': failed_count
                }
                
            else:
                return jsonify({'success': False, 'error': '不支持的操作类型'}), 400
            
            return jsonify(result), 200 if result['success'] else 400
            
        except Exception as e:
            print(f"❌ 批量更新稍后阅读失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/quick-add', methods=['POST'])
    @auth_required
    def api_quick_add_read_later():
        """快速添加到稍后阅读（简化版）"""
        try:
            data = request.get_json()
            paper_id = data.get('paper_id') if data else None
            
            if not paper_id:
                return jsonify({'success': False, 'error': '缺少paper_id参数'}), 400
            
            # 使用默认优先级快速添加
            user_id = get_current_user_id()
            result = read_later_service.mark_read_later(paper_id=paper_id, user_id=user_id)
            
            return jsonify(result), 200 if result['success'] else 400
            
        except Exception as e:
            print(f"❌ 快速添加稍后阅读失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/export')
    def api_export_read_later():
        """导出稍后阅读列表"""
        try:
            export_format = request.args.get('format', 'json')
            
            read_later_list = read_later_service.get_read_later_list()
            
            if export_format == 'json':
                return jsonify({
                    'success': True,
                    'data': {
                        'export_format': 'json',
                        'export_date': datetime.now().isoformat(),
                        'items': read_later_list,
                        'count': len(read_later_list)
                    }
                })
                
            elif export_format == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)
                
                # 写入标题行
                writer.writerow([
                    'Paper ID', 'Title', 'Authors', 'Journal', 'Priority',
                    'Notes', 'Tags', 'Estimated Read Time', 'Marked At', 'URL'
                ])
                
                # 写入数据行
                for item in read_later_list:
                    writer.writerow([
                        item['paper_id'],
                        item['title'],
                        item['authors'],
                        item['journal'],
                        item['priority'],
                        item['notes'] or '',
                        ', '.join(item['tags']) if item['tags'] else '',
                        item['estimated_read_time'] or '',
                        item['marked_at'],
                        item['url']
                    ])
                
                response = make_response(output.getvalue())
                response.headers['Content-Type'] = 'text/csv'
                response.headers['Content-Disposition'] = f'attachment; filename=read_later_{datetime.now().strftime("%Y%m%d")}.csv'
                
                return response
                
            else:
                return jsonify({'success': False, 'error': '不支持的导出格式'}), 400
                
        except Exception as e:
            print(f"❌ 导出稍后阅读列表失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/read-later/priorities')
    def api_get_priority_options():
        """获取优先级选项"""
        priority_options = [
            {'value': 1, 'label': '最低', 'color': '#6b7280'},
            {'value': 2, 'label': '较低', 'color': '#9ca3af'},
            {'value': 3, 'label': '低', 'color': '#d1d5db'},
            {'value': 4, 'label': '偏低', 'color': '#fbbf24'},
            {'value': 5, 'label': '普通', 'color': '#f59e0b'},
            {'value': 6, 'label': '偏高', 'color': '#f97316'},
            {'value': 7, 'label': '高', 'color': '#ea580c'},
            {'value': 8, 'label': '较高', 'color': '#dc2626'},
            {'value': 9, 'label': '很高', 'color': '#b91c1c'},
            {'value': 10, 'label': '最高', 'color': '#991b1b'}
        ]
        
        return jsonify({
            'success': True,
            'data': priority_options
        })
    
    @app.route('/api/papers/<int:paper_id>/read-later-info')
    def api_get_paper_read_later_info(paper_id):
        """获取论文的稍后阅读信息"""
        try:
            from services.paper_manager import PaperManager
            
            paper_manager = PaperManager()
            
            # 获取论文基本信息
            paper = paper_manager.get_paper(paper_id)
            if not paper:
                return jsonify({'success': False, 'error': '论文不存在'}), 404
            
            # 检查是否在稍后阅读列表中
            is_marked = read_later_service.is_marked_read_later(paper_id)
            
            read_later_info = None
            if is_marked:
                # 获取稍后阅读详细信息
                read_later_list = read_later_service.get_read_later_list()
                for item in read_later_list:
                    if item['paper_id'] == paper_id:
                        read_later_info = {
                            'priority': item['priority'],
                            'notes': item['notes'],
                            'tags': item['tags'],
                            'estimated_read_time': item['estimated_read_time'],
                            'marked_at': item['marked_at'],
                            'updated_at': item['updated_at']
                        }
                        break
            
            return jsonify({
                'success': True,
                'data': {
                    'paper_id': paper_id,
                    'title': paper['title'],
                    'is_marked': is_marked,
                    'read_later_info': read_later_info
                }
            })
            
        except Exception as e:
            print(f"❌ 获取论文稍后阅读信息失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500