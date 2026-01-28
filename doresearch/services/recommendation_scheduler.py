"""
推荐系统后台任务调度器
负责启动、管理和协调异步推荐计算服务
"""
import atexit
import time
import threading
from datetime import datetime
from services.async_recommendation_processor import recommendation_processor
from services.recommendation_cache_manager import cache_manager


class RecommendationScheduler:
    """推荐系统调度器"""
    
    def __init__(self):
        self.is_initialized = False
        self.startup_delay = 30  # 应用启动后延迟30秒启动推荐服务
        self.auto_warmup_enabled = True  # 是否自动预热缓存
        
    def initialize(self):
        """初始化推荐调度器"""
        if self.is_initialized:
            return
        
        try:
            print("🚀 初始化推荐系统调度器...")
            
            # 延迟启动后台处理器，避免应用启动时资源竞争
            startup_thread = threading.Thread(target=self._delayed_startup, daemon=True)
            startup_thread.start()
            
            # 注册应用退出时的清理函数
            atexit.register(self.shutdown)
            
            self.is_initialized = True
            print("✅ 推荐系统调度器初始化完成")
            
        except Exception as e:
            print(f"❌ 推荐系统调度器初始化失败: {e}")
    
    def _delayed_startup(self):
        """延迟启动后台服务"""
        try:
            print(f"⏳ 推荐系统将在 {self.startup_delay} 秒后启动...")
            time.sleep(self.startup_delay)
            
            # 启动异步推荐处理器
            recommendation_processor.start_background_processor()
            
            # 如果启用，执行初始缓存预热
            if self.auto_warmup_enabled:
                self._perform_initial_warmup()
            
            print("🎯 推荐系统后台服务已全面启动")
            
        except Exception as e:
            print(f"❌ 推荐系统延迟启动失败: {e}")
    
    def _perform_initial_warmup(self):
        """执行初始缓存预热"""
        try:
            print("🔥 开始初始缓存预热...")
            
            # 检查是否已有有效缓存
            cache_status = cache_manager.get_cache_status()
            
            # 如果缓存为空或很少，触发预热
            personalized_cache = cache_status.get('cache_statistics', {}).get('personalized', {})
            cache_count = personalized_cache.get('count', 0)
            
            if cache_count < 5:  # 如果个性化推荐缓存少于5条
                print(f"⚠️ 发现缓存数据不足（{cache_count}条），开始预热...")
                cache_manager.warm_up_cache()
            else:
                print(f"✅ 缓存数据充足（{cache_count}条），跳过预热")
                
        except Exception as e:
            print(f"❌ 初始缓存预热失败: {e}")
    
    def start_services(self):
        """手动启动推荐服务"""
        try:
            if not recommendation_processor.is_running:
                recommendation_processor.start_background_processor()
                print("✅ 推荐后台处理器已启动")
            else:
                print("⚠️ 推荐后台处理器已在运行中")
                
        except Exception as e:
            print(f"❌ 启动推荐服务失败: {e}")
    
    def stop_services(self):
        """停止推荐服务"""
        try:
            if recommendation_processor.is_running:
                recommendation_processor.stop_background_processor()
                print("⚠️ 推荐后台处理器已停止")
            else:
                print("ℹ️ 推荐后台处理器未在运行")
                
        except Exception as e:
            print(f"❌ 停止推荐服务失败: {e}")
    
    def restart_services(self):
        """重启推荐服务"""
        try:
            print("🔄 重启推荐服务...")
            self.stop_services()
            time.sleep(2)  # 等待停止完成
            self.start_services()
            print("✅ 推荐服务重启完成")
            
        except Exception as e:
            print(f"❌ 重启推荐服务失败: {e}")
    
    def shutdown(self):
        """优雅关闭推荐系统"""
        try:
            print("🛑 正在关闭推荐系统...")
            self.stop_services()
            print("✅ 推荐系统已优雅关闭")
            
        except Exception as e:
            print(f"❌ 推荐系统关闭失败: {e}")
    
    def get_system_status(self):
        """获取推荐系统整体状态"""
        try:
            processor_status = recommendation_processor.get_job_status()
            cache_status = cache_manager.get_cache_status()
            
            return {
                'scheduler_initialized': self.is_initialized,
                'processor_running': recommendation_processor.is_running,
                'auto_warmup_enabled': self.auto_warmup_enabled,
                'startup_delay': self.startup_delay,
                'processor_status': processor_status,
                'cache_status': cache_status,
                'system_health': {
                    'all_services_running': (
                        self.is_initialized and 
                        recommendation_processor.is_running
                    )
                },
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def emergency_warmup(self):
        """紧急缓存预热（用于缓存完全失效时）"""
        try:
            print("🚨 执行紧急缓存预热...")
            
            # 强制刷新缓存
            cache_manager.force_refresh_cache()
            
            # 创建高优先级任务
            recommendation_processor.create_full_recompute_job(priority=10)
            
            print("✅ 紧急缓存预热任务已创建")
            
        except Exception as e:
            print(f"❌ 紧急缓存预热失败: {e}")
    
    def health_check(self):
        """健康检查"""
        try:
            health_info = {
                'timestamp': datetime.now().isoformat(),
                'scheduler_ok': self.is_initialized,
                'processor_ok': recommendation_processor.is_running,
                'issues': []
            }
            
            # 检查各个组件状态
            if not self.is_initialized:
                health_info['issues'].append('调度器未初始化')
            
            if not recommendation_processor.is_running:
                health_info['issues'].append('后台处理器未运行')
            
            # 检查缓存状态
            cache_status = cache_manager.get_cache_status()
            cache_stats = cache_status.get('cache_statistics', {})
            
            if not cache_stats:
                health_info['issues'].append('推荐缓存为空')
            
            # 检查任务队列
            job_status = recommendation_processor.get_job_status()
            failed_jobs = job_status.get('job_counts', {}).get('failed', 0)
            
            if failed_jobs > 5:
                health_info['issues'].append(f'失败任务过多: {failed_jobs}')
            
            health_info['overall_health'] = 'healthy' if not health_info['issues'] else 'warning'
            
            return health_info
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'error',
                'error': str(e)
            }
    
    def configure(self, **kwargs):
        """配置调度器参数"""
        try:
            if 'startup_delay' in kwargs:
                self.startup_delay = max(0, int(kwargs['startup_delay']))
                print(f"📝 启动延迟设置为: {self.startup_delay}秒")
            
            if 'auto_warmup_enabled' in kwargs:
                self.auto_warmup_enabled = bool(kwargs['auto_warmup_enabled'])
                print(f"📝 自动预热设置为: {self.auto_warmup_enabled}")
                
            return True
            
        except Exception as e:
            print(f"❌ 配置调度器失败: {e}")
            return False


# 全局调度器实例
scheduler = RecommendationScheduler()