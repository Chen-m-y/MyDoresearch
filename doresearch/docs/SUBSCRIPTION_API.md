# 新订阅管理系统 API 文档

## 概述

新的订阅管理系统提供基于模板的订阅功能，支持IEEE、Elsevier、DBLP等数据源的自动化论文获取。

## 认证

所有API都需要用户认证。请在请求头中包含有效的认证信息。

## 用户API (v2)

### 获取订阅模板列表

**GET** `/api/v2/subscription-templates`

获取所有可用的订阅模板。

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "IEEE期刊订阅",
      "source_type": "ieee",
      "description": "订阅IEEE期刊最新论文（自动获取最新发表的论文）",
      "parameter_schema": {
        "type": "object",
        "required": ["pnumber"],
        "properties": {
          "pnumber": {
            "type": "string",
            "description": "IEEE期刊的publication number",
            "pattern": "^[0-9]+$"
          }
        }
      },
      "example_params": {"pnumber": "5962382"}
    }
  ]
}
```

### 获取单个订阅模板

**GET** `/api/v2/subscription-templates/{template_id}`

获取指定模板的详细信息。

### 创建订阅

**POST** `/api/v2/subscriptions`

基于模板创建新订阅。

**请求体：**
```json
{
  "template_id": 1,
  "name": "我的IEEE Computer Society订阅",
  "source_params": {
    "pnumber": "5962382"
  }
}
```

**响应示例：**
```json
{
  "success": true,
  "subscription_id": 123
}
```

### 获取用户订阅列表

**GET** `/api/v2/subscriptions`

获取当前用户的所有订阅。

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "name": "我的IEEE Computer Society订阅",
      "source_params": {"pnumber": "5962382"},
      "status": "active",
      "sync_frequency": 86400,
      "last_sync_at": "2024-01-15T10:00:00",
      "next_sync_at": "2024-01-16T10:00:00",
      "template_name": "IEEE期刊订阅",
      "source_type": "ieee",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### 获取订阅详情

**GET** `/api/v2/subscriptions/{subscription_id}`

获取指定订阅的详细信息。

### 更新订阅

**PUT** `/api/v2/subscriptions/{subscription_id}`

更新订阅配置。

**请求体：**
```json
{
  "name": "新的订阅名称",
  "source_params": {"pnumber": "1234567"},
  "sync_frequency": 43200,
  "status": "active"
}
```

### 删除订阅

**DELETE** `/api/v2/subscriptions/{subscription_id}`

删除指定的订阅。

### 手动同步

**POST** `/api/v2/subscriptions/{subscription_id}/sync`

手动触发订阅同步。

**响应示例：**
```json
{
  "success": true,
  "message": "同步已完成"
}
```

### 获取同步历史

**GET** `/api/v2/subscriptions/{subscription_id}/history`

获取订阅的同步历史记录。

**查询参数：**
- `limit`: 返回记录数量限制（默认20，最大100）

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "sync_started_at": "2024-01-15T10:00:00",
      "sync_completed_at": "2024-01-15T10:02:30",
      "status": "success",
      "papers_found": 25,
      "papers_new": 5,
      "error_details": null
    }
  ]
}
```

### 获取订阅的论文

**GET** `/api/v2/subscriptions/{subscription_id}/papers`

获取通过该订阅获取的论文列表。

**查询参数：**
- `status`: 论文状态过滤 (`all`, `read`, `unread`, `reading`)
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认20，最大100）

**响应示例：**
```json
{
  "success": true,
  "data": {
    "papers": [
      {
        "id": 1,
        "title": "论文标题",
        "abstract": "论文摘要",
        "authors": "作者1, 作者2",
        "journal": "期刊名称",
        "published_date": "2024-01-01",
        "url": "论文链接",
        "status": "unread",
        "created_at": "2024-01-15T10:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

## 管理员API

### 获取所有模板（管理员）

**GET** `/api/admin/subscription-templates`

获取所有订阅模板，包括已禁用的。

### 创建模板

**POST** `/api/admin/subscription-templates`

创建新的订阅模板。

**请求体：**
```json
{
  "name": "新期刊订阅",
  "source_type": "custom",
  "description": "自定义期刊订阅",
  "parameter_schema": {
    "type": "object",
    "required": ["journal_id"],
    "properties": {
      "journal_id": {
        "type": "string",
        "description": "期刊ID"
      }
    }
  },
  "example_params": {"journal_id": "example-journal"}
}
```

### 更新模板

**PUT** `/api/admin/subscription-templates/{template_id}`

更新指定的订阅模板。

### 删除模板

**DELETE** `/api/admin/subscription-templates/{template_id}`

删除（禁用）指定的订阅模板。

### 检查外部服务状态

**GET** `/api/admin/external-service/health`

检查外部Paper Fetcher微服务的健康状态。

**响应示例：**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": "2 days, 3 hours"
  }
}
```

