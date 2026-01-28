import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import apiClient from '../services/apiClient.jsx';
import { AuthContext } from './AuthContext.jsx';

export const TaskContext = createContext();

export function TaskProvider({ children }) {
    const { isAuthenticated, isLoading: authLoading } = useContext(AuthContext);
    
    const [tasks, setTasks] = useState([]);
    const [agents, setAgents] = useState([]);
    const [taskStats, setTaskStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [pollingActive, setPollingActive] = useState(false);

    // 加载任务列表
    const loadTasks = useCallback(async (status = null, limit = 50) => {
        // 如果用户未认证，直接返回空数组
        if (!isAuthenticated || authLoading) {
            console.log('用户未认证，跳过加载任务列表');
            return [];
        }
        
        try {
            setLoading(true);
            const tasksData = await apiClient.getTasks({ status, limit });
            setTasks(tasksData || []);
            return tasksData || [];
        } catch (error) {
            console.error('Failed to load tasks:', error);
            setTasks([]);
            return [];
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated, authLoading]);

    // 加载Agent列表
    const loadAgents = useCallback(async () => {
        // 如果用户未认证，直接返回空数组
        if (!isAuthenticated || authLoading) {
            console.log('用户未认证，跳过加载Agent列表');
            return [];
        }
        
        try {
            const agentsData = await apiClient.getAgents();
            setAgents(agentsData);
            return agentsData;
        } catch (error) {
            console.error('Failed to load agents:', error);
            return [];
        }
    }, [isAuthenticated, authLoading]);

    // 加载任务统计
    const loadTaskStats = useCallback(async () => {
        // 如果用户未认证，直接返回
        if (!isAuthenticated || authLoading) {
            console.log('用户未认证，跳过加载任务统计');
            return null;
        }
        
        try {
            const statsData = await apiClient.getTaskStats();
            setTaskStats(statsData);
            return statsData;
        } catch (error) {
            console.error('Failed to load task stats:', error);
            return null;
        }
    }, [isAuthenticated, authLoading]);

    // 创建深度分析任务
    const createAnalysisTask = useCallback(async (paperId, priority = 5) => {
        try {
            setLoading(true);
            const result = await apiClient.createAnalysisTask(paperId, priority);

            if (result.success) {
                // 重新加载任务列表
                await loadTasks();
                // 开始轮询
                startPolling();
                return { success: true, taskId: result.task_id };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('Failed to create analysis task:', error);
            return { success: false, error: '创建任务失败' };
        } finally {
            setLoading(false);
        }
    }, [loadTasks]);

    // 取消任务
    const cancelTask = useCallback(async (taskId) => {
        try {
            const result = await apiClient.cancelTask(taskId);

            if (result.success) {
                // 重新加载任务列表
                await loadTasks();
                return { success: true };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('Failed to cancel task:', error);
            return { success: false, error: '取消任务失败' };
        }
    }, [loadTasks]);

    // 获取单个任务详情
    const getTask = useCallback(async (taskId) => {
        try {
            return await apiClient.getTask(taskId);
        } catch (error) {
            console.error('Failed to get task:', error);
            return null;
        }
    }, []);

    // 开始轮询任务状态
    const startPolling = useCallback(() => {
        if (pollingActive) return;

        setPollingActive(true);
    }, [pollingActive]);

    // 停止轮询
    const stopPolling = useCallback(() => {
        setPollingActive(false);
    }, []);

    // 轮询逻辑
    useEffect(() => {
        if (!pollingActive) return;

        const pollInterval = setInterval(async () => {
            try {
                // 检查是否有活跃任务
                const currentTasks = await loadTasks();
                const activeTasks = currentTasks.filter(task =>
                    ['pending', 'in_progress', 'downloading', 'analyzing'].includes(task.status)
                );

                if (activeTasks.length === 0) {
                    stopPolling();
                } else {
                    // 同时更新统计数据
                    await loadTaskStats();
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 5000); // 每5秒检查一次

        return () => {
            clearInterval(pollInterval);
        };
    }, [pollingActive, loadTasks, loadTaskStats, stopPolling]);

    // 页面可见性变化处理
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible') {
                // 页面变为可见时检查是否需要开始轮询
                loadTasks().then(tasks => {
                    const activeTasks = tasks.filter(task =>
                        ['pending', 'in_progress', 'downloading', 'analyzing'].includes(task.status)
                    );
                    if (activeTasks.length > 0) {
                        startPolling();
                    }
                });
            } else {
                // 页面隐藏时停止轮询
                stopPolling();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [loadTasks, startPolling, stopPolling]);

    // 初始化时检查活跃任务 - 只有在用户已认证时才执行
    useEffect(() => {
        if (!isAuthenticated || authLoading) {
            return;
        }

        const initCheck = async () => {
            const tasks = await loadTasks();
            const activeTasks = tasks.filter(task =>
                task && ['pending', 'in_progress', 'downloading', 'analyzing'].includes(task.status)
            );

            if (activeTasks.length > 0) {
                startPolling();
            }
        };

        initCheck();
    }, [isAuthenticated, authLoading, loadTasks, startPolling]);

    const value = {
        // 状态
        tasks,
        agents,
        taskStats,
        loading,
        pollingActive,

        // 任务操作
        loadTasks,
        createAnalysisTask,
        cancelTask,
        getTask,

        // Agent操作
        loadAgents,

        // 统计操作
        loadTaskStats,

        // 轮询控制
        startPolling,
        stopPolling,

        // 工具方法
        getTaskStatusText: (status) => {
            const statusMap = {
                'pending': '等待中',
                'in_progress': '处理中',
                'downloading': '下载PDF',
                'analyzing': 'AI分析中',
                'completed': '分析完成',
                'failed': '分析失败',
                'cancelled': '已取消'
            };
            return statusMap[status] || status;
        },

        getTaskStatusColor: (status) => {
            const colorMap = {
                'pending': 'default',
                'in_progress': 'info',
                'downloading': 'info',
                'analyzing': 'info',
                'completed': 'success',
                'failed': 'error',
                'cancelled': 'default'
            };
            return colorMap[status] || 'default';
        },

        getAgentStatusText: (status) => {
            const statusMap = {
                'online': '在线',
                'offline': '离线',
                'busy': '忙碌',
                'error': '错误'
            };
            return statusMap[status] || status;
        },

        getAgentStatusColor: (status) => {
            const colorMap = {
                'online': 'success',
                'offline': 'error',
                'busy': 'warning',
                'error': 'error'
            };
            return colorMap[status] || 'default';
        }
    };

    return (
        <TaskContext.Provider value={value}>
            {children}
        </TaskContext.Provider>
    );
}