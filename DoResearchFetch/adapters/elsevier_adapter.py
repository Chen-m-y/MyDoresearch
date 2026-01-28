"""
Elsevier适配器
基于ScienceDirect API获取期刊论文数据
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseAdapter, PaperData
from utils.exceptions import FetchError, ValidationError


class ElsevierAdapter(BaseAdapter):
    """Elsevier ScienceDirect数据源适配器"""
    
    @property
    def name(self) -> str:
        return "elsevier"
    
    @property
    def display_name(self) -> str:
        return "ScienceDirect"
    
    @property
    def description(self) -> str:
        return "Elsevier期刊论文"
    
    @property
    def required_params(self) -> List[str]:
        return ["pnumber"]
    
    @property
    def optional_params(self) -> List[str]:
        return ["limit", "subject_areas", "start_date", "end_date"]
    
    def _validate_specific_params(self, params: Dict[str, Any]) -> None:
        """Elsevier特定的参数验证"""
        pnumber = params.get('pnumber')
        if not isinstance(pnumber, str) or not pnumber.strip():
            raise ValidationError("pnumber必须是非空字符串")
        
        # 验证ISSN格式 (可以是ISSN或期刊标识符)
        if not re.match(r'^\d{4}-\d{3}[\dX]$|^[A-Za-z0-9\-]+$', pnumber):
            raise ValidationError("pnumber格式无效，应为ISSN格式(例如: 0164-1212)或期刊标识符")
        
        limit = params.get('limit', 25)
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            raise ValidationError("limit必须是1-100之间的整数")
        
        # 验证主题领域
        subject_areas = params.get('subject_areas')
        if subject_areas and not isinstance(subject_areas, list):
            raise ValidationError("subject_areas必须是字符串数组")
    
    def fetch_papers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取Elsevier论文数据
        
        Args:
            params: 包含pnumber和可选参数的字典
                - pnumber: 期刊ISSN或标识符
                - limit: 返回结果数量限制 (默认25, 最大100)
                - subject_areas: 主题领域过滤 (可选)
                - start_date: 开始日期 YYYY-MM-DD (可选)
                - end_date: 结束日期 YYYY-MM-DD (可选)
        """
        pnumber = params['pnumber'].strip()
        limit = params.get('limit', 25)
        subject_areas = params.get('subject_areas', [])
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        try:
            # 1. 构建搜索查询
            query_parts = []
            
            # 添加期刊限制
            if self._is_issn_format(pnumber):
                query_parts.append(f'ISSN({pnumber})')
            else:
                # 假设是期刊名称或缩写
                query_parts.append(f'SRCTITLE("{pnumber}")')
            
            # 添加日期范围
            if start_date or end_date:
                date_range = self._build_date_range(start_date, end_date)
                if date_range:
                    query_parts.append(date_range)
            
            # 添加主题领域
            if subject_areas:
                area_query = ' OR '.join([f'SUBJAREA("{area}")' for area in subject_areas])
                query_parts.append(f'({area_query})')
            
            query = ' AND '.join(query_parts)
            
            # 2. 执行搜索
            search_results = self._search_articles(query, limit)
            
            # 3. 获取详细信息（如果需要）
            papers = []
            entries = search_results.get('search-results', {}).get('entry', [])
            
            for entry in entries:
                try:
                    paper = self._map_to_paper_data(entry)
                    papers.append(paper.to_dict())
                except Exception as e:
                    # 记录但不中断处理
                    print(f"Warning: Failed to process Elsevier article: {e}")
                    continue
            
            # 4. 构建响应
            total_results = int(search_results.get('search-results', {}).get('totalResults', len(papers)))
            has_more = len(papers) >= limit and total_results > limit
            
            return {
                'papers': papers,
                'total_count': total_results,
                'has_more': has_more,
                'next_cursor': None,  # Elsevier支持分页，但这里简化处理
                'rate_limit_remaining': self._get_rate_limit_info(),
                'cache_hit': False
            }
            
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(
                f"Elsevier数据抓取失败: {str(e)}",
                error_code='ELSEVIER_FETCH_ERROR'
            )
    
    def _is_issn_format(self, pnumber: str) -> bool:
        """检查是否为ISSN格式"""
        return bool(re.match(r'^\d{4}-\d{3}[\dX]$', pnumber))
    
    def _build_date_range(self, start_date: str, end_date: str) -> str:
        """构建日期范围查询"""
        if not start_date and not end_date:
            return ""
        
        if start_date and end_date:
            return f'PUBYEAR > {start_date[:4]} AND PUBYEAR < {end_date[:4]}'
        elif start_date:
            return f'PUBYEAR > {start_date[:4]}'
        else:
            return f'PUBYEAR < {end_date[:4]}'
    
    def _search_articles(self, query: str, limit: int) -> Dict[str, Any]:
        """执行文章搜索"""
        url = f"{self.base_url}/content/search/sciencedirect"
        
        params = {
            'query': query,
            'count': min(limit, 100),
            'start': 0,
            'field': 'dc:title,dc:creator,prism:publicationName,prism:coverDate,prism:doi,dc:description,prism:url,citedby-count,prism:issn'
        }
        
        headers = {}
        if self.api_key:
            headers['X-ELS-APIKey'] = self.api_key
        
        try:
            response = self._make_request(url, params=params, headers=headers)
            return response
        except Exception as e:
            raise FetchError(
                f"Elsevier搜索失败: {str(e)}",
                error_code='ELSEVIER_SEARCH_ERROR'
            )
    
    def _map_to_paper_data(self, entry: Dict[str, Any]) -> PaperData:
        """将Elsevier原始数据映射为标准格式"""
        
        # 基本字段
        title = entry.get('dc:title', '').strip()
        abstract = entry.get('dc:description', '').strip()
        
        # 作者信息
        authors = []
        authors_data = entry.get('dc:creator')
        if isinstance(authors_data, str):
            authors = [authors_data]
        elif isinstance(authors_data, list):
            authors = [str(author) for author in authors_data]
        
        # 期刊名称
        journal = entry.get('prism:publicationName', '').strip()
        
        # URL和DOI
        url = entry.get('prism:url', '')
        doi = entry.get('prism:doi', '')
        
        # PDF URL - Elsevier通常需要通过特定的API获取
        pdf_url = None
        if doi:
            pdf_url = f"https://www.sciencedirect.com/science/article/pii/{self._extract_pii_from_url(url)}"
        
        # 发布日期
        published_date = self._extract_publication_date(entry)
        
        # 关键词 - Elsevier API响应中通常不直接包含关键词
        keywords = []
        
        # 引用数
        citations = 0
        citedby_count = entry.get('citedby-count')
        if citedby_count and str(citedby_count).isdigit():
            citations = int(citedby_count)
        
        # Elsevier特定字段
        source_specific = {
            'scopus_id': entry.get('dc:identifier', '').replace('SCOPUS_ID:', ''),
            'eid': entry.get('eid', ''),
            'pii': self._extract_pii_from_url(url),
            'issn': entry.get('prism:issn', ''),
            'aggregation_type': entry.get('prism:aggregationType', ''),
            'subtype': entry.get('subtypeDescription', '')
        }
        
        # 元数据
        metadata = {
            'publisher': 'Elsevier',
            'platform': 'ScienceDirect',
            'issn': entry.get('prism:issn', ''),
            'publication_year': self._extract_year_from_date(published_date),
            'is_open_access': entry.get('openaccessFlag', False),
            'source_title': journal
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
    
    def _extract_pii_from_url(self, url: str) -> str:
        """从URL中提取PII"""
        if not url:
            return ""
        
        # 匹配ScienceDirect URL中的PII
        match = re.search(r'/pii/([A-Z0-9]+)', url)
        return match.group(1) if match else ""
    
    def _extract_publication_date(self, entry: Dict[str, Any]) -> str:
        """提取发布日期"""
        cover_date = entry.get('prism:coverDate')
        if cover_date:
            parsed_date = self._parse_date(cover_date)
            if parsed_date:
                return parsed_date
        
        # 默认返回当前日期
        return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        # Elsevier通常使用ISO格式
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{4})-(\d{2})',  # YYYY-MM
            r'(\d{4})',  # YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, str(date_str))
            if match:
                groups = match.groups()
                if len(groups) == 1:  # 仅年份
                    return f"{groups[0]}-01-01"
                elif len(groups) == 2:  # 年月
                    return f"{groups[0]}-{groups[1].zfill(2)}-01"
                elif len(groups) == 3:  # 年月日
                    return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
        
        return None
    
    def _extract_year_from_date(self, date_str: str) -> str:
        """从日期字符串中提取年份"""
        if not date_str:
            return ""
        
        year_match = re.search(r'(\d{4})', date_str)
        return year_match.group(1) if year_match else ""
    
    def _get_rate_limit_info(self) -> Optional[int]:
        """获取API限流信息 - Elsevier API通常有限流"""
        # 这里应该从响应头中获取实际的限流信息
        # 目前返回None，实际实现中可以从HTTP响应头中提取
        return None