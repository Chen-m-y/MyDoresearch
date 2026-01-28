# Do Research Fetch 微服务

基于 Flask 的学术数据抓取微服务，为 DoResearch 主服务提供统一的学术论文数据和项目申报新闻抓取能力。

## 功能特性

- 支持多个学术数据源（IEEE、Elsevier、DBLP）
- **新增：项目申报新闻订阅**（科技部、自然科学基金委等）
- 统一的API接口和数据格式
- 可扩展的适配器架构
- 完整的错误处理和日志记录
- Docker 部署支持
- Redis 缓存支持
- SQLite 摘要缓存
- 异步任务和进度监控

## 快速开始

### 使用 Docker Compose（推荐）

1. 克隆项目并进入目录：
```bash
cd do_research_fetch
```

2. 复制环境变量配置：
```bash
cp .env.example .env
```

3. 编辑 `.env` 文件，配置必要的 API 密钥：
```bash
IEEE_API_KEY=your_ieee_api_key_here
ELSEVIER_API_KEY=your_elsevier_api_key_here
```

4. 启动服务：
```bash
docker-compose up -d
```

5. 验证服务状态：
```bash
curl http://localhost:8000/api/v1/health
```

### 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量（复制 `.env.example` 为 `.env` 并修改）

3. 启动 Redis（如果需要缓存）：
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

4. 运行应用：
```bash
python app.py
```

## API 接口

### 健康检查

```http
GET /api/v1/health
```

