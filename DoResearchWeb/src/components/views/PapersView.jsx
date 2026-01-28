import React, {useState, useMemo, useContext, useEffect, useCallback, useRef} from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    Chip,
    CircularProgress,
    useMediaQuery,
    useTheme,
    IconButton,
    Divider,
    Stack,
    Pagination
} from '@mui/material';
import {
    ArrowBack as ArrowBackIcon,
    ArrowForward as ArrowForwardIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import { Slide } from '@mui/material';

import {useParams, useNavigate} from 'react-router-dom';
import {PaperContext} from '../../contexts/PaperContext';
import PaperDetail from '../PaperDetail.jsx';
import PaperList from '../PaperList.jsx';
import { LAYOUT_CONSTANTS } from '../../constants/layout.js';
import { usePagination } from '../../hooks/usePagination.js';
import subscriptionClient from '../../services/subscriptionClient.jsx';

const initialFilterOptions = [
    {value: 'all', label: '全部'},
    {value: 'read', label: '已读'},
    {value: 'unread', label: '未读'},
];

function PapersView() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD));
    const {paperId, subscriptionId} = useParams();
    const navigate = useNavigate();

    const {
        currentPaperId,
        currentPaper,
        paperFilter,
        registerViewRefreshCallback, // 新增：注册刷新回调
        selectPaper,
        setFilter,
        setCurrentView
    } = useContext(PaperContext);

    // 创建稳定的 selectPaper 引用，避免不必要的重新调用
    const stableSelectPaper = useCallback((paperId) => {
        selectPaper(paperId);
    }, []); // 空依赖数组，因为我们确保 selectPaper 函数内部使用 ref

    // 使用服务器端分页，包含统计信息
    const fetchPapersWithPagination = useCallback(async (params) => {
        try {
            let result;
            
            // 如果是订阅模式
            if (subscriptionId) {
                // 直接使用 paperFilter，不做任何转换
                result = await subscriptionClient.getSubscriptionPapers(parseInt(subscriptionId), {
                    ...params,
                    status: paperFilter
                });
            } else {
                // 没有订阅ID，返回空结果
                return Promise.resolve({ papers: [], pagination: { page: 1, per_page: 15, total: 0, total_pages: 0, has_prev: false, has_next: false } });
            }
            
            return result;
        } catch (error) {
            console.error('获取论文失败:', error);
            return { papers: [], pagination: { page: 1, per_page: 15, total: 0, total_pages: 0, has_prev: false, has_next: false } };
        }
    }, [paperFilter, subscriptionId]);

    const {
        data: paginationResult,
        loading,
        pagination,
        goToPage,
        refresh,
        reset,
        isEmpty,
        hasData
    } = usePagination({
        fetchFunction: fetchPapersWithPagination,
        perPage: 15,
        autoFetch: true,
        dependencies: [subscriptionId] // 只依赖订阅ID，筛选变化时手动刷新
    });

    // 当页面或筛选条件变化时，清理本地更新
    useEffect(() => {
        setLocalPaperUpdates(new Map());
    }, [subscriptionId, paperFilter, pagination.page]);

    // 自定义加载状态，用于控制分页组件的禁用
    const [isPaginationDisabled, setIsPaginationDisabled] = useState(false);

    // 监听原始loading状态，但在筛选变化时不禁用分页
    const prevFilterChangeRef = useRef(false);
    useEffect(() => {
        if (prevFilterChangeRef.current) {
            // 如果是筛选变化导致的loading，不禁用分页
            prevFilterChangeRef.current = false;
            setIsPaginationDisabled(false);
        } else {
            // 正常的loading，禁用分页
            setIsPaginationDisabled(loading);
        }
    }, [loading]);

    // 监听筛选条件变化，立即调用reset
    const prevFilterRef = useRef(paperFilter);
    useEffect(() => {
        if (subscriptionId && prevFilterRef.current !== paperFilter) {
            prevFilterRef.current = paperFilter;
            prevFilterChangeRef.current = true; // 标记这是筛选变化
            reset();
        }
    }, [paperFilter, subscriptionId, reset]);

    // 从分页结果中提取论文列表和统计信息
    const rawPapers = paginationResult?.papers || paginationResult || [];
    const apiStats = paginationResult?.stats || {};

    // 本地更新论文状态，避免重新请求API
    const [localPaperUpdates, setLocalPaperUpdates] = useState(new Map());

    // 处理后的论文列表，包含本地更新
    const papers = useMemo(() => {
        if (!rawPapers || !Array.isArray(rawPapers)) return [];
        
        // 应用本地状态更新
        return rawPapers.map(paper => {
            const localUpdate = localPaperUpdates.get(paper.id);
            return localUpdate ? { ...paper, ...localUpdate } : paper;
        });
    }, [rawPapers, localPaperUpdates]);

    // 订阅模式下的订阅信息
    const [currentSubscription, setCurrentSubscription] = useState(null);
    
    // 当subscriptionId变化时，获取订阅信息
    useEffect(() => {
        if (subscriptionId) {
            subscriptionClient.getSubscription(parseInt(subscriptionId))
                .then(subscription => {
                    setCurrentSubscription(subscription);
                })
                .catch(error => {
                    console.error('获取订阅信息失败:', error);
                    setCurrentSubscription(null);
                });
        } else {
            setCurrentSubscription(null);
        }
    }, [subscriptionId]);
    
    // 状态统计 - 优先使用API返回的统计，必要时补充获取
    const [statusCounts, setStatusCounts] = useState({ all: 0, read: 0, unread: 0 });
    const [hasInitializedStats, setHasInitializedStats] = useState(false);
    
    // 跟踪即将移除的论文（用于动画效果）
    const [fadingOutPapers, setFadingOutPapers] = useState(new Set());
    
    // 防止重复请求的ref
    const statsRequestRef = useRef(null);

    // 更新状态统计 - 使用批量统计API
    const updateStatusCounts = useCallback(async (forceRefresh = false) => {
        if (!subscriptionId) return;
        
        // 防止重复请求，但允许强制刷新时覆盖
        const requestKey = `${subscriptionId}-${Date.now()}`;
        if (statsRequestRef.current && !forceRefresh) {
            return; // 如果有正在进行的请求且不是强制刷新，直接返回
        }
        
        // 强制刷新时，取消之前的请求
        if (forceRefresh && statsRequestRef.current) {
            statsRequestRef.current = null;
        }
        
        statsRequestRef.current = requestKey;
        
        try {
            // 如果不是强制刷新，优先使用API返回的统计信息
            if (!forceRefresh && apiStats && Object.keys(apiStats).length > 0) {
                setStatusCounts({
                    all: apiStats.all || apiStats.total || 0,
                    read: apiStats.read || 0,
                    unread: apiStats.unread || 0
                });
                return;
            }
            
            // 使用批量统计API获取准确数据
            const statsData = await subscriptionClient.getBatchSubscriptionStats([parseInt(subscriptionId)]);
            
            // 检查是否还是当前的请求
            if (statsRequestRef.current !== requestKey) return;
            
            const subscriptionStats = statsData[subscriptionId];
            if (subscriptionStats) {
                setStatusCounts({
                    all: subscriptionStats.total_papers || 0,
                    read: subscriptionStats.status_counts?.read || 0,
                    unread: subscriptionStats.status_counts?.unread || 0
                });
            } else {
                // 降级：使用当前分页信息
                setStatusCounts(prev => ({
                    ...prev,
                    all: 0 // 如果没有统计数据，设为0
                }));
            }
            
        } catch (error) {
            console.error('获取统计数据失败:', error);
            // 最后的降级：设置为0
            if (statsRequestRef.current === requestKey) {
                setStatusCounts(prev => ({
                    ...prev,
                    all: 0
                }));
            }
        } finally {
            if (statsRequestRef.current === requestKey) {
                statsRequestRef.current = null;
            }
        }
    }, [subscriptionId, apiStats]);

    const filterOptionsWithCounts = initialFilterOptions.map(opt => ({
        ...opt,
        label: `${opt.label} (${statusCounts[opt.value] || 0})`
    }));

    // 论文导航逻辑 - 基于当前页面的论文列表
    const getNavigationInfo = () => {
        if (!currentPaperId || papers.length === 0) return null;
        const currentIndex = papers.findIndex(p => p.id === currentPaperId);
        if (currentIndex === -1) return null;
        return {
            hasPrev: currentIndex > 0 || pagination.has_prev,
            hasNext: currentIndex < papers.length - 1 || pagination.has_next,
            current: ((pagination.page - 1) * pagination.per_page) + currentIndex + 1,
            total: pagination.total
        };
    };

    const navigationInfo = getNavigationInfo();

    const handlePageChange = (event, value) => {
        goToPage(value);
    };

    // 当API返回统计信息时，优先使用API统计
    useEffect(() => {
        if (apiStats && Object.keys(apiStats).length > 0) {
            setStatusCounts({
                all: apiStats.all || apiStats.total || 0,
                read: apiStats.read || 0,
                unread: apiStats.unread || 0
            });
        }
    }, [apiStats]);

    // 当订阅切换时，获取统计信息
    useEffect(() => {        
        if (subscriptionId && !loading) {
            // 重置初始化状态，允许重新获取统计
            setHasInitializedStats(false);
            // 如果没有API统计信息，获取统计数据
            if (!apiStats || Object.keys(apiStats).length === 0) {
                updateStatusCounts(true);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [subscriptionId]);

    // 只在组件挂载或订阅切换时获取统计信息
    useEffect(() => {
        if (subscriptionId && !loading && !hasInitializedStats) {
            if (!apiStats || Object.keys(apiStats).length === 0) {
                updateStatusCounts(true).then(() => {
                    setHasInitializedStats(true);
                });
            } else {
                setHasInitializedStats(true);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [subscriptionId, loading, hasInitializedStats]);

    // 注册视图刷新回调
    useEffect(() => {
        const unregister = registerViewRefreshCallback((paperId, oldStatus, newStatus, statsUpdated = false) => {
            // 检查论文状态变更后是否还符合当前筛选条件
            const newStatusMatchesFilter = paperFilter === 'all' || newStatus === paperFilter;
            const oldStatusMatchedFilter = paperFilter === 'all' || oldStatus === paperFilter;
            
            // 如果论文状态变更后不再符合筛选条件，添加淡出效果
            if (oldStatusMatchedFilter && !newStatusMatchesFilter) {
                // 先添加到淡出列表
                setFadingOutPapers(prev => new Set(prev.add(paperId)));
                
                // 延迟刷新列表，让用户看到淡出动画
                setTimeout(() => {
                    // 论文不再符合筛选条件，需要刷新整个列表移除该论文
                    refresh(); // 这种情况下必须刷新，因为论文需要从列表中移除
                    // 强制刷新统计数据，因为文章状态改变了
                    updateStatusCounts(true);
                    // 清理本地更新和淡出状态
                    setLocalPaperUpdates(prev => {
                        const newMap = new Map(prev);
                        newMap.delete(paperId);
                        return newMap;
                    });
                    setFadingOutPapers(prev => {
                        const newSet = new Set(prev);
                        newSet.delete(paperId);
                        return newSet;
                    });
                }, 300); // 与CSS动画时间匹配
            } else {
                // 论文状态变更但仍符合筛选条件，立即更新本地状态
                setLocalPaperUpdates(prev => {
                    const newMap = new Map(prev);
                    newMap.set(paperId, { status: newStatus });
                    return newMap;
                });
                
                // 刷新统计数据
                updateStatusCounts(true);
            }
        });

        return unregister; // 组件卸载时注销回调
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [registerViewRefreshCallback, paperFilter, refresh]);

    useEffect(() => {
        setCurrentView('papers');
    }, [setCurrentView]);

    useEffect(() => {
        // 当URL中的 paperId 与 context 中的不一致时，更新 context
        const numericPaperId = paperId ? parseInt(paperId) : null;
        if (numericPaperId !== currentPaperId) {
            stableSelectPaper(numericPaperId);
        }
    }, [paperId, currentPaperId, stableSelectPaper]);

    const handleFilterChange = (newFilter) => {
        // 根据当前模式跳转到相应的URL
        if (subscriptionId) {
            navigate(`/subscription/${subscriptionId}/papers`, { replace: true });
            // 手动更新筛选状态，useEffect 会自动处理数据刷新
            setFilter(newFilter);
        } else {
            // 订阅模式不支持直接筛选跳转
            console.warn('订阅模式不支持筛选跳转');
        }
    };

    const handleSelectPaper = (selectedPaperId) => {
        // 只支持订阅模式
        if (subscriptionId) {
            navigate(`/subscription/${subscriptionId}/papers/paper/${selectedPaperId}`);
        }
    };

    const localNavigatePaper = async (direction) => {
        if (!currentPaperId || papers.length === 0) return;
        const currentIndex = papers.findIndex(p => p.id === currentPaperId);
        if (currentIndex === -1) return;

        let targetIndex;
        let targetPaperId;

        if (direction === 'prev') {
            targetIndex = currentIndex - 1;
            if (targetIndex < 0 && pagination.has_prev) {
                // 需要跳转到上一页的最后一项
                await goToPage(pagination.page - 1);
                // 页面数据更新后，选择新页面的最后一项
                setTimeout(() => {
                    if (papers.length > 0) {
                        const lastPaper = papers[papers.length - 1];
                        navigate(`/subscription/${subscriptionId}/papers/paper/${lastPaper.id}`, { replace: true });
                    }
                }, 100);
                return;
            }
        } else {
            targetIndex = currentIndex + 1;
            if (targetIndex >= papers.length && pagination.has_next) {
                // 需要跳转到下一页的第一项
                await goToPage(pagination.page + 1);
                // 页面数据更新后，选择新页面的第一项
                setTimeout(() => {
                    if (papers.length > 0) {
                        const firstPaper = papers[0];
                        navigate(`/subscription/${subscriptionId}/papers/paper/${firstPaper.id}`, { replace: true });
                    }
                }, 100);
                return;
            }
        }

        if (targetIndex >= 0 && targetIndex < papers.length) {
            targetPaperId = papers[targetIndex].id;
            navigate(`/subscription/${subscriptionId}/papers/paper/${targetPaperId}`, { replace: true });
        }
    };

    const handleUpdateFeed = async () => {
        if (subscriptionId) {
            // 订阅模式：手动同步订阅
            try {
                await subscriptionClient.syncSubscription(parseInt(subscriptionId));
                // 同步后刷新当前页面和状态统计
                refresh();
                updateStatusCounts(true);
            } catch (error) {
                console.error('同步订阅失败:', error);
            }
        }
    };

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
            <Box sx={{height: '76px', p: 2.5, bgcolor: 'grey.50', borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center'}}>
                {/* 标题行：论文源名称和更新按钮 */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                            {subscriptionId ? (currentSubscription?.name || '智能订阅') : '选择一个订阅'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.2, mt: 0.5 }}>
                            {pagination.total} 篇论文 {pagination.total_pages > 1 && `(第 ${pagination.page}/${pagination.total_pages} 页)`}
                        </Typography>
                    </Box>
                    {subscriptionId && (
                        <Button 
                            variant="outlined" 
                            size="small" 
                            startIcon={<RefreshIcon sx={{ fontSize: '0.9rem' }}/>} 
                            onClick={handleUpdateFeed}
                            disabled={loading} 
                            sx={(theme) => ({
                                py: 0.5,
                                px: 1.5,
                                fontSize: '0.75rem',
                                minWidth: 'auto',
                                flexShrink: 0,
                                ml: 1,
                                background: `linear-gradient(135deg, ${theme.palette.success.main}15 0%, ${theme.palette.success.main}25 100%)`,
                                border: `1px solid ${theme.palette.success.main}40`,
                                color: theme.palette.success.main,
                                position: 'relative',
                                overflow: 'hidden',
                                '&::before': {
                                    content: '""',
                                    position: 'absolute',
                                    top: 0,
                                    right: 0,
                                    width: '25px',
                                    height: '25px',
                                    background: `radial-gradient(circle, ${theme.palette.success.main}10 0%, transparent 70%)`,
                                    transform: 'translate(8px, -8px)',
                                },
                                '& .MuiButton-startIcon': {
                                    position: 'relative',
                                    zIndex: 1,
                                },
                                '&:hover': {
                                    background: `linear-gradient(135deg, ${theme.palette.success.main}20 0%, ${theme.palette.success.main}30 100%)`,
                                    transform: 'translateY(-1px)',
                                    boxShadow: `0px 3px 8px ${theme.palette.success.main}20`,
                                },
                                '&:disabled': {
                                    background: `linear-gradient(135deg, ${theme.palette.grey[300]}15 0%, ${theme.palette.grey[300]}25 100%)`,
                                    border: `1px solid ${theme.palette.grey[300]}40`,
                                    color: theme.palette.grey[500],
                                },
                                transition: 'all 0.2s ease'
                            })}
                        >
                            更新
                        </Button>
                    )}
                </Box>
            </Box>
                
            {/* 筛选标签 */}
            <Box sx={{ 
                py: 1, 
                px: 2,
                borderBottom: 1,
                borderColor: 'divider',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
                <Stack 
                    direction="row" 
                    spacing={0.5} 
                    sx={{
                        flexWrap: 'wrap', 
                        gap: 0.5,
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}
                >
                    {filterOptionsWithCounts.map((option) => (
                        <Chip
                            key={option.value}
                            label={option.label}
                            color={paperFilter === option.value ? 'primary' : 'default'}
                            variant={paperFilter === option.value ? 'filled' : 'outlined'}
                            size="small"
                            onClick={() => handleFilterChange(option.value)}
                            sx={{
                                cursor: 'pointer',
                                height: 24,
                                fontSize: '0.7rem',
                                '& .MuiChip-label': {
                                    px: 1,
                                    py: 0
                                }
                            }}
                        />
                    ))}
                </Stack>
            </Box>

            <Box sx={{flex: 1, overflowY: 'auto'}}>
                {loading && papers.length === 0 ? (
                    <Box sx={{display: 'flex', justifyContent: 'center', p: 3}}><CircularProgress/></Box>
                ) : papers.length === 0 ? (
                    <Box sx={{p: 3, textAlign: 'center', color: 'text.secondary'}}><Typography
                        variant="body2">{subscriptionId ? '暂无论文' : '请选择一个订阅'}</Typography></Box>
                ) : (
                    <PaperList
                        papers={papers}
                        currentPaperId={currentPaperId}
                        onSelectPaper={handleSelectPaper}
                        showJournal={false}
                        showReadLaterBadge={false}
                        showAnalysisBadge={true}
                        dateField="published_date"
                        dateLabel=""
                        loading={false}
                        paperFilter={paperFilter}
                        fadingOutPapers={fadingOutPapers}
                        enableFilterAnimation={true}
                    />
                )}
            </Box>

            {pagination.total_pages > 1 && (
                <Box sx={{p: 1, borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: 'center'}}>
                    <Pagination 
                        count={pagination.total_pages} 
                        page={pagination.page} 
                        onChange={handlePageChange} 
                        size="small"
                        color="primary"
                        disabled={isPaginationDisabled}
                    />
                </Box>
            )}
        </Paper>
    );

    const renderWelcome = () => (
        <Box sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            textAlign: 'center',
            p: 3
        }}>
            <Box>
                <Typography variant="h4" sx={{mb: 2, fontWeight: 600}}>欢迎使用论文阅读器</Typography>
                <Typography variant="body1" color="text.secondary"
                            sx={{mb: 3}}>请先添加论文源，然后选择文章进行阅读</Typography>
                <Box sx={{
                    mt: 4, 
                    p: 2, 
                    background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main}08 0%, ${theme.palette.primary.main}12 100%)`,
                    border: (theme) => `1px solid ${theme.palette.primary.light}30`,
                    borderRadius: 2,
                    boxShadow: (theme) => `0px 2px 8px ${theme.palette.primary.main}06`
                }}>
                    <Typography variant="subtitle2" sx={{mb: 1}}>快速开始：</Typography>
                    <Typography variant="body2" color="text.secondary">测试源名称:
                        测试论文库<br/>API地址: <code>/api/test/papers</code></Typography>
                </Box>
            </Box>
        </Box>
    );

    if (!subscriptionId) {
        return renderWelcome();
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
                            onClick={() => {
                                navigate(`/subscription/${subscriptionId}/papers`);
                            }}
                        >
                            <ArrowBackIcon />
                        </IconButton>
                        <Typography variant="subtitle1" sx={{ flex: 1 }} noWrap>
                            {subscriptionId ? (currentSubscription?.name || '智能订阅') : '订阅源'}
                        </Typography>
                        {navigationInfo && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <IconButton 
                                    size="small" 
                                    onClick={() => localNavigatePaper('prev')}
                                    disabled={!navigationInfo.hasPrev}
                                >
                                    <ArrowBackIcon />
                                </IconButton>
                                <Typography variant="caption" color="text.secondary">
                                    {navigationInfo.current} / {navigationInfo.total}
                                </Typography>
                                <IconButton 
                                    size="small" 
                                    onClick={() => localNavigatePaper('next')}
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
                        <IconButton onClick={() => localNavigatePaper('prev')}
                                    disabled={!navigationInfo.hasPrev}>
                            <ArrowBackIcon />
                        </IconButton>
                        <Typography variant="body2" color="text.secondary">
                            {navigationInfo.current} / {navigationInfo.total}
                        </Typography>
                        <IconButton onClick={() => localNavigatePaper('next')}
                                    disabled={!navigationInfo.hasNext}>
                            <ArrowForwardIcon />
                        </IconButton>
                    </Paper>
                )}
            </Box>
        </Box>
    );
}

export default PapersView;