# 🤖 智能推荐系统文档

DoResearch项目的智能推荐系统，基于用户实际行为（而非简单的读/未读状态）进行个性化推荐。

## 🎯 系统特点

### 解决的核心问题
- **传统问题**：用户为了确认文章内容会点开查看，导致所有文章都被标记为"已读"，无法区分真正的兴趣
- **我们的解决方案**：基于多维度行为数据（浏览时长、滚动深度、点击行为等）智能评估用户兴趣

### 核心优势
- ✅ **智能兴趣评估**：区分"随便看看"和"真正感兴趣"
- ✅ **多维度数据**：时间、滚动、点击、收藏等综合分析
- ✅ **个性化推荐**：基于实际行为模式，不是简单的关键词匹配
- ✅ **实时学习**：用户行为越多，推荐越精准
- ✅ **隐私友好**：所有数据本地存储，不上传个人信息

## 🏗️ 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   前端追踪库     │───▶│   交互追踪服务    │───▶│   数据库存储     │
│ SmartTracker.js │    │InteractionTracker│    │ paper_interactions│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   推荐API接口    │◀───│  行为分析引擎     │◀───│ 兴趣评分计算     │
│   /api/rec/*    │    │BehaviorRecommender│    │paper_interest_scores│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 数据库设计

### 1. paper_interactions - 交互记录表
```sql
CREATE TABLE paper_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL,  -- 'view_start', 'view_end', 'scroll', 'click_pdf' etc.
    duration_seconds INTEGER DEFAULT 0,
    scroll_depth_percent INTEGER DEFAULT 0,  -- 0-100
    click_count INTEGER DEFAULT 0,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. paper_interest_scores - 兴趣评分表
```sql
CREATE TABLE paper_interest_scores (
    paper_id INTEGER PRIMARY KEY,
    interest_score INTEGER DEFAULT 0,     -- 0-100综合兴趣分数
    interaction_count INTEGER DEFAULT 0,  -- 交互次数
    total_view_time INTEGER DEFAULT 0,    -- 总查看时间
    max_scroll_depth INTEGER DEFAULT 0,   -- 最大滚动深度
    explicit_interest INTEGER DEFAULT 0,  -- 1:喜欢, -1:不喜欢, 0:中性
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. user_interest_patterns - 用户兴趣模式表
```sql
CREATE TABLE user_interest_patterns (
    pattern_type TEXT NOT NULL,      -- 'keyword', 'author', 'journal'
    pattern_value TEXT NOT NULL,     -- 具体的关键词/作者/期刊名
    interest_strength REAL DEFAULT 0.0,  -- 0.0-1.0 兴趣强度
    occurrence_count INTEGER DEFAULT 0,   -- 出现次数
    UNIQUE(pattern_type, pattern_value)
);
```

## 🚀 快速开始

### 1. 数据库迁移
```bash
# 运行迁移脚本添加推荐系统表
python scripts/migrate_recommendation_tables.py
```

### 2. 前端集成
```html
<!-- 引入智能追踪库 -->
<script src="/static/js/smart-interaction-tracker.js"></script>

<script>
// 初始化追踪器
const tracker = new SmartInteractionTracker({
    debug: true,  // 开发模式
    trackScrolling: true,
    trackClicks: true
});

// 在论文详情页开始追踪
tracker.startTrackingPaper(paperId, paperTitle);

// 用户明确表示兴趣时
document.getElementById('like-btn').onclick = () => {
    tracker.markInterest(paperId, 'like');
};

// 获取个性化推荐
async function loadRecommendations() {
    const result = await tracker.getPersonalizedRecommendations(10);
    if (result.success) {
        displayRecommendations(result.data.recommendations);
    }
}
</script>
```

### 3. 后端API使用
```python
from services.interaction_tracker import InteractionTracker
from services.behavior_based_recommender import BehaviorBasedRecommender

# 初始化服务
tracker = InteractionTracker()
recommender = BehaviorBasedRecommender()

# 记录用户交互
tracker.track_paper_view(paper_id=123, duration_seconds=180, scroll_depth_percent=85)

# 获取个性化推荐
recommendations = recommender.get_personalized_recommendations(limit=10)

# 查找相似论文
similar_papers = recommender.find_similar_papers(paper_id=123, limit=5)
```

## 📡 API接口详情

### 交互追踪接口

#### POST /api/interactions/track
记录用户交互行为
```json
{
    "paper_id": 123,
    "interaction_type": "view_end",
    "duration_seconds": 120,
    "scroll_depth_percent": 75,
    "session_id": "session_xxx"
}
```

#### POST /api/interactions/track-view
记录论文查看（带智能分析）
```json
{
    "paper_id": 123,
    "duration_seconds": 180,
    "scroll_depth_percent": 85,
    "session_id": "session_xxx"
}
```

响应示例：
```json
{
    "success": true,
    "data": {
        "paper_id": 123,
        "interest_level": "high",
        "interest_score": 78,
        "signals": ["深度阅读 (2-5分钟)", "详细查看内容"]
    }
}
```

### 推荐系统接口

#### GET /api/recommendations/personalized
获取个性化推荐
```json
{
    "success": true,
    "data": {
        "recommendations": [
            {
                "id": 456,
                "title": "Recommended Paper Title",
                "recommendation_score": 0.85,
                "matched_features": ["关键词: machine learning", "作者: John Smith"],
                "keyword_matches": 3,
                "author_matches": 1
            }
        ],
        "count": 10
    }
}
```

#### GET /api/recommendations/similar/{paper_id}
获取相似论文推荐
```json
{
    "success": true,
    "data": {
        "target_paper_id": 123,
        "similar_papers": [
            {
                "id": 789,
                "title": "Similar Paper Title",
                "similarity_score": 0.72,
                "keyword_matches": 5
            }
        ]
    }
}
```

#### POST /api/interactions/mark-interest
明确标记兴趣
```json
{
    "paper_id": 123,
    "interest_type": "like"  // 'like' or 'dislike'
}
```

## 🧠 智能算法详解

### 1. 兴趣评分算法
```python
def calculate_interest_score(interactions):
    score = 0
    
    # 基于浏览时间 (30% 权重)
    if duration < 10:      score -= 5   # 快速跳过
    elif duration < 30:    score += 5   # 简单浏览
    elif duration < 120:   score += 15  # 中等关注
    elif duration < 300:   score += 25  # 深度阅读
    else:                  score += 35  # 长时间研究
    
    # 基于滚动深度 (20% 权重)
    if scroll_depth < 20:  score -= 2   # 仅看标题
    elif scroll_depth < 50: score += 5  # 浏览摘要
    elif scroll_depth < 80: score += 12 # 详细查看
    else:                   score += 18 # 完整浏览
    
    # 基于行为权重 (50% 权重)
    action_weights = {
        'bookmark': +20,      # 收藏
        'click_pdf': +15,     # 点击PDF
        'explicit_like': +25, # 明确喜欢
        'explicit_dislike': -25  # 明确不喜欢
    }
    
    return max(0, min(100, score))
```

### 2. 个性化推荐算法
```python
def get_personalized_recommendations():
    # 1. 分析用户兴趣模式
    user_patterns = analyze_user_patterns()
    
    # 2. 筛选候选论文（只选择未读的）
    candidates = get_unread_papers()
    
    # 3. 提取特征权重
    keywords = user_patterns['keywords']    # 70%权重
    authors = user_patterns['authors']      # 20%权重  
    journals = user_patterns['journals']    # 10%权重
    
    # 4. 计算候选论文匹配分数
    for candidate in candidates:
        score = 0
        score += keyword_match_score * 0.7
        score += author_match_score * 0.2
        score += journal_match_score * 0.1
        
        # 5. 新鲜度加成（越新的文章权重越高）
        freshness_bonus = calculate_freshness_bonus(candidate.date)
        score += freshness_bonus  # 最高+0.3分
        
    # 6. 过滤已交互论文，返回Top-N
    return filter_and_rank(scored_candidates)
```

## 📈 性能监控

### 统计接口
- `GET /api/interactions/stats` - 交互统计
- `GET /api/interactions/user-patterns` - 兴趣模式分析
- `GET /api/recommendations/dashboard` - 推荐系统仪表板

### 性能指标
- **数据收集率**：用户交互记录成功率
- **推荐准确率**：用户对推荐内容的实际兴趣度
- **系统响应时间**：推荐算法执行速度
- **用户参与度**：明确标记兴趣的比例

## 🔧 配置选项

### InteractionTracker配置
```python
# services/interaction_tracker.py
INTEREST_WEIGHTS = {
    'VIEW_START': 1,
    'SCROLL': 2,
    'CLICK_PDF': 10,
    'BOOKMARK': 15,
    'EXPLICIT_LIKE': 20,
    'EXPLICIT_DISLIKE': -20,
}
```

### 推荐算法配置
```python
# services/behavior_based_recommender.py
MIN_INTEREST_SCORE = 50      # 最低兴趣阈值
SIMILARITY_THRESHOLD = 0.3   # 相似度阈值
MAX_RECOMMENDATIONS = 20     # 最大推荐数量
```

### 前端追踪配置
```javascript
const tracker = new SmartInteractionTracker({
    apiBase: '/api',           // API基础路径
    debounceDelay: 1000,      // 防抖延迟
    trackScrolling: true,      // 是否追踪滚动
    trackClicks: true,         // 是否追踪点击
    debug: false              // 调试模式
});
```

## 🚨 注意事项

### 数据隐私
- 所有交互数据本地存储，不上传到外部服务
- 不收集用户个人身份信息
- 支持数据清理和重置功能

### 性能考虑
- 交互数据异步记录，不影响用户体验
- 推荐计算采用缓存机制
- 数据库查询已优化索引

### 兼容性
- 支持现代浏览器（ES6+）
- 渐进式增强，不影响基础功能
- 服务端容错处理，API调用失败不影响主流程

## 🔮 未来规划

- [ ] **深度学习推荐**：集成更先进的机器学习算法
- [ ] **协同过滤**：基于相似用户的推荐
- [ ] **多模态分析**：结合图像、文本等多种特征
- [ ] **实时推荐**：基于当前浏览上下文的即时推荐
- [ ] **A/B测试框架**：推荐算法效果对比测试

## 📞 技术支持

如有问题或建议，请通过以下方式联系：
- 在项目Issue中提出问题
- 查看代码注释了解详细实现
- 参考测试用例了解使用方法

---

*智能推荐系统让论文发现更加精准高效！🎯*