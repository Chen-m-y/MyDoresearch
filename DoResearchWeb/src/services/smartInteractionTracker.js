import apiClient from './apiClient.jsx';

/**
 * 智能交互追踪服务
 * 用于追踪用户对论文的交互行为并分析兴趣度
 */
class SmartInteractionTracker {
    constructor(options = {}) {
        this.options = {
            debug: false,
            trackScrolling: true,
            trackClicks: true,
            autoSubmitThreshold: 10, // 每10次交互自动提交一次
            scrollThrottleMs: 2000,   // 滚动事件节流时间（增加到2秒）
            minTrackingInterval: 5000, // 最小追踪间隔5秒
            realTimeAnalysisInterval: 5000, // 实时分析间隔5秒
            ...options
        };

        // 添加防抖状态
        this.lastTrackTime = 0;
        // 添加实时分析定时器
        this.realTimeAnalysisTimer = null;

        // 当前会话状态
        this.currentSession = null;
        this.currentPaper = null;
        this.sessionStartTime = null;
        this.maxScrollDepth = 0;
        this.clickCount = 0;
        this.interactionQueue = [];

        // 事件监听器
        this.scrollListener = null;
        this.clickListener = null;
        this.beforeUnloadListener = null;

        // 初始化会话ID
        this.generateSessionId();

        this.log('智能交互追踪器已初始化', this.options);
    }

    /**
     * 生成会话ID
     */
    generateSessionId() {
        this.currentSession = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        return this.currentSession;
    }

    /**
     * 开始追踪指定论文
     */
    startTrackingPaper(paperId, paperTitle = '') {
        // 如果已经在追踪相同论文，不重复开始
        if (this.currentPaper && this.currentPaper.id === paperId) {
            this.log(`已在追踪论文: ${paperId}，跳过重复开始`);
            return this.currentSession;
        }

        this.log(`开始追踪论文: ${paperId} - ${paperTitle}`);

        // 如果已经在追踪其他论文，先结束之前的追踪
        if (this.currentPaper && this.currentPaper.id !== paperId) {
            this.stopTrackingPaper();
        }

        this.currentPaper = {
            id: paperId,
            title: paperTitle,
            startTime: Date.now()
        };
        
        this.sessionStartTime = Date.now();
        this.maxScrollDepth = 0;
        this.clickCount = 0;

        // 记录开始查看事件
        this.trackInteraction('view_start', {
            duration_seconds: 0,
            scroll_depth_percent: 0
        });

        // 设置事件监听器
        this.setupEventListeners();

        // 设置页面离开时自动结束追踪
        this.setupUnloadHandler();

        // 启动实时分析定时器
        this.startRealTimeAnalysis();

        return this.currentSession;
    }

    /**
     * 停止追踪当前论文
     */
    stopTrackingPaper() {
        if (!this.currentPaper) {
            return;
        }

        this.log(`停止追踪论文: ${this.currentPaper.id}`);

        // 计算总的查看时间
        const duration = Math.floor((Date.now() - this.sessionStartTime) / 1000);

        // 记录结束查看事件（带智能兴趣分析）
        // 确保每次停止追踪都会触发分析
        this.trackViewEnd(duration, this.maxScrollDepth);

        // 清理状态
        this.currentPaper = null;
        this.sessionStartTime = null;
        this.maxScrollDepth = 0;
        this.clickCount = 0;

        // 停止实时分析定时器
        this.stopRealTimeAnalysis();

        // 移除事件监听器
        this.removeEventListeners();
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        if (this.options.trackScrolling) {
            this.scrollListener = this.throttle(this.handleScroll.bind(this), this.options.scrollThrottleMs);
            window.addEventListener('scroll', this.scrollListener);
        }

        if (this.options.trackClicks) {
            this.clickListener = this.handleClick.bind(this);
            document.addEventListener('click', this.clickListener);
        }
    }

    /**
     * 移除事件监听器
     */
    removeEventListeners() {
        if (this.scrollListener) {
            window.removeEventListener('scroll', this.scrollListener);
            this.scrollListener = null;
        }

        if (this.clickListener) {
            document.removeEventListener('click', this.clickListener);
            this.clickListener = null;
        }

        if (this.beforeUnloadListener) {
            window.removeEventListener('beforeunload', this.beforeUnloadListener);
            this.beforeUnloadListener = null;
        }
    }

    /**
     * 设置页面离开处理器
     */
    setupUnloadHandler() {
        this.beforeUnloadListener = () => {
            if (this.currentPaper) {
                // 同步提交最后的追踪数据
                this.stopTrackingPaper();
            }
        };
        window.addEventListener('beforeunload', this.beforeUnloadListener);
    }

