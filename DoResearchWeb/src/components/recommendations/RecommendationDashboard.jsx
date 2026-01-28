import React, { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Alert,
    CircularProgress,
    Chip,
    Divider
} from '@mui/material';
import {
    Psychology as PsychologyIcon,
    TrendingUp as TrendingUpIcon,
    Star as StarIcon,
    Schedule as ScheduleIcon
} from '@mui/icons-material';
import apiClient from '../../services/apiClient.jsx';
import PersonalizedRecommendations from './PersonalizedRecommendations.jsx';
import UserInterestPatterns from './UserInterestPatterns.jsx';

/**
 * 推荐系统仪表板组件
 * 整合推荐、兴趣分析、统计等功能
 */
const RecommendationDashboard = ({ compact = false }) => {
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 获取推荐仪表板数据
    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await apiClient.getRecommendationDashboard();
            
            if (response.success) {
                setDashboardData(response.data);
            } else {
                setError(response.error || '获取仪表板数据失败');
            }
        } catch (err) {
            console.error('获取推荐仪表板失败:', err);
            setError(err.message || '获取仪表板数据失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
    }, []);

    // 渲染统计卡片
    const renderStatCard = (title, value, icon, color = 'primary') => (
        <Card sx={{ height: '100%' }}>
            <CardContent sx={{ 
                display: 'flex', 
                alignItems: 'center',
                p: compact ? 1.5 : 2,
                '&:last-child': { pb: compact ? 1.5 : 2 }
            }}>
                <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    bgcolor: `${color}.lighter`,
                    mr: 2
                }}>
                    {React.cloneElement(icon, { 
                        sx: { fontSize: 24, color: `${color}.main` }
                    })}
                </Box>
                <Box>
                    <Typography 
                        variant="h6" 
                        sx={{ 
                            fontWeight: 'bold',
                            fontSize: compact ? '1.1rem' : '1.25rem'
                        }}
                    >
                        {value}
                    </Typography>
                    <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ fontSize: compact ? '0.8rem' : '0.875rem' }}
                    >
                        {title}
                    </Typography>
                </Box>
            </CardContent>
        </Card>
    );

    if (loading) {
        return (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 6 }}>
                <CircularProgress sx={{ mr: 2 }} />
                <Typography>正在加载推荐系统数据...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ mb: 2 }}>
                {error}
            </Alert>
        );
    }

    if (!dashboardData) {
        return (
            <Alert severity="info">
                推荐系统暂无数据，请先浏览一些论文来建立用户画像。
            </Alert>
        );
    }

    const { 
        recent_stats, 
        interest_patterns, 
        high_interest_papers, 
        latest_recommendations,
        system_health 
    } = dashboardData;

    return (
        <Box>
            {/* 系统健康状态 */}
            {system_health && (
                <Box sx={{ mb: 3 }}>
                    <Card>
                        <CardContent sx={{ py: 1.5 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Typography variant="subtitle2" color="text.secondary">
                                    推荐系统状态:
                                </Typography>
                                <Chip
                                    label={system_health.can_recommend ? "运行正常" : "数据不足"}
                                    color={system_health.can_recommend ? "success" : "warning"}
                                    size="small"
                                />
                                {system_health.has_interaction_data && (
                                    <Chip 
                                        label="有交互数据" 
                                        color="info" 
                                        size="small" 
                                        sx={{
                                            background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}15 0%, ${theme.palette.info.main}25 100%)`,
                                            color: (theme) => theme.palette.info.main,
                                            borderColor: (theme) => `${theme.palette.info.main}40`,
                                            '&:hover': {
                                                transform: 'translateY(-1px)',
                                                boxShadow: (theme) => `0px 2px 6px ${theme.palette.info.main}20`
                                            },
                                            transition: 'all 0.2s ease'
                                        }}
                                    />
                                )}
                                {system_health.has_patterns && (
                                    <Chip 
                                        label="已建立用户画像" 
                                        color="secondary" 
                                        size="small" 
                                        sx={{
                                            background: (theme) => `linear-gradient(135deg, ${theme.palette.secondary.main}15 0%, ${theme.palette.secondary.main}25 100%)`,
                                            color: (theme) => theme.palette.secondary.main,
                                            borderColor: (theme) => `${theme.palette.secondary.main}40`,
                                            '&:hover': {
                                                transform: 'translateY(-1px)',
                                                boxShadow: (theme) => `0px 2px 6px ${theme.palette.secondary.main}20`
                                            },
                                            transition: 'all 0.2s ease'
                                        }}
                                    />
                                )}
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            )}

            {/* 统计概览 */}
            {recent_stats && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'medium' }}>
                        📊 交互统计
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={6} md={3}>
                            {renderStatCard(
                                "总交互次数",
                                recent_stats.total_interactions || 0,
                                <TrendingUpIcon />,
                                'primary'
                            )}
                        </Grid>
                        <Grid item xs={6} md={3}>
                            {renderStatCard(
                                "浏览论文数",
                                recent_stats.unique_papers || 0,
                                <PsychologyIcon />,
                                'secondary'
                            )}
                        </Grid>
                        <Grid item xs={6} md={3}>
                            {renderStatCard(
                                "高兴趣论文",
                                high_interest_papers?.count || 0,
                                <StarIcon />,
                                'warning'
                            )}
                        </Grid>
                        <Grid item xs={6} md={3}>
                            {renderStatCard(
                                "推荐论文数",
                                latest_recommendations?.count || 0,
                                <ScheduleIcon />,
                                'info'
                            )}
                        </Grid>
                    </Grid>
                </Box>
            )}

            <Divider sx={{ my: 3 }} />

            {/* 兴趣模式分析 */}
            {interest_patterns && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'medium' }}>
                        🧠 兴趣模式分析
                    </Typography>
                    <UserInterestPatterns compact={compact} />
                </Box>
            )}

            <Divider sx={{ my: 3 }} />

            {/* 个性化推荐 */}
            {latest_recommendations && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'medium' }}>
                        🎯 为你推荐
                    </Typography>
                    <PersonalizedRecommendations
                        limit={compact ? 5 : 8}
                        showExplanations={!compact}
                        compact={compact}
                        onPaperClick={(paper) => {
                            // 这里可以处理论文点击事件
                        }}
                    />
                </Box>
            )}

            {/* 高兴趣论文列表 */}
            {high_interest_papers?.papers?.length > 0 && (
                <Box>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'medium' }}>
                        ⭐ 高兴趣论文
                    </Typography>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                {high_interest_papers.papers.slice(0, compact ? 3 : 5).map((paper, index) => (
                                    <Box 
                                        key={paper.id}
                                        sx={{ 
                                            p: 1.5,
                                            bgcolor: 'grey.50',
                                            borderRadius: 1,
                                            borderLeft: 4,
                                            borderLeftColor: 'success.main'
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'flex-start', mb: 0.5 }}>
                                            <Typography 
                                                variant="subtitle2" 
                                                sx={{ 
                                                    fontWeight: 'medium',
                                                    flex: 1,
                                                    mr: 1
                                                }}
                                            >
                                                {paper.title}
                                            </Typography>
                                            <Chip
                                                label={`${paper.interest_score}%`}
                                                size="small"
                                                color="success"
                                                sx={{ fontSize: '0.7rem', height: 20 }}
                                            />
                                        </Box>
                                        <Typography variant="caption" color="text.secondary">
                                            浏览时长: {Math.floor(paper.total_view_time / 60)}分钟 | 
                                            交互次数: {paper.interaction_count}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            )}
        </Box>
    );
};

export default RecommendationDashboard;