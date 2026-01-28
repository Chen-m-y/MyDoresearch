"""
数据抓取适配器的抽象基类
所有数据源适配器都应继承这个基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PaperData:
    """标准化的论文数据结构"""
    title: str
    abstract: str
    authors: List[str]
    journal: str
    published_date: str  # 格式：YYYY-MM-DD
    url: str
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    keywords: Optional[List[str]] = None
    citations: int = 0
    source_specific: Optional[Dict[str, Any]] = None  # 源特有字段
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "journal": self.journal,
            "published_date": self.published_date,
            "url": self.url,
            "citations": self.citations,
        }

        # 添加可选字段
        if self.pdf_url:
            result["pdf_url"] = self.pdf_url
        if self.doi:
            result["doi"] = self.doi
        if self.keywords:
            result["keywords"] = self.keywords
        if self.source_specific:
            result["source_specific"] = self.source_specific
        if self.metadata:
            result["metadata"] = self.metadata

        return result


@dataclass
class NewsData:
    """标准化的新闻数据结构"""
    title: str
    content: str
    summary: str
    source: str
    published_date: str  # 格式：YYYY-MM-DD HH:MM:SS
    url: str
    category: str  # 新闻分类：funding_announcement, policy_update, call_for_proposals等
    organization: str  # 发布机构
    attachment_urls: Optional[List[str]] = None  # 附件链接
    deadline: Optional[str] = None  # 申报截止日期
    funding_amount: Optional[str] = None  # 资助金额
    keywords: Optional[List[str]] = None
    priority: str = "normal"  # 优先级：high, normal, low
    status: str = "active"  # 状态：active, expired, draft
    source_specific: Optional[Dict[str, Any]] = None  # 源特有字段
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "source": self.source,
            "published_date": self.published_date,
            "url": self.url,
            "category": self.category,
            "organization": self.organization,
            "priority": self.priority,
            "status": self.status,
        }

        # 添加可选字段
        if self.attachment_urls:
            result["attachment_urls"] = self.attachment_urls
        if self.deadline:
            result["deadline"] = self.deadline
        if self.funding_amount:
            result["funding_amount"] = self.funding_amount
        if self.keywords:
            result["keywords"] = self.keywords
        if self.source_specific:
            result["source_specific"] = self.source_specific
        if self.metadata:
            result["metadata"] = self.metadata

        return result


class BaseAdapter(ABC):
    """抽象基类：数据源适配器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器

        Args:
            config: 配置字典，包含API密钥、基础URL等
        """
        self.config = config
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)

    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称，用作标识符"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """适配器显示名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """适配器描述"""
        pass

    @property
    @abstractmethod
    def required_params(self) -> List[str]:
        """必需的参数列表"""
        pass

    @property
    @abstractmethod
    def optional_params(self) -> List[str]:
        """可选的参数列表"""
        pass

    @property
    def adapter_type(self) -> str:
        """适配器类型：paper(论文) 或 news(新闻)"""
        return "paper"  # 默认为论文适配器

    def validate_params(self, params: Dict[str, Any]) -> None:
        """
        验证输入参数

        Args:
            params: 要验证的参数字典

        Raises:
            ValidationError: 参数验证失败时抛出
        """
        from utils.exceptions import ValidationError

        # 检查必需参数
        for param in self.required_params:
            if param not in params or params[param] is None:
                raise ValidationError(f"缺少必需参数: {param}")

        # 子类可以重写此方法来添加更多验证逻辑
        self._validate_specific_params(params)

    def _validate_specific_params(self, params: Dict[str, Any]) -> None:
        """
        子类特定的参数验证逻辑
        子类可以重写此方法来实现特定的验证逻辑

        Args:
            params: 要验证的参数字典
        """
        pass

    @abstractmethod
    def fetch_papers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取论文数据的主要方法

        Args:
            params: 查询参数

        Returns:
            包含以下字段的字典:
            - papers: List[PaperData] - 论文列表
            - total_count: int - 总数量
            - has_more: bool - 是否还有更多数据
            - next_cursor: Optional[str] - 下一页游标
            - rate_limit_remaining: Optional[int] - 剩余API调用次数
            - cache_hit: bool - 是否命中缓存

        Raises:
            FetchError: 抓取失败时抛出
            RateLimitError: 达到API限制时抛出
        """
        pass

    def _map_to_paper_data(self, raw_data: Dict[str, Any]) -> PaperData:
        """
        将原始数据映射为标准格式
        子类必须实现此方法

        Args:
            raw_data: 从数据源获取的原始数据

        Returns:
            PaperData: 标准化的论文数据
        """
        raise NotImplementedError("子类必须实现 _map_to_paper_data 方法")


class BaseNewsAdapter(BaseAdapter):
    """新闻适配器基类"""

    @property
    def adapter_type(self) -> str:
        """适配器类型"""
        return "news"

    @abstractmethod
    def fetch_news(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        抓取新闻数据的主要方法

        Args:
            params: 查询参数

        Returns:
            包含以下字段的字典:
            - news: List[NewsData] - 新闻列表
            - total_count: int - 总数量
            - has_more: bool - 是否还有更多数据
            - next_cursor: Optional[str] - 下一页游标
            - rate_limit_remaining: Optional[int] - 剩余API调用次数
            - cache_hit: bool - 是否命中缓存

        Raises:
            FetchError: 抓取失败时抛出
            RateLimitError: 达到API限制时抛出
        """
        pass

    def fetch_papers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """重写父类方法，转发到fetch_news"""
        return self.fetch_news(params)

    def _map_to_news_data(self, raw_data: Dict[str, Any]) -> NewsData:
        """
        将原始数据映射为标准新闻格式
        子类必须实现此方法

        Args:
            raw_data: 从数据源获取的原始数据

        Returns:
            NewsData: 标准化的新闻数据
        """
        raise NotImplementedError("子类必须实现 _map_to_news_data 方法")
    
    def _make_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        统一的HTTP请求方法
        子类可以使用此方法发送HTTP请求
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应数据
            
        Raises:
            FetchError: 请求失败时抛出
        """
        import requests
        from utils.exceptions import FetchError, RateLimitError
        import time
        
        # 设置默认超时
        kwargs.setdefault('timeout', self.timeout)
        
        # 添加API密钥（如果需要）
        if self.api_key and 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        # 重试机制
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, **kwargs)
                
                # 检查HTTP状态码
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
                        details={'status_code': response.status_code, 'response': response.text}
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
    
    def _post_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        统一的HTTP POST请求方法
        """
        import requests
        from utils.exceptions import FetchError, RateLimitError
        import time
        
        kwargs.setdefault('timeout', self.timeout)
        
        if self.api_key and 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(url, **kwargs)
                
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
                        details={'status_code': response.status_code, 'response': response.text}
                    )
                
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries:
                    raise FetchError("请求超时", error_code='REQUEST_TIMEOUT')
                time.sleep(2 ** attempt)
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise FetchError(
                        f"网络请求失败: {str(e)}",
                        error_code='NETWORK_ERROR'
                    )
                time.sleep(2 ** attempt)