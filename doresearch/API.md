# DoResearch API 文档

## 概览

DoResearch 是一个研究论文管理系统，提供论文搜索、阅读状态跟踪、稍后阅读、统计分析和分布式下载等功能。

**基础信息:**
- 基础URL: `http://localhost:5000`
- 数据格式: JSON
- 字符编码: UTF-8
- 无需身份验证

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {
    // 具体数据内容
  }
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误描述信息"
}
```

## 分页支持

DoResearch API 在多个论文列表端点中提供分页支持，以提高性能和用户体验。

### 通用分页参数
- `page`: 页码，从1开始 (默认: 1)
- `per_page`: 每页数量 (默认: 20, 最大: 100)

### 分页响应格式
所有支持分页的端点都会返回以下格式：

```json
{
  "papers": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_prev": false,
    "has_next": true
  }
}
```

### 支持分页的端点
- `GET /api/feeds/{feed_id}/papers` - 论文源的论文列表
- `GET /api/papers/by-status-change` - 按状态变化时间的论文列表
- `GET /api/search` - 搜索结果 (使用limit/offset)
- `GET /api/read-later` - 稍后阅读列表 (使用limit/offset)

## 核心 API 接口

### 1. 系统状态

#### 健康检查
```
GET /api/health
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-03T10:30:00Z",
  "services": {
    "database": "ok",
    "translator": "ok",
    "task_processor": "ok",
    "paper_manager": "ok",
    "statistics_service": "ok",
    "sse_manager": "ok",
    "task_service": "ok"
  }
}
```

### 2. 论文源管理

#### 获取所有论文源
```
GET /api/feeds
```

**响应示例:**
```json
[
  {
    "id": 1,
    "name": "IEEE Computer Society",
    "url": "https://ieeexplore.ieee.org/rss/TOC123.XML",
    "journal": "IEEE Computer",
    "created_at": "2025-01-01T00:00:00Z",
    "last_updated": "2025-08-03T10:00:00Z",
    "active": true
  }
]
```

#### 添加论文源
```
POST /api/feeds
Content-Type: application/json

