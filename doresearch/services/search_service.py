"""
论文搜索服务
支持多字段搜索、高级搜索、相关性排序等功能
"""
import sqlite3
import re
from typing import Dict, List, Optional, Tuple
from models.database import Database
from config import DATABASE_PATH


class SearchService:
    def __init__(self):
        self.db = Database(DATABASE_PATH)

    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def search_papers(self, query: str, search_fields: List[str] = None,
                      filters: Dict = None, limit: int = 50, offset: int = 0,
                      order_by: str = 'relevance') -> Dict:
        """
        搜索论文

        Args:
            query: 搜索关键词
            search_fields: 搜索字段列表，默认为['title', 'abstract', 'authors']
            filters: 过滤条件
            limit: 返回数量限制
            offset: 偏移量
            order_by: 排序方式（relevance, date, title）

        Returns:
            搜索结果字典
        """
        if not query or not query.strip():
            return {
                'success': False,
                'error': '搜索关键词不能为空'
            }

        query = query.strip()

        if search_fields is None:
            search_fields = ['title', 'abstract', 'authors']

        if filters is None:
            filters = {}

        conn = self.get_db()
        try:
            # 构建搜索查询
            search_sql, search_params = self._build_search_query(
                query, search_fields, filters, order_by, limit, offset
            )

            # 执行搜索
            c = conn.cursor()
            c.execute(search_sql, search_params)
            results = c.fetchall()

            # 获取总数（用于分页）
            count_sql, count_params = self._build_count_query(query, search_fields, filters)
            c.execute(count_sql, count_params)
            total_count = c.fetchone()[0]

            # 处理结果
            papers = []
            for row in results:
                paper_dict = dict(row)

                # 计算相关性得分和高亮
                if order_by == 'relevance':
                    paper_dict['relevance_score'] = self._calculate_relevance_score(
                        query, paper_dict, search_fields
                    )

                # 添加搜索高亮
                paper_dict['highlights'] = self._generate_highlights(
                    query, paper_dict, search_fields
                )

                # 检查是否在稍后阅读列表中
                paper_dict['is_read_later'] = self._check_read_later_status(paper_dict['id'])

                papers.append(paper_dict)

            return {
                'success': True,
                'data': {
                    'query': query,
                    'search_fields': search_fields,
                    'filters': filters,
                    'results': papers,
                    'pagination': {
                        'total_count': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_more': (offset + limit) < total_count,
                        'page': (offset // limit) + 1,
                        'total_pages': (total_count + limit - 1) // limit
                    },
                    'search_time_ms': 0  # 可以添加计时
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'搜索失败: {str(e)}'
            }
        finally:
            conn.close()

    def _build_search_query(self, query: str, search_fields: List[str],
                            filters: Dict, order_by: str, limit: int, offset: int) -> Tuple[str, List]:
        """构建搜索SQL查询"""

        # 基础查询
        base_query = '''
                     SELECT p.*, f.name as feed_name
                     FROM papers p
                              LEFT JOIN feeds f ON p.feed_id = f.id \
                     '''

        # 构建WHERE条件
        where_conditions = []
        params = []

        # 搜索条件
        if query:
            search_conditions = []
            search_terms = self._parse_search_query(query)

            for term in search_terms:
                field_conditions = []

                for field in search_fields:
                    if field in ['title', 'abstract', 'authors', 'journal', 'doi']:
                        field_conditions.append(f'p.{field} LIKE ?')
                        params.append(f'%{term}%')
                    elif field == 'abstract_cn':
                        field_conditions.append(f'p.abstract_cn LIKE ?')
                        params.append(f'%{term}%')

                if field_conditions:
                    search_conditions.append(f'({" OR ".join(field_conditions)})')

            if search_conditions:
                where_conditions.append(f'({" AND ".join(search_conditions)})')

        # 过滤条件
        if filters.get('status'):
            where_conditions.append('p.status = ?')
            params.append(filters['status'])

        if filters.get('journal'):
            where_conditions.append('p.journal LIKE ?')
            params.append(f'%{filters["journal"]}%')

        if filters.get('feed_id'):
            where_conditions.append('p.feed_id = ?')
            params.append(filters['feed_id'])

        if filters.get('start_date'):
            where_conditions.append('DATE(p.published_date) >= ?')
            params.append(filters['start_date'])

        if filters.get('end_date'):
            where_conditions.append('DATE(p.published_date) <= ?')
            params.append(filters['end_date'])

        if filters.get('has_pdf'):
            if filters['has_pdf']:
                where_conditions.append('(p.pdf_url IS NOT NULL OR p.pdf_path IS NOT NULL)')
            else:
                where_conditions.append('(p.pdf_url IS NULL AND p.pdf_path IS NULL)')

        if filters.get('has_analysis'):
            if filters['has_analysis']:
                where_conditions.append('p.analysis_result IS NOT NULL')
            else:
                where_conditions.append('p.analysis_result IS NULL')

        # 组装WHERE子句
        if where_conditions:
            base_query += ' WHERE ' + ' AND '.join(where_conditions)

        # 排序
        if order_by == 'relevance':
            # 相关性排序（通过匹配次数）
            relevance_score = self._build_relevance_score_sql(query, search_fields)
            base_query += f' ORDER BY {relevance_score} DESC, p.published_date DESC'
        elif order_by == 'date':
            base_query += ' ORDER BY p.published_date DESC'
        elif order_by == 'title':
            base_query += ' ORDER BY p.title ASC'
        elif order_by == 'created_at':
            base_query += ' ORDER BY p.created_at DESC'
        else:
            base_query += ' ORDER BY p.published_date DESC'

        # 分页
        base_query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        return base_query, params

    def _build_count_query(self, query: str, search_fields: List[str], filters: Dict) -> Tuple[str, List]:
        """构建计数查询"""
        count_query = 'SELECT COUNT(*) FROM papers p LEFT JOIN feeds f ON p.feed_id = f.id'

        where_conditions = []
        params = []

        # 搜索条件（与主查询相同）
        if query:
            search_conditions = []
            search_terms = self._parse_search_query(query)

            for term in search_terms:
                field_conditions = []

                for field in search_fields:
                    if field in ['title', 'abstract', 'authors', 'journal', 'doi']:
                        field_conditions.append(f'p.{field} LIKE ?')
                        params.append(f'%{term}%')
                    elif field == 'abstract_cn':
                        field_conditions.append(f'p.abstract_cn LIKE ?')
                        params.append(f'%{term}%')

                if field_conditions:
                    search_conditions.append(f'({" OR ".join(field_conditions)})')

            if search_conditions:
                where_conditions.append(f'({" AND ".join(search_conditions)})')

        # 过滤条件（与主查询相同）
        if filters.get('status'):
            where_conditions.append('p.status = ?')
            params.append(filters['status'])

        if filters.get('journal'):
            where_conditions.append('p.journal LIKE ?')
            params.append(f'%{filters["journal"]}%')

        if filters.get('feed_id'):
            where_conditions.append('p.feed_id = ?')
            params.append(filters['feed_id'])

        if filters.get('start_date'):
            where_conditions.append('DATE(p.published_date) >= ?')
            params.append(filters['start_date'])

        if filters.get('end_date'):
            where_conditions.append('DATE(p.published_date) <= ?')
            params.append(filters['end_date'])

        if filters.get('has_pdf'):
            if filters['has_pdf']:
                where_conditions.append('(p.pdf_url IS NOT NULL OR p.pdf_path IS NOT NULL)')
            else:
                where_conditions.append('(p.pdf_url IS NULL AND p.pdf_path IS NULL)')

        if filters.get('has_analysis'):
            if filters['has_analysis']:
                where_conditions.append('p.analysis_result IS NOT NULL')
            else:
                where_conditions.append('p.analysis_result IS NULL')

        if where_conditions:
            count_query += ' WHERE ' + ' AND '.join(where_conditions)

        return count_query, params

    def _parse_search_query(self, query: str) -> List[str]:
        """解析搜索查询，支持引号和多个词"""
        terms = []

        # 处理引号内的短语
        quoted_pattern = r'"([^"]*)"'
        quoted_matches = re.findall(quoted_pattern, query)

        # 移除引号内容，处理剩余单词
        remaining_query = re.sub(quoted_pattern, '', query)
        word_matches = re.findall(r'\b\w+\b', remaining_query, re.UNICODE)

        # 合并结果
        terms.extend(quoted_matches)
        terms.extend(word_matches)

        # 过滤掉过短的词
        return [term.strip() for term in terms if len(term.strip()) >= 2]

    def _build_relevance_score_sql(self, query: str, search_fields: List[str]) -> str:
        """构建相关性得分SQL"""
        score_parts = []
        terms = self._parse_search_query(query)

        for term in terms:
            for field in search_fields:
                if field in ['title', 'abstract', 'authors', 'journal']:
                    # 标题匹配权重更高
                    if field == 'title':
                        score_parts.append(f"(CASE WHEN p.{field} LIKE '%{term}%' THEN 3 ELSE 0 END)")
                    elif field == 'authors':
                        score_parts.append(f"(CASE WHEN p.{field} LIKE '%{term}%' THEN 2 ELSE 0 END)")
                    else:
                        score_parts.append(f"(CASE WHEN p.{field} LIKE '%{term}%' THEN 1 ELSE 0 END)")

        if score_parts:
            return f"({' + '.join(score_parts)})"
        else:
            return "0"

    def _calculate_relevance_score(self, query: str, paper: Dict, search_fields: List[str]) -> float:
        """计算相关性得分"""
        score = 0.0
        terms = self._parse_search_query(query)

        for term in terms:
            term_lower = term.lower()

            for field in search_fields:
                field_value = paper.get(field, '') or ''
                field_lower = field_value.lower()

                if term_lower in field_lower:
                    # 不同字段有不同权重
                    if field == 'title':
                        score += 3.0
                    elif field == 'authors':
                        score += 2.0
                    else:
                        score += 1.0

                    # 完全匹配加分
                    if term_lower == field_lower:
                        score += 2.0

        return score

    def _generate_highlights(self, query: str, paper: Dict, search_fields: List[str]) -> Dict:
        """生成搜索高亮"""
        highlights = {}
        terms = self._parse_search_query(query)

        for field in search_fields:
            field_value = paper.get(field, '') or ''
            if field_value:
                highlighted = field_value

                for term in terms:
                    # 使用正则表达式进行大小写不敏感的替换
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)

                if '<mark>' in highlighted:
                    highlights[field] = highlighted

        return highlights

    def _check_read_later_status(self, paper_id: int) -> bool:
        """检查论文是否在稍后阅读列表中"""
        try:
            from services.read_later_service import ReadLaterService
            read_later_service = ReadLaterService()
            return read_later_service.is_marked_read_later(paper_id)
        except:
            return False

    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """获取搜索建议"""
        if not query or len(query) < 2:
            return []

        conn = self.get_db()
        try:
            c = conn.cursor()

            # 从标题中获取建议
            c.execute('''
                      SELECT DISTINCT title
                      FROM papers
                      WHERE title LIKE ?
                      ORDER BY title LIMIT ?
                      ''', (f'%{query}%', limit // 2))

            title_suggestions = [row[0] for row in c.fetchall()]

            # 从作者中获取建议
            c.execute('''
                      SELECT DISTINCT authors
                      FROM papers
                      WHERE authors LIKE ?
                        AND authors IS NOT NULL
                      ORDER BY authors LIMIT ?
                      ''', (f'%{query}%', limit // 2))

            author_suggestions = [row[0] for row in c.fetchall()]

            # 合并并去重
            all_suggestions = title_suggestions + author_suggestions
            return list(dict.fromkeys(all_suggestions))[:limit]

        except Exception as e:
            print(f"❌ 获取搜索建议失败: {e}")
            return []
        finally:
            conn.close()

    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """获取热门搜索词（基于论文中的常见词汇）"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 获取期刊分布（作为热门搜索）
            c.execute('''
                      SELECT journal, COUNT(*) as count
                      FROM papers
                      WHERE journal IS NOT NULL AND journal != ''
                      GROUP BY journal
                      ORDER BY count DESC
                          LIMIT ?
                      ''', (limit,))

            popular_terms = []
            for row in c.fetchall():
                popular_terms.append({
                    'term': row[0],
                    'count': row[1],
                    'type': 'journal'
                })

            return popular_terms

        except Exception as e:
            print(f"❌ 获取热门搜索失败: {e}")
            return []
        finally:
            conn.close()

    def advanced_search(self, criteria: Dict) -> Dict:
        """高级搜索"""

        filters = {}
        search_fields = criteria.get('search_fields', ['title', 'abstract', 'authors'])

        # 构建过滤条件
        if criteria.get('status'):
            filters['status'] = criteria['status']

        if criteria.get('journal'):
            filters['journal'] = criteria['journal']

        if criteria.get('feed_id'):
            filters['feed_id'] = criteria['feed_id']

        if criteria.get('date_range'):
            if criteria['date_range'].get('start'):
                filters['start_date'] = criteria['date_range']['start']
            if criteria['date_range'].get('end'):
                filters['end_date'] = criteria['date_range']['end']

        if 'has_pdf' in criteria:
            filters['has_pdf'] = criteria['has_pdf']

        if 'has_analysis' in criteria:
            filters['has_analysis'] = criteria['has_analysis']

        # 执行搜索
        return self.search_papers(
            query=criteria.get('query', ''),
            search_fields=search_fields,
            filters=filters,
            limit=criteria.get('limit', 50),
            offset=criteria.get('offset', 0),
            order_by=criteria.get('order_by', 'relevance')
        )