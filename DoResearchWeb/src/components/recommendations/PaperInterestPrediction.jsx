import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Chip,
    CircularProgress,
    Alert,
    LinearProgress,
    Tooltip,
    IconButton,
    Collapse,
    List,
    ListItem,
    ListItemText,
    ListItemIcon
} from '@mui/material';
import {
    Psychology as PsychologyIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
    Lightbulb as LightbulbIcon,
    Person as PersonIcon,
    Book as BookIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import apiClient from '../../services/apiClient.jsx';

/**
 * 论文兴趣预测组件
 * 基于用户的兴趣模式预测对当前论文的兴趣度
 */
const PaperInterestPrediction = ({ paperId }) => {
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expanded, setExpanded] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    // 获取论文兴趣预测
    const fetchPrediction = async (isRefresh = false) => {
        if (!paperId) return;

        try {
            if (isRefresh) {
                setRefreshing(true);
            } else {
                setLoading(true);
            }
            setError(null);

            // 获取推荐解释（这能告诉我们为什么推荐这篇论文）
            const response = await apiClient.getRecommendationExplanation(paperId);
            
            if (response.success) {
                setPrediction(response.data);
            } else {
                // 如果没有解释，说明用户还没有足够的兴趣数据
                setError('暂无兴趣预测 - 请先标记一些论文为感兴趣');
            }
        } catch (err) {
            console.error('获取兴趣预测失败:', err);
            if (err.message.includes('404')) {
                setError('暂无兴趣预测 - 请先标记一些论文为感兴趣');
            } else {
                setError(err.message || '获取兴趣预测失败');
            }
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        if (paperId) {
            fetchPrediction();
        }
    }, [paperId]); // eslint-disable-line react-hooks/exhaustive-deps

    // 计算兴趣评分（基于AI分析内容的复杂度和匹配度）
    const calculateInterestScore = (prediction) => {
        if (!prediction || !prediction.explanation) return 0;
        
        const explanation = prediction.explanation.toLowerCase();
        let score = 40; // 基础分数，表示有AI分析结果
        
        // 根据解释内容的关键词来评估兴趣度
        const highValueKeywords = ['高度匹配', '直接参考', '重要意义', '核心', '关键', '显著', '突出'];
        const mediumValueKeywords = ['匹配', '相关', '类似', '涉及', '包含', '采用'];
        const fieldKeywords = ['研究领域', '技术方法', '应用场景', '算法', '模型', '框架'];
        
        // 高价值关键词 +15分每个
        highValueKeywords.forEach(keyword => {
            if (explanation.includes(keyword)) score += 15;
        });
        
        // 中等价值关键词 +8分每个
        mediumValueKeywords.forEach(keyword => {
            if (explanation.includes(keyword)) score += 8;
        });
        
        // 领域相关关键词 +5分每个
        fieldKeywords.forEach(keyword => {
            if (explanation.includes(keyword)) score += 5;
        });
        
        // 如果解释很详细（字数多），增加分数
        if (explanation.length > 200) score += 10;
        if (explanation.length > 400) score += 10;
        
        // 限制最大分数
        return Math.min(Math.round(score), 100);
    };

    // 获取兴趣等级和颜色
    const getInterestLevel = (score) => {
        if (score >= 80) return { level: '非常感兴趣', color: 'success' };
        if (score >= 60) return { level: '比较感兴趣', color: 'warning' };
        if (score >= 40) return { level: '可能感兴趣', color: 'info' };
        if (score >= 20) return { level: '不太感兴趣', color: 'default' };
        return { level: '不感兴趣', color: 'error' };
    };

    if (!paperId) {
        return null;
    }

    if (loading && !refreshing) {
        return (
            <Card variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="center" py={1}>
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                            分析兴趣匹配度...
                        </Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                    <Alert 
                        severity="info" 
                        size="small"
                        sx={{ 
                            '& .MuiAlert-message': { 
                                fontSize: '0.8rem' 
                            }
                        }}
                    >
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (!prediction) {
        return null;
    }

    const interestScore = calculateInterestScore(prediction);
    const { level, color } = getInterestLevel(interestScore);

    return (
        <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent sx={{ pb: 1 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                    <Box display="flex" alignItems="center">
                        <PsychologyIcon color="primary" sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant="subtitle2" component="h3">
                            兴趣匹配度
                        </Typography>
                        <Chip 
                            label={level} 
                            size="small" 
                            color={color}
                            sx={{ 
                                ml: 1, 
                                height: 20, 
                                fontSize: '0.7rem',
                                fontWeight: 'medium'
                            }}
                        />
                    </Box>
                    <Box display="flex" alignItems="center">
                        <Typography 
                            variant="h6" 
                            color={`${color}.main`}
                            sx={{ 
                                fontWeight: 'bold',
                                mr: 1,
                                fontSize: '1.1rem'
                            }}
                        >
                            {interestScore}%
                        </Typography>
                        <Tooltip title="刷新兴趣预测">
                            <IconButton 
                                onClick={() => fetchPrediction(true)}
                                disabled={refreshing}
                                size="small"
                            >
                                <RefreshIcon 
                                    fontSize="small"
                                    sx={{ 
                                        animation: refreshing ? 'spin 1s linear infinite' : 'none',
                                        '@keyframes spin': {
                                            '0%': { transform: 'rotate(0deg)' },
                                            '100%': { transform: 'rotate(360deg)' }
                                        }
                                    }} 
                                />
                            </IconButton>
                        </Tooltip>
                        <IconButton
                            onClick={() => setExpanded(!expanded)}
                            size="small"
                        >
                            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                    </Box>
                </Box>

                {/* 兴趣评分进度条 */}
                <Box sx={{ mb: 1 }}>
                    <LinearProgress 
                        variant="determinate" 
                        value={interestScore} 
                        color={color}
                        sx={{ 
                            height: 6, 
                            borderRadius: 3,
                            backgroundColor: 'grey.200'
                        }}
                    />
                </Box>

                {/* 详细匹配信息 */}
                <Collapse in={expanded}>
                    <Box sx={{ pt: 1, borderTop: 1, borderColor: 'divider' }}>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                            AI智能分析：
                        </Typography>
                        
                        {/* AI分析方法 */}
                        {prediction.analysis_method && (
                            <Box sx={{ mb: 1 }}>
                                <Chip
                                    label={prediction.analysis_method}
                                    size="small"
                                    color="primary"
                                    variant="outlined"
                                    sx={{ fontSize: '0.65rem', height: 18 }}
                                />
                            </Box>
                        )}
                        
                        {/* AI分析解释 */}
                        <Box sx={{ 
                            p: 1.5, 
                            bgcolor: 'grey.50', 
                            borderRadius: 1, 
                            border: 1, 
                            borderColor: 'divider',
                            mb: 1
                        }}>
                            <Typography 
                                variant="body2" 
                                sx={{ 
                                    fontSize: '0.8rem', 
                                    lineHeight: 1.5,
                                    color: 'text.primary'
                                }}
                            >
                                {prediction.explanation}
                            </Typography>
                        </Box>

                        {/* 分析维度标签 */}
                        <Box display="flex" gap={0.5} mt={1} flexWrap="wrap">
                            {prediction.explanation?.includes('研究领域') && (
                                <Chip
                                    label="研究领域匹配"
                                    size="small"
                                    variant="outlined"
                                    color="success"
                                    sx={{ fontSize: '0.65rem', height: 18 }}
                                />
                            )}
                            {prediction.explanation?.includes('技术方法') && (
                                <Chip
                                    label="技术方法相关"
                                    size="small"
                                    variant="outlined"
                                    color="warning"
                                    sx={{ fontSize: '0.65rem', height: 18 }}
                                />
                            )}
                            {prediction.explanation?.includes('应用场景') && (
                                <Chip
                                    label="应用场景相似"
                                    size="small"
                                    variant="outlined"
                                    color="info"
                                    sx={{ fontSize: '0.65rem', height: 18 }}
                                />
                            )}
                        </Box>
                    </Box>
                </Collapse>
            </CardContent>
        </Card>
    );
};

export default PaperInterestPrediction;