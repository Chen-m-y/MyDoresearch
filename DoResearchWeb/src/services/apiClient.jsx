import axios from 'axios';

// 获取环境变量的兼容函数
const getEnvVar = (key) => {
    // Vite环境变量 (以VITE_开头)
    if (typeof import.meta !== 'undefined' && import.meta.env) {
        return import.meta.env[key];
    }

    // Create React App环境变量 (需要polyfill)
    if (typeof process !== 'undefined' && process.env) {
        return process.env[key];
    }

    return undefined;
};

// 获取当前环境
const getEnvironment = () => {
    // Vite环境
    if (typeof import.meta !== 'undefined' && import.meta.env) {
        return import.meta.env.MODE || 'development';
    }

    // CRA环境
    if (typeof process !== 'undefined' && process.env) {
        return process.env.NODE_ENV || 'development';
    }

    // 默认为开发环境
    return 'development';
};

// 获取API基础URL
const getApiBaseUrl = () => {
    // 优先使用Vite环境变量
    const viteApiUrl = getEnvVar('VITE_API_BASE_URL');
    if (viteApiUrl) {
        return viteApiUrl;
    }

    // 回退到CRA环境变量
    const craApiUrl = getEnvVar('REACT_APP_API_BASE_URL');
    if (craApiUrl) {
        return craApiUrl;
    }

    // 开发环境默认值
    if (getEnvironment() === 'development') {
        return 'http://localhost:5000';
    }

    // 生产环境默认为相对路径
    return '';
};

// 创建axios实例
const api = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 全局token存储
let currentToken = null;

// 设置当前token的方法
const setAuthToken = (token) => {
    currentToken = token;
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete api.defaults.headers.common['Authorization'];
    }
};

// 获取当前token的方法
const getAuthToken = () => {
    if (currentToken) {
        return currentToken;
    }
    // 如果内存中没有，尝试从localStorage获取
    const token = localStorage.getItem('session_token');
    if (token) {
        setAuthToken(token);
        return token;
    }
    return null;
};

// 初始化时设置token
const initialToken = localStorage.getItem('session_token');
if (initialToken) {
    setAuthToken(initialToken);
}

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        // 确保每次请求都获取最新的token
        const token = getAuthToken();
        
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            delete config.headers.Authorization;
        }
        
        return config;
    },
    (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        // 统一错误处理
        console.error('API Error:', error);

        if (error.response) {
            // 服务器返回的错误状态码
            const { status, data } = error.response;
            console.error(`API Error ${status}:`, data);

            switch (status) {
                case 400:
                    throw new Error(data?.error || '请求参数错误');
                case 401:
                    // 未授权，清除本地token并可能重定向到登录页
                    setAuthToken(null);
                    localStorage.removeItem('session_token');
                    localStorage.removeItem('user_info');
                    // 触发全局认证状态更新（通过事件）
                    window.dispatchEvent(new CustomEvent('auth-expired'));
                    throw new Error('登录已过期，请重新登录');
                case 403:
                    throw new Error('访问被拒绝');
                case 404:
                    throw new Error('资源不存在');
                case 500:
                    throw new Error('服务器内部错误');
                default:
                    throw new Error(data?.error || `请求失败 (${status})`);
            }
        } else if (error.request) {
            // 网络错误
            console.error('Network Error:', error.request);
            throw new Error('网络连接失败，请检查网络连接');
        } else {
            // 其他错误
            console.error('Other Error:', error.message);
            throw new Error(error.message || '请求失败');
        }
    }
);

