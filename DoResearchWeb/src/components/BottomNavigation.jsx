import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
    BottomNavigation,
    BottomNavigationAction,
    Paper,
    Badge,
    useTheme,
    Box,
    IconButton,
    useMediaQuery,
    Avatar,
    Menu,
    MenuItem,
    ListItemIcon,
    ListItemText,
    Divider,
    Typography
} from '@mui/material';
import { 
    KeyboardArrowUp as KeyboardArrowUpIcon,
    PersonOutline,
    Settings,
    ExitToApp
} from '@mui/icons-material';
import { navigationItems } from '../constants/navigation.js';
import { useLayout } from '../hooks/useLayout.js';
import { useElegantHideNavigation } from '../hooks/useElegantHideNavigation.js';
import { useAuth } from '../contexts/AuthContext';
import CryptoJS from 'crypto-js';


function MobileBottomNavigation() {
    const location = useLocation();
    const navigate = useNavigate();
    const theme = useTheme();
    const { bottomNavigation, styles } = useLayout();
    const { user, logout } = useAuth();
    const [userMenuAnchor, setUserMenuAnchor] = useState(null);
    
    // 检查是否应该显示底部导航栏（与App.jsx保持一致）
    const shouldShowBottomNav = useMediaQuery(theme.breakpoints.down('lg'));
    
    // 优雅的自动隐藏导航栏功能
    const {
        isVisible,
        show
    } = useElegantHideNavigation({
        autoHideDelay: 3500,    // 3.5秒后隐藏
        touchZoneHeight: 25,    // 底部25px触摸区域
        enabled: true
    });

    // 生成Gravatar头像URL
    const getGravatarUrl = (email, size = 56) => {
        if (!email) return null;
        
        const trimmedEmail = email.toLowerCase().trim();
        const hash = CryptoJS.MD5(trimmedEmail).toString();
        return `https://www.gravatar.com/avatar/${hash}?s=${size}&d=identicon&r=pg`;
    };

    // 用户菜单处理函数
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

    // 动态调整主内容区域的底部间距 - 只在确实需要底部导航时设置
    useEffect(() => {
        const mainElement = document.querySelector('main');
        if (!mainElement) return;

        // 只有在应该显示底部导航的情况下才设置样式
        if (shouldShowBottomNav) {
            // 需要显示底部导航栏的屏幕尺寸：根据导航栏可见状态设置间距
            const paddingBottom = isVisible ? '48px' : '0px';
            if (mainElement.style.paddingBottom !== paddingBottom) {
                mainElement.style.paddingBottom = paddingBottom;
                mainElement.style.transition = 'padding-bottom 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)';
            }
        }
        // 大屏模式下不在此处设置，由App.jsx统一处理

        // 组件卸载时清理样式
        return () => {
            const mainElement = document.querySelector('main');
            if (mainElement && shouldShowBottomNav) {
                // 只在之前设置了样式的情况下才清理
                mainElement.style.paddingBottom = '';
                mainElement.style.removeProperty('padding-bottom');
            }
        };
    }, [isVisible, shouldShowBottomNav]);

    // 确定当前激活的标签
    const getCurrentValue = () => {
        const currentPath = location.pathname;
        
        // 精确匹配或前缀匹配
        const index = navigationItems.findIndex(item => {
            if (item.path === '/stats' && (currentPath === '/stats' || currentPath === '/')) {
                return true;
            }
            if (item.path === '/feeds' && (currentPath === '/feeds' || currentPath.startsWith('/feed'))) {
                return true;
            }
            return currentPath === item.path;
        });
        
        return index >= 0 ? index : 0; // 默认选中第一个
    };

    const handleChange = (event, newValue) => {
        const targetPath = navigationItems[newValue].path;
        navigate(targetPath);
    };

    // 如果不应该显示底部导航，直接返回null
    if (!shouldShowBottomNav) {
        return null;
    }

    return (
        <>
            {/* 主导航栏 */}
            <Paper
                sx={{
                    ...styles.bottomNavigationContainer,
                    // 优雅的 CSS 变换动画
                    transform: isVisible ? 'translateY(0)' : 'translateY(100%)',
                    transition: 'transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
                    // 美观的视觉效果
                    borderTop: `1px solid ${theme.palette.divider}`,
                    boxShadow: '0 -2px 16px rgba(0,0,0,0.08), 0 -1px 4px rgba(0,0,0,0.04)',
                    backdropFilter: 'blur(16px)',
                    backgroundColor: 'rgba(255, 255, 255, 0.92)',
                    // 轻微的渐变效果
                    background: 'linear-gradient(to top, rgba(255,255,255,0.95), rgba(255,255,255,0.9))',
                    // 顶部微光效果
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '1px',
                        background: 'linear-gradient(90deg, transparent, rgba(25, 118, 210, 0.15), transparent)',
                    },
                    borderBottomLeftRadius: 0,
                    borderBottomRightRadius: 0,
                }}
                elevation={0}
            >
                <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    height: bottomNavigation.height,
                    px: 1
                }}>
                    {/* 主导航区域 */}
                    <BottomNavigation
                        value={getCurrentValue()}
                        onChange={handleChange}
                        showLabels
                        sx={{
                            flex: 1,
                            height: '100%',
                            backgroundColor: 'transparent',
                            '& .MuiBottomNavigationAction-root': {
                                paddingTop: 0.25,
                                paddingBottom: 0.25,
                                minWidth: 'auto',
                                flex: 1,
                                gap: 0.25,
                                transition: 'all 0.2s ease',
                                '&.Mui-selected': {
                                    color: 'primary.main',
                                },
                            },
                            '& .MuiBottomNavigationAction-label': {
                                fontSize: '0.65rem',
                                fontWeight: 500,
                                marginTop: 0,
                                lineHeight: 1.2,
                                '&.Mui-selected': {
                                    fontSize: '0.7rem',
                                }
                            },
                            '& .MuiSvgIcon-root': {
                                fontSize: '1.1rem',
                                transition: 'transform 0.2s ease'
                            }
                        }}
                    >
                        {navigationItems.map((item, index) => {
                            const IconComponent = item.icon;
                            const isActive = getCurrentValue() === index;
                            
                            return (
                                <BottomNavigationAction
                                    key={item.path}
                                    sx={{
                                        '&.Mui-selected': {
                                            color: '#1976d2',
                                            background: 'linear-gradient(135deg, #e8f4fd 0%, #d1e9f6 100%)',
                                            borderRadius: '16px',
                                            margin: '4px 2px',
                                            position: 'relative',
                                            '& .MuiSvgIcon-root': {
                                                transform: 'scale(1.08)',
                                            }
                                        },
                                        '&:active': {
                                            transform: 'scale(0.98)',
                                        },
                                        borderRadius: '16px',
                                        margin: '4px 2px',
                                    }}
                                    icon={
                                        item.id === 'tasks' ? (
                                            <Badge 
                                                badgeContent={0} 
                                                color="error" 
                                                max={99}
                                            >
                                                <IconComponent 
                                                    sx={{ color: isActive ? '#1976d2' : 'inherit' }}
                                                />
                                            </Badge>
                                        ) : item.id === 'readlater' ? (
                                            <Badge 
                                                badgeContent={0} 
                                                color="primary" 
                                                max={99}
                                            >
                                                <IconComponent 
                                                    sx={{ color: isActive ? '#1976d2' : 'inherit' }}
                                                />
                                            </Badge>
                                        ) : (
                                            <IconComponent 
                                                sx={{ color: isActive ? '#1976d2' : 'inherit' }}
                                            />
                                        )
                                    }
                                />
                            );
                        })}
                    </BottomNavigation>

                    {/* 用户头像区域 */}
                    <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center',
                        pl: 1,
                        borderLeft: `1px solid ${theme.palette.divider}`,
                        ml: 1
                    }}>
                        <Avatar
                            onClick={handleUserMenuOpen}
                            src={avatarUrl}
                            sx={{
                                width: 28,
                                height: 28,
                                bgcolor: 'primary.main',
                                color: 'white',
                                fontWeight: 600,
                                fontSize: '0.8rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                border: '1px solid rgba(25, 118, 210, 0.2)',
                                '&:hover': {
                                    transform: 'scale(1.05)',
                                    boxShadow: '0 2px 8px rgba(25, 118, 210, 0.3)',
                                }
                            }}
                        >
                            {!avatarUrl && fallbackLetter}
                        </Avatar>
                    </Box>
                </Box>
            </Paper>

            {/* 轻量级显示提示 - 悬浮在右下角 */}
            <Box
                sx={{
                    position: 'fixed',
                    bottom: 12,
                    right: 16,  // 移动到右下角
                    opacity: isVisible ? 0 : 0.85,
                    visibility: isVisible ? 'hidden' : 'visible',
                    transition: 'opacity 0.6s ease, visibility 0.6s ease',
                    transitionDelay: isVisible ? '0s' : '0.3s',
                    zIndex: theme.zIndex.fab,
                    pointerEvents: isVisible ? 'none' : 'auto',
                }}
            >
                <IconButton
                    onClick={show}
                    size="small"
                    sx={{
                        width: 36,
                        height: 36,
                        backgroundColor: 'rgba(230, 74, 25, 0.88)',
                        color: '#ffffff',
                        border: '1.5px solid rgba(255, 255, 255, 0.7)',
                        backdropFilter: 'blur(12px)',
                        boxShadow: '0 3px 12px rgba(230, 74, 25, 0.35), 0 1px 6px rgba(0, 0, 0, 0.15)',
                        '&:hover': {
                            backgroundColor: 'rgba(230, 74, 25, 1)',
                            transform: 'scale(1.08)',
                            boxShadow: '0 4px 16px rgba(230, 74, 25, 0.5), 0 2px 8px rgba(0, 0, 0, 0.2)',
                            border: '1.5px solid rgba(255, 255, 255, 0.9)',
                        },
                        '&:active': {
                            transform: 'scale(0.96)',
                        },
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        // 静态样式代替脉冲动画避免性能问题
                        boxShadow: '0 4px 16px rgba(230, 74, 25, 0.5), 0 2px 8px rgba(0, 0, 0, 0.2)',
                        backgroundColor: 'rgba(230, 74, 25, 0.9)'
                    }}
                    aria-label="显示导航栏"
                >
                    <KeyboardArrowUpIcon sx={{ 
                        fontSize: '1.2rem',
                        fontWeight: 'bold',
                        filter: 'drop-shadow(0 1px 1px rgba(0,0,0,0.25))'
                    }} />
                </IconButton>
            </Box>

            {/* 用户菜单 */}
            <Menu
                anchorEl={userMenuAnchor}
                open={Boolean(userMenuAnchor)}
                onClose={handleUserMenuClose}
                PaperProps={{
                    sx: { 
                        minWidth: 160,
                        mt: -1
                    }
                }}
                anchorOrigin={{
                    vertical: 'top',
                    horizontal: 'center',
                }}
                transformOrigin={{
                    vertical: 'bottom',
                    horizontal: 'center',
                }}
            >
                {/* 用户信息显示在菜单顶部 */}
                <Box sx={{ px: 2, py: 1, borderBottom: 1, borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, lineHeight: 1.2, fontSize: '0.8rem' }}>
                        {user?.username || '用户'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.2, fontSize: '0.7rem' }}>
                        {user?.email || ''}
                    </Typography>
                </Box>
                
                <MenuItem 
                    onClick={() => {
                        handleUserMenuClose();
                        navigate('/profile');
                    }}
                    sx={{ py: 0.75 }}
                >
                    <ListItemIcon sx={{ minWidth: 32 }}>
                        <PersonOutline fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                        primary="用户资料" 
                        primaryTypographyProps={{ fontSize: '0.8rem' }}
                    />
                </MenuItem>
                <MenuItem 
                    onClick={() => {
                        handleUserMenuClose();
                        navigate('/settings');
                    }}
                    sx={{ py: 0.75 }}
                >
                    <ListItemIcon sx={{ minWidth: 32 }}>
                        <Settings fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                        primary="设置" 
                        primaryTypographyProps={{ fontSize: '0.8rem' }}
                    />
                </MenuItem>
                <Divider />
                <MenuItem 
                    onClick={handleLogout}
                    sx={{ py: 0.75 }}
                >
                    <ListItemIcon sx={{ minWidth: 32 }}>
                        <ExitToApp fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                        primary="退出登录" 
                        primaryTypographyProps={{ fontSize: '0.8rem' }}
                    />
                </MenuItem>
            </Menu>
        </>
    );
}

export default MobileBottomNavigation;