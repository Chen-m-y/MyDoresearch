"""
搜索路由主模块
整合所有搜索相关路由
"""
from flask import Flask
from services.search_service import SearchService
from .basic_search import setup_basic_search_routes
from .advanced_search import setup_advanced_search_routes
from .search_metadata import setup_search_metadata_routes
from .search_export import setup_search_export_routes


def setup_search_routes(app: Flask):
    """设置搜索相关路由"""
    
    # 创建搜索服务实例
    search_service = SearchService()
    
    # 设置各个功能模块的路由
    setup_basic_search_routes(app, search_service)
    setup_advanced_search_routes(app, search_service)
    setup_search_metadata_routes(app, search_service)
    setup_search_export_routes(app, search_service)