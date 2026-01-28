import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import apiClient from '../services/apiClient';
import { useNotification } from '../components/NotificationProvider';
import { AuthContext } from './AuthContext';

export const DataContext = createContext();

export function DataProvider({ children }) {
    const { showSuccess, showError } = useNotification();
    const { isAuthenticated, isLoading: authLoading } = useContext(AuthContext);

    // --- 变更: addToReadLater 现在调用后端API ---
    const addToReadLater = useCallback(async (paperId) => {
        try {
            const result = await apiClient.quickAddReadLater(paperId);
            if (result.success) {
                showSuccess(result.message || '已添加到稍后阅读');
                return { success: true };
            }
            throw new Error(result.error);
        } catch (error) {
            console.error('Failed to add to read later:', error);
            showError(error.message || '添加失败');
            return { success: false, error: error.message };
        }
    }, [showSuccess, showError]);

    // --- 变更: removeFromReadLater 现在调用后端API ---
    const removeFromReadLater = useCallback(async (paperId) => {
        try {
            const result = await apiClient.removeReadLater(paperId);
            if (result.success) {
                showSuccess(result.message || '已从稍后阅读中移除', 'success');
                return { success: true };
            }
            throw new Error(result.error);
        } catch (error) {
            console.error('Failed to remove from read later:', error);
            showError(error.message || '移除失败');
            return { success: false, error: error.message };
        }
    }, [showSuccess, showError]);

    // 获取统计数据
    const getStatsData = useCallback(async () => {
        // 如果用户未认证，返回空数据
        if (!isAuthenticated || authLoading) {
            console.log('用户未认证，返回空统计数据');
            return {
                total_papers: 0,
                read_papers: 0,
                reading_streak_days: 0,
                last_30_days_new_papers: [],
                last_30_days_read_papers: [],
                last_year_read_papers: [],
            };
        }
        
        try {
            // 直接调用新的API接口
            const statsSummary = await apiClient.getStatisticsSummary();
            return statsSummary;
        } catch (error) {
            console.error('Failed to get stats data:', error);
            showError(error.message || '获取统计数据失败');
            // 在出错时返回一个空的结构，防止页面崩溃
            return {
                total_papers: 0,
                read_papers: 0,
                reading_streak_days: 0,
                last_30_days_new_papers: [],
                last_30_days_read_papers: [],
                last_year_read_papers: [],
            };
        }
    }, [isAuthenticated, authLoading, showSuccess, showError]);

    const value = {
        getStatsData,
        addToReadLater,
        removeFromReadLater,
    };

    return (
        <DataContext.Provider value={value}>
            {children}
        </DataContext.Provider>
    );
}