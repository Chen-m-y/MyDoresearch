import React from 'react';
import {
    ThemeProvider,
    createTheme,
    CssBaseline,
    Box,
    Drawer,
    useMediaQuery
} from '@mui/material';
import { useLayout } from './hooks/useLayout.js';

// 1. 导入 React Router 的核心组件
import { Routes, Route, Navigate } from 'react-router-dom';

import Sidebar from './components/Sidebar.jsx';
import MobileBottomNavigation from './components/BottomNavigation.jsx';
import StatsView from './components/views/StatsView.jsx';
import PapersView from './components/views/PapersView.jsx';
import ReadLaterView from './components/views/ReadLaterView.jsx';
import TasksView from './components/views/TasksView.jsx';
import EnhancedSearchView from './components/views/EnhancedSearchView.jsx';
import UserProfilePage from './components/UserProfilePage.jsx';
import SettingsPage from './components/SettingsPage.jsx';

// 新订阅系统页面
import SubscriptionTemplatesPage from './components/subscriptions/SubscriptionTemplatesPage.jsx';
import CreateSubscriptionPage from './components/subscriptions/CreateSubscriptionPage.jsx';
import MySubscriptionsPage from './components/subscriptions/MySubscriptionsPage.jsx';
import SubscriptionDetailPage from './components/subscriptions/SubscriptionDetailPage.jsx';

import { PaperProvider } from './contexts/PaperContext';
import { DataProvider } from './contexts/DataContext.jsx';
import { TaskProvider } from './contexts/TaskContext.jsx';
import { AuthProvider } from './contexts/AuthContext.jsx';
import NotificationProvider from './components/NotificationProvider.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';

// 创建主题
const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#1976d2',
            light: '#42a5f5',
            dark: '#1565c0',
            contrastText: '#ffffff',
        },
        secondary: {
            main: '#9c27b0',
            light: '#ba68c8',
            dark: '#7b1fa2',
            contrastText: '#ffffff',
        },
        success: {
            main: '#2e7d32',
            light: '#4caf50',
            dark: '#1b5e20',
            contrastText: '#ffffff',
        },
        warning: {
            main: '#ed6c02',
            light: '#ff9800',
            dark: '#e65100',
            contrastText: '#ffffff',
        },
        error: {
            main: '#d32f2f',
            light: '#f44336',
            dark: '#c62828',
            contrastText: '#ffffff',
        },
        info: {
            main: '#0288d1',
            light: '#03a9f4',
            dark: '#01579b',
            contrastText: '#ffffff',
        },
        background: {
            default: '#fafafa',
            paper: '#ffffff',
        },
        text: {
            primary: '#1a1a1a',
            secondary: '#666666',
        },
        divider: '#e0e0e0',
    },
    typography: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif',
        h1: {
            fontWeight: 700,
        },
        h2: {
            fontWeight: 600,
        },
        h3: {
            fontWeight: 600,
        },
        h4: {
            fontWeight: 600,
        },
        h5: {
            fontWeight: 600,
        },
        h6: {
            fontWeight: 600,
        },
        button: {
            fontWeight: 500,
        },
    },
    shape: {
        borderRadius: 12,
    },
    shadows: [
        'none',
        '0px 2px 4px rgba(0,0,0,0.05)',
        '0px 4px 8px rgba(0,0,0,0.08)',
        '0px 8px 16px rgba(0,0,0,0.1)',
        '0px 12px 24px rgba(0,0,0,0.12)',
        '0px 16px 32px rgba(0,0,0,0.14)',
        '0px 20px 40px rgba(0,0,0,0.16)',
        '0px 24px 48px rgba(0,0,0,0.18)',
        '0px 28px 56px rgba(0,0,0,0.2)',
        '0px 32px 64px rgba(0,0,0,0.22)',
        '0px 36px 72px rgba(0,0,0,0.24)',
        '0px 40px 80px rgba(0,0,0,0.26)',
        '0px 44px 88px rgba(0,0,0,0.28)',
        '0px 48px 96px rgba(0,0,0,0.3)',
        '0px 52px 104px rgba(0,0,0,0.32)',
        '0px 56px 112px rgba(0,0,0,0.34)',
        '0px 60px 120px rgba(0,0,0,0.36)',
        '0px 64px 128px rgba(0,0,0,0.38)',
        '0px 68px 136px rgba(0,0,0,0.4)',
        '0px 72px 144px rgba(0,0,0,0.42)',
        '0px 76px 152px rgba(0,0,0,0.44)',
        '0px 80px 160px rgba(0,0,0,0.46)',
        '0px 84px 168px rgba(0,0,0,0.48)',
        '0px 88px 176px rgba(0,0,0,0.5)',
        '0px 92px 184px rgba(0,0,0,0.52)',
    ],
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    borderRadius: 8,
                    fontWeight: 500,
                    padding: '8px 16px',
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                        transform: 'translateY(-1px)',
                        boxShadow: '0px 4px 12px rgba(0,0,0,0.15)',
                    },
                },
                contained: {
                    boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    boxShadow: '0px 2px 8px rgba(0,0,0,0.06)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                        boxShadow: '0px 8px 24px rgba(0,0,0,0.12)',
                        transform: 'translateY(-2px)',
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: 16,
                    fontWeight: 500,
                },
            },
        },
        MuiListItemButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                        backgroundColor: 'rgba(25, 118, 210, 0.04)',
                        transform: 'translateX(2px)',
                    },
                    '&.Mui-selected': {
                        backgroundColor: 'rgba(25, 118, 210, 0.08)',
                        '&:hover': {
                            backgroundColor: 'rgba(25, 118, 210, 0.12)',
                        },
                    },
                },
            },
        },
    },
});

