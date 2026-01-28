/**
 * 智能交互追踪JavaScript库
 * 自动追踪用户与论文的交互行为，为推荐系统提供数据
 */
class SmartInteractionTracker {
    constructor(options = {}) {
        this.apiBase = options.apiBase || '/api';
        this.sessionId = this.generateSessionId();
        this.currentPaper = null;
        this.startTime = null;
        this.maxScrollDepth = 0;
        this.isTracking = false;
        this.debounceDelay = options.debounceDelay || 1000;
        
        // 配置选项
        this.trackScrolling = options.trackScrolling !== false;
        this.trackClicks = options.trackClicks !== false;
        this.trackTime = options.trackTime !== false;
        this.debug = options.debug || false;
        
        this.log('SmartInteractionTracker 已初始化', { sessionId: this.sessionId });
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    log(message, data = null) {
        if (this.debug) {
            console.log(`[SmartTracker] ${message}`, data || '');
        }
    }
    
    /**
     * 开始追踪论文查看
     */
    startTrackingPaper(paperId, paperTitle = '') {
        if (this.isTracking && this.currentPaper === paperId) {
            return; // 已经在追踪这篇论文
        }
        
        // 如果正在追踪其他论文，先结束之前的追踪
        if (this.isTracking) {
            this.endTrackingPaper();
        }
        
        this.currentPaper = paperId;
        this.startTime = Date.now();
        this.maxScrollDepth = 0;
        this.isTracking = true;
        
        this.log('开始追踪论文', { paperId, paperTitle });
        
        // 记录开始查看事件
        this.trackInteraction('view_start');
        
        // 设置事件监听器
        if (this.trackScrolling) {
            this.setupScrollTracking();
        }
        
        if (this.trackClicks) {
            this.setupClickTracking();
        }
        
        // 页面关闭时自动结束追踪
        window.addEventListener('beforeunload', () => this.endTrackingPaper());
        window.addEventListener('pagehide', () => this.endTrackingPaper());
    }
    
    /**
     * 结束追踪论文查看
     */
    endTrackingPaper() {
        if (!this.isTracking || !this.currentPaper) {
            return;
        }
        
        const duration = Math.floor((Date.now() - this.startTime) / 1000);
        
        this.log('结束追踪论文', { 
            paperId: this.currentPaper, 
            duration, 
            maxScrollDepth: this.maxScrollDepth 
        });
        
        // 发送查看结束事件（带分析）
        this.trackPaperView(duration, this.maxScrollDepth);
        
        // 清理状态
        this.isTracking = false;
        this.currentPaper = null;
        this.startTime = null;
        this.maxScrollDepth = 0;
        
        // 移除事件监听器
        this.cleanupEventListeners();
    }
    
    /**
     * 设置滚动追踪
     */
    setupScrollTracking() {
        this.scrollHandler = this.debounce(() => {
            if (!this.isTracking) return;
            
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            const scrollDepth = Math.min(100, Math.floor((scrollTop + windowHeight) / documentHeight * 100));
            
            if (scrollDepth > this.maxScrollDepth) {
                this.maxScrollDepth = scrollDepth;
                
                // 记录重要的滚动里程碑
                if (scrollDepth >= 25 && scrollDepth % 25 === 0) {
                    this.trackInteraction('scroll', 0, scrollDepth);
                }
            }
        }, this.debounceDelay);
        
        window.addEventListener('scroll', this.scrollHandler, { passive: true });
    }
    
    /**
     * 设置点击追踪
     */
    setupClickTracking() {
        this.clickHandler = (event) => {
            if (!this.isTracking) return;
            
            const target = event.target;
            const href = target.getAttribute('href') || target.closest('a')?.getAttribute('href');
            
            if (href) {
                // PDF链接点击
                if (href.includes('.pdf') || href.includes('/pdf/') || href.includes('pdf_url')) {
                    this.trackInteraction('click_pdf');
                    this.log('检测到PDF点击', { href });
                }
                // 论文URL点击
                else if (href.includes('ieeexplore.ieee.org') || href.includes('arxiv.org') || 
                         href.includes('doi.org') || target.closest('.paper-url')) {
                    this.trackInteraction('click_url');
                    this.log('检测到论文URL点击', { href });
                }
            }
            
            // 稍后阅读按钮点击
            if (target.closest('.bookmark-btn') || target.closest('[data-action="bookmark"]')) {
                this.trackInteraction('bookmark');
                this.log('检测到收藏操作');
            }
        };
        
        document.addEventListener('click', this.clickHandler, true);
    }
    
    /**
     * 清理事件监听器
     */
    cleanupEventListeners() {
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler);
            this.scrollHandler = null;
        }
        
