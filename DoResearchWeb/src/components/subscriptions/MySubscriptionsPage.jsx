import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    CardActions,
    Button,
    IconButton,
    Grid,
    Chip,
    CircularProgress,
    Alert,
    Menu,
    MenuItem,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Tabs,
    Tab,
    Paper,
    Divider,
    Tooltip,
    LinearProgress,
    Fab,
    alpha,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    ListItemSecondaryAction,
    Avatar
    // useTheme
} from '@mui/material';
import {
    Add as AddIcon,
    MoreVert as MoreVertIcon,
    Sync as SyncIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Pause as PauseIcon,
    PlayArrow as PlayArrowIcon,
    Schedule as ScheduleIcon,
    Error as ErrorIcon,
    CheckCircle as CheckCircleIcon,
    Info as InfoIcon,
    Refresh as RefreshIcon,
    Settings as SettingsIcon,
    Subscriptions as SubscriptionsIcon,
    PauseCircle as PauseCircleIcon,
    Cancel as CancelIcon,
    TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

import subscriptionClient from '../../services/subscriptionClient.jsx';
import { SOURCE_TYPE_CONFIGS } from '../../types/subscription.ts';
import { createCountChipStyles } from '../../constants/chipStyles.js';

// 统计卡片组件（与StatsView保持一致）
const SubscriptionStatsCard = ({ title, value, icon, color }) => {
    // const theme = useTheme();
    
    return (
        <Card
            sx={{
                height: { xs: 100, md: 120 },
                position: 'relative',
                background: `linear-gradient(135deg, ${color}15 0%, ${color}25 100%)`,
                border: `1px solid ${alpha(color, 0.2)}`,
                overflow: 'hidden',
                '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: '100px',
                    height: '100px',
                    background: `radial-gradient(circle, ${alpha(color, 0.1)} 0%, transparent 70%)`,
                    transform: 'translate(30px, -30px)',
                },
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: `0px 12px 32px ${alpha(color, 0.15)}`,
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
        >
            <CardContent sx={{
                display: 'flex',
                alignItems: 'center',
                gap: { xs: 1, md: 2 },
                height: '100%',
                p: { xs: 1.5, md: 2.5 },
                '&:last-child': { pb: { xs: 1.5, md: 2.5 } },
                position: 'relative',
                zIndex: 1,
            }}>
                {/* 图标区域 */}
                <Box
                    sx={{
                        p: { xs: 1, md: 1.5 },
                        borderRadius: 3,
                        backgroundColor: alpha(color, 0.1),
                        color: color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minWidth: { xs: 40, md: 56 },
                        minHeight: { xs: 40, md: 56 },
                        boxShadow: `0px 4px 12px ${alpha(color, 0.15)}`,
                        '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1.4rem', md: '2rem' },
                        }
                    }}
                >
                    {icon}
                </Box>

                {/* 内容区域 */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography 
                        variant="h4" 
                        sx={{
                            fontWeight: 700,
                            fontSize: { xs: '1.2rem', sm: '1.4rem', md: '2rem' },
                            color: 'text.primary',
                            mb: 0.5
                        }}
                    >
                        {value}
                    </Typography>
                    
                    <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{
                            fontSize: { xs: '0.75rem', md: '0.875rem' },
                            fontWeight: 500,
                            lineHeight: 1.2,
                        }}
                    >
                        {title}
                    </Typography>
                </Box>
            </CardContent>
        </Card>
    );
};

