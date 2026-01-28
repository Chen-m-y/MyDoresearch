import React, { useState, useEffect, useContext, useCallback } from 'react';
import {
    Box,
    Paper,
    Typography,
    useMediaQuery,
    useTheme,
    IconButton,
    CircularProgress, 
    Card, 
    CardContent,
    List,
    ListItem,
    ListItemText,
    Pagination
} from '@mui/material';
import {
    ArrowBack as ArrowBackIcon,
    ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';

import apiClient from '../../services/apiClient';
import { PaperContext } from '../../contexts/PaperContext'; // 引入 PaperContext
import PaperDetail from '../PaperDetail';
import PaperList from '../PaperList';
import { LAYOUT_CONSTANTS } from '../../constants/layout.js';
import { usePagination } from '../../hooks/usePagination.js';

function ReadLaterView() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD));

    // --- 从 PaperContext 获取状态和函数 ---
    const {
        currentPaper,
        currentPaperId,
        selectPaper,
        setCurrentView,
        registerViewRefreshCallback // 新增：注册刷新回调
    } = useContext(PaperContext);

    // 使用服务器端分页
    const fetchReadLaterWithPagination = useCallback((params) => {
        return apiClient.getReadLaterList({
            order_by: 'priority',
            ...params
        });
    }, []);

    const {
        data: readLaterPapers,
        loading: loadingList,
        pagination,
        goToPage,
        refresh,
        isEmpty,
        hasData
    } = usePagination({
        fetchFunction: fetchReadLaterWithPagination,
        perPage: 15,
        autoFetch: true,
        dependencies: []
    });

    const handlePageChange = (event, page) => {
        goToPage(page);
    };

    useEffect(() => {
        setCurrentView('readlater');
    }, [setCurrentView]);

    // 注册视图刷新回调
    useEffect(() => {
        const unregister = registerViewRefreshCallback((paperId, oldStatus, newStatus) => {
            // ReadLater 视图需要刷新列表，因为状态变更可能影响稍后阅读的论文显示
            refresh();
        });

        return unregister; // 组件卸载时注销回调
    }, [registerViewRefreshCallback, refresh]);

    // 当离开此视图时，清空当前选择
    useEffect(() => {
        return () => {
            selectPaper(null);
        };
    }, [selectPaper]);

    // --- handleSelectPaper 现在直接调用 Context 的函数 ---
    const handleSelectPaper = (paperId) => {
        selectPaper(paperId); // 调用 context 中的 selectPaper
    };

    // 论文导航
    const handleNavigate = (direction) => {
        if (!currentPaperId || readLaterPapers.length === 0) return;
        const currentIndex = readLaterPapers.findIndex(p => p.paper_id === currentPaperId);
        if (currentIndex === -1) return;

        let targetIndex;
        if (direction === 'prev') {
            targetIndex = currentIndex - 1;
        } else {
            targetIndex = currentIndex + 1;
        }

        if (targetIndex >= 0 && targetIndex < readLaterPapers.length) {
            const targetPaper = readLaterPapers[targetIndex];
            handleSelectPaper(targetPaper.paper_id);
        }
    };

    // 获取导航信息
    const getNavigationInfo = () => {
        if (!currentPaperId || readLaterPapers.length === 0) return null;
        const currentIndex = readLaterPapers.findIndex(p => p.paper_id === currentPaperId);
        if (currentIndex === -1) return null;

        return {
            hasPrev: currentIndex > 0,
            hasNext: currentIndex < readLaterPapers.length - 1,
            current: currentIndex + 1,
            total: readLaterPapers.length
        };
    };


    // 渲染论文列表
    const renderPaperList = () => (
        <Paper
            elevation={0}
            sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                borderRight: `1px solid`,
                borderColor: 'divider',
                borderRadius: 0,
            }}
        >
            {/* 列表头部 */}
            <Box sx={{ height: '76px', p: 2.5, bgcolor: 'grey.50', borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                        📚 稍后阅读
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.2, mt: 0.5 }}>
                        {pagination ? `共 ${pagination.total} 篇待读论文` : `共 ${readLaterPapers.length} 篇待读论文`}
                        {pagination && pagination.total_pages > 1 && ` (第 ${pagination.page}/${pagination.total_pages} 页)`}
                    </Typography>
                </Box>
            </Box>

            {/* 列表主体 */}
            <Box sx={{ flex: 1, overflowY: 'auto' }}>
                {loadingList ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                        <CircularProgress />
                    </Box>
                ) : isEmpty ? (
                    <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
                        <Typography variant="body2">
                            📚 暂无稍后阅读的文章
                        </Typography>
                    </Box>
                ) : (
                    <PaperList
                        papers={readLaterPapers}
                        currentPaperId={currentPaperId}
                        onSelectPaper={handleSelectPaper}
                        showJournal={true}
                        showReadLaterBadge={true}
                        showAnalysisBadge={true}
                        dateField="marked_at"
                        dateLabel="添加于"
                    />
                )}
            </Box>
            
            {/* 分页导航 - 始终显示在底部 */}
            {pagination && pagination.total_pages > 1 && (
                <Box sx={{
                    p: 1, 
                    borderTop: 1, 
                    borderColor: 'divider', 
                    display: 'flex', 
                    justifyContent: 'center'
                }}>
                    <Pagination
                        count={pagination.total_pages}
                        page={pagination.page}
                        onChange={handlePageChange}
                        size="small"
                        color="primary"
                        disabled={loadingList}
                    />
                </Box>
            )}
        </Paper>
    );

    const navigationInfo = getNavigationInfo();

    // 如果没有稍后读的论文且不在加载中，显示空状态
    if (isEmpty && !loadingList) {
        return (
            <Box sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                p: 3
            }}>
                <Box sx={{ textAlign: 'center', maxWidth: 600 }}>
                    <Typography variant="h4" sx={{ mb: 2, fontWeight: 600 }}>
                        📚 稍后阅读
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                        管理您想要深度阅读的文章
                    </Typography>

                    <Card sx={{ maxWidth: 400, mx: 'auto', mb: 3 }}>
                        <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Box
                                sx={{
                                    p: 1.5,
                                    borderRadius: 2,
                                    backgroundColor: theme.palette.secondary.light + '20',
                                    color: theme.palette.secondary.main,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}
                            >
                                📚
                            </Box>
                            <Box sx={{ flex: 1 }}>
                                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                                    {readLaterPapers.length}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    待读文章
                                </Typography>
                            </Box>
                        </CardContent>
                    </Card>

                    <Box sx={{ textAlign: 'left', maxWidth: 400, mx: 'auto' }}>
                        <Typography variant="h6" sx={{ mb: 2 }}>功能说明：</Typography>
                        <List dense>
                            {[
                                '📖 在任何文章详情页点击"稍后阅读"按钮',
                                '🗂️ 所有标记的文章会保存在这里',
                                '⏰ 按添加时间排序，最新的在前面',
                                '🔄 可以随时移除不需要的文章',
                                '🌍 支持摘要翻译功能',
                                '🧠 一键创建AI深度分析任务'
                            ].map((feature, index) => (
                                <ListItem key={index} sx={{ py: 0.5 }}>
                                    <ListItemText primary={feature} />
                                </ListItem>
                            ))}
                        </List>
                    </Box>

                    <Box sx={{ 
                        mt: 3, 
                        p: 2, 
                        background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}08 0%, ${theme.palette.info.main}12 100%)`,
                        border: (theme) => `1px solid ${theme.palette.info.light}30`,
                        borderRadius: 2, 
                        maxWidth: 400, 
                        mx: 'auto',
                        boxShadow: (theme) => `0px 2px 8px ${theme.palette.info.main}06`
                    }}>
                        <Typography variant="body2" color="text.secondary">
                            💡 提示：稍后阅读的文章会自动保存在本地，即使刷新页面也不会丢失
                        </Typography>
                    </Box>
                </Box>
            </Box>
        );
    }

    // 移动端：如果选中了论文，显示详情；否则显示论文列表
    if (isMobile) {
        if (currentPaper) {
            // 显示论文详情，带返回按钮
            return (
                <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Paper elevation={0} sx={{
                        p: 1,
                        borderBottom: 1,
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2
                    }}>
                        <IconButton 
                            size="small" 
                            onClick={() => selectPaper(null)}
                        >
                            <ArrowBackIcon />
                        </IconButton>
                        <Typography variant="subtitle1" sx={{ flex: 1 }} noWrap>
                            稍后阅读
                        </Typography>
                        {navigationInfo && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <IconButton 
                                    size="small" 
                                    onClick={() => handleNavigate('prev')}
                                    disabled={!navigationInfo.hasPrev}
                                >
                                    <ArrowBackIcon />
                                </IconButton>
                                <Typography variant="caption" color="text.secondary">
                                    {navigationInfo.current} / {navigationInfo.total}
                                </Typography>
                                <IconButton 
                                    size="small" 
                                    onClick={() => handleNavigate('next')}
                                    disabled={!navigationInfo.hasNext}
                                >
                                    <ArrowForwardIcon />
                                </IconButton>
                            </Box>
                        )}
                    </Paper>
                    <Box sx={{ flex: 1, height: '100%', overflow: 'auto' }}>
                        <PaperDetail />
                    </Box>
                </Box>
            );
        } else {
            // 显示论文列表
            return (
                <Box sx={{ height: '100%' }}>
                    {renderPaperList()}
                </Box>
            );
        }
    }

    // 桌面端：分栏显示
    return (
        <Box sx={{ height: '100%', display: 'flex' }}>
            <Box sx={{ width: 320, minWidth: 320 }}>
                {renderPaperList()}
            </Box>
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ flex: 1, overflowY: 'auto' }}>
                    {currentPaper ? (
                        <PaperDetail />
                    ) : (
                        <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            color: 'text.secondary'
                        }}>
                            <Typography>请选择一篇论文进行阅读</Typography>
                        </Box>
                    )}
                </Box>
                {navigationInfo && (
                    <Paper elevation={0} sx={{
                        p: 1,
                        borderTop: 1,
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 2,
                        height: '45px'
                    }}>
                        <IconButton onClick={() => handleNavigate('prev')}
                                    disabled={!navigationInfo.hasPrev}>
                            <ArrowBackIcon />
                        </IconButton>
                        <Typography variant="body2" color="text.secondary">
                            {navigationInfo.current} / {navigationInfo.total}
                        </Typography>
                        <IconButton onClick={() => handleNavigate('next')}
                                    disabled={!navigationInfo.hasNext}>
                            <ArrowForwardIcon />
                        </IconButton>
                    </Paper>
                )}
            </Box>
        </Box>
    );
}

export default ReadLaterView;