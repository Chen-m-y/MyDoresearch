"""
优化版论文管理服务 - 使用连接池和批量操作
解决N+1查询问题和数据库连接重复创建问题
"""
import hashlib
import re
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from services.database_service import get_database_service


class OptimizedPaperManager:
    """优化版论文管理服务"""
    
    def __init__(self):
        self.db_service = get_database_service()
    
    def add_feed(self, name: str, url: str, journal: str = "") -> Dict:
        """添加论文源"""
        try:
            feed_id = self.db_service.execute_insert(
                'INSERT INTO feeds (name, url, journal) VALUES (?, ?, ?)',
                (name, url, journal)
            )
            return {'success': True, 'feed_id': feed_id}
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                return {'success': False, 'error': 'API地址已存在'}
            return {'success': False, 'error': str(e)}
    
    def get_all_feeds(self) -> List[Dict]:
        """获取所有论文源（使用缓存）"""
        cache_key = "all_feeds"
        return self.db_service.get_cached_query(
            cache_key,
            'SELECT * FROM feeds WHERE active = 1 ORDER BY name',
            cache_duration=300
        )
    
    def update_feed(self, feed_id: int) -> Dict:
        """更新指定论文源的文章（批量优化）"""
        # 获取论文源信息
        feed = self.db_service.execute_query(
            'SELECT * FROM feeds WHERE id = ?', 
            (feed_id,), 
            fetch_one=True
        )
        
        if not feed:
            return {'success': False, 'error': '论文源不存在'}
        
        try:
            response = requests.get(feed['url'], timeout=30)
            response.raise_for_status()
            papers_data = response.json()
            
            if not isinstance(papers_data, list):
                return {'success': False, 'error': 'API响应格式错误，应该是数组格式'}
            
            # 批量处理论文数据
            new_papers = self._batch_insert_papers(feed_id, feed, papers_data)
            
            # 更新论文源最后更新时间
            self.db_service.execute_update(
                'UPDATE feeds SET last_updated = CURRENT_TIMESTAMP WHERE id = ?',
                (feed_id,)
            )
            
            # 清理相关缓存
            self.db_service.clear_cache("all_feeds")
            
            return {'success': True, 'new_papers': new_papers}
            
        except requests.RequestException as e:
            return {'success': False, 'error': f'网络请求失败: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON解析失败: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'更新失败: {str(e)}'}
    
    def _batch_insert_papers(self, feed_id: int, feed: Dict, papers_data: List[Dict]) -> int:
        """批量插入论文数据"""
        if not papers_data:
            return 0
        
        # 准备批量插入的数据
        insert_params = []
        paper_hashes = []
        
        for paper_data in papers_data:
            if not paper_data.get('title'):
                continue
            
            # 计算哈希值
            paper_hash = hashlib.md5(
                (paper_data.get('title', '') +
                 paper_data.get('url', '') +
                 str(paper_data.get('external_id', ''))).encode()
            ).hexdigest()
            
            paper_hashes.append(paper_hash)
            
            # 准备插入参数
            ieee_number = self._extract_ieee_number(paper_data)
            title = paper_data.get('title', '').strip()
            abstract = paper_data.get('abstract', '').strip()
            authors = paper_data.get('author', paper_data.get('authors', ''))
            journal = paper_data.get('journal') or feed['journal']
            url = paper_data.get('url', '')
            pdf_url = paper_data.get('pdf_url', '')
            doi = paper_data.get('doi', '')
            external_id = paper_data.get('id', '')
            published_date = self._parse_date_from_json(paper_data)
            status = paper_data.get('status', 'unread')
            current_time = datetime.now().isoformat()
            
            insert_params.append((
                feed_id, title, abstract, authors, journal, published_date,
                url, pdf_url, doi, status, current_time, paper_hash,
                external_id, ieee_number
            ))
        
        if not insert_params:
            return 0
        
        # 批量检查已存在的哈希
        if paper_hashes:
            placeholders = ','.join(['?' for _ in paper_hashes])
            existing_hashes = self.db_service.execute_query(
                f'SELECT hash FROM papers WHERE hash IN ({placeholders})',
                tuple(paper_hashes),
                fetch_all=True
            )
            existing_hash_set = {row['hash'] for row in existing_hashes}
            
            # 过滤掉已存在的论文
            filtered_params = []
            for params in insert_params:
                paper_hash = params[11]  # hash字段的位置
                if paper_hash not in existing_hash_set:
                    filtered_params.append(params)
            
            if not filtered_params:
                return 0
            
            # 批量插入新论文
            insert_query = '''
                INSERT INTO papers
                (feed_id, title, abstract, authors, journal, published_date,
                 url, pdf_url, doi, status, status_changed_at, hash, external_id, ieee_article_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            self.db_service.execute_batch(insert_query, filtered_params)
            return len(filtered_params)
        
        return 0
    
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
        """从JSON数据中解析发布日期"""
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
    
    def get_papers_by_feed(self, feed_id: int, status: str = None) -> List[Dict]:
        """获取指定订阅的论文列表（优化查询）"""
        cache_key = f"papers_feed_{feed_id}_{status or 'all'}"
        
        if status:
            query = '''
                SELECT * FROM papers 
                WHERE feed_id = ? AND status = ? 
                ORDER BY published_date DESC
            '''
            params = (feed_id, status)
        else:
            query = '''
                SELECT * FROM papers 
                WHERE feed_id = ? 
                ORDER BY published_date DESC
            '''
            params = (feed_id,)
        
        return self.db_service.get_cached_query(cache_key, query, params, cache_duration=60)
    
    def get_paper(self, paper_id: int) -> Optional[Dict]:
        """获取单篇论文详情（包含分析结果）"""
        # 获取论文基本信息
        paper = self.db_service.execute_query(
            'SELECT * FROM papers WHERE id = ?', 
            (paper_id,), 
            fetch_one=True
        )
        
        if not paper:
            return None
        
        # 获取相关任务信息（使用JOIN优化）
        task = self.db_service.execute_query(
            '''SELECT *
               FROM tasks
               WHERE paper_id = ? AND task_type = 'deep_analysis'
               ORDER BY created_at DESC LIMIT 1''',
            (paper_id,),
            fetch_one=True
        )
        
        if task:
            paper['analysis_task'] = task
            
            # 获取任务步骤
            steps = self.db_service.execute_query(
                'SELECT * FROM task_steps WHERE task_id = ? ORDER BY id',
                (task['id'],),
                fetch_all=True
            )
            paper['analysis_task']['steps'] = steps
        
        return paper
    
    def update_paper_status(self, paper_id: int, status: str) -> Dict:
        """更新论文状态并记录变化时间"""
        # 获取当前状态
        current = self.db_service.execute_query(
            'SELECT status FROM papers WHERE id = ?', 
            (paper_id,), 
            fetch_one=True
        )
        
        if not current:
            return {'success': False, 'error': '论文不存在'}
        
        current_status = current['status']
        status_changed = current_status != status
        
        # 根据状态是否变化决定更新策略
        if status_changed:
            current_time = datetime.now().isoformat()
            affected_rows = self.db_service.execute_update(
                'UPDATE papers SET status = ?, status_changed_at = ? WHERE id = ?',
                (status, current_time, paper_id)
            )
            print(f"📝 论文 {paper_id} 状态从 '{current_status}' 变更为 '{status}' (时间: {current_time})")
        else:
            affected_rows = self.db_service.execute_update(
                'UPDATE papers SET status = ? WHERE id = ?',
                (status, paper_id)
            )
        
        # 清理相关缓存
        self._clear_paper_caches(paper_id)
        
        return {
            'success': affected_rows > 0, 
            'status_changed': status_changed
        }
    
    def translate_abstract(self, paper_id: int) -> Dict:
        """翻译论文摘要"""
        # 获取论文信息
        paper = self.db_service.execute_query(
            'SELECT abstract, abstract_cn FROM papers WHERE id = ?',
            (paper_id,),
            fetch_one=True
        )
        
        if not paper:
            return {'success': False, 'error': '论文不存在'}
        
        if paper['abstract_cn']:
            return {'success': True, 'translation': paper['abstract_cn'], 'cached': True}
        
        if not paper['abstract']:
            return {'success': False, 'error': '该论文没有摘要'}
        
        try:
            # 导入翻译器
            from services.deepseek_analyzer import DeepSeekAnalyzer
            analyzer = DeepSeekAnalyzer()
            
            translation = analyzer.translate_text(paper['abstract'])
            
            # 更新翻译结果
            self.db_service.execute_update(
                'UPDATE papers SET abstract_cn = ? WHERE id = ?',
                (translation, paper_id)
            )
            
            return {'success': True, 'translation': translation, 'cached': False}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_paper_navigation(self, paper_id: int, feed_id: int) -> Optional[Dict]:
        """获取论文导航信息（优化版）"""
        # 使用更高效的查询获取导航信息
        nav_query = '''
            WITH ordered_papers AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY published_date DESC) as row_num
                FROM papers 
                WHERE feed_id = ?
            ),
            current_paper AS (
                SELECT row_num FROM ordered_papers WHERE id = ?
            )
            SELECT 
                (SELECT id FROM ordered_papers WHERE row_num = cp.row_num - 1) as prev_id,
                (SELECT id FROM ordered_papers WHERE row_num = cp.row_num + 1) as next_id,
                cp.row_num as current_index,
                (SELECT COUNT(*) FROM papers WHERE feed_id = ?) as total
            FROM current_paper cp
        '''
        
        result = self.db_service.execute_query(
            nav_query, 
            (feed_id, paper_id, feed_id), 
            fetch_one=True
        )
        
        if result:
            return {
                'prev_id': result['prev_id'],
                'next_id': result['next_id'],
                'current_index': result['current_index'],
                'total': result['total']
            }
        
        return None
    
    def get_status_change_history(self, paper_id: int) -> Optional[Dict]:
        """获取论文状态变化历史"""
        result = self.db_service.execute_query(
            '''SELECT status, status_changed_at, created_at
               FROM papers WHERE id = ?''',
            (paper_id,),
            fetch_one=True
        )
        
        if result:
            return {
                'current_status': result['status'],
                'status_changed_at': result['status_changed_at'],
                'created_at': result['created_at']
            }
        
        return None
    
    def get_papers_by_status_change_time(self, start_time: str = None, end_time: str = None) -> List[Dict]:
        """根据状态变化时间获取论文列表（优化查询）"""
        conditions = ['1=1']
        params = []
        
        if start_time:
            conditions.append('status_changed_at >= ?')
            params.append(start_time)
        
        if end_time:
            conditions.append('status_changed_at <= ?')
            params.append(end_time)
        
        query = f'''
            SELECT * FROM papers 
            WHERE {' AND '.join(conditions)}
            ORDER BY status_changed_at DESC
        '''
        
        return self.db_service.execute_query(query, tuple(params), fetch_all=True)
    
    def _clear_paper_caches(self, paper_id: int):
        """清理与特定论文相关的缓存"""
        # 清理论文列表缓存
        self.db_service.clear_cache()  # 简化处理，清理所有缓存
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        return self.db_service.get_statistics()