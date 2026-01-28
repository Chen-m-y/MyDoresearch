import React from 'react';
import {
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    Typography,
    Stack,
    Box,
    Chip,
    Divider
} from '@mui/material';
import { formatDate, formatRelativeDate } from '../utils/dateUtils';
import AuthorChips from './AuthorChips';

function PaperList({
    papers = [],
    currentPaperId,
    onSelectPaper,
    showJournal = false,
    showReadLaterBadge = false,
    showAnalysisBadge = true,
    dateField = 'published_date', // 'published_date', 'marked_at', etc.
    dateLabel = '', // '添加于', '发布于', etc.
    loading = false,
    // 新增筛选和动画支持
    paperFilter = 'all', // 筛选条件
    fadingOutPapers = new Set(), // 淡出动画的论文集合
    enableFilterAnimation = false // 是否启用筛选动画
}) {

    const handlePaperClick = (paper) => {
        // 对于稍后阅读等场景，paper_id 是论文的真实ID，id可能是其他记录ID
        const paperId = paper.paper_id || paper.id;
        if (onSelectPaper) {
            onSelectPaper(paperId);
        }
    };

    const getPaperId = (paper) => paper.paper_id || paper.id;
    const getPaperTitle = (paper) => paper.title || (paper.paper && paper.paper.title);
    const getPaperAuthors = (paper) => paper.authors || paper.author || (paper.paper && (paper.paper.authors || paper.paper.author));
    const getPaperJournal = (paper) => paper.journal || (paper.paper && paper.paper.journal);
    const getPaperDate = (paper) => paper[dateField] || paper.published_date || paper.marked_at || (paper.paper && (paper.paper[dateField] || paper.paper.published_date || paper.paper.marked_at));
    const getPaperStatus = (paper) => paper.status || (paper.paper && paper.paper.status);
    const hasAnalysisResult = (paper) => paper.analysis_result || (paper.paper && paper.paper.analysis_result);
    const hasPdfFile = (paper) => {
        // 支持多种可能的PDF字段名称和数据结构
        return paper.pdf_path || paper.pdfPath || (paper.paper && paper.paper.pdf_path);
    };
    const isInReadLater = (paper) => {
        // 检查论文是否在稍后阅读列表中
        return paper.read_later && paper.read_later !== null;
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <Typography>加载中...</Typography>
            </Box>
        );
    }

    if (papers.length === 0) {
        return (
            <Box sx={{ textAlign: 'center', p: 4 }}>
                <Typography variant="body1" color="text.secondary">
                    暂无论文
                </Typography>
            </Box>
        );
    }

    return (
        <List disablePadding sx={{ overflowX: 'hidden' }}>
                {papers.map((paper) => {
                    const paperId = getPaperId(paper);
                    const isSelected = currentPaperId === paperId;
                    const paperStatus = getPaperStatus(paper);
                    
                    // 筛选和动画逻辑
                    const matchesFilter = !enableFilterAnimation || paperFilter === 'all' || paperStatus === paperFilter;
                    const isKeptVisible = enableFilterAnimation && isSelected && !matchesFilter;
                    const isFadingOut = enableFilterAnimation && fadingOutPapers.has(paperId);
                    
                    return (
                        <React.Fragment key={paperId}>
                            <ListItem disablePadding>
                                <ListItemButton
                                    selected={isSelected}
                                    onClick={() => handlePaperClick(paper)}
                                    sx={(theme) => ({
                                        px: 1,
                                        py: 0.75,
                                        position: 'relative',
                                        transition: enableFilterAnimation ? 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)' : 'background-color 0.2s ease-in-out',
                                        transform: isFadingOut ? 'translateX(-20px)' : 'translateX(0)',
                                        opacity: isFadingOut ? 0.3 : 1,
                                        // 为不匹配筛选条件但保持可见的论文添加特殊样式
                                        ...(isKeptVisible && {
                                            backgroundColor: theme.palette.action.hover + '40',
                                            borderLeft: `3px solid ${theme.palette.warning.main}`,
                                        }),
                                        '&:hover': { backgroundColor: theme.palette.action.hover },
                                        '&.Mui-selected': {
                                            backgroundColor: theme.palette.action.selected,
                                            '&::before': {
                                                content: '""',
                                                position: 'absolute',
                                                left: isKeptVisible ? '3px' : 0,
                                                top: '15%',
                                                bottom: '15%',
                                                width: '4px',
                                                backgroundColor: theme.palette.primary.main,
                                                borderRadius: '0 4px 4px 0'
                                            }
                                        }
                                    })}
                                >
                                    <ListItemText
                                        primary={
                                            <Stack direction="row" spacing={1.5} alignItems="center">
                                                {/* 状态指示器 */}
                                                {paperStatus === 'unread' && (
                                                    <Box component="span" sx={{
                                                        width: 8,
                                                        height: 8,
                                                        borderRadius: '50%',
                                                        backgroundColor: 'primary.main',
                                                        flexShrink: 0
                                                    }} />
                                                )}
                                                {(showReadLaterBadge && !paperStatus) || isInReadLater(paper) ? (
                                                    <Box component="span" sx={{
                                                        width: 8,
                                                        height: 8,
                                                        borderRadius: '50%',
                                                        backgroundColor: 'secondary.main',
                                                        flexShrink: 0
                                                    }} />
                                                ) : null}
                                                
                                                {/* 论文标题 */}
                                                <Typography
                                                    variant="body1"
                                                    sx={{
                                                        fontWeight: 500,
                                                        lineHeight: 1.5,
                                                        fontSize: '0.9rem',
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: 3,
                                                        WebkitBoxOrient: 'vertical',
                                                        overflow: 'hidden',
                                                        minWidth: 0,
                                                        flex: 1
                                                    }}
                                                >
                                                    {getPaperTitle(paper)}
                                                </Typography>
                                            </Stack>
                                        }
                                        secondary={
                                            <Stack sx={{ mt: 1.5 }} spacing={0.5}>
                                                {/* 作者信息 */}
                                                {getPaperAuthors(paper) && (
                                                    <Box sx={{ mb: 0.5 }}>
                                                        <AuthorChips authors={getPaperAuthors(paper)} />
                                                    </Box>
                                                )}
                                                
                                                {/* 期刊信息 */}
                                                {showJournal && getPaperJournal(paper) && (
                                                    <Typography variant="caption" color="text.secondary" noWrap>
                                                        {getPaperJournal(paper)}
                                                    </Typography>
                                                )}
                                                
                                                {/* 底部一行：日期和标签 */}
                                                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ minWidth: 0 }}>
                                                    <Typography variant="caption" color="text.secondary" sx={{ flex: 1, minWidth: 0 }}>
                                                        {dateLabel ? `${dateLabel} ` : ''}
                                                        {dateLabel === '添加于' ? formatRelativeDate(getPaperDate(paper)) : formatDate(getPaperDate(paper))}
                                                    </Typography>
                                                    
                                                    <Box display="flex" alignItems="center" spacing={1} sx={{ flexShrink: 0, ml: 1 }}>
                                                        {/* PDF文件标签 */}
                                                        {hasPdfFile(paper) && (
                                                            <Chip
                                                                label="PDF"
                                                                size="small"
                                                                color="info"
                                                                variant="filled"
                                                                sx={{
                                                                    marginRight: 0.5,
                                                                    height: 18,
                                                                    fontSize: '0.65rem',
                                                                    background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}80 0%, ${theme.palette.info.main}90 100%)`,
                                                                    color: 'white',
                                                                    '& .MuiChip-label': {
                                                                        px: 0.75,
                                                                        py: 0
                                                                    },
                                                                    '&:hover': {
                                                                        background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}90 0%, ${theme.palette.info.main} 100%)`,
                                                                        transform: 'translateY(-1px)',
                                                                        boxShadow: (theme) => `0px 2px 6px ${theme.palette.info.main}30`
                                                                    },
                                                                    transition: 'all 0.2s ease'
                                                                }}
                                                            />
                                                        )}
                                                        
                                                        {/* 深度分析标签 */}
                                                        {showAnalysisBadge && hasAnalysisResult(paper) && (
                                                            <Chip
                                                                label="深度分析"
                                                                size="small"
                                                                color="warning"
                                                                variant="filled"
                                                                sx={{
                                                                    marginRight: 0.5,
                                                                    height: 18,
                                                                    fontSize: '0.65rem',
                                                                    background: (theme) => `linear-gradient(135deg, ${theme.palette.warning.main}80 0%, ${theme.palette.warning.main}90 100%)`,
                                                                    color: 'white',
                                                                    '& .MuiChip-label': {
                                                                        px: 0.75,
                                                                        py: 0
                                                                    },
                                                                    '&:hover': {
                                                                        background: (theme) => `linear-gradient(135deg, ${theme.palette.warning.main}90 0%, ${theme.palette.warning.main} 100%)`,
                                                                        transform: 'translateY(-1px)',
                                                                        boxShadow: (theme) => `0px 2px 6px ${theme.palette.warning.main}30`
                                                                    },
                                                                    transition: 'all 0.2s ease'
                                                                }}
                                                            />
                                                        )}
                                                        
                                                        {/* 稍后阅读标签 */}
                                                        {(showReadLaterBadge || isInReadLater(paper)) && (
                                                            <Chip
                                                                label="稍后阅读"
                                                                size="small"
                                                                color="secondary"
                                                                variant="outlined"
                                                                sx={{
                                                                    marginRight: 0.5,
                                                                    height: 18,
                                                                    fontSize: '0.65rem',
                                                                    background: (theme) => `linear-gradient(135deg, ${theme.palette.secondary.main}08 0%, ${theme.palette.secondary.main}15 100%)`,
                                                                    borderColor: (theme) => `${theme.palette.secondary.main}40`,
                                                                    color: (theme) => theme.palette.secondary.main,
                                                                    '& .MuiChip-label': {
                                                                        px: 0.75,
                                                                        py: 0
                                                                    },
                                                                    '&:hover': {
                                                                        background: (theme) => `linear-gradient(135deg, ${theme.palette.secondary.main}12 0%, ${theme.palette.secondary.main}20 100%)`,
                                                                    },
                                                                    transition: 'all 0.2s ease'
                                                                }}
                                                            />
                                                        )}
                                                        
                                                        {/* 已读/未读状态标签 - 始终显示在最右侧 */}
                                                        <Chip
                                                            label={paperStatus === 'read' ? '已读' : '未读'}
                                                            size="small"
                                                            color={paperStatus === 'read' ? 'success' : 'warning'}
                                                            variant={paperStatus === 'read' ? 'outlined' : 'filled'}
                                                            sx={{
                                                                height: 18,
                                                                fontSize: '0.65rem',
                                                                background: (theme) => {
                                                                    const color = paperStatus === 'read' ? theme.palette.success.main : theme.palette.warning.main;
                                                                    return paperStatus === 'read'
                                                                        ? `linear-gradient(135deg, ${color}08 0%, ${color}15 100%)`
                                                                        : `linear-gradient(135deg, ${color}80 0%, ${color}90 100%)`;
                                                                },
                                                                borderColor: (theme) => {
                                                                    return paperStatus === 'read' ? `${theme.palette.success.main}40` : 'transparent';
                                                                },
                                                                color: (theme) => {
                                                                    return paperStatus === 'read' ? theme.palette.success.main : 'white';
                                                                },
                                                                '& .MuiChip-label': {
                                                                    px: 0.75,
                                                                    py: 0
                                                                },
                                                                '&:hover': {
                                                                    background: (theme) => {
                                                                        const color = paperStatus === 'read' ? theme.palette.success.main : theme.palette.warning.main;
                                                                        return paperStatus === 'read'
                                                                            ? `linear-gradient(135deg, ${color}12 0%, ${color}20 100%)`
                                                                            : `linear-gradient(135deg, ${color}90 0%, ${color} 100%)`;
                                                                    }
                                                                },
                                                                transition: 'all 0.2s ease'
                                                            }}
                                                        />
                                                    </Box>
                                                </Stack>
                                            </Stack>
                                        }
                                        secondaryTypographyProps={{
                                            component: 'div',
                                            variant: 'body2'
                                        }}
                                    />
                                </ListItemButton>
                            </ListItem>
                            <Divider component="li" />
                        </React.Fragment>
                    );
                })}
        </List>
    );
}

export default PaperList;