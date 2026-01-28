import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Button,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    FormControlLabel,
    Checkbox,
    Alert,
    Paper,
    Divider,
    IconButton,
    Chip,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions
} from '@mui/material';
import {
    ArrowBack as ArrowBackIcon,
    Info as InfoIcon,
    Code as CodeIcon,
    Preview as PreviewIcon,
    Check as CheckIcon,
    Error as ErrorIcon
} from '@mui/icons-material';
import { useParams, useNavigate, useLocation } from 'react-router-dom';

import subscriptionClient from '../../services/subscriptionClient.jsx';
import { SYNC_FREQUENCY_OPTIONS, SOURCE_TYPE_CONFIGS } from '../../types/subscription.ts';

// 动态表单字段组件
const DynamicFormField = ({ fieldName, fieldSchema, value, onChange, example, error }) => {
    const isRequired = fieldSchema.required;

    const renderField = () => {
        switch (fieldSchema.type) {
            case 'string':
                if (fieldSchema.enum) {
                    return (
                        <FormControl fullWidth>
                            <InputLabel>{fieldSchema.description || fieldName}</InputLabel>
                            <Select
                                value={value || ''}
                                onChange={(e) => onChange(fieldName, e.target.value)}
                                label={fieldSchema.description || fieldName}
                            >
                                {fieldSchema.enum.map(option => (
                                    <MenuItem key={option} value={option}>
                                        {option}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    );
                }

                return (
                    <TextField
                        fullWidth
                        label={fieldSchema.description || fieldName}
                        value={value || ''}
                        onChange={(e) => onChange(fieldName, e.target.value)}
                        placeholder={example ? `例如: ${example}` : undefined}
                        required={isRequired}
                        error={!!error}
                        helperText={error || (example ? `示例: ${example}` : fieldSchema.description)}
                        inputProps={{
                            pattern: fieldSchema.pattern
                        }}
                    />
                );

            case 'number':
            case 'integer':
                return (
                    <TextField
                        fullWidth
                        type="number"
                        label={fieldSchema.description || fieldName}
                        value={value || fieldSchema.default || ''}
                        onChange={(e) => onChange(fieldName, e.target.valueAsNumber || e.target.value)}
                        required={isRequired}
                        error={!!error}
                        helperText={error || (example ? `示例: ${example}` : fieldSchema.description)}
                        inputProps={{
                            min: fieldSchema.minimum,
                            max: fieldSchema.maximum,
                            step: fieldSchema.type === 'integer' ? 1 : 'any'
                        }}
                    />
                );

            case 'boolean':
                return (
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={value !== undefined ? value : (fieldSchema.default || false)}
                                onChange={(e) => onChange(fieldName, e.target.checked)}
                            />
                        }
                        label={fieldSchema.description || fieldName}
                    />
                );

            default:
                return (
                    <Alert severity="warning">
                        不支持的字段类型: {fieldSchema.type}
                    </Alert>
                );
        }
    };

    return (
        <Box sx={{ mb: 3 }}>
            {renderField()}
            {error && (
                <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                    {error}
                </Typography>
            )}
        </Box>
    );
};

// 动态表单组件
const DynamicForm = ({ schema, values, onChange, examples, errors = [] }) => {
    if (!schema || !schema.properties) {
        return (
            <Alert severity="info">
                该订阅类型无需额外配置参数
            </Alert>
        );
    }

    return (
        <Box>
            {Object.entries(schema.properties).map(([fieldName, fieldSchema]) => {
                const fieldError = errors.find(error => error.includes(fieldName));
                const fieldValue = values[fieldName];
                const exampleValue = examples[fieldName];

                return (
                    <DynamicFormField
                        key={fieldName}
                        fieldName={fieldName}
                        fieldSchema={{
                            ...fieldSchema,
                            required: schema.required?.includes(fieldName)
                        }}
                        value={fieldValue}
                        onChange={onChange}
                        example={exampleValue}
                        error={fieldError}
                    />
                );
            })}
        </Box>
    );
};

// 创建订阅页面
const CreateSubscriptionPage = () => {
    const { templateId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    // 状态
    const [template, setTemplate] = useState(location.state?.template || null);
    const [loading, setLoading] = useState(!template);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState(null);
    const [validationErrors, setValidationErrors] = useState([]);
    const [showPreview, setShowPreview] = useState(false);

    // 表单数据
    const [formData, setFormData] = useState({
        name: '',
        source_params: {},
        sync_frequency: 86400 // 默认每天
    });

    // 加载模板详情
    const loadTemplate = async () => {
        try {
            setLoading(true);
            setError(null);
            const templateData = await subscriptionClient.getSubscriptionTemplate(templateId);
            setTemplate(templateData);
            
            // 设置默认表单数据
            setFormData(prev => ({
                ...prev,
                name: `我的${templateData.name}`,
                source_params: { ...templateData.example_params }
            }));
        } catch (err) {
            console.error('加载模板失败:', err);
            setError(err.message || '加载模板失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!template && templateId) {
            loadTemplate();
        } else if (template) {
            // 设置默认表单数据
            setFormData(prev => ({
                ...prev,
                name: `我的${template.name}`,
                source_params: { ...template.example_params }
            }));
        }
    }, [template, templateId]);

    // 处理参数变更
    const handleParamChange = (fieldName, value) => {
        setFormData(prev => ({
            ...prev,
            source_params: {
                ...prev.source_params,
                [fieldName]: value
            }
        }));

        // 清除相关验证错误
        setValidationErrors(prev => 
            prev.filter(error => !error.includes(fieldName))
        );
    };

    // 处理表单提交
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!template) return;

        // 验证参数
        const validation = subscriptionClient.validateSubscriptionParams(
            formData.source_params,
            template.parameter_schema
        );

        if (!validation.valid) {
            setValidationErrors(validation.errors);
            return;
        }

        try {
            setCreating(true);
            setError(null);

            await subscriptionClient.createSubscription({
                template_id: template.id,
                name: formData.name,
                source_params: formData.source_params,
                sync_frequency: formData.sync_frequency
            });

            // 通知侧边栏刷新订阅列表
            window.dispatchEvent(new CustomEvent('subscription-list-updated'));

            // 创建成功，跳转到订阅列表
            navigate('/subscriptions', {
                state: { message: '订阅创建成功！' }
            });
        } catch (err) {
            console.error('创建订阅失败:', err);
            setError(err.message || '创建订阅失败');
        } finally {
            setCreating(false);
        }
    };

    // 获取同步频率选项
    const getSyncFrequencyLabel = (seconds) => {
        const option = SYNC_FREQUENCY_OPTIONS.find(opt => opt.value === seconds);
        return option ? option.label : `${seconds} 秒`;
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }} color="text.secondary">
                    正在加载订阅模板...
                </Typography>
            </Box>
        );
    }

    if (!template) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    订阅模板不存在或加载失败
                    <Button 
                        sx={{ 
                            ml: 2,
                            background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                            border: '1px solid rgba(25, 118, 210, 0.2)',
                            color: '#1976d2',
                            fontWeight: 600,
                            '&:hover': {
                                background: 'linear-gradient(135deg, #bbdefb 0%, #90caf9 100%)',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(25, 118, 210, 0.2)',
                            },
                            transition: 'all 0.2s ease'
                        }} 
                        onClick={() => navigate('/subscriptions/templates')}
                    >
                        返回模板列表
                    </Button>
                </Alert>
            </Box>
        );
    }

    const sourceConfig = SOURCE_TYPE_CONFIGS[template.source_type] || {
        displayName: template.source_type.toUpperCase(),
        color: '#666666'
    };

    return (
        <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
            {/* 页面标题 */}
            <Box sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <IconButton
                        onClick={() => navigate('/subscriptions/templates')}
                        sx={{ mr: 1 }}
                    >
                        <ArrowBackIcon />
                    </IconButton>
                    <Box>
                        <Typography variant="h5" sx={{ fontWeight: 600 }}>
                            创建 {template.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {template.description}
                        </Typography>
                    </Box>
                </Box>

                {/* 订阅源信息卡片 */}
                <Card sx={{ mb: 3, border: `2px solid ${sourceConfig.color}30` }}>
                    <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                        <Box
                            sx={{
                                width: 48,
                                height: 48,
                                borderRadius: 2,
                                background: `linear-gradient(135deg, ${sourceConfig.color}20, ${sourceConfig.color}40)`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                mr: 2
                            }}
                        >
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                    color: sourceConfig.color,
                                    fontSize: '0.8rem'
                                }}
                            >
                                {sourceConfig.displayName.substring(0, 3)}
                            </Typography>
                        </Box>
                        <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {sourceConfig.displayName}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                {template.description}
                            </Typography>
                        </Box>
                        <Chip
                            icon={<CheckIcon />}
                            label="已激活"
                            color="success"
                            size="small"
                        />
                    </CardContent>
                </Card>
            </Box>

            {/* 创建表单 */}
            <form onSubmit={handleSubmit}>
                {/* 基本信息 */}
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                        <InfoIcon sx={{ mr: 1 }} />
                        基本信息
                    </Typography>
                    <TextField
                        fullWidth
                        label="订阅名称"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        required
                        placeholder={`我的${template.name}`}
                        sx={{ mb: 3 }}
                    />
                    
                    <FormControl fullWidth>
                        <InputLabel>同步频率</InputLabel>
                        <Select
                            value={formData.sync_frequency}
                            onChange={(e) => setFormData(prev => ({ ...prev, sync_frequency: e.target.value }))}
                            label="同步频率"
                        >
                            {SYNC_FREQUENCY_OPTIONS.map(option => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                    {option.description && (
                                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                            - {option.description}
                                        </Typography>
                                    )}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Paper>

                {/* 参数配置 */}
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                        <CodeIcon sx={{ mr: 1 }} />
                        参数配置
                    </Typography>
                    
                    <DynamicForm
                        schema={template.parameter_schema}
                        values={formData.source_params}
                        onChange={handleParamChange}
                        examples={template.example_params}
                        errors={validationErrors}
                    />
                </Paper>

                {/* 错误提示 */}
                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}

                {/* 验证错误提示 */}
                {validationErrors.length > 0 && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                            请修复以下错误:
                        </Typography>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                            {validationErrors.map((error, index) => (
                                <li key={index}>
                                    <Typography variant="body2">{error}</Typography>
                                </li>
                            ))}
                        </ul>
                    </Alert>
                )}

                {/* 操作按钮 */}
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                        variant="outlined"
                        startIcon={<PreviewIcon />}
                        onClick={() => setShowPreview(true)}
                        disabled={creating}
                        sx={{
                            border: '1px solid rgba(25, 118, 210, 0.3)',
                            color: '#1976d2',
                            fontWeight: 500,
                            '&:hover': {
                                background: 'rgba(25, 118, 210, 0.04)',
                                transform: 'translateY(-1px)',
                                borderColor: 'rgba(25, 118, 210, 0.5)',
                            },
                            '&:disabled': {
                                border: '1px solid rgba(25, 118, 210, 0.1)',
                                color: 'rgba(25, 118, 210, 0.3)',
                            },
                            transition: 'all 0.2s ease'
                        }}
                    >
                        预览配置
                    </Button>
                    <Button
                        variant="outlined"
                        onClick={() => navigate('/subscriptions/templates')}
                        disabled={creating}
                        sx={{
                            border: '1px solid rgba(25, 118, 210, 0.3)',
                            color: '#1976d2',
                            fontWeight: 500,
                            '&:hover': {
                                background: 'rgba(25, 118, 210, 0.04)',
                                transform: 'translateY(-1px)',
                                borderColor: 'rgba(25, 118, 210, 0.5)',
                            },
                            '&:disabled': {
                                border: '1px solid rgba(25, 118, 210, 0.1)',
                                color: 'rgba(25, 118, 210, 0.3)',
                            },
                            transition: 'all 0.2s ease'
                        }}
                    >
                        取消
                    </Button>
                    <Button
                        type="submit"
                        variant="contained"
                        disabled={creating || !formData.name.trim()}
                        startIcon={creating ? <CircularProgress size={16} sx={{ color: '#1976d2' }} /> : <CheckIcon />}
                        sx={{
                            background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                            border: '1px solid rgba(25, 118, 210, 0.2)',
                            color: '#1976d2',
                            fontWeight: 600,
                            '&:hover': {
                                background: 'linear-gradient(135deg, #bbdefb 0%, #90caf9 100%)',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(25, 118, 210, 0.2)',
                            },
                            '&:disabled': {
                                background: 'linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%)',
                                color: 'rgba(25, 118, 210, 0.5)',
                                border: '1px solid rgba(25, 118, 210, 0.1)',
                            },
                            transition: 'all 0.2s ease'
                        }}
                    >
                        {creating ? '创建中...' : '创建订阅'}
                    </Button>
                </Box>
            </form>

            {/* 预览对话框 */}
            <Dialog
                open={showPreview}
                onClose={() => setShowPreview(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    订阅配置预览
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                            订阅名称
                        </Typography>
                        <Typography variant="body1">
                            {formData.name}
                        </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                            订阅类型
                        </Typography>
                        <Typography variant="body1">
                            {template.name} ({sourceConfig.displayName})
                        </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                            同步频率
                        </Typography>
                        <Typography variant="body1">
                            {getSyncFrequencyLabel(formData.sync_frequency)}
                        </Typography>
                    </Box>

                    {Object.keys(formData.source_params).length > 0 && (
                        <Box>
                            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                                配置参数
                            </Typography>
                            <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                                {Object.entries(formData.source_params).map(([key, value]) => (
                                    <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                            {key}:
                                        </Typography>
                                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                            {String(value)}
                                        </Typography>
                                    </Box>
                                ))}
                            </Paper>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={() => setShowPreview(false)}
                        sx={{
                            background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                            border: '1px solid rgba(25, 118, 210, 0.2)',
                            color: '#1976d2',
                            fontWeight: 600,
                            '&:hover': {
                                background: 'linear-gradient(135deg, #bbdefb 0%, #90caf9 100%)',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(25, 118, 210, 0.2)',
                            },
                            transition: 'all 0.2s ease'
                        }}
                    >
                        关闭
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default CreateSubscriptionPage;