# DoResearch 环境变量配置说明

## 🌍 环境变量列表

### 核心系统配置
```bash
# DeepSeek API密钥（用于AI分析功能）
DEEPSEEK_API_KEY=sk-your-api-key-here

# 数据库文件路径
DATABASE_PATH=papers.db
```

### 外部微服务配置
```bash
# 论文抓取微服务地址
PAPER_FETCHER_SERVICE_URL=http://192.168.1.135:8000

# 微服务连接超时时间（秒）
PAPER_FETCHER_TIMEOUT=30

# 微服务请求重试次数
PAPER_FETCHER_RETRY=3

# 重试间隔延迟（秒）
PAPER_FETCHER_RETRY_DELAY=2.0
```

### 订阅同步配置
```bash
# 同步检查间隔（秒）
SYNC_CHECK_INTERVAL=60

# 每次处理的订阅数量
SYNC_BATCH_SIZE=10

# 同步最大重试次数
SYNC_MAX_RETRY=3

# 默认同步频率（秒，24小时）
DEFAULT_SYNC_FREQ=86400
```

### 订阅限制配置
```bash
# 每用户最大订阅数量
MAX_SUBSCRIPTIONS_PER_USER=50

# 最高同步频率（秒，最快1小时）
MAX_SYNC_FREQUENCY=3600

# 最低同步频率（秒，最慢24小时）
MIN_SYNC_FREQUENCY=86400
```

### 验证和安全配置
```bash
# 严格验证模式
VALIDATION_STRICT_MODE=true

# 是否允许额外属性
ALLOW_ADDITIONAL_PROPERTIES=false
```

### 日志配置
```bash
# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# 是否记录同步详细信息
LOG_SYNC_DETAILS=true

# 是否记录外部请求详情
LOG_EXTERNAL_REQUESTS=false
```

## 🚀 部署示例

### 开发环境
```bash
export PAPER_FETCHER_SERVICE_URL=http://localhost:8000
export LOG_LEVEL=DEBUG
export LOG_SYNC_DETAILS=true
export SYNC_CHECK_INTERVAL=30
```

### 生产环境
```bash
export PAPER_FETCHER_SERVICE_URL=http://192.168.1.135:8000
export LOG_LEVEL=INFO
export LOG_SYNC_DETAILS=false
export SYNC_CHECK_INTERVAL=60
export MAX_SUBSCRIPTIONS_PER_USER=100
```

### Docker部署
```dockerfile
ENV PAPER_FETCHER_SERVICE_URL=http://paper-fetcher:8000
ENV DATABASE_PATH=/data/papers.db
ENV LOG_LEVEL=INFO
ENV SYNC_CHECK_INTERVAL=60
```

## 📋 配置优先级

1. **环境变量** (最高优先级)
2. **配置文件默认值** (configs/subscription_config.py)
3. **主配置文件备用值** (config.py)

## 🔧 配置验证

运行以下命令验证配置：

```bash
# 测试配置加载
python3 -c "from config import EXTERNAL_SERVICE_CONFIG; print(EXTERNAL_SERVICE_CONFIG)"

# 测试订阅配置
python3 -c "from configs.subscription_config import get_external_service_config; print(get_external_service_config())"
```