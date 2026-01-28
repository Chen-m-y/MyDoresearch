"""
数据库优化集成指南和使用示例
展示如何使用优化后的数据库服务和监控功能
"""
from services.database_service import get_database_service
from services.optimized_statistics_service import OptimizedStatisticsService
from services.optimized_paper_manager import OptimizedPaperManager
from services.database_performance_monitor import get_performance_monitor, start_performance_monitoring


def demo_connection_pool():
    """演示连接池的使用"""
    print("🔧 连接池使用示例")
    print("=" * 50)
    
    db_service = get_database_service()
    
    # 获取连接池统计
    stats = db_service.get_statistics()
    print(f"当前连接池状态: {stats['connection_pool']}")
    
    # 使用连接池执行查询
    papers = db_service.execute_query(
        "SELECT COUNT(*) as count FROM papers",
        fetch_one=True
    )
    print(f"论文总数: {papers['count']}")
    
    # 执行批量操作示例
    # batch_params = [
    #     ("test_title_1", "test_abstract_1"),
    #     ("test_title_2", "test_abstract_2"),
    # ]
    # db_service.execute_batch(
    #     "INSERT INTO test_table (title, abstract) VALUES (?, ?)",
    #     batch_params
    # )
    
    print(f"操作后连接池状态: {db_service.get_statistics()['connection_pool']}")


def demo_optimized_statistics():
    """演示优化后的统计服务"""
    print("\n📊 优化统计服务示例")
    print("=" * 50)
    
    stats_service = OptimizedStatisticsService()
    
    # 获取快速统计（带缓存）
    quick_stats = stats_service.get_quick_stats()
    print(f"快速统计: {quick_stats}")
    
    # 获取详细统计
    full_stats = stats_service.get_reading_statistics()
    print(f"基础统计: {full_stats['basic']}")
    print(f"连续阅读天数: {full_stats['reading_streak_days']}")
    
    # 获取阅读日历
    calendar_data = stats_service.get_reading_calendar()
    print(f"阅读日历摘要: {calendar_data['summary']}")
    
    # 获取数据库服务统计
    db_stats = stats_service.get_database_stats()
    print(f"数据库服务统计: {db_stats}")


def demo_optimized_paper_manager():
    """演示优化后的论文管理"""
    print("\n📚 优化论文管理示例")
    print("=" * 50)
    
    paper_manager = OptimizedPaperManager()
    
    # 获取所有订阅源（带缓存）
    feeds = paper_manager.get_all_feeds()
    print(f"找到 {len(feeds)} 个订阅源")
    
    if feeds:
        feed = feeds[0]
        print(f"第一个订阅源: {feed['name']}")
        
        # 获取论文列表（带缓存）
        papers = paper_manager.get_papers_by_feed(feed['id'])
        print(f"该订阅源有 {len(papers)} 篇论文")
        
        if papers:
            paper = papers[0]
            print(f"第一篇论文: {paper['title'][:50]}...")
            
            # 获取详细信息
            detail = paper_manager.get_paper(paper['id'])
            if detail:
                print(f"论文状态: {detail['status']}")
                
                # 获取导航信息（优化查询）
                nav = paper_manager.get_paper_navigation(paper['id'], feed['id'])
                if nav:
                    print(f"导航信息: {nav['current_index']}/{nav['total']}")


