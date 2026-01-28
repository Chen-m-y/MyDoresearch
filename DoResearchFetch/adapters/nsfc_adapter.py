"""
国家自然科学基金委员会适配器
抓取基金申报通知和政策信息
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from .base import BaseNewsAdapter, NewsData
from utils.exceptions import FetchError, ValidationError
from utils.progress_monitor import create_progress_tracker


class NSFCAdapter(BaseNewsAdapter):
    """国家自然科学基金委员会新闻适配器"""

    @property
    def name(self) -> str:
        return "nsfc"

    @property
    def display_name(self) -> str:
        return "国家自然科学基金委员会"

    @property
    def description(self) -> str:
        return "自然科学基金项目申报指南、政策通知等信息"

    @property
    def required_params(self) -> List[str]:
        return []

    @property
    def optional_params(self) -> List[str]:
        return ["limit", "category_filter", "date_from", "date_to", "news_type"]

    def _validate_specific_params(self, params: Dict[str, Any]) -> None:
        """基金委特定的参数验证"""
        limit = params.get('limit', 20)
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            raise ValidationError("limit必须是1-100之间的整数")

        news_type = params.get('news_type', 'all')
        if news_type not in ['all', 'funding', 'policy', 'results']:
            raise ValidationError("news_type必须是: all, funding, policy, results")

    def fetch_news(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取基金委新闻数据

        Args:
            params: 包含可选参数的字典
                - limit: 返回结果数量限制 (默认20, 最大100)
                - category_filter: 分类过滤
                - date_from: 开始日期 (YYYY-MM-DD)
                - date_to: 结束日期 (YYYY-MM-DD)
                - news_type: 新闻类型 (all, funding, policy, results)
        """
        limit = params.get('limit', 20)
        category_filter = params.get('category_filter')
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        news_type = params.get('news_type', 'all')

        # 创建进度追踪器
        with create_progress_tracker(f"nsfc-news", limit, "抓取基金委通知公告") as tracker:
            try:
                tracker.update(operation="获取通知列表...")

                # 1. 根据类型获取不同页面的数据
                news_list = []
                if news_type in ['all', 'funding']:
                    funding_news = self._fetch_funding_announcements()
                    news_list.extend(funding_news)

                if news_type in ['all', 'policy']:
                    policy_news = self._fetch_policy_announcements()
                    news_list.extend(policy_news)

                if news_type in ['all', 'results']:
                    result_news = self._fetch_result_announcements()
                    news_list.extend(result_news)

                tracker.update(operation=f"处理 {len(news_list)} 条新闻...")

                # 2. 转换为标准格式
                news_items = []
                for i, raw_news in enumerate(news_list):
                    try:
                        news_data = self._map_to_news_data(raw_news)

                        # 应用过滤条件
                        if self._should_include_news(news_data, category_filter, date_from, date_to):
                            news_items.append(news_data)

                        tracker.increment(success=True, operation=f"处理新闻 {i+1}/{len(news_list)}")
                    except Exception as e:
                        print(f"Warning: Failed to process NSFC news item: {e}")
                        tracker.increment(success=False, operation=f"处理新闻失败 {i+1}/{len(news_list)}")
                        continue

                tracker.update(operation="排序和应用限制...")

                # 3. 按发布日期倒序排序
                news_items.sort(key=lambda x: x.published_date, reverse=True)

                # 4. 应用limit限制
                news_items = news_items[:limit]

                # 转换为字典格式
                news_dicts = [news.to_dict() for news in news_items]

                # 5. 构建响应
                total_count = len(news_dicts)
                has_more = len(news_list) > limit

                result = {
                    'news': news_dicts,
                    'total_count': total_count,
                    'has_more': has_more,
                    'next_cursor': None,
                    'rate_limit_remaining': None,
                    'cache_hit': False
                }

                # 设置结果到进度追踪器
                tracker.set_results({
                    'news_count': len(news_dicts),
                    'total_available': len(news_list),
                    'news_type': news_type,
                    'filtered': bool(category_filter or date_from or date_to)
                })

                return result

            except FetchError:
                raise
            except Exception as e:
                raise FetchError(
                    f"基金委新闻抓取失败: {str(e)}",
                    error_code='NSFC_FETCH_ERROR'
                )

    def _fetch_funding_announcements(self) -> List[Dict[str, Any]]:
        """抓取申报通知"""
        url = "https://www.nsfc.gov.cn/publish/portal0/tab434/"
        return self._fetch_news_from_url(url, 'funding_announcement')

    def _fetch_policy_announcements(self) -> List[Dict[str, Any]]:
        """抓取政策文件"""
        url = "https://www.nsfc.gov.cn/publish/portal0/tab442/"
        return self._fetch_news_from_url(url, 'policy_update')

    def _fetch_result_announcements(self) -> List[Dict[str, Any]]:
        """抓取评审结果"""
        url = "https://www.nsfc.gov.cn/publish/portal0/tab446/"
        return self._fetch_news_from_url(url, 'results_announcement')

    def _fetch_news_from_url(self, url: str, default_category: str) -> List[Dict[str, Any]]:
        """从指定URL抓取新闻列表"""
        try:
            response = self._make_request_html(url)
            soup = BeautifulSoup(response, 'html.parser')

            items = []

            # 查找新闻列表 - 基金委网站通常使用特定的CSS类
            news_items = soup.find_all('li', class_='line_list') or soup.find_all('tr')

            for item in news_items:
                try:
                    # 提取标题和链接
                    link_elem = item.find('a')
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title:
                        continue

                    # 构建完整链接
                    href = link_elem.get('href', '')
                    if href.startswith('//'):
                        link = f"https:{href}"
                    elif href.startswith('/'):
                        link = f"https://www.nsfc.gov.cn{href}"
                    elif not href.startswith('http'):
                        link = f"{url.rstrip('/')}/{href}"
                    else:
                        link = href

                    # 提取日期
                    date_str = ""
                    date_elem = item.find(class_='date') or item.find('td', class_='time')
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)

                    # 如果没有找到日期元素，尝试从文本中提取
                    if not date_str:
                        date_pattern = r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})'
                        date_match = re.search(date_pattern, item.get_text())
                        if date_match:
                            date_str = date_match.group(1)

                    items.append({
                        'title': title,
                        'link': link,
                        'date': date_str,
                        'category': default_category,
                        'raw_html': str(item)
                    })

                except Exception as e:
                    print(f"Warning: Failed to parse NSFC news item: {e}")
                    continue

            return items

        except Exception as e:
            print(f"Warning: Failed to fetch news from {url}: {e}")
            return []

    def _map_to_news_data(self, raw_data: Dict[str, Any]) -> NewsData:
        """将基金委原始数据映射为标准格式"""

        title = raw_data.get('title', '').strip()
        link = raw_data.get('link', '')
        date_str = raw_data.get('date', '')
        raw_category = raw_data.get('category', 'general_announcement')

        # 解析发布日期
        published_date = self._parse_date(date_str)

        # 生成摘要
        summary = self._generate_summary(title)

        # 重新分析分类（基于标题内容）
        category = self._categorize_news(title, raw_category)

        # 提取关键词
        keywords = self._extract_keywords(title)

        # 确定优先级
        priority = self._determine_priority(title, category)

        # 判断状态
        status = self._determine_status(title, published_date)

        # 提取申报截止日期
        deadline = self._extract_deadline(title)

        # 提取资助信息
        funding_amount = self._extract_funding_amount(title)

        # 基金委特定字段
        source_specific = {
            'original_category': raw_category,
            'nsfc_url': link,
            'news_source': '国家自然科学基金委员会'
        }

        # 元数据
        metadata = {
            'publisher': '国家自然科学基金委员会',
            'website': 'https://www.nsfc.gov.cn/',
            'crawl_time': datetime.now().isoformat(),
            'data_source': 'nsfc_portal'
        }

        return NewsData(
            title=title,
            content=title,  # 初始内容为标题，可后续增强
            summary=summary,
            source='nsfc',
            published_date=published_date,
            url=link,
            category=category,
            organization='国家自然科学基金委员会',
            deadline=deadline,
            funding_amount=funding_amount,
            keywords=keywords,
            priority=priority,
            status=status,
            source_specific=source_specific,
            metadata=metadata
        )

    def _parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 清理日期字符串
        date_str = re.sub(r'[年月日]', '-', date_str).replace('--', '-').strip('-')

        # 常见的日期格式
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # YYYY.MM.DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                year, month, day = groups[0], groups[1].zfill(2), groups[2].zfill(2)
                try:
                    # 验证日期有效性
                    datetime(int(year), int(month), int(day))
                    return f"{year}-{month}-{day} 00:00:00"
                except ValueError:
                    continue

        # 如果无法解析，返回当前日期
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _generate_summary(self, title: str) -> str:
        """生成摘要"""
        if len(title) <= 60:
            return title
        return title[:57] + "..."

    def _categorize_news(self, title: str, default_category: str) -> str:
        """根据标题重新确定分类"""
        title_lower = title.lower()

        # 项目申报相关
        if any(keyword in title for keyword in ['申报', '指南', '申请须知', '项目申请']):
            return 'funding_announcement'

        # 评审结果
        if any(keyword in title for keyword in ['评审结果', '资助项目', '获批', '批准资助']):
            return 'results_announcement'

        # 政策文件
        if any(keyword in title for keyword in ['管理办法', '实施细则', '规定', '通知']):
            return 'policy_update'

        # 征集通知
        if any(keyword in title for keyword in ['征集', '征求意见', '评议']):
            return 'call_for_proposals'

        return default_category

    def _extract_keywords(self, title: str) -> List[str]:
        """提取关键词"""
        keywords = []

        # 基金类型关键词
        fund_types = [
            r'面上项目', r'重点项目', r'青年.*?基金', r'地区.*?基金',
            r'国际.*?合作', r'重大.*?项目', r'创新.*?群体',
            r'杰出青年', r'优秀青年', r'重大研究计划'
        ]

        for pattern in fund_types:
            matches = re.findall(pattern, title)
            keywords.extend(matches)

        # 学科领域关键词
        disciplines = [
            r'数学', r'物理', r'化学', r'生物', r'医学', r'工程',
            r'信息', r'管理', r'地球', r'环境', r'材料'
        ]

        for pattern in disciplines:
            if re.search(pattern, title):
                keywords.append(pattern)

        # 移除重复并限制数量
        keywords = list(dict.fromkeys(keywords))[:8]
        return keywords

    def _determine_priority(self, title: str, category: str) -> str:
        """确定优先级"""
        # 重大、重点项目为高优先级
        if any(keyword in title for keyword in ['重大', '重点', '杰出', '创新群体']):
            return 'high'

        # 申报指南为高优先级
        if category == 'funding_announcement':
            return 'high'

        return 'normal'

    def _determine_status(self, title: str, published_date: str) -> str:
        """确定状态"""
        try:
            pub_date = datetime.strptime(published_date.split()[0], '%Y-%m-%d')
            days_diff = (datetime.now() - pub_date).days

            # 申报通知类的有效期较长
            if any(keyword in title for keyword in ['申报', '指南']):
                if days_diff > 180:  # 6个月
                    return 'expired'
            else:
                if days_diff > 90:  # 3个月
                    return 'expired'

            return 'active'

        except:
            return 'active'

    def _extract_deadline(self, title: str) -> Optional[str]:
        """从标题中提取申报截止日期"""
        # 寻找日期模式
        deadline_patterns = [
            r'截止.*?(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}年\d{1,2}月\d{1,2}日).*?截止',
            r'(\d{4}-\d{1,2}-\d{1,2}).*?截止',
        ]

        for pattern in deadline_patterns:
            match = re.search(pattern, title)
            if match:
                date_str = match.group(1)
                # 转换为标准格式
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date.split()[0]  # 只返回日期部分

        return None

    def _extract_funding_amount(self, title: str) -> Optional[str]:
        """从标题中提取资助金额信息"""
        amount_patterns = [
            r'(\d+(?:\.\d+)?万元)',
            r'(\d+(?:\.\d+)?亿元)',
            r'资助.*?(\d+(?:\.\d+)?万)',
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)

        return None

    def _should_include_news(self, news: NewsData, category_filter: Optional[str],
                           date_from: Optional[str], date_to: Optional[str]) -> bool:
        """判断是否应该包含这条新闻"""
        # 分类过滤
        if category_filter and news.category != category_filter:
            return False

        # 日期过滤
        if date_from or date_to:
            try:
                news_date = datetime.strptime(news.published_date.split()[0], '%Y-%m-%d')

                if date_from:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d')
                    if news_date < from_date:
                        return False

                if date_to:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d')
                    if news_date > to_date:
                        return False
            except:
                pass

        return True

    def _make_request_html(self, url: str, **kwargs) -> str:
        """发送HTTP请求并返回HTML内容"""
        import requests
        from utils.exceptions import FetchError, RateLimitError
        import time

        # 设置请求头
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', (3, 10))  # 连接超时3秒，读取超时10秒

        # 重试机制
        for attempt in range(2 + 1):  # 最多2次重试
            try:
                response = requests.get(url, **kwargs)

                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError(
                        "API调用频率限制",
                        details={'retry_after': retry_after}
                    )

                if response.status_code >= 400:
                    raise FetchError(
                        f"HTTP请求失败: {response.status_code}",
                        error_code='HTTP_ERROR',
                        details={'status_code': response.status_code}
                    )

                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text

            except requests.exceptions.Timeout:
                if attempt == 2:  # 最多2次重试
                    raise FetchError("请求超时", error_code='REQUEST_TIMEOUT')
                time.sleep(1)  # 固定1秒延迟

            except requests.exceptions.RequestException as e:
                if attempt == 2:  # 最多2次重试
                    raise FetchError(f"网络请求失败: {str(e)}", error_code='NETWORK_ERROR')
                time.sleep(1)  # 固定1秒延迟