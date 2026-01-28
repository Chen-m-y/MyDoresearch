"""
高级搜索路由模块
"""
from flask import Flask, request, jsonify
from services.search_service import SearchService
from .search_utils import SearchParameterValidator, SearchResponseBuilder


def setup_advanced_search_routes(app: Flask, search_service: SearchService):
    """设置高级搜索路由"""
    
    @app.route('/api/search/advanced', methods=['POST'])
    def api_advanced_search():
        """高级搜索"""
        try:
            data = request.get_json()
            if not data:
                return jsonify(SearchResponseBuilder.build_error_response('请求数据为空'))
            
            # 验证必要参数
            query = data.get('query', '').strip()
            error = SearchParameterValidator.validate_query(query)
            if error:
                return jsonify(SearchResponseBuilder.build_error_response(error))
            
            # 构建搜索条件
            criteria = {
                'query': query,
                'search_fields': data.get('search_fields', ['title', 'abstract', 'authors']),
                'status': data.get('status'),
                'journal': data.get('journal'),
                'feed_id': data.get('feed_id'),
                'date_range': data.get('date_range'),
                'has_pdf': data.get('has_pdf'),
                'has_analysis': data.get('has_analysis'),
                'limit': data.get('limit', 20),
                'offset': data.get('offset', 0),
                'order_by': data.get('order_by', 'relevance')
            }
            
            # 验证参数
            if criteria['limit'] <= 0 or criteria['limit'] > 100:
                criteria['limit'] = 20
            if criteria['offset'] < 0:
                criteria['offset'] = 0
            
            criteria['search_fields'] = SearchParameterValidator.validate_search_fields(
                criteria['search_fields']
            )
            criteria['order_by'] = SearchParameterValidator.validate_order_by(
                criteria['order_by']
            )
            
            # 执行高级搜索
            result = search_service.advanced_search(criteria)
            
            return jsonify(result)
            
        except Exception as e:
            print(f"❌ 高级搜索失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(
                f'高级搜索过程中发生错误: {str(e)}', 500
            ))
    
    @app.route('/api/search/suggestions')
    def api_search_suggestions():
        """获取搜索建议"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 10))
            
            if len(query) < 2:
                return jsonify(SearchResponseBuilder.build_success_response({
                    'query': query,
                    'suggestions': []
                }))
            
            if limit <= 0 or limit > 50:
                limit = 10
            
            suggestions = search_service.get_search_suggestions(query, limit)
            
            return jsonify(SearchResponseBuilder.build_success_response({
                'query': query,
                'suggestions': suggestions
            }))
            
        except Exception as e:
            print(f"❌ 获取搜索建议失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(
                f'获取搜索建议时发生错误: {str(e)}', 500
            ))