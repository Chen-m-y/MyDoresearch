"""
异步并行摘要抓取服务
基于 asyncio + aiohttp 实现高效的IEEE摘要获取
"""

import asyncio
import aiohttp
import json
import re
import time
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FetchMetrics:
    """抓取性能指标"""
    total_papers: int
    successful_abstracts: int
    cache_hits: int
    total_time: float
    avg_response_time: float
    error_count: int


class IEEEAsyncService:
    """IEEE异步摘要抓取服务"""
    
    def __init__(self, concurrent_limit: int = 8, request_delay: float = 0.1):
        self.concurrent_limit = concurrent_limit
        self.request_delay = request_delay
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        
        # 性能监控
        self.metrics = FetchMetrics(0, 0, 0, 0.0, 0.0, 0)
        
        # HTTP头设置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://ieeexplore.ieee.org/'
        }

    async def fetch_abstracts_parallel(self, papers: List[Dict]) -> List[Dict]:
        """
        并行获取论文完整摘要（支持缓存）
        
        Args:
            papers: 包含基本信息的论文列表
            
        Returns:
            包含完整摘要的论文列表
        """
        if not papers:
            return []
        
        # 导入缓存功能
        from utils.abstract_cache import get_cached_abstract, cache_abstract
        
        start_time = time.time()
        self.metrics = FetchMetrics(len(papers), 0, 0, 0.0, 0.0, 0)
        
        print(f"🚀 Starting parallel abstract fetching for {len(papers)} papers...")
        
        # 1. 检查缓存，分离需要抓取的论文
        papers_to_fetch = []
        papers_with_cache = []
        cache_hits = 0
        
        for i, paper in enumerate(papers):
            article_number = self._extract_article_number(paper)
            if article_number:
                cached_abstract = get_cached_abstract(article_number, "ieee")
                if cached_abstract:
                    # 使用缓存的摘要
                    paper['abstract'] = cached_abstract
                    papers_with_cache.append(paper)
                    cache_hits += 1
                    print(f"📋 Paper {i+1}: Using cached abstract ({len(cached_abstract)} chars)")
                else:
                    # 需要抓取
                    papers_to_fetch.append((i, paper, article_number))
            else:
                # 无法提取文章编号，保持原样
                papers_with_cache.append(paper)
        
        self.metrics.cache_hits = cache_hits
        print(f"📊 Cache status: {cache_hits} hits, {len(papers_to_fetch)} need fetching")
        
        # 2. 如果所有摘要都已缓存，直接返回
        if not papers_to_fetch:
            self.metrics.total_time = time.time() - start_time
            print(f"✅ All abstracts available from cache!")
            self._log_performance_report()
            return papers_with_cache
        
        # 3. 并行抓取未缓存的摘要
        print(f"🔍 Fetching {len(papers_to_fetch)} uncached abstracts...")
        
        # 创建连接器，限制连接数
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=self.concurrent_limit,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.session_timeout,
            headers=self.headers
        ) as session:
            
            # 创建并发任务（只针对未缓存的论文）
            tasks = [
                self._fetch_single_abstract_with_cache(session, paper, article_number, original_index)
                for original_index, paper, article_number in papers_to_fetch
            ]
            
            # 执行所有任务，使用gather收集结果
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果和异常
            processed_results = []
            for i, result in enumerate(results):
                original_index, paper, article_number = papers_to_fetch[i]
                
                if isinstance(result, Exception):
                    logging.error(f"Task for paper {original_index+1} failed: {result}")
                    self.metrics.error_count += 1
                    processed_results.append((original_index, paper))
                else:
                    processed_results.append((original_index, result))
        
        # 4. 合并缓存的和新抓取的结果
        final_results = [None] * len(papers)
        
        # 放置缓存的结果
        cache_index = 0
        for i, paper in enumerate(papers):
            article_number = self._extract_article_number(paper)
            if not article_number or get_cached_abstract(article_number, "ieee"):
                if cache_index < len(papers_with_cache):
                    final_results[i] = papers_with_cache[cache_index]
                    cache_index += 1
                else:
                    final_results[i] = paper
        
        # 放置新抓取的结果
        for original_index, paper in processed_results:
            final_results[original_index] = paper
        
        # 过滤None值
        final_results = [paper for paper in final_results if paper is not None]
        
        # 计算性能指标
        self.metrics.total_time = time.time() - start_time
        self.metrics.avg_response_time = self.metrics.total_time / len(papers_to_fetch) if papers_to_fetch else 0
        
        # 输出性能报告
        self._log_performance_report()
        
        return final_results

    async def _fetch_single_abstract_with_cache(self, session: aiohttp.ClientSession, paper: Dict, article_number: str, index: int) -> Dict:
        """
        获取单篇论文的完整摘要（支持缓存）
        
        Args:
            session: aiohttp会话
            paper: 论文信息
            article_number: 文章编号
            index: 论文索引（用于日志）
            
        Returns:
            包含完整摘要的论文信息
        """
        async with self.semaphore:  # 控制并发数
            try:
                # 导入缓存功能
                from utils.abstract_cache import cache_abstract
                
                # 构建详细页面URL
                detail_url = f"https://ieeexplore.ieee.org/document/{article_number}"
                
                # 添加延迟避免被限流
                await asyncio.sleep(self.request_delay)
                
                # 发送HTTP请求
                async with session.get(detail_url) as response:
                    if response.status != 200:
                        logging.warning(f"HTTP {response.status} for paper {index+1}: {article_number}")
                        return paper
                    
                    html_content = await response.text()
                    
                    # 解析页面获取完整摘要
                    full_abstract = self._extract_abstract_from_html(html_content)
                    
                    if full_abstract and len(full_abstract) > len(paper.get('abstract', '')):
                        # 更新论文摘要
                        paper['abstract'] = full_abstract
                        self.metrics.successful_abstracts += 1
                        
                        # 缓存新的完整摘要
                        cache_abstract(
                            article_id=article_number,
                            url=detail_url,
                            title=paper.get('title', ''),
                            abstract=full_abstract,
                            source='ieee'
                        )
                        
                        print(f"✓ Paper {index+1}: Updated and cached abstract ({len(full_abstract)} chars)")
                    else:
                        print(f"⚠ Paper {index+1}: No improvement found")
                    
                    return paper
                    
            except asyncio.TimeoutError:
                logging.error(f"Timeout for paper {index+1}")
                self.metrics.error_count += 1
                return paper
                
            except Exception as e:
                logging.error(f"Error fetching abstract for paper {index+1}: {e}")
                self.metrics.error_count += 1
                return paper

    async def _fetch_single_abstract(self, session: aiohttp.ClientSession, paper: Dict, index: int) -> Dict:
        """
        获取单篇论文的完整摘要
        
        Args:
            session: aiohttp会话
            paper: 论文信息
            index: 论文索引（用于日志）
            
        Returns:
            包含完整摘要的论文信息
        """
        async with self.semaphore:  # 控制并发数
            try:
                # 从paper中获取文章编号
                article_number = self._extract_article_number(paper)
                if not article_number:
                    return paper
                
                # 构建详细页面URL
                detail_url = f"https://ieeexplore.ieee.org/document/{article_number}"
                
                # 添加延迟避免被限流
                await asyncio.sleep(self.request_delay)
                
                # 发送HTTP请求
                async with session.get(detail_url) as response:
                    if response.status != 200:
                        logging.warning(f"HTTP {response.status} for paper {index+1}: {article_number}")
                        return paper
                    
                    html_content = await response.text()
                    
                    # 解析页面获取完整摘要
                    full_abstract = self._extract_abstract_from_html(html_content)
                    
                    if full_abstract and len(full_abstract) > len(paper.get('abstract', '')):
                        paper['abstract'] = full_abstract
                        self.metrics.successful_abstracts += 1
                        
                        print(f"✓ Paper {index+1}: Updated abstract ({len(full_abstract)} chars)")
                    else:
                        print(f"⚠ Paper {index+1}: No improvement found")
                    
                    return paper
                    
            except asyncio.TimeoutError:
                logging.error(f"Timeout for paper {index+1}")
                self.metrics.error_count += 1
                return paper
                
            except Exception as e:
                logging.error(f"Error fetching abstract for paper {index+1}: {e}")
                self.metrics.error_count += 1
                return paper

    def _extract_article_number(self, paper: Dict) -> Optional[str]:
        """从论文信息中提取文章编号"""
        # 调试：打印paper结构
        print(f"Debug: Extracting article number from paper keys: {list(paper.keys())}")
        
        # 1. 首先检查 source_specific 字段中的 ieee_number
        if 'source_specific' in paper and isinstance(paper['source_specific'], dict):
            ieee_number = paper['source_specific'].get('ieee_number')
            if ieee_number:
                article_num = str(ieee_number).strip()
                if article_num.isdigit():
                    print(f"Debug: Found IEEE number in source_specific: {article_num}")
                    return article_num
        
        # 2. 尝试从URL中提取
        url_fields = ['url', 'documentLink', 'htmlLink']
        for field in url_fields:
            if field in paper and paper[field]:
                value = str(paper[field])
                print(f"Debug: Checking {field} = {value}")
                
                # 从 /document/12345678/ 或 https://ieeexplore.ieee.org/document/12345678/ 提取
                match = re.search(r'/document/(\d+)', value)
                if match:
                    article_num = match.group(1)
                    print(f"Debug: Extracted article number from URL: {article_num}")
                    return article_num
        
        # 3. 尝试其他可能的字段
        other_fields = ['articleNumber', 'ieee_number', 'article_number']
        for field in other_fields:
            if field in paper and paper[field]:
                value = str(paper[field]).strip()
                print(f"Debug: Found {field} = {value}")
                
                if value.isdigit():
                    print(f"Debug: Direct article number: {value}")
                    return value
        
        print("Debug: No article number found!")
        return None

    def _extract_abstract_from_html(self, html_content: str) -> Optional[str]:
        """
        从IEEE页面HTML中提取完整摘要
        基于提供的参考代码，使用正确的正则表达式匹配xplGlobal.document.metadata
        """
        try:
            # 主要方法：使用与参考代码相同的正则表达式
            matches = re.search(r'xplGlobal\.document\.metadata=(\{.*?\});', html_content, re.DOTALL)
            
            if matches:
                try:
                    # 获取JSON字符串
                    json_str = matches.group(1)
                    # 将JSON字符串转换为字典
                    metadata = json.loads(json_str)
                    abstract = metadata.get('abstract', '')
                    
                    if abstract and len(abstract) > 50:  # 确保是有效的摘要
                        print(f"✓ Successfully extracted abstract ({len(abstract)} chars)")
                        return abstract.strip()
                    else:
                        print(f"⚠ Abstract too short or empty: {len(abstract)} chars")
                        
                except json.JSONDecodeError as e:
                    print(f"✗ JSON decode error: {e}")
                    logging.debug(f"Failed to parse JSON: {json_str[:200]}...")
            else:
                print("✗ xplGlobal.document.metadata not found in HTML")
            
            # 备用方法1: 尝试其他可能的metadata变量
            backup_patterns = [
                r'document\.metadata\s*=\s*(\{.*?\});',
                r'metadata\s*=\s*(\{.*?\});'
            ]
            
            for pattern in backup_patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1)
                        metadata = json.loads(json_str)
                        abstract = metadata.get('abstract', '')
                        if abstract and len(abstract) > 50:
                            print(f"✓ Extracted from backup pattern ({len(abstract)} chars)")
                            return abstract.strip()
                    except json.JSONDecodeError:
                        continue
            
            # 备用方法2: 直接从HTML元素中提取
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                abstract_selectors = [
                    '.abstract-text',
                    '.abstract .description', 
                    '[data-testid="abstract-text"]',
                    '.u-mb-1.stats-abstract-text',
                    '.abstract-desktop-div .u-mb-1'
                ]
                
                for selector in abstract_selectors:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if len(text) > 50:
                            print(f"✓ Extracted from HTML element ({len(text)} chars)")
                            return text
            except ImportError:
                print("BeautifulSoup not available for HTML parsing")
            
            print("✗ No abstract found using any method")
            return None
            
        except Exception as e:
            print(f"✗ Error extracting abstract: {e}")
            logging.error(f"Error extracting abstract: {e}")
            return None

    def _decode_html_entities(self, text: str) -> str:
        """解码HTML实体"""
        import html
        return html.unescape(text)

    def _log_performance_report(self):
        """输出性能报告（包含缓存统计）"""
        success_rate = (self.metrics.successful_abstracts / self.metrics.total_papers * 100) if self.metrics.total_papers > 0 else 0
        error_rate = (self.metrics.error_count / self.metrics.total_papers * 100) if self.metrics.total_papers > 0 else 0
        cache_rate = (self.metrics.cache_hits / self.metrics.total_papers * 100) if self.metrics.total_papers > 0 else 0
        
        print(f"""
📊 并行抓取性能报告:
   总论文数: {self.metrics.total_papers}
   缓存命中: {self.metrics.cache_hits} ({cache_rate:.1f}%)
   成功获取: {self.metrics.successful_abstracts} ({success_rate:.1f}%)
   错误数量: {self.metrics.error_count} ({error_rate:.1f}%)
   总耗时: {self.metrics.total_time:.2f}秒
   平均耗时: {self.metrics.avg_response_time:.2f}秒/篇
   并发数: {self.concurrent_limit}
        """)
        
        # 性能建议
        if self.metrics.avg_response_time > 3.0:
            print("💡 建议: 平均响应时间较慢，可以减少并发数")
        elif self.metrics.avg_response_time < 0.5:
            print("💡 建议: 响应时间很快，可以适当增加并发数")
        
        if error_rate > 20:
            print("⚠️  警告: 错误率较高，可能触发了反爬虫机制")
        
        if cache_rate > 50:
            print("🎉 缓存效果良好，大量重复请求被避免")
        elif cache_rate < 10:
            print("📋 缓存命中率较低，这是正常的首次抓取")


# 工厂函数
def create_async_service(concurrent_limit: int = 8, request_delay: float = 0.1) -> IEEEAsyncService:
    """创建异步服务实例"""
    return IEEEAsyncService(concurrent_limit=concurrent_limit, request_delay=request_delay)