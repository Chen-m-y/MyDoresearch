# DoResearch 新订阅系统前端对接详细规范

## 📋 目录
- [API接口详细说明](#api接口详细说明)
- [数据模型定义](#数据模型定义)
- [页面组件详细设计](#页面组件详细设计)
- [状态管理方案](#状态管理方案)
- [UI/UX设计规范](#uiux设计规范)
- [错误处理机制](#错误处理机制)
- [实现示例代码](#实现示例代码)

## 🔌 API接口详细说明

### 基础配置
- **Base URL**: `http://localhost:5000` (开发环境)
- **认证方式**: 使用现有的认证机制（Session/JWT）
- **Content-Type**: `application/json`

### 1. 订阅模板相关API

#### 获取订阅模板列表
```http
GET /api/v2/subscription-templates
Authorization: [现有认证方式]
```

**响应格式**:
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
        "required": ["punumber"],
        "properties": {
          "punumber": {
            "type": "string",
            "description": "IEEE期刊的publication number",
            "pattern": "^[0-9]+$"
          }
        }
      },
      "example_params": {"punumber": "32"},
      "active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 获取单个模板详情
```http
GET /api/v2/subscription-templates/{template_id}
Authorization: [现有认证方式]
```

### 2. 用户订阅相关API

#### 创建订阅
```http
POST /api/v2/subscriptions
Content-Type: application/json
Authorization: [现有认证方式]

{
  "template_id": 1,
  "name": "我的IEEE订阅",
  "source_params": {
    "punumber": "32"
  }
}
```

**响应格式**:
```json
{
  "success": true,
  "subscription_id": 123
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "参数验证失败: 'punumber' is a required property"
}
```

#### 获取用户订阅列表
```http
GET /api/v2/subscriptions
Authorization: [现有认证方式]
```

**响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "name": "我的IEEE订阅",
      "template_id": 1,
      "source_params": {"punumber": "32"},
      "status": "active",
      "sync_frequency": 86400,
      "last_sync_at": "2024-01-15T10:00:00Z",
      "next_sync_at": "2024-01-16T10:00:00Z",
      "error_message": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z",
      "template_name": "IEEE期刊订阅",
      "source_type": "ieee",
      "description": "订阅IEEE期刊最新论文"
    }
  ]
}
```

#### 获取单个订阅详情
```http
GET /api/v2/subscriptions/{subscription_id}
Authorization: [现有认证方式]
```

#### 更新订阅
```http
PUT /api/v2/subscriptions/{subscription_id}
Content-Type: application/json
Authorization: [现有认证方式]

{
  "name": "更新的订阅名称",
  "source_params": {"punumber": "64"},
  "sync_frequency": 43200,
  "status": "active"
}
```

#### 删除订阅
```http
DELETE /api/v2/subscriptions/{subscription_id}
Authorization: [现有认证方式]
```

#### 手动同步
```http
POST /api/v2/subscriptions/{subscription_id}/sync
Authorization: [现有认证方式]
```

**响应格式**:
```json
{
  "success": true,
  "message": "同步已完成"
}
```

#### 获取同步历史
```http
GET /api/v2/subscriptions/{subscription_id}/history?limit=20
Authorization: [现有认证方式]
```

**响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "subscription_id": 123,
      "sync_started_at": "2024-01-15T10:00:00Z",
      "sync_completed_at": "2024-01-15T10:02:30Z",
      "status": "success",
      "papers_found": 25,
      "papers_new": 5,
      "error_details": null,
      "external_service_response": null
    }
  ]
}
```

#### 获取订阅的论文
```http
GET /api/v2/subscriptions/{subscription_id}/papers?page=1&per_page=20&status=all
Authorization: [现有认证方式]
```

**响应格式**:
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
        "journal": "IEEE Transactions on Software Engineering",
        "published_date": "2024-01-15",
        "url": "https://ieeexplore.ieee.org/document/123456",
        "pdf_url": "/stamp/stamp.jsp?tp=&arnumber=123456",
        "doi": "10.1109/TSE.2024.123456",
        "status": "unread",
        "created_at": "2024-01-15T10:00:00Z",
        "subscription_id": 123,
        "keywords": ["keyword1", "keyword2"],
        "citations": 10,
        "metadata": "{\"ieee_number\":\"123456\"}"
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

### 3. 管理员API（可选）

#### 检查外部服务状态
```http
GET /api/admin/external-service/health
Authorization: [管理员认证]
```

#### 获取系统统计
```http
GET /api/admin/subscriptions/stats
Authorization: [管理员认证]
```

## 📊 数据模型定义

### TypeScript 接口定义

```typescript
// 基础响应类型
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// 分页响应类型
interface PaginatedResponse<T> {
  success: boolean;
  data: {
    [key: string]: T[];
    pagination: {
      page: number;
      per_page: number;
      total: number;
      pages: number;
    };
  };
}

// JSON Schema类型
interface JSONSchema {
  type: 'object' | 'string' | 'number' | 'boolean' | 'array';
  required?: string[];
  properties?: Record<string, JSONSchemaProperty>;
  items?: JSONSchemaProperty;
}

interface JSONSchemaProperty {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description?: string;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  default?: any;
  enum?: any[];
  items?: JSONSchemaProperty;
}

// 订阅模板
interface SubscriptionTemplate {
  id: number;
  name: string;
  source_type: 'ieee' | 'elsevier' | 'dblp';
  description: string;
  parameter_schema: JSONSchema;
  example_params: Record<string, any>;
  active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: number;
}

// 用户订阅
interface UserSubscription {
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
  template_name: string;
  source_type: string;
  description: string;
  parameter_schema?: JSONSchema;
  example_params?: Record<string, any>;
}

// 同步历史
interface SyncHistory {
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

// 论文数据
interface Paper {
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
  subscription_id: number | null;
  feed_id: number | null; // 兼容旧系统
  keywords: string | null; // JSON字符串
  citations: number;
  metadata: string | null; // JSON字符串
  // 解析后的字段
  keywords_array?: string[];
  metadata_object?: Record<string, any>;
}

// 表单数据类型
interface CreateSubscriptionForm {
  template_id: number;
  name: string;
  source_params: Record<string, any>;
  sync_frequency?: number;
}

interface UpdateSubscriptionForm {
  name?: string;
  source_params?: Record<string, any>;
  sync_frequency?: number;
  status?: 'active' | 'paused';
}

// UI状态类型
interface SubscriptionListState {
  subscriptions: UserSubscription[];
  loading: boolean;
  error: string | null;
  selectedSubscription: UserSubscription | null;
}

interface TemplateListState {
  templates: SubscriptionTemplate[];
  loading: boolean;
  error: string | null;
}

interface SyncStatus {
  subscription_id: number;
  is_syncing: boolean;
  progress?: number;
  last_update: string;
}
```

## 🎨 页面组件详细设计

### 1. 订阅模板浏览页面 (`/subscriptions/templates`)

#### 组件结构
```jsx
<SubscriptionTemplatesPage>
  <PageHeader title="选择订阅类型" />
  <SearchAndFilter />
  <TemplateGrid>
    <TemplateCard />
    <TemplateCard />
    <TemplateCard />
  </TemplateGrid>
</SubscriptionTemplatesPage>
```

#### TemplateCard 组件详细设计
```jsx
<Card className="template-card">
  <CardHeader>
    <SourceIcon type={template.source_type} />
    <Title>{template.name}</Title>
    <Badge status={template.active ? 'active' : 'inactive'} />
  </CardHeader>
  <CardBody>
    <Description>{template.description}</Description>
    <ParameterPreview schema={template.parameter_schema} />
    <ExampleParams params={template.example_params} />
  </CardBody>
  <CardFooter>
    <Button 
      variant="primary" 
      onClick={() => navigateToCreate(template.id)}
    >
      立即订阅
    </Button>
    <Button variant="outline" onClick={() => showDetails(template)}>
      查看详情
    </Button>
  </CardFooter>
</Card>
```

### 2. 订阅创建页面 (`/subscriptions/create/:templateId`)

#### 动态表单实现
```jsx
<CreateSubscriptionPage>
  <PageHeader>
    <BackButton />
    <Title>创建 {template.name}</Title>
  </PageHeader>
  
  <Form onSubmit={handleSubmit}>
    <FormSection title="基本信息">
      <Input
        label="订阅名称"
        name="name"
        required
        placeholder={`我的${template.name}`}
      />
    </FormSection>
    
    <FormSection title="参数配置">
      <DynamicParameterForm 
        schema={template.parameter_schema}
        values={formData.source_params}
        onChange={handleParamsChange}
        examples={template.example_params}
      />
    </FormSection>
    
    <FormSection title="同步设置">
      <Select
        label="同步频率"
        name="sync_frequency"
        options={syncFrequencyOptions}
        defaultValue={86400}
      />
    </FormSection>
    
    <FormActions>
      <Button type="submit" loading={creating}>
        创建订阅
      </Button>
      <Button variant="outline" onClick={goBack}>
        取消
      </Button>
    </FormActions>
  </Form>
</CreateSubscriptionPage>
```

#### DynamicParameterForm 实现
```jsx
function DynamicParameterForm({ schema, values, onChange, examples }) {
  const renderField = (fieldName, fieldSchema) => {
    switch (fieldSchema.type) {
      case 'string':
        if (fieldSchema.pattern) {
          return (
            <Input
              name={fieldName}
              label={fieldSchema.description || fieldName}
              pattern={fieldSchema.pattern}
              required={schema.required?.includes(fieldName)}
              placeholder={examples[fieldName]}
              value={values[fieldName] || ''}
              onChange={(e) => onChange(fieldName, e.target.value)}
              helperText={`示例: ${examples[fieldName]}`}
            />
          );
        }
        return <Input ... />;
      
      case 'number':
        return (
          <NumberInput
            name={fieldName}
            label={fieldSchema.description || fieldName}
            min={fieldSchema.minimum}
            max={fieldSchema.maximum}
            required={schema.required?.includes(fieldName)}
            value={values[fieldName] || fieldSchema.default}
            onChange={(value) => onChange(fieldName, value)}
          />
        );
      
      case 'boolean':
        return (
          <Checkbox
            name={fieldName}
            label={fieldSchema.description || fieldName}
            checked={values[fieldName] || fieldSchema.default}
            onChange={(checked) => onChange(fieldName, checked)}
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="dynamic-form">
      {Object.entries(schema.properties || {}).map(([fieldName, fieldSchema]) => (
        <FormField key={fieldName}>
          {renderField(fieldName, fieldSchema)}
        </FormField>
      ))}
    </div>
  );
}
```

### 3. 我的订阅页面 (`/subscriptions`)

#### 页面布局
```jsx
<MySubscriptionsPage>
  <PageHeader>
    <Title>我的订阅</Title>
    <Actions>
      <Button 
        icon={<PlusIcon />}
        onClick={() => navigate('/subscriptions/templates')}
      >
        添加订阅
      </Button>
      <RefreshButton onClick={refreshSubscriptions} />
    </Actions>
  </PageHeader>
  
  <FilterTabs
    tabs={[
      { key: 'all', label: '全部', count: totalCount },
      { key: 'active', label: '活跃', count: activeCount },
      { key: 'paused', label: '暂停', count: pausedCount },
      { key: 'error', label: '错误', count: errorCount }
    ]}
    activeTab={activeTab}
    onChange={setActiveTab}
  />
  
  <SubscriptionList
    subscriptions={filteredSubscriptions}
    loading={loading}
    onSync={handleManualSync}
    onEdit={handleEdit}
    onDelete={handleDelete}
    onPause={handlePause}
    onResume={handleResume}
  />
</MySubscriptionsPage>
```

#### SubscriptionItem 组件
```jsx
<Card className="subscription-item">
  <CardHeader className="flex justify-between">
    <div className="flex items-center space-x-3">
      <SourceIcon type={subscription.source_type} />
      <div>
        <Title>{subscription.name}</Title>
        <Subtitle>{subscription.template_name}</Subtitle>
      </div>
    </div>
    <StatusBadge status={subscription.status} />
  </CardHeader>
  
  <CardBody>
    <ParametersDisplay params={subscription.source_params} />
    <SyncInfo
      lastSync={subscription.last_sync_at}
      nextSync={subscription.next_sync_at}
      frequency={subscription.sync_frequency}
    />
    {subscription.error_message && (
      <ErrorMessage>{subscription.error_message}</ErrorMessage>
    )}
  </CardBody>
  
  <CardFooter>
    <ButtonGroup>
      <Button
        size="sm"
        icon={<SyncIcon />}
        onClick={() => onSync(subscription.id)}
        loading={syncingIds.includes(subscription.id)}
      >
        同步
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => navigate(`/subscriptions/${subscription.id}`)}
      >
        详情
      </Button>
      <DropdownMenu>
        <DropdownItem onClick={() => onEdit(subscription)}>
          编辑
        </DropdownItem>
        <DropdownItem 
          onClick={() => subscription.status === 'active' ? 
            onPause(subscription.id) : 
            onResume(subscription.id)
          }
        >
          {subscription.status === 'active' ? '暂停' : '恢复'}
        </DropdownItem>
        <DropdownItem 
          danger 
          onClick={() => onDelete(subscription.id)}
        >
          删除
        </DropdownItem>
      </DropdownMenu>
    </ButtonGroup>
  </CardFooter>
</Card>
```

### 4. 订阅详情页面 (`/subscriptions/:id`)

#### 标签页布局
```jsx
<SubscriptionDetailPage>
  <PageHeader>
    <BackButton />
    <div>
      <Title>{subscription.name}</Title>
      <Subtitle>{subscription.template_name}</Subtitle>
    </div>
    <Actions>
      <Button onClick={() => handleManualSync()}>手动同步</Button>
      <Button variant="outline" onClick={() => handleEdit()}>编辑</Button>
    </Actions>
  </PageHeader>
  
  <Tabs>
    <TabPanel title="概览" icon={<OverviewIcon />}>
      <OverviewSection subscription={subscription} />
    </TabPanel>
    
    <TabPanel title="同步历史" icon={<HistoryIcon />}>
      <SyncHistorySection subscriptionId={subscription.id} />
    </TabPanel>
    
    <TabPanel title="获取的论文" icon={<PaperIcon />}>
      <SubscriptionPapersSection subscriptionId={subscription.id} />
    </TabPanel>
    
    <TabPanel title="设置" icon={<SettingsIcon />}>
      <SubscriptionSettings subscription={subscription} />
    </TabPanel>
  </Tabs>
</SubscriptionDetailPage>
```

#### 同步历史组件
```jsx
function SyncHistorySection({ subscriptionId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  return (
    <div className="sync-history">
      <SectionHeader>
        <Title>同步历史</Title>
        <RefreshButton onClick={loadHistory} />
      </SectionHeader>
      
      {loading ? (
        <SkeletonLoader />
      ) : (
        <Timeline>
          {history.map((record) => (
            <TimelineItem key={record.id} status={record.status}>
              <TimelineHeader>
                <Timestamp>{formatDateTime(record.sync_started_at)}</Timestamp>
                <StatusBadge status={record.status} />
              </TimelineHeader>
              <TimelineContent>
                {record.status === 'success' ? (
                  <SuccessMessage>
                    发现 {record.papers_found} 篇论文，新增 {record.papers_new} 篇
                  </SuccessMessage>
                ) : record.error_details ? (
                  <ErrorMessage>{record.error_details}</ErrorMessage>
                ) : (
                  <PendingMessage>同步进行中...</PendingMessage>
                )}
                <Duration>
                  {record.sync_completed_at && 
                    `耗时 ${formatDuration(record.sync_started_at, record.sync_completed_at)}`
                  }
                </Duration>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      )}
    </div>
  );
}
```

## 🔄 状态管理方案

### 使用 React Query / TanStack Query

```typescript
// hooks/useSubscriptions.ts
export function useSubscriptions() {
  return useQuery({
    queryKey: ['subscriptions'],
    queryFn: async () => {
      const response = await api.get('/api/v2/subscriptions');
      if (!response.data.success) {
        throw new Error(response.data.error);
      }
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: CreateSubscriptionForm) => {
      const response = await api.post('/api/v2/subscriptions', data);
      if (!response.data.success) {
        throw new Error(response.data.error);
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      toast.success('订阅创建成功');
    },
    onError: (error) => {
      toast.error(`创建失败: ${error.message}`);
    }
  });
}

export function useManualSync() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (subscriptionId: number) => {
      const response = await api.post(`/api/v2/subscriptions/${subscriptionId}/sync`);
      if (!response.data.success) {
        throw new Error(response.data.error);
      }
      return response.data;
    },
    onSuccess: (data, subscriptionId) => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({ queryKey: ['subscription', subscriptionId] });
      toast.success('同步已开始');
    },
    onError: (error) => {
      toast.error(`同步失败: ${error.message}`);
    }
  });
}

// hooks/useSubscriptionTemplates.ts
export function useSubscriptionTemplates() {
  return useQuery({
    queryKey: ['subscription-templates'],
    queryFn: async () => {
      const response = await api.get('/api/v2/subscription-templates');
      if (!response.data.success) {
        throw new Error(response.data.error);
      }
      return response.data.data;
    },
    staleTime: 10 * 60 * 1000, // 10分钟，模板变化不频繁
  });
}

// hooks/useSyncHistory.ts
export function useSyncHistory(subscriptionId: number) {
  return useQuery({
    queryKey: ['sync-history', subscriptionId],
    queryFn: async () => {
      const response = await api.get(`/api/v2/subscriptions/${subscriptionId}/history`);
      if (!response.data.success) {
        throw new Error(response.data.error);
      }
      return response.data.data;
    },
    enabled: !!subscriptionId,
    refetchInterval: 30000, // 30秒刷新一次，获取最新状态
  });
}
```

### 实时状态更新

```typescript
// hooks/useRealtimeSync.ts
export function useRealtimeSync() {
  const [syncingSubscriptions, setSyncingSubscriptions] = useState<Set<number>>(new Set());
  
  // 可以使用WebSocket或者定时轮询
  useEffect(() => {
    const interval = setInterval(async () => {
      if (syncingSubscriptions.size > 0) {
        // 检查正在同步的订阅状态
        const updates = await checkSyncStatus(Array.from(syncingSubscriptions));
        // 更新状态...
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [syncingSubscriptions]);
  
  const startSync = (subscriptionId: number) => {
    setSyncingSubscriptions(prev => new Set([...prev, subscriptionId]));
  };
  
  const stopSync = (subscriptionId: number) => {
    setSyncingSubscriptions(prev => {
      const newSet = new Set(prev);
      newSet.delete(subscriptionId);
      return newSet;
    });
  };
  
  return { syncingSubscriptions, startSync, stopSync };
}
```

## 🎯 UI/UX设计规范

### 1. 颜色和图标体系

```css
/* 订阅源类型颜色 */
.source-ieee { --color: #1f77b4; }
.source-elsevier { --color: #ff7f0e; }
.source-dblp { --color: #2ca02c; }

/* 状态颜色 */
.status-active { --color: #28a745; }
.status-paused { --color: #ffc107; }
.status-error { --color: #dc3545; }
.status-syncing { --color: #17a2b8; }
```

### 2. 图标使用规范

```jsx
// 订阅源图标
const SourceIcon = ({ type, size = 24 }) => {
  const icons = {
    ieee: <IEEEIcon size={size} />,
    elsevier: <ElsevierIcon size={size} />,
    dblp: <DBLPIcon size={size} />
  };
  return icons[type] || <DefaultIcon size={size} />;
};

// 状态图标
const StatusIcon = ({ status, size = 16 }) => {
  const icons = {
    active: <CheckCircleIcon className="text-green-500" size={size} />,
    paused: <PauseCircleIcon className="text-yellow-500" size={size} />,
    error: <XCircleIcon className="text-red-500" size={size} />,
    syncing: <RefreshIcon className="text-blue-500 animate-spin" size={size} />
  };
  return icons[status];
};
```

### 3. 响应式断点

```css
/* Tailwind CSS 配置或自定义 CSS */
@media (max-width: 640px) {
  .subscription-card {
    @apply flex-col;
  }
  .card-actions {
    @apply w-full mt-4;
  }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .subscription-grid {
    @apply grid-cols-2;
  }
}

@media (min-width: 1025px) {
  .subscription-grid {
    @apply grid-cols-3;
  }
}
```

## ⚠️ 错误处理机制

### 1. API错误分类处理

```typescript
// utils/errorHandler.ts
export class SubscriptionError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'SubscriptionError';
  }
}

export function handleApiError(error: any): SubscriptionError {
  if (error.response?.status === 400) {
    return new SubscriptionError(
      error.response.data.error || '请求参数错误',
      'VALIDATION_ERROR',
      400
    );
  }
  
  if (error.response?.status === 401) {
    return new SubscriptionError('请先登录', 'AUTH_ERROR', 401);
  }
  
  if (error.response?.status === 403) {
    return new SubscriptionError('权限不足', 'PERMISSION_ERROR', 403);
  }
  
  if (error.response?.status === 404) {
    return new SubscriptionError('资源不存在', 'NOT_FOUND', 404);
  }
  
  if (error.response?.status >= 500) {
    return new SubscriptionError('服务器内部错误，请稍后重试', 'SERVER_ERROR', 500);
  }
  
  return new SubscriptionError('网络错误，请检查网络连接', 'NETWORK_ERROR');
}
```

### 2. 表单验证

```typescript
// utils/validation.ts
import Ajv from 'ajv';

const ajv = new Ajv({ allErrors: true });

export function validateSubscriptionParams(
  params: Record<string, any>,
  schema: JSONSchema
): { valid: boolean; errors: string[] } {
  const validate = ajv.compile(schema);
  const valid = validate(params);
  
  if (!valid) {
    const errors = validate.errors?.map(error => {
      switch (error.keyword) {
        case 'required':
          return `${error.params.missingProperty} 是必填字段`;
        case 'pattern':
          return `${error.instancePath.slice(1)} 格式不正确`;
        case 'minimum':
          return `${error.instancePath.slice(1)} 不能小于 ${error.params.limit}`;
        case 'maximum':
          return `${error.instancePath.slice(1)} 不能大于 ${error.params.limit}`;
        default:
          return `${error.instancePath.slice(1)} ${error.message}`;
      }
    }) || [];
    
    return { valid: false, errors };
  }
  
  return { valid: true, errors: [] };
}
```

### 3. 全局错误边界

```jsx
// components/ErrorBoundary.tsx
class SubscriptionErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Subscription Error:', error, errorInfo);
    // 发送错误报告到监控系统
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={() => this.setState({ hasError: false, error: null })}
        />
      );
    }

    return this.props.children;
  }
}

const ErrorFallback = ({ error, onRetry }) => (
  <div className="error-boundary">
    <h2>出现了一些问题</h2>
    <details style={{ whiteSpace: 'pre-wrap' }}>
      {error && error.toString()}
    </details>
    <button onClick={onRetry}>重试</button>
  </div>
);
```

## 💻 实现示例代码

### 1. 完整的订阅创建页面实现

```jsx
// pages/CreateSubscriptionPage.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSubscriptionTemplates, useCreateSubscription } from '../hooks/subscriptions';
import { validateSubscriptionParams } from '../utils/validation';
import { DynamicForm } from '../components/DynamicForm';

export function CreateSubscriptionPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();
  
  const { data: templates, isLoading } = useSubscriptionTemplates();
  const createSubscription = useCreateSubscription();
  
  const [formData, setFormData] = useState({
    name: '',
    source_params: {},
    sync_frequency: 86400
  });
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  const template = templates?.find(t => t.id === parseInt(templateId || ''));
  
  useEffect(() => {
    if (template) {
      setFormData(prev => ({
        ...prev,
        name: `我的${template.name}`,
        source_params: { ...template.example_params }
      }));
    }
  }, [template]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!template) return;
    
    // 验证参数
    const validation = validateSubscriptionParams(
      formData.source_params, 
      template.parameter_schema
    );
    
    if (!validation.valid) {
      setValidationErrors(validation.errors);
      return;
    }
    
    try {
      await createSubscription.mutateAsync({
        template_id: template.id,
        name: formData.name,
        source_params: formData.source_params,
        sync_frequency: formData.sync_frequency
      });
      
      navigate('/subscriptions');
    } catch (error) {
      // 错误已在mutation中处理
    }
  };
  
  const handleParamsChange = (fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      source_params: {
        ...prev.source_params,
        [fieldName]: value
      }
    }));
    
    // 清除该字段的验证错误
    setValidationErrors(prev => 
      prev.filter(error => !error.includes(fieldName))
    );
  };
  
  if (isLoading) {
    return <PageSkeleton />;
  }
  
  if (!template) {
    return <NotFoundPage message="订阅模板不存在" />;
  }
  
  return (
    <div className="create-subscription-page">
      <PageHeader>
        <BackButton onClick={() => navigate(-1)} />
        <div>
          <h1>创建 {template.name}</h1>
          <p className="text-gray-600">{template.description}</p>
        </div>
      </PageHeader>
      
      <form onSubmit={handleSubmit} className="form-container">
        {/* 基本信息 */}
        <FormSection title="基本信息">
          <Input
            label="订阅名称"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            required
            placeholder={`我的${template.name}`}
          />
        </FormSection>
        
        {/* 参数配置 */}
        <FormSection title="参数配置">
          <DynamicForm
            schema={template.parameter_schema}
            values={formData.source_params}
            onChange={handleParamsChange}
            examples={template.example_params}
            errors={validationErrors}
          />
        </FormSection>
        
        {/* 同步设置 */}
        <FormSection title="同步设置">
          <Select
            label="同步频率"
            value={formData.sync_frequency}
            onChange={(value) => setFormData(prev => ({ ...prev, sync_frequency: value }))}
            options={[
              { value: 3600, label: '每小时' },
              { value: 21600, label: '每6小时' },
              { value: 43200, label: '每12小时' },
              { value: 86400, label: '每天' },
              { value: 604800, label: '每周' }
            ]}
          />
        </FormSection>
        
        {/* 错误提示 */}
        {validationErrors.length > 0 && (
          <ErrorAlert>
            <ul>
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </ErrorAlert>
        )}
        
        {/* 操作按钮 */}
        <FormActions>
          <Button
            type="submit"
            loading={createSubscription.isPending}
            disabled={!formData.name || Object.keys(formData.source_params).length === 0}
          >
            创建订阅
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/subscriptions/templates')}
          >
            取消
          </Button>
        </FormActions>
      </form>
    </div>
  );
}
```

### 2. 动态表单组件实现

```jsx
// components/DynamicForm.tsx
import React from 'react';
import { JSONSchema } from '../types/subscription';

interface DynamicFormProps {
  schema: JSONSchema;
  values: Record<string, any>;
  onChange: (fieldName: string, value: any) => void;
  examples: Record<string, any>;
  errors: string[];
}

export function DynamicForm({ schema, values, onChange, examples, errors }: DynamicFormProps) {
  const renderField = (fieldName: string, fieldSchema: any) => {
    const isRequired = schema.required?.includes(fieldName);
    const fieldError = errors.find(error => error.includes(fieldName));
    const fieldValue = values[fieldName];
    const exampleValue = examples[fieldName];
    
    const commonProps = {
      label: fieldSchema.description || fieldName,
      required: isRequired,
      error: fieldError,
      helperText: exampleValue ? `示例: ${exampleValue}` : undefined
    };
    
    switch (fieldSchema.type) {
      case 'string':
        if (fieldSchema.enum) {
          return (
            <Select
              {...commonProps}
              value={fieldValue || ''}
              onChange={(value) => onChange(fieldName, value)}
              options={fieldSchema.enum.map(option => ({
                value: option,
                label: option
              }))}
            />
          );
        }
        
        return (
          <Input
            {...commonProps}
            type="text"
            value={fieldValue || ''}
            onChange={(e) => onChange(fieldName, e.target.value)}
            placeholder={exampleValue}
            pattern={fieldSchema.pattern}
          />
        );
      
      case 'number':
      case 'integer':
        return (
          <NumberInput
            {...commonProps}
            value={fieldValue || fieldSchema.default || 0}
            onChange={(value) => onChange(fieldName, value)}
            min={fieldSchema.minimum}
            max={fieldSchema.maximum}
            step={fieldSchema.type === 'integer' ? 1 : 0.1}
          />
        );
      
      case 'boolean':
        return (
          <Checkbox
            {...commonProps}
            checked={fieldValue !== undefined ? fieldValue : fieldSchema.default}
            onChange={(checked) => onChange(fieldName, checked)}
          />
        );
      
      case 'array':
        if (fieldSchema.items?.type === 'string') {
          return (
            <TagInput
              {...commonProps}
              value={fieldValue || []}
              onChange={(tags) => onChange(fieldName, tags)}
              placeholder="输入后按回车添加"
            />
          );
        }
        break;
      
      default:
        return (
          <div className="unsupported-field">
            <span>不支持的字段类型: {fieldSchema.type}</span>
          </div>
        );
    }
  };
  
  if (!schema.properties) {
    return <div>无参数配置</div>;
  }
  
  return (
    <div className="dynamic-form space-y-4">
      {Object.entries(schema.properties).map(([fieldName, fieldSchema]) => (
        <FormField key={fieldName}>
          {renderField(fieldName, fieldSchema)}
        </FormField>
      ))}
    </div>
  );
}
```

这个详细的对接文档应该能够帮助前端开发者完整实现新订阅管理系统的界面和功能。文档包含了完整的API规范、数据类型、组件设计、状态管理、错误处理和实现示例，可以直接用于开发指导。