const DRAWER_WIDTH = 280;

function App() {
    const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
    const { styles } = useLayout();

    // 全局错误处理将在NotificationProvider中处理

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <NotificationProvider>
                <AuthProvider>
                    <ProtectedRoute>
                        <TaskProvider>
                            <DataProvider>
                                <PaperProvider>
                                <Box sx={{ display: 'flex', height: '100vh', width: '100%' }}>

                                    {/* 侧边栏 - 仅桌面端显示 */}
                                    {!isMobile && (
                                        <Box
                                            component="nav"
                                            sx={{
                                                width: DRAWER_WIDTH,
                                                flexShrink: 0
                                            }}
                                        >
                                            <Drawer
                                                variant="permanent"
                                                sx={{
                                                    '& .MuiDrawer-paper': {
                                                        boxSizing: 'border-box',
                                                        width: DRAWER_WIDTH,
                                                        border: 'none',
                                                        borderRight: '1px solid',
                                                        borderColor: 'divider'
                                                    },
                                                }}
                                                open
                                            >
                                                <Sidebar />
                                            </Drawer>
                                        </Box>
                                    )}

                                    {/* 主内容区域 */}
                                    <Box
                                        component="main"
                                        sx={{
                                            flexGrow: 1,
                                            height: '100vh',
                                            // 移动端底部留出底部导航空间
                                            ...styles.mainContentPadding,
                                            flexDirection: 'column',
                                            overflowY: 'auto',
                                            overflowX: 'hidden'
                                        }}
                                    >
                                        <Routes>
                                            <Route path="/" element={<Navigate replace to="/stats" />} />
                                            <Route path="/stats" element={<StatsView />} />
                                            <Route path="/readlater" element={<ReadLaterView />} />
                                            <Route path="/tasks" element={<TasksView />} />
                                            <Route path="/search" element={<EnhancedSearchView />} />
                                            <Route path="/profile" element={<UserProfilePage />} />
                                            <Route path="/settings" element={<SettingsPage />} />
                                            {/* 新订阅系统路由 */}
                                            <Route path="/subscriptions" element={<MySubscriptionsPage />} />
                                            <Route path="/subscriptions/templates" element={<SubscriptionTemplatesPage />} />
                                            <Route path="/subscriptions/create/:templateId" element={<CreateSubscriptionPage />} />
                                            <Route path="/subscriptions/:id" element={<SubscriptionDetailPage />} />
                                            <Route path="/subscriptions/:id/edit" element={<CreateSubscriptionPage />} />
                                            {/* 订阅论文列表复用 PapersView */}
                                            <Route path="/subscription/:subscriptionId/papers" element={<PapersView />} />
                                            <Route path="/subscription/:subscriptionId/papers/paper/:paperId" element={<PapersView />} />
                                        </Routes>
                                    </Box>

                                    {/* 移动端底部导航 */}
                                    {isMobile && <MobileBottomNavigation />}
                                </Box>
                                </PaperProvider>
                            </DataProvider>
                        </TaskProvider>
                    </ProtectedRoute>
                </AuthProvider>
            </NotificationProvider>
        </ThemeProvider>
    );
}

export default App;