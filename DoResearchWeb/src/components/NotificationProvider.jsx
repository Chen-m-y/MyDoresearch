import React, { createContext, useContext, useState, useCallback } from 'react';
import {
    Snackbar,
    Alert,
    AlertTitle,
    Slide,
    Stack,
    useTheme,
    alpha,
    IconButton,
} from '@mui/material';
import {
    CheckCircle as SuccessIcon,
    Error as ErrorIcon,
    Warning as WarningIcon,
    Info as InfoIcon,
    Close as CloseIcon,
} from '@mui/icons-material';

const NotificationContext = createContext();

export const useNotification = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotification must be used within a NotificationProvider');
    }
    return context;
};

const NotificationProvider = ({ children }) => {
    const theme = useTheme();
    const [notifications, setNotifications] = useState([]);

    const showNotification = useCallback((message, options = {}) => {
        const {
            severity = 'info',
            title = null,
            autoHideDuration = severity === 'error' ? 8000 : 6000,
            persistent = false,
            action = null,
        } = options;

        const id = Date.now() + Math.random();
        
        const notification = {
            id,
            message,
            severity,
            title,
            autoHideDuration: persistent ? null : autoHideDuration,
            action,
            timestamp: Date.now(),
        };

        setNotifications(prev => [...prev, notification]);

        // 自动移除非持久化通知
        if (!persistent && autoHideDuration) {
            setTimeout(() => {
                hideNotification(id);
            }, autoHideDuration);
        }

        return id;
    }, []);

    const hideNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(notification => notification.id !== id));
    }, []);

    const hideAllNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    // 便捷方法
    const showSuccess = useCallback((message, options = {}) => {
        return showNotification(message, { ...options, severity: 'success' });
    }, [showNotification]);

    const showError = useCallback((message, options = {}) => {
        return showNotification(message, { ...options, severity: 'error' });
    }, [showNotification]);

    const showWarning = useCallback((message, options = {}) => {
        return showNotification(message, { ...options, severity: 'warning' });
    }, [showNotification]);

    const showInfo = useCallback((message, options = {}) => {
        return showNotification(message, { ...options, severity: 'info' });
    }, [showNotification]);

    const getIcon = (severity) => {
        const icons = {
            success: SuccessIcon,
            error: ErrorIcon,
            warning: WarningIcon,
            info: InfoIcon,
        };
        const IconComponent = icons[severity];
        return IconComponent ? <IconComponent fontSize="small" /> : null;
    };

    const contextValue = {
        showNotification,
        hideNotification,
        hideAllNotifications,
        showSuccess,
        showError,
        showWarning,
        showInfo,
        notifications,
    };

    return (
        <NotificationContext.Provider value={contextValue}>
            {children}
            
            {/* 通知渲染区域 */}
            <Stack
                spacing={1}
                sx={{
                    position: 'fixed',
                    top: { xs: 16, md: 24 },
                    right: { xs: 16, md: 24 },
                    zIndex: theme.zIndex.snackbar,
                    maxWidth: { xs: 'calc(100vw - 32px)', md: 400 },
                    pointerEvents: 'none',
                }}
            >
                {notifications.map((notification, index) => (
                    <Slide
                        key={notification.id}
                        direction="left"
                        in={true}
                        timeout={{ enter: 300, exit: 200 }}
                        style={{ 
                            transitionDelay: `${index * 100}ms`,
                            pointerEvents: 'auto',
                        }}
                    >
                        <Alert
                            severity={notification.severity}
                            variant="filled"
                            icon={getIcon(notification.severity)}
                            action={
                                <Stack direction="row" spacing={1} alignItems="center">
                                    {notification.action}
                                    <IconButton
                                        size="small"
                                        onClick={() => hideNotification(notification.id)}
                                        sx={{ 
                                            color: 'inherit',
                                            opacity: 0.8,
                                            '&:hover': { opacity: 1 }
                                        }}
                                        aria-label="关闭通知"
                                    >
                                        <CloseIcon fontSize="small" />
                                    </IconButton>
                                </Stack>
                            }
                            sx={{
                                minWidth: 300,
                                boxShadow: theme.shadows[8],
                                backgroundColor: alpha(theme.palette[notification.severity].main, 0.9),
                                backdropFilter: 'blur(8px)',
                                border: `1px solid ${alpha(theme.palette[notification.severity].main, 0.3)}`,
                                '& .MuiAlert-message': {
                                    width: '100%',
                                },
                                animation: 'slideIn 0.3s ease-out',
                                '@keyframes slideIn': {
                                    from: {
                                        opacity: 0,
                                        transform: 'translateX(100%)',
                                    },
                                    to: {
                                        opacity: 1,
                                        transform: 'translateX(0)',
                                    },
                                },
                            }}
                            role="alert"
                            aria-live="polite"
                        >
                            {notification.title && (
                                <AlertTitle sx={{ fontWeight: 600, mb: 0.5 }}>
                                    {notification.title}
                                </AlertTitle>
                            )}
                            {notification.message}
                        </Alert>
                    </Slide>
                ))}
            </Stack>
        </NotificationContext.Provider>
    );
};

export default NotificationProvider;