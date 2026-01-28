"""
统计路由模块
"""
from flask import Flask, request, jsonify
from services.statistics_service import StatisticsService
from datetime import datetime
import time


def setup_statistics_routes(app: Flask):
    """设置统计相关路由"""
    
    statistics_service = StatisticsService()
    
    @app.route('/api/statistics/overview')
    def api_statistics_overview():
        """获取统计概览"""
        try:
            stats = statistics_service.get_reading_statistics()
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            print(f"❌ 获取统计概览失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/statistics/quick')
    def api_statistics_quick():
        """获取快速统计（只包含基础数据）"""
        try:
            stats = statistics_service.get_quick_stats()
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            print(f"❌ 获取快速统计失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/statistics/calendar')
    def api_statistics_calendar():
        """获取阅读日历数据"""
        try:
            year = request.args.get('year', type=int)
            if year is None:
                year = datetime.now().year
            
            calendar_data = statistics_service.get_reading_calendar(year)
            return jsonify({
                'success': True,
                'data': calendar_data
            })
        except Exception as e:
            print(f"❌ 获取阅读日历失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/statistics/trends')
    def api_statistics_trends():
        """获取阅读趋势分析"""
        try:
            days = request.args.get('days', default=90, type=int)
            if days <= 0 or days > 365:
                return jsonify({
                    'success': False,
                    'error': 'days参数必须在1-365之间'
                }), 400
            
            trends = statistics_service.get_reading_trends(days)
            return jsonify({
                'success': True,
                'data': trends
            })
        except Exception as e:
            print(f"❌ 获取阅读趋势失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/statistics/dashboard')
    def api_statistics_dashboard():
        """获取仪表盘数据（包含多个统计）"""
        try:
            # 获取基础统计
            quick_stats = statistics_service.get_quick_stats()
            
            # 获取近30天趋势
            trends_30 = statistics_service.get_reading_trends(30)
            
            # 获取当年日历概览
            current_year = datetime.now().year
            calendar_summary = statistics_service.get_reading_calendar(current_year)
            
            dashboard_data = {
                'basic_stats': quick_stats,
                'recent_trends': {
                    'days': 30,
                    'trend_direction': trends_30['analysis']['trend_direction'],
                    'avg_per_day': trends_30['analysis']['avg_per_day'],
                    'total_read': trends_30['analysis']['total_read']
                },
                'year_summary': {
                    'year': current_year,
                    'total_read': calendar_summary['summary']['total_read_papers'],
                    'reading_days': calendar_summary['summary']['total_reading_days'],
                    'reading_rate': calendar_summary['summary']['reading_rate']
                },
                'generated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
        except Exception as e:
            print(f"❌ 获取仪表盘数据失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/statistics/summary')
    def api_statistics_summary():
        """获取统计汇总（符合要求的6个指标）"""
        try:
            stats = statistics_service.get_reading_statistics()
            
            # 按照要求的格式整理数据
            summary = {
                # 1. 总文章数量
                'total_papers': stats['basic']['total_papers'],
                
                # 2. 已读文章数量
                'read_papers': stats['basic']['read_papers'],
                
                # 3. 连续阅读天数
                'reading_streak_days': stats['reading_streak_days'],
                
                # 4. 近30天每天的新增文章数量
                'last_30_days_new_papers': [
                    {
                        'date': item['date'],
                        'count': item['new_papers']
                    }
                    for item in stats['last_30_days']['daily_data']
                ],
                
                # 5. 近30天每天的已读文章数量
                'last_30_days_read_papers': [
                    {
                        'date': item['date'],
                        'count': item['read_papers']
                    }
                    for item in stats['last_30_days']['daily_data']
                ],
                
                # 6. 近一年每天的已读文章数量
                'last_year_read_papers': [
                    {
                        'date': item['date'],
                        'count': item['read_papers']
                    }
                    for item in stats['last_year_read']['daily_data']
                ],
                
                # 额外的汇总信息
                'summary': {
                    'last_30_days': stats['last_30_days']['summary'],
                    'last_year': stats['last_year_read']['summary']
                },
                
                'generated_at': stats['generated_at']
            }
            
            return jsonify({
                'success': True,
                'data': summary
            })
        except Exception as e:
            print(f"❌ 获取统计汇总失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/statistics/performance-test')
    def api_statistics_performance_test():
        """性能测试接口"""
        try:
            start_time = time.time()
            
            # 测试各个统计功能的性能
            tests = {}
            
            # 测试基础统计
            test_start = time.time()
            basic_stats = statistics_service.get_quick_stats()
            tests['basic_stats'] = time.time() - test_start
            
            # 测试30天统计
            test_start = time.time()
            statistics_service._get_last_30_days_statistics(statistics_service.get_db())
            tests['last_30_days'] = time.time() - test_start
            
            # 测试一年统计
            test_start = time.time()
            statistics_service._get_last_year_read_statistics(statistics_service.get_db())
            tests['last_year'] = time.time() - test_start
            
            total_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'performance': {
                    'total_time_ms': round(total_time * 1000, 2),
                    'individual_tests_ms': {k: round(v * 1000, 2) for k, v in tests.items()},
                    'data_sample': {
                        'total_papers': basic_stats['total_papers'],
                        'read_papers': basic_stats['read_papers']
                    }
                }
            })
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500