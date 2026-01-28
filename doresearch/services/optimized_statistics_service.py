"""
优化版统计服务 - 使用连接池和查询优化
解决统计查询性能问题，避免内存占用过高
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from services.database_service import get_database_service


class OptimizedStatisticsService:
    """优化版统计服务"""
    
    def __init__(self):
        self.db_service = get_database_service()
    
    def get_reading_statistics(self) -> Dict:
        """获取完整的阅读统计数据"""
        # 使用缓存的基础统计
        basic_stats = self._get_basic_statistics_cached()
        
        # 获取连续阅读天数（优化版）
        streak_days = self._get_reading_streak_optimized()
        
        # 获取近30天统计（优化版）
        last_30_days = self._get_last_30_days_statistics_optimized()
        
        # 获取近一年已读统计（分页处理）
        last_year_read = self._get_last_year_read_statistics_optimized()
        
        return {
            'basic': basic_stats,
            'reading_streak_days': streak_days,
            'last_30_days': last_30_days,
            'last_year_read': last_year_read,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_basic_statistics_cached(self) -> Dict:
        """获取缓存的基础统计数据"""
        cache_key = "basic_statistics"
        query = '''
            SELECT 
                COUNT(*) as total_papers,
                SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as read_papers,
                SUM(CASE WHEN status = 'unread' THEN 1 ELSE 0 END) as unread_papers
            FROM papers
        '''
        
        result = self.db_service.get_cached_query(cache_key, query, cache_duration=60)
        if result:
            return dict(result[0])
        
        return {'total_papers': 0, 'read_papers': 0, 'unread_papers': 0}
    
    def _get_reading_streak_optimized(self) -> int:
        """获取连续阅读天数（优化版 - 避免加载所有日期到内存）"""
        today = datetime.now().date()
        streak = 0
        
        # 从今天开始逐天检查，直到找到没有阅读的日期
        for days_back in range(365):  # 最多检查365天
            check_date = today - timedelta(days=days_back)
            date_str = check_date.strftime('%Y-%m-%d')
            
            query = '''
                SELECT COUNT(*) as read_count
                FROM papers 
                WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE(status_changed_at) = ?
            '''
            
            result = self.db_service.execute_query(query, (date_str,), fetch_one=True)
            
            if result and result['read_count'] > 0:
                streak += 1
            else:
                break
        
        return streak
    
    def _get_last_30_days_statistics_optimized(self) -> Dict:
        """获取近30天统计数据（优化版 - 单次查询）"""
        cache_key = "last_30_days_stats"
        
        # 使用单个查询获取所有数据
        query = '''
            WITH date_range AS (
                SELECT DATE('now', '-' || value || ' days') as date
                FROM (
                    SELECT 0 as value UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION
                    SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION
                    SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION
                    SELECT 15 UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION
                    SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION
                    SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29
                )
            ),
            new_papers_by_date AS (
                SELECT 
                    DATE(published_date) as date,
                    COUNT(*) as new_papers
                FROM papers
                WHERE DATE(published_date) >= DATE('now', '-30 days')
                GROUP BY DATE(published_date)
            ),
            read_papers_by_date AS (
                SELECT 
                    DATE(status_changed_at) as date,
                    COUNT(*) as read_papers
                FROM papers
                WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE(status_changed_at) >= DATE('now', '-30 days')
                GROUP BY DATE(status_changed_at)
            )
            SELECT 
                dr.date,
                COALESCE(np.new_papers, 0) as new_papers,
                COALESCE(rp.read_papers, 0) as read_papers
            FROM date_range dr
            LEFT JOIN new_papers_by_date np ON dr.date = np.date
            LEFT JOIN read_papers_by_date rp ON dr.date = rp.date
            ORDER BY dr.date DESC
        '''
        
        results = self.db_service.get_cached_query(cache_key, query, cache_duration=300)
        
        # 计算总计
        total_new = sum(row['new_papers'] for row in results)
        total_read = sum(row['read_papers'] for row in results)
        
        return {
            'daily_data': results,
            'summary': {
                'total_new_papers': total_new,
                'total_read_papers': total_read,
                'avg_new_per_day': round(total_new / 30, 1),
                'avg_read_per_day': round(total_read / 30, 1)
            }
        }
    
    def _get_last_year_read_statistics_optimized(self) -> Dict:
        """获取近一年已读文章统计（优化版 - 聚合查询）"""
        cache_key = "last_year_read_stats"
        
        # 使用聚合查询避免生成366行数据
        query = '''
            SELECT 
                DATE(status_changed_at) as date,
                COUNT(*) as read_papers
            FROM papers
            WHERE status = 'read'
                AND status_changed_at IS NOT NULL
                AND DATE(status_changed_at) >= DATE('now', '-365 days')
            GROUP BY DATE(status_changed_at)
            ORDER BY date ASC
        '''
        
        results = self.db_service.get_cached_query(cache_key, query, cache_duration=600)
        
        # 构建月度统计
        monthly_stats = {}
        daily_data = []
        read_data = {row['date']: row['read_papers'] for row in results}
        
        # 只为有数据的日期生成记录，减少内存占用
        start_date = datetime.now().date() - timedelta(days=365)
        total_read = 0
        reading_days = 0
        
        for row in results:
            date_str = row['date']
            read_count = row['read_papers']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            month_key = date_obj.strftime('%Y-%m')
            
            daily_data.append({
                'date': date_str,
                'read_papers': read_count
            })
            
            total_read += read_count
            reading_days += 1
            
            # 累计月度统计
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'month': month_key,
                    'read_papers': 0,
                    'reading_days': 0
                }
            
            monthly_stats[month_key]['read_papers'] += read_count
            monthly_stats[month_key]['reading_days'] += 1
        
        return {
            'daily_data': daily_data,
            'monthly_data': list(monthly_stats.values()),
            'summary': {
                'total_read_papers': total_read,
                'total_reading_days': reading_days,
                'avg_read_per_day': round(total_read / 365, 1) if total_read > 0 else 0,
                'avg_read_per_reading_day': round(total_read / reading_days, 1) if reading_days > 0 else 0
            }
        }
    
    def get_quick_stats(self) -> Dict:
        """获取快速统计（使用缓存）"""
        cache_key = "quick_stats"
        
        # 尝试从缓存获取
        basic_stats = self._get_basic_statistics_cached()
        
        # 获取连续阅读天数（限制检查范围）
        streak_days = self._get_reading_streak_quick()
        
        return {
            **basic_stats,
            'reading_streak_days': streak_days,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_reading_streak_quick(self) -> int:
        """快速获取连续阅读天数（限制查询范围）"""
        today = datetime.now().date()
        streak = 0
        
        # 只检查最近30天，提高响应速度
        for days_back in range(30):
            check_date = today - timedelta(days=days_back)
            date_str = check_date.strftime('%Y-%m-%d')
            
            query = '''
                SELECT 1
                FROM papers 
                WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE(status_changed_at) = ?
                LIMIT 1
            '''
            
            result = self.db_service.execute_query(query, (date_str,), fetch_one=True)
            
            if result:
                streak += 1
            else:
                break
        
        return streak
    
    def get_reading_calendar(self, year: int = None) -> Dict:
        """获取阅读日历数据（优化版）"""
        if year is None:
            year = datetime.now().year
        
        cache_key = f"reading_calendar_{year}"
        
        query = '''
            SELECT
                DATE(status_changed_at) as date, 
                COUNT(*) as read_count
            FROM papers
            WHERE status = 'read'
                AND status_changed_at IS NOT NULL
                AND strftime('%Y', status_changed_at) = ?
            GROUP BY DATE(status_changed_at)
            ORDER BY date ASC
        '''
        
        results = self.db_service.get_cached_query(
            cache_key, query, (str(year),), cache_duration=3600
        )
        
        read_data = {row['date']: row['read_count'] for row in results}
        
        # 生成日历数据
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        calendar_data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            read_count = read_data.get(date_str, 0)
            
            # 计算强度等级
            if read_count == 0:
                level = 0
            elif read_count <= 2:
                level = 1
            elif read_count <= 5:
                level = 2
            elif read_count <= 10:
                level = 3
            else:
                level = 4
            
            calendar_data.append({
                'date': date_str,
                'count': read_count,
                'level': level
            })
            
            current_date += timedelta(days=1)
        
        # 计算统计
        total_read = sum(item['count'] for item in calendar_data)
        reading_days = sum(1 for item in calendar_data if item['count'] > 0)
        
        return {
            'year': year,
            'calendar_data': calendar_data,
            'summary': {
                'total_read_papers': total_read,
                'total_reading_days': reading_days,
                'avg_read_per_day': round(total_read / len(calendar_data), 2),
                'reading_rate': round(reading_days / len(calendar_data) * 100, 1)
            }
        }
    
    def get_reading_trends(self, days: int = 90) -> Dict:
        """获取阅读趋势分析（优化版）"""
        cache_key = f"reading_trends_{days}"
        
        query = '''
            SELECT 
                DATE(status_changed_at) as date,
                COUNT(*) as read_count
            FROM papers 
            WHERE status = 'read'
                AND status_changed_at IS NOT NULL
                AND DATE(status_changed_at) >= DATE('now', '-{} days')
            GROUP BY DATE(status_changed_at)
            ORDER BY date ASC
        '''.format(days)
        
        results = self.db_service.get_cached_query(cache_key, query, cache_duration=300)
        read_data = {row['date']: row['read_count'] for row in results}
        
        # 生成趋势数据（只包含有数据的日期）
        trend_data = []
        for i in range(days):
            date = datetime.now().date() - timedelta(days=days - 1 - i)
            date_str = date.strftime('%Y-%m-%d')
            read_count = read_data.get(date_str, 0)
            
            trend_data.append({
                'date': date_str,
                'read_count': read_count
            })
        
        # 计算移动平均（优化版）
        self._calculate_moving_average(trend_data)
        
        # 计算趋势指标
        analysis = self._calculate_trend_analysis(trend_data, days)
        
        return {
            'days': days,
            'trend_data': trend_data,
            'analysis': analysis
        }
    
    def _calculate_moving_average(self, trend_data: List[Dict], window: int = 7):
        """计算移动平均（就地修改）"""
        for i, item in enumerate(trend_data):
            start_idx = max(0, i - window // 2)
            end_idx = min(len(trend_data), i + window // 2 + 1)
            
            avg_count = sum(trend_data[j]['read_count'] for j in range(start_idx, end_idx))
            avg_count = avg_count / (end_idx - start_idx)
            
            item['moving_average'] = round(avg_count, 2)
    
    def _calculate_trend_analysis(self, trend_data: List[Dict], days: int) -> Dict:
        """计算趋势分析指标"""
        if not trend_data:
            return {}
        
        first_half = trend_data[:days // 2]
        second_half = trend_data[days // 2:]
        
        first_half_avg = sum(item['read_count'] for item in first_half) / len(first_half)
        second_half_avg = sum(item['read_count'] for item in second_half) / len(second_half)
        
        trend_direction = 'up' if second_half_avg > first_half_avg else 'down' if second_half_avg < first_half_avg else 'stable'
        trend_change = abs(second_half_avg - first_half_avg)
        
        total_read = sum(item['read_count'] for item in trend_data)
        peak_day = max(trend_data, key=lambda x: x['read_count'])
        
        return {
            'trend_direction': trend_direction,
            'trend_change': round(trend_change, 2),
            'first_half_avg': round(first_half_avg, 2),
            'second_half_avg': round(second_half_avg, 2),
            'total_read': total_read,
            'peak_day': peak_day,
            'avg_per_day': round(total_read / days, 2)
        }
    
    def clear_cache(self):
        """清理统计缓存"""
        self.db_service.clear_cache()
    
    def get_database_stats(self) -> Dict:
        """获取数据库服务统计"""
        return self.db_service.get_statistics()