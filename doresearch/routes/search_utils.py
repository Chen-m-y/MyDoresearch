"""
搜索路由工具模块
"""
from flask import request, jsonify, make_response
from typing import Dict, Any, List, Optional, Tuple
import csv
import io


class SearchParameterValidator:
    """搜索参数验证器"""
    
    @staticmethod
    def validate_query(query: str) -> Optional[str]:
        """验证搜索查询"""
        if not query or not query.strip():
            return "搜索关键词不能为空"
        return None
    
    @staticmethod
    def validate_search_fields(fields: List[str]) -> List[str]:
        """验证和过滤搜索字段"""
        valid_fields = ['title', 'abstract', 'abstract_cn', 'authors', 'journal', 'doi']
        validated_fields = [field for field in fields if field in valid_fields]
        
        if not validated_fields:
            return ['title', 'abstract', 'authors']
        
        return validated_fields
    
    @staticmethod
    def validate_pagination(limit_str: str, offset_str: str) -> Tuple[int, int, Optional[str]]:
        """验证分页参数"""
        try:
            limit = int(limit_str) if limit_str else 20
            offset = int(offset_str) if offset_str else 0
            
            if limit <= 0 or limit > 100:
                limit = 20
            if offset < 0:
                offset = 0
                
            return limit, offset, None
            
        except ValueError:
            return 20, 0, "limit和offset必须是有效的整数"
    
    @staticmethod
    def validate_order_by(order_by: str) -> str:
        """验证排序参数"""
        valid_orders = ['relevance', 'date', 'title', 'created_at']
        return order_by if order_by in valid_orders else 'relevance'
    
    @staticmethod
    def build_filters() -> Dict[str, Any]:
        """构建过滤条件"""
        filters = {}
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('journal'):
            filters['journal'] = request.args.get('journal')
        
        if request.args.get('feed_id'):
            try:
                filters['feed_id'] = int(request.args.get('feed_id'))
            except ValueError:
                pass  # 忽略无效的feed_id
        
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        if request.args.get('has_pdf') is not None:
            filters['has_pdf'] = request.args.get('has_pdf').lower() == 'true'
        
        if request.args.get('has_analysis') is not None:
            filters['has_analysis'] = request.args.get('has_analysis').lower() == 'true'
        
        return filters


class SearchResponseBuilder:
    """搜索响应构建器"""
    
    @staticmethod
    def build_success_response(data: Any, total: int = None) -> Dict[str, Any]:
        """构建成功响应"""
        response = {
            'success': True,
            'data': data
        }
        
        if total is not None:
            response['total'] = total
            
        return response
    
    @staticmethod
    def build_error_response(message: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
        """构建错误响应"""
        return {
            'success': False,
            'error': message
        }, status_code
    
    @staticmethod
    def build_csv_response(data: List[Dict], filename: str) -> Any:
        """构建CSV响应"""
        output = io.StringIO()
        
        if not data:
            return make_response("", 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename="{filename}"'
            })
        
        # 获取所有可能的字段
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
        
        fieldnames = sorted(all_fields)
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            # 处理可能包含列表或字典的字段
            row = {}
            for field in fieldnames:
                value = item.get(field, '')
                if isinstance(value, (list, dict)):
                    value = str(value)
                row[field] = value
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return make_response(csv_content, 200, {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })