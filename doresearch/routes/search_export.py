"""
搜索导出路由模块
"""
from flask import Flask, request, jsonify
from datetime import datetime
from services.search_service import SearchService
from .search_utils import SearchParameterValidator, SearchResponseBuilder


def setup_search_export_routes(app: Flask, search_service: SearchService):
    """设置搜索导出路由"""
    
    @app.route('/api/search/export')
    def api_export_search_results():
        """导出搜索结果"""
        try:
            query = request.args.get('q', '').strip()
            
            # 验证查询参数
            error = SearchParameterValidator.validate_query(query)
            if error:
                return jsonify(SearchResponseBuilder.build_error_response(error))
            
            export_format = request.args.get('format', 'json')
            
            # 获取所有搜索结果（不分页）
            result = search_service.search_papers(
                query=query,
                search_fields=['title', 'abstract', 'authors'],
                limit=1000,  # 设置较大的限制
                offset=0,
                order_by='relevance'
            )
            
            if not result['success']:
                return jsonify(result)
            
            papers = result['data']['results']
            
            if export_format == 'json':
                return jsonify(SearchResponseBuilder.build_success_response({
                    'query': query,
                    'export_format': 'json',
                    'export_date': datetime.now().isoformat(),
                    'results': papers,
                    'count': len(papers)
                }))
            
            elif export_format == 'csv':
                # 准备CSV数据
                csv_data = []
                for paper in papers:
                    csv_data.append({
                        'ID': paper['id'],
                        'Title': paper['title'],
                        'Authors': paper['authors'] or '',
                        'Journal': paper['journal'] or '',
                        'Published Date': paper['published_date'] or '',
                        'Status': paper['status'],
                        'URL': paper['url'] or '',
                        'DOI': paper['doi'] or '',
                        'Abstract': (paper['abstract'] or '')[:200] + '...' if len(paper['abstract'] or '') > 200 else paper['abstract'] or '',
                        'Relevance Score': paper.get('relevance_score', 0)
                    })
                
                filename = f"search_results_{datetime.now().strftime('%Y%m%d')}.csv"
                return SearchResponseBuilder.build_csv_response(csv_data, filename)
            
            else:
                return jsonify(SearchResponseBuilder.build_error_response(
                    '不支持的导出格式，支持: json, csv'
                ))
                
        except Exception as e:
            print(f"❌ 导出搜索结果失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(str(e), 500))
    
    @app.route('/api/search/similar/<int:paper_id>')
    def api_find_similar_papers(paper_id):
        """查找相似论文"""
        try:
            from services.paper_manager import PaperManager
            paper_manager = PaperManager()
            
            # 获取目标论文
            paper = paper_manager.get_paper(paper_id)
            if not paper:
                return jsonify(SearchResponseBuilder.build_error_response(
                    '论文不存在', 404
                ))
            
            # 提取关键词进行搜索
            keywords = []
            
            # 从标题提取关键词
            if paper['title']:
                title_words = [word for word in paper['title'].split() if len(word) > 3]
                keywords.extend(title_words[:5])  # 取前5个词
            
            # 从期刊名提取
            if paper['journal']:
                keywords.append(paper['journal'])
            
            # 从作者中提取姓氏
            if paper['authors']:
                author_words = [word for word in paper['authors'].replace(',', ' ').split() if len(word) > 2]
                keywords.extend(author_words[:3])  # 取前3个作者相关词
            
            if not keywords:
                return jsonify(SearchResponseBuilder.build_success_response({
                    'paper_id': paper_id,
                    'similar_papers': [],
                    'keywords_used': []
                }))
            
            # 使用关键词搜索相似论文
            query = ' '.join(keywords)
            limit = int(request.args.get('limit', 10))
            if limit <= 0 or limit > 50:
                limit = 10
            
            # 执行搜索，排除自身
            result = search_service.search_papers(
                query=query,
                search_fields=['title', 'abstract', 'authors'],
                filters={'exclude_id': paper_id},
                limit=limit + 1,  # 多取一个以防自身被包含
                offset=0,
                order_by='relevance'
            )
            
            if result['success']:
                similar_papers = result['data']['results']
                # 确保排除目标论文自身
                similar_papers = [p for p in similar_papers if p['id'] != paper_id][:limit]
                
                return jsonify(SearchResponseBuilder.build_success_response({
                    'paper_id': paper_id,
                    'similar_papers': similar_papers,
                    'keywords_used': keywords,
                    'total': len(similar_papers)
                }))
            else:
                return jsonify(result)
                
        except Exception as e:
            print(f"❌ 查找相似论文失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(str(e), 500))