### 获取支持的数据源

**GET** `/api/admin/external-service/sources`

获取外部服务支持的数据源列表。

### 获取订阅统计

**GET** `/api/admin/subscriptions/stats`

获取系统的订阅统计信息。

**响应示例：**
```json
{
  "success": true,
  "data": {
    "total_subscriptions": 150,
    "active_subscriptions": 120,
    "by_source_type": {
      "ieee": 80,
      "elsevier": 30,
      "dblp": 10
    },
    "by_status": {
      "active": 120,
      "paused": 20,
      "error": 10
    },
    "syncs_last_24h": 45,
    "success_rate": 95.2
  }
}
```

## 错误处理

所有API都使用标准的HTTP状态码和统一的错误响应格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

常见状态码：
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 外部微服务接口

### 论文获取接口

**POST** `{PAPER_FETCHER_SERVICE_URL}/api/v1/fetch`

**请求体：**
```json
{
  "source": "ieee|elsevier|dblp",
  "source_params": {
    "pnumber": "5962382"
  }
}
```

**响应格式：**
```json
{
  "success": true,
  "data": {
    "papers": [
      {
        "title": "论文标题",
        "abstract": "论文摘要",
        "authors": ["作者1", "作者2"],
        "journal": "期刊名称",
        "published_date": "2024-01-01",
        "url": "论文链接",
        "pdf_url": "PDF链接",
        "doi": "DOI编号",
        "keywords": ["关键词1", "关键词2"],
        "citations": 10,
        "source_specific": {
          "ieee_number": "123456"
        },
        "metadata": {
          "volume": "Vol. 50",
          "pages": "1-10"
        }
      }
    ],
    "total_count": 100,
    "has_more": false
  },
  "source_info": {
    "source": "ieee",
    "execution_time_ms": 1500
  }
}
```

## 配置选项

### 环境变量

- `PAPER_FETCHER_SERVICE_URL`: 外部服务URL（默认: http://localhost:8000）
- `SYNC_CHECK_INTERVAL`: 同步检查间隔秒数（默认: 60）
- `DEFAULT_SYNC_FREQ`: 默认同步频率秒数（默认: 86400）
- `MAX_SUBSCRIPTIONS_PER_USER`: 每用户最大订阅数（默认: 50）

### 源类型配置

系统预定义了三种主要的源类型：

1. **IEEE期刊** (`ieee`)
   - 参数: `punumber` (IEEE publication number) ⚠️ 已更新
   - 同步策略: 获取最新论文，建议每日同步
   - 示例: `{"punumber": "32"}`
   - 测试状态: ✅ 已验证（成功获取33篇IEEE TSE论文）

2. **Elsevier期刊** (`elsevier`) 
   - 参数: `pnumber` (ISSN或期刊ID)
   - 同步策略: 获取最新论文，建议每日同步
   - 示例: `{"pnumber": "0164-1212"}`
   - 测试状态: ⏳ 待验证

3. **DBLP会议** (`dblp`)
   - 参数: `dblp_id` (会议ID), `year` (年份)
   - 同步策略: 获取指定年份所有论文，建议每周同步
   - 示例: `{"dblp_id": "icse", "year": 2024}`
   - 测试状态: ⏳ 待验证

## 系统集成状态

✅ **生产就绪** (2025-08-13)
- **微服务连接**: http://192.168.1.135:8000 正常工作
- **IEEE抓取**: 成功获取33篇IEEE TSE论文，数据完整
- **自动同步**: 完整的创建→同步→存储流程正常
- **API接口**: 所有用户和管理员API已验证
- **数据库**: 升级完成，兼容现有系统

## 重要提醒

⚠️ **参数名称更新**: IEEE模板参数已从`pnumber`更新为`punumber`以匹配微服务接口。如有现有代码引用，请及时更新。