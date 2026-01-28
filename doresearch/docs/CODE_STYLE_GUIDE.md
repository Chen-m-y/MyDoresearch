# DoResearch 代码风格指南

## 概述

本指南定义了DoResearch项目的代码风格和最佳实践，旨在提高代码的可读性、可维护性和团队协作效率。

## 目录

- [Python代码风格](#python代码风格)
- [类型注解](#类型注解)
- [错误处理](#错误处理)
- [日志记录](#日志记录)
- [文档注释](#文档注释)
- [测试](#测试)
- [配置管理](#配置管理)
- [安全最佳实践](#安全最佳实践)

## Python代码风格

### 基本规则

- 遵循 PEP 8 风格指南
- 使用 Black 进行代码格式化（行长度88字符）
- 使用 isort 进行导入排序
- 使用有意义的变量和函数名

### 命名约定

```python
# 类名：PascalCase
class PaperManager:
    pass

class DeepSeekAnalyzer:
    pass

# 函数和变量名：snake_case
def get_paper_by_id(paper_id: int) -> Optional[PaperDict]:
    pass

# 常量：UPPER_CASE
MAX_RETRY_ATTEMPTS = 3
API_BASE_URL = "https://api.deepseek.com"

# 私有方法：前缀下划线
def _validate_input(self, data: dict) -> bool:
    pass

# 特殊方法：双下划线包围
def __init__(self):
    pass
```

### 导入顺序

```python
# 1. 标准库导入
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 2. 第三方库导入
import requests
from flask import Flask, jsonify

# 3. 本地应用导入
from common.types import PaperDict
from common.exceptions import PaperNotFoundError
from services.paper_manager import PaperManager
```

## 类型注解

### 必须使用类型注解的场景

- 所有公共函数和方法
- 所有类属性
- 复杂的数据结构

```python
from typing import Dict, List, Optional, Union
from common.types import PaperDict, APIResponse

class PaperService:
    def __init__(self, database_path: str) -> None:
        self.database_path: str = database_path
        self.papers: Dict[int, PaperDict] = {}
    
    def get_paper(self, paper_id: int) -> Optional[PaperDict]:
        """获取论文信息"""
        return self.papers.get(paper_id)
    
    def create_paper(self, paper_data: Dict[str, Any]) -> APIResponse:
        """创建新论文"""
        # 实现逻辑
        pass
    
    def search_papers(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[PaperDict]:
        """搜索论文"""
        # 实现逻辑
        pass
```

### 复杂类型定义

```python
# 使用 TypedDict 定义数据结构
from typing import TypedDict

class SearchFilter(TypedDict, total=False):
    status: str
    start_date: str
    end_date: str
    category: str

# 使用 Protocol 定义接口
from typing import Protocol

class DatabaseProtocol(Protocol):
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        ...
    
    def execute_update(self, query: str) -> int:
        ...
```

## 错误处理

### 使用自定义异常

```python
from common.exceptions import PaperNotFoundError, ValidationError

def get_paper(paper_id: int) -> PaperDict:
    """获取论文，如果不存在则抛出异常"""
    if not isinstance(paper_id, int) or paper_id <= 0:
        raise ValidationError(
            field="paper_id",
            message="Paper ID must be a positive integer",
            value=paper_id
        )
    
    paper = self.database.get_paper(paper_id)
    if not paper:
        raise PaperNotFoundError(paper_id)
    
    return paper
```

### 错误处理模式

```python
# 好的做法：具体的异常处理
try:
    paper = paper_service.get_paper(paper_id)
    return {"success": True, "data": paper}
except PaperNotFoundError as e:
    logger.warning(f"Paper not found: {paper_id}")
    return {"success": False, "error": e.to_dict()}
except ValidationError as e:
    logger.error(f"Validation error: {e.message}")
    return {"success": False, "error": e.to_dict()}

# 避免的做法：通用异常捕获
try:
    # 业务逻辑
    pass
except Exception as e:  # 避免这样做
    print(f"Something went wrong: {e}")
```

## 日志记录

### 使用结构化日志

```python
from common.logging import get_logger

logger = get_logger(__name__)

class PaperService:
    def create_paper(self, paper_data: Dict[str, Any]) -> APIResponse:
        logger.info(
            "Creating new paper",
            title=paper_data.get("title", "")[:50],
            feed_id=paper_data.get("feed_id"),
            user_id=self._get_current_user_id()
        )
        
        try:
            paper = self._validate_and_create(paper_data)
            
            logger.info(
                "Paper created successfully",
                paper_id=paper["id"],
                title=paper["title"][:50]
            )
            
            return {"success": True, "data": paper}
            
        except Exception as e:
            logger.error(
                "Failed to create paper",
                error=str(e),
                paper_data=str(paper_data)[:200]
            )
            raise
```

### 日志级别使用

```python
# DEBUG: 详细的调试信息
logger.debug("Processing paper data", data_size=len(paper_data))

# INFO: 一般信息，重要的业务事件
logger.info("Paper status updated", paper_id=123, old_status="unread", new_status="read")

# WARNING: 警告，可能的问题
logger.warning("API rate limit approaching", current_requests=950, limit=1000)

# ERROR: 错误，需要关注
logger.error("Database connection failed", error=str(e), retry_count=3)

# CRITICAL: 严重错误，系统可能无法继续运行
logger.critical("Configuration file missing", config_path="/path/to/config")
```

## 文档注释

### 函数文档

```python
def analyze_paper(
    self, 
    paper_id: int, 
    analysis_type: str = "deep_analysis",
    options: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """分析论文内容并返回分析结果。
    
    Args:
        paper_id: 论文ID，必须是有效的整数
        analysis_type: 分析类型，支持 'deep_analysis', 'summary', 'translation'
        options: 可选的分析选项，包含自定义参数
    
    Returns:
        AnalysisResult: 包含分析结果的字典，格式如下:
            - summary: 论文摘要
            - key_points: 关键点列表
            - categories: 分类标签
            - confidence: 置信度评分 (0.0-1.0)
    
    Raises:
        PaperNotFoundError: 当指定的论文不存在时
        ValidationError: 当参数验证失败时
        ExternalServiceError: 当AI分析服务不可用时
    
    Example:
        >>> analyzer = PaperAnalyzer()
        >>> result = analyzer.analyze_paper(123, "deep_analysis")
        >>> print(result["summary"])
        "This paper presents a novel approach to..."
    """
    # 实现逻辑
    pass
```

### 类文档

```python
class PaperManager:
    """论文管理服务。
    
    负责论文的CRUD操作、状态管理和批量处理。
    提供线程安全的数据库访问和缓存机制。
    
    Attributes:
        database_path: 数据库文件路径
        cache_size: 缓存大小限制
        
    Example:
        >>> manager = PaperManager("papers.db")
        >>> paper = manager.get_paper(123)
        >>> manager.update_paper_status(123, "read")
    """
    
    def __init__(self, database_path: str, cache_size: int = 1000):
        """初始化论文管理器。
        
        Args:
            database_path: SQLite数据库文件路径
            cache_size: 论文缓存的最大数量
        """
        pass
```

## 测试

### 测试文件结构

```
tests/
├── unit/                   # 单元测试
│   ├── test_paper_manager.py
│   ├── test_deepseek_analyzer.py
│   └── test_exceptions.py
├── integration/            # 集成测试
│   ├── test_api_endpoints.py
│   └── test_database.py
├── fixtures/               # 测试数据
│   ├── sample_papers.json
│   └── test_config.yaml
└── conftest.py            # pytest配置
```

### 测试代码示例

```python
import pytest
from unittest.mock import Mock, patch
from common.exceptions import PaperNotFoundError
from services.paper_manager import PaperManager

class TestPaperManager:
    """论文管理器测试类"""
    
    @pytest.fixture
    def paper_manager(self):
        """创建测试用的论文管理器"""
        return PaperManager(":memory:")  # 使用内存数据库
    
    @pytest.fixture
    def sample_paper(self):
        """示例论文数据"""
        return {
            "id": 1,
            "title": "Test Paper",
            "abstract": "This is a test paper",
            "status": "unread"
        }
    
    def test_get_existing_paper(self, paper_manager, sample_paper):
        """测试获取存在的论文"""
        # 准备数据
        paper_manager._papers[1] = sample_paper
        
        # 执行测试
        result = paper_manager.get_paper(1)
        
        # 验证结果
        assert result is not None
        assert result["title"] == "Test Paper"
        assert result["status"] == "unread"
    
    def test_get_nonexistent_paper(self, paper_manager):
        """测试获取不存在的论文"""
        with pytest.raises(PaperNotFoundError) as exc_info:
            paper_manager.get_paper(999)
        
        assert exc_info.value.entity_id == 999
    
    @patch('services.paper_manager.requests.get')
    def test_update_feed_success(self, mock_get, paper_manager):
        """测试成功更新订阅源"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = [{"title": "New Paper"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 执行测试
        result = paper_manager.update_feed(1)
        
        # 验证结果
        assert result["success"] is True
        assert result["new_papers"] >= 0
```

## 配置管理

### 配置文件结构

```yaml
# config.yaml
database:
  path: "papers.db"
  max_connections: 10
  timeout: 30

logging:
  level: "INFO"
  file_enabled: true
  log_dir: "data/logs"

api:
  deepseek_api_key: null  # 从环境变量获取
  request_timeout: 60
  max_retries: 3

development:
  debug: true
  host: "localhost"
  port: 5000

production:
  debug: false
  host: "0.0.0.0"
  port: 5000
```

### 配置使用示例

```python
from common.config import load_app_config, Environment

# 加载配置
config = load_app_config(
    config_files=["config.yaml"],
    environment=Environment.DEVELOPMENT
)

# 使用配置
database_path = config.database.path
api_key = config.api.deepseek_api_key
log_level = config.logging.level
```

## 安全最佳实践

### 1. 敏感信息处理

```python
# 好的做法：从环境变量获取
import os
from common.config import get_app_config

config = get_app_config()
api_key = config.api.deepseek_api_key

# 避免的做法：硬编码敏感信息
API_KEY = "sk-1234567890abcdef"  # 不要这样做
```

### 2. 输入验证

```python
from common.exceptions import ValidationError

def create_paper(self, paper_data: Dict[str, Any]) -> APIResponse:
    """创建论文，包含输入验证"""
    
    # 验证必需字段
    required_fields = ["title", "feed_id"]
    for field in required_fields:
        if not paper_data.get(field):
            raise ValidationError(
                field=field,
                message=f"Field '{field}' is required"
            )
    
    # 验证数据类型
    if not isinstance(paper_data["feed_id"], int):
        raise ValidationError(
            field="feed_id",
            message="feed_id must be an integer",
            value=paper_data["feed_id"]
        )
    
    # 验证数据长度
    title = paper_data["title"]
    if len(title) > 500:
        raise ValidationError(
            field="title",
            message="Title too long (max 500 characters)",
            value=len(title)
        )
```

### 3. SQL注入防护

```python
# 好的做法：使用参数化查询
def get_papers_by_status(self, status: str) -> List[PaperDict]:
    query = "SELECT * FROM papers WHERE status = ?"
    return self.database.execute_query(query, (status,))

# 避免的做法：字符串拼接
def get_papers_by_status_bad(self, status: str) -> List[PaperDict]:
    query = f"SELECT * FROM papers WHERE status = '{status}'"  # 危险！
    return self.database.execute_query(query)
```

## 代码审查清单

### 提交前检查

- [ ] 代码通过所有测试
- [ ] 添加了适当的类型注解
- [ ] 包含错误处理
- [ ] 添加了日志记录
- [ ] 写了文档注释
- [ ] 没有硬编码的敏感信息
- [ ] 通过了代码格式化检查
- [ ] 通过了静态分析检查

### 代码审查要点

- [ ] 代码逻辑清晰易懂
- [ ] 函数职责单一
- [ ] 异常处理适当
- [ ] 性能考虑合理
- [ ] 安全性没有问题
- [ ] 测试覆盖充分
- [ ] 文档更新同步

## 工具配置

### 开发环境设置

```bash
# 安装开发依赖
pip install -e .[dev]

# 安装pre-commit钩子
pre-commit install

# 运行代码格式化
black .
isort .

# 运行类型检查
mypy .

# 运行代码检查
flake8 .
pylint .

# 运行测试
pytest tests/ -v --cov=.

# 运行安全检查
bandit -r .
python scripts/check_secrets.py
```

这个代码风格指南应该作为团队开发的标准参考，定期更新以反映项目的演进和最佳实践的发展。