{
  "name": "论文源名称",
  "url": "RSS订阅URL",
  "journal": "期刊名称"
}
```

#### 更新论文源
```
POST /api/feeds/{feed_id}/update
```

#### 获取指定订阅的论文列表
```
GET /api/feeds/{feed_id}/papers?status=unread&page=1&per_page=20
```

**查询参数:**
- `status`: 论文状态 (unread, reading, read)
- `page`: 页码 (默认1)
- `per_page`: 每页数量 (默认20，最大100)

**响应示例:**
```json
{
  "papers": [
    {
      "id": 123,
      "title": "论文标题",
      "abstract": "摘要内容",
      "authors": "作者列表",
      "journal": "期刊名称",
      "published_date": "2025-08-01",
      "status": "unread",
      "url": "https://example.com/paper"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_prev": false,
    "has_next": true
  }
}
```

### 3. 论文管理

#### 获取论文详情
```
GET /api/papers/{paper_id}?feed_id={feed_id}
```

**响应示例:**
```json
{
  "id": 123,
  "title": "论文标题",
  "abstract": "摘要内容",
  "abstract_cn": "中文摘要",
  "authors": "作者1, 作者2",
  "journal": "期刊名称",
  "published_date": "2025-08-01",
  "url": "https://example.com/paper",
  "doi": "10.1109/example.2025.123456",
  "status": "unread",
  "pdf_url": "https://example.com/paper.pdf",
  "pdf_path": "/data/pdfs/paper123.pdf",
  "created_at": "2025-08-03T10:00:00Z",
  "navigation": {
    "prev_paper_id": 122,
    "next_paper_id": 124
  }
}
```

#### 更新论文状态
```
PUT /api/papers/{paper_id}/status
Content-Type: application/json

{
  "status": "read"
}
```

**支持的状态:**
- `unread`: 未读
- `reading`: 正在阅读
- `read`: 已读

#### 翻译论文摘要
```
POST /api/papers/{paper_id}/translate
```

#### 获取论文状态变化历史
```
GET /api/papers/{paper_id}/status-history
```

#### 根据状态变化时间获取论文列表
```
GET /api/papers/by-status-change?start_time=2025-08-01&end_time=2025-08-03&page=1&per_page=20
```

**查询参数:**
- `start_time`: 开始时间 (ISO格式)
- `end_time`: 结束时间 (ISO格式)
- `page`: 页码 (默认1)
- `per_page`: 每页数量 (默认20，最大100)

**响应示例:**
```json
{
  "papers": [
    {
      "id": 123,
      "title": "论文标题",
      "status": "read",
      "status_changed_at": "2025-08-02T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3,
    "has_prev": false,
    "has_next": true
  }
}
```

### 4. 搜索功能

#### 基础搜索
```
GET /api/search?q=关键词&fields=title,abstract&status=unread&limit=20&offset=0
```

**查询参数:**
- `q`: 搜索关键词 (必需)
- `fields`: 搜索字段 (title, abstract, abstract_cn, authors, journal, doi)
- `status`: 论文状态过滤
- `journal`: 期刊过滤
- `feed_id`: 论文源过滤
- `start_date`, `end_date`: 日期范围
- `has_pdf`: 是否有PDF (true/false)
- `has_analysis`: 是否有分析 (true/false)
- `limit`: 每页数量 (默认20，最大100)
- `offset`: 偏移量
- `order_by`: 排序方式 (relevance, date, title, created_at)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "query": "machine learning",
    "results": [
      {
        "id": 123,
        "title": "论文标题",
        "authors": "作者列表",
        "journal": "期刊名称",
        "published_date": "2025-08-01",
        "status": "unread",
        "url": "https://example.com/paper",
        "relevance_score": 0.95,
        "highlights": {
          "title": ["machine <mark>learning</mark>"],
          "abstract": ["深度<mark>学习</mark>算法"]
        }
      }
    ],
    "pagination": {
      "total_count": 150,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

#### 高级搜索
```
POST /api/search/advanced
Content-Type: application/json

{
  "query": "deep learning",
  "search_fields": ["title", "abstract"],
  "status": "unread",
  "journal": "IEEE",
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-08-03"
  },
  "has_pdf": true,
  "limit": 20,
  "offset": 0,
  "order_by": "relevance"
}
```

#### 搜索建议
```
GET /api/search/suggestions?q=机器&limit=10
```

#### 热门搜索
```
GET /api/search/popular?limit=10
```

#### 快速搜索
```
GET /api/search/quick?q=关键词
```

#### 搜索过滤选项
```
GET /api/search/filters
```

#### 查找相似论文
```
GET /api/search/similar/{paper_id}
```

#### 导出搜索结果
```
GET /api/search/export?q=关键词&format=json
```

**支持格式:**
- `json`: JSON格式
- `csv`: CSV格式

#### 搜索统计
```
GET /api/search/stats
```

### 5. 稍后阅读

#### 标记稍后阅读
```
POST /api/read-later
Content-Type: application/json

{
  "paper_id": 123,
  "priority": 5,
  "notes": "重要论文，需要详细阅读",
  "tags": ["machine-learning", "deep-learning"],
  "estimated_read_time": 30
}
```

**参数说明:**
- `paper_id`: 论文ID (必需)
- `priority`: 优先级 1-10 (默认5)
- `notes`: 备注
- `tags`: 标签数组
- `estimated_read_time`: 预计阅读时间(分钟)

#### 快速添加稍后阅读
```
POST /api/read-later/quick-add
Content-Type: application/json

{
  "paper_id": 123
}
```

#### 获取稍后阅读列表
```
GET /api/read-later?order_by=priority&limit=20&offset=0
```

**查询参数:**
- `order_by`: 排序方式 (priority, marked_at, title, published_date)
- `limit`: 每页数量
- `offset`: 偏移量

#### 更新稍后阅读信息
```
PUT /api/read-later/{paper_id}
Content-Type: application/json

{
  "priority": 8,
  "notes": "更新后的备注",
  "tags": ["updated-tag"],
  "estimated_read_time": 45
}
```

#### 取消稍后阅读
```
DELETE /api/read-later/{paper_id}
```

#### 检查稍后阅读状态
```
GET /api/read-later/{paper_id}/check
```

#### 搜索稍后阅读
```
GET /api/read-later/search?q=关键词&search_in=title,notes
```

#### 批量操作
```
POST /api/read-later/bulk-update
Content-Type: application/json

{
  "action": "update_priority",
  "paper_ids": [123, 124, 125],
  "priority": 8
}
```

**支持的操作:**
- `update_priority`: 批量更新优先级
- `remove`: 批量移除

#### 稍后阅读统计
```
GET /api/read-later/stats
```

#### 导出稍后阅读列表
```
GET /api/read-later/export?format=json
```

#### 获取优先级选项
```
GET /api/read-later/priorities
```

### 6. 统计分析

#### 快速统计
```
GET /api/statistics/quick
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "total_papers": 1250,
    "read_papers": 345,
    "unread_papers": 805,
    "reading_papers": 100,
    "reading_streak_days": 15,
    "total_feeds": 8,
    "active_feeds": 6
  }
}
```

#### 详细统计概览
```
GET /api/statistics/overview
```

#### 统计汇总(6个核心指标)
```
GET /api/statistics/summary
```

#### 阅读日历
```
GET /api/statistics/calendar?year=2025
```

#### 阅读趋势
```
GET /api/statistics/trends?days=90
```

#### 仪表盘数据
```
GET /api/statistics/dashboard
```

#### 快捷统计接口
```
GET /api/stats
```

### 7. 任务管理

#### 获取任务列表
```
GET /api/tasks?status=pending&task_type=pdf_download_only&limit=100&include_steps=false
```

**查询参数:**
- `status`: 任务状态筛选 (`pending`, `in_progress`, `completed`, `failed`, `cancelled`)
- `task_type`: 任务类型筛选 (`pdf_download_only`, `full_analysis`, `deep_analysis`, `translation`)
- `limit`: 返回数量限制 (默认100)
- `include_steps`: 是否包含任务步骤详情 (默认true)

**响应示例 (enhanced):**
```json
[
  {
    "id": "uuid-string",
    "paper_id": 123,
    "task_type": "pdf_download_only",
    "task_type_desc": "仅下载PDF",
    "task_type_icon": "📥",
    "status": "pending",
    "priority": 5,
    "created_at": "2025-08-07T10:00:00Z",
    "title": "论文标题",
    "ieee_article_number": "9123456",
    "metadata": {
      "article_number": "9123456",
      "download_method": "agent",
      "task_description": "仅下载PDF文件"
    },
    "steps": [...] // 或 "steps_count": 1 (当include_steps=false时)
  }
]
```

#### 获取任务详情
```
GET /api/tasks/{task_id}
```

#### 创建分析任务
```
POST /api/papers/{paper_id}/analyze
Content-Type: application/json

