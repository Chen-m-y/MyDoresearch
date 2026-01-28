"""
论文管理服务 - 修改版
支持新的JSON格式解析和状态变化时间记录
"""
import sqlite3
import requests
import json
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional
from models.database import Database
from config import DATABASE_PATH


class PaperManager:
    """论文管理服务"""

    def __init__(self):
        self.db = Database(DATABASE_PATH)

    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def add_feed(self, name: str, url: str, journal: str = "", user_id: int = None) -> Dict:
        """添加论文源"""
        if not user_id:
            return {'success': False, 'error': '用户ID不能为空'}
            
        conn = self.get_db()
        try:
            c = conn.cursor()
            c.execute('INSERT INTO feeds (name, url, journal, user_id) VALUES (?, ?, ?, ?)',
                      (name, url, journal, user_id))
            feed_id = c.lastrowid
            conn.commit()
            return {'success': True, 'feed_id': feed_id}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'API地址已存在'}
        finally:
            conn.close()

    def get_all_feeds(self, include: List[str] = None, user_id: int = None) -> List[Dict]:
        """获取所有论文源（支持扩展信息）"""
        if not user_id:
            return []
            
        conn = self.get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM feeds WHERE active = 1 AND user_id = ? ORDER BY name', (user_id,))
        feeds = [dict(row) for row in c.fetchall()]
        
        include = include or []
        
        if include:
            for feed in feeds:
                feed_id = feed['id']
                
                # 包含未读数量统计
                if 'unread_counts' in include:
                    c.execute('SELECT COUNT(*) FROM papers WHERE feed_id = ? AND status = ?', 
                             (feed_id, 'unread'))
                    feed['unread_count'] = c.fetchone()[0]
                
                # 包含总论文数统计
                if 'paper_counts' in include:
                    c.execute('SELECT COUNT(*) FROM papers WHERE feed_id = ?', (feed_id,))
                    feed['total_papers'] = c.fetchone()[0]
                    
                    # 各状态统计
                    c.execute('''SELECT status, COUNT(*) as count 
                                FROM papers WHERE feed_id = ? 
                                GROUP BY status''', (feed_id,))
                    status_counts = {row['status']: row['count'] for row in c.fetchall()}
                    feed['status_counts'] = {
                        'read': status_counts.get('read', 0),
                        'unread': status_counts.get('unread', 0),
                        'reading': status_counts.get('reading', 0)
                    }
                
                # 包含最后更新信息 (已经在基础数据中)
                if 'last_updated' in include:
                    # last_updated 已经在基础查询中包含
                    pass
        
        conn.close()
        return feeds

    def update_feed(self, feed_id: int, user_id: int = None) -> Dict:
        """更新指定论文源的文章"""
        if not user_id:
            return {'success': False, 'error': '用户ID不能为空'}
            
        conn = self.get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM feeds WHERE id = ? AND user_id = ?', (feed_id, user_id))
        feed = c.fetchone()

        if not feed:
            conn.close()
            return {'success': False, 'error': '论文源不存在或无权限访问'}

        try:
            response = requests.get(feed['url'], timeout=30)
            response.raise_for_status()
            papers_data = response.json()

            if not isinstance(papers_data, list):
                return {'success': False, 'error': 'API响应格式错误，应该是数组格式'}

            new_papers = 0

            for paper_data in papers_data:
                if not paper_data.get('title'):
                    continue

                paper_hash = hashlib.md5(
                    (paper_data.get('title', '') +
                     paper_data.get('url', '') +
                     str(paper_data.get('external_id', ''))).encode()
                ).hexdigest()

                c.execute('SELECT id FROM papers WHERE hash = ?', (paper_hash,))
                if c.fetchone():
                    continue

                # 提取IEEE文章编号
                ieee_number = self._extract_ieee_number(paper_data)

                title = paper_data.get('title', '').strip()
                abstract = paper_data.get('abstract', '').strip()

                # 修改：从 'author' 字段获取作者信息，而不是 'authors'
                authors = paper_data.get('author', paper_data.get('authors', ''))

                journal = paper_data.get('journal') or feed['journal']
                url = paper_data.get('url', '')
                pdf_url = paper_data.get('pdf_url', '')
                doi = paper_data.get('doi', '')
                external_id = paper_data.get('id', '')

                # 修改：支持新的日期字段格式
                published_date = self._parse_date_from_json(paper_data)

                status = paper_data.get('status', 'unread')

                # 获取当前时间作为状态变化时间
                current_time = datetime.now().isoformat()

                c.execute('''INSERT INTO papers
                             (feed_id, title, abstract, authors, journal, published_date,
                              url, pdf_url, doi, status, status_changed_at, hash, external_id, ieee_article_number)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (feed_id, title, abstract, authors, journal,
                           published_date, url, pdf_url, doi, status, current_time, paper_hash,
                           external_id, ieee_number))
                new_papers += 1

            c.execute('UPDATE feeds SET last_updated = CURRENT_TIMESTAMP WHERE id = ?',
                      (feed_id,))

            conn.commit()
            return {'success': True, 'new_papers': new_papers}

        except requests.RequestException as e:
            return {'success': False, 'error': f'网络请求失败: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON解析失败: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'更新失败: {str(e)}'}
        finally:
            conn.close()

    def _extract_ieee_number(self, paper_data: Dict) -> Optional[str]:
        """从论文数据中提取IEEE文章编号"""
        # 1. 直接从字段获取
        ieee_number = paper_data.get('ieee_article_number')
        if ieee_number:
            return ieee_number

        # 2. 从DOI提取
        doi = paper_data.get('doi')
        if doi and 'ieee' in doi.lower():
            ieee_match = re.search(r'(\d+)$', doi)
            if ieee_match:
                return ieee_match.group(1)

        # 3. 从URL提取
        url = paper_data.get('url')
        if url and 'ieee' in url.lower():
            ieee_match = re.search(r'/document/(\d+)', url)
            if ieee_match:
                return ieee_match.group(1)

        return None

    def _parse_date_from_json(self, paper_data: Dict) -> str:
        """从JSON数据中解析发布日期 - 支持新格式"""
        # 支持新的字段名
        date_fields = ['published_at', 'published_date', 'date', 'created_at', 'updated_at', 'pub_date']

        for field in date_fields:
            date_value = paper_data.get(field)
            if date_value:
                try:
                    if isinstance(date_value, (int, float)):
                        return datetime.fromtimestamp(date_value).isoformat()

                    if isinstance(date_value, str):
                        try:
                            # 处理ISO格式时间（包含Z后缀）
                            if date_value.endswith('Z'):
                                date_value = date_value[:-1] + '+00:00'
                            return datetime.fromisoformat(date_value).isoformat()
                        except:
                            pass

                        date_formats = [
                            '%Y-%m-%d',
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S.%f',
                            '%Y/%m/%d',
                            '%d/%m/%Y',
                            '%m/%d/%Y'
                        ]

                        for fmt in date_formats:
                            try:
                                return datetime.strptime(date_value, fmt).isoformat()
                            except:
                                continue
                except:
                    continue

        return datetime.now().isoformat()

    def get_papers_by_feed(self, feed_id: int, status: str = None, page: int = 1, per_page: int = 20, include_stats: bool = False) -> Dict:
        """获取指定订阅的论文列表（带分页和统计）"""
        conn = self.get_db()
        c = conn.cursor()

        # 支持 status="all" 的情况
        if status == "all":
            status = None

        # 构建基础查询
        base_query = 'FROM papers WHERE feed_id = ?'
        params = [feed_id]

        if status:
            base_query += ' AND status = ?'
            params.append(status)

        # 获取总数
        count_query = f'SELECT COUNT(*) {base_query}'
        c.execute(count_query, params)
        total = c.fetchone()[0]

        # 计算分页参数
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page

        # 获取分页数据
        data_query = f'SELECT * {base_query} ORDER BY published_date DESC LIMIT ? OFFSET ?'
        c.execute(data_query, params + [per_page, offset])
        papers = [dict(row) for row in c.fetchall()]
        
        result = {
            'papers': papers,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        }

        # 如果需要包含统计信息
        if include_stats:
            # 获取该feed的全部状态统计
            c.execute('''SELECT status, COUNT(*) as count 
                         FROM papers WHERE feed_id = ? 
                         GROUP BY status''', (feed_id,))
            stats_rows = c.fetchall()
            
            stats = {
                'total': 0,
                'read': 0,
                'unread': 0,
                'reading': 0
            }
            
            for row in stats_rows:
                stats['total'] += row['count']
                stats[row['status']] = row['count']
            
            # 获取今日新增数量
            from datetime import date
            today = date.today().isoformat()
            c.execute('''SELECT COUNT(*) FROM papers 
                         WHERE feed_id = ? AND DATE(created_at) = ?''', (feed_id, today))
            today_added = c.fetchone()[0]
            stats['today_added'] = today_added
            
            result['stats'] = stats
        
        conn.close()
        return result

    def get_paper(self, paper_id: int, expand: List[str] = None, user_id: int = None) -> Optional[Dict]:
        """获取单篇论文详情（支持扩展信息）"""
        conn = self.get_db()
        c = conn.cursor()
        
        # 检查用户是否有权访问该论文（通过feed或subscription的用户关联）
        if user_id:
            c.execute('''SELECT p.* FROM papers p 
                        LEFT JOIN feeds f ON p.feed_id = f.id 
                        LEFT JOIN user_subscriptions us ON p.subscription_id = us.id 
                        WHERE p.id = ? AND (f.user_id = ? OR us.user_id = ?)''', 
                     (paper_id, user_id, user_id))
        else:
            c.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
            
        paper = c.fetchone()

        if not paper:
            conn.close()
            return None

        paper_dict = dict(paper)
        expand = expand or []

        # 获取相关任务信息 (默认包含或者在expand中)
        if 'analysis' in expand or not expand:
            # 只获取当前用户的任务
            if user_id:
                c.execute('''SELECT *
                             FROM tasks
                             WHERE paper_id = ? AND user_id = ?
                               AND task_type = 'deep_analysis'
                             ORDER BY created_at DESC LIMIT 1''', (paper_id, user_id))
            else:
                c.execute('''SELECT *
                             FROM tasks
                             WHERE paper_id = ?
                               AND task_type = 'deep_analysis'
                             ORDER BY created_at DESC LIMIT 1''', (paper_id,))
            
            task = c.fetchone()

            if task:
                paper_dict['analysis_task'] = dict(task)
                # 获取任务步骤
                from services.task_manager import TaskManager
                task_manager = TaskManager()
                paper_dict['analysis_task']['steps'] = task_manager.get_task_steps(task['id'])

        # 获取稍后阅读信息 (默认包含或者在expand中)
        if 'read_later' in expand or 'full' in expand or not expand:
            if user_id:
                c.execute('''SELECT * FROM read_later WHERE paper_id = ? AND user_id = ?''', (paper_id, user_id))
            else:
                c.execute('''SELECT * FROM read_later WHERE paper_id = ?''', (paper_id,))
            read_later = c.fetchone()
            if read_later:
                paper_dict['read_later'] = dict(read_later)
            else:
                paper_dict['read_later'] = None

        # 获取相似论文推荐
        if 'similar' in expand or 'full' in expand:
            # 基于相同期刊和关键词的简单相似度算法
            c.execute('''SELECT id, title, authors, published_date, status
                         FROM papers 
                         WHERE journal = ? AND id != ? 
                         ORDER BY published_date DESC LIMIT 5''', 
                         (paper['journal'], paper_id))
            similar_papers = [dict(row) for row in c.fetchall()]
            paper_dict['similar_papers'] = similar_papers

        conn.close()
        return paper_dict

    def update_paper_status(self, paper_id: int, status: str, return_stats: bool = False) -> Dict:
        """更新论文状态并记录变化时间"""
        conn = self.get_db()
        try:
            c = conn.cursor()

            # 获取当前状态和feed_id
            c.execute('SELECT status, feed_id FROM papers WHERE id = ?', (paper_id,))
            current_row = c.fetchone()

            if not current_row:
                return {'success': False, 'error': '论文不存在'}

            current_status = current_row['status']
            feed_id = current_row['feed_id']
            
            result = {'success': True, 'status_changed': current_status != status}

            # 获取旧统计数据 (如果需要返回统计变化)
            old_stats = None
            if return_stats:
                old_stats = self.get_feed_stats(feed_id)

            # 只有状态真正发生变化时才更新状态变化时间
            if current_status != status:
                current_time = datetime.now().isoformat()
                c.execute('UPDATE papers SET status = ?, status_changed_at = ? WHERE id = ?',
                          (status, current_time, paper_id))
                print(f"📝 论文 {paper_id} 状态从 '{current_status}' 变更为 '{status}' (时间: {current_time})")
            else:
                # 状态未变化，只更新状态字段（不更新时间）
                c.execute('UPDATE papers SET status = ? WHERE id = ?', (status, paper_id))

            conn.commit()
            
            # 如果需要返回统计变化
            if return_stats and result['status_changed']:
                new_stats = self.get_feed_stats(feed_id)
                result['data'] = {
                    'paper': {
                        'id': paper_id,
                        'status': status,
                        'old_status': current_status
                    },
                    'stats_delta': {
                        'feed_id': feed_id,
                        'old_stats': old_stats['stats'] if old_stats else None,
                        'new_stats': new_stats['stats'] if new_stats else None
                    }
                }
            
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def translate_abstract(self, paper_id: int) -> Dict:
        """翻译论文摘要"""
        # 导入翻译器
        try:
            from services.deepseek_analyzer import DeepSeekAnalyzer
            analyzer = DeepSeekAnalyzer()
        except Exception:
            return {'success': False, 'error': '翻译功能未启用'}

        conn = self.get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
        paper = c.fetchone()

        if not paper:
            conn.close()
            return {'success': False, 'error': '论文不存在'}

        if paper['abstract_cn']:
            conn.close()
            return {'success': True, 'translation': paper['abstract_cn'], 'cached': True}

        if not paper['abstract']:
            conn.close()
            return {'success': False, 'error': '该论文没有摘要'}

        try:
            translation = analyzer.translate_text(paper['abstract'])
            c.execute('UPDATE papers SET abstract_cn = ? WHERE id = ?',
                      (translation, paper_id))
            conn.commit()
            conn.close()
            return {'success': True, 'translation': translation, 'cached': False}

        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}

    def get_paper_navigation(self, paper_id: int, feed_id: int) -> Optional[Dict]:
        """获取论文导航信息"""
        conn = self.get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
        current = c.fetchone()
        if not current:
            conn.close()
            return None

        c.execute('SELECT id FROM papers WHERE feed_id = ? ORDER BY published_date DESC', (feed_id,))
        paper_ids = [row[0] for row in c.fetchall()]
        conn.close()

        try:
            current_index = paper_ids.index(paper_id)
            prev_id = paper_ids[current_index - 1] if current_index > 0 else None
            next_id = paper_ids[current_index + 1] if current_index < len(paper_ids) - 1 else None

            return {
                'prev_id': prev_id,
                'next_id': next_id,
                'current_index': current_index + 1,
                'total': len(paper_ids)
            }
        except ValueError:
            return None

    def get_status_change_history(self, paper_id: int) -> Dict:
        """获取论文状态变化历史"""
        conn = self.get_db()
        c = conn.cursor()

        c.execute('''SELECT status, status_changed_at, created_at
                     FROM papers
                     WHERE id = ?''', (paper_id,))

        result = c.fetchone()
        conn.close()

        if result:
            return {
                'current_status': result['status'],
                'status_changed_at': result['status_changed_at'],
                'created_at': result['created_at']
            }
        return None

    def get_feed_stats(self, feed_id: int) -> Optional[Dict]:
        """获取单个feed的完整统计"""
        conn = self.get_db()
        c = conn.cursor()
        
        # 检查feed是否存在
        c.execute('SELECT name FROM feeds WHERE id = ?', (feed_id,))
        feed = c.fetchone()
        if not feed:
            conn.close()
            return None
        
        # 获取状态统计
        c.execute('''SELECT status, COUNT(*) as count 
                     FROM papers WHERE feed_id = ? 
                     GROUP BY status''', (feed_id,))
        status_rows = c.fetchall()
        
        stats = {
            'total': 0,
            'read': 0,
            'unread': 0,
            'reading': 0
        }
        
        for row in status_rows:
            stats['total'] += row['count']
            stats[row['status']] = row['count']
        
        # 获取今日新增数量
        from datetime import date
        today = date.today().isoformat()
        c.execute('''SELECT COUNT(*) FROM papers 
                     WHERE feed_id = ? AND DATE(created_at) = ?''', (feed_id, today))
        today_added = c.fetchone()[0]
        stats['today_added'] = today_added
        
        conn.close()
        return {
            'feed_id': feed_id,
            'feed_name': feed['name'],
            'stats': stats
        }
    
    def get_feeds_batch_stats(self, feed_ids: List[int]) -> Dict:
        """批量获取多个feed的统计"""
        conn = self.get_db()
        c = conn.cursor()
        
        if not feed_ids:
            conn.close()
            return {'stats': {}}
        
        # 构建IN查询
        placeholders = ','.join('?' * len(feed_ids))
        query = f'''SELECT feed_id, status, COUNT(*) as count 
                    FROM papers 
                    WHERE feed_id IN ({placeholders}) 
                    GROUP BY feed_id, status'''
        
        c.execute(query, feed_ids)
        rows = c.fetchall()
        
        # 组织数据
        stats = {}
        for feed_id in feed_ids:
            stats[str(feed_id)] = {
                'total': 0,
                'read': 0,
                'unread': 0,
                'reading': 0
            }
        
        for row in rows:
            feed_id = str(row['feed_id'])
            if feed_id in stats:
                stats[feed_id]['total'] += row['count']
                stats[feed_id][row['status']] = row['count']
        
        conn.close()
        return {'stats': stats}

    def get_papers_batch(self, paper_ids: List[int], expand: List[str] = None) -> List[Dict]:
        """批量获取论文信息"""
        if not paper_ids:
            return []
        
        conn = self.get_db()
        c = conn.cursor()
        
        # 构建IN查询
        placeholders = ','.join('?' * len(paper_ids))
        c.execute(f'SELECT * FROM papers WHERE id IN ({placeholders})', paper_ids)
        papers = [dict(row) for row in c.fetchall()]
        
        expand = expand or []
        
        # 如果需要扩展信息，为每个论文添加
        if expand:
            for paper in papers:
                paper_id = paper['id']
                
                # 稍后阅读信息
                if 'read_later' in expand or 'full' in expand:
                    c.execute('SELECT * FROM read_later WHERE paper_id = ?', (paper_id,))
                    read_later = c.fetchone()
                    paper['read_later'] = dict(read_later) if read_later else None
                
                # 分析任务信息
                if 'analysis' in expand or 'full' in expand:
                    c.execute('''SELECT * FROM tasks
                                 WHERE paper_id = ? AND task_type = 'deep_analysis'
                                 ORDER BY created_at DESC LIMIT 1''', (paper_id,))
                    task = c.fetchone()
                    paper['analysis_task'] = dict(task) if task else None
        
        conn.close()
        return papers

    def update_papers_batch_status(self, updates: List[Dict]) -> Dict:
        """批量更新论文状态
        updates格式: [{"paper_id": 1, "status": "read"}, ...]
        """
        if not updates:
            return {'success': True, 'updated': 0}
        
        conn = self.get_db()
        try:
            c = conn.cursor()
            updated_count = 0
            current_time = datetime.now().isoformat()
            
            for update in updates:
                paper_id = update.get('paper_id')
                status = update.get('status')
                
                if not paper_id or not status:
                    continue
                
                # 获取当前状态
                c.execute('SELECT status FROM papers WHERE id = ?', (paper_id,))
                current_row = c.fetchone()
                
                if not current_row:
                    continue
                
                current_status = current_row['status']
                
                # 只有状态真正发生变化时才更新状态变化时间
                if current_status != status:
                    c.execute('UPDATE papers SET status = ?, status_changed_at = ? WHERE id = ?',
                              (status, current_time, paper_id))
                    updated_count += 1
                    print(f"📝 批量更新: 论文 {paper_id} 状态从 '{current_status}' 变更为 '{status}'")
            
            conn.commit()
            return {'success': True, 'updated': updated_count}
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_papers_by_status_change_time(self, start_time: str = None, end_time: str = None, page: int = 1, per_page: int = 20) -> Dict:
        """根据状态变化时间获取论文列表（带分页）"""
        conn = self.get_db()
        c = conn.cursor()

        # 构建基础查询
        base_query = 'FROM papers WHERE 1=1'
        params = []

        if start_time:
            base_query += ' AND status_changed_at >= ?'
            params.append(start_time)

        if end_time:
            base_query += ' AND status_changed_at <= ?'
            params.append(end_time)

        # 获取总数
        count_query = f'SELECT COUNT(*) {base_query}'
        c.execute(count_query, params)
        total = c.fetchone()[0]

        # 计算分页参数
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page

        # 获取分页数据
        data_query = f'SELECT * {base_query} ORDER BY status_changed_at DESC LIMIT ? OFFSET ?'
        c.execute(data_query, params + [per_page, offset])
        papers = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        return {
            'papers': papers,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        }
