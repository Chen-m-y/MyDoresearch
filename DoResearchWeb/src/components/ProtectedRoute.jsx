import React, { useEffect } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import AuthPage from './AuthPage';

export default function ProtectedRoute({ children }) {
    const { isAuthenticated, isLoading, refreshAuth } = useAuth();

    // 监听认证过期事件
    useEffect(() => {
        const handleAuthExpired = () => {
            // 当收到认证过期事件时，刷新认证状态
            refreshAuth();
        };

        window.addEventListener('auth-expired', handleAuthExpired);
        
        return () => {
            window.removeEventListener('auth-expired', handleAuthExpired);
        };
    }, [refreshAuth]);

    // 加载中状态
    if (isLoading) {
        return (
            <Box 
                sx={{ 
                    height: '100vh', 
                    display: 'flex', 
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center',
                    gap: 2
                }}
            >
                <CircularProgress size={60} />
                <Typography variant="h6" color="text.secondary">
                    正在验证登录状态...
                </Typography>
            </Box>
        );
    }

    // 未认证，显示登录页面
    if (!isAuthenticated) {
        return <AuthPage />;
    }

    // 已认证，显示受保护的内容
    return <>{children}</>;
}