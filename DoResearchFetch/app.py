from flask import Flask, jsonify, request
from datetime import datetime
from adapters.registry import SourceRegistry
from config import Config
from utils.exceptions import FetchError, ValidationError, RateLimitError
from utils.response_formatter import format_response, format_error
from utils.logging_config import LogConfig, metrics_collector, log_api_call
from utils.cache import cache, get_cached_result, cache_result
from utils.progress_monitor import progress_manager, create_progress_tracker
from utils.abstract_cache import abstract_cache
import traceback
import time

app = Flask(__name__)
app.config.from_object(Config)

# 初始化日志配置
log_config = LogConfig(app)

# 初始化数据源注册器
source_registry = SourceRegistry()

# 记录应用启动时间
app_start_time = time.time()

@app.route('/api/v1/metrics', methods=['GET'])
def get_metrics():
    """获取服务指标"""
    return format_response(metrics_collector.get_metrics())


# 添加摘要缓存管理端点
@app.route('/api/v1/abstract-cache/stats', methods=['GET'])
def get_abstract_cache_stats():
    """获取摘要缓存统计信息"""
    return format_response(abstract_cache.get_stats())


@app.route('/api/v1/abstract-cache/clear', methods=['POST'])
def clear_abstract_cache():
    """清空摘要缓存"""
    abstract_cache.clear()
    return format_response({"message": "摘要缓存已清空"})


@app.route('/api/v1/abstract-cache/clean', methods=['POST'])
def clean_expired_abstract_cache():
    """清理过期的摘要缓存"""
    cleaned_count = abstract_cache.clean_expired()
    return format_response({"message": f"已清理 {cleaned_count} 个过期摘要缓存条目"})


@app.route('/api/v1/abstract-cache/export', methods=['POST'])
def export_abstract_cache():
    """导出摘要缓存"""
    data = request.get_json()
    output_file = data.get('output_file', 'abstract_cache_export.json')
    
    try:
        abstract_cache.export_to_json(output_file)
        return format_response({
            "message": f"摘要缓存已导出到 {output_file}",
            "output_file": output_file
        })
    except Exception as e:
        return format_error("EXPORT_ERROR", f"导出失败: {str(e)}"), 500


# 添加缓存管理端点
@app.route('/api/v1/cache/stats', methods=['GET'])
def get_cache_stats():
    """获取缓存统计信息"""
    return format_response(cache.get_stats())


@app.route('/api/v1/cache/clear', methods=['POST'])
def clear_cache():
    """清空缓存"""
    cache.clear()
    return format_response({"message": "缓存已清空"})


@app.route('/api/v1/cache/clean', methods=['POST'])
def clean_expired_cache():
    """清理过期缓存"""
    cleaned_count = cache.clean_expired()
    return format_response({"message": f"已清理 {cleaned_count} 个过期缓存条目"})


