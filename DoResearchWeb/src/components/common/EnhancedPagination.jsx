import React from 'react';
import {
    Box,
    Pagination,
    Typography,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    IconButton,
    Tooltip,
    useTheme,
    useMediaQuery
} from '@mui/material';
import {
    FirstPage as FirstPageIcon,
    LastPage as LastPageIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';

/**
 * 增强的分页组件
 * 提供页码导航、每页数量选择、快速跳转等功能
 */
function EnhancedPagination({
    // 分页数据
    pagination,
    // 页面变化回调
    onPageChange,
    // 每页数量变化回调
    onPerPageChange,
    // 刷新回调
    onRefresh,
    // 是否加载中
    loading = false,
    // 是否显示每页数量选择器
    showPerPageSelector = true,
    // 是否显示统计信息
    showStats = true,
    // 是否显示快速跳转按钮
    showQuickJump = true,
    // 每页数量选项
    perPageOptions = [10, 15, 20, 50, 100],
    // 组件大小
    size = 'small',
    // 自定义样式
    sx = {}
}) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

    // 如果没有分页数据或总页数为1，不显示分页器
    if (!pagination || pagination.total_pages <= 1) {
        return null;
    }

    const handlePageChange = (event, page) => {
        if (onPageChange && !loading) {
            onPageChange(event, page);
        }
    };

    const handlePerPageChange = (event) => {
        if (onPerPageChange && !loading) {
            onPerPageChange(event.target.value);
        }
    };

    const handleFirstPage = () => {
        if (pagination.page > 1 && !loading) {
            onPageChange?.(null, 1);
        }
    };

    const handleLastPage = () => {
        if (pagination.page < pagination.total_pages && !loading) {
            onPageChange?.(null, pagination.total_pages);
        }
    };

    const handleRefresh = () => {
        if (onRefresh && !loading) {
            onRefresh();
        }
    };

    // 计算显示范围
    const startItem = (pagination.page - 1) * pagination.per_page + 1;
    const endItem = Math.min(pagination.page * pagination.per_page, pagination.total);

    return (
        <Box
            sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: isMobile ? 'wrap' : 'nowrap',
                gap: 2,
                p: 1,
                borderTop: 1,
                borderColor: 'divider',
                backgroundColor: 'background.paper',
                ...sx
            }}
        >
            {/* 左侧：统计信息 */}
            {showStats && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                    <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                            fontSize: '0.75rem',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                        }}
                    >
                        显示 {startItem}-{endItem} / 共 {pagination.total} 条
                    </Typography>
                    
                    {/* 每页数量选择器 */}
                    {showPerPageSelector && !isMobile && (
                        <FormControl size="small" sx={{ minWidth: 80 }}>
                            <Select
                                value={pagination.per_page}
                                onChange={handlePerPageChange}
                                disabled={loading}
                                sx={{
                                    '& .MuiSelect-select': {
                                        fontSize: '0.75rem',
                                        py: 0.5
                                    }
                                }}
                            >
                                {perPageOptions.map((option) => (
                                    <MenuItem key={option} value={option} sx={{ fontSize: '0.75rem' }}>
                                        {option} 条/页
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    )}
                </Box>
            )}

            {/* 中间：分页器 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {/* 快速跳转按钮 */}
                {showQuickJump && !isMobile && (
                    <>
                        <Tooltip title="首页">
                            <IconButton
                                size="small"
                                onClick={handleFirstPage}
                                disabled={loading || pagination.page === 1}
                                sx={{ p: 0.5 }}
                            >
                                <FirstPageIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    </>
                )}

                <Pagination
                    count={pagination.total_pages}
                    page={pagination.page}
                    onChange={handlePageChange}
                    size={size}
                    color="primary"
                    disabled={loading}
                    showFirstButton={!isMobile && !showQuickJump}
                    showLastButton={!isMobile && !showQuickJump}
                    siblingCount={isMobile ? 0 : 1}
                    boundaryCount={isMobile ? 1 : 2}
                    sx={{
                        '& .MuiPaginationItem-root': {
                            fontSize: isMobile ? '0.7rem' : '0.8rem',
                            minWidth: isMobile ? '28px' : '32px',
                            height: isMobile ? '28px' : '32px'
                        }
                    }}
                />

                {/* 快速跳转按钮 */}
                {showQuickJump && !isMobile && (
                    <>
                        <Tooltip title="末页">
                            <IconButton
                                size="small"
                                onClick={handleLastPage}
                                disabled={loading || pagination.page === pagination.total_pages}
                                sx={{ p: 0.5 }}
                            >
                                <LastPageIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    </>
                )}
            </Box>

            {/* 右侧：刷新按钮 */}
            {onRefresh && (
                <Tooltip title="刷新">
                    <IconButton
                        size="small"
                        onClick={handleRefresh}
                        disabled={loading}
                        sx={{ 
                            p: 0.5,
                            color: 'primary.main',
                            '&:hover': {
                                backgroundColor: 'primary.main',
                                color: 'primary.contrastText'
                            }
                        }}
                    >
                        <RefreshIcon 
                            fontSize="small" 
                            sx={{
                                animation: loading ? 'spin 1s linear infinite' : 'none',
                                '@keyframes spin': {
                                    '0%': {
                                        transform: 'rotate(0deg)',
                                    },
                                    '100%': {
                                        transform: 'rotate(360deg)',
                                    },
                                }
                            }}
                        />
                    </IconButton>
                </Tooltip>
            )}

            {/* 移动端每页数量选择器 */}
            {showPerPageSelector && isMobile && (
                <FormControl size="small" sx={{ width: '100%', mt: 1 }}>
                    <InputLabel sx={{ fontSize: '0.75rem' }}>每页条数</InputLabel>
                    <Select
                        value={pagination.per_page}
                        onChange={handlePerPageChange}
                        disabled={loading}
                        label="每页条数"
                        sx={{
                            '& .MuiSelect-select': {
                                fontSize: '0.75rem'
                            }
                        }}
                    >
                        {perPageOptions.map((option) => (
                            <MenuItem key={option} value={option} sx={{ fontSize: '0.75rem' }}>
                                {option} 条/页
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            )}
        </Box>
    );
}

export default EnhancedPagination;