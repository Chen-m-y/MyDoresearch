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

// 获取API基础URL (复用 apiClient 的逻辑)
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

// 创建一个简单的HTTP客户端，复用apiClient的配置
const httpClient = axios.create({
    baseURL: getApiBaseUrl(), // 使用与 apiClient 相同的逻辑
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
    maxRedirects: 5,
    maxContentLength: 50 * 1024 * 1024, // 50MB
    maxBodyLength: 50 * 1024 * 1024,
});

// 复制apiClient的拦截器逻辑
httpClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('session_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
    }
);

httpClient.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        console.error('API Error:', error);
        if (error.response?.status === 401) {
            localStorage.removeItem('session_token');
            localStorage.removeItem('user_info');
            window.dispatchEvent(new CustomEvent('auth-expired'));
        }
        throw new Error(error.response?.data?.error || error.message || '请求失败');
    }
);

// 创建专用的订阅API客户端
const subscriptionClient = {
    // === 订阅模板相关API ===
    
    async getSubscriptionTemplates() {
        try {
            const result = await httpClient.get('/api/v2/subscription-templates');
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取订阅模板失败');
        } catch (error) {
            console.error('获取订阅模板失败:', error.message);
            throw error;
        }
    },

    async getSubscriptionTemplate(templateId) {
        try {
            const result = await httpClient.get(`/api/v2/subscription-templates/${templateId}`);
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取订阅模板详情失败');
        } catch (error) {
            console.error(`获取订阅模板 ${templateId} 失败:`, error.message);
            throw error;
        }
    },

    // === 用户订阅相关API ===
    
    async createSubscription(subscriptionData) {
        try {
            const { template_id, name, source_params, sync_frequency } = subscriptionData;
            const result = await httpClient.post('/api/v2/subscriptions', {
                template_id,
                name,
                source_params,
                sync_frequency
            });
            
            if (result.success) {
                return result;
            }
            throw new Error(result.error || '创建订阅失败');
        } catch (error) {
            console.error('创建订阅失败:', error.message);
            throw error;
        }
    },

    async getSubscriptions() {
        try {
            const result = await httpClient.get('/api/v2/subscriptions');
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取订阅列表失败');
        } catch (error) {
            console.error('获取订阅列表失败:', error.message);
            // 返回空数组作为降级处理
            return [];
        }
    },

    async getSubscription(subscriptionId) {
        try {
            const result = await httpClient.get(`/api/v2/subscriptions/${subscriptionId}`);
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取订阅详情失败');
        } catch (error) {
            console.error(`获取订阅 ${subscriptionId} 失败:`, error.message);
            throw error;
        }
    },

    async updateSubscription(subscriptionId, updateData) {
        try {
            const result = await httpClient.put(`/api/v2/subscriptions/${subscriptionId}`, updateData);
            if (result.success) {
                return result;
            }
            throw new Error(result.error || '更新订阅失败');
        } catch (error) {
            console.error(`更新订阅 ${subscriptionId} 失败:`, error.message);
            throw error;
        }
    },

    async deleteSubscription(subscriptionId) {
        try {
            const result = await httpClient.delete(`/api/v2/subscriptions/${subscriptionId}`);
            if (result.success) {
                return result;
            }
            throw new Error(result.error || '删除订阅失败');
        } catch (error) {
            console.error(`删除订阅 ${subscriptionId} 失败:`, error.message);
            throw error;
        }
    },

    async syncSubscription(subscriptionId) {
        try {
            const result = await httpClient.post(`/api/v2/subscriptions/${subscriptionId}/sync`);
            if (result.success) {
                return result;
            }
            throw new Error(result.error || '手动同步失败');
        } catch (error) {
            console.error(`同步订阅 ${subscriptionId} 失败:`, error.message);
            throw error;
        }
    },

    // === 订阅历史和统计 ===
    
    async getSubscriptionHistory(subscriptionId, limit = 20) {
        try {
            const result = await httpClient.get(`/api/v2/subscriptions/${subscriptionId}/history`, {
                params: { limit }
            });
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取同步历史失败');
        } catch (error) {
            console.error(`获取订阅 ${subscriptionId} 历史失败:`, error.message);
            // 返回空数组作为降级处理
            return [];
        }
    },

    async getSubscriptionPapers(subscriptionId, params = {}) {
        try {
            const { page = 1, per_page = 20, status = 'all' } = params;
            const result = await httpClient.get(`/api/v2/subscriptions/${subscriptionId}/papers`, {
                params: { 
                    page, 
                    per_page, 
                    status, 
                    include_stats: true, // 添加统计信息请求
                    expand: 'read_later' // 添加read_later数据
                }
            });
            
            if (result.success) {
                // 标准化分页数据结构，确保与前端期望的格式一致
                const data = result.data;
                if (data && data.pagination) {
                    // 如果后端返回的是 'pages'，转换为 'total_pages'
                    if (data.pagination.pages && !data.pagination.total_pages) {
                        data.pagination.total_pages = data.pagination.pages;
                    }
                    
                    // 确保有 has_prev 和 has_next 字段
                    if (data.pagination.has_prev === undefined) {
                        data.pagination.has_prev = data.pagination.page > 1;
                    }
                    if (data.pagination.has_next === undefined) {
                        data.pagination.has_next = data.pagination.page < data.pagination.total_pages;
                    }
                }
                
                // 如果有统计信息，将其添加到结果中
                if (data && data.stats) {
                    // 将统计信息格式化为前端期望的格式
                    data.stats = {
                        all: data.stats.total || data.stats.all || 0,
                        total: data.stats.total || data.stats.all || 0,
                        read: data.stats.read || 0,
                        unread: data.stats.unread || 0
                    };
                }
                
                return data;
            }
            throw new Error(result.error || '获取订阅论文失败');
        } catch (error) {
            console.error(`获取订阅 ${subscriptionId} 论文失败:`, error.message);
            // 返回空数据作为降级处理
            return {
                papers: [],
                pagination: {
                    page: params.page || 1,
                    per_page: params.per_page || 20,
                    total: 0,
                    total_pages: 0,
                    has_prev: false,
                    has_next: false
                }
            };
        }
    },

    // 获取单个订阅的统计信息
    async getSubscriptionStats(subscriptionId) {
        try {
            const result = await httpClient.get(`/api/v2/subscriptions/${subscriptionId}/stats`);
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取订阅统计失败');
        } catch (error) {
            console.error(`获取订阅 ${subscriptionId} 统计失败:`, error.message);
            // 返回默认统计信息
            return {
                paper_stats: {
                    total_papers: 0,
                    status_counts: { read: 0, unread: 0, reading: 0 }
                },
                sync_stats: {
                    total_syncs: 0,
                    success_rate: 0,
                    last_sync: null
                }
            };
        }
    },

    // 批量获取多个订阅的统计信息
    async getBatchSubscriptionStats(subscriptionIds) {
        try {
            if (!subscriptionIds || subscriptionIds.length === 0) {
                return {};
            }
            
            const idsString = subscriptionIds.join(',');
            const result = await httpClient.get('/api/v2/subscriptions/stats', {
                params: { subscription_ids: idsString }
            });
            
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '批量获取订阅统计失败');
        } catch (error) {
            console.error('批量获取订阅统计失败:', error.message);
            // 返回空统计作为降级处理
            const emptyStats = {};
            subscriptionIds.forEach(id => {
                emptyStats[id] = {
                    total_papers: 0,
                    unread_count: 0,
                    status_counts: { read: 0, unread: 0, reading: 0 },
                    last_sync_status: 'unknown'
                };
            });
            return emptyStats;
        }
    },

    // === 管理员API（可选） ===
    
    async getExternalServiceHealth() {
        try {
            const result = await httpClient.get('/api/admin/external-service/health');
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取外部服务状态失败');
        } catch (error) {
            console.warn('获取外部服务状态失败:', error.message);
            return { status: 'unknown' };
        }
    },

    async getGlobalSubscriptionStats() {
        try {
            const result = await httpClient.get('/api/admin/subscriptions/stats');
            if (result.success) {
                return result.data;
            }
            throw new Error(result.error || '获取订阅统计失败');
        } catch (error) {
            console.warn('获取订阅统计失败:', error.message);
            return {};
        }
    },

    // === 辅助工具函数 ===
    
    // 验证订阅参数
    validateSubscriptionParams(params, schema) {
        const errors = [];
        
        if (!schema || !schema.properties) {
            return { valid: true, errors: [] };
        }

        // 检查必填字段
        if (schema.required) {
            for (const requiredField of schema.required) {
                if (!params[requiredField] || params[requiredField] === '') {
                    errors.push(`${requiredField} 是必填字段`);
                }
            }
        }

        // 检查字段格式
        for (const [fieldName, fieldSchema] of Object.entries(schema.properties)) {
            const value = params[fieldName];
            
            if (value !== undefined && value !== null && value !== '') {
                // 字符串格式检查
                if (fieldSchema.type === 'string' && fieldSchema.pattern) {
                    const regex = new RegExp(fieldSchema.pattern);
                    if (!regex.test(value)) {
                        errors.push(`${fieldName} 格式不正确`);
                    }
                }
                
                // 数字范围检查
                if (fieldSchema.type === 'number') {
                    const numValue = Number(value);
                    if (isNaN(numValue)) {
                        errors.push(`${fieldName} 必须是有效数字`);
                    } else {
                        if (fieldSchema.minimum !== undefined && numValue < fieldSchema.minimum) {
                            errors.push(`${fieldName} 不能小于 ${fieldSchema.minimum}`);
                        }
                        if (fieldSchema.maximum !== undefined && numValue > fieldSchema.maximum) {
                            errors.push(`${fieldName} 不能大于 ${fieldSchema.maximum}`);
                        }
                    }
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    },

    // 格式化同步频率
    formatSyncFrequency(seconds) {
        if (seconds < 3600) {
            return `${Math.round(seconds / 60)} 分钟`;
        } else if (seconds < 86400) {
            return `${Math.round(seconds / 3600)} 小时`;
        } else if (seconds < 604800) {
            return `${Math.round(seconds / 86400)} 天`;
        } else {
            return `${Math.round(seconds / 604800)} 周`;
        }
    },

    // 获取订阅源类型的显示名称
    getSourceTypeDisplayName(sourceType) {
        const typeNames = {
            ieee: 'IEEE',
            elsevier: 'Elsevier',
            dblp: 'DBLP',
            arxiv: 'arXiv',
            pubmed: 'PubMed'
        };
        return typeNames[sourceType] || sourceType.toUpperCase();
    },

    // 获取订阅状态的显示信息
    getSubscriptionStatusInfo(status) {
        const statusInfo = {
            active: {
                label: '活跃',
                color: 'success',
                description: '订阅正常运行中'
            },
            paused: {
                label: '暂停',
                color: 'warning',
                description: '订阅已暂停同步'
            },
            error: {
                label: '错误',
                color: 'error',
                description: '订阅出现错误'
            }
        };
        return statusInfo[status] || {
            label: status,
            color: 'default',
            description: '未知状态'
        };
    }
};

export default subscriptionClient;