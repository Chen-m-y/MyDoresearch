"""
基础搜索路由模块
"""
from flask import Flask, request, jsonify
from services.search_service import SearchService
from .search_utils import SearchParameterValidator, SearchResponseBuilder


def setup_basic_search_routes(app: Flask, search_service: SearchService):
    """设置基础搜索路由"""
    
    @app.route('/api/search', methods=['GET'])
    def api_search_papers():
        """搜索论文"""
        try:
            # 获取查询参数
            query = request.args.get('q', '').strip()
            
            # 验证查询参数
            error = SearchParameterValidator.validate_query(query)
            if error:
                return jsonify(SearchResponseBuilder.build_error_response(error))
            
            # 验证搜索字段
            search_fields = request.args.getlist('fields')
            if not search_fields:
                search_fields = ['title', 'abstract', 'authors']
            search_fields = SearchParameterValidator.validate_search_fields(search_fields)
            
            # 构建过滤条件
            filters = SearchParameterValidator.build_filters()
            
            # 验证分页参数
            limit, offset, pagination_error = SearchParameterValidator.validate_pagination(
                request.args.get('limit'),
                request.args.get('offset')
            )
            if pagination_error:
                return jsonify(SearchResponseBuilder.build_error_response(pagination_error))
            
            # 验证排序参数
            order_by = SearchParameterValidator.validate_order_by(
                request.args.get('order_by', 'relevance')
            )
            
            # 执行搜索
            result = search_service.search_papers(
                query=query,
                search_fields=search_fields,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(
                f'搜索过程中发生错误: {str(e)}', 500
            ))
    
    @app.route('/api/search/quick')
    def api_quick_search():
        """快速搜索"""
        try:
            query = request.args.get('q', '').strip()
            
            # 验证查询参数
            error = SearchParameterValidator.validate_query(query)
            if error:
                return jsonify(SearchResponseBuilder.build_error_response(error))
            
            # 快速搜索只搜索标题和作者，限制结果数量
            result = search_service.search_papers(
                query=query,
                search_fields=['title', 'authors'],
                filters={},
                limit=10,
                offset=0,
                order_by='relevance'
            )
            
            # 只返回必要字段
            if result.get('success') and result.get('papers'):
                simplified_papers = []
                for paper in result['papers']:
                    simplified_papers.append({
                        'id': paper.get('id'),
                        'title': paper.get('title', ''),
                        'authors': paper.get('authors', ''),
                        'published_date': paper.get('published_date', ''),
                        'journal': paper.get('journal', '')
                    })
                
                return jsonify(SearchResponseBuilder.build_success_response({
                    'papers': simplified_papers,
                    'total': result.get('total', 0)
                }))
            
            return jsonify(result)
            
        except Exception as e:
            print(f"❌ 快速搜索失败: {e}")
            return jsonify(SearchResponseBuilder.build_error_response(
                f'快速搜索过程中发生错误: {str(e)}', 500
            ))