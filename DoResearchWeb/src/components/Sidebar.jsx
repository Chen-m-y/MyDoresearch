import React, { useState, useEffect, useCallback } from 'react';
import {
    Box,
    Typography,
    Button,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    ListItemButton,
    Divider,
    Chip,
    Paper,
    Avatar,
    IconButton,
    Menu,
    MenuItem,
    CircularProgress
} from '@mui/material';
import {
    Add as AddIcon,
    PersonOutline,
    ExitToApp,
    Settings,
    MoreVert
} from '@mui/icons-material';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import CryptoJS from 'crypto-js';

import { useAuth } from '../contexts/AuthContext';
import EmptyState from './EmptyState.jsx';
import { navigationItems } from '../constants/navigation.js';
import { createCountChipStyles } from '../constants/chipStyles.js';
import subscriptionClient from '../services/subscriptionClient.jsx';
import { SOURCE_TYPE_CONFIGS } from '../types/subscription.ts';


function Sidebar({ onClose }) {
    // const {
    //     currentView,
    //     currentFeedId
    // } = useContext(PaperContext);

    const { user, logout } = useAuth();
    const navigate = useNavigate();
    
    const [userMenuAnchor, setUserMenuAnchor] = useState(null);
    
    // 新订阅系统状态
    const [subscriptions, setSubscriptions] = useState([]);
    const [subscriptionStats, setSubscriptionStats] = useState({});
    const [loadingSubscriptions, setLoadingSubscriptions] = useState(true);

    // 加载订阅列表和统计信息
    const loadSubscriptions = useCallback(async () => {
        try {
            setLoadingSubscriptions(true);
            
            // 获取订阅列表
            const subscriptionsData = await subscriptionClient.getSubscriptions();
            setSubscriptions(subscriptionsData || []);
            
            // 如果有订阅，获取统计信息
            if (subscriptionsData && subscriptionsData.length > 0) {
                const subscriptionIds = subscriptionsData.map(sub => sub.id);
                const statsData = await subscriptionClient.getBatchSubscriptionStats(subscriptionIds);
                setSubscriptionStats(statsData || {});
            }
        } catch (error) {
            console.error('加载侧边栏订阅数据失败:', error);
            setSubscriptions([]);
            setSubscriptionStats({});
        } finally {
            setLoadingSubscriptions(false);
        }
    }, []);

    useEffect(() => {
        loadSubscriptions();
    }, [loadSubscriptions]);

    // 监听订阅列表更新事件
    useEffect(() => {
        const handleSubscriptionListUpdate = () => {
            loadSubscriptions();
        };

        window.addEventListener('subscription-list-updated', handleSubscriptionListUpdate);
        
        return () => {
            window.removeEventListener('subscription-list-updated', handleSubscriptionListUpdate);
        };
    }, [loadSubscriptions]);

    // 生成Gravatar头像URL
    const getGravatarUrl = (email, size = 80) => {
        if (!email) return null;
        
        // 将邮箱转换为小写并去除空格
        const trimmedEmail = email.toLowerCase().trim();
        
        // 生成MD5哈希
        const hash = CryptoJS.MD5(trimmedEmail).toString();
        
        // 返回Gravatar URL，添加默认头像参数
        return `https://www.gravatar.com/avatar/${hash}?s=${size}&d=identicon&r=pg`;
    };

    const handleSubscriptionClick = (subscriptionId) => {
        // 直接导航，不做预加载
        navigate(`/subscription/${subscriptionId}/papers`);
        onClose && onClose();
    };

    const handleUserMenuOpen = (event) => {
        setUserMenuAnchor(event.currentTarget);
    };

    const handleUserMenuClose = () => {
        setUserMenuAnchor(null);
    };

    const handleLogout = async () => {
        handleUserMenuClose();
        await logout();
    };

    const avatarUrl = getGravatarUrl(user?.email);
    const fallbackLetter = user?.username?.charAt(0)?.toUpperCase() || 'U';

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* 标题和用户头像区域 */}
            <Paper
                elevation={0}
                sx={{
                    p: 2.5,
                    bgcolor: 'grey.50',
                    borderBottom: 1,
                    borderColor: 'divider',
                    height: '76px',
                    borderRadius: 0
                }}
            >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        {/* 用户头像替换原来的logo */}
                        <Avatar
                            onClick={handleUserMenuOpen}
                            src={avatarUrl}
                            sx={{
                                width: 40,
                                height: 40,
                                bgcolor: 'primary.main',
                                color: 'white',
                                fontWeight: 600,
                                fontSize: '1.1rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                border: '2px solid rgba(255,255,255,0.8)',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                '&:hover': {
                                    transform: 'scale(1.1)',
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
                                    border: '2px solid rgba(255,255,255,1)',
                                }
                            }}
                        >
                            {!avatarUrl && fallbackLetter}
                        </Avatar>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            论文阅读器
                        </Typography>
                    </Box>
                    <Button
                        variant="contained"
                        size="small"
                        startIcon={<AddIcon sx={{ fontSize: '0.8rem' }} />}
                        onClick={() => navigate('/subscriptions/templates')}
                        sx={{ 
                            fontSize: '0.7rem',
                            px: 1.2,
                            py: 0.4,
                            minWidth: 'auto',
                            minHeight: '26px',
                            height: '26px',
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
                        新订阅
                    </Button>
                </Box>
            </Paper>

            {/* 用户菜单 */}
            <Menu
                anchorEl={userMenuAnchor}
                open={Boolean(userMenuAnchor)}
                onClose={handleUserMenuClose}
                PaperProps={{
                    sx: { minWidth: 180 }
                }}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'left',
                }}
            >
                {/* 用户信息显示在菜单顶部 */}
                <Box sx={{ px: 2, py: 1.5, borderBottom: 1, borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                        {user?.username || '用户'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.2 }}>
                        {user?.email || ''}
                    </Typography>
                </Box>
                
                <MenuItem 
                    component={NavLink}
                    to="/profile"
                    onClick={handleUserMenuClose}
                    sx={{ textDecoration: 'none', color: 'inherit' }}
                >
                    <ListItemIcon>
                        <PersonOutline fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>用户资料</ListItemText>
                </MenuItem>
                <MenuItem 
                    component={NavLink}
                    to="/settings"
                    onClick={handleUserMenuClose}
                    sx={{ textDecoration: 'none', color: 'inherit' }}
                >
                    <ListItemIcon>
                        <Settings fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>设置</ListItemText>
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>
                    <ListItemIcon>
                        <ExitToApp fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>退出登录</ListItemText>
                </MenuItem>
            </Menu>

            {/* 导航菜单 */}
            <Box 
                sx={{ py: 2 }}
                role="navigation"
                aria-label="主导航菜单"
            >
                <List disablePadding>
                    {navigationItems.map((item) => {
                        const IconComponent = item.icon;
                        return (
                            <ListItem key={item.id} disablePadding>
                                <ListItemButton
                                    component={NavLink}
                                    to={item.path}
                                    onClick={onClose}
                                    aria-label={`${item.fullLabel} - ${item.description}`}
                                    role="menuitem"
                                    sx={{
                                        mx: 1, mb: 0.5, borderRadius: 0.75,
                                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                        '&.active': {
                                            background: `linear-gradient(135deg, ${item.color}15 0%, ${item.color}25 100%)`,
                                            border: `1px solid ${item.color}30`,
                                            borderLeft: `3px solid ${item.color}`,
                                            position: 'relative',
                                            overflow: 'hidden',
                                            '&::before': {
                                                content: '""',
                                                position: 'absolute',
                                                top: 0,
                                                right: 0,
                                                width: '60px',
                                                height: '60px',
                                                background: `radial-gradient(circle, ${item.color}10 0%, transparent 70%)`,
                                                transform: 'translate(20px, -20px)',
                                            },
                                            '& .MuiListItemIcon-root': {
                                                color: item.color,
                                                position: 'relative',
                                                zIndex: 1,
                                            },
                                            '& .MuiListItemText-primary': {
                                                color: item.color,
                                                fontWeight: 600,
                                                position: 'relative',
                                                zIndex: 1,
                                            },
                                            '& .MuiListItemText-secondary': {
                                                position: 'relative',
                                                zIndex: 1,
                                            },
                                        },
                                        '&:hover': {
                                            backgroundColor: item.color + '08',
                                            '& .MuiListItemIcon-root': {
                                                color: item.color,
                                            },
                                        },
                                        '&:focus-visible': {
                                            outline: `2px solid ${item.color}`,
                                            outlineOffset: 2,
                                        },
                                    }}
                                >
                                    <ListItemIcon 
                                        sx={{ 
                                            minWidth: 40,
                                            transition: 'color 0.2s ease',
                                        }}
                                        aria-hidden="true"
                                    >
                                        <IconComponent />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={item.fullLabel}
                                        secondary={item.subtitle}
                                        primaryTypographyProps={{ 
                                            fontSize: '0.875rem', 
                                            fontWeight: 500,
                                            transition: 'all 0.2s ease',
                                        }}
                                        secondaryTypographyProps={{ 
                                            fontSize: '0.75rem',
                                            opacity: 0.8,
                                        }}
                                    />
                                </ListItemButton>
                            </ListItem>
                        );
                    })}
                </List>
            </Box>

            <Divider />

            {/* 订阅源列表 */}
            <Box sx={{ flex: 1, overflow: 'auto' }}>
                {loadingSubscriptions ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                        <CircularProgress size={24} />
                    </Box>
                ) : (!subscriptions || subscriptions.length === 0) ? (
                    <EmptyState
                        type="subscriptions"
                        size="small"
                        onAction={() => navigate('/subscriptions/templates')}
                        customConfig={{
                            title: '暂无订阅',
                            subtitle: '使用新订阅系统获取论文',
                            description: '点击按钮开始添加智能订阅源',
                            actionText: '添加订阅',
                        }}
                    />
                ) : (
                    <List disablePadding>
                        {subscriptions
                            .filter(subscription => subscription.status === 'active') // 只显示活跃订阅
                            .map((subscription) => {
                                const stats = subscriptionStats[subscription.id] || {};
                                const unreadCount = stats.unread_count || 0;
                                const sourceConfig = SOURCE_TYPE_CONFIGS[subscription.source_type] || {
                                    displayName: subscription.source_type?.toUpperCase() || 'UNKNOWN',
                                    color: '#666666'
                                };
                                
                                // 检查是否为当前选中的订阅
                                const isSelected = window.location.pathname.includes(`/subscription/${subscription.id}/papers`);
                                
                                return (
                                    <ListItem key={subscription.id} disablePadding>
                                        <ListItemButton
                                            onClick={() => handleSubscriptionClick(subscription.id)}
                                            selected={isSelected}
                                            sx={(theme) => ({
                                                borderRadius: 0.75,
                                                mx: 1,
                                                mb: 0.5,
                                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                                '&.Mui-selected': {
                                                    background: `linear-gradient(135deg, ${theme.palette.primary.main}15 0%, ${theme.palette.primary.main}25 100%)`,
                                                    border: `1px solid ${theme.palette.primary.main}30`,
                                                    borderLeft: `3px solid ${theme.palette.primary.main}`,
                                                    position: 'relative',
                                                    overflow: 'hidden',
                                                    '&::before': {
                                                        content: '""',
                                                        position: 'absolute',
                                                        top: 0,
                                                        right: 0,
                                                        width: '50px',
                                                        height: '50px',
                                                        background: `radial-gradient(circle, ${theme.palette.primary.main}10 0%, transparent 70%)`,
                                                        transform: 'translate(15px, -15px)',
                                                    },
                                                    '& .MuiListItemText-root': {
                                                        position: 'relative',
                                                        zIndex: 1,
                                                    },
                                                    '&:hover': {
                                                        background: `linear-gradient(135deg, ${theme.palette.primary.main}18 0%, ${theme.palette.primary.main}28 100%)`,
                                                    }
                                                },
                                                '&:hover': {
                                                    backgroundColor: `${sourceConfig.color}08`,
                                                }
                                            })}
                                        >
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                                                        {/* 订阅源类型标识 */}
                                                        <Box
                                                            sx={{
                                                                width: 20,
                                                                height: 20,
                                                                borderRadius: '3px',
                                                                background: `${sourceConfig.color}20`,
                                                                border: `1px solid ${sourceConfig.color}40`,
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                flexShrink: 0
                                                            }}
                                                        >
                                                            <Typography
                                                                sx={{
                                                                    fontSize: '0.4rem',
                                                                    fontWeight: 700,
                                                                    color: sourceConfig.color,
                                                                    lineHeight: 1
                                                                }}
                                                            >
                                                                {subscription.source_type === 'ieee' && 'IEEE'}
                                                                {subscription.source_type === 'elsevier' && 'ELS'}
                                                                {subscription.source_type === 'dblp' && 'DBLP'}
                                                                {!['ieee', 'elsevier', 'dblp'].includes(subscription.source_type) && 
                                                                    sourceConfig.displayName.substring(0, 3)
                                                                }
                                                            </Typography>
                                                        </Box>
                                                        
                                                        <Typography 
                                                            variant="body2" 
                                                            sx={{ 
                                                                fontWeight: 500, 
                                                                flex: 1,
                                                                fontSize: '0.875rem',
                                                                overflow: 'hidden',
                                                                textOverflow: 'ellipsis',
                                                                whiteSpace: 'nowrap'
                                                            }}
                                                        >
                                                            {subscription.name}
                                                        </Typography>
                                                        
                                                        {unreadCount > 0 && (
                                                            <Chip
                                                                label={unreadCount > 99 ? '99+' : unreadCount}
                                                                size="small"
                                                                sx={(theme) => createCountChipStyles(theme, { 
                                                                    size: 'small' 
                                                                })}
                                                            />
                                                        )}
                                                    </Box>
                                                }
                                                secondary={null}
                                            />
                                        </ListItemButton>
                                    </ListItem>
                                );
                            })}
                    </List>
                )}
            </Box>
        </Box>
    );
}

export default Sidebar;