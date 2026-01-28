import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    Typography,
    List,
    ListItem,
    ListItemText,
    Chip,
    Box,
    Button,
    CircularProgress,
    Alert,
    Divider,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    TrendingUp as TrendingUpIcon,
    Psychology as PsychologyIcon,
    Info as InfoIcon
} from '@mui/icons-material';
import apiClient from '../../services/apiClient.jsx';

/**
 * 个性化推荐组件
 * 基于用户交互历史和兴趣模式推荐论文
 */
const PersonalizedRecommendations = ({ 
    limit = 10, 
    showExplanations = true,
    onPaperClick = null,
    compact = false 
}) => {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [explanations, setExplanations] = useState({});
    const [refreshing, setRefreshing] = useState(false);

    // 获取个性化推荐
    const fetchRecommendations = async (isRefresh = false) => {
        try {
            if (isRefresh) {
                setRefreshing(true);
            } else {
                setLoading(true);
            }
            setError(null);

            const response = await apiClient.getPersonalizedRecommendations(limit);
            
            if (response.success) {
                const recommendations = response.data.recommendations || [];
                setRecommendations(recommendations);
                
                // 如果需要显示推荐解释，获取每篇论文的推荐原因
                if (showExplanations && recommendations.length > 0) {
                    const explanationPromises = recommendations.slice(0, 3).map(async (paper) => {
                        try {
                            const explanationResponse = await apiClient.getRecommendationExplanation(paper.id);
                            if (explanationResponse.success) {
                                return { id: paper.id, explanation: explanationResponse.data };
                            }
                            return { id: paper.id, explanation: null };
                        } catch (err) {
                            return { id: paper.id, explanation: null };
                        }
                    });

                    const explanationResults = await Promise.all(explanationPromises);
                    const explanationMap = {};
                    explanationResults.forEach(({ id, explanation }) => {
                        explanationMap[id] = explanation;
                    });
                    setExplanations(explanationMap);
                }
            } else {
                setError(response.error || '获取推荐失败');
            }
        } catch (err) {
            console.error('获取个性化推荐失败:', err);
            setError(err.message || '获取推荐失败');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchRecommendations();
    }, [limit]);

    // 处理论文点击
    const handlePaperClick = (paper) => {
        if (onPaperClick) {
            onPaperClick(paper);
        }
    };

    // 格式化推荐分数
    const formatScore = (score) => {
        return (score * 100).toFixed(0);
    };

    // 渲染推荐解释
    const renderExplanation = (paperId) => {
        const explanation = explanations[paperId];
        if (!explanation) return null;

        return (
            <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                    <InfoIcon sx={{ fontSize: 14, mr: 0.5 }} />
                    推荐理由:
                </Typography>
                {explanation.explanations?.map((reason, index) => (
                    <Typography key={index} variant="caption" display="block" color="text.secondary">
                        • {reason}
                    </Typography>
                ))}
            </Box>
        );
    };

    if (loading && !refreshing) {
        return (
            <Card>
                <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="center" py={3}>
                        <CircularProgress size={24} sx={{ mr: 2 }} />
                        <Typography>正在获取个性化推荐...</Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card>
                <CardContent>
                    <Alert severity="error" action={
                        <Button color="inherit" size="small" onClick={() => fetchRecommendations()}>
                            重试
                        </Button>
                    }>
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (recommendations.length === 0) {
        return (
            <Card>
                <CardContent>
                    <Alert severity="info">
                        暂无个性化推荐。多浏览一些论文后会有更好的推荐效果！
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardContent>
                <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
                    <Box display="flex" alignItems="center">
                        <PsychologyIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6" component="h2">
                            为你推荐
                        </Typography>
                        <Chip 
                            label={`${recommendations.length}篇`} 
                            size="small" 
                            color="primary" 
                            variant="outlined"
                            sx={{ ml: 1 }}
                        />
                    </Box>
                    <Tooltip title="刷新推荐">
                        <IconButton 
                            onClick={() => fetchRecommendations(true)}
                            disabled={refreshing}
                            size="small"
                        >
                            <RefreshIcon sx={{ 
                                animation: refreshing ? 'spin 1s linear infinite' : 'none',
                                '@keyframes spin': {
                                    '0%': { transform: 'rotate(0deg)' },
                                    '100%': { transform: 'rotate(360deg)' }
                                }
                            }} />
                        </IconButton>
                    </Tooltip>
                </Box>

                <List dense={compact}>
                    {recommendations.map((paper, index) => (
                        <React.Fragment key={paper.id}>
                            <ListItem
                                button={!!onPaperClick}
                                onClick={() => handlePaperClick(paper)}
                                sx={{ 
                                    px: 0,
                                    py: compact ? 1 : 1.5,
                                    '&:hover': {
                                        bgcolor: 'action.hover'
                                    }
                                }}
                            >
                                <ListItemText
                                    primary={
                                        <Box>
                                            <Box display="flex" alignItems="center" justifyContent="between" mb={0.5}>
                                                <Typography 
                                                    variant={compact ? "body2" : "subtitle2"} 
                                                    component="div"
                                                    sx={{ 
                                                        fontWeight: 'medium',
                                                        lineHeight: 1.3,
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: compact ? 2 : 3,
                                                        WebkitBoxOrient: 'vertical',
                                                        overflow: 'hidden'
                                                    }}
                                                >
                                                    {paper.title}
                                                </Typography>
                                                <Box display="flex" alignItems="center" ml={1}>
                                                    <TrendingUpIcon 
                                                        sx={{ 
                                                            fontSize: 16, 
                                                            color: 'success.main',
                                                            mr: 0.5 
                                                        }} 
                                                    />
                                                    <Typography 
                                                        variant="caption" 
                                                        color="success.main"
                                                        fontWeight="medium"
                                                    >
                                                        {formatScore(paper.recommendation_score)}%
                                                    </Typography>
                                                </Box>
                                            </Box>
                                            
                                            <Typography 
                                                variant="caption" 
                                                color="text.secondary"
                                                display="block"
                                            >
                                                {paper.authors} • {paper.journal}
                                            </Typography>

                                            {/* 匹配特征标签 */}
                                            {paper.matched_features?.length > 0 && (
                                                <Box sx={{ mt: 1 }}>
                                                    {paper.matched_features.slice(0, compact ? 2 : 3).map((feature, idx) => (
                                                        <Chip
                                                            key={idx}
                                                            label={feature}
                                                            size="small"
                                                            variant="outlined"
                                                            sx={{ 
                                                                mr: 0.5, 
                                                                mb: 0.5,
                                                                fontSize: '0.7rem',
                                                                height: 20
                                                            }}
                                                        />
                                                    ))}
                                                </Box>
                                            )}

                                            {/* 推荐解释 */}
                                            {showExplanations && !compact && renderExplanation(paper.id)}
                                        </Box>
                                    }
                                />
                            </ListItem>
                            {index < recommendations.length - 1 && <Divider />}
                        </React.Fragment>
                    ))}
                </List>

                {recommendations.length === limit && (
                    <Box textAlign="center" mt={2}>
                        <Button 
                            variant="outlined" 
                            size="small"
                            onClick={() => fetchRecommendations()}
                        >
                            查看更多推荐
                        </Button>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default PersonalizedRecommendations;