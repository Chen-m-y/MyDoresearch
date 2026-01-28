"""
DBLP适配器
基于DBLP API获取计算机科学会议和期刊数据
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAdapter, PaperData
from utils.exceptions import FetchError, ValidationError


class DBLPAdapter(BaseAdapter):
    """DBLP数据库数据源适配器"""
    
    @property
    def name(self) -> str:
        return "dblp"
    
    @property
    def display_name(self) -> str:
        return "DBLP Database"
    
    @property
    def description(self) -> str:
        return "计算机科学会议和期刊"
    
    @property
    def required_params(self) -> List[str]:
        return ["dblp_id", "year"]
    
    @property
    def optional_params(self) -> List[str]:
        return ["include_workshops", "limit", "format"]
    
    def _validate_specific_params(self, params: Dict[str, Any]) -> None:
        """DBLP特定的参数验证"""
        dblp_id = params.get('dblp_id')
        if not isinstance(dblp_id, str) or not dblp_id.strip():
            raise ValidationError("dblp_id必须是非空字符串")
        
        year = params.get('year')
        if not isinstance(year, int) or year < 1950 or year > datetime.now().year + 1:
            raise ValidationError(f"year必须是1950到{datetime.now().year + 1}之间的整数")
        
        limit = params.get('limit', 100)
        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            raise ValidationError("limit必须是1-1000之间的整数")
        
        include_workshops = params.get('include_workshops', False)
        if not isinstance(include_workshops, bool):
            raise ValidationError("include_workshops必须是布尔值")
    
    def fetch_papers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取DBLP论文数据
        
        Args:
            params: 包含dblp_id和年份的字典
                - dblp_id: DBLP会议或期刊标识符 (例如: "icse", "tse", "pldi")
                - year: 年份
                - include_workshops: 是否包含workshop论文 (默认False)
                - limit: 返回结果数量限制 (默认100, 最大1000)
                - format: 返回格式 ("json"或"xml", 默认"json")
        """
        dblp_id = params['dblp_id'].strip().lower()
        year = params['year']
        include_workshops = params.get('include_workshops', False)
        limit = params.get('limit', 100)
        format_type = params.get('format', 'json')
        
        try:
            # 1. 构建查询URL和参数
            query = f"{dblp_id} {year}"
            
            # 2. 执行搜索
            search_results = self._search_publications(query, limit, format_type)
            
            # 3. 过滤结果
            filtered_results = self._filter_results(
                search_results, 
                dblp_id, 
                year, 
                include_workshops
            )
            
            # 4. 转换为标准格式
            papers = []
            hits = filtered_results.get('result', {}).get('hits', {})
            hit_list = hits.get('hit', [])
            
            # 确保hit_list是列表
            if isinstance(hit_list, dict):
                hit_list = [hit_list]
            elif not isinstance(hit_list, list):
                hit_list = []
            
            for hit in hit_list:
                try:
                    info = hit.get('info', {})
                    paper = self._map_to_paper_data(info, dblp_id)
                    papers.append(paper.to_dict())
                except Exception as e:
                    # 记录但不中断处理
                    print(f"Warning: Failed to process DBLP entry: {e}")
                    continue
            
            # 5. 构建响应
            total_hits = int(hits.get('@total', len(papers)))
            has_more = len(papers) >= limit and total_hits > limit
            
            return {
                'papers': papers,
                'total_count': total_hits,
                'has_more': has_more,
                'next_cursor': None,  # DBLP API支持分页，但这里简化处理
                'rate_limit_remaining': None,  # DBLP通常无API限制
                'cache_hit': False
            }
            
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(
                f"DBLP数据抓取失败: {str(e)}",
                error_code='DBLP_FETCH_ERROR'
            )
    
    def _search_publications(self, query: str, limit: int, format_type: str) -> Dict[str, Any]:
        """执行DBLP搜索"""
        url = f"{self.base_url}"
        
        params = {
            'q': query,
            'h': min(limit, 1000),  # DBLP API的最大限制
            'c': 0,  # 起始位置
            'f': format_type
        }
        
        try:
            response = self._make_request(url, params=params)
            return response
        except Exception as e:
            raise FetchError(
                f"DBLP搜索请求失败: {str(e)}",
                error_code='DBLP_SEARCH_ERROR'
            )
    
    def _filter_results(self, results: Dict[str, Any], dblp_id: str, year: int, include_workshops: bool) -> Dict[str, Any]:
        """过滤搜索结果"""
        filtered_results = {'result': {'hits': {'hit': [], '@total': 0}}}
        
        hits = results.get('result', {}).get('hits', {})
        hit_list = hits.get('hit', [])
        
        # 确保hit_list是列表
        if isinstance(hit_list, dict):
            hit_list = [hit_list]
        elif not isinstance(hit_list, list):
            return filtered_results
        
        filtered_hits = []
        
        for hit in hit_list:
            info = hit.get('info', {})
            
            # 检查年份
            pub_year = self._extract_year(info)
            if pub_year != year:
                continue
            
            # 检查是否为目标会议/期刊
            if not self._is_target_venue(info, dblp_id):
                continue
            
            # 检查是否包含workshop
            if not include_workshops and self._is_workshop(info):
                continue
            
            filtered_hits.append(hit)
        
        filtered_results['result']['hits']['hit'] = filtered_hits
        filtered_results['result']['hits']['@total'] = len(filtered_hits)
        
        return filtered_results
    
    def _is_target_venue(self, info: Dict[str, Any], target_id: str) -> bool:
        """检查是否为目标会议或期刊"""
        venue = info.get('venue', '').lower()
        key = info.get('key', '').lower()
        
        # 检查venue字段
        if target_id in venue:
            return True
        
        # 检查key字段中的venue信息
        if f"/{target_id}/" in key or key.startswith(f"{target_id}/"):
            return True
        
        return False
    
    def _is_workshop(self, info: Dict[str, Any]) -> bool:
        """检查是否为workshop论文"""
        venue = info.get('venue', '').lower()
        title = info.get('title', '').lower()
        
        workshop_indicators = ['workshop', 'wksp', 'ws ', 'doctoral', 'student', 'poster']
        
        for indicator in workshop_indicators:
            if indicator in venue or indicator in title:
                return True
        
        return False
    
    def _extract_year(self, info: Dict[str, Any]) -> Optional[int]:
        """从info中提取年份"""
        year = info.get('year')
        if year:
            try:
                return int(year)
            except (ValueError, TypeError):
                pass
        
        # 从key中尝试提取年份
        key = info.get('key', '')
        year_match = re.search(r'/(\d{4})/', key)
        if year_match:
            try:
                return int(year_match.group(1))
            except ValueError:
                pass
        
        return None
    
    def _map_to_paper_data(self, info: Dict[str, Any], venue_id: str) -> PaperData:
        """将DBLP原始数据映射为标准格式"""
        
        # 基本字段
        title = info.get('title', '').strip()
        # DBLP通常不提供摘要
        abstract = ""
        
        # 作者信息
        authors = []
        authors_data = info.get('author', [])
        if isinstance(authors_data, str):
            authors = [authors_data]
        elif isinstance(authors_data, list):
            authors = [str(author) for author in authors_data]
        elif isinstance(authors_data, dict):
            # 单个作者的情况
            author_name = authors_data.get('text', str(authors_data))
            authors = [author_name]
        
        # 期刊/会议名称
        journal = info.get('venue', '').strip()
        if not journal:
            # 从key中提取venue信息
            key = info.get('key', '')
            venue_match = re.match(r'^[^/]+/([^/]+)/', key)
            if venue_match:
                journal = venue_match.group(1).upper()
        
        # URL
        url = info.get('url', '')
        if not url:
            # 构建DBLP URL
            key = info.get('key', '')
            if key:
                url = f"https://dblp.org/rec/{key}.html"
        
        # DOI
        doi = info.get('doi', '')
        
        # PDF URL - DBLP通常不直接提供PDF链接
        pdf_url = info.get('ee', '') if info.get('ee', '').endswith('.pdf') else None
        
        # 发布日期
        year = info.get('year')
        published_date = f"{year}-01-01" if year else datetime.now().strftime('%Y-%m-%d')
        
        # DBLP通常不提供关键词
        keywords = []
        
        # 引用数 - DBLP不提供引用数据
        citations = 0
        
        # DBLP特定字段
        source_specific = {
            'dblp_key': info.get('key', ''),
            'venue_id': venue_id,
            'type': info.get('type', ''),
            'pages': info.get('pages', ''),
            'volume': info.get('volume', ''),
            'number': info.get('number', ''),
            'ee': info.get('ee', ''),  # Electronic Edition链接
            'crossref': info.get('crossref', '')
        }
        
        # 元数据
        publication_type = self._determine_publication_type(info, venue_id)
        metadata = {
            'publisher': self._get_publisher_info(venue_id),
            'conference': journal if publication_type == 'conference' else None,
            'publication_type': publication_type,
            'dblp_venue': journal,
            'isbn': info.get('isbn', ''),
            'publication_year': year,
            'is_open_access': False  # DBLP无此信息
        }
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            published_date=published_date,
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            keywords=keywords,
            citations=citations,
            source_specific=source_specific,
            metadata=metadata
        )
    
    def _determine_publication_type(self, info: Dict[str, Any], venue_id: str) -> str:
        """确定出版物类型"""
        key = info.get('key', '').lower()
        venue = info.get('venue', '').lower()
        
        # 期刊类型指标
        journal_indicators = ['journal', 'trans', 'acm', 'ieee']
        
        # 会议类型指标
        conf_indicators = ['conf', 'proc', 'workshop', 'symposium', 'international']
        
        # 检查key中的类型信息
        if '/journals/' in key:
            return 'journal'
        elif '/conf/' in key:
            return 'conference'
        
        # 检查venue名称
        for indicator in journal_indicators:
            if indicator in venue:
                return 'journal'
        
        for indicator in conf_indicators:
            if indicator in venue:
                return 'conference'
        
        # 默认根据常见的venue_id判断
        known_journals = ['tse', 'tac', 'tosem', 'tpds', 'tc']
        known_conferences = ['icse', 'fse', 'ase', 'pldi', 'oopsla', 'sigcomm']
        
        if venue_id.lower() in known_journals:
            return 'journal'
        elif venue_id.lower() in known_conferences:
            return 'conference'
        
        return 'unknown'
    
    def _get_publisher_info(self, venue_id: str) -> str:
        """根据venue_id获取出版商信息"""
        venue_id = venue_id.lower()
        
        # IEEE出版物
        ieee_venues = ['tse', 'tc', 'tpds', 'tmc', 'tkde', 'icse', 'icsm']
        if venue_id in ieee_venues:
            return 'IEEE'
        
        # ACM出版物
        acm_venues = ['tosem', 'tacs', 'pldi', 'oopsla', 'fse', 'sigcomm']
        if venue_id in acm_venues:
            return 'ACM'
        
        # Springer出版物
        springer_venues = ['ase', 'fase', 'tacas']
        if venue_id in springer_venues:
            return 'Springer'
        
        return 'Unknown'