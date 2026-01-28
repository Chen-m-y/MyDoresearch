"""
稍后阅读服务
管理稍后阅读的论文列表
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from models.database import Database
from config import DATABASE_PATH


class ReadLaterService:
    def __init__(self):
        self.db = Database(DATABASE_PATH)

    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def mark_read_later(self, paper_id: int, user_id: int = None, priority: int = 5,
                        notes: str = None, tags: str = None,
                        estimated_read_time: int = None) -> Dict:
        """标记论文为稍后阅读"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 检查论文是否存在
            c.execute('SELECT id, title FROM papers WHERE id = ?', (paper_id,))
            paper = c.fetchone()

            if not paper:
                return {'success': False, 'error': '论文不存在'}

            # 检查是否已经标记（按用户）
            if user_id:
                c.execute('SELECT id FROM read_later WHERE paper_id = ? AND user_id = ?', (paper_id, user_id))
            else:
                c.execute('SELECT id FROM read_later WHERE paper_id = ? AND user_id IS NULL', (paper_id,))
            existing = c.fetchone()

            if existing:
                return {'success': False, 'error': '该论文已在稍后阅读列表中'}

            # 插入稍后阅读记录
            c.execute('''INSERT INTO read_later
                             (user_id, paper_id, priority, notes, tags, estimated_read_time, marked_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, paper_id, priority, notes, tags, estimated_read_time,
                       datetime.now().isoformat()))

            conn.commit()

            print(f"📚 论文 {paper_id} ({paper['title'][:50]}...) 已标记为稍后阅读")

            return {
                'success': True,
                'message': '已添加到稍后阅读列表',
                'paper_id': paper_id,
                'marked_at': datetime.now().isoformat()
            }

        except sqlite3.IntegrityError as e:
            return {'success': False, 'error': '该论文已在稍后阅读列表中'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def unmark_read_later(self, paper_id: int, user_id: int = None) -> Dict:
        """取消标记稍后阅读"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 检查是否存在（按用户）
            if user_id:
                c.execute('SELECT id FROM read_later WHERE paper_id = ? AND user_id = ?', (paper_id, user_id))
            else:
                c.execute('SELECT id FROM read_later WHERE paper_id = ? AND user_id IS NULL', (paper_id,))
            existing = c.fetchone()

            if not existing:
                return {'success': False, 'error': '该论文不在稍后阅读列表中'}

            # 删除记录（按用户）
            if user_id:
                c.execute('DELETE FROM read_later WHERE paper_id = ? AND user_id = ?', (paper_id, user_id))
            else:
                c.execute('DELETE FROM read_later WHERE paper_id = ? AND user_id IS NULL', (paper_id,))
            conn.commit()

            print(f"📚 论文 {paper_id} 已从稍后阅读列表中移除")

            return {
                'success': True,
                'message': '已从稍后阅读列表中移除',
                'paper_id': paper_id
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def update_read_later(self, paper_id: int, user_id: int = None, priority: int = None,
                          notes: str = None, tags: str = None,
                          estimated_read_time: int = None) -> Dict:
        """更新稍后阅读信息"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 检查是否存在（按用户）
            if user_id:
                c.execute('SELECT id FROM read_later WHERE paper_id = ? AND user_id = ?', (paper_id, user_id))
            else:
                c.execute('SELECT id FROM read_later WHERE paper_id = ? AND user_id IS NULL', (paper_id,))
            existing = c.fetchone()

            if not existing:
                return {'success': False, 'error': '该论文不在稍后阅读列表中'}

            # 构建更新语句
            update_fields = []
            params = []

            if priority is not None:
                update_fields.append('priority = ?')
                params.append(priority)

            if notes is not None:
                update_fields.append('notes = ?')
                params.append(notes)

            if tags is not None:
                update_fields.append('tags = ?')
                params.append(tags)

            if estimated_read_time is not None:
                update_fields.append('estimated_read_time = ?')
                params.append(estimated_read_time)

            if not update_fields:
                return {'success': False, 'error': '没有提供要更新的字段'}

            # 添加更新时间
            update_fields.append('updated_at = ?')
            params.append(datetime.now().isoformat())

            # 添加WHERE条件
            params.append(paper_id)

            # 执行更新（按用户）
            if user_id:
                c.execute(f'UPDATE read_later SET {", ".join(update_fields)} WHERE paper_id = ? AND user_id = ?',
                          params + [user_id])
            else:
                c.execute(f'UPDATE read_later SET {", ".join(update_fields)} WHERE paper_id = ? AND user_id IS NULL',
                          params)
            conn.commit()

            return {
                'success': True,
                'message': '稍后阅读信息已更新',
                'paper_id': paper_id
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_read_later_list(self, user_id: int = None, order_by: str = 'priority',
                            limit: int = None, offset: int = 0) -> List[Dict]:
        """获取稍后阅读列表"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 构建查询语句
            base_query = '''
                         SELECT rl.*, 
                                p.title, 
                                p.abstract, 
                                p.authors, 
                                p.journal, 
                                p.published_date, 
                                p.url, 
                                p.doi, 
                                p.status, 
                                p.ieee_article_number, 
                                p.analysis_result, 
                                p.abstract_cn,
                                p.pdf_path 
                         FROM read_later rl
                                  JOIN papers p ON rl.paper_id = p.id 
                         '''
            
            # 添加用户过滤
            if user_id:
                base_query += ' WHERE rl.user_id = ? '
                query_params = [user_id]
            else:
                base_query += ' WHERE rl.user_id IS NULL '
                query_params = []

            # 添加排序
            order_options = {
                'priority': 'rl.priority DESC, rl.marked_at DESC',
                'marked_at': 'rl.marked_at DESC',
                'title': 'p.title ASC',
                'published_date': 'p.published_date DESC'
            }

            order_clause = order_options.get(order_by, order_options['priority'])
            query = f"{base_query} ORDER BY {order_clause}"

            # 添加分页
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            c.execute(query, query_params)
            results = c.fetchall()

            read_later_list = []
            for row in results:
                item = dict(row)

                # 解析标签
                if item['tags']:
                    item['tags'] = [tag.strip() for tag in item['tags'].split(',') if tag.strip()]
                else:
                    item['tags'] = []

                read_later_list.append(item)

            return read_later_list

        except Exception as e:
            print(f"❌ 获取稍后阅读列表失败: {e}")
            return []
        finally:
            conn.close()

    def get_read_later_count(self, user_id: int = None) -> int:
        """获取稍后阅读列表总数"""
        conn = self.get_db()
        try:
            c = conn.cursor()
            if user_id:
                c.execute('SELECT COUNT(*) FROM read_later WHERE user_id = ?', (user_id,))
            else:
                c.execute('SELECT COUNT(*) FROM read_later WHERE user_id IS NULL')
            return c.fetchone()[0]
        except Exception as e:
            print(f"❌ 获取稍后阅读数量失败: {e}")
            return 0
        finally:
            conn.close()

    def is_marked_read_later(self, paper_id: int) -> bool:
        """检查论文是否标记为稍后阅读"""
        conn = self.get_db()
        try:
            c = conn.cursor()
            c.execute('SELECT id FROM read_later WHERE paper_id = ?', (paper_id,))
            return c.fetchone() is not None
        except Exception as e:
            print(f"❌ 检查稍后阅读状态失败: {e}")
            return False
        finally:
            conn.close()

    def get_read_later_stats(self) -> Dict:
        """获取稍后阅读统计信息"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 总数
            c.execute('SELECT COUNT(*) FROM read_later')
            total_count = c.fetchone()[0]

            # 按优先级分组
            c.execute('''SELECT priority, COUNT(*) as count
                         FROM read_later
                         GROUP BY priority
                         ORDER BY priority DESC''')
            priority_stats = [{'priority': row[0], 'count': row[1]} for row in c.fetchall()]

            # 按标记时间统计（近7天）
            c.execute('''SELECT DATE (marked_at) as date, COUNT (*) as count
                         FROM read_later
                         WHERE DATE (marked_at) >= DATE ('now', '-7 days')
                         GROUP BY DATE (marked_at)
                         ORDER BY date DESC''')
            recent_marks = [{'date': row[0], 'count': row[1]} for row in c.fetchall()]

            # 预估总阅读时间
            c.execute('SELECT SUM(estimated_read_time) FROM read_later WHERE estimated_read_time IS NOT NULL')
            total_estimated_time = c.fetchone()[0] or 0

            # 有标签的数量
            c.execute('SELECT COUNT(*) FROM read_later WHERE tags IS NOT NULL AND tags != ""')
            tagged_count = c.fetchone()[0]

            # 有笔记的数量
            c.execute('SELECT COUNT(*) FROM read_later WHERE notes IS NOT NULL AND notes != ""')
            noted_count = c.fetchone()[0]

            return {
                'total_count': total_count,
                'priority_distribution': priority_stats,
                'recent_marks': recent_marks,
                'total_estimated_time_minutes': total_estimated_time,
                'tagged_count': tagged_count,
                'noted_count': noted_count,
                'avg_priority': self._get_average_priority()
            }

        except Exception as e:
            print(f"❌ 获取稍后阅读统计失败: {e}")
            return {}
        finally:
            conn.close()

    def _get_average_priority(self) -> float:
        """获取平均优先级"""
        conn = self.get_db()
        try:
            c = conn.cursor()
            c.execute('SELECT AVG(priority) FROM read_later')
            result = c.fetchone()[0]
            return round(result, 1) if result else 5.0
        except:
            return 5.0
        finally:
            conn.close()

    def search_read_later(self, query: str, search_in: List[str] = None) -> List[Dict]:
        """搜索稍后阅读列表"""
        if search_in is None:
            search_in = ['title', 'abstract', 'authors', 'notes', 'tags']

        conn = self.get_db()
        try:
            c = conn.cursor()

            # 构建搜索条件
            search_conditions = []
            params = []

            query_pattern = f'%{query}%'

            if 'title' in search_in:
                search_conditions.append('p.title LIKE ?')
                params.append(query_pattern)

            if 'abstract' in search_in:
                search_conditions.append('p.abstract LIKE ?')
                params.append(query_pattern)

            if 'authors' in search_in:
                search_conditions.append('p.authors LIKE ?')
                params.append(query_pattern)

            if 'notes' in search_in:
                search_conditions.append('rl.notes LIKE ?')
                params.append(query_pattern)

            if 'tags' in search_in:
                search_conditions.append('rl.tags LIKE ?')
                params.append(query_pattern)

            if not search_conditions:
                return []

            # 执行搜索
            search_query = f'''
                SELECT 
                    rl.*,
                    p.title,
                    p.abstract,
                    p.authors,
                    p.journal,
                    p.published_date,
                    p.url,
                    p.doi,
                    p.status,
                    p.pdf_path
                FROM read_later rl
                JOIN papers p ON rl.paper_id = p.id
                WHERE ({' OR '.join(search_conditions)})
                ORDER BY rl.priority DESC, rl.marked_at DESC
            '''

            c.execute(search_query, params)
            results = c.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            print(f"❌ 搜索稍后阅读列表失败: {e}")
            return []
        finally:
            conn.close()

    def bulk_update_priority(self, paper_ids: List[int], priority: int) -> Dict:
        """批量更新优先级"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 验证所有paper_id都在稍后阅读列表中
            placeholders = ','.join(['?'] * len(paper_ids))
            c.execute(f'SELECT paper_id FROM read_later WHERE paper_id IN ({placeholders})',
                      paper_ids)
            existing_ids = [row[0] for row in c.fetchall()]

            if len(existing_ids) != len(paper_ids):
                missing_ids = set(paper_ids) - set(existing_ids)
                return {
                    'success': False,
                    'error': f'以下论文不在稍后阅读列表中: {list(missing_ids)}'
                }

            # 批量更新
            c.execute(f'''UPDATE read_later 
                         SET priority = ?, updated_at = ? 
                         WHERE paper_id IN ({placeholders})''',
                      [priority, datetime.now().isoformat()] + paper_ids)

            conn.commit()

            return {
                'success': True,
                'message': f'已更新 {len(paper_ids)} 篇论文的优先级',
                'updated_count': len(paper_ids)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()