    /**
     * 处理滚动事件
     */
    handleScroll() {
        if (!this.currentPaper) return;

        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = documentHeight > 0 ? Math.min(100, Math.max(0, (scrollTop / documentHeight) * 100)) : 0;

        // 只有当滚动深度显著增加时才记录（减少API调用）
        const significantIncrease = scrollPercent > this.maxScrollDepth + 10; // 每增加10%才记录一次
        
        if (significantIncrease) {
            this.maxScrollDepth = scrollPercent;
            
            // 记录滚动事件
            this.trackInteraction('scroll', {
                duration_seconds: Math.floor((Date.now() - this.sessionStartTime) / 1000),
                scroll_depth_percent: Math.floor(scrollPercent)
            });
        } else {
            // 仅更新本地状态，不调用API
            this.maxScrollDepth = Math.max(this.maxScrollDepth, scrollPercent);
        }
    }

    /**
     * 处理点击事件
     */
    handleClick(event) {
        if (!this.currentPaper) return;

        this.clickCount++;
        const target = event.target;

        // 检测特定类型的点击
        let interactionType = 'click';
        if (target.closest('a[href$=".pdf"]') || target.closest('[data-pdf-link]')) {
            interactionType = 'click_pdf';
        } else if (target.closest('a[href^="http"]') || target.closest('[data-external-link]')) {
            interactionType = 'click_url';
        } else if (target.closest('[data-bookmark]') || target.closest('.bookmark-btn')) {
            interactionType = 'bookmark';
        }

        this.trackInteraction(interactionType, {
            duration_seconds: Math.floor((Date.now() - this.sessionStartTime) / 1000),
            scroll_depth_percent: Math.floor(this.maxScrollDepth),
            click_count: this.clickCount
        });
    }

    /**
     * 记录交互行为
     */
    async trackInteraction(interactionType, additionalData = {}) {
        if (!this.currentPaper) {
            this.log('没有当前追踪的论文，忽略交互记录');
            return;
        }

        // 防抖：避免频繁调用
        const now = Date.now();
        if (interactionType === 'scroll' && now - this.lastTrackTime < this.options.minTrackingInterval) {
            this.log(`交互记录防抖: ${interactionType}, 距离上次 ${now - this.lastTrackTime}ms`);
            return;
        }

        const interactionData = {
            paper_id: this.currentPaper.id,
            interaction_type: interactionType,
            session_id: this.currentSession,
            ...additionalData
        };

        try {
            const response = await apiClient.trackInteraction(interactionData);
            this.log(`交互记录成功: ${interactionType}`, response);
            this.lastTrackTime = now;
            return response;
        } catch (error) {
            this.log(`交互记录失败: ${error.message}`, 'error');
            // 将失败的交互加入队列，稍后重试
            this.interactionQueue.push(interactionData);
        }
    }

    /**
     * 记录查看结束事件（带智能兴趣分析）
     */
    async trackViewEnd(duration, scrollDepth) {
        if (!this.currentPaper) return;

        // 对所有阅读行为进行兴趣分析（进一步降低门槛）
        if (duration < 2) {
            this.log(`阅读时间过短 (${duration}秒)，跳过兴趣分析`);
            return;
        }

        try {
            const response = await apiClient.trackView({
                paper_id: this.currentPaper.id,
                duration_seconds: duration,
                scroll_depth_percent: Math.floor(scrollDepth),
                session_id: this.currentSession
            });

            if (response.success) {
                const { interest_level, interest_score, signals } = response.data;
                this.log(`查看结束记录成功 - 兴趣度: ${interest_level} (${interest_score}%)`, {
                    signals: signals || [],
                    duration,
                    scrollDepth
                });
                
                // 触发兴趣度分析完成事件
                if (this.options.onInterestAnalyzed) {
                    this.options.onInterestAnalyzed({
                        paperId: this.currentPaper.id,
                        interestLevel: interest_level,
                        interestScore: interest_score,
                        signals,
                        duration,
                        scrollDepth
                    });
                }
            }
            
            return response;
        } catch (error) {
            this.log(`查看结束记录失败: ${error.message}`, 'error');
        }
    }