{
  "priority": 5
}
```

#### 获取论文分析结果
```
GET /api/papers/{paper_id}/analysis
```

#### 取消任务
```
POST /api/tasks/{task_id}/cancel
```

#### 创建完整分析任务（下载PDF + AI分析）
```
POST /api/tasks/analysis
Content-Type: application/json

{
  "paper_id": 123,
  "priority": 5
}
```

**响应示例:**
```json
{
  "success": true,
  "task_id": "uuid-string",
  "task_type": "full_analysis",
  "paper_id": 123,
  "message": "完整分析任务创建成功"
}
```

#### 任务统计
```
GET /api/tasks/stats
```

### 8. SSE 和 Agent 管理

#### Agent注册
```
POST /api/agent/register
Content-Type: application/json

{
  "agent_id": "ieee-agent-001",
  "name": "IEEE下载器",
  "capabilities": ["ieee_download", "pdf_download"]
}
```

#### SSE事件流 (Agent使用)
```
GET /api/agent/{agent_id}/events
```

**SSE事件类型:**
- `connected`: 连接确认
- `task`: 新任务
- `heartbeat`: 心跳
- `error`: 错误信息
- `disconnect`: 连接断开

#### 提交任务结果
```
POST /api/agent/task-result
Content-Type: application/json

{
  "task_id": "uuid-string",
  "result": {
    "pdf_path": "/data/pdfs/paper123.pdf",
    "file_size": 1024000
  },
  "success": true
}
```

#### SSE系统状态
```
GET /api/sse/status
```

#### 活跃Agent列表
```
GET /api/sse/agents
```

#### Agent状态
```
GET /api/agents/status
```

### 9. 下载服务

#### 同步下载IEEE论文
```
POST /api/download/ieee
Content-Type: application/json

