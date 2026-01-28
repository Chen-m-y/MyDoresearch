import React, { useState, useEffect, useContext, useCallback } from 'react';
import {
    Box,
    Paper,
    Typography,
    InputBase,
    IconButton,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    CircularProgress,
    Pagination,
    Divider,
    Stack,
    Chip,
    useTheme,
    useMediaQuery,
    Tabs,
    Tab
} from '@mui/material';
import {
    Search as SearchIcon,
    TrendingUp as TrendingIcon,
    Star as StarIcon
} from '@mui/icons-material';

import { PaperContext } from '../../contexts/PaperContext';
import apiClient from '../../services/apiClient';
import PaperDetail from '../PaperDetail';
import PaperList from '../PaperList';
import { LAYOUT_CONSTANTS } from '../../constants/layout.js';
import { usePagination } from '../../hooks/usePagination.js';

function EnhancedSearchView() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD));
    const { currentPaper, currentPaperId, selectPaper, registerViewRefreshCallback } = useContext(PaperContext);

    const [activeTab, setActiveTab] = useState(0);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchTriggered, setSearchTriggered] = useState(false); // 新增：跟踪是否已经搜索
    const [popularSearches, setPopularSearches] = useState([]);

    // 使用服务器端分页进行搜索
    const searchWithPagination = useCallback((params) => {
        if (!searchQuery.trim()) {
            return Promise.resolve({ papers: [], pagination: { page: 1, per_page: 15, total: 0, total_pages: 0, has_prev: false, has_next: false } });
        }
        
        const searchParams = {
            q: searchQuery,
            fields: ['title', 'abstract'],
            order_by: 'relevance',
            ...params
        };
        
        return apiClient.searchPapers(searchParams);
    }, [searchQuery]);

    const {
        data: results,
        loading,
        pagination,
        goToPage,
        refresh,
        isEmpty
    } = usePagination({
        fetchFunction: searchWithPagination,
        perPage: 15,
        autoFetch: false, // 手动控制搜索时机
        dependencies: [searchQuery]
    });

    // 获取热门搜索
    useEffect(() => {
        const fetchPopularSearches = async () => {
            try {
                const popular = await apiClient.getPopularSearches();
                setPopularSearches(popular || []);
            } catch (error) {
                console.error('Failed to fetch popular searches:', error);
                // 设置一些默认的热门搜索
                setPopularSearches([
                    'machine learning',
                    'deep learning',
                    'artificial intelligence',
                    'neural networks',
                    'computer vision'
                ]);
            }
        };

        fetchPopularSearches();
    }, []);

    const handleSearch = async (query = searchQuery) => {
        if (!query.trim()) return;
        
        setSearchQuery(query);
        setSearchTriggered(true);
        setActiveTab(0); // 切换到搜索结果标签
        
        // 触发新的搜索
        setTimeout(() => {
            refresh();
        }, 100);
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            handleSearch();
        }
    };

    const handlePageChange = (event, value) => {
        goToPage(value);
    };

    const handleTabChange = (event, newValue) => {
        setActiveTab(newValue);
    };


    const handlePopularSearchClick = (query) => {
        setSearchQuery(query);
        handleSearch(query);
    };

    // 清理工作：当离开搜索视图时，清空当前选择的论文
    useEffect(() => {
        return () => {
            selectPaper(null);
        };
    }, []);

    // 注册视图刷新回调
    useEffect(() => {
        const unregister = registerViewRefreshCallback((paperId, oldStatus, newStatus) => {
            // 搜索视图也需要刷新，因为状态变更可能影响搜索结果的显示
            refresh();
        });

        return unregister; // 组件卸载时注销回调
    }, [registerViewRefreshCallback, refresh]);

    const renderSearchContent = () => (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* 搜索输入框 */}
            <Box sx={{ height: '76px', p: 2.5, bgcolor: 'grey.50', borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
                <Paper
                    component="form"
                    onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
                    elevation={0}
                    sx={{
                        p: 1,
                        display: 'flex',
                        alignItems: 'center',
                        width: '100%',
                        height: '44px',
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
                        '&:hover': {
                            background: 'linear-gradient(135deg, #f1f3f4 0%, #e3e6ea 100%)',
                            borderColor: 'primary.main',
                        },
                        '&:focus-within': {
                            background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
                            borderColor: 'primary.main',
                            boxShadow: (theme) => `0px 0px 0px 2px ${theme.palette.primary.main}20`
                        },
                        transition: 'all 0.2s ease'
                    }}
                >
                    <InputBase
                        sx={{ 
                            ml: 1.5, 
                            flex: 1,
                            '& input': {
                                fontSize: '0.95rem',
                                '&::placeholder': {
                                    color: 'text.secondary',
                                    opacity: 0.7
                                }
                            }
                        }}
                        placeholder="搜索论文标题、摘要..."
                        inputProps={{ 'aria-label': '搜索论文' }}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={handleKeyPress}
                    />
                    <IconButton
                        type="submit"
                        size="small"
                        sx={{ 
                            p: 1,
                            mr: 0.5,
                            background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                            border: '1px solid rgba(25, 118, 210, 0.2)',
                            color: '#1976d2',
                            '&:hover': {
                                background: 'linear-gradient(135deg, #bbdefb 0%, #90caf9 100%)',
                                borderColor: 'rgba(25, 118, 210, 0.3)',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(25, 118, 210, 0.2)',
                            },
                            '&:disabled': {
                                background: 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)',
                                borderColor: 'rgba(0, 0, 0, 0.1)',
                                color: 'text.disabled'
                            },
                            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                        }}
                        aria-label="search"
                        onClick={() => handleSearch()}
                        disabled={loading}
                    >
                        {loading ? <CircularProgress size={16} color="inherit" /> : <SearchIcon fontSize="small" />}
                    </IconButton>
                </Paper>
            </Box>

            {/* 标签页 */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
                    <Tab label="搜索结果" />
                    <Tab label="热门搜索" />
                </Tabs>
            </Box>

            {/* 标签页内容 */}
            <Box sx={{ flex: 1, overflow: 'auto' }}>
                {activeTab === 0 && (
                    <>
                        {loading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                                <CircularProgress />
                            </Box>
                        ) : results.length > 0 ? (
                            <PaperList
                                papers={results.map(paper => ({
                                    ...paper,
                                    paper_id: paper.id, // 映射字段名
                                    published_date: paper.published_date
                                }))}
                                currentPaperId={currentPaperId}
                                onSelectPaper={selectPaper}
                                showJournal={true}
                                showAnalysisBadge={false}
                                showReadLaterBadge={false}
                                dateField="published_date"
                                dateLabel="发布日期"
                            />
                        ) : searchTriggered ? (
                            <Box sx={{ textAlign: 'center', p: 4 }}>
                                <Typography variant="body1" color="text.secondary">
                                    未找到相关论文
                                </Typography>
                            </Box>
                        ) : (
                            <Box sx={{ textAlign: 'center', p: 4 }}>
                                <Typography variant="body1" color="text.secondary">
                                    输入关键词开始搜索
                                </Typography>
                            </Box>
                        )}
                    </>
                )}

                {activeTab === 1 && (
                    <Box sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            热门搜索
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                            {popularSearches.map((query, index) => (
                                <Chip
                                    key={index}
                                    label={query}
                                    onClick={() => handlePopularSearchClick(query)}
                                    icon={<TrendingIcon />}
                                    sx={{ 
                                        mb: 1,
                                        background: (theme) => `linear-gradient(135deg, ${theme.palette.warning.main}08 0%, ${theme.palette.warning.main}15 100%)`,
                                        color: (theme) => theme.palette.warning.main,
                                        borderColor: (theme) => `${theme.palette.warning.main}30`,
                                        '&:hover': {
                                            background: (theme) => `linear-gradient(135deg, ${theme.palette.warning.main}15 0%, ${theme.palette.warning.main}25 100%)`,
                                            transform: 'translateY(-1px)',
                                            boxShadow: (theme) => `0px 4px 8px ${theme.palette.warning.main}15`
                                        },
                                        '&:active': {
                                            transform: 'translateY(0px)'
                                        },
                                        transition: 'all 0.2s ease'
                                    }}
                                />
                            ))}
                        </Stack>
                    </Box>
                )}
            </Box>
            
            {/* 分页导航 - 固定在底部 */}
            {activeTab === 0 && pagination && pagination.total_pages > 1 && (
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
                        disabled={loading}
                    />
                </Box>
            )}
        </Box>
    );

    if (isMobile) {
        // 移动端：全屏显示搜索内容或论文详情
        return (
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                {currentPaper ? (
                    <Box sx={{ flex: 1, overflowY: 'auto' }}>
                        <PaperDetail />
                    </Box>
                ) : (
                    renderSearchContent()
                )}
            </Box>
        );
    }

    // 桌面端：分栏显示
    return (
        <Box sx={{ height: '100%', display: 'flex' }}>
            {/* 左侧：搜索内容 */}
            <Paper
                elevation={0}
                sx={{
                    width: 320,
                    minWidth: 320,
                    height: '100%',
                    borderRight: `1px solid`,
                    borderColor: 'divider',
                    borderRadius: 0,
                }}
            >
                {renderSearchContent()}
            </Paper>

            {/* 右侧：论文详情 */}
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
                            <Typography variant="h6">
                                选择一篇论文查看详情
                            </Typography>
                        </Box>
                    )}
                </Box>
            </Box>
        </Box>
    );
}

export default EnhancedSearchView;