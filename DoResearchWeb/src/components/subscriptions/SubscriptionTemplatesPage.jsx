import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    CardActions,
    Button,
    Grid,
    Chip,
    CircularProgress,
    Alert,
    TextField,
    InputAdornment,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Badge,
    Paper
} from '@mui/material';
import {
    Search as SearchIcon,
    Add as AddIcon,
    Code as CodeIcon,
    Description as DescriptionIcon,
    CheckCircle as CheckCircleIcon,
    Schedule as ScheduleIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import subscriptionClient from '../../services/subscriptionClient.jsx';
import { SOURCE_TYPE_CONFIGS } from '../../types/subscription.ts';

// 订阅模板卡片组件
const TemplateCard = ({ template, onSelect }) => {
    const sourceConfig = SOURCE_TYPE_CONFIGS[template.source_type] || {
        name: template.source_type,
        displayName: template.source_type.toUpperCase(),
        color: '#666666',
        description: '未知订阅源类型'
    };

    return (
        <Card
            sx={{
                height: 200, // 减少高度从280到200
                display: 'flex',
                flexDirection: 'column',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'visible',
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                    '& .action-buttons': {
                        opacity: 1,
                        transform: 'translateY(0)'
                    }
                }
            }}
            onClick={() => onSelect(template)}
        >
            {/* 状态指示器 */}
            <Box
                sx={{
                    position: 'absolute',
                    top: 12,
                    right: 12,
                    zIndex: 1
                }}
            >
                {template.active ? (
                    <Chip
                        icon={<CheckCircleIcon />}
                        label="可用"
                        size="small"
                        color="success"
                        sx={{ fontSize: '0.75rem' }}
                    />
                ) : (
                    <Chip
                        label="维护中"
                        size="small"
                        color="default"
                        sx={{ fontSize: '0.75rem' }}
                    />
                )}
            </Box>

            <CardContent sx={{ flexGrow: 1, pb: 0, pt: 2, px: 2 }}>
                {/* 订阅源类型标识 */}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                        sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '8px',
                            background: `linear-gradient(135deg, ${sourceConfig.color}20, ${sourceConfig.color}40)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            mr: 1.5,
                            border: `1px solid ${sourceConfig.color}30`,
                            overflow: 'hidden'
                        }}
                    >
                        {/* 根据不同的订阅源类型显示不同的logo */}
                        {template.source_type === 'ieee' && (
                            <Box
                                sx={{
                                    width: 32,
                                    height: 32,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: '#fff',
                                    borderRadius: '4px',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                                }}
                            >
                                <Typography
                                    sx={{
                                        fontWeight: 800,
                                        fontSize: '0.6rem',
                                        color: '#005496',
                                        fontFamily: 'Arial, sans-serif'
                                    }}
                                >
                                    IEEE
                                </Typography>
                            </Box>
                        )}
                        {template.source_type === 'elsevier' && (
                            <Box
                                sx={{
                                    width: 32,
                                    height: 32,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: '#fff',
                                    borderRadius: '4px',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                                }}
                            >
                                <Typography
                                    sx={{
                                        fontWeight: 700,
                                        fontSize: '0.5rem',
                                        color: '#FF6C00',
                                        fontFamily: 'Arial, sans-serif'
                                    }}
                                >
                                    Elsevier
                                </Typography>
                            </Box>
                        )}
                        {template.source_type === 'dblp' && (
                            <Box
                                sx={{
                                    width: 32,
                                    height: 32,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: '#fff',
                                    borderRadius: '4px',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                                }}
                            >
                                <Typography
                                    sx={{
                                        fontWeight: 800,
                                        fontSize: '0.6rem',
                                        color: '#1f4e79',
                                        fontFamily: 'Arial, sans-serif'
                                    }}
                                >
                                    dblp
                                </Typography>
                            </Box>
                        )}
                        {!['ieee', 'elsevier', 'dblp'].includes(template.source_type) && (
                            <Typography
                                variant="caption"
                                sx={{
                                    fontWeight: 700,
                                    color: sourceConfig.color,
                                    fontSize: '0.7rem'
                                }}
                            >
                                {sourceConfig.displayName.substring(0, 3)}
                            </Typography>
                        )}
                    </Box>
                    <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                            {template.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            {sourceConfig.displayName}
                        </Typography>
                    </Box>
                </Box>

                {/* 描述 */}
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                        mb: 1,
                        display: '-webkit-box',
                        WebkitLineClamp: 2, // 减少到2行
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        lineHeight: 1.4,
                        minHeight: '2.8rem' // 减少固定描述区域高度
                    }}
                >
                    {template.description}
                </Typography>
            </CardContent>

            <CardActions
                className="action-buttons"
                sx={{
                    p: 1.5, // 减少padding
                    pt: 1, // 减少顶部padding
                    opacity: 0,
                    transform: 'translateY(10px)',
                    transition: 'all 0.2s ease'
                }}
            >
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    fullWidth
                    disabled={!template.active}
                    sx={{
                        fontWeight: 600,
                        background: `linear-gradient(135deg, ${sourceConfig.color}, ${sourceConfig.color}dd)`,
                        '&:hover': {
                            background: `linear-gradient(135deg, ${sourceConfig.color}dd, ${sourceConfig.color})`
                        }
                    }}
                    onClick={(e) => {
                        e.stopPropagation();
                        onSelect(template);
                    }}
                >
                    立即订阅
                </Button>
            </CardActions>
        </Card>
    );
};

// 主页面组件
const SubscriptionTemplatesPage = () => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState('all');
    
    const navigate = useNavigate();

    // 加载订阅模板
    const loadTemplates = async () => {
        try {
            setLoading(true);
            setError(null);
            const templatesData = await subscriptionClient.getSubscriptionTemplates();
            setTemplates(templatesData || []);
        } catch (err) {
            console.error('加载订阅模板失败:', err);
            setError(err.message || '加载失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadTemplates();
    }, []);

    // 过滤模板
    const filteredTemplates = templates.filter(template => {
        const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            template.description.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesType = filterType === 'all' || template.source_type === filterType;
        return matchesSearch && matchesType;
    });

    // 处理模板选择
    const handleTemplateSelect = (template) => {
        navigate(`/subscriptions/create/${template.id}`, {
            state: { template }
        });
    };

    // 获取可用的订阅源类型
    const availableTypes = [...new Set(templates.map(t => t.source_type))];

    return (
        <Box sx={{ p: 3, maxWidth: '1400px', margin: '0 auto' }}>
            {/* 页面标题和描述 */}
            <Box sx={{ mb: 4, textAlign: 'center' }}>
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: 700,
                        background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        mb: 1
                    }}
                >
                    选择订阅类型
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
                    从下方选择您感兴趣的论文来源，我们将为您自动获取最新发表的论文
                </Typography>
            </Box>

            {/* 搜索和过滤 */}
            <Box
                sx={{
                    display: 'flex',
                    gap: 2,
                    mb: 4,
                    flexDirection: { xs: 'column', md: 'row' },
                    alignItems: { xs: 'stretch', md: 'center' }
                }}
            >
                <TextField
                    placeholder="搜索订阅类型..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon color="action" />
                            </InputAdornment>
                        )
                    }}
                    sx={{ flex: 1 }}
                />

                <FormControl sx={{ minWidth: 200 }}>
                    <InputLabel>订阅源类型</InputLabel>
                    <Select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        label="订阅源类型"
                    >
                        <MenuItem value="all">全部类型</MenuItem>
                        {availableTypes.map(type => (
                            <MenuItem key={type} value={type}>
                                {SOURCE_TYPE_CONFIGS[type]?.displayName || type.toUpperCase()}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <Button
                    variant="outlined"
                    onClick={loadTemplates}
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={16} sx={{ color: '#1976d2' }} /> : <DescriptionIcon />}
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
                    刷新
                </Button>
            </Box>

            {/* 错误提示 */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* 加载状态 */}
            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
                    <CircularProgress />
                    <Typography sx={{ ml: 2 }} color="text.secondary">
                        正在加载订阅模板...
                    </Typography>
                </Box>
            ) : (
                <>
                    {/* 统计信息 */}
                    {filteredTemplates.length > 0 && (
                        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                            <Typography variant="body2" color="text.secondary">
                                找到 {filteredTemplates.length} 个订阅模板
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                {availableTypes.map(type => {
                                    const count = filteredTemplates.filter(t => t.source_type === type).length;
                                    if (count === 0) return null;
                                    const config = SOURCE_TYPE_CONFIGS[type];
                                    return (
                                        <Chip
                                            key={type}
                                            label={`${config?.displayName || type} (${count})`}
                                            size="small"
                                            sx={{
                                                bgcolor: `${config?.color}20`,
                                                color: config?.color,
                                                border: `1px solid ${config?.color}30`,
                                                fontSize: '0.75rem'
                                            }}
                                        />
                                    );
                                })}
                            </Box>
                        </Box>
                    )}

                    {/* 模板网格 */}
                    {filteredTemplates.length === 0 ? (
                        <Paper
                            sx={{
                                p: 6,
                                textAlign: 'center',
                                bgcolor: 'grey.50',
                                border: '2px dashed',
                                borderColor: 'grey.300'
                            }}
                        >
                            <DescriptionIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                                {searchTerm || filterType !== 'all' ? '未找到匹配的订阅模板' : '暂无可用的订阅模板'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                {searchTerm || filterType !== 'all'
                                    ? '请尝试调整搜索条件或过滤器'
                                    : '管理员正在配置订阅模板，请稍后再试'
                                }
                            </Typography>
                            {(searchTerm || filterType !== 'all') && (
                                <Button
                                    variant="text"
                                    sx={{ mt: 2 }}
                                    onClick={() => {
                                        setSearchTerm('');
                                        setFilterType('all');
                                    }}
                                >
                                    清除筛选条件
                                </Button>
                            )}
                        </Paper>
                    ) : (
                        <Box
                            sx={{
                                display: 'grid',
                                gridTemplateColumns: {
                                    xs: '1fr',
                                    sm: 'repeat(2, 1fr)', 
                                    md: 'repeat(3, 1fr)',
                                    lg: 'repeat(4, 1fr)'
                                },
                                gap: 3
                            }}
                        >
                            {filteredTemplates.map(template => (
                                <TemplateCard
                                    key={template.id}
                                    template={template}
                                    onSelect={handleTemplateSelect}
                                />
                            ))}
                        </Box>
                    )}
                </>
            )}

            {/* 返回按钮 */}
            <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Button
                    variant="text"
                    onClick={() => navigate('/subscriptions')}
                    sx={{ 
                        color: '#1976d2',
                        fontWeight: 500,
                        '&:hover': {
                            background: 'rgba(25, 118, 210, 0.04)',
                            transform: 'translateY(-1px)',
                        },
                        transition: 'all 0.2s ease'
                    }}
                >
                    返回我的订阅
                </Button>
            </Box>
        </Box>
    );
};

export default SubscriptionTemplatesPage;