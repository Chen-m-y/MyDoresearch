import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Avatar,
    Chip,
    CircularProgress,
    Button,
    useTheme,
    alpha,
    useMediaQuery
} from '@mui/material';
import {
    PersonOutline,
    EmailOutlined,
    CalendarTodayOutlined,
    LoginOutlined,
    VerifiedUserOutlined,
    EditOutlined,
    SecurityOutlined,
    BookOutlined,
    BadgeOutlined,
    AccountCircleOutlined
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import CryptoJS from 'crypto-js';

export default function UserProfilePage() {
    const theme = useTheme();
    const navigate = useNavigate();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const { user, getProfile, isLoading: authLoading } = useAuth();
    const [profileData, setProfileData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [hasAttemptedLoad, setHasAttemptedLoad] = useState(false);

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

    useEffect(() => {
        const loadProfile = async () => {
            if (authLoading) return;
            if (hasAttemptedLoad) return;
            
            setHasAttemptedLoad(true);
            setLoading(true);

            try {
                const result = await getProfile();
                if (result.success) {
                    setProfileData(result.data);
                } else {
                    setProfileData(user);
                }
            } catch (error) {
                console.error('获取用户资料失败:', error);
                setProfileData(user);
            } finally {
                setLoading(false);
            }
        };

        loadProfile();
    }, [authLoading, hasAttemptedLoad, getProfile, user]);

    const formatDateTime = (dateString) => {
        if (!dateString) return '未知';
        try {
            return new Date(dateString).toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    };

    const formatDateOnly = (dateString) => {
        if (!dateString) return '未知';
        try {
            return new Date(dateString).toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch {
            return dateString;
        }
    };

    if (authLoading || loading) {
        return (
            <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 2
            }}>
                <CircularProgress size={48} />
                <Typography variant="h6" color="text.secondary">
                    正在加载用户资料...
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    获取个人信息中
                </Typography>
            </Box>
        );
    }

    const displayData = profileData || user;
    const avatarUrl = getGravatarUrl(displayData?.email, isMobile ? 320 : 480);
    const fallbackLetter = displayData?.username?.charAt(0)?.toUpperCase() || 'U';

    if (!displayData) {
        return (
            <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 2,
                textAlign: 'center'
            }}>
                <Typography variant="h5" color="text.secondary">
                    无法获取用户资料
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    请尝试刷新页面或重新登录
                </Typography>
                <Button variant="contained" onClick={() => window.location.reload()}>
                    刷新页面
                </Button>
            </Box>
        );
    }

    const profileCards = [
        {
            title: '用户名',
            value: displayData?.username || '未设置',
            icon: <PersonOutline />,
            color: theme.palette.primary.main,
        },
        {
            title: '邮箱地址',
            value: displayData?.email || '未设置',
            icon: <EmailOutlined />,
            color: theme.palette.secondary.main,
        },
        {
            title: '注册时间',
            value: formatDateOnly(displayData?.created_at),
            icon: <CalendarTodayOutlined />,
            color: theme.palette.success.main,
        },
        {
            title: '最后登录',
            value: formatDateOnly(displayData?.last_login),
            icon: <LoginOutlined />,
            color: theme.palette.info.main,
        },
    ];

    const statsCards = [
        {
            title: '用户ID',
            value: `#${displayData?.id || '0'}`,
            color: theme.palette.primary.main,
            subtitle: '唯一标识符'
        },
        {
            title: '账户状态',
            value: displayData?.active ? '正常' : '未激活',
            color: displayData?.active ? theme.palette.success.main : theme.palette.warning.main,
            subtitle: '当前状态'
        },
        {
            title: '系统角色',
            value: '标准用户',
            color: theme.palette.info.main,
            subtitle: '权限级别'
        },
        {
            title: '安全级别',
            value: '高',
            color: theme.palette.warning.main,
            subtitle: '账户安全'
        },
    ];

    return (
        <Box sx={{
            p: { xs: 1, md: 2 }
        }}>
            {/* 用户头像和基本信息合并卡片 */}
            <Card sx={{
                mb: { xs: 1.5, md: 2 },
                animation: 'fadeInUp 0.6s ease-out',
                '@keyframes fadeInUp': {
                    from: {
                        opacity: 0,
                        transform: 'translateY(30px)',
                    },
                    to: {
                        opacity: 1,
                        transform: 'translateY(0)',
                    },
                },
            }}>
                <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
                    {/* 标题区域 - 与账户统计风格一致 */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                        <Box sx={{
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            width: 32,
                            height: 32,
                            borderRadius: 1.5,
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            color: theme.palette.primary.main,
                            mr: 1.5
                        }}>
                            <PersonOutline fontSize="small" />
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                            用户资料
                        </Typography>
                    </Box>
                    
                    {/* 用户基本信息区域 */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Avatar
                            src={avatarUrl}
                            sx={{
                                width: { xs: 60, md: 80 },
                                height: { xs: 60, md: 80 },
                                mr: 2,
                                bgcolor: theme.palette.primary.main,
                                fontSize: { xs: '1.5rem', md: '2rem' },
                                fontWeight: 700,
                            }}
                        >
                            {!avatarUrl && fallbackLetter}
                        </Avatar>
                        
                        <Box sx={{ flex: 1 }}>
                            <Typography variant="h5" gutterBottom sx={{ 
                                fontWeight: 600,
                                fontSize: { xs: '1.1rem', md: '1.25rem' },
                                mb: 0.5
                            }}>
                                {displayData?.username || '用户'}
                            </Typography>
                            
                            <Typography variant="body2" sx={{ 
                                opacity: 0.8,
                                mb: 1,
                                fontSize: { xs: '0.85rem', md: '0.9rem' }
                            }}>
                                {displayData?.email || ''}
                            </Typography>
                            
                            <Chip
                                icon={<VerifiedUserOutlined />}
                                label={displayData?.active ? "正常" : "未激活"}
                                color={displayData?.active ? "success" : "warning"}
                                size="small"
                                sx={{
                                    fontWeight: 500,
                                    fontSize: '0.75rem'
                                }}
                            />
                        </Box>
                        
                        <Button 
                            variant="outlined" 
                            size="small"
                            startIcon={<SecurityOutlined />}
                            onClick={() => navigate('/settings')}
                            sx={{ 
                                borderRadius: 1.5,
                                px: 2,
                                py: 0.5,
                                fontSize: '0.75rem'
                            }}
                        >
                            设置
                        </Button>
                    </Box>
                    
                    {/* 详细信息网格 */}
                    <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: { 
                            xs: 'repeat(2, 1fr)',
                            md: 'repeat(4, 1fr)'
                        },
                        gap: { xs: 1, md: 1.5 }
                    }}>
                        {profileCards.map((card, index) => (
                            <Box key={index} sx={{
                                p: { xs: 1, md: 1.5 },
                                borderRadius: 1.5,
                                bgcolor: alpha(card.color, 0.06),
                                border: `1px solid ${alpha(card.color, 0.15)}`,
                                textAlign: 'center'
                            }}>
                                <Box sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: 24,
                                    height: 24,
                                    borderRadius: 1,
                                    bgcolor: alpha(card.color, 0.15),
                                    color: card.color,
                                    mx: 'auto',
                                    mb: 0.5
                                }}>
                                    {React.cloneElement(card.icon, { fontSize: 'small' })}
                                </Box>
                                <Typography variant="caption" color="text.secondary" sx={{
                                    display: 'block',
                                    fontSize: '0.65rem',
                                    mb: 0.25
                                }}>
                                    {card.title}
                                </Typography>
                                <Typography variant="body2" sx={{
                                    fontSize: { xs: '0.75rem', md: '0.8rem' },
                                    fontWeight: 500,
                                    lineHeight: 1.2
                                }}>
                                    {card.value}
                                </Typography>
                            </Box>
                        ))}
                    </Box>
                </CardContent>
            </Card>

            {/* 账户统计卡片 */}
            <Card sx={{
                animation: 'fadeInUp 0.6s ease-out 0.2s',
                animationFillMode: 'both',
                '@keyframes fadeInUp': {
                    from: {
                        opacity: 0,
                        transform: 'translateY(30px)',
                    },
                    to: {
                        opacity: 1,
                        transform: 'translateY(0)',
                    },
                },
            }}>
                <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                        <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 32,
                            height: 32,
                            borderRadius: 1.5,
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            color: theme.palette.primary.main,
                            mr: 1.5
                        }}>
                            <BookOutlined fontSize="small" />
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                            账户统计
                        </Typography>
                    </Box>
                    
                    <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: { 
                            xs: 'repeat(2, 1fr)',
                            md: 'repeat(4, 1fr)'
                        },
                        gap: { xs: 1, md: 1.5 }
                    }}>
                        {statsCards.map((card, index) => (
                            <Box key={index} sx={{ 
                                textAlign: 'center', 
                                p: { xs: 1, md: 1.5 }, 
                                borderRadius: 1.5,
                                background: alpha(card.color, 0.06),
                                border: `1px solid ${alpha(card.color, 0.15)}`
                            }}>
                                <Typography variant="h5" sx={{ 
                                    fontWeight: 700, 
                                    mb: 0.5,
                                    color: card.color,
                                    fontSize: { xs: '1.1rem', md: '1.25rem' }
                                }}>
                                    {card.value}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ 
                                    fontWeight: 500,
                                    fontSize: '0.65rem',
                                    display: 'block',
                                    mb: 0.25
                                }}>
                                    {card.title}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{
                                    fontSize: '0.6rem',
                                    opacity: 0.7
                                }}>
                                    {card.subtitle}
                                </Typography>
                            </Box>
                        ))}
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
}