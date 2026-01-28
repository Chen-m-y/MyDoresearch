"""
搜索元数据路由模块
"""
from flask import Flask, request, jsonify
from services.search_service import SearchService
from .search_utils import SearchResponseBuilder


def setup_search_metadata_routes(app: Flask, search_service: SearchService):
    """设置搜索元数据路由"""
    
    @app.route('/api/search/popular')
    def api_popular_searches():
        """获取热门搜索"""
        try:
            limit = int(request.args.get('limit', 10))
            
            if limit <= 0 or limit > 50:
                limit = 10
            
            popular_terms = search_service.get_popular_searches(limit)
            
            return jsonify(SearchResponseBuilder.build_success_response({
                'popular_searches': popular_terms
            }))
            
        except Exception as e:
            print(f"❌ 获取热门搜索失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(str(e), 500))
    
    @app.route('/api/search/filters')
    def api_search_filters():
        """获取可用的搜索过滤选项"""
        try:
            from services.paper_manager import PaperManager
            paper_manager = PaperManager()
            
            conn = paper_manager.get_db()
            c = conn.cursor()
            
            # 获取所有期刊
            c.execute('''SELECT DISTINCT journal, COUNT(*) as count 
                        FROM papers 
                        WHERE journal IS NOT NULL AND journal != ''
                        GROUP BY journal 
                        ORDER BY count DESC 
                        LIMIT 50''')
            journals = [{'name': row[0], 'count': row[1]} for row in c.fetchall()]
            
            # 获取所有论文源
            c.execute('SELECT id, name FROM feeds WHERE active = 1 ORDER BY name')
            feeds = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
            
            # 获取状态统计
            c.execute('''SELECT status, COUNT(*) as count 
                        FROM papers 
                        GROUP BY status''')
            statuses = [{'name': row[0], 'count': row[1]} for row in c.fetchall()]
            
            conn.close()
            
            return jsonify(SearchResponseBuilder.build_success_response({
                'search_fields': [
                    {'value': 'title', 'label': '标题'},
                    {'value': 'abstract', 'label': '摘要'},
                    {'value': 'abstract_cn', 'label': '中文摘要'},
                    {'value': 'authors', 'label': '作者'},
                    {'value': 'journal', 'label': '期刊'},
                    {'value': 'doi', 'label': 'DOI'}
                ],
                'order_options': [
                    {'value': 'relevance', 'label': '相关性'},
                    {'value': 'date', 'label': '发布时间'},
                    {'value': 'title', 'label': '标题'},
                    {'value': 'created_at', 'label': '添加时间'}
                ],
                'journals': journals,
                'feeds': feeds,
                'statuses': statuses
            }))
            
        except Exception as e:
            print(f"❌ 获取搜索过滤选项失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(str(e), 500))
    
    @app.route('/api/search/stats')
    def api_search_stats():
        """获取搜索统计信息"""
        try:
            from services.paper_manager import PaperManager
            paper_manager = PaperManager()
            
            conn = paper_manager.get_db()
            c = conn.cursor()
            
            # 总论文数
            c.execute('SELECT COUNT(*) FROM papers')
            total_papers = c.fetchone()[0]
            
            # 按状态分组统计
            c.execute('SELECT status, COUNT(*) FROM papers GROUP BY status')
            status_stats = {row[0]: row[1] for row in c.fetchall()}
            
            # 有PDF的论文数
            c.execute('SELECT COUNT(*) FROM papers WHERE pdf_path IS NOT NULL AND pdf_path != ""')
            papers_with_pdf = c.fetchone()[0]
            
            # 有分析结果的论文数
            c.execute('SELECT COUNT(*) FROM papers WHERE analysis_result IS NOT NULL AND analysis_result != ""')
            papers_with_analysis = c.fetchone()[0]
            
            # 最近30天新增论文数
            c.execute('''SELECT COUNT(*) FROM papers 
                        WHERE created_at >= datetime('now', '-30 days')''')
            recent_papers = c.fetchone()[0]
            
            conn.close()
            
            return jsonify(SearchResponseBuilder.build_success_response({
                'total_papers': total_papers,
                'status_stats': status_stats,
                'papers_with_pdf': papers_with_pdf,
                'papers_with_analysis': papers_with_analysis,
                'recent_papers': recent_papers
            }))
            
        except Exception as e:
            print(f"❌ 获取搜索统计失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(str(e), 500))