# 新订阅管理系统设计文档

## 概述

本文档描述了DoResearch项目的新订阅管理系统设计方案。该系统旨在替换现有的自由URL订阅模式，改为基于管理员维护的预定义订阅模板，用户通过参数化配置进行订阅。

## 设计目标

1. **管理员可控**：由管理员维护订阅源的底层实现
2. **用户友好**：用户只需选择模板并提供简单参数
3. **微服务架构**：信息抓取独立为外部微服务
4. **数据丰富**：抓取的信息比现有系统更全面
5. **向下兼容**：与现有功能并行，不影响当前使用

## 整体架构

```
外部微服务（独立仓库）：
┌─────────────────────────────────┐
│    Paper Fetcher Service       │
│  统一的论文抓取微服务            │
│                                │
│  - IEEE 适配器                 │
│  - Elsevier 适配器             │  
│  - DBLP 适配器                 │
│  - 统一返回格式                │
└─────────────────────────────────┘

当前仓库（DoResearch后端）：
┌─────────────────────────────────┐
│       DoResearch Backend        │
│                                │
│  新增API：                      │
│  - 订阅模板管理API              │
│  - 用户订阅管理API              │
│  - 同步调度API                 │
│                                │
│  新增数据表：                   │
│  - subscription_templates      │
│  - user_subscriptions         │
│  - subscription_sync_history   │
└─────────────────────────────────┘

前端仓库（独立）：
┌─────────────────────────────────┐
│       Frontend Repository       │
│                                │
│  - 订阅管理界面                 │
│  - 管理员配置界面               │
└─────────────────────────────────┘
```

## 数据库设计

### 新增数据表

#### subscription_templates（订阅模板表）
管理员维护的订阅源模板定义

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 模板ID |
| name | TEXT NOT NULL | 模板名称（如"IEEE期刊订阅"） |
| source_type | TEXT NOT NULL | 订阅类型：ieee, elsevier, dblp |
| description | TEXT | 模板描述 |
| parameter_schema | TEXT NOT NULL | JSON Schema格式的参数定义 |
| example_params | TEXT | 示例参数 |
| active | BOOLEAN DEFAULT 1 | 是否可用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### user_subscriptions（用户订阅表）
用户基于模板创建的具体订阅

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 订阅ID |
| user_id | INTEGER NOT NULL | 用户ID，外键关联users表 |
| template_id | INTEGER NOT NULL | 模板ID，外键关联subscription_templates |
| name | TEXT NOT NULL | 用户自定义订阅名称 |
| source_params | TEXT NOT NULL | JSON格式的订阅参数 |
| status | TEXT DEFAULT 'active' | 状态：active, paused, error |
| sync_frequency | INTEGER DEFAULT 3600 | 同步频率（秒） |
| last_sync_at | TIMESTAMP | 最后同步时间 |
| next_sync_at | TIMESTAMP | 下次同步时间 |
| error_message | TEXT | 最后的错误信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### subscription_sync_history（同步历史表）
记录每次同步的详细信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 历史记录ID |
| subscription_id | INTEGER NOT NULL | 订阅ID，外键 |
| sync_started_at | TIMESTAMP NOT NULL | 同步开始时间 |
| sync_completed_at | TIMESTAMP | 同步完成时间 |
| status | TEXT NOT NULL | 同步状态：success, error, running |
| papers_found | INTEGER DEFAULT 0 | 找到的论文数 |
| papers_new | INTEGER DEFAULT 0 | 新增的论文数 |
| error_details | TEXT | 错误详情 |
| external_service_response | TEXT | 外部服务响应数据 |

## 外部微服务接口规范

### Paper Fetcher Service API

#### 基础接口
```
GET /api/v1/health - 健康检查
GET /api/v1/sources - 获取支持的数据源列表
POST /api/v1/fetch - 获取论文数据
```

#### 请求格式
```json
{
  "source": "ieee|elsevier|dblp",
  "source_params": {
    // IEEE期刊: {"pnumber": "5962382"}
    // Elsevier期刊: {"pnumber": "0164-1212"} 
    // DBLP会议: {"dblp_id": "icse", "year": 2024}
  }
}
```

#### 统一响应格式
```json
{
  "success": true,
  "data": {
    "papers": [...],
    "total_count": 100,
    "has_more": false,
    "next_cursor": "eyJ..."
  },
  "source_info": {
    "source": "ieee",
    "query_executed": "...",
    "execution_time_ms": 1500
  }
}
```

#### 论文数据标准格式
```json
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
    "ieee_number": "123456",
    "scopus_id": "789",
    "dblp_key": "conf/icse/2024"
  },
  "metadata": {
    "conference": "会议名",
    "volume": "卷号", 
    "pages": "1-10",
    "year": 2024
  }
}
```