def demo_performance_monitoring():
    """演示性能监控功能"""
    print("\n⚡ 性能监控示例")
    print("=" * 50)
    
    # 启动性能监控
    start_performance_monitoring(interval=30)  # 30秒间隔
    
    monitor = get_performance_monitor()
    
    # 获取性能报告
    report = monitor.get_performance_report()
    print(f"连接池状态: {report['connection_pool_status']}")
    print(f"查询缓存状态: {report['query_cache_status']}")
    print(f"数据库大小: {report['database_size_mb']} MB")
    
    # 获取优化建议
    suggestions = monitor.get_optimization_suggestions()
    if suggestions:
        print("\n💡 优化建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("✅ 暂无优化建议，系统运行良好")
    
    # 查询性能统计
    query_stats = monitor.profiler.get_stats()
    print(f"\n📈 查询统计:")
    print(f"  总查询数: {query_stats['total_queries']}")
    print(f"  慢查询数: {query_stats['slow_queries_count']}")
    print(f"  唯一查询数: {query_stats['unique_queries']}")


def demo_cache_usage():
    """演示缓存使用"""
    print("\n💾 缓存使用示例")
    print("=" * 50)
    
    db_service = get_database_service()
    
    # 第一次查询（会缓存）
    import time
    start_time = time.time()
    
    result1 = db_service.get_cached_query(
        "demo_cache",
        "SELECT COUNT(*) as count FROM papers WHERE status = ?",
        ("read",),
        cache_duration=300
    )
    
    first_query_time = time.time() - start_time
    print(f"第一次查询耗时: {first_query_time:.3f}秒")
    print(f"查询结果: {result1}")
    
    # 第二次查询（从缓存获取）
    start_time = time.time()
    
    result2 = db_service.get_cached_query(
        "demo_cache",
        "SELECT COUNT(*) as count FROM papers WHERE status = ?",
        ("read",),
        cache_duration=300
    )
    
    second_query_time = time.time() - start_time
    print(f"第二次查询耗时: {second_query_time:.3f}秒")
    print(f"查询结果: {result2}")
    
    # 显示缓存效果
    if second_query_time < first_query_time:
        speedup = first_query_time / second_query_time
        print(f"🚀 缓存提速: {speedup:.1f}x")
    
    # 清理演示缓存
    db_service.clear_cache("demo_cache")


def performance_comparison():
    """性能对比测试"""
    print("\n⚔️ 性能对比测试")
    print("=" * 50)
    
    import time
    
    # 测试优化前后的统计查询性能
    print("测试统计查询性能...")
    
    # 优化版统计服务
    optimized_stats = OptimizedStatisticsService()
    
    start_time = time.time()
    quick_stats = optimized_stats.get_quick_stats()
    optimized_time = time.time() - start_time
    
    print(f"优化版快速统计耗时: {optimized_time:.3f}秒")
    
    # 测试论文管理性能
    print("\n测试论文管理性能...")
    
    optimized_manager = OptimizedPaperManager()
    
    start_time = time.time()
    feeds = optimized_manager.get_all_feeds()
    feed_query_time = time.time() - start_time
    
    print(f"获取订阅源耗时: {feed_query_time:.3f}秒")
    
    if feeds:
        start_time = time.time()
        papers = optimized_manager.get_papers_by_feed(feeds[0]['id'])
        paper_query_time = time.time() - start_time
        
        print(f"获取论文列表耗时: {paper_query_time:.3f}秒")


def cleanup_demo():
    """清理演示数据"""
    print("\n🧹 清理演示数据")
    print("=" * 50)
    
    # 停止性能监控
    from services.database_performance_monitor import stop_performance_monitoring
    stop_performance_monitoring()
    
    # 清理缓存
    db_service = get_database_service()
    db_service.clear_cache()
    
    print("清理完成")


def main():
    """主演示函数"""
    print("🚀 DoResearch 数据库优化演示")
    print("=" * 60)
    
    try:
        # 1. 连接池演示
        demo_connection_pool()
        
        # 2. 优化统计服务演示
        demo_optimized_statistics()
        
        # 3. 优化论文管理演示
        demo_optimized_paper_manager()
        
        # 4. 性能监控演示
        demo_performance_monitoring()
        
        # 5. 缓存使用演示
        demo_cache_usage()
        
        # 6. 性能对比测试
        performance_comparison()
        
        print("\n✅ 所有演示完成!")
        print("\n📋 优化效果总结:")
        print("  • 连接池管理 - 减少连接创建开销")
        print("  • 查询优化 - 添加复合索引，提升查询速度")
        print("  • 缓存机制 - 减少重复查询，提升响应速度")
        print("  • 批量操作 - 减少数据库往返次数")
        print("  • 性能监控 - 实时监控系统性能")
        print("  • 内存优化 - 避免大量数据加载到内存")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        cleanup_demo()


if __name__ == "__main__":
    main()