"""
推荐系统初始化脚本
用于在主应用启动时自动初始化异步推荐系统
"""
from services.recommendation_scheduler import scheduler


def initialize_recommendation_system():
    """
    初始化推荐系统
    应在主应用启动后调用
    """
    try:
        print("🎯 正在初始化推荐系统...")
        scheduler.initialize()
        print("✅ 推荐系统初始化完成")
        
    except Exception as e:
        print(f"❌ 推荐系统初始化失败: {e}")


def setup_recommendation_system(app):
    """
    为Flask应用设置推荐系统
    包括路由和初始化
    """
    try:
        # 导入并设置推荐路由
        from routes.recommendation_routes import setup_recommendation_routes
        setup_recommendation_routes(app)
        
        # 在应用启动后初始化推荐系统
        @app.before_first_request
        def init_recommendation_on_startup():
            initialize_recommendation_system()
        
        print("✅ 推荐系统已集成到Flask应用")
        
    except Exception as e:
        print(f"❌ 集成推荐系统失败: {e}")


def get_system_info():
    """获取推荐系统信息（用于应用状态检查）"""
    try:
        return scheduler.get_system_status()
    except Exception as e:
        return {
            'error': str(e),
            'system_available': False
        }


# 导出的公共接口
__all__ = [
    'initialize_recommendation_system',
    'setup_recommendation_system', 
    'get_system_info'
]