### 抓取策略
- **IEEE期刊**：抓取最新的N篇论文（如最近50篇）
- **Elsevier期刊**：抓取最新的N篇论文
- **DBLP会议**：抓取指定年份会议的所有论文

## DoResearch后端API设计

### 管理员API
```
GET /api/admin/subscription-templates        # 获取所有模板
POST /api/admin/subscription-templates       # 创建模板
PUT /api/admin/subscription-templates/{id}   # 更新模板
DELETE /api/admin/subscription-templates/{id} # 删除模板
GET /api/admin/external-service/health       # 检查外部服务状态
```

### 用户API（v2版本）
```
GET /api/v2/subscription-templates           # 获取可用订阅模板
POST /api/v2/subscriptions                  # 创建新订阅
GET /api/v2/subscriptions                   # 获取用户订阅列表
PUT /api/v2/subscriptions/{id}              # 更新订阅配置
DELETE /api/v2/subscriptions/{id}           # 删除订阅
POST /api/v2/subscriptions/{id}/sync        # 手动触发同步
GET /api/v2/subscriptions/{id}/history      # 获取同步历史
GET /api/v2/subscriptions/{id}/papers       # 获取该订阅的论文列表
```

## 预定义订阅模板

### IEEE期刊订阅
```json
{
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
```

### Elsevier期刊订阅
```json
{
  "name": "Elsevier期刊订阅",
  "source_type": "elsevier",
  "description": "订阅Elsevier期刊最新论文",
  "parameter_schema": {
    "type": "object",
    "required": ["pnumber"],
    "properties": {
      "pnumber": {
        "type": "string",
        "description": "Elsevier期刊的ISSN或期刊ID"
      }
    }
  },
  "example_params": {"pnumber": "0164-1212"}
}
```

### DBLP会议订阅
```json
{
  "name": "DBLP会议订阅",
  "source_type": "dblp",
  "description": "订阅DBLP会议论文（获取指定年份的所有论文）",
  "parameter_schema": {
    "type": "object",
    "required": ["dblp_id", "year"],
    "properties": {
      "dblp_id": {
        "type": "string",
        "description": "DBLP会议ID，如icse、nips、aaai等"
      },
      "year": {
        "type": "integer",
        "minimum": 2000,
        "maximum": 2030,
        "description": "会议年份（必填）"
      }
    }
  },
  "example_params": {"dblp_id": "icse", "year": 2024}
}
```

## 同步机制设计

### 同步行为差异

#### 期刊类订阅（IEEE、Elsevier）
- **同步频率**：建议每日或每周同步
- **增量更新**：每次获取最新论文，系统自动去重
- **数据特点**：持续有新论文发表

#### 会议类订阅（DBLP）
- **同步频率**：会议结束后一次性同步，或年度同步
- **全量获取**：获取该年份会议的所有论文
- **数据特点**：某个时间点后数据相对稳定

### 调度策略
- 基于用户设置的sync_frequency定期同步
- 支持手动触发同步
- 错误重试机制和退避策略
- 调用外部Paper Fetcher Service
- 使用现有hash机制进行去重
- 将结果存储到现有papers表

## 与现有系统集成

### 数据整合
- 新订阅获取的论文存入现有papers表
- 在papers表中增加字段标识数据来源（subscription_id）
- 现有API（如GET /api/feeds/{id}/papers）自动包含新订阅的论文

### 兼容性策略
- 现有feeds功能保持不变，与新系统并行运行
- 新v2 API与现有API并存
- 统计功能自动包含两种数据源
- 用户界面提供两种订阅方式的选择

### 迁移路径
1. **第一阶段**：部署新系统，与现有系统并行
2. **第二阶段**：用户逐步迁移到新订阅方式
3. **第三阶段**：在确认稳定后，可选择性废弃旧系统

## 用户使用流程

### 用户订阅流程
1. 浏览可用的订阅模板
2. 选择合适的模板（如"IEEE期刊订阅"）
3. 填写必要参数（如IEEE期刊的pnumber）
4. 设置同步频率
5. 创建订阅，系统自动开始定期同步

### 管理员配置流程
1. 定义新的订阅模板
2. 配置参数模式（JSON Schema）
3. 测试外部服务连接
4. 发布模板供用户使用
5. 监控订阅状态和错误日志

## 实现优势

1. **可控性**：管理员统一维护订阅源，确保数据质量
2. **用户友好**：简化用户配置，只需提供关键参数
3. **扩展性**：微服务架构便于添加新的数据源
4. **标准化**：统一的数据格式和接口规范
5. **监控性**：完整的同步历史和错误追踪
6. **兼容性**：与现有系统平滑共存
7. **性能**：专业的抓取服务，数据更全面准确

## 技术栈

- **后端**：Python Flask（现有技术栈）
- **数据库**：SQLite（现有数据库）
- **外部服务**：独立的Paper Fetcher微服务
- **数据格式**：JSON Schema用于参数验证
- **API风格**：RESTful API设计