const apiClient = {
    // 认证相关API
    async login(username, password) {
        try {
            console.log('发送登录请求到:', '/api/auth/login');
            const result = await api.post('/api/auth/login', { username, password });
            console.log('登录API响应:', result);
            
            // 如果登录成功，立即设置token
            if (result.success && result.session_token) {
                console.log('设置新的认证token:', result.session_token.substring(0, 20) + '...');
                setAuthToken(result.session_token);
            }
            
            return result;
        } catch (error) {
            console.error('登录失败:', error.message);
            console.error('错误详情:', error);
            throw error;
        }
    },

    async register(username, email, password) {
        try {
            const result = await api.post('/api/auth/register', { username, email, password });
            return result;
        } catch (error) {
            console.error('注册失败:', error.message);
            throw error;
        }
    },

    async logout() {
        try {
            const result = await api.post('/api/auth/logout');
            // 清除token
            setAuthToken(null);
            return result;
        } catch (error) {
            console.error('登出失败:', error.message);
            // 即使API调用失败，也清除本地token
            setAuthToken(null);
            throw error;
        }
    },

    async checkAuth() {
        try {
            const result = await api.get('/api/auth/check');
            return result;
        } catch (error) {
            console.error('检查认证状态失败:', error.message);
            throw error;
        }
    },

    async getProfile() {
        try {
            const result = await api.get('/api/auth/profile');
            return result;
        } catch (error) {
            console.error('获取用户资料失败:', error.message);
            throw error;
        }
    },

    async changePassword(currentPassword, newPassword) {
        try {
            const result = await api.post('/api/auth/change-password', {
                old_password: currentPassword,
                new_password: newPassword
            });
            return result;
        } catch (error) {
            console.error('修改密码失败:', error.message);
            throw error;
        }
    },

    async changeUsername(newUsername, password) {
        try {
            const result = await api.post('/api/auth/change-username', {
                new_username: newUsername,
                password: password
            });
            return result;
        } catch (error) {
            console.error('修改用户名失败:', error.message);
            throw error;
        }
    },

    async changeEmail(newEmail, password) {
        try {
            const result = await api.post('/api/auth/change-email', {
                new_email: newEmail,
                password: password
            });
            return result;
        } catch (error) {
            console.error('修改邮箱失败:', error.message);
            throw error;
        }
    },

    async initDefaultUser() {
        try {
            const result = await api.post('/api/auth/init');
            return result;
        } catch (error) {
            console.error('初始化默认用户失败:', error.message);
            throw error;
        }
    },
    // 旧的论文源相关API已移除，由新订阅系统替代

    // 论文相关API
    async getPaperDetail(paperId, options = {}) {
        const { expand = [] } = options;
        const params = {};
        
        if (expand.length > 0) params.expand = expand.join(',');
        
        return api.get(`/api/papers/${paperId}`, { params });
    },

    async updatePaperStatus(paperId, status, options = {}) {
        const { returnStats = false } = options;
        const payload = { status };
        
        if (returnStats) {
            payload.return_stats = true;
        }
        
        return api.put(`/api/papers/${paperId}/status`, payload);
    },

    async translateAbstract(paperId) {
        return api.post(`/api/papers/${paperId}/translate`);
    },

    // 稍后阅读 + 任务创建
    async addToReadLaterWithTask(paperId, priority = 5) {
        return api.post('/api/read-later', { paper_id: paperId, priority });
    },

    // 任务相关API
    async getTasks(options = {}) {
        try {
            const {
                status = null,
                task_type = null,
                limit = 100,
                include_steps = false
            } = options;
            
            const params = { limit, include_steps };
            if (status) params.status = status;
            if (task_type) params.task_type = task_type;
            
            const result = await api.get('/api/tasks', { params });
            
            // 确保返回的是数组，并处理null值
            if (Array.isArray(result)) {
                return result.filter(task => task && typeof task === 'object');
            } else if (result && Array.isArray(result.data)) {
                return result.data.filter(task => task && typeof task === 'object');
            } else {
                return [];
            }
        } catch (error) {
            console.warn('获取任务列表失败:', error.message);
            return [];
        }
    },

    async getTask(taskId) {
        return api.get(`/api/tasks/${taskId}`);
    },

    async cancelTask(taskId) {
        return api.post(`/api/tasks/${taskId}/cancel`);
    },

    async createAnalysisTask(paperId, priority = 5) {
        return api.post(`/api/papers/${paperId}/analyze`, { priority });
    },

    async getPaperAnalysis(paperId) {
        return api.get(`/api/papers/${paperId}/analysis`);
    },

    async getTaskStats() {
        try {
            return await api.get('/api/tasks/stats');
        } catch (error) {
            console.warn('获取任务统计失败:', error.message);
            return {
                task_status_counts: {},
                agent_status_counts: {},
                recent_completed_tasks: []
            };
        }
    },

    // Agent相关API
    async getAgents() {
        try {
            const result = await api.get('/api/agents');
            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.warn('获取Agent列表失败:', error.message);
            return [];
        }
    },

    async registerAgent(agentData) {
        return api.post('/api/agents/register', agentData);
    },

    async updateAgentStatus(agentId, status) {
        return api.put(`/api/agents/${agentId}/status`, { status });
    },

    async agentHeartbeat(agentId) {
        return api.post(`/api/agents/${agentId}/heartbeat`);
    },

    // 测试API
    async getTestPapers() {
        try {
            const result = await api.get('/api/test/papers');
            return Array.isArray(result) ? result : [];
        } catch (error) {
            console.warn('获取测试论文失败:', error.message);
            return [];
        }
    },

    // 通用文件下载
    async downloadFile(url) {
        return api.get(url, {
            responseType: 'blob',
        });
    },

    // PDF下载相关API
    async downloadPdfAsync(paperId, articleNumber, priority = 5) {
        return api.post('/api/download/pdf', {
            paper_id: paperId,
            article_number: articleNumber,
            priority: priority
        });
    },

    async createFullAnalysisTask(paperId, articleNumber, priority = 5) {
        return api.post('/api/tasks/analysis', {
            paper_id: paperId,
            article_number: articleNumber,
            priority: priority
        });
    },

    async downloadPdfAsyncLegacy(paperId, articleNumber) {
        return api.post('/api/download/async', {
            paper_id: paperId,
            article_number: articleNumber
        });
    },

    async downloadPdfSync(articleNumber) {
        return api.post('/api/download/ieee', {
            article_number: articleNumber
        });
    },

    async testDownload(articleNumber) {
        return api.post('/api/sse/test-download', {
            article_number: articleNumber
        });
    },

    // 新增：批量操作接口
    async getBatchPapers(paperIds, expand = []) {
        try {
            const payload = { paper_ids: paperIds };
            if (expand.length > 0) {
                payload.expand = expand;
            }
            return await api.post('/api/papers/batch', payload);
        } catch (error) {
            console.warn('批量获取论文失败:', error.message);
            return [];
        }
    },

    async batchUpdatePaperStatus(updates) {
        try {
            return await api.post('/api/papers/batch/status', { updates });
        } catch (error) {
            console.warn('批量更新论文状态失败:', error.message);
            return { success: false, error: error.message };
        }
    },

    // 健康检查
    async healthCheck() {
        try {
            return await api.get('/api/health');
        } catch (error) {
            console.warn('健康检查失败:', error.message);
            return { status: 'unhealthy', error: error.message };
        }
    },

    async getStatisticsSummary() {
        try {
            const result = await api.get('/api/statistics/summary');
            if (result.success) {
                return result.data;
            }
            // 如果 success 为 false，则抛出错误
            throw new Error(result.error || '获取统计汇总失败');
        } catch (error) {
            console.error('API Error in getStatisticsSummary:', error.message);
            // 将错误继续向上抛出，以便调用方可以捕获
            throw error;
        }
    },

    // --- 新增：稍后阅读相关API ---
    async getReadLaterList(params = {}) {
        try {
            const result = await api.get('/api/read-later', { params });
            
            // 如果返回的是新的分页格式 
            if (result && result.success && result.data) {
                // 适配新的分页格式
                if (result.data.papers && result.data.pagination) {
                    return {
                        papers: result.data.papers,
                        pagination: result.data.pagination
                    };
                }
                
                // 兼容旧格式
                return result;
            }
            
            return result;
        } catch (error) {
            console.warn('获取稍后阅读列表失败:', error.message);
            return {
                success: false,
                error: error.message,
                data: { items: [], total_count: 0 }
            };
        }
    },

    quickAddReadLater(paperId) {
        return api.post('/api/read-later', { paper_id: paperId, priority: 5 });
    },

    removeReadLater(paperId) {
        return api.delete(`/api/read-later/${paperId}`);
    },

    getReadLaterInfoForPaper(paperId) {
        return api.get(`/api/papers/${paperId}/read-later-info`);
    },

    async searchPapers(params = {}) {
        try {
            // 支持新的分页参数
            const queryParams = new URLSearchParams();

            // 将所有参数添加到查询中
            for (const key in params) {
                if (Array.isArray(params[key])) {
                    params[key].forEach(value => queryParams.append(key, value));
                } else if (params[key] !== null && params[key] !== undefined) {
                    queryParams.set(key, params[key]);
                }
            }

            const result = await api.get(`/api/search?${queryParams.toString()}`);
            
            if (result.success) {
                // 如果返回的是新的分页格式
                if (result.data.papers && result.data.pagination) {
                    return {
                        papers: result.data.papers,
                        pagination: result.data.pagination
                    };
                }
                
                // 处理搜索API返回的results字段
                if (result.data.results && result.data.pagination) {
                    return {
                        papers: result.data.results,
                        pagination: result.data.pagination
                    };
                }
                
                // 兼容旧格式：使用limit/offset转换为page格式
                const items = result.data.results || result.data.papers || result.data.items || result.data;
                const total = result.data.pagination?.total_count || result.data.total || result.data.total_count || items.length;
                const limit = params.limit || params.per_page || 20;
                const offset = params.offset || 0;
                const currentPage = Math.floor(offset / limit) + 1;
                
                return {
                    papers: items,
                    pagination: {
                        page: currentPage,
                        per_page: limit,
                        total: total,
                        total_pages: Math.ceil(total / limit),
                        has_prev: offset > 0,
                        has_next: offset + limit < total
                    }
                };
            }
            
            throw new Error(result.error || '搜索失败');
        } catch (error) {
            console.error('API Error in searchPapers:', error.message);
            throw error;
        }
    },

    // 获取热门搜索
    async getPopularSearches(limit = 10) {
        try {
            const result = await api.get(`/api/search/popular?limit=${limit}`);
            if (result.success) {
                return result.data;
            }
            return result; // 如果没有success字段，直接返回结果
        } catch (error) {
            console.warn('获取热门搜索失败:', error.message);
            return [];
        }
    },

    // 获取当前配置信息 (调试用)
    getConfig() {
        return {
            baseURL: api.defaults.baseURL,
            timeout: api.defaults.timeout,
            environment: getEnvironment(),
            viteApiUrl: getEnvVar('VITE_API_BASE_URL'),
            craApiUrl: getEnvVar('REACT_APP_API_BASE_URL'),
            isVite: typeof import.meta !== 'undefined',
            hasProcess: typeof process !== 'undefined',
        };
    },
};

// 在开发环境下输出配置信息
if (getEnvironment() === 'development') {
    console.log('🔧 API Client Configuration:', apiClient.getConfig());
}

// 导出token管理函数
export { setAuthToken, getAuthToken };
export default apiClient;