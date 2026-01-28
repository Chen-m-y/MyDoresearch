import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * 通用分页Hook
 * 支持服务器端分页，与DoResearch API的分页格式兼容
 */
export const usePagination = (options = {}) => {
    const {
        // API调用函数，应该返回包含 papers 和 pagination 的对象
        fetchFunction,
        // 每页项目数，默认20
        perPage = 20,
        // 初始页码，默认1
        initialPage = 1,
        // 额外的查询参数
        params = {},
        // 是否在Hook初始化时自动获取数据
        autoFetch = true,
        // 依赖项数组，当这些值改变时重新获取数据
        dependencies = []
    } = options;

    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({
        page: initialPage,
        per_page: perPage,
        total: 0,
        total_pages: 0,
        has_prev: false,
        has_next: false
    });
    
    // 请求去重
    const currentRequestRef = useRef(null);
    const requestIdRef = useRef(0);

    // 获取数据的函数
    const fetchData = useCallback(async (page = pagination.page) => {
        if (!fetchFunction) {
            console.warn('usePagination: fetchFunction is required');
            return;
        }

        // 生成请求ID并取消之前的请求
        const requestId = ++requestIdRef.current;
        currentRequestRef.current = requestId;

        setLoading(true);
        setError(null);

        try {
            const queryParams = {
                page,
                per_page: perPage,
                ...params
            };

            const response = await fetchFunction(queryParams);
            
            // 检查请求是否已被取消
            if (currentRequestRef.current !== requestId) {
                return; // 请求已被取消，忽略结果
            }
            
            if (response && response.papers && response.pagination) {
                // 新的分页格式
                setData(response.papers);
                setPagination(response.pagination);
            } else if (Array.isArray(response)) {
                // 兼容旧格式：直接返回数组
                setData(response);
                setPagination({
                    page: page,
                    per_page: perPage,
                    total: response.length,
                    total_pages: Math.ceil(response.length / perPage),
                    has_prev: page > 1,
                    has_next: page < Math.ceil(response.length / perPage)
                });
            } else if (response && response.data) {
                // 兼容包装格式
                const items = response.data.items || response.data.papers || response.data;
                const totalCount = response.data.total_count || response.data.total || items.length;
                
                setData(items);
                setPagination({
                    page: page,
                    per_page: perPage,
                    total: totalCount,
                    total_pages: Math.ceil(totalCount / perPage),
                    has_prev: page > 1,
                    has_next: page < Math.ceil(totalCount / perPage)
                });
            } else {
                throw new Error('Invalid response format');
            }
        } catch (err) {
            console.error('Pagination fetch error:', err);
            setError(err.message || '获取数据失败');
            setData([]);
            setPagination(prev => ({ ...prev, total: 0, total_pages: 0 }));
        } finally {
            setLoading(false);
        }
    }, [fetchFunction, perPage, params]);

    // 跳转到指定页码
    const goToPage = useCallback((page) => {
        if (page < 1 || page > pagination.total_pages) return;
        fetchData(page);
    }, [fetchData, pagination.total_pages]);

    // 跳转到下一页
    const nextPage = useCallback(() => {
        if (pagination.has_next) {
            goToPage(pagination.page + 1);
        }
    }, [goToPage, pagination.has_next, pagination.page]);

    // 跳转到上一页
    const prevPage = useCallback(() => {
        if (pagination.has_prev) {
            goToPage(pagination.page - 1);
        }
    }, [goToPage, pagination.has_prev, pagination.page]);

    // 跳转到第一页
    const firstPage = useCallback(() => {
        goToPage(1);
    }, [goToPage]);

    // 跳转到最后一页
    const lastPage = useCallback(() => {
        goToPage(pagination.total_pages);
    }, [goToPage, pagination.total_pages]);

    // 刷新当前页
    const refresh = useCallback(async () => {
        if (!fetchFunction) return;
        
        // 生成请求ID并取消之前的请求
        const requestId = ++requestIdRef.current;
        currentRequestRef.current = requestId;
        
        setLoading(true);
        setError(null);

        try {
            const queryParams = {
                page: pagination.page,
                per_page: perPage,
                ...params
            };

            const response = await fetchFunction(queryParams);
            
            // 检查请求是否已被取消
            if (currentRequestRef.current !== requestId) {
                return; // 请求已被取消，忽略结果
            }
            
            if (response && response.papers && response.pagination) {
                // 新的分页格式
                setData(response.papers);
                setPagination(response.pagination);
            } else if (Array.isArray(response)) {
                // 兼容旧格式：直接返回数组
                setData(response);
                setPagination({
                    page: pagination.page,
                    per_page: perPage,
                    total: response.length,
                    total_pages: Math.ceil(response.length / perPage),
                    has_prev: pagination.page > 1,
                    has_next: pagination.page < Math.ceil(response.length / perPage)
                });
            } else if (response && response.data) {
                // 兼容包装格式
                const items = response.data.items || response.data.papers || response.data;
                const totalCount = response.data.total_count || response.data.total || items.length;
                
                setData(items);
                setPagination({
                    page: pagination.page,
                    per_page: perPage,
                    total: totalCount,
                    total_pages: Math.ceil(totalCount / perPage),
                    has_prev: pagination.page > 1,
                    has_next: pagination.page < Math.ceil(totalCount / perPage)
                });
            } else {
                throw new Error('Invalid response format');
            }
        } catch (err) {
            console.error('Pagination refresh error:', err);
            setError(err.message || '刷新数据失败');
        } finally {
            setLoading(false);
        }
    }, [fetchFunction, pagination.page, perPage, params]);

    // 重置到第一页
    const reset = useCallback(() => {
        fetchData(1);
    }, [fetchData]);

    // 当依赖项改变时重新获取数据
    useEffect(() => {
        if (autoFetch) {
            fetchData(1);
        }
    }, dependencies); // 只依赖于用户传入的依赖项

    // 返回状态和操作函数
    return {
        // 数据状态
        data,
        loading,
        error,
        pagination,
        
        // 操作函数
        goToPage,
        nextPage,
        prevPage,
        firstPage,
        lastPage,
        refresh,
        reset,
        
        // 便捷属性
        isEmpty: !loading && data.length === 0,
        hasData: data.length > 0,
        currentPage: pagination.page,
        totalPages: pagination.total_pages,
        totalItems: pagination.total,
        hasNextPage: pagination.has_next,
        hasPrevPage: pagination.has_prev,
    };
};

export default usePagination;