        if (this.clickHandler) {
            document.removeEventListener('click', this.clickHandler, true);
            this.clickHandler = null;
        }
    }
    
    /**
     * 记录通用交互事件
     */
    async trackInteraction(interactionType, duration = 0, scrollDepth = 0, clickCount = 0) {
        if (!this.currentPaper) return;
        
        const data = {
            paper_id: this.currentPaper,
            interaction_type: interactionType,
            duration_seconds: duration,
            scroll_depth_percent: scrollDepth,
            click_count: clickCount,
            session_id: this.sessionId
        };
        
        try {
            const response = await fetch(`${this.apiBase}/interactions/track`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.log('交互记录成功', { interactionType, data });
            
        } catch (error) {
            console.warn('记录交互失败:', error);
        }
    }
    
    /**
     * 记录论文查看行为（带智能分析）
     */
    async trackPaperView(duration, scrollDepth) {
        if (!this.currentPaper) return;
        
        const data = {
            paper_id: this.currentPaper,
            duration_seconds: duration,
            scroll_depth_percent: scrollDepth,
            session_id: this.sessionId
        };
        
        try {
            const response = await fetch(`${this.apiBase}/interactions/track-view`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.log('论文查看记录成功', result.data);
                
                // 可以在这里处理兴趣分析结果
                this.onInterestAnalyzed(result.data);
            }
            
        } catch (error) {
            console.warn('记录论文查看失败:', error);
        }
    }
    
    /**
     * 明确标记对论文的兴趣
     */
    async markInterest(paperId, interestType) {
        const data = {
            paper_id: paperId,
            interest_type: interestType, // 'like' or 'dislike'
            session_id: this.sessionId
        };
        
        try {
            const response = await fetch(`${this.apiBase}/interactions/mark-interest`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.log('兴趣标记成功', result);
            
            return result;
            
        } catch (error) {
            console.warn('标记兴趣失败:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 获取个性化推荐
     */
    async getPersonalizedRecommendations(limit = 10) {
        try {
            const response = await fetch(`${this.apiBase}/recommendations/personalized?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.log('获取个性化推荐成功', result);
            
            return result;
            
        } catch (error) {
            console.warn('获取推荐失败:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 获取相似论文推荐
     */
    async getSimilarPapers(paperId, limit = 5) {
        try {
            const response = await fetch(`${this.apiBase}/recommendations/similar/${paperId}?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.log('获取相似论文成功', result);
            
            return result;
            
        } catch (error) {
            console.warn('获取相似论文失败:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 兴趣分析完成回调（可被重写）
     */
    onInterestAnalyzed(analysisResult) {
        // 默认实现：可以在这里添加UI反馈
        if (analysisResult.interest_level === 'high' || analysisResult.interest_level === 'very_high') {
            console.log('检测到高兴趣度论文，可以显示相关推荐');
        }
    }
    
    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * 销毁追踪器
     */
    destroy() {
        this.endTrackingPaper();
        this.cleanupEventListeners();
        this.log('SmartInteractionTracker 已销毁');
    }
}

// 导出到全局对象（如果不使用模块系统）
if (typeof window !== 'undefined') {
    window.SmartInteractionTracker = SmartInteractionTracker;
}

// 如果支持模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SmartInteractionTracker;
}

/**
 * 使用示例：
 * 
 * // 初始化追踪器
 * const tracker = new SmartInteractionTracker({
 *     debug: true,
 *     trackScrolling: true,
 *     trackClicks: true
 * });
 * 
 * // 开始追踪论文
 * tracker.startTrackingPaper(123, 'Paper Title');
 * 
 * // 明确标记兴趣
 * tracker.markInterest(123, 'like');
 * 
 * // 获取推荐
 * const recommendations = await tracker.getPersonalizedRecommendations(10);
 * 
 * // 页面离开时会自动结束追踪
 */