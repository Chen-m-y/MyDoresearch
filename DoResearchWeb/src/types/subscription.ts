// 订阅系统相关的类型定义

// === 基础API响应类型 ===
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
}

export interface PaginatedResponse<T> {
    success: boolean;
    data: {
        [key: string]: T[];
        pagination: {
            page: number;
            per_page: number;
            total: number;
            pages: number;
            has_prev?: boolean;
            has_next?: boolean;
        };
    };
}

// === JSON Schema相关类型 ===
export interface JSONSchemaProperty {
    type: 'string' | 'number' | 'integer' | 'boolean' | 'array' | 'object';
    description?: string;
    pattern?: string;
    minimum?: number;
    maximum?: number;
    default?: any;
    enum?: any[];
    items?: JSONSchemaProperty;
}

export interface JSONSchema {
    type: 'object' | 'string' | 'number' | 'boolean' | 'array';
    required?: string[];
    properties?: Record<string, JSONSchemaProperty>;
    items?: JSONSchemaProperty;
}

// === 订阅模板类型 ===
export interface SubscriptionTemplate {
    id: number;
    name: string;
    source_type: 'ieee' | 'elsevier' | 'dblp' | 'arxiv' | 'pubmed';
    description: string;
    parameter_schema: JSONSchema;
    example_params: Record<string, any>;
    active: boolean;
    created_at: string;
    updated_at?: string;
    created_by?: number;
}

// === 用户订阅类型 ===
export interface UserSubscription {
    id: number;
    user_id: number;
    template_id: number;
    name: string;
    source_params: Record<string, any>;
    status: 'active' | 'paused' | 'error';
    sync_frequency: number;
    last_sync_at: string | null;
    next_sync_at: string | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
    // 关联数据
    template_name?: string;
    source_type?: string;
    description?: string;
    parameter_schema?: JSONSchema;
    example_params?: Record<string, any>;
}

// === 同步历史类型 ===
export interface SyncHistory {
    id: number;
    subscription_id: number;
    sync_started_at: string;
    sync_completed_at: string | null;
    status: 'success' | 'error' | 'running';
    papers_found: number;
    papers_new: number;
    error_details: string | null;
    external_service_response: string | null;
}

// === 论文数据类型 ===
export interface Paper {
    id: number;
    title: string;
    abstract: string;
    authors: string;
    journal: string;
    published_date: string;
    url: string;
    pdf_url: string | null;
    doi: string | null;
    status: 'read' | 'unread' | 'reading';
    created_at: string;
    subscription_id?: number | null;
    feed_id?: number | null; // 兼容旧系统
    keywords: string | null; // JSON字符串
    citations: number;
    metadata: string | null; // JSON字符串
    // 解析后的字段
    keywords_array?: string[];
    metadata_object?: Record<string, any>;
}

// === 表单数据类型 ===
export interface CreateSubscriptionForm {
    template_id: number;
    name: string;
    source_params: Record<string, any>;
    sync_frequency?: number;
}

export interface UpdateSubscriptionForm {
    name?: string;
    source_params?: Record<string, any>;
    sync_frequency?: number;
    status?: 'active' | 'paused';
}

// === UI状态类型 ===
export interface SubscriptionListState {
    subscriptions: UserSubscription[];
    loading: boolean;
    error: string | null;
    selectedSubscription: UserSubscription | null;
}

export interface TemplateListState {
    templates: SubscriptionTemplate[];
    loading: boolean;
    error: string | null;
}

export interface SyncStatus {
    subscription_id: number;
    is_syncing: boolean;
    progress?: number;
    last_update: string;
}

// === 订阅统计类型 ===
export interface SubscriptionStats {
    total_subscriptions: number;
    active_subscriptions: number;
    paused_subscriptions: number;
    error_subscriptions: number;
    total_papers_today: number;
    avg_sync_time: number;
}

// === 组件Props类型 ===
export interface TemplateCardProps {
    template: SubscriptionTemplate;
    onSelect: (template: SubscriptionTemplate) => void;
    onViewDetails: (template: SubscriptionTemplate) => void;
}

export interface SubscriptionItemProps {
    subscription: UserSubscription;
    onSync: (subscriptionId: number) => void;
    onEdit: (subscription: UserSubscription) => void;
    onDelete: (subscriptionId: number) => void;
    onPause: (subscriptionId: number) => void;
    onResume: (subscriptionId: number) => void;
    syncingIds: number[];
}

export interface DynamicFormProps {
    schema: JSONSchema;
    values: Record<string, any>;
    onChange: (fieldName: string, value: any) => void;
    examples: Record<string, any>;
    errors?: string[];
}

export interface SyncHistoryProps {
    subscriptionId: number;
    limit?: number;
}