{
  "article_number": "9123456"
}
```

#### 异步下载任务
```
POST /api/download/async
Content-Type: application/json

{
  "paper_id": 123,
  "article_number": "9123456"
}
```

#### 创建PDF下载任务（仅下载）
```
POST /api/download/pdf
Content-Type: application/json

{
  "paper_id": 123,
  "article_number": "9123456",
  "priority": 5
}
```

**响应示例:**
```json
{
  "success": true,
  "task_id": "uuid-string",
  "task_type": "pdf_download_only",
  "paper_id": 123,
  "message": "PDF下载任务创建成功"
}
```

#### 测试下载
```
POST /api/sse/test-download
Content-Type: application/json

{
  "article_number": "9123456"
}
```

### 10. 文件下载

#### 下载PDF文件
```
GET /data/pdfs/{filename}
```

## 错误代码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用示例

### Python 客户端示例

```python
import requests
import json

class DoResearchClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search_papers(self, query, limit=20):
        """搜索论文"""
        response = self.session.get(
            f"{self.base_url}/api/search",
            params={"q": query, "limit": limit}
        )
        return response.json()
    
    def mark_read_later(self, paper_id, priority=5, notes=None):
        """标记稍后阅读"""
        data = {
            "paper_id": paper_id,
            "priority": priority
        }
        if notes:
            data["notes"] = notes
            
        response = self.session.post(
            f"{self.base_url}/api/read-later",
            json=data
        )
        return response.json()
    
    def get_statistics(self):
        """获取统计信息"""
        response = self.session.get(f"{self.base_url}/api/stats")
        return response.json()

# 使用示例
client = DoResearchClient()

# 搜索论文
results = client.search_papers("machine learning", limit=10)
print(f"找到 {results['data']['pagination']['total_count']} 篇论文")

# 标记第一篇论文为稍后阅读
if results['data']['results']:
    paper = results['data']['results'][0]
    client.mark_read_later(paper['id'], priority=8, notes="重要论文")

# 获取统计信息
stats = client.get_statistics()
print(f"总共 {stats['data']['total_papers']} 篇论文")
```

### JavaScript 客户端示例

```javascript
class DoResearchAPI {
    constructor(baseURL = 'http://localhost:5000') {
        this.baseURL = baseURL;
    }
    
    async searchPapers(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            limit: options.limit || 20,
            ...options
        });
        
        const response = await fetch(`${this.baseURL}/api/search?${params}`);
        return response.json();
    }
    
    async markReadLater(paperId, options = {}) {
        const response = await fetch(`${this.baseURL}/api/read-later`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paper_id: paperId,
                priority: options.priority || 5,
                notes: options.notes,
                tags: options.tags
            })
        });
        return response.json();
    }
    
    async getStatistics() {
        const response = await fetch(`${this.baseURL}/api/stats`);
        return response.json();
    }
}

// 使用示例
const api = new DoResearchAPI();

// 搜索并显示结果
api.searchPapers('deep learning', { limit: 5 })
    .then(result => {
        console.log(`找到 ${result.data.pagination.total_count} 篇论文`);
        result.data.results.forEach(paper => {
            console.log(`- ${paper.title}`);
        });
    });
```

## 部署和配置

### 环境要求
- Python 3.8+
- SQLite 3
- DeepSeek API Key

### 启动服务
```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

### 配置文件
主要配置在 `config.py` 中：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `DATABASE_PATH`: 数据库路径
- `PDF_DIR`: PDF存储目录
- `TASK_CHECK_INTERVAL`: 任务检查间隔

## 注意事项

1. **并发限制**: 搜索API有并发限制，建议控制请求频率
2. **文件大小**: PDF文件下载可能较大，注意网络超时设置
3. **SSE连接**: Agent SSE连接会自动重连，但建议实现客户端重连逻辑
4. **数据备份**: 定期备份SQLite数据库文件
5. **API密钥**: 确保DeepSeek API密钥安全存储

## 更新日志

- v1.0: 初始版本，包含基础论文管理功能
- v1.1: 增加搜索和统计功能
- v1.2: 增加稍后阅读和任务队列
- v1.3: 增加SSE支持和分布式Agent系统