import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Chip,
    LinearProgress,
    Alert,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Divider,
    Tooltip,
    CircularProgress,
    IconButton
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    Psychology as PsychologyIcon,
    TrendingUp as TrendingUpIcon,
    Schedule as ScheduleIcon,
    Refresh as RefreshIcon,
    Info as InfoIcon
} from '@mui/icons-material';
import apiClient from '../../services/apiClient.jsx';

/**
 * 用户兴趣模式分析组件
 * 显示基于时间衰减权重的用户兴趣分析
 */
const UserInterestPatterns = ({ compact = false }) => {
    const [patterns, setPatterns] = useState(null);
    const [timeDecayInfo, setTimeDecayInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    // 获取用户兴趣模式
    const fetchPatterns = async (isRefresh = false) => {
        try {
            if (isRefresh) {
                setRefreshing(true);
            } else {
                setLoading(true);
            }
            setError(null);

            const [patternsResponse, timeDecayResponse] = await Promise.all([
                apiClient.getUserPatterns(),
                apiClient.getTimeDecayInfo()
            ]);

            if (patternsResponse.success) {
                setPatterns(patternsResponse.data);
            }
            if (timeDecayResponse.success) {
                setTimeDecayInfo(timeDecayResponse.data);
            }
        } catch (err) {
            console.error('获取用户兴趣模式失败:', err);
            setError(err.message || '获取兴趣模式失败');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchPatterns();
    }, []);

    // 格式化权重分数
    const formatWeight = (weight) => {
        return (weight * 100).toFixed(1);
    };

    // 获取权重颜色
    const getWeightColor = (weight) => {
        if (weight >= 0.8) return 'success';
        if (weight >= 0.6) return 'info';
        if (weight >= 0.4) return 'warning';
        return 'default';
    };

    // 渲染兴趣项目
    const renderInterestItems = (items, title, icon) => {
        if (!items || Object.keys(items).length === 0) return null;

        const sortedItems = Object.entries(items)
            .sort(([, a], [, b]) => b - a)
            .slice(0, compact ? 5 : 10);

        return (
            <Accordion defaultExpanded={!compact}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box display="flex" alignItems="center">
                        {icon}
                        <Typography variant="subtitle1" sx={{ ml: 1, fontWeight: 'medium' }}>
                            {title}
                        </Typography>
                        <Chip 
                            label={sortedItems.length} 
                            size="small" 
                            sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                        />
                    </Box>
                </AccordionSummary>
                <AccordionDetails>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {sortedItems.map(([name, weight], index) => (
                            <Box key={name} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography 
                                    variant="body2" 
                                    sx={{ 
                                        minWidth: 120, 
                                        flex: 1,
                                        fontSize: compact ? '0.8rem' : '0.875rem'
                                    }}
                                >
                                    {name}
                                </Typography>
                                <Box sx={{ flex: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <LinearProgress
                                        variant="determinate"
                                        value={weight * 100}
                                        color={getWeightColor(weight)}
                                        sx={{ 
                                            flex: 1, 
                                            height: 6, 
                                            borderRadius: 3
                                        }}
                                    />
                                    <Typography 
                                        variant="caption" 
                                        color={`${getWeightColor(weight)}.main`}
                                        sx={{ 
                                            minWidth: 40, 
                                            fontWeight: 'medium',
                                            fontSize: '0.7rem'
                                        }}
                                    >
                                        {formatWeight(weight)}%
                                    </Typography>
                                </Box>
                            </Box>
                        ))}
                    </Box>
                </AccordionDetails>
            </Accordion>
        );
    };

    if (loading && !refreshing) {
        return (
            <Card>
                <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="center" py={3}>
                        <CircularProgress size={24} sx={{ mr: 2 }} />
                        <Typography>正在分析用户兴趣模式...</Typography>
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
                        <IconButton 
                            color="inherit" 
                            size="small" 
                            onClick={() => fetchPatterns()}
                        >
                            <RefreshIcon fontSize="small" />
                        </IconButton>
                    }>
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (!patterns || !patterns.time_weighted_patterns) {
        return (
            <Card>
                <CardContent>
                    <Alert severity="info">
                        暂无足够的交互数据进行兴趣分析。多浏览一些论文后会有更准确的分析结果！
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    const { time_weighted_patterns, analysis_info, basic_patterns } = patterns;

    return (
        <Card>
            <CardContent>
                <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
                    <Box display="flex" alignItems="center">
                        <PsychologyIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6" component="h2">
                            兴趣模式分析
                        </Typography>
                        {analysis_info?.time_decay_enabled && (
                            <Tooltip title="基于时间衰减权重的智能分析">
                                <ScheduleIcon 
                                    color="info" 
                                    sx={{ ml: 1, fontSize: 20 }} 
                                />
                            </Tooltip>
                        )}
                    </Box>
                    <IconButton 
                        onClick={() => fetchPatterns(true)}
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
                </Box>

                {/* 时间衰减权重说明 */}
                {analysis_info?.description && !compact && (
                    <Alert severity="info" sx={{ mb: 2 }} icon={<InfoIcon />}>
                        <Typography variant="caption">
                            {analysis_info.description}
                        </Typography>
                    </Alert>
                )}

                {/* 统计概览 */}
                <Box sx={{ 
                    display: 'grid', 
                    gridTemplateColumns: compact ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)', 
                    gap: 1, 
                    mb: 2 
                }}>
                    <Box sx={{ 
                        textAlign: 'center', 
                        p: 1.5, 
                        bgcolor: 'grey.50', 
                        borderRadius: 2 
                    }}>
                        <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
                            {time_weighted_patterns.total_papers || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            分析论文数
                        </Typography>
                    </Box>
                    <Box sx={{ 
                        textAlign: 'center', 
                        p: 1.5, 
                        bgcolor: 'grey.50', 
                        borderRadius: 2 
                    }}>
                        <Typography variant="h6" color="success.main" sx={{ fontWeight: 'bold' }}>
                            {Object.keys(time_weighted_patterns.keywords || {}).length}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            关注关键词
                        </Typography>
                    </Box>
                    {!compact && (
                        <Box sx={{ 
                            textAlign: 'center', 
                            p: 1.5, 
                            bgcolor: 'grey.50', 
                            borderRadius: 2 
                        }}>
                            <Typography variant="h6" color="info.main" sx={{ fontWeight: 'bold' }}>
                                {Object.keys(time_weighted_patterns.authors || {}).length}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                关注作者
                            </Typography>
                        </Box>
                    )}
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* 兴趣模式详情 */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {renderInterestItems(
                        time_weighted_patterns.keywords,
                        '关键词偏好',
                        <TrendingUpIcon color="primary" sx={{ fontSize: 20 }} />
                    )}

                    {renderInterestItems(
                        time_weighted_patterns.authors,
                        '作者偏好', 
                        <PsychologyIcon color="secondary" sx={{ fontSize: 20 }} />
                    )}

                    {renderInterestItems(
                        time_weighted_patterns.journals,
                        '期刊偏好',
                        <InfoIcon color="info" sx={{ fontSize: 20 }} />
                    )}
                </Box>

                {/* 基础统计信息 */}
                {basic_patterns && !compact && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                        <Typography variant="caption" color="text.secondary">
                            基础分析覆盖 {basic_patterns.total_analyzed_papers} 篇论文，
                            时间加权分析覆盖 {time_weighted_patterns.total_papers} 篇论文
                        </Typography>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default UserInterestPatterns;