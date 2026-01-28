import React, { useState } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Chip,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Fade,
    Alert,
    Collapse,
    IconButton
} from '@mui/material';
import {
    Psychology as PsychologyIcon,
    TrendingUp as TrendingUpIcon,
    AccessTime as AccessTimeIcon,
    Visibility as VisibilityIcon,
    TouchApp as TouchAppIcon,
    Info as InfoIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon
} from '@mui/icons-material';

/**
 * 兴趣分析结果显示组件
 * 显示用户对论文的兴趣分析结果
 */
const InterestAnalysisResult = ({ 
    analysisResult, 
    visible = true,
    onClose = null,
    defaultExpanded = true
}) => {
    const [expanded, setExpanded] = useState(defaultExpanded);
    
    if (!analysisResult || !visible) return null;

    const {
        paperId,
        interestLevel,
        interestScore,
        signals = [],
        duration,
        scrollDepth
    } = analysisResult;

    // 兴趣级别配置
    const interestLevelConfig = {
        very_low: {
            label: '很低兴趣',
            color: 'error',
            description: '浏览时间很短，可能不太感兴趣',
            bgColor: 'error.lighter'
        },
        low: {
            label: '低兴趣',
            color: 'warning',
            description: '简单浏览，兴趣有限',
            bgColor: 'warning.lighter'
        },
        medium: {
            label: '中等兴趣',
            color: 'info',
            description: '有一定兴趣，进行了基本阅读',
            bgColor: 'info.lighter'
        },
        high: {
            label: '高兴趣',
            color: 'success',
            description: '表现出较强兴趣，深度阅读',
            bgColor: 'success.lighter'
        },
        very_high: {
            label: '很高兴趣',
            color: 'success',
            description: '表现出很强兴趣，深入研读',
            bgColor: 'success.lighter'
        }
    };

    const config = interestLevelConfig[interestLevel] || interestLevelConfig.medium;

    // 格式化时长
    const formatDuration = (seconds) => {
        if (seconds < 60) return `${seconds}秒`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分钟`;
    };

    // 获取信号图标
    const getSignalIcon = (signal) => {
        if (signal.includes('时长') || signal.includes('时间')) return <AccessTimeIcon />;
        if (signal.includes('滚动') || signal.includes('查看')) return <VisibilityIcon />;
        if (signal.includes('点击') || signal.includes('交互')) return <TouchAppIcon />;
        return <TrendingUpIcon />;
    };

    return (
        <Fade in={visible} timeout={500}>
            <Card sx={{ 
                mb: { xs: 1, md: 2 }, // 移动端减少下边距
                border: 1,
                borderColor: `${config.color}.light`,
                bgcolor: config.bgColor,
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                    boxShadow: 2
                }
            }}>
                <CardContent sx={{ 
                    p: { xs: 1.5, md: 2 }, // 移动端减少内边距
                    '&:last-child': { pb: { xs: 1.5, md: 2 } }
                }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 1, md: 2 } }}>
                        <PsychologyIcon color={config.color} sx={{ mr: 1, fontSize: { xs: 24, md: 28 } }} />
                        <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" sx={{ 
                                fontWeight: 'bold', 
                                mb: 0.5,
                                fontSize: { xs: '1rem', md: '1.25rem' } // 移动端字体小一些
                            }}>
                                阅读兴趣分析
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{
                                fontSize: { xs: '0.75rem', md: '0.875rem' } // 移动端字体小一些
                            }}>
                                基于您的阅读行为智能分析结果
                            </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, md: 1 } }}>
                            <Chip
                                label={config.label}
                                color={config.color}
                                variant="filled"
                                size="small"
                                sx={{ 
                                    fontWeight: 'bold',
                                    fontSize: { xs: '0.7rem', md: '0.75rem' },
                                    height: { xs: 20, md: 24 }
                                }}
                            />
                            <IconButton
                                onClick={() => setExpanded(!expanded)}
                                size="small"
                                sx={{ 
                                    transition: 'transform 0.2s',
                                    transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                    p: { xs: 0.5, md: 1 }
                                }}
                            >
                                <ExpandMoreIcon sx={{ fontSize: { xs: 18, md: 20 } }} />
                            </IconButton>
                            {onClose && (
                                <Chip
                                    label="×"
                                    size="small"
                                    onClick={onClose}
                                    sx={{ 
                                        cursor: 'pointer',
                                        minWidth: { xs: 20, md: 24 },
                                        height: { xs: 20, md: 24 },
                                        fontSize: { xs: '0.7rem', md: '0.75rem' },
                                        '& .MuiChip-label': { px: 0.5 }
                                    }}
                                />
                            )}
                        </Box>
                    </Box>

                    <Collapse in={expanded}>
                        {/* 兴趣度评分 */}
                        <Box sx={{ mb: { xs: 1.5, md: 2 } }}>
                            <Typography variant="subtitle1" sx={{ 
                                fontWeight: 'medium', 
                                mb: { xs: 0.5, md: 1 },
                                fontSize: { xs: '0.9rem', md: '1rem' }
                            }}>
                                兴趣度评估
                            </Typography>
                        
                        <LinearProgress
                            variant="determinate"
                            value={interestScore}
                            color={config.color}
                            sx={{ 
                                height: { xs: 6, md: 8 }, 
                                borderRadius: 4,
                                mb: { xs: 0.5, md: 1 }
                            }}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                            <Typography variant="body2" color="text.secondary" sx={{
                                fontSize: { xs: '0.75rem', md: '0.875rem' }
                            }}>
                                {config.description}
                            </Typography>
                            <Typography variant="subtitle2" color={`${config.color}.main`} sx={{ 
                                fontWeight: 'bold',
                                fontSize: { xs: '0.8rem', md: '0.875rem' }
                            }}>
                                {interestScore}%
                            </Typography>
                        </Box>
                    </Box>

                    {/* 行为数据 */}
                    <Box sx={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(2, 1fr)', 
                        gap: { xs: 1, md: 2 }, 
                        mb: { xs: 1.5, md: 2 },
                        p: { xs: 1, md: 1.5 },
                        bgcolor: 'background.paper',
                        borderRadius: 1
                    }}>
                        <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" color="primary.main" sx={{ 
                                fontWeight: 'bold',
                                fontSize: { xs: '1rem', md: '1.25rem' }
                            }}>
                                {formatDuration(duration || 0)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{
                                fontSize: { xs: '0.7rem', md: '0.75rem' }
                            }}>
                                阅读时长
                            </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" color="secondary.main" sx={{ 
                                fontWeight: 'bold',
                                fontSize: { xs: '1rem', md: '1.25rem' }
                            }}>
                                {Math.round(scrollDepth || 0)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{
                                fontSize: { xs: '0.7rem', md: '0.75rem' }
                            }}>
                                浏览深度
                            </Typography>
                        </Box>
                    </Box>

                    {/* 分析信号 */}
                    {signals.length > 0 && (
                        <Box>
                            <Typography variant="subtitle2" sx={{ 
                                mb: { xs: 0.5, md: 1 }, 
                                fontWeight: 'medium',
                                fontSize: { xs: '0.8rem', md: '0.875rem' }
                            }}>
                                分析依据:
                            </Typography>
                            <List dense sx={{ py: 0 }}>
                                {signals.map((signal, index) => (
                                    <ListItem key={index} sx={{ 
                                        py: { xs: 0.1, md: 0.25 }, 
                                        px: 0 
                                    }}>
                                        <ListItemIcon sx={{ minWidth: { xs: 28, md: 32 } }}>
                                            {React.cloneElement(getSignalIcon(signal), {
                                                sx: { fontSize: { xs: 16, md: 18 }, color: 'text.secondary' }
                                            })}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={signal}
                                            primaryTypographyProps={{
                                                variant: 'body2',
                                                color: 'text.secondary',
                                                sx: { fontSize: { xs: '0.75rem', md: '0.875rem' } }
                                            }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Box>
                    )}

                        {/* 改进建议 */}
                        {(interestLevel === 'high' || interestLevel === 'very_high') && (
                            <Alert severity="info" sx={{ mt: { xs: 1, md: 2 } }}>
                                <Typography variant="body2" sx={{
                                    fontSize: { xs: '0.75rem', md: '0.875rem' }
                                }}>
                                    💡 由于您对此类论文很感兴趣，我们会为您推荐更多相关内容！
                                </Typography>
                            </Alert>
                        )}
                    </Collapse>
                </CardContent>
            </Card>
        </Fade>
    );
};

export default InterestAnalysisResult;