# 进度监控相关API
@app.route('/api/v1/progress/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务列表"""
    tasks = progress_manager.get_all_tasks()
    return format_response({
        "tasks": [task.to_dict() for task in tasks],
        "total_count": len(tasks)
    })


@app.route('/api/v1/progress/tasks/running', methods=['GET'])
def get_running_tasks():
    """获取正在运行的任务"""
    running_tasks = progress_manager.get_running_tasks()
    return format_response({
        "tasks": [task.to_dict() for task in running_tasks],
        "count": len(running_tasks)
    })


@app.route('/api/v1/progress/tasks/<task_id>', methods=['GET'])
def get_task_progress(task_id):
    """获取特定任务的进度"""
    task = progress_manager.get_task(task_id)
    if not task:
        return format_error("TASK_NOT_FOUND", f"任务 {task_id} 不存在"), 404
    
    return format_response({
        "task": task.to_dict()
    })


@app.route('/api/v1/progress/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    task = progress_manager.get_task(task_id)
    if not task:
        return format_error("TASK_NOT_FOUND", f"任务 {task_id} 不存在"), 404
    
    progress_manager.cancel_task(task_id)
    return format_response({
        "message": f"任务 {task_id} 已取消",
        "task_id": task_id
    })


@app.route('/api/v1/progress/stats', methods=['GET'])
def get_progress_stats():
    """获取任务统计信息"""
    stats = progress_manager.get_task_stats()
    return format_response(stats)


@app.route('/favicon.ico')
def favicon():
    """处理浏览器favicon请求"""
    return '', 204  # 返回空内容和204状态码


@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return format_error("NOT_FOUND", "请求的资源不存在"), 404


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    uptime_seconds = int(time.time() - app_start_time)
    uptime_str = format_uptime(uptime_seconds)
    
    return format_response({
        "status": "healthy",
        "version": "1.0.0",
        "uptime": uptime_str,
        "supported_sources": list(source_registry.list_sources().keys()),
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    })


@app.route('/api/v1/sources', methods=['GET'])
def get_sources():
    """获取支持的数据源列表"""
    sources = source_registry.list_sources()

    # 分类数据源
    paper_sources = []
    news_sources = []

    for name, adapter in sources.items():
        source_info = {
            "name": name,
            "display_name": adapter.display_name,
            "description": adapter.description,
            "status": "active",
            "required_params": adapter.required_params,
            "optional_params": adapter.optional_params,
            "adapter_type": getattr(adapter, 'adapter_type', 'paper')
        }

        if getattr(adapter, 'adapter_type', 'paper') == 'news':
            news_sources.append(source_info)
        else:
            paper_sources.append(source_info)

    return format_response({
        "total_sources": len(sources),
        "paper_sources": paper_sources,
        "news_sources": news_sources,
        "all_sources": paper_sources + news_sources
    })


@app.route('/api/v1/fetch', methods=['POST'])
def fetch_papers():
    """论文抓取接口"""
    source = None
    source_params = {}

    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationError("请求体不能为空")

        source = data.get('source')
        source_params = data.get('source_params', {})

        if not source:
            raise ValidationError("source 参数是必需的")

        # 检查缓存
        if app.config.get('ENABLE_CACHE', True):
            cached_result = get_cached_result(source, source_params)
            if cached_result:
                # 构建响应
                response_data = {
                    "papers": cached_result.get('papers', []),
                    "total_count": cached_result.get('total_count', 0),
                    "has_more": cached_result.get('has_more', False),
                    "next_cursor": cached_result.get('next_cursor')
                }

                source_info = {
                    "source": source,
                    "query_params": source_params,
                    "execution_time_ms": 0,
                    "rate_limit_remaining": cached_result.get('rate_limit_remaining'),
                    "cache_hit": True
                }

                return format_response(response_data, source_info=source_info)

        # 获取适配器
        adapter = source_registry.get_adapter(source)
        if not adapter:
            raise ValidationError(f"不支持的数据源: {source}")

        # 验证参数
        adapter.validate_params(source_params)

        # 执行抓取
        start_time = time.time()
        result = adapter.fetch_papers(source_params)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # 缓存结果
        if app.config.get('ENABLE_CACHE', True):
            cache_result(source, source_params, result, app.config.get('CACHE_TTL', 3600))

        # 记录API调用日志
        log_api_call(
            source=source,
            params=source_params,
            success=True,
            response_time=time.time() - start_time,
            papers_count=len(result.get('papers', []))
        )

        # 格式化响应
        response_data = {
            "papers": result.get('papers', []),
            "total_count": result.get('total_count', len(result.get('papers', []))),
            "has_more": result.get('has_more', False),
            "next_cursor": result.get('next_cursor')
        }

        source_info = {
            "source": source,
            "query_params": source_params,
            "execution_time_ms": execution_time_ms,
            "rate_limit_remaining": result.get('rate_limit_remaining'),
            "cache_hit": False
        }

        return format_response(response_data, source_info=source_info)

    except ValidationError as e:
        log_api_call(source or 'unknown', {}, False, 0, 0, str(e))
        return format_error("INVALID_PARAMS", str(e)), 400
    except RateLimitError as e:
        log_api_call(source or 'unknown', source_params or {}, False, 0, 0, str(e))
        return format_error("RATE_LIMIT_EXCEEDED", str(e), e.details), 429
    except FetchError as e:
        log_api_call(source or 'unknown', source_params or {}, False, 0, 0, str(e))
        return format_error(e.error_code, str(e), e.details), 500
    except Exception as e:
        log_api_call(source or 'unknown', source_params or {}, False, 0, 0, str(e))
        app.logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return format_error("INTERNAL_ERROR", "服务内部错误"), 500


@app.route('/api/v1/fetch/news', methods=['POST'])
def fetch_news():
    """新闻抓取接口"""
    source = None
    source_params = {}

    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationError("请求体不能为空")

        source = data.get('source')
        source_params = data.get('source_params', {})

        if not source:
            raise ValidationError("source 参数是必需的")

        # 检查缓存
        if app.config.get('ENABLE_CACHE', True):
            cached_result = get_cached_result(f"news_{source}", source_params)
            if cached_result:
                # 构建响应
                response_data = {
                    "news": cached_result.get('news', []),
                    "total_count": cached_result.get('total_count', 0),
                    "has_more": cached_result.get('has_more', False),
                    "next_cursor": cached_result.get('next_cursor')
                }

                source_info = {
                    "source": source,
                    "query_params": source_params,
                    "execution_time_ms": 0,
                    "rate_limit_remaining": cached_result.get('rate_limit_remaining'),
                    "cache_hit": True
                }

                return format_response(response_data, source_info=source_info)

        # 获取适配器
        adapter = source_registry.get_adapter(source)
        if not adapter:
            raise ValidationError(f"不支持的数据源: {source}")

        # 检查是否为新闻适配器
        if not hasattr(adapter, 'adapter_type') or adapter.adapter_type != 'news':
            raise ValidationError(f"数据源 {source} 不支持新闻抓取")

        # 验证参数
        adapter.validate_params(source_params)

        # 执行抓取
        start_time = time.time()
        result = adapter.fetch_news(source_params)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # 缓存结果
        if app.config.get('ENABLE_CACHE', True):
            cache_result(f"news_{source}", source_params, result, app.config.get('CACHE_TTL', 3600))

        # 记录API调用日志
        log_api_call(
            source=f"news_{source}",
            params=source_params,
            success=True,
            response_time=time.time() - start_time,
            papers_count=len(result.get('news', []))
        )

        # 格式化响应
        response_data = {
            "news": result.get('news', []),
            "total_count": result.get('total_count', len(result.get('news', []))),
            "has_more": result.get('has_more', False),
            "next_cursor": result.get('next_cursor')
        }

        source_info = {
            "source": source,
            "query_params": source_params,
            "execution_time_ms": execution_time_ms,
            "rate_limit_remaining": result.get('rate_limit_remaining'),
            "cache_hit": False
        }

        return format_response(response_data, source_info=source_info)

    except ValidationError as e:
        log_api_call(source or 'unknown', {}, False, 0, 0, str(e))
        return format_error("INVALID_PARAMS", str(e)), 400
    except RateLimitError as e:
        log_api_call(source or 'unknown', source_params or {}, False, 0, 0, str(e))
        return format_error("RATE_LIMIT_EXCEEDED", str(e), e.details), 429
    except FetchError as e:
        log_api_call(source or 'unknown', source_params or {}, False, 0, 0, str(e))
        return format_error(e.error_code, str(e), e.details), 500
    except Exception as e:
        log_api_call(source or 'unknown', source_params or {}, False, 0, 0, str(e))
        app.logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return format_error("INTERNAL_ERROR", "服务内部错误"), 500


@app.route('/api/v1/fetch/async', methods=['POST'])  
def fetch_papers_async():
    """异步论文抓取接口（返回任务ID，可通过进度API查询状态）"""
    import threading
    
    def async_fetch_worker(source, source_params, task_callback):
        """异步抓取工作线程"""
        try:
            # 获取适配器
            adapter = source_registry.get_adapter(source)
            if not adapter:
                task_callback(None, f"不支持的数据源: {source}")
                return
            
            # 验证参数
            adapter.validate_params(source_params)
            
            # 执行抓取（这里会自动创建进度追踪）
            result = adapter.fetch_papers(source_params)
            task_callback(result, None)
            
        except Exception as e:
            task_callback(None, str(e))
    
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            raise ValidationError("请求体不能为空")
        
        source = data.get('source')
        source_params = data.get('source_params', {})
        
        if not source:
            raise ValidationError("source 参数是必需的")
        
        # 创建进度任务（这里先创建一个占位任务）
        task_id = progress_manager.create_task(source, source_params.get('limit', 50), f"异步抓取{source}数据")
        
        def task_callback(result, error):
            if error:
                progress_manager.fail_task(task_id, error)
            else:
                progress_manager.complete_task(task_id, result)
        
        # 启动后台线程
        thread = threading.Thread(
            target=async_fetch_worker,
            args=(source, source_params, task_callback)
        )
        thread.daemon = True
        thread.start()
        
        # 立即返回任务ID
        return format_response({
            "task_id": task_id,
            "status": "started",
            "message": "任务已开始，请使用task_id查询进度",
            "progress_url": f"/api/v1/progress/tasks/{task_id}"
        })
        
    except ValidationError as e:
        return format_error("INVALID_PARAMS", str(e)), 400
    except Exception as e:
        app.logger.error(f"Async fetch error: {str(e)}\n{traceback.format_exc()}")
        return format_error("INTERNAL_ERROR", "异步任务创建失败"), 500


@app.route('/api/v1/fetch/batch', methods=['POST'])
def fetch_papers_batch():
    """批量抓取接口"""
    try:
        data = request.get_json()
        if not data or 'requests' not in data:
            raise ValidationError("批量请求格式错误")
        
        requests_list = data['requests']
        if not isinstance(requests_list, list) or len(requests_list) == 0:
            raise ValidationError("requests必须是非空数组")
        
        results = []
        for req in requests_list:
            req_id = req.get('id')
            source = req.get('source')
            source_params = req.get('source_params', {})
            
            try:
                adapter = source_registry.get_adapter(source)
                if not adapter:
                    raise ValidationError(f"不支持的数据源: {source}")
                
                adapter.validate_params(source_params)
                result = adapter.fetch_papers(source_params)
                
                results.append({
                    "id": req_id,
                    "success": True,
                    "data": result
                })
                
            except Exception as e:
                results.append({
                    "id": req_id,
                    "success": False,
                    "error": {
                        "code": type(e).__name__,
                        "message": str(e)
                    }
                })
        
        return format_response({"results": results})
        
    except ValidationError as e:
        return format_error("INVALID_PARAMS", str(e)), 400
    except Exception as e:
        app.logger.error(f"Batch fetch error: {str(e)}\n{traceback.format_exc()}")
        return format_error("INTERNAL_ERROR", "批量处理失败"), 500


def format_uptime(seconds):
    """格式化运行时间"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days} days, {hours} hours, {minutes} minutes"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    else:
        return f"{minutes} minutes"


if __name__ == '__main__':
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 8000),
        debug=app.config.get('DEBUG', False)
    )