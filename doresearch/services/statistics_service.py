"""
统计服务 - 高性能论文阅读统计
优化数据库查询性能，避免全表扫描
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models.database import Database
from config import DATABASE_PATH


class StatisticsService:
    def __init__(self):
        self.db = Database(DATABASE_PATH)

    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_reading_statistics(self) -> Dict:
        """获取完整的阅读统计数据"""
        conn = self.get_db()
        try:
            # 获取基础统计
            basic_stats = self._get_basic_statistics(conn)

            # 获取连续阅读天数
            streak_days = self._get_reading_streak(conn)

            # 获取近30天统计
            last_30_days = self._get_last_30_days_statistics(conn)

            # 获取近一年已读统计
            last_year_read = self._get_last_year_read_statistics(conn)

            return {
                'basic': basic_stats,
                'reading_streak_days': streak_days,
                'last_30_days': last_30_days,
                'last_year_read': last_year_read,
                'generated_at': datetime.now().isoformat()
            }
        finally:
            conn.close()

    def _get_basic_statistics(self, conn: sqlite3.Connection) -> Dict:
        """获取基础统计数据"""
        c = conn.cursor()

        # 单次查询获取总数和已读数
        c.execute('''
                  SELECT COUNT(*)                                         as total_papers,
                         SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as read_papers
                  FROM papers
                  ''')
        result = c.fetchone()

        return {
            'total_papers': result['total_papers'],
            'read_papers': result['read_papers'],
            'unread_papers': result['total_papers'] - result['read_papers']
        }

    def _get_reading_streak(self, conn: sqlite3.Connection) -> int:
        """获取连续阅读天数（从今天往前计算）"""
        c = conn.cursor()

        # 获取最近有阅读活动的日期（按天分组）
        c.execute('''
                  SELECT DATE (status_changed_at) as read_date
                  FROM papers
                  WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE (status_changed_at) >= DATE ('now'
                      , '-365 days')
                  GROUP BY DATE (status_changed_at)
                  ORDER BY read_date DESC
                  ''')

        read_dates = [row['read_date'] for row in c.fetchall()]

        if not read_dates:
            return 0

        # 计算连续天数
        today = datetime.now().date()
        streak = 0

        for i, date_str in enumerate(read_dates):
            read_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            expected_date = today - timedelta(days=i)

            if read_date == expected_date:
                streak += 1
            else:
                break

        return streak

    def _get_last_30_days_statistics(self, conn: sqlite3.Connection) -> Dict:
        """获取近30天统计数据"""
        c = conn.cursor()

        # 获取近30天每天的新增文章数
        c.execute('''
                  SELECT
                      DATE (published_date) as date, COUNT (*) as new_papers
                  FROM papers
                  WHERE DATE (published_date) >= DATE ('now', '-30 days')
                  GROUP BY DATE (published_date)
                  ORDER BY date DESC
                  ''')
        new_papers_data = {row['date']: row['new_papers'] for row in c.fetchall()}

        # 获取近30天每天的已读文章数
        c.execute('''
                  SELECT
                      DATE (status_changed_at) as date, COUNT (*) as read_papers
                  FROM papers
                  WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE (status_changed_at) >= DATE ('now'
                      , '-30 days')
                  GROUP BY DATE (status_changed_at)
                  ORDER BY date DESC
                  ''')
        read_papers_data = {row['date']: row['read_papers'] for row in c.fetchall()}

        # 生成近30天的完整数据
        daily_stats = []
        for i in range(30):
            date = datetime.now().date() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            daily_stats.append({
                'date': date_str,
                'new_papers': new_papers_data.get(date_str, 0),
                'read_papers': read_papers_data.get(date_str, 0)
            })

        # 计算30天总计
        total_new = sum(item['new_papers'] for item in daily_stats)
        total_read = sum(item['read_papers'] for item in daily_stats)

        return {
            'daily_data': daily_stats,
            'summary': {
                'total_new_papers': total_new,
                'total_read_papers': total_read,
                'avg_new_per_day': round(total_new / 30, 1),
                'avg_read_per_day': round(total_read / 30, 1)
            }
        }

    def _get_last_year_read_statistics(self, conn: sqlite3.Connection) -> Dict:
        """获取近一年已读文章统计"""
        c = conn.cursor()

        # 获取近一年每天的已读文章数
        c.execute('''
                  SELECT
                      DATE (status_changed_at) as date, COUNT (*) as read_papers
                  FROM papers
                  WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE (status_changed_at) >= DATE ('now'
                      , '-365 days')
                  GROUP BY DATE (status_changed_at)
                  ORDER BY date ASC
                  ''')

        read_data = {row['date']: row['read_papers'] for row in c.fetchall()}

        # 按月统计
        monthly_stats = {}
        daily_stats = []

        # 生成近一年的每日数据
        start_date = datetime.now().date() - timedelta(days=365)
        for i in range(366):  # 包含今天
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            month_key = date.strftime('%Y-%m')

            read_count = read_data.get(date_str, 0)

            daily_stats.append({
                'date': date_str,
                'read_papers': read_count
            })

            # 累计月度统计
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'month': month_key,
                    'read_papers': 0,
                    'reading_days': 0
                }

            monthly_stats[month_key]['read_papers'] += read_count
            if read_count > 0:
                monthly_stats[month_key]['reading_days'] += 1

        # 计算总计
        total_read = sum(item['read_papers'] for item in daily_stats)
        reading_days = sum(1 for item in daily_stats if item['read_papers'] > 0)

        return {
            'daily_data': daily_stats,
            'monthly_data': list(monthly_stats.values()),
            'summary': {
                'total_read_papers': total_read,
                'total_reading_days': reading_days,
                'avg_read_per_day': round(total_read / 365, 1) if total_read > 0 else 0,
                'avg_read_per_reading_day': round(total_read / reading_days, 1) if reading_days > 0 else 0
            }
        }

    def get_quick_stats(self) -> Dict:
        """获取快速统计（只包含基础数据）"""
        conn = self.get_db()
        try:
            basic_stats = self._get_basic_statistics(conn)
            streak_days = self._get_reading_streak(conn)

            return {
                **basic_stats,
                'reading_streak_days': streak_days,
                'generated_at': datetime.now().isoformat()
            }
        finally:
            conn.close()

    def get_reading_calendar(self, year: int = None) -> Dict:
        """获取阅读日历数据（类似GitHub贡献图）"""
        if year is None:
            year = datetime.now().year

        conn = self.get_db()
        try:
            c = conn.cursor()

            # 获取指定年份的每日阅读数据
            c.execute('''
                      SELECT
                          DATE (status_changed_at) as date, COUNT (*) as read_count
                      FROM papers
                      WHERE status = 'read'
                        AND status_changed_at IS NOT NULL
                        AND strftime('%Y'
                          , status_changed_at) = ?
                      GROUP BY DATE (status_changed_at)
                      ORDER BY date ASC
                      ''', (str(year),))

            read_data = {row['date']: row['read_count'] for row in c.fetchall()}

            # 生成全年日历
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()

            calendar_data = []
            current_date = start_date

            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                read_count = read_data.get(date_str, 0)

                # 计算强度等级（0-4）
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

            # 计算年度统计
            total_read = sum(item['count'] for item in calendar_data)
            reading_days = sum(1 for item in calendar_data if item['count'] > 0)

            return {
                'year': year,
                'calendar_data': calendar_data,
                'summary': {
                    'total_read_papers': total_read,
                    'total_reading_days': reading_days,
                    'avg_read_per_day': round(total_read / len(calendar_data), 2),
                    'reading_rate': round(reading_days / len(calendar_data) * 100, 1)  # 阅读天数百分比
                }
            }
        finally:
            conn.close()

    def get_reading_trends(self, days: int = 90) -> Dict:
        """获取阅读趋势分析"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 获取指定天数内的趋势数据
            c.execute('''
                SELECT 
                    DATE(status_changed_at) as date,
                    COUNT(*) as read_count
                FROM papers 
                WHERE status = 'read'
                    AND status_changed_at IS NOT NULL
                    AND DATE(status_changed_at) >= DATE('now', '-{} days')
                GROUP BY DATE(status_changed_at)
                ORDER BY date ASC
            '''.format(days))

            trend_data = []
            read_data = {row['date']: row['read_count'] for row in c.fetchall()}

            # 生成趋势数据
            for i in range(days):
                date = datetime.now().date() - timedelta(days=days - 1 - i)
                date_str = date.strftime('%Y-%m-%d')
                read_count = read_data.get(date_str, 0)

                trend_data.append({
                    'date': date_str,
                    'read_count': read_count
                })

            # 计算移动平均（7天）
            for i, item in enumerate(trend_data):
                start_idx = max(0, i - 3)
                end_idx = min(len(trend_data), i + 4)

                avg_count = sum(trend_data[j]['read_count'] for j in range(start_idx, end_idx))
                avg_count = avg_count / (end_idx - start_idx)

                item['moving_average'] = round(avg_count, 2)

            # 计算趋势指标
            first_half = trend_data[:days // 2]
            second_half = trend_data[days // 2:]

            first_half_avg = sum(item['read_count'] for item in first_half) / len(first_half)
            second_half_avg = sum(item['read_count'] for item in second_half) / len(second_half)

            trend_direction = 'up' if second_half_avg > first_half_avg else 'down' if second_half_avg < first_half_avg else 'stable'
            trend_change = abs(second_half_avg - first_half_avg)

            return {
                'days': days,
                'trend_data': trend_data,
                'analysis': {
                    'trend_direction': trend_direction,
                    'trend_change': round(trend_change, 2),
                    'first_half_avg': round(first_half_avg, 2),
                    'second_half_avg': round(second_half_avg, 2),
                    'total_read': sum(item['read_count'] for item in trend_data),
                    'peak_day': max(trend_data, key=lambda x: x['read_count']),
                    'avg_per_day': round(sum(item['read_count'] for item in trend_data) / days, 2)
                }
            }
        finally:
            conn.close()