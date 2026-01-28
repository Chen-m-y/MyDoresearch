"""
国家科技管理信息系统适配器
基于科技部通知公告页面抓取项目申报新闻
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from .base import BaseNewsAdapter, NewsData
from utils.exceptions import FetchError, ValidationError
from utils.progress_monitor import create_progress_tracker


class MOSTAdapter(BaseNewsAdapter):
    """国家科技管理信息系统（科技部）新闻适配器"""

    @property
    def name(self) -> str:
        return "most"

    @property
    def display_name(self) -> str:
        return "国家科技管理信息系统"

    @property
    def description(self) -> str:
        return "科技部通知公告，包含国家科技项目申报信息"

    @property
    def required_params(self) -> List[str]:
        return []  # 无必需参数

    @property
    def optional_params(self) -> List[str]:
        return ["limit", "category_filter", "date_from", "date_to"]

    def _validate_specific_params(self, params: Dict[str, Any]) -> None:
        """科技部特定的参数验证"""
        limit = params.get('limit', 20)
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            raise ValidationError("limit必须是1-100之间的整数")

    def fetch_news(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取科技部新闻数据

        Args:
            params: 包含可选参数的字典
                - limit: 返回结果数量限制 (默认20, 最大100)
                - category_filter: 分类过滤 (funding_announcement, policy_update等)
                - date_from: 开始日期 (YYYY-MM-DD)
                - date_to: 结束日期 (YYYY-MM-DD)
        """
        limit = params.get('limit', 20)
        category_filter = params.get('category_filter')
        date_from = params.get('date_from')
        date_to = params.get('date_to')

        # 完全移除进度监控，直接执行
        try:
            import time
            total_start = time.time()

            print(f"🔍 开始抓取科技部新闻...")

            # 1. 获取主页数据
            fetch_start = time.time()
            news_list = self._fetch_news_list()
            fetch_time = time.time() - fetch_start
            print(f"⏱️  抓取新闻列表耗时: {fetch_time:.2f}秒, 获取到 {len(news_list)} 条")

            # 2. 转换为标准格式
            news_items = []
            for i, raw_news in enumerate(news_list):
                try:
                    news_data = self._map_to_news_data(raw_news)

                    # 应用过滤条件
                    if self._should_include_news(news_data, category_filter, date_from, date_to):
                        news_items.append(news_data)

                    # tracker.increment(success=True, operation=f"处理新闻 {i+1}/{len(news_list)}")
                    pass
                except Exception as e:
                    print(f"Warning: Failed to process news item: {e}")
                    # tracker.increment(success=False, operation=f"处理新闻失败 {i+1}/{len(news_list)}")
                    continue

            # tracker.update(operation="排序和应用限制...")

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
                'next_cursor': None,  # 科技部网站通常不支持分页游标
                'rate_limit_remaining': None,
                'cache_hit': False
            }

            # 设置结果到进度追踪器
            # tracker.set_results({
            #     'news_count': len(news_dicts),
            #     'total_available': len(news_list),
            #     'filtered': bool(category_filter or date_from or date_to)
            # })

            total_time = time.time() - total_start
            print(f"🎉 科技部新闻抓取完成，总耗时: {total_time:.2f}秒")

            # 临时添加调试信息到返回结果中
            result['debug_info'] = {
                'fetch_time': f"{fetch_time:.2f}s",
                'total_time': f"{total_time:.2f}s",
                'news_count': len(news_list)
            }

            return result

        except FetchError:
            raise
        except Exception as e:
            raise FetchError(
                f"科技部新闻抓取失败: {str(e)}",
                error_code='MOST_FETCH_ERROR'
            )

    def _fetch_news_list(self) -> List[Dict[str, Any]]:
        """获取新闻列表"""
        url = "https://service.most.gov.cn/kjjh_tztg/"

        try:
            # 使用父类的请求方法
            response = self._make_request_html(url)
            soup = BeautifulSoup(response, 'html.parser')

            items = []

            # 查找所有表格行
            rows = soup.find_all('tr')

            for row in rows:
                try:
                    # 提取标题
                    title_cell = row.find('td', class_='table_gkgs_title')
                    if not title_cell:
                        continue

                    title = title_cell.get_text(strip=True)
                    if not title:
                        continue

                    # 提取链接
                    title_div = title_cell.find('div')
                    if not title_div or not title_div.get('onclick'):
                        continue

                    onclick = title_div.get('onclick')
                    link_match = re.search(r"['\"](.*?)['\"]", onclick)
                    if not link_match:
                        continue

                    link = link_match.group(1)
                    if not link.startswith('http'):
                        link = f"https://service.most.gov.cn{link}" if link.startswith('/') else f"https://service.most.gov.cn/kjjh_tztg/{link}"

                    # 提取发布单位
                    unit_cell = row.find('td', class_='table_gkgs_unit')
                    unit = unit_cell.get_text(strip=True) if unit_cell else "科技部"

                    # 提取日期
                    date_cell = row.find('td', class_='table_gkgs_date')
                    date_str = date_cell.get_text(strip=True) if date_cell else ""

                    items.append({
                        'title': title,
                        'link': link,
                        'unit': unit,
                        'date': date_str,
                        'raw_html': str(row)
                    })

                except Exception as e:
                    print(f"Warning: Failed to parse row: {e}")
                    continue

            return items

        except Exception as e:
            raise FetchError(
                f"获取科技部新闻列表失败: {str(e)}",
                error_code='NEWS_LIST_FETCH_ERROR'
            )

    def _map_to_news_data(self, raw_data: Dict[str, Any]) -> NewsData:
        """将科技部原始数据映射为标准格式"""

        title = raw_data.get('title', '').strip()
        link = raw_data.get('link', '')
        unit = raw_data.get('unit', '科技部')
        date_str = raw_data.get('date', '')

        # 解析发布日期
        published_date = self._parse_date(date_str)

        # 生成摘要（从标题提取关键信息）
        summary = self._generate_summary(title)

        # 确定新闻分类
        category = self._categorize_news(title)

        # 提取关键词
        keywords = self._extract_keywords(title)

        # 确定优先级
        priority = self._determine_priority(title, category)

        # 判断状态（基于日期和内容）
        status = self._determine_status(title, published_date)

        # 科技部特定字段
        source_specific = {
            'source_unit': unit,
            'original_link': link,
            'news_source': '国家科技管理信息系统'
        }

        # 元数据
        metadata = {
            'publisher': '中华人民共和国科学技术部',
            'website': 'https://service.most.gov.cn/',
            'crawl_time': datetime.now().isoformat(),
            'data_source': 'most_kjjh_tztg'
        }

        return NewsData(
            title=title,
            content=title,  # 初始内容为标题，可后续增强
            summary=summary,
            source='most',
            published_date=published_date,
            url=link,
            category=category,
            organization=unit,
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

        # 常见的日期格式
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{4})/(\d{2})/(\d{2})',  # YYYY/MM/DD
            r'(\d{4})\.(\d{2})\.(\d{2})',  # YYYY.MM.DD
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # YYYY年MM月DD日
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
        """从标题生成摘要"""
        # 简单的摘要生成逻辑
        if len(title) <= 50:
            return title

        # 截取前50个字符并添加省略号
        return title[:47] + "..."

    def _categorize_news(self, title: str) -> str:
        """根据标题确定新闻分类"""
        title_lower = title.lower()

        # 资助公告相关关键词
        if any(keyword in title for keyword in ['申报', '指南', '申请', '资助', '基金', '项目']):
            return 'funding_announcement'

        # 政策更新
        if any(keyword in title for keyword in ['政策', '规定', '办法', '通知', '管理']):
            return 'policy_update'

        # 征集公告
        if any(keyword in title for keyword in ['征集', '征求', '意见', '建议']):
            return 'call_for_proposals'

        # 结果公示
        if any(keyword in title for keyword in ['公示', '结果', '名单', '评审']):
            return 'results_announcement'

        # 默认分类
        return 'general_announcement'

    def _extract_keywords(self, title: str) -> List[str]:
        """从标题提取关键词"""
        keywords = []

        # 常见的科技项目关键词
        keyword_patterns = [
            r'国家.*?(?:基金|项目|计划)',
            r'重[大点].*?(?:项目|专项|工程)',
            r'(?:申报|申请|征集).*?(?:指南|通知)',
            r'(?:科技|创新|研发|技术)',
            r'(?:资助|支持|经费)',
        ]

        for pattern in keyword_patterns:
            matches = re.findall(pattern, title)
            keywords.extend(matches)

        # 移除重复并限制数量
        keywords = list(dict.fromkeys(keywords))[:10]

        return keywords

    def _determine_priority(self, title: str, category: str) -> str:
        """确定新闻优先级"""
        title_lower = title.lower()

        # 高优先级关键词
        high_priority_keywords = ['重大', '重点', '国家级', '紧急', '重要']
        if any(keyword in title for keyword in high_priority_keywords):
            return 'high'

        # 资助公告通常为高优先级
        if category == 'funding_announcement':
            return 'high'

        # 征集公告为普通优先级
        if category == 'call_for_proposals':
            return 'normal'

        return 'normal'

    def _determine_status(self, title: str, published_date: str) -> str:
        """确定新闻状态"""
        try:
            pub_date = datetime.strptime(published_date.split()[0], '%Y-%m-%d')
            days_diff = (datetime.now() - pub_date).days

            # 超过60天的新闻标记为过期
            if days_diff > 60:
                return 'expired'

            # 检查标题中是否有截止相关信息
            if any(keyword in title for keyword in ['截止', '结束', '已结束']):
                return 'expired'

            return 'active'

        except:
            return 'active'

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
                pass  # 如果日期解析失败，不进行过滤

        return True

    def _make_request_html(self, url: str, **kwargs) -> str:
        """
        发送HTTP请求并返回HTML内容 - 优化版requests
        """
        import requests
        import time

        # 创建session以复用连接
        session = requests.Session()

        # 设置基本请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36 Edg/140.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }

        print(f"🌐 正在请求: {url}")
        start_time = time.time()

        try:
            # 优化的requests参数
            response = session.get(
                url,
                headers=headers,
                timeout=(5, 10),  # 连接超时5秒，读取超时10秒
                allow_redirects=True,
                stream=False,  # 不使用流模式
                verify=True    # 验证SSL证书
            )

            request_time = time.time() - start_time
            print(f"⏱️  请求耗时: {request_time:.2f}秒")

            # 检查状态码
            if response.status_code == 200:
                # 设置正确的编码
                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text
            else:
                raise Exception(f"HTTP状态码错误: {response.status_code}")

        except Exception as e:
            request_time = time.time() - start_time
            print(f"⚠️  请求失败，耗时: {request_time:.2f}秒，错误: {e}")
            raise Exception(f"网络请求失败: {str(e)}")
        finally:
            session.close()