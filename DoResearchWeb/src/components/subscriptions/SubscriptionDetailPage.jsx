import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Button,
    IconButton,
    Tabs,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    CircularProgress,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Divider,
    Pagination,
    Grid,
    Tooltip
} from '@mui/material';
import {
    ArrowBack as ArrowBackIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Sync as SyncIcon,
    Pause as PauseIcon,
    PlayArrow as PlayArrowIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Schedule as ScheduleIcon,
    Settings as SettingsIcon,
    Article as ArticleIcon,
    Info as InfoIcon,
    Refresh as RefreshIcon,
    AccessTime as AccessTimeIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

import subscriptionClient from '../../services/subscriptionClient.jsx';
import { SOURCE_TYPE_CONFIGS, SYNC_FREQUENCY_OPTIONS } from '../../types/subscription.ts';

// 同步历史列表组件
const SyncHistoryTimeline = ({ subscriptionId }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadHistory = async () => {
        try {
            setLoading(true);
            setError(null);
            const historyData = await subscriptionClient.getSubscriptionHistory(subscriptionId);
            setHistory(historyData || []);
        } catch (err) {
            console.error('加载同步历史失败:', err);
            setError(err.message || '加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadHistory();
    }, [subscriptionId]);

    const getStatusChip = (status) => {
        switch (status) {
            case 'success':
                return <Chip label="成功" size="small" color="success" />;
            case 'error':
                return <Chip label="失败" size="small" color="error" />;
            case 'running':
                return <Chip label="进行中" size="small" color="info" />;
            default:
                return <Chip label="未知" size="small" color="default" />;
        }
    };

    const formatDuration = (start, end) => {
        if (!end) return '-';
        const duration = new Date(end) - new Date(start);
        if (duration < 60000) {
            return `${Math.round(duration / 1000)}秒`;
        } else if (duration < 3600000) {
            return `${Math.round(duration / 60000)}分钟`;
        } else {
            return `${Math.round(duration / 3600000)}小时`;
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>加载同步历史...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ m: 2 }}>
                {error}
                <Button sx={{ ml: 2 }} onClick={loadHistory}
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
                    重试
                </Button>
            </Alert>
        );
    }

    if (history.length === 0) {
        return (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
                <ScheduleIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                    暂无同步历史
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    系统还未开始同步此订阅
                </Typography>
            </Paper>
        );
    }

    return (
        <Paper sx={{ overflow: 'hidden' }}>
            <TableContainer>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>状态</TableCell>
                            <TableCell>开始时间</TableCell>
                            <TableCell>完成时间</TableCell>
                            <TableCell>耗时</TableCell>
                            <TableCell>发现论文</TableCell>
                            <TableCell>新增论文</TableCell>
                            <TableCell>错误信息</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {history.map((record) => (
                            <TableRow key={record.id} hover>
                                <TableCell>
                                    {getStatusChip(record.status)}
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2">
                                        {new Date(record.sync_started_at).toLocaleString('zh-CN')}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2">
                                        {record.sync_completed_at 
                                            ? new Date(record.sync_completed_at).toLocaleString('zh-CN')
                                            : '-'
                                        }
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2">
                                        {formatDuration(record.sync_started_at, record.sync_completed_at)}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2">
                                        {record.papers_found || 0}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2">
                                        {record.papers_new || 0}
                                    </Typography>
                                </TableCell>
                                <TableCell>
                                    {record.error_details ? (
                                        <Tooltip title={record.error_details}>
                                            <Typography 
                                                variant="body2" 
                                                color="error"
                                                sx={{ 
                                                    maxWidth: 200,
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap',
                                                    cursor: 'help'
                                                }}
                                            >
                                                {record.error_details}
                                            </Typography>
                                        </Tooltip>
                                    ) : (
                                        <Typography variant="body2" color="text.secondary">
                                            -
                                        </Typography>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );
};

// 订阅论文列表组件
const SubscriptionPapers = ({ subscriptionId }) => {
    const [papers, setPapers] = useState([]);
    const [pagination, setPagination] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [statusFilter, setStatusFilter] = useState('all');

    const loadPapers = async (page = 1, status = 'all') => {
        try {
            setLoading(true);
            setError(null);
            const data = await subscriptionClient.getSubscriptionPapers(subscriptionId, {
                page,
                per_page: 20,
                status: status !== 'all' ? status : undefined
            });
            setPapers(data.papers || []);
            setPagination(data.pagination || {});
        } catch (err) {
            console.error('加载论文失败:', err);
            setError(err.message || '加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPapers(currentPage, statusFilter);
    }, [subscriptionId, currentPage, statusFilter]);

    const handlePageChange = (event, page) => {
        setCurrentPage(page);
    };

    const handleStatusFilterChange = (event) => {
        setStatusFilter(event.target.value);
        setCurrentPage(1);
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>加载论文列表...</Typography>
            </Box>
        );
    }

    return (
        <Box>
            {/* 过滤器 */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>状态过滤</InputLabel>
                    <Select
                        value={statusFilter}
                        onChange={handleStatusFilterChange}
                        label="状态过滤"
                    >
                        <MenuItem value="all">全部</MenuItem>
                        <MenuItem value="unread">未读</MenuItem>
                        <MenuItem value="reading">阅读中</MenuItem>
                        <MenuItem value="read">已读</MenuItem>
                    </Select>
                </FormControl>

                {pagination.total && (
                    <Typography variant="body2" color="text.secondary">
                        共 {pagination.total} 篇论文
                    </Typography>
                )}
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
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
                        onClick={() => loadPapers(currentPage, statusFilter)}
                    >
                        重试
                    </Button>
                </Alert>
            )}

            {papers.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                    <ArticleIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                        {statusFilter === 'all' ? '暂无论文' : `暂无${statusFilter === 'unread' ? '未读' : statusFilter === 'reading' ? '阅读中' : '已读'}论文`}
                    </Typography>
                </Box>
            ) : (
                <>
                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>标题</TableCell>
                                    <TableCell>作者</TableCell>
                                    <TableCell>发布日期</TableCell>
                                    <TableCell>状态</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {papers.map((paper) => (
                                    <TableRow key={paper.id} hover>
                                        <TableCell>
                                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                                {paper.title}
                                            </Typography>
                                            {paper.journal && (
                                                <Typography variant="caption" color="text.secondary">
                                                    {paper.journal}
                                                </Typography>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {paper.authors}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2">
                                                {new Date(paper.published_date).toLocaleDateString('zh-CN')}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={
                                                    paper.status === 'read' ? '已读' :
                                                    paper.status === 'reading' ? '阅读中' : '未读'
                                                }
                                                size="small"
                                                color={
                                                    paper.status === 'read' ? 'success' :
                                                    paper.status === 'reading' ? 'warning' : 'default'
                                                }
                                            />
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>

                    {/* 分页 */}
                    {pagination.pages > 1 && (
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                            <Pagination
                                count={pagination.pages}
                                page={currentPage}
                                onChange={handlePageChange}
                                color="primary"
                            />
                        </Box>
                    )}
                </>
            )}
        </Box>
    );
};

// 订阅设置组件
const SubscriptionSettings = ({ subscription, onUpdate }) => {
    const [editMode, setEditMode] = useState(false);
    const [formData, setFormData] = useState({
        name: subscription.name,
        sync_frequency: subscription.sync_frequency,
        status: subscription.status
    });
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        try {
            setSaving(true);
            await subscriptionClient.updateSubscription(subscription.id, formData);
            await onUpdate();
            setEditMode(false);
            
            // 通知侧边栏刷新订阅列表
            window.dispatchEvent(new CustomEvent('subscription-list-updated'));
        } catch (err) {
            console.error('更新订阅设置失败:', err);
        } finally {
            setSaving(false);
        }
    };

    const handleCancel = () => {
        setFormData({
            name: subscription.name,
            sync_frequency: subscription.sync_frequency,
            status: subscription.status
        });
        setEditMode(false);
    };

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6">
                        订阅设置
                    </Typography>
                    {!editMode ? (
                        <Button
                            startIcon={<EditIcon />}
                            onClick={() => setEditMode(true)}
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
                            编辑
                        </Button>
                    ) : (
                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button
                                onClick={handleCancel}
                                disabled={saving}
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
                                variant="contained"
                                onClick={handleSave}
                                disabled={saving}
                                startIcon={saving ? <CircularProgress size={16} sx={{ color: '#1976d2' }} /> : undefined}
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
                                保存
                            </Button>
                        </Box>
                    )}
                </Box>

                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="订阅名称"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            disabled={!editMode}
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                            <InputLabel>同步频率</InputLabel>
                            <Select
                                value={formData.sync_frequency}
                                onChange={(e) => setFormData(prev => ({ ...prev, sync_frequency: e.target.value }))}
                                label="同步频率"
                                disabled={!editMode}
                            >
                                {SYNC_FREQUENCY_OPTIONS.map(option => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                            <InputLabel>状态</InputLabel>
                            <Select
                                value={formData.status}
                                onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                                label="状态"
                                disabled={!editMode}
                            >
                                <MenuItem value="active">活跃</MenuItem>
                                <MenuItem value="paused">暂停</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
};

// 主页面组件
const SubscriptionDetailPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    const [subscription, setSubscription] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState(0);
    const [syncing, setSyncing] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    // 加载订阅详情
    const loadSubscription = async () => {
        try {
            setLoading(true);
            setError(null);
            const subscriptionData = await subscriptionClient.getSubscription(id);
            setSubscription(subscriptionData);
        } catch (err) {
            console.error('加载订阅详情失败:', err);
            setError(err.message || '加载失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (id) {
            loadSubscription();
        }
    }, [id]);

    // 手动同步
    const handleManualSync = async () => {
        try {
            setSyncing(true);
            await subscriptionClient.syncSubscription(id);
            await loadSubscription();
        } catch (err) {
            console.error('手动同步失败:', err);
            setError(err.message || '同步失败');
        } finally {
            setSyncing(false);
        }
    };

    // 删除订阅
    const handleDeleteSubscription = async () => {
        try {
            await subscriptionClient.deleteSubscription(id);
            
            // 通知侧边栏刷新订阅列表
            window.dispatchEvent(new CustomEvent('subscription-list-updated'));
            
            navigate('/subscriptions', {
                state: { message: '订阅已删除' }
            });
        } catch (err) {
            console.error('删除订阅失败:', err);
            setError(err.message || '删除失败');
        }
        setDeleteDialogOpen(false);
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>加载订阅详情...</Typography>
            </Box>
        );
    }

    if (error && !subscription) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    {error}
                    <Button sx={{ ml: 2 }} onClick={loadSubscription}
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
                        重试
                    </Button>
                </Alert>
            </Box>
        );
    }

    if (!subscription) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    订阅不存在
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
                        onClick={() => navigate('/subscriptions')}
                    >
                        返回订阅列表
                    </Button>
                </Alert>
            </Box>
        );
    }

    const sourceConfig = SOURCE_TYPE_CONFIGS[subscription.source_type] || {
        displayName: subscription.source_type?.toUpperCase() || 'UNKNOWN',
        color: '#666666'
    };

    return (
        <Box sx={{ p: { xs: 2, md: 3 }, maxWidth: '1400px', margin: '0 auto' }}>
            {/* 页面标题和操作按钮 */}
            <Paper sx={{ p: { xs: 2, md: 3 }, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <IconButton
                            onClick={() => navigate('/subscriptions')}
                            sx={{ mr: 1 }}
                        >
                            <ArrowBackIcon />
                        </IconButton>
                        <Box>
                            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                                {subscription.name}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Chip
                                    label={sourceConfig.displayName}
                                    size="small"
                                    sx={{
                                        bgcolor: `${sourceConfig.color}20`,
                                        color: sourceConfig.color,
                                        border: `1px solid ${sourceConfig.color}30`
                                    }}
                                />
                                <Chip
                                    label={subscription.status === 'active' ? '活跃' : subscription.status === 'paused' ? '暂停' : '错误'}
                                    size="small"
                                    color={
                                        subscription.status === 'active' ? 'success' :
                                        subscription.status === 'paused' ? 'warning' : 'error'
                                    }
                                />
                            </Box>
                        </Box>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                            variant="outlined"
                            startIcon={syncing ? <CircularProgress size={16} sx={{ color: '#1976d2' }} /> : <SyncIcon />}
                            onClick={handleManualSync}
                            disabled={syncing}
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
                            {syncing ? '同步中...' : '手动同步'}
                        </Button>
                        <Button
                            variant="outlined"
                            color="error"
                            startIcon={<DeleteIcon />}
                            onClick={() => setDeleteDialogOpen(true)}
                            sx={{
                                border: '1px solid rgba(211, 47, 47, 0.3)',
                                color: '#d32f2f',
                                fontWeight: 500,
                                '&:hover': {
                                    background: 'rgba(211, 47, 47, 0.04)',
                                    transform: 'translateY(-1px)',
                                    borderColor: 'rgba(211, 47, 47, 0.5)',
                                },
                                transition: 'all 0.2s ease'
                            }}
                        >
                            删除订阅
                        </Button>
                    </Box>
                </Box>
            </Paper>

            {/* 错误提示 */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* 订阅信息概览 */}
            <Paper sx={{ p: { xs: 2, md: 3 }, mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    📊 订阅概览
                </Typography>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                                上次同步
                            </Typography>
                            <Typography variant="body2" sx={{ fontSize: '0.875rem', mt: 0.5 }}>
                                {subscription.last_sync_at 
                                    ? new Date(subscription.last_sync_at).toLocaleString('zh-CN')
                                    : '从未同步'
                                }
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                                下次同步
                            </Typography>
                            <Typography variant="body2" sx={{ fontSize: '0.875rem', mt: 0.5 }}>
                                {subscription.next_sync_at && subscription.status === 'active'
                                    ? new Date(subscription.next_sync_at).toLocaleString('zh-CN')
                                    : subscription.status === 'active' ? '计算中...' : '已暂停'
                                }
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                                同步频率
                            </Typography>
                            <Typography variant="body2" sx={{ fontSize: '0.875rem', mt: 0.5 }}>
                                {subscriptionClient.formatSyncFrequency(subscription.sync_frequency)}
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                                创建时间
                            </Typography>
                            <Typography variant="body2" sx={{ fontSize: '0.875rem', mt: 0.5 }}>
                                {new Date(subscription.created_at).toLocaleDateString('zh-CN')}
                            </Typography>
                        </Box>
                    </Grid>
                </Grid>
                
                {subscription.error_message && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        {subscription.error_message}
                    </Alert>
                )}
            </Paper>

            {/* 标签页 */}
            <Paper sx={{ mb: 3 }}>
                <Tabs
                    value={activeTab}
                    onChange={(e, newValue) => setActiveTab(newValue)}
                    indicatorColor="primary"
                    textColor="primary"
                >
                    <Tab label="概览" icon={<InfoIcon />} />
                    <Tab label="同步历史" icon={<AccessTimeIcon />} />
                    <Tab label="获取的论文" icon={<ArticleIcon />} />
                    <Tab label="设置" icon={<SettingsIcon />} />
                </Tabs>
            </Paper>

            {/* 标签页内容 */}
            <Box>
                {activeTab === 0 && (
                    <Paper sx={{ p: { xs: 2, md: 3 } }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                            📋 订阅详细信息
                        </Typography>
                        
                        <Grid container spacing={3}>
                            <Grid item xs={12}>
                                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
                                    描述
                                </Typography>
                                <Typography variant="body1" sx={{ mb: 2 }}>
                                    {subscription.description || subscription.template_name}
                                </Typography>
                            </Grid>

                            {subscription.source_params && Object.keys(subscription.source_params).length > 0 && (
                                <Grid item xs={12}>
                                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2, fontWeight: 500 }}>
                                        配置参数
                                    </Typography>
                                    <Paper sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                                        <Grid container spacing={2}>
                                            {Object.entries(subscription.source_params).map(([key, value]) => (
                                                <Grid item xs={12} sm={6} md={4} key={key}>
                                                    <Box sx={{ 
                                                        p: 1.5, 
                                                        bgcolor: 'white', 
                                                        borderRadius: 1,
                                                        border: '1px solid rgba(0,0,0,0.08)'
                                                    }}>
                                                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', fontWeight: 500 }}>
                                                            {key}
                                                        </Typography>
                                                        <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 0.5, wordBreak: 'break-all' }}>
                                                            {String(value)}
                                                        </Typography>
                                                    </Box>
                                                </Grid>
                                            ))}
                                        </Grid>
                                    </Paper>
                                </Grid>
                            )}
                        </Grid>
                    </Paper>
                )}

                {activeTab === 1 && (
                    <SyncHistoryTimeline subscriptionId={subscription.id} />
                )}

                {activeTab === 2 && (
                    <SubscriptionPapers subscriptionId={subscription.id} />
                )}

                {activeTab === 3 && (
                    <SubscriptionSettings
                        subscription={subscription}
                        onUpdate={loadSubscription}
                    />
                )}
            </Box>

            {/* 删除确认对话框 */}
            <Dialog
                open={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
            >
                <DialogTitle>
                    确认删除订阅
                </DialogTitle>
                <DialogContent>
                    <Typography>
                        您确定要删除订阅 "{subscription.name}" 吗？此操作将：
                    </Typography>
                    <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                        <li>删除订阅配置</li>
                        <li>停止自动同步</li>
                        <li>保留已获取的论文数据</li>
                    </Box>
                    <Typography variant="body2" color="error.main" sx={{ mt: 2 }}>
                        此操作无法撤销！
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={() => setDeleteDialogOpen(false)}
                        sx={{
                            border: '1px solid rgba(25, 118, 210, 0.3)',
                            color: '#1976d2',
                            fontWeight: 500,
                            '&:hover': {
                                background: 'rgba(25, 118, 210, 0.04)',
                                transform: 'translateY(-1px)',
                                borderColor: 'rgba(25, 118, 210, 0.5)',
                            },
                            transition: 'all 0.2s ease'
                        }}
                    >
                        取消
                    </Button>
                    <Button
                        onClick={handleDeleteSubscription}
                        color="error"
                        variant="contained"
                        sx={{
                            background: 'linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)',
                            border: '1px solid rgba(211, 47, 47, 0.2)',
                            color: '#d32f2f',
                            fontWeight: 600,
                            '&:hover': {
                                background: 'linear-gradient(135deg, #ffcdd2 0%, #ef9a9a 100%)',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(211, 47, 47, 0.2)',
                            },
                            transition: 'all 0.2s ease'
                        }}
                    >
                        确认删除
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default SubscriptionDetailPage;