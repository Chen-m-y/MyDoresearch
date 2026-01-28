"""
IEEE适配器
基于IEEE Xplore API/爬虫获取期刊论文数据
支持异步并行抓取完整摘要
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base import BaseAdapter, PaperData
from utils.exceptions import FetchError, ValidationError
from utils.progress_monitor import create_progress_tracker

# 尝试导入异步模块，如果失败则提供回退方案
try:
    import asyncio
    from utils.async_abstract_fetcher import create_async_service
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    print("Warning: Async modules not available, falling back to basic abstract extraction")


class IEEEAdapter(BaseAdapter):
    """IEEE Xplore数据源适配器"""
    
    @property
    def name(self) -> str:
        return "ieee"
    
    @property
    def display_name(self) -> str:
        return "IEEE Xplore"
    
    @property
    def description(self) -> str:
        return "IEEE期刊和会议论文"
    
    @property
    def required_params(self) -> List[str]:
        return ["punumber"]
    
    @property
    def optional_params(self) -> List[str]:
        return ["limit", "early_access", "fetch_full_abstract"]
    
    def _validate_specific_params(self, params: Dict[str, Any]) -> None:
        """IEEE特定的参数验证"""
        punumber = params.get('punumber')
        if not isinstance(punumber, (str, int)):
            raise ValidationError("punumber必须是字符串或整数")
        
        limit = params.get('limit', 50)
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            raise ValidationError("limit必须是1-100之间的整数")
    
    def fetch_papers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取IEEE论文数据
        
        Args:
            params: 包含punumber和可选参数的字典
                - punumber: 期刊发布号码
                - limit: 返回结果数量限制 (默认50, 最大100)
                - early_access: 是否获取早期访问文章 (默认True)
                - fetch_full_abstract: 是否抓取完整摘要 (默认True)
        """
        punumber = str(params['punumber'])
        limit = params.get('limit', 50)
        early_access = params.get('early_access', True)
        fetch_full_abstract = params.get('fetch_full_abstract', True)  # 默认抓取完整摘要
        
        # 创建进度追踪器
        with create_progress_tracker(f"ieee-{punumber}", limit, f"抓取IEEE论文 {punumber}") as tracker:
            try:
                tracker.update(operation="获取期刊元数据...")
                
                # 1. 获取期刊元数据
                metadata = self._fetch_metadata(punumber)
                display_title = metadata.get('displayTitle', f'IEEE Publication {punumber}')
                
                tracker.update(operation="分析期刊issue...")
                
                # 2. 确定使用哪个issue
                current_issue = metadata.get('currentIssue', {})
                preprint_issue = metadata.get('preprintIssue', {})
                
                # 根据early_access参数选择issue
                target_issue = preprint_issue if early_access and preprint_issue else current_issue
                
                if not target_issue:
                    raise FetchError(
                        f"无法找到期刊 {punumber} 的有效issue",
                        error_code='NO_VALID_ISSUE'
                    )
                
                issue_number = target_issue.get('issueNumber')
                volume = target_issue.get('volume')
                
                if not issue_number:
                    raise FetchError(
                        f"期刊 {punumber} 的issue信息不完整",
                        error_code='INCOMPLETE_ISSUE_INFO'
                    )
                
                tracker.update(operation="获取论文目录数据...")
                
                # 3. 获取TOC数据
                toc_data = self._fetch_toc_data(punumber, issue_number, limit)
                print(toc_data)
                records = toc_data.get('records', [])
                
                # 更新总数
                actual_total = len(records)
                tracker.update(operation=f"处理 {actual_total} 篇论文...")
                
                # 4. 转换为标准格式
                papers = []
                for i, record in enumerate(records):
                    try:
                        paper = self._map_to_paper_data(record, volume, display_title)
                        papers.append(paper)
                        tracker.increment(success=True, operation=f"处理论文 {i+1}/{actual_total}")
                    except Exception as e:
                        # 记录但不中断处理
                        print(f"Warning: Failed to process paper record: {e}")
                        tracker.increment(success=False, operation=f"处理论文失败 {i+1}/{actual_total}")
                        continue
                
                # 5. 并行抓取完整摘要（如果启用且可用）
                if fetch_full_abstract and papers:
                    if ASYNC_AVAILABLE:
                        tracker.update(operation=f"并行抓取 {len(papers)} 篇论文的完整摘要...")
                        print(f"🔍 Starting parallel abstract fetching for {len(papers)} papers...")
                        try:
                            # 转换为适合异步处理的格式
                            paper_dicts = [paper.to_dict() for paper in papers]
                            
                            # 创建异步服务并执行并行抓取
                            from config import Config
                            async_service = create_async_service(
                                concurrent_limit=Config.MAX_CONCURRENT_REQUESTS,
                                request_delay=Config.ABSTRACT_REQUEST_DELAY
                            )
                            
                            # 在新的事件循环中运行异步任务
                            enhanced_papers = asyncio.run(async_service.fetch_abstracts_parallel(paper_dicts))
                            
                            # 更新论文对象
                            for i, enhanced_dict in enumerate(enhanced_papers):
                                if i < len(papers):
                                    papers[i].abstract = enhanced_dict.get('abstract', papers[i].abstract)
                            
                            print(f"✅ Parallel abstract fetching completed!")
                            tracker.update(operation="完整摘要抓取完成")
                            
                        except Exception as e:
                            print(f"⚠️  Parallel abstract fetching failed, using original abstracts: {e}")
                            tracker.update(operation="摘要抓取失败，使用基础摘要")
                    else:
                        print(f"ℹ️  Async not available, using basic abstracts (install aiohttp for parallel fetching)")
                        tracker.update(operation="使用基础摘要（未安装并行抓取依赖）")
                
                
                tracker.update(operation="排序和整理结果...")
                
                # 6. 按发表日期倒序排序（最新的在前面）
                papers.sort(key=lambda x: x.published_date, reverse=True)
                
                # 7. 应用limit限制
                papers = papers[:limit]
                
                # 转换为字典格式
                paper_dicts = [paper.to_dict() for paper in papers]
                
                # 8. 构建响应
                total_count = toc_data.get('totalRecords', len(paper_dicts))
                has_more = len(paper_dicts) >= limit and total_count > limit
                
                result = {
                    'papers': paper_dicts,
                    'total_count': total_count,
                    'has_more': has_more,
                    'next_cursor': None,  # IEEE API通常不支持分页游标
                    'rate_limit_remaining': None,  # IEEE通常没有明确的限流信息
                    'cache_hit': False
                }
                
                # 设置结果到进度追踪器
                tracker.set_results({
                    'papers_count': len(paper_dicts),
                    'total_available': total_count,
                    'enhanced_abstracts': fetch_full_abstract and ASYNC_AVAILABLE
                })
                
                return result
                
            except FetchError:
                raise
            except Exception as e:
                raise FetchError(
                    f"IEEE数据抓取失败: {str(e)}",
                    error_code='IEEE_FETCH_ERROR'
                )
    
    def _make_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        IEEE特定的HTTP请求方法，包含必要的请求头
        """
        import requests
        from utils.exceptions import FetchError, RateLimitError
        import time
        
        # 设置IEEE特定的请求头
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://ieeexplore.ieee.org/',
            'Origin': 'https://ieeexplore.ieee.org'
        })
        kwargs['headers'] = headers
        
        # 设置默认超时
        kwargs.setdefault('timeout', self.timeout)
        
        # 创建会话以保持cookie
        session = requests.Session()
        
        # 重试机制
        for attempt in range(self.max_retries + 1):
            try:
                if 'json' in kwargs:
                    # POST请求
                    response = session.post(url, **kwargs)
                else:
                    # GET请求
                    response = session.get(url, **kwargs)
                
                # 检查HTTP状态码
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError(
                        "API调用频率限制",
                        details={'retry_after': retry_after}
                    )
                
                if response.status_code == 418:
                    # 特殊处理418错误，增加延迟后重试
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt + 1)  # 更长的延迟
                        continue
                    else:
                        raise FetchError(
                            "IEEE服务器拒绝请求，可能触发反爬虫机制",
                            error_code='IEEE_BLOCKED',
                            details={'status_code': response.status_code}
                        )
                
                if response.status_code >= 400:
                    raise FetchError(
                        f"HTTP请求失败: {response.status_code}",
                        error_code='HTTP_ERROR',
                        details={'status_code': response.status_code, 'response': response.text[:500]}
                    )
                
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries:
                    raise FetchError(
                        "请求超时",
                        error_code='REQUEST_TIMEOUT'
                    )
                time.sleep(2 ** attempt)  # 指数退避
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise FetchError(
                        f"网络请求失败: {str(e)}",
                        error_code='NETWORK_ERROR'
                    )
                time.sleep(2 ** attempt)
        
        session.close()
    
    def _fetch_metadata(self, punumber: str) -> Dict[str, Any]:
        """获取期刊元数据"""
        url = f"{self.base_url}/rest/publication/home/metadata?pubid={punumber}"
        
        try:
            response = self._make_request(url)
            return response
        except Exception as e:
            raise FetchError(
                f"获取期刊元数据失败: {str(e)}",
                error_code='METADATA_FETCH_ERROR'
            )
    
    def _fetch_toc_data(self, punumber: str, issue_number: str, limit: int = 50) -> Dict[str, Any]:
        """获取期刊目录数据"""
        url = f"{self.base_url}/rest/search/pub/{punumber}/issue/{issue_number}/toc"
        
        payload = {
            'punumber': punumber,
            'isnumber': issue_number,
            'sortType': "vol-only-newest",
            'rowsPerPage': str(min(limit, 100))  # 限制最大100
        }
        
        try:
            response = self._make_request(url, json=payload)
            return response
        except Exception as e:
            raise FetchError(
                f"获取TOC数据失败: {str(e)}",
                error_code='TOC_FETCH_ERROR'
            )
    
    def _map_to_paper_data(self, record: Dict[str, Any], volume: str, journal_name: str) -> PaperData:
        """将IEEE原始数据映射为标准格式"""
        
        # 基本字段
        title = record.get('articleTitle', '').strip()
        abstract = record.get('abstract', '').strip()
        
        # 作者信息
        authors = []
        if 'authors' in record and isinstance(record['authors'], list):
            authors = [
                author.get('preferredName', author.get('normalizedName', ''))
                for author in record['authors']
                if author.get('preferredName') or author.get('normalizedName')
            ]
        
        # URL和DOI
        url = record.get('htmlLink', '')
        if url and not url.startswith('http'):
            url = self.base_url + url if url.startswith('/') else f"{self.base_url}/{url}"
        
        doi = record.get('doi', '')
        
        # PDF URL - 尝试从多个可能的字段获取
        pdf_url = None
        if 'pdfLink' in record:
            pdf_url = record['pdfLink']
        elif doi:
            # 基于DOI构造PDF URL
            article_number = record.get('articleNumber', '')
            if article_number:
                pdf_url = f"{self.base_url}/stamp/stamp.jsp?tp=&arnumber={article_number}"
        
        # 发布日期
        published_date = self._extract_publication_date(record)
        
        # 关键词
        keywords = self._extract_keywords(record)
        
        # 引用数
        citations = record.get('citationCount', 0)
        if isinstance(citations, str) and citations.isdigit():
            citations = int(citations)
        elif not isinstance(citations, int):
            citations = 0
        
        # IEEE特定字段
        source_specific = {
            'ieee_number': record.get('articleNumber', ''),
            'volume': volume,
            'issue': record.get('issue', ''),
            'pages': self._format_pages(record.get('startPage'), record.get('endPage')),
            'publication_number': record.get('punumber', ''),
            'access_type': record.get('accessType', ''),
            'content_type': record.get('contentType', '')
        }
        
        # 元数据
        metadata = {
            'publisher': 'IEEE',
            'conference': record.get('publicationTitle'),
            'isbn': record.get('isbn'),
            'issn': record.get('issn'),
            'publication_year': record.get('publicationYear'),
            'is_open_access': record.get('isOpenAccess', False),
            'ieee_terms': record.get('controlledTerms', [])
        }
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal_name,
            published_date=published_date,
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            keywords=keywords,
            citations=citations,
            source_specific=source_specific,
            metadata=metadata
        )
    
    def _extract_publication_date(self, record: Dict[str, Any]) -> str:
        """提取发布日期"""
        # 优先从 rightsLink 中提取日期
        rights_link = record.get('rightsLink', '')
        if rights_link and 'publicationDate=' in rights_link:
            import urllib.parse
            try:
                # 解析URL参数
                parsed_url = urllib.parse.urlparse(rights_link)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                pub_date = query_params.get('publicationDate', [''])[0]
                
                if pub_date:
                    # 解析日期格式如: "31+Jul+2025" 
                    pub_date = pub_date.replace('+', ' ')
                    parsed_date = self._parse_date_string(pub_date)
                    if parsed_date:
                        return parsed_date
            except Exception:
                pass  # 如果解析失败，继续尝试其他方法
        
        # 尝试多个日期字段
        date_fields = ['publicationDate', 'insertDate', 'publishedDate', 'onlineDate', 'coverDate']
        
        for field in date_fields:
            if field in record and record[field]:
                date_str = record[field]
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date
        
        # 如果没有找到具体日期，尝试使用年份
        year = record.get('publicationYear')
        if year:
            try:
                year_int = int(year)
                return f"{year_int}-01-01"
            except (ValueError, TypeError):
                pass
        
        # 默认返回当前日期
        return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """解析特殊格式的日期字符串，如 '31 Jul 2025'"""
        if not date_str:
            return None
            
        try:
            from datetime import datetime
            
            # 清理字符串
            date_str = date_str.strip()
            
            # 尝试解析 "DD MMM YYYY" 格式，如 "31 Jul 2025"
            try:
                date_obj = datetime.strptime(date_str, '%d %b %Y')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
            
            # 尝试解析 "DD Month YYYY" 格式，如 "31 July 2025"
            try:
                date_obj = datetime.strptime(date_str, '%d %B %Y')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
                
            # 尝试解析 "MMM DD YYYY" 格式，如 "Jul 31 2025"
            try:
                date_obj = datetime.strptime(date_str, '%b %d %Y')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
                
            # 尝试解析 "Month DD YYYY" 格式，如 "July 31 2025"
            try:
                date_obj = datetime.strptime(date_str, '%B %d %Y')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
                
        except Exception:
            pass
            
        # 如果特殊格式都失败了，尝试通用解析
        return self._parse_date(date_str)
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析各种格式的日期字符串"""
        if not date_str:
            return None
        
        # 常见的日期格式
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{4})/(\d{2})/(\d{2})',  # YYYY/MM/DD
            r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{4})',  # 仅年份
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, str(date_str))
            if match:
                groups = match.groups()
                if len(groups) == 1:  # 仅年份
                    return f"{groups[0]}-01-01"
                elif len(groups) == 3:
                    # 判断是否为YYYY-MM-DD格式
                    if len(groups[0]) == 4:
                        year, month, day = groups
                    else:  # DD-MM-YYYY格式
                        day, month, year = groups
                    
                    try:
                        # 验证日期有效性
                        datetime(int(year), int(month), int(day))
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except ValueError:
                        continue
        
        return None
    
    def _extract_keywords(self, record: Dict[str, Any]) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # IEEE特定的术语字段
        if 'indexTerms' in record:
            terms = record['indexTerms']
            if isinstance(terms, dict):
                for category, terms_list in terms.items():
                    if isinstance(terms_list, list):
                        keywords.extend([term.get('term', '') for term in terms_list if isinstance(term, dict)])
                    elif isinstance(terms_list, str):
                        keywords.append(terms_list)
        
        # 受控词汇
        if 'controlledTerms' in record and isinstance(record['controlledTerms'], list):
            keywords.extend(record['controlledTerms'])
        
        # 作者关键词
        if 'authorTerms' in record and isinstance(record['authorTerms'], list):
            keywords.extend(record['authorTerms'])
        
        # 清理并去重
        keywords = [kw.strip() for kw in keywords if kw and isinstance(kw, str) and kw.strip()]
        return list(dict.fromkeys(keywords))  # 保持顺序的去重
    
    def _format_pages(self, start_page: Any, end_page: Any) -> str:
        """格式化页码范围"""
        if start_page and end_page:
            return f"{start_page}-{end_page}"
        elif start_page:
            return str(start_page)
        elif end_page:
            return str(end_page)
        else:
            return ""