// === 表单验证类型 ===
export interface ValidationResult {
    valid: boolean;
    errors: string[];
}

// === 分页参数类型 ===
export interface PaginationParams {
    page?: number;
    per_page?: number;
}

// === 搜索和过滤参数 ===
export interface SubscriptionFilters {
    status?: 'all' | 'active' | 'paused' | 'error';
    source_type?: string;
    template_id?: number;
    search?: string;
}

export interface PaperFilters {
    status?: 'all' | 'read' | 'unread' | 'reading';
    date_from?: string;
    date_to?: string;
    search?: string;
}

// === 错误处理类型 ===
export class SubscriptionError extends Error {
    public code: string;
    public statusCode?: number;

    constructor(message: string, code: string, statusCode?: number) {
        super(message);
        this.name = 'SubscriptionError';
        this.code = code;
        this.statusCode = statusCode;
    }
}

// === Hook返回类型 ===
export interface UseSubscriptionsResult {
    subscriptions: UserSubscription[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

export interface UseSubscriptionTemplatesResult {
    templates: SubscriptionTemplate[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

export interface UseCreateSubscriptionResult {
    createSubscription: (data: CreateSubscriptionForm) => Promise<void>;
    loading: boolean;
    error: string | null;
}

export interface UseSyncHistoryResult {
    history: SyncHistory[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

// === 订阅源类型配置 ===
export interface SourceTypeConfig {
    name: string;
    displayName: string;
    color: string;
    icon: string;
    description: string;
    supportedFeatures: string[];
}

// === 同步频率选项 ===
export interface SyncFrequencyOption {
    value: number;
    label: string;
    description?: string;
}

// === 常量定义 ===
export const SYNC_FREQUENCY_OPTIONS: SyncFrequencyOption[] = [
    { value: 3600, label: '每小时', description: '适用于高频更新的期刊' },
    { value: 21600, label: '每6小时', description: '平衡频率和性能' },
    { value: 43200, label: '每12小时', description: '大多数期刊的推荐频率' },
    { value: 86400, label: '每天', description: '默认选项，适合大多数场景' },
    { value: 604800, label: '每周', description: '低频更新的期刊或会议' }
];

export const SOURCE_TYPE_CONFIGS: Record<string, SourceTypeConfig> = {
    ieee: {
        name: 'ieee',
        displayName: 'IEEE',
        color: '#1f77b4',
        icon: 'ieee',
        description: 'IEEE数字图书馆论文订阅',
        supportedFeatures: ['auto_sync', 'pdf_download', 'citation_export']
    },
    elsevier: {
        name: 'elsevier',
        displayName: 'Elsevier',
        color: '#ff7f0e',
        icon: 'elsevier',
        description: 'Elsevier期刊论文订阅',
        supportedFeatures: ['auto_sync', 'abstract_translation']
    },
    dblp: {
        name: 'dblp',
        displayName: 'DBLP',
        color: '#2ca02c',
        icon: 'dblp',
        description: 'DBLP计算机科学论文库',
        supportedFeatures: ['auto_sync', 'author_tracking']
    },
    arxiv: {
        name: 'arxiv',
        displayName: 'arXiv',
        color: '#d62728',
        icon: 'arxiv',
        description: 'arXiv预印本论文库',
        supportedFeatures: ['auto_sync', 'category_filtering', 'pdf_download']
    },
    pubmed: {
        name: 'pubmed',
        displayName: 'PubMed',
        color: '#9467bd',
        icon: 'pubmed',
        description: 'PubMed生物医学论文库',
        supportedFeatures: ['auto_sync', 'mesh_terms', 'abstract_translation']
    }
};

// === 状态相关常量 ===
export const SUBSCRIPTION_STATUSES = {
    ACTIVE: 'active' as const,
    PAUSED: 'paused' as const,
    ERROR: 'error' as const
};

export const SYNC_STATUSES = {
    SUCCESS: 'success' as const,
    ERROR: 'error' as const,
    RUNNING: 'running' as const
};

export const PAPER_STATUSES = {
    READ: 'read' as const,
    UNREAD: 'unread' as const,
    READING: 'reading' as const
};

// === 默认值 ===
export const DEFAULT_PAGINATION_PARAMS: PaginationParams = {
    page: 1,
    per_page: 20
};

export const DEFAULT_SUBSCRIPTION_FILTERS: SubscriptionFilters = {
    status: 'all'
};

export const DEFAULT_PAPER_FILTERS: PaperFilters = {
    status: 'all'
};

// === 路由路径常量 ===
export const SUBSCRIPTION_ROUTES = {
    TEMPLATES: '/subscriptions/templates',
    CREATE: '/subscriptions/create',
    LIST: '/subscriptions',
    DETAIL: '/subscriptions/:id',
    EDIT: '/subscriptions/:id/edit'
} as const;