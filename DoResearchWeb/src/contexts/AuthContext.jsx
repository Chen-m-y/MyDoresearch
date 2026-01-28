import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import apiClient, { setAuthToken, getAuthToken } from '../services/apiClient';
import { useNotification } from '../components/NotificationProvider';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
    const { showSuccess, showError } = useNotification();
    
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [sessionToken, setSessionToken] = useState(null);

    // 从localStorage恢复登录状态
    useEffect(() => {
        const checkAuthStatus = async () => {
            try {
                const savedToken = localStorage.getItem('session_token');
                const savedUser = localStorage.getItem('user_info');
                
                if (savedToken && savedUser) {
                    setSessionToken(savedToken);
                    setUser(JSON.parse(savedUser));
                    setIsAuthenticated(true);
                    
                    // 验证token是否仍然有效
                    try {
                        const result = await apiClient.checkAuth();
                        if (!result.success) {
                            // Token无效，清除本地存储
                            logout(false);
                        }
                    } catch (error) {
                        // 网络错误或token无效，清除本地存储
                        logout(false);
                    }
                }
            } catch (error) {
                console.error('检查认证状态失败:', error);
                logout(false);
            } finally {
                setIsLoading(false);
            }
        };
        
        // 监听认证过期事件
        const handleAuthExpired = () => {
            console.log('收到认证过期事件，清除认证状态');
            logout(false);
        };

        window.addEventListener('auth-expired', handleAuthExpired);
        checkAuthStatus();
        
        return () => {
            window.removeEventListener('auth-expired', handleAuthExpired);
        };
    }, []);

    // 登录
    const login = useCallback(async (username, password) => {
        try {
            setIsLoading(true);
            const result = await apiClient.login(username, password);
            
            if (result.success) {
                // 从API响应中直接获取数据
                const session_token = result.session_token;
                const userData = result.user;
                
                if (!session_token) {
                    console.error('登录响应中缺少session_token:', result);
                    throw new Error('登录响应格式错误');
                }
                
                // 保存到state
                setSessionToken(session_token);
                setUser(userData);
                setIsAuthenticated(true);
                
                // 保存到localStorage
                localStorage.setItem('session_token', session_token);
                localStorage.setItem('user_info', JSON.stringify(userData));
                
                showSuccess(`欢迎回来，${userData.username || '用户'}！`);
                
                // 不需要刷新页面，直接更新认证状态即可
                return { success: true };
            } else {
                showError(result.error || '登录失败');
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('登录失败:', error);
            showError(error.message || '登录失败');
            return { success: false, error: error.message };
        } finally {
            setIsLoading(false);
        }
    }, [showSuccess, showError]);

    // 注册
    const register = useCallback(async (username, email, password) => {
        try {
            setIsLoading(true);
            const result = await apiClient.register(username, email, password);
            
            if (result.success) {
                showSuccess('注册成功！请登录');
                return { success: true };
            } else {
                showError(result.error || '注册失败');
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('注册失败:', error);
            showError(error.message || '注册失败');
            return { success: false, error: error.message };
        } finally {
            setIsLoading(false);
        }
    }, [showSuccess, showError]);

    // 登出
    const logout = useCallback(async (showMessage = true) => {
        try {
            if (sessionToken) {
                await apiClient.logout();
            }
        } catch (error) {
            console.error('登出请求失败:', error);
        } finally {
            // 无论API调用是否成功，都清除本地状态
            setAuthToken(null); // 清除apiClient中的token
            setSessionToken(null);
            setUser(null);
            setIsAuthenticated(false);
            
            // 清除localStorage
            localStorage.removeItem('session_token');
            localStorage.removeItem('user_info');
            
            if (showMessage) {
                showSuccess('已退出登录');
            }
        }
    }, [sessionToken, showSuccess]);

    // 修改密码
    const changePassword = useCallback(async (currentPassword, newPassword) => {
        try {
            const result = await apiClient.changePassword(currentPassword, newPassword);
            
            if (result.success) {
                return { success: true };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('密码修改失败:', error);
            return { success: false, error: error.message };
        }
    }, []);

    // 修改用户名
    const changeUsername = useCallback(async (newUsername, password) => {
        try {
            const result = await apiClient.changeUsername(newUsername, password);
            
            if (result.success) {
                // 更新用户信息中的用户名
                const updatedUser = { ...user, username: result.new_username };
                setUser(updatedUser);
                localStorage.setItem('user_info', JSON.stringify(updatedUser));
                
                return { success: true, newUsername: result.new_username };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('用户名修改失败:', error);
            return { success: false, error: error.message };
        }
    }, [user]);

    // 修改邮箱
    const changeEmail = useCallback(async (newEmail, password) => {
        try {
            const result = await apiClient.changeEmail(newEmail, password);
            
            if (result.success) {
                // 更新用户信息中的邮箱
                const updatedUser = { ...user, email: result.new_email };
                setUser(updatedUser);
                localStorage.setItem('user_info', JSON.stringify(updatedUser));
                
                return { success: true, newEmail: result.new_email };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('邮箱修改失败:', error);
            return { success: false, error: error.message };
        }
    }, [user]);

    // 获取用户资料
    const getProfile = useCallback(async () => {
        try {
            const result = await apiClient.getProfile();
            if (result.success) {
                // API返回格式是 {success: true, user: {...}}
                const userData = result.user;
                setUser(userData);
                // 更新localStorage
                localStorage.setItem('user_info', JSON.stringify(userData));
                return { success: true, data: userData };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('获取用户资料失败:', error);
            return { success: false, error: error.message };
        }
    }, []);

    // 刷新认证状态（用于token过期处理）
    const refreshAuth = useCallback(async () => {
        try {
            const result = await apiClient.checkAuth();
            if (result.success) {
                return true;
            } else {
                // Token无效，登出用户
                logout(true);
                return false;
            }
        } catch (error) {
            console.error('刷新认证状态失败:', error);
            logout(true);
            return false;
        }
    }, [logout]);

    const value = {
        user,
        isAuthenticated,
        isLoading,
        sessionToken,
        login,
        register,
        logout,
        changePassword,
        changeUsername,
        changeEmail,
        getProfile,
        refreshAuth
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

// 自定义hook
export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth必须在AuthProvider内部使用');
    }
    return context;
}