响应示例：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "2 days, 3 hours, 15 minutes",
  "supported_sources": ["ieee"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 获取支持的数据源

```http
GET /api/v1/sources
```

响应示例：
```json
{
  "success": true,
  "data": {
    "total_sources": 5,
    "paper_sources": [
      {
        "name": "ieee",
        "display_name": "IEEE Xplore",
        "description": "IEEE期刊和会议论文",
        "adapter_type": "paper",
        "required_params": ["punumber"],
        "optional_params": ["limit", "early_access", "fetch_full_abstract"]
      }
    ],
    "news_sources": [
      {
        "name": "most",
        "display_name": "国家科技管理信息系统",
        "description": "科技部通知公告，包含国家科技项目申报信息",
        "adapter_type": "news",
        "required_params": [],
        "optional_params": ["limit", "category_filter", "date_from", "date_to"]
      },
      {
        "name": "nsfc",
        "display_name": "国家自然科学基金委员会",
        "description": "自然科学基金项目申报指南、政策通知等信息",
        "adapter_type": "news",
        "required_params": [],
        "optional_params": ["limit", "category_filter", "date_from", "date_to", "news_type"]
      }
    ]
  }
}
```

### 抓取论文数据

```http
POST /api/v1/fetch
Content-Type: application/json

{
  "source": "ieee",
  "source_params": {
    "punumber": "5962382",
    "limit": 50,
    "early_access": true
  }
}
```

### 抓取项目申报新闻

```http
POST /api/v1/fetch/news
Content-Type: application/json

{
  "source": "most",
  "source_params": {
    "limit": 20,
    "category_filter": "funding_announcement",
    "date_from": "2024-01-01"
  }
}
```

响应示例：
```json
{
  "success": true,
  "data": {
    "news": [
      {
        "title": "关于发布国家重点研发计划2024年度项目申报指南的通知",
        "content": "关于发布国家重点研发计划2024年度项目申报指南的通知",
        "summary": "关于发布国家重点研发计划2024年度项目申报指南的通知",
        "source": "most",
        "published_date": "2024-01-15 00:00:00",
        "url": "https://service.most.gov.cn/kjjh_tztg/20240115001.html",
        "category": "funding_announcement",
        "organization": "科技部",
        "priority": "high",
        "status": "active",
        "keywords": ["国家重点研发计划", "申报指南", "项目申请"],
        "deadline": "2024-03-15",
        "funding_amount": "500万元",
        "source_specific": {
          "source_unit": "科技部",
          "news_source": "国家科技管理信息系统"
        }
      }
    ],
    "total_count": 15,
    "has_more": false
  },
  "source_info": {
    "source": "most",
    "execution_time_ms": 1200,
    "cache_hit": false
  }
}
```

#### 新闻分类说明

- `funding_announcement`: 资助公告/项目申报
- `policy_update`: 政策更新/管理办法
- `call_for_proposals`: 征集通知/征求意见
- `results_announcement`: 结果公示/获批名单
- `general_announcement`: 一般通知公告

### 批量抓取

```http
POST /api/v1/fetch/batch
Content-Type: application/json

{
  "requests": [
    {
      "id": "req1",
      "source": "ieee",
      "source_params": {"punumber": "5962382"}
    }
  ]
}
```

## 数据源适配器

### 论文数据源

#### IEEE 适配器

支持通过期刊发布号码（punumber）抓取 IEEE Xplore 的论文数据。

**必需参数：**
- `punumber`: 期刊发布号码

**可选参数：**
- `limit`: 返回结果数量（默认50，最大100）
- `early_access`: 是否获取早期访问文章（默认true）

### 新闻数据源

#### 科技部适配器 (most)

抓取国家科技管理信息系统的通知公告，包含国家科技项目申报信息。

**数据来源：** https://service.most.gov.cn/kjjh_tztg/

**可选参数：**
- `limit`: 返回结果数量（默认20，最大100）
- `category_filter`: 分类过滤（funding_announcement, policy_update等）
- `date_from`: 开始日期（YYYY-MM-DD）
- `date_to`: 结束日期（YYYY-MM-DD）

**支持的新闻类型：**
- 国家重点研发计划申报指南
- 科技项目征集通知
- 政策文件和管理办法
- 项目评审结果公示

#### 自然科学基金委适配器 (nsfc)

抓取国家自然科学基金委员会的项目申报指南、政策通知等信息。

**数据来源：** https://www.nsfc.gov.cn/

**可选参数：**
- `limit`: 返回结果数量（默认20，最大100）
- `category_filter`: 分类过滤
- `date_from`: 开始日期（YYYY-MM-DD）
- `date_to`: 结束日期（YYYY-MM-DD）
- `news_type`: 新闻类型（all, funding, policy, results）

**支持的基金类型：**
- 面上项目
- 重点项目
- 青年科学基金
- 地区科学基金
- 重大研究计划
- 杰出青年科学基金
- 优秀青年科学基金

### 扩展新的数据源

1. 创建新的适配器类，继承 `BaseAdapter`
2. 实现必需的抽象方法
3. 在 `adapters/registry.py` 中注册适配器

示例：
```python
from adapters.base import BaseAdapter, PaperData

class NewSourceAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "new_source"
    
    def fetch_papers(self, params):
        # 实现抓取逻辑
        pass
```

## 配置选项

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `HOST` | 0.0.0.0 | 服务监听地址 |
| `PORT` | 8000 | 服务监听端口 |
| `DEBUG` | false | 调试模式 |
| `IEEE_API_KEY` | - | IEEE API密钥 |
| `REDIS_URL` | redis://localhost:6379 | Redis连接URL |
| `REQUEST_TIMEOUT` | 30 | 请求超时时间（秒） |

完整的配置选项请参考 `.env.example` 文件。

## 数据格式

所有适配器返回的论文数据都遵循统一的格式：

```json
{
  "title": "论文标题",
  "abstract": "摘要",
  "authors": ["作者1", "作者2"],
  "journal": "期刊名称",
  "published_date": "2024-01-15",
  "url": "论文链接",
  "pdf_url": "PDF链接",
  "doi": "DOI",
  "keywords": ["关键词1", "关键词2"],
  "citations": 15,
  "source_specific": {
    "源特有字段": "值"
  },
  "metadata": {
    "额外元数据": "值"
  }
}
```

## 错误处理

API 使用统一的错误格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      "额外信息": "值"
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

常见错误码：
- `INVALID_SOURCE`: 不支持的数据源
- `INVALID_PARAMS`: 参数验证失败
- `RATE_LIMIT_EXCEEDED`: API限流
- `SOURCE_UNAVAILABLE`: 数据源服务不可用

## 开发

### 项目结构

```
do_research_fetch/
├── adapters/           # 数据源适配器
│   ├── __init__.py
│   ├── base.py         # 抽象基类
│   ├── ieee_adapter.py # IEEE适配器
│   └── registry.py     # 适配器注册器
├── utils/              # 工具类
│   ├── __init__.py
│   ├── exceptions.py   # 自定义异常
│   └── response_formatter.py
├── app.py              # Flask 应用
├── config.py           # 配置类
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 日志

应用使用Python标准日志库，日志级别可通过 `LOG_LEVEL` 环境变量控制。

### 测试

```bash
# 安装测试依赖
pip install pytest pytest-cov

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=.
```

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t do-research-fetch .

# 运行容器
docker run -p 8000:8000 \
  -e IEEE_API_KEY=your_key \
  do-research-fetch
```

### 生产环境建议

- 使用反向代理（Nginx）
- 配置 HTTPS
- 设置适当的日志级别
- 监控服务状态和性能
- 配置数据库持久化

## 许可证

MIT License