// 订阅项组件
const SubscriptionItem = ({ 
    subscription, 
    subscriptionStats,
    onSync, 
    onEdit, 
    onDelete, 
    onPause, 
    onResume, 
    syncingIds 
}) => {
    const [menuAnchor, setMenuAnchor] = useState(null);
    const navigate = useNavigate();

    const sourceConfig = SOURCE_TYPE_CONFIGS[subscription.source_type] || {
        displayName: subscription.source_type?.toUpperCase() || 'UNKNOWN',
        color: '#666666'
    };

    const getStatusInfo = () => {
        switch (subscription.status) {
            case 'active':
                return {
                    label: '活跃',
                    color: 'success',
                    icon: <CheckCircleIcon />
                };
            case 'paused':
                return {
                    label: '暂停',
                    color: 'warning',
                    icon: <PauseIcon />
                };
            case 'error':
                return {
                    label: '错误',
                    color: 'error',
                    icon: <ErrorIcon />
                };
            default:
                return {
                    label: '未知',
                    color: 'default',
                    icon: <InfoIcon />
                };
        }
    };

    const statusInfo = getStatusInfo();
    const isSyncing = syncingIds.includes(subscription.id);

    const formatDateTime = (dateString) => {
        if (!dateString) return '从未';
        return new Date(dateString).toLocaleString('zh-CN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatSyncFrequency = (seconds) => {
        return subscriptionClient.formatSyncFrequency(seconds);
    };

    const handleMenuClose = () => {
        setMenuAnchor(null);
    };

    const handleAction = (action) => {
        handleMenuClose();
        switch (action) {
            case 'sync':
                onSync(subscription.id);
                break;
            case 'edit':
                onEdit(subscription);
                break;
            case 'pause':
                onPause(subscription.id);
                break;
            case 'resume':
                onResume(subscription.id);
                break;
            case 'delete':
                onDelete(subscription.id);
                break;
            case 'detail':
                navigate(`/subscriptions/${subscription.id}`);
                break;
        }
    };

    return (
        <Box sx={{ position: 'relative' }}>
            {/* 同步进度条 */}
            {isSyncing && (
                <LinearProgress
                    sx={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        zIndex: 1
                    }}
                />
            )}

            <ListItem
                sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    bgcolor: 'background.paper',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer',
                    '&:hover': {
                        bgcolor: 'action.hover',
                        borderColor: 'primary.main'
                    }
                }}
                divider
                onClick={() => navigate(`/subscription/${subscription.id}/papers`)}
            >
                <ListItemIcon>
                    <Box
                        sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '8px',
                            background: `linear-gradient(135deg, ${sourceConfig.color}20, ${sourceConfig.color}40)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: `1px solid ${sourceConfig.color}30`,
                            overflow: 'hidden'
                        }}
                    >
                        {/* 根据不同的订阅源类型显示不同的logo */}
                        {subscription.source_type === 'ieee' && (
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
                                        fontSize: '0.5rem',
                                        color: '#005496',
                                        fontFamily: 'Arial, sans-serif'
                                    }}
                                >
                                    IEEE
                                </Typography>
                            </Box>
                        )}
                        {subscription.source_type === 'elsevier' && (
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
                                        fontSize: '0.35rem',
                                        color: '#FF6C00',
                                        fontFamily: 'Arial, sans-serif'
                                    }}
                                >
                                    Elsevier
                                </Typography>
                            </Box>
                        )}
                        {subscription.source_type === 'dblp' && (
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
                                        fontSize: '0.45rem',
                                        color: '#1f4e79',
                                        fontFamily: 'Arial, sans-serif'
                                    }}
                                >
                                    dblp
                                </Typography>
                            </Box>
                        )}
                        {!['ieee', 'elsevier', 'dblp'].includes(subscription.source_type) && (
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
                </ListItemIcon>

                <ListItemText
                    primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                {subscription.name}
                            </Typography>
                            <Chip
                                icon={statusInfo.icon}
                                label={statusInfo.label}
                                size="small"
                                color={statusInfo.color}
                                sx={{ height: 20 }}
                            />
                        </Box>
                    }
                    secondary={
                        <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                                <Typography variant="caption" color="text.secondary">
                                    上次同步: {formatDateTime(subscription.last_sync_at)}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    频率: {formatSyncFrequency(subscription.sync_frequency)}
                                </Typography>
                                {/* 统计信息显示 */}
                                {subscriptionStats[subscription.id] && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Typography variant="caption" color="text.secondary">
                                            共 {subscriptionStats[subscription.id].total_papers || 0} 篇
                                        </Typography>
                                        <Box sx={{ width: 60, display: 'flex', justifyContent: 'flex-start' }}>
                                            {subscriptionStats[subscription.id].unread_count > 0 ? (
                                                <Chip
                                                    label={`未读 ${subscriptionStats[subscription.id].unread_count}`}
                                                    size="small"
                                                    sx={(theme) => createCountChipStyles(theme, { size: 'small' })}
                                                />
                                            ) : (
                                                <Typography variant="caption" color="text.disabled" sx={{ fontSize: '0.65rem', px: 0.5 }}>
                                                    全部已读
                                                </Typography>
                                            )}
                                        </Box>
                                    </Box>
                                )}
                                {subscription.error_message && (
                                    <Chip 
                                        label="有错误" 
                                        size="small" 
                                        color="error" 
                                        variant="outlined"
                                        sx={{ height: 18, fontSize: '0.6rem' }}
                                    />
                                )}
                            </Box>
                        </Box>
                    }
                />

                <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Button
                            size="small"
                            variant="outlined"
                            startIcon={isSyncing ? <CircularProgress size={12} /> : <SyncIcon />}
                            onClick={() => handleAction('sync')}
                            disabled={isSyncing}
                            sx={{
                                minWidth: 'auto',
                                px: 1.5,
                                height: 28,
                                fontSize: '0.7rem',
                                background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                                border: '1px solid rgba(25, 118, 210, 0.2)',
                                color: '#1976d2',
                                '&:hover': {
                                    background: 'linear-gradient(135deg, #bbdefb 0%, #90caf9 100%)',
                                }
                            }}
                        >
                            同步
                        </Button>
                        <IconButton
                            onClick={(e) => setMenuAnchor(e.currentTarget)}
                            size="small"
                        >
                            <MoreVertIcon />
                        </IconButton>
                    </Box>
                </ListItemSecondaryAction>
            </ListItem>

            {/* 操作菜单 */}
            <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={handleMenuClose}
            >
                <MenuItem onClick={() => handleAction('detail')}>
                    <InfoIcon sx={{ mr: 1, fontSize: 20 }} />
                    查看详情
                </MenuItem>
                <MenuItem onClick={() => handleAction('edit')}>
                    <EditIcon sx={{ mr: 1, fontSize: 20 }} />
                    编辑订阅
                </MenuItem>
                <Divider />
                <MenuItem onClick={() => handleAction('sync')} disabled={isSyncing}>
                    <SyncIcon sx={{ mr: 1, fontSize: 20 }} />
                    手动同步
                </MenuItem>
                {subscription.status === 'active' ? (
                    <MenuItem onClick={() => handleAction('pause')}>
                        <PauseIcon sx={{ mr: 1, fontSize: 20 }} />
                        暂停订阅
                    </MenuItem>
                ) : (
                    <MenuItem onClick={() => handleAction('resume')}>
                        <PlayArrowIcon sx={{ mr: 1, fontSize: 20 }} />
                        恢复订阅
                    </MenuItem>
                )}
                <Divider />
                <MenuItem onClick={() => handleAction('delete')} sx={{ color: 'error.main' }}>
                    <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
                    删除订阅
                </MenuItem>
            </Menu>
        </Box>
    );
};

// 主页面组件
const MySubscriptionsPage = () => {
    const [subscriptions, setSubscriptions] = useState([]);
    const [subscriptionStats, setSubscriptionStats] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('all');
    const [syncingIds, setSyncingIds] = useState([]);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [subscriptionToDelete, setSubscriptionToDelete] = useState(null);

    const navigate = useNavigate();
    const location = useLocation();

    // 显示成功消息（如果从其他页面跳转过来）
    useEffect(() => {
        if (location.state?.message) {
            // 这里可以显示通知，暂时用console输出
            console.log(location.state.message);
        }
    }, [location.state]);

    // 加载订阅列表和统计信息
    const loadSubscriptions = async () => {
        try {
            setLoading(true);
            setError(null);
            const subscriptionsData = await subscriptionClient.getSubscriptions();
            setSubscriptions(subscriptionsData || []);
            
            // 获取每个订阅的统计信息
            if (subscriptionsData && subscriptionsData.length > 0) {
                const subscriptionIds = subscriptionsData.map(sub => sub.id);
                const statsData = await subscriptionClient.getBatchSubscriptionStats(subscriptionIds);
                setSubscriptionStats(statsData || {});
            }
        } catch (err) {
            console.error('加载订阅列表失败:', err);
            setError(err.message || '加载失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSubscriptions();
    }, []);

    // 过滤订阅
    const filteredSubscriptions = subscriptions.filter(subscription => {
        switch (activeTab) {
            case 'active':
                return subscription.status === 'active';
            case 'paused':
                return subscription.status === 'paused';
            case 'error':
                return subscription.status === 'error';
            default:
                return true;
        }
    });

    // 获取统计数据
    const getStats = () => {
        const total = subscriptions.length;
        const active = subscriptions.filter(s => s.status === 'active').length;
        const paused = subscriptions.filter(s => s.status === 'paused').length;
        const error = subscriptions.filter(s => s.status === 'error').length;
        
        return { total, active, paused, error };
    };

    const stats = getStats();

    // 处理手动同步
    const handleManualSync = async (subscriptionId) => {
        try {
            setSyncingIds(prev => [...prev, subscriptionId]);
            await subscriptionClient.syncSubscription(subscriptionId);
            await loadSubscriptions(); // 重新加载数据
        } catch (err) {
            console.error('手动同步失败:', err);
            setError(err.message || '同步失败');
        } finally {
            setSyncingIds(prev => prev.filter(id => id !== subscriptionId));
        }
    };

    // 处理编辑订阅
    const handleEditSubscription = (subscription) => {
        navigate(`/subscriptions/${subscription.id}/edit`, {
            state: { subscription }
        });
    };

    // 处理删除订阅
    const handleDeleteSubscription = (subscription) => {
        setSubscriptionToDelete(subscription);
        setDeleteDialogOpen(true);
    };

    const confirmDeleteSubscription = async () => {
        if (!subscriptionToDelete) return;

        try {
            await subscriptionClient.deleteSubscription(subscriptionToDelete.id);
            setSubscriptions(prev => prev.filter(s => s.id !== subscriptionToDelete.id));
            setDeleteDialogOpen(false);
            setSubscriptionToDelete(null);
            
            // 通知侧边栏刷新订阅列表
            window.dispatchEvent(new CustomEvent('subscription-list-updated'));
        } catch (err) {
            console.error('删除订阅失败:', err);
            setError(err.message || '删除失败');
        }
    };

    // 处理暂停/恢复订阅
    const handleToggleSubscription = async (subscriptionId, newStatus) => {
        try {
            await subscriptionClient.updateSubscription(subscriptionId, { status: newStatus });
            await loadSubscriptions();
            
            // 通知侧边栏刷新订阅列表
            window.dispatchEvent(new CustomEvent('subscription-list-updated'));
        } catch (err) {
            console.error('更新订阅状态失败:', err);
            setError(err.message || '操作失败');
        }
    };

    return (
        <Box sx={{ p: 3, maxWidth: '1400px', margin: '0 auto' }}>
            {/* 页面标题 */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                        我的订阅
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        管理您的论文订阅源，获取最新学术资讯
                    </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        variant="contained"
                        startIcon={loading ? <CircularProgress size={16} sx={{ color: '#1976d2' }} /> : <RefreshIcon />}
                        onClick={loadSubscriptions}
                        disabled={loading}
                        sx={{
                            fontSize: '0.8rem',
                            px: 1.5,
                            py: 0.6,
                            minWidth: 'auto',
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
                        刷新
                    </Button>
                </Box>
            </Box>

            {/* 统计卡片 */}
            <Box
                sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                        xs: 'repeat(2, 1fr)', // 移动端2列
                        sm: 'repeat(4, 1fr)', // 平板及以上4列
                    },
                    gap: 2,
                    mb: 3
                }}
            >
                <SubscriptionStatsCard
                    title="总订阅数"
                    value={stats.total}
                    icon={<SubscriptionsIcon />}
                    color="#1976d2"
                />
                <SubscriptionStatsCard
                    title="活跃订阅"
                    value={stats.active}
                    icon={<CheckCircleIcon />}
                    color="#2e7d32"
                />
                <SubscriptionStatsCard
                    title="暂停订阅"
                    value={stats.paused}
                    icon={<PauseCircleIcon />}
                    color="#ed6c02"
                />
                <SubscriptionStatsCard
                    title="错误订阅"
                    value={stats.error}
                    icon={<CancelIcon />}
                    color="#d32f2f"
                />
            </Box>

            {/* 过滤标签 */}
            <Paper sx={{ mb: 3 }}>
                <Tabs
                    value={activeTab}
                    onChange={(e, newValue) => setActiveTab(newValue)}
                    indicatorColor="primary"
                    textColor="primary"
                >
                    <Tab
                        label={`全部 (${stats.total})`}
                        value="all"
                    />
                    <Tab
                        label={`活跃 (${stats.active})`}
                        value="active"
                    />
                    <Tab
                        label={`暂停 (${stats.paused})`}
                        value="paused"
                    />
                    <Tab
                        label={`错误 (${stats.error})`}
                        value="error"
                    />
                </Tabs>
            </Paper>

            {/* 错误提示 */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* 订阅列表 */}
            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
                    <CircularProgress />
                    <Typography sx={{ ml: 2 }} color="text.secondary">
                        正在加载订阅列表...
                    </Typography>
                </Box>
            ) : filteredSubscriptions.length === 0 ? (
                <Paper
                    sx={{
                        p: 6,
                        textAlign: 'center',
                        bgcolor: 'grey.50',
                        border: '2px dashed',
                        borderColor: 'grey.300'
                    }}
                >
                    <AddIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                        {activeTab === 'all' ? '还没有任何订阅' : `没有${activeTab === 'active' ? '活跃' : activeTab === 'paused' ? '暂停' : '错误'}的订阅`}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        {activeTab === 'all' ? '添加您的第一个订阅，开始获取最新论文' : '切换到其他标签查看更多订阅'}
                    </Typography>
                    {activeTab === 'all' && (
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={() => navigate('/subscriptions/templates')}
                        >
                            添加订阅
                        </Button>
                    )}
                </Paper>
            ) : (
                <Paper sx={{ mt: 2 }}>
                    <List disablePadding>
                        {filteredSubscriptions.map(subscription => (
                            <SubscriptionItem
                                key={subscription.id}
                                subscription={subscription}
                                subscriptionStats={subscriptionStats}
                                onSync={handleManualSync}
                                onEdit={handleEditSubscription}
                                onDelete={handleDeleteSubscription}
                                onPause={(id) => handleToggleSubscription(id, 'paused')}
                                onResume={(id) => handleToggleSubscription(id, 'active')}
                                syncingIds={syncingIds}
                            />
                        ))}
                    </List>
                </Paper>
            )}

            {/* 添加订阅浮动按钮 */}
            <Fab
                color="primary"
                sx={{ position: 'fixed', bottom: 24, right: 24 }}
                onClick={() => navigate('/subscriptions/templates')}
            >
                <AddIcon />
            </Fab>

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
                        您确定要删除订阅 "{subscriptionToDelete?.name}" 吗？此操作无法撤销。
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>
                        取消
                    </Button>
                    <Button
                        onClick={confirmDeleteSubscription}
                        color="error"
                        variant="contained"
                    >
                        确认删除
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default MySubscriptionsPage;