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
    CircularProgress,
    Alert,
    Divider,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    FindInPage as SimilarityIcon,
    KeyboardArrowRight as ArrowIcon
} from '@mui/icons-material';
import apiClient from '../../services/apiClient.jsx';

/**
 * 相似论文推荐组件
 * 基于指定论文查找相似内容
 */
const SimilarPapers = ({ 
    paperId, 
    paperTitle = '',
    limit = 5, 
    onPaperClick = null,
    compact = false,
    showSimilarityScore = true 
}) => {
    const [similarPapers, setSimilarPapers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    // 获取相似论文
    const fetchSimilarPapers = async (isRefresh = false) => {
        if (!paperId) return;

        try {
            if (isRefresh) {
                setRefreshing(true);
            } else {
                setLoading(true);
            }
            setError(null);

            const response = await apiClient.getSimilarPapers(paperId, limit);
            
            if (response.success) {
                setSimilarPapers(response.data.similar_papers || []);
            } else {
                setError(response.error || '获取相似论文失败');
            }
        } catch (err) {
            console.error('获取相似论文失败:', err);
            setError(err.message || '获取相似论文失败');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        if (paperId) {
            fetchSimilarPapers();
        }
    }, [paperId, limit]);

    // 处理论文点击
    const handlePaperClick = (paper) => {
        if (onPaperClick) {
            onPaperClick(paper);
        }
    };

    // 格式化相似度分数
    const formatSimilarity = (score) => {
        return (score * 100).toFixed(0);
    };

    // 获取相似度颜色
    const getSimilarityColor = (score) => {
        if (score >= 0.8) return 'success';
        if (score >= 0.6) return 'warning';
        return 'default';
    };

    if (!paperId) {
        return null;
    }

    if (loading && !refreshing) {
        return (
            <Card>
                <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="center" py={2}>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        <Typography variant="body2">正在查找相似论文...</Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card>
                <CardContent>
                    <Alert 
                        severity="warning" 
                        size="small"
                        action={
                            <IconButton 
                                color="inherit" 
                                size="small" 
                                onClick={() => fetchSimilarPapers()}
                            >
                                <RefreshIcon fontSize="small" />
                            </IconButton>
                        }
                    >
                        {error}
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    if (similarPapers.length === 0) {
        return (
            <Card>
                <CardContent>
                    <Alert severity="info" size="small">
                        暂未找到相似论文
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardContent>
                <Box display="flex" alignItems="center" justifyContent="between" mb={1.5}>
                    <Box display="flex" alignItems="center">
                        <SimilarityIcon color="primary" sx={{ mr: 1, fontSize: 20 }} />
                        <Typography variant={compact ? "subtitle2" : "h6"} component="h3">
                            相似论文
                        </Typography>
                        <Chip 
                            label={`${similarPapers.length}篇`} 
                            size="small" 
                            color="primary" 
                            variant="outlined"
                            sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                        />
                    </Box>
                    <Tooltip title="刷新相似论文">
                        <IconButton 
                            onClick={() => fetchSimilarPapers(true)}
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
                </Box>

                {/* 基准论文信息 */}
                {paperTitle && !compact && (
                    <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="caption" color="text.secondary" display="block">
                            基于论文:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                            {paperTitle}
                        </Typography>
                    </Box>
                )}

                <List dense={compact}>
                    {similarPapers.map((paper, index) => (
                        <React.Fragment key={paper.id}>
                            <ListItem
                                button={!!onPaperClick}
                                onClick={() => handlePaperClick(paper)}
                                sx={{ 
                                    px: 0,
                                    py: compact ? 0.5 : 1,
                                    '&:hover': {
                                        bgcolor: 'action.hover'
                                    }
                                }}
                            >
                                <ListItemText
                                    primary={
                                        <Box>
                                            <Box display="flex" alignItems="flex-start" justifyContent="between">
                                                <Typography 
                                                    variant={compact ? "body2" : "subtitle2"} 
                                                    component="div"
                                                    sx={{ 
                                                        fontWeight: 'medium',
                                                        lineHeight: 1.3,
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: compact ? 2 : 3,
                                                        WebkitBoxOrient: 'vertical',
                                                        overflow: 'hidden',
                                                        flex: 1,
                                                        mr: 1
                                                    }}
                                                >
                                                    {paper.title}
                                                </Typography>
                                                
                                                {showSimilarityScore && (
                                                    <Box display="flex" alignItems="center" flexShrink={0}>
                                                        <Chip
                                                            label={`${formatSimilarity(paper.similarity_score)}%`}
                                                            size="small"
                                                            color={getSimilarityColor(paper.similarity_score)}
                                                            variant="outlined"
                                                            sx={{ 
                                                                fontSize: '0.7rem',
                                                                height: 20,
                                                                minWidth: 40
                                                            }}
                                                        />
                                                        {onPaperClick && (
                                                            <ArrowIcon 
                                                                sx={{ 
                                                                    ml: 0.5, 
                                                                    fontSize: 16,
                                                                    color: 'text.secondary'
                                                                }} 
                                                            />
                                                        )}
                                                    </Box>
                                                )}
                                            </Box>
                                            
                                            <Typography 
                                                variant="caption" 
                                                color="text.secondary"
                                                display="block"
                                                sx={{ mt: 0.5 }}
                                            >
                                                {paper.authors}
                                            </Typography>

                                            {paper.journal && (
                                                <Typography 
                                                    variant="caption" 
                                                    color="text.secondary"
                                                    display="block"
                                                >
                                                    {paper.journal}
                                                </Typography>
                                            )}

                                            {/* 关键词匹配数量 */}
                                            {paper.keyword_matches > 0 && (
                                                <Box sx={{ mt: 0.5 }}>
                                                    <Chip
                                                        label={`${paper.keyword_matches}个关键词匹配`}
                                                        size="small"
                                                        variant="outlined"
                                                        color="secondary"
                                                        sx={{ 
                                                            fontSize: '0.65rem',
                                                            height: 18
                                                        }}
                                                    />
                                                </Box>
                                            )}
                                        </Box>
                                    }
                                />
                            </ListItem>
                            {index < similarPapers.length - 1 && <Divider />}
                        </React.Fragment>
                    ))}
                </List>
            </CardContent>
        </Card>
    );
};

export default SimilarPapers;