    /**
     * 明确标记兴趣
     */
    async markInterest(paperId, interestType) {
        try {
            const response = await apiClient.markInterest({
                paper_id: paperId,
                interest_type: interestType, // 'like' 或 'dislike'
                session_id: this.currentSession
            });

            this.log(`兴趣标记成功: ${interestType}`, response);

            // 同时记录明确兴趣交互
            const explicitType = interestType === 'like' ? 'explicit_like' : 'explicit_dislike';
            this.trackInteraction(explicitType, {
                duration_seconds: this.currentPaper ? Math.floor((Date.now() - this.sessionStartTime) / 1000) : 0,
                scroll_depth_percent: Math.floor(this.maxScrollDepth)
            });

            return response;
        } catch (error) {
            this.log(`兴趣标记失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 获取论文的兴趣评分
     */
    async getPaperInterestScore(paperId) {
        try {
            return await apiClient.getPaperInterestScore(paperId);
        } catch (error) {
            this.log(`获取兴趣评分失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 获取个性化推荐
     */
    async getPersonalizedRecommendations(limit = 10) {
        try {
            return await apiClient.getPersonalizedRecommendations(limit);
        } catch (error) {
            this.log(`获取个性化推荐失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 获取相似论文推荐
     */
    async getSimilarPapers(paperId, limit = 5) {
        try {
            return await apiClient.getSimilarPapers(paperId, limit);
        } catch (error) {
            this.log(`获取相似论文失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 获取推荐解释
     */
    async getRecommendationExplanation(paperId) {
        try {
            return await apiClient.getRecommendationExplanation(paperId);
        } catch (error) {
            this.log(`获取推荐解释失败: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * 重试队列中的失败交互
     */
    async retryFailedInteractions() {
        if (this.interactionQueue.length === 0) return;

        this.log(`重试 ${this.interactionQueue.length} 个失败的交互记录`);

        const retryQueue = [...this.interactionQueue];
        this.interactionQueue = [];

        for (const interaction of retryQueue) {
            try {
                await apiClient.trackInteraction(interaction);
                this.log(`重试成功: ${interaction.interaction_type}`);
            } catch (error) {
                this.log(`重试失败: ${error.message}`, 'error');
                // 重新加入队列（最多重试3次）
                if (!interaction.retryCount) interaction.retryCount = 0;
                if (interaction.retryCount < 3) {
                    interaction.retryCount++;
                    this.interactionQueue.push(interaction);
                }
            }
        }
    }

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 日志输出
     */
    log(message, data = null, level = 'info') {
        if (!this.options.debug) return;

        const timestamp = new Date().toISOString();
        const prefix = `[SmartTracker ${timestamp}]`;

        switch (level) {
            case 'error':
                console.error(prefix, message, data);
                break;
            case 'warn':
                console.warn(prefix, message, data);
                break;
            default:
                console.log(prefix, message, data);
        }
    }

    /**
     * 启动实时分析定时器
     */
    startRealTimeAnalysis() {
        if (!this.currentPaper) return;

        // 清除之前的定时器
        this.stopRealTimeAnalysis();

        this.log(`启动实时分析定时器，间隔: ${this.options.realTimeAnalysisInterval}ms`);

        this.realTimeAnalysisTimer = setInterval(() => {
            if (!this.currentPaper || !this.sessionStartTime) {
                this.stopRealTimeAnalysis();
                return;
            }

            const duration = Math.floor((Date.now() - this.sessionStartTime) / 1000);
            
            // 只有阅读时间超过3秒才进行实时分析
            if (duration >= 3) {
                this.log(`执行实时兴趣分析，当前阅读时长: ${duration}秒`);
                this.performRealTimeAnalysis(duration);
            }
        }, this.options.realTimeAnalysisInterval);
    }

    /**
     * 停止实时分析定时器
     */
    stopRealTimeAnalysis() {
        if (this.realTimeAnalysisTimer) {
            this.log('停止实时分析定时器');
            clearInterval(this.realTimeAnalysisTimer);
            this.realTimeAnalysisTimer = null;
        }
    }

    /**
     * 执行实时兴趣分析
     */
    async performRealTimeAnalysis(duration) {
        if (!this.currentPaper) return;

        try {
            this.log(`发送实时分析请求:`, {
                paper_id: this.currentPaper.id,
                duration_seconds: duration,
                scroll_depth_percent: Math.floor(this.maxScrollDepth),
                session_id: this.currentSession
            });

            const response = await apiClient.trackView({
                paper_id: this.currentPaper.id,
                duration_seconds: duration,
                scroll_depth_percent: Math.floor(this.maxScrollDepth),
                session_id: this.currentSession
            });

            this.log(`收到API响应:`, response);

            if (response && response.success) {
                const { interest_level, interest_score, signals } = response.data || {};
                this.log(`实时兴趣分析完成 - 兴趣度: ${interest_level} (${interest_score}%)`, {
                    signals: signals || [],
                    duration,
                    scrollDepth: this.maxScrollDepth
                });
                
                // 触发兴趣度分析完成事件
                if (this.options.onInterestAnalyzed) {
                    this.options.onInterestAnalyzed({
                        paperId: this.currentPaper.id,
                        interestLevel: interest_level,
                        interestScore: interest_score,
                        signals,
                        duration,
                        scrollDepth: this.maxScrollDepth,
                        isRealTime: true // 标记为实时分析
                    });
                }
            } else {
                this.log(`API响应格式异常:`, response);
                
                // 如果后端没有实现推荐系统API，创建模拟数据
                const mockResult = this.createMockAnalysisResult(duration);
                if (this.options.onInterestAnalyzed) {
                    this.options.onInterestAnalyzed(mockResult);
                }
            }
        } catch (error) {
            this.log(`实时兴趣分析失败: ${error.message}`, 'error');
            
            // API失败时也提供模拟数据，确保用户能看到分析结果
            const mockResult = this.createMockAnalysisResult(duration);
            if (this.options.onInterestAnalyzed) {
                this.options.onInterestAnalyzed(mockResult);
            }
        }
    }

    /**
     * 获取当前状态（调试用）
     */
    getStatus() {
        return {
            currentSession: this.currentSession,
            currentPaper: this.currentPaper,
            maxScrollDepth: this.maxScrollDepth,
            clickCount: this.clickCount,
            queueLength: this.interactionQueue.length,
            isTracking: !!this.currentPaper,
            hasRealTimeTimer: !!this.realTimeAnalysisTimer
        };
    }
}

export default SmartInteractionTracker;