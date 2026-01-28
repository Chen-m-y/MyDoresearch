import React, {createContext, useState, useEffect, useCallback, useContext, useRef} from 'react';
import apiClient from '../services/apiClient.jsx';
import {DataContext} from "./DataContext.jsx";
import {AuthContext} from "./AuthContext.jsx";
import { useNotification } from '../components/NotificationProvider.jsx';

export const PaperContext = createContext();


export function PaperProvider({ children }) {
    const { addToReadLater, removeFromReadLater } = useContext(DataContext);
    const { showNotification } = useNotification();

    // 视图状态
    const [currentView, setCurrentView] = useState('stats');

    // 移除旧的论文源相关状态，已由新订阅系统替代

    // 论文相关状态 - 移除papers数组，由各视图自己管理
    const [currentPaperId, setCurrentPaperId] = useState(null);
    const [currentPaper, setCurrentPaper] = useState(null);
    const [paperFilter, setPaperFilter] = useState('all');
    
    // 记录上一个访问的论文，用于自动标记已读
    // const [previousPaper, setPreviousPaper] = useState(null);

    // UI状态
    const [loading, setLoading] = useState(false);
    const [paperLoading, setPaperLoading] = useState(false);

    // 添加视图刷新回调注册机制
    const viewRefreshCallbacks = useRef([]);
    const currentPaperRef = useRef(currentPaper);
    
    // 记录最近手动状态变更的论文，防止自动标记冲突
    const recentManualStatusChanges = useRef(new Set());
    
    // 保持 ref 与 state 同步
    useEffect(() => {
        currentPaperRef.current = currentPaper;
    }, [currentPaper]);

    // 注册视图刷新回调
    const registerViewRefreshCallback = useCallback((callback) => {
        viewRefreshCallbacks.current.push(callback);
        return () => {
            viewRefreshCallbacks.current = viewRefreshCallbacks.current.filter(cb => cb !== callback);
        };
    }, []);

    // 通知所有视图刷新
    const notifyViewsRefresh = useCallback((paperId, oldStatus, newStatus, statsUpdated = false) => {
        viewRefreshCallbacks.current.forEach(callback => {
            try {
                callback(paperId, oldStatus, newStatus, statsUpdated);
            } catch (error) {
                console.error('View refresh callback error:', error);
            }
        });
    }, []);

    // --- 简化版 togglePaperStatus，立即通知视图 ---
    const togglePaperStatus = useCallback(async (paperId, currentStatus, notify = false) => {
        const newStatus = currentStatus === 'read' ? 'unread' : 'read';
        
        // 记录这是一次手动状态变更
        recentManualStatusChanges.current.add(parseInt(paperId));
        
        // 5秒后移除记录，防止长期阻止自动标记
        setTimeout(() => {
            recentManualStatusChanges.current.delete(parseInt(paperId));
        }, 5000);
        
        // 立即更新当前论文状态（乐观更新）
        setCurrentPaper(prevCurrentPaper => {
            if (prevCurrentPaper && prevCurrentPaper.id === parseInt(paperId)) {
                return { ...prevCurrentPaper, status: newStatus };
            }
            return prevCurrentPaper;
        });

        // 后台更新服务器状态，请求返回统计变化
        try {
            const result = await apiClient.updatePaperStatus(paperId, newStatus, { returnStats: true });
            if (result.success) {
                // API成功后通知视图刷新，确保列表数据与服务器同步
                notifyViewsRefresh(parseInt(paperId), currentStatus, newStatus, true);
                // 移除弹出提示
                // if (notify) showNotification(`已标记为${newStatus === 'read' ? '已读' : '未读'}`, 'success');
                
                // 统计更新已由新订阅系统处理，移除旧的feed统计代码
            } else {
                // API失败时回滚并重新通知
                setCurrentPaper(prevCurrentPaper => {
                    if (prevCurrentPaper && prevCurrentPaper.id === parseInt(paperId)) {
                        return { ...prevCurrentPaper, status: currentStatus };
                    }
                    return prevCurrentPaper;
                });
                notifyViewsRefresh(parseInt(paperId), newStatus, currentStatus, false);
                if (notify) showNotification('更新状态失败', 'error');
            }
        } catch (error) {
            console.error('Failed to update paper status:', error);
            // 回滚状态并通知
            setCurrentPaper(prevCurrentPaper => {
                if (prevCurrentPaper && prevCurrentPaper.id === parseInt(paperId)) {
                    return { ...prevCurrentPaper, status: currentStatus };
                }
                return prevCurrentPaper;
            });
            notifyViewsRefresh(parseInt(paperId), newStatus, currentStatus);
            if (notify) showNotification('更新状态失败，请稍后重试', 'error');
        }
    }, [showNotification, notifyViewsRefresh]);


    // 移除旧的论文源管理方法，已由新订阅系统替代


    // --- 优化版 selectPaper，使用新的expand API，支持自动标记已读 ---
    const selectPaper = useCallback(async (paperId) => {
        // 获取当前状态
        let currentId;
        setCurrentPaperId(prevId => {
            currentId = prevId;
            return prevId; // 暂时不更新，先获取当前值
        });

        if (paperId === currentId) return;

        if (!paperId) {
            setCurrentPaperId(paperId);
            setCurrentPaper(null);
            // setPreviousPaper(null);
            return;
        }

        // 立即设置加载状态和新的论文ID，优先显示新论文
        setPaperLoading(true);
        setCurrentPaperId(paperId);

        try {
            // 使用新的expand API一次性获取所有信息
            const paperData = await apiClient.getPaperDetail(paperId, {
                expand: ['read_later', 'analysis']
            });

            const fullPaperData = {
                ...paperData,
                isLoadingDetails: false,
                // 确保有status字段
                status: paperData.status || 'unread'
            };

            // 使用批量状态更新减少重新渲染
            React.startTransition(() => {
                setCurrentPaper(fullPaperData);
                
                // 更新previousPaper为当前论文的基本信息（用于下次切换时的自动标记）
                // setPreviousPaper({
                //     id: fullPaperData.id,
                //     status: fullPaperData.status,
                //     title: fullPaperData.title
                // });
            });

            // 新论文加载完成后，在后台标记上一个论文为已读
            if (currentId && currentPaperRef.current && currentPaperRef.current.status === 'unread') {
                // 检查是否是最近手动变更状态的论文，如果是则跳过自动标记
                if (!recentManualStatusChanges.current.has(currentId)) {
                    // 使用 setTimeout 确保新论文显示后再处理旧论文标记
                    setTimeout(async () => {
                        try {
                            // 再次检查，确保在延迟期间没有被手动变更
                            if (!recentManualStatusChanges.current.has(currentId)) {
                                await togglePaperStatus(currentId, 'unread', false); // 不显示通知
                            }
                        } catch (error) {
                            console.error('Failed to mark previous paper as read:', error);
                        }
                    }, 100); // 延迟100ms，确保新论文UI已经显示
                }
            }

        } catch (error) {
            console.error('Failed to fetch paper details:', error);
            showNotification('加载论文详情失败', 'error');
            const errorPaper = { 
                id: paperId,
                error: '加载失败', 
                status: 'unread',
                isLoadingDetails: false
            };
            // 使用批量状态更新减少重新渲染
            React.startTransition(() => {
                setCurrentPaper(errorPaper);
                
                // 即使加载失败，也记录这个论文作为previousPaper
                // setPreviousPaper({
                //     id: paperId,
                //     status: 'unread',
                //     title: '加载失败'
                // });
            });
        } finally {
            setPaperLoading(false);
        }
    }, [showNotification, togglePaperStatus]);

    const handleAddToReadLater = async (paperId) => {
        const result = await addToReadLater(paperId);
        if (result.success && currentPaper && currentPaper.id === paperId) {
            // 乐观更新UI，立即显示已标记状态
            setCurrentPaper(prev => ({...prev, is_marked: true}));
        }
    };

    const handleRemoveFromReadLater = async (paperId) => {
        const result = await removeFromReadLater(paperId);
        if (result.success && currentPaper && currentPaper.id === paperId) {
            // 乐观更新UI，立即显示未标记状态
            setCurrentPaper(prev => ({...prev, is_marked: false}));
        }
    };

    // 移除selectFeed方法，已由新订阅系统替代

    const handleSetCurrentView = useCallback((viewId) => {
        setCurrentView(viewId);
    }, []);

    // 翻译摘要
    const translateAbstract = useCallback(async (paperId) => {
        try {
            setLoading(true);
            const result = await apiClient.translateAbstract(paperId);

            if (result.success) {
                // 更新当前论文的翻译
                if (currentPaper && currentPaper.id === parseInt(paperId)) {
                    setCurrentPaper(prev => ({
                        ...prev,
                        abstract_cn: result.translation
                    }));
                }

                const message = result.cached ? '翻译结果已显示（来自缓存）' : '翻译完成';
                showNotification(message, 'success');

                return result;
            } else {
                showNotification(result.error || '翻译失败', 'error');
                return result;
            }
        } catch (error) {
            console.error('Failed to translate abstract:', error);
            showNotification('翻译请求失败', 'error');
            return { success: false, error: '翻译请求失败' };
        } finally {
            setLoading(false);
        }
    }, [currentPaper, showNotification]);

    // 设置论文筛选
    const setFilter = useCallback((status) => {
        setPaperFilter(status);
    }, []);

    // 论文导航 - 已废弃，由各个视图自己处理
    const navigatePaper = useCallback((/* direction */) => {
        console.warn('navigatePaper is deprecated, should be handled by individual views');
        return;
    }, []);

    // 获取导航信息 - 已废弃，由各个视图自己处理
    const getNavigationInfo = useCallback(() => {
        console.warn('getNavigationInfo is deprecated, should be handled by individual views');
        return null;
    }, []);

    // 移除旧的论文源初始化代码，已由新订阅系统替代

    const value = {
        currentView,
        // papers 已移除，由各个视图自己管理分页数据
        currentPaperId,
        currentPaper,
        paperFilter,
        loading,
        paperLoading,
        registerViewRefreshCallback, // 新增：注册视图刷新回调
        setCurrentView: handleSetCurrentView, // <-- 暴露新的包装函数
        selectPaper,
        togglePaperStatus,
        translateAbstract,
        setFilter, // 提供设置筛选状态的函数
        navigatePaper, // 已废弃
        getNavigationInfo, // 已废弃
        handleAddToReadLater,
        handleRemoveFromReadLater
    };

    return (
        <PaperContext.Provider value={value}>
            {children}
        </PaperContext.Provider>
    );
}