import React, { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Alert,
    Grid,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Switch,
    Divider,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    DialogContentText,
    IconButton,
    InputAdornment,
    useTheme,
    useMediaQuery,
    alpha
} from '@mui/material';
import {
    LockOutlined,
    EmailOutlined,
    SecurityOutlined,
    NotificationsOutlined,
    LanguageOutlined,
    DarkModeOutlined,
    Visibility,
    VisibilityOff,
    SaveOutlined,
    RefreshOutlined,
    AccountCircleOutlined
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from './NotificationProvider';

export default function SettingsPage() {
    const { changePassword, changeUsername, changeEmail, logout } = useAuth();
    const { showSuccess } = useNotification();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    
    // 统一账户设置表单状态
    const [accountForm, setAccountForm] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        newUsername: '',
        newEmail: ''
    });
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [accountError, setAccountError] = useState('');
    const [isUpdatingAccount, setIsUpdatingAccount] = useState(false);
    const [accountUpdateSuccess, setAccountUpdateSuccess] = useState('');
    
    // 应用设置相关状态
    const [settings, setSettings] = useState({
        notifications: true,
        darkMode: false,
        language: 'zh-CN',
        emailNotifications: true,
        autoRefresh: true
    });
    
    // 确认对话框状态
    const [confirmDialog, setConfirmDialog] = useState({
        open: false,
        title: '',
        content: '',
        action: null
    });

    // 统一的账户信息修改处理函数
    const handleAccountUpdate = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        setAccountError('');
        setAccountUpdateSuccess('');

        // 检查是否有任何要修改的内容
        const hasPasswordChange = accountForm.newPassword || accountForm.confirmPassword;
        const hasUsernameChange = accountForm.newUsername.trim();
        const hasEmailChange = accountForm.newEmail.trim();

        if (!hasPasswordChange && !hasUsernameChange && !hasEmailChange) {
            setAccountError('请至少填写一项要修改的内容');
            return;
        }

        // 验证当前密码
        if (!accountForm.currentPassword) {
            setAccountError('请输入当前密码以确认身份');
            return;
        }

        // 密码修改验证
        if (hasPasswordChange) {
            if (!accountForm.newPassword || !accountForm.confirmPassword) {
                setAccountError('请填写完整的新密码信息');
                return;
            }
            
            if (accountForm.newPassword !== accountForm.confirmPassword) {
                setAccountError('两次输入的新密码不一致');
                return;
            }

            if (accountForm.newPassword.length < 6) {
                setAccountError('新密码长度至少需要6个字符');
                return;
            }

            if (accountForm.currentPassword === accountForm.newPassword) {
                setAccountError('新密码不能与当前密码相同');
                return;
            }
        }

        // 用户名验证
        if (hasUsernameChange) {
            if (accountForm.newUsername.length < 3) {
                setAccountError('用户名长度至少需要3个字符');
                return;
            }
            if (accountForm.newUsername.length > 50) {
                setAccountError('用户名长度不能超过50个字符');
                return;
            }
        }

        // 邮箱验证
        if (hasEmailChange) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(accountForm.newEmail)) {
                setAccountError('请输入有效的邮箱地址');
                return;
            }
        }

        try {
            setIsUpdatingAccount(true);
            const results = [];
            const successMessages = [];

            // 依次执行修改操作
            if (hasPasswordChange) {
                const result = await changePassword(accountForm.currentPassword, accountForm.newPassword);
                if (result.success) {
                    successMessages.push('密码修改成功');
                } else {
                    throw new Error(result.error || '密码修改失败');
                }
            }

            if (hasUsernameChange) {
                const result = await changeUsername(accountForm.newUsername, accountForm.currentPassword);
                if (result.success) {
                    successMessages.push(`用户名已修改为: ${result.newUsername}`);
                } else {
                    throw new Error(result.error || '用户名修改失败');
                }
            }

            if (hasEmailChange) {
                const result = await changeEmail(accountForm.newEmail, accountForm.currentPassword);
                if (result.success) {
                    successMessages.push(`邮箱已修改为: ${result.newEmail}`);
                    // 延迟提示用户头像将自动更新
                    setTimeout(() => {
                        showSuccess('头像已根据新邮箱自动更新');
                    }, 1500);
                } else {
                    throw new Error(result.error || '邮箱修改失败');
                }
            }

            // 所有修改成功
            setAccountUpdateSuccess(successMessages.join('；'));
            setAccountForm({
                currentPassword: '',
                newPassword: '',
                confirmPassword: '',
                newUsername: '',
                newEmail: ''
            });

            showSuccess('账户信息修改成功！');

            // 如果修改了密码，询问是否重新登录
            if (hasPasswordChange) {
                setTimeout(() => {
                    showConfirmDialog(
                        '密码修改成功',
                        '为了确保账户安全，建议您重新登录。是否现在登出？',
                        () => {
                            logout(false);
                        }
                    );
                }, 1000);
            }

        } catch (error) {
            console.error('账户信息修改失败:', error);
            setAccountError(error.message || '修改失败，请稍后重试');
        } finally {
            setIsUpdatingAccount(false);
        }
    };

    // 处理设置变更
    const handleSettingChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
        
        showSuccess(`${getSettingLabel(key)}已${value ? '开启' : '关闭'}`);
    };

    // 获取设置项标签
    const getSettingLabel = (key) => {
        const labels = {
            notifications: '桌面通知',
            darkMode: '深色模式',
            emailNotifications: '邮件通知',
            autoRefresh: '自动刷新'
        };
        return labels[key] || key;
    };

    // 显示确认对话框
    const showConfirmDialog = (title, content, action) => {
        setConfirmDialog({
            open: true,
            title,
            content,
            action
        });
    };

    // 关闭确认对话框
    const closeConfirmDialog = () => {
        setConfirmDialog({
            open: false,
            title: '',
            content: '',
            action: null
        });
    };

    // 执行确认操作
    const executeConfirmAction = () => {
        if (confirmDialog.action) {
            confirmDialog.action();
        }
        closeConfirmDialog();
    };

    // 重置设置
    const handleResetSettings = () => {
        showConfirmDialog(
            '重置设置',
            '确定要将所有设置重置为默认值吗？此操作无法撤销。',
            () => {
                setSettings({
                    notifications: true,
                    darkMode: false,
                    language: 'zh-CN',
                    emailNotifications: true,
                    autoRefresh: true
                });
                showSuccess('设置已重置为默认值');
            }
        );
    };

    return (
        <Box sx={{
            p: { xs: 1, md: 2 }
        }}>
            {/* 统一账户设置卡片 */}
            <Box sx={{
                display: 'grid',
                gridTemplateColumns: '1fr',
                gap: { xs: 1.5, md: 2 },
                mb: { xs: 1.5, md: 2 }
            }}>
                <Card sx={{
                    animation: 'fadeInUp 0.6s ease-out',
                    '@keyframes fadeInUp': {
                        from: {
                            opacity: 0,
                            transform: 'translateY(30px)',
                        },
                        to: {
                            opacity: 1,
                            transform: 'translateY(0)',
                        },
                    },
                }}>
                    <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                            <Box sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center',
                                width: 32,
                                height: 32,
                                borderRadius: 1.5,
                                bgcolor: alpha(theme.palette.primary.main, 0.1),
                                color: theme.palette.primary.main,
                                mr: 1.5
                            }}>
                                <AccountCircleOutlined fontSize="small" />
                            </Box>
                            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                                ⚙️ 账户信息设置
                            </Typography>
                        </Box>

                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontSize: '0.8rem' }}>
                            一次性修改密码、用户名和邮箱，只需输入一次当前密码
                        </Typography>

                        <Box component="form" onSubmit={handleAccountUpdate}>
                            {accountError && (
                                <Alert severity="error" sx={{ mb: 1.5, fontSize: '0.8rem' }}>
                                    {accountError}
                                </Alert>
                            )}
                            
                            {accountUpdateSuccess && (
                                <Alert severity="success" sx={{ mb: 1.5, fontSize: '0.8rem' }}>
                                    {accountUpdateSuccess}
                                </Alert>
                            )}

                            <Box sx={{ 
                                display: 'grid',
                                gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
                                gap: 1.5,
                                mb: 2
                            }}>
                                {/* 当前密码 - 必填 */}
                                <TextField
                                    fullWidth
                                    label="当前密码 *"
                                    type={showCurrentPassword ? 'text' : 'password'}
                                    value={accountForm.currentPassword}
                                    onChange={(e) => setAccountForm({
                                        ...accountForm,
                                        currentPassword: e.target.value
                                    })}
                                    required
                                    size="small"
                                    helperText="验证身份，必填"
                                    InputProps={{
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                                    edge="end"
                                                >
                                                    {showCurrentPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                    }}
                                />

                                {/* 新用户名 - 可选 */}
                                <TextField
                                    fullWidth
                                    label="新用户名（可选）"
                                    value={accountForm.newUsername}
                                    onChange={(e) => setAccountForm({
                                        ...accountForm,
                                        newUsername: e.target.value
                                    })}
                                    size="small"
                                    helperText="3-50个字符，留空表示不修改"
                                />

                                {/* 新邮箱 - 可选 */}
                                <TextField
                                    fullWidth
                                    label="新邮箱（可选）"
                                    type="email"
                                    value={accountForm.newEmail}
                                    onChange={(e) => setAccountForm({
                                        ...accountForm,
                                        newEmail: e.target.value
                                    })}
                                    size="small"
                                    helperText="头像将根据Gravatar自动更新"
                                />

                                {/* 新密码 - 可选 */}
                                <TextField
                                    fullWidth
                                    label="新密码（可选）"
                                    type={showNewPassword ? 'text' : 'password'}
                                    value={accountForm.newPassword}
                                    onChange={(e) => setAccountForm({
                                        ...accountForm,
                                        newPassword: e.target.value
                                    })}
                                    size="small"
                                    helperText="至少6个字符，留空表示不修改"
                                    InputProps={{
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => setShowNewPassword(!showNewPassword)}
                                                    edge="end"
                                                >
                                                    {showNewPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                    }}
                                />
                            </Box>

                            {/* 确认新密码 - 只在填写新密码时显示 */}
                            {accountForm.newPassword && (
                                <Box sx={{ mb: 2 }}>
                                    <TextField
                                        fullWidth
                                        label="确认新密码"
                                        type={showConfirmPassword ? 'text' : 'password'}
                                        value={accountForm.confirmPassword}
                                        onChange={(e) => setAccountForm({
                                            ...accountForm,
                                            confirmPassword: e.target.value
                                        })}
                                        required={!!accountForm.newPassword}
                                        size="small"
                                        error={accountForm.newPassword !== accountForm.confirmPassword && accountForm.confirmPassword !== ''}
                                        helperText={
                                            accountForm.newPassword !== accountForm.confirmPassword && accountForm.confirmPassword !== ''
                                                ? '密码不匹配'
                                                : '请再次输入新密码'
                                        }
                                        InputProps={{
                                            endAdornment: (
                                                <InputAdornment position="end">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                        edge="end"
                                                    >
                                                        {showConfirmPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                                                    </IconButton>
                                                </InputAdornment>
                                            ),
                                        }}
                                    />
                                </Box>
                            )}

                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    size="small"
                                    startIcon={<SaveOutlined fontSize="small" />}
                                    disabled={isUpdatingAccount}
                                    sx={{ fontSize: '0.8rem' }}
                                >
                                    {isUpdatingAccount ? '保存中...' : '保存更改'}
                                </Button>
                                
                                <Button
                                    type="button"
                                    variant="outlined"
                                    size="small"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        setAccountForm({
                                            currentPassword: '',
                                            newPassword: '',
                                            confirmPassword: '',
                                            newUsername: '',
                                            newEmail: ''
                                        });
                                        setAccountError('');
                                        setAccountUpdateSuccess('');
                                    }}
                                    disabled={isUpdatingAccount}
                                    sx={{ fontSize: '0.8rem' }}
                                >
                                    清空表单
                                </Button>
                            </Box>
                        </Box>
                    </CardContent>
                </Card>
            </Box>

            {/* 应用设置和危险操作 */}
            <Box sx={{
                display: 'grid',
                gridTemplateColumns: { 
                    xs: 'repeat(1, 1fr)',
                    md: 'repeat(2, 1fr)'
                },
                gap: { xs: 1.5, md: 2 }
            }}>
                {/* 应用设置卡片 */}
                <Card sx={{
                    animation: 'fadeInUp 0.6s ease-out 0.2s',
                    animationFillMode: 'both',
                    '@keyframes fadeInUp': {
                        from: {
                            opacity: 0,
                            transform: 'translateY(30px)',
                        },
                        to: {
                            opacity: 1,
                            transform: 'translateY(0)',
                        },
                    },
                }}>
                    <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                            <Box sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center',
                                width: 32,
                                height: 32,
                                borderRadius: 1.5,
                                bgcolor: alpha(theme.palette.success.main, 0.1),
                                color: theme.palette.success.main,
                                mr: 1.5
                            }}>
                                <SecurityOutlined fontSize="small" />
                            </Box>
                            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                                🛠️ 应用偏好
                            </Typography>
                        </Box>

                        <List sx={{ py: 0 }}>
                            <ListItem sx={{ px: 0, py: 1 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <NotificationsOutlined fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={<Typography variant="body2" sx={{ fontWeight: 500 }}>桌面通知</Typography>}
                                    secondary={<Typography variant="caption" color="text.secondary">接收重要信息的桌面通知</Typography>}
                                />
                                <Switch
                                    size="small"
                                    checked={settings.notifications}
                                    onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                                />
                            </ListItem>
                            
                            <Divider />
                            
                            <ListItem sx={{ px: 0, py: 1 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <DarkModeOutlined fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={<Typography variant="body2" sx={{ fontWeight: 500 }}>深色模式</Typography>}
                                    secondary={<Typography variant="caption" color="text.secondary">使用深色主题保护眼睛</Typography>}
                                />
                                <Switch
                                    size="small"
                                    checked={settings.darkMode}
                                    onChange={(e) => handleSettingChange('darkMode', e.target.checked)}
                                />
                            </ListItem>
                            
                            <Divider />
                            
                            <ListItem sx={{ px: 0, py: 1 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <LanguageOutlined fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={<Typography variant="body2" sx={{ fontWeight: 500 }}>邮件通知</Typography>}
                                    secondary={<Typography variant="caption" color="text.secondary">通过邮件接收系统通知</Typography>}
                                />
                                <Switch
                                    size="small"
                                    checked={settings.emailNotifications}
                                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                                />
                            </ListItem>
                            
                            <Divider />
                            
                            <ListItem sx={{ px: 0, py: 1 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <RefreshOutlined fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={<Typography variant="body2" sx={{ fontWeight: 500 }}>自动刷新</Typography>}
                                    secondary={<Typography variant="caption" color="text.secondary">自动刷新数据以保持最新状态</Typography>}
                                />
                                <Switch
                                    size="small"
                                    checked={settings.autoRefresh}
                                    onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
                                />
                            </ListItem>
                        </List>
                    </CardContent>
                </Card>

                {/* 危险操作区域 */}
                <Card sx={{
                    animation: 'fadeInUp 0.6s ease-out 0.3s',
                    animationFillMode: 'both',
                    border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`,
                    '@keyframes fadeInUp': {
                        from: {
                            opacity: 0,
                            transform: 'translateY(30px)',
                        },
                        to: {
                            opacity: 1,
                            transform: 'translateY(0)',
                        },
                    },
                }}>
                    <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                            <Box sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center',
                                width: 32,
                                height: 32,
                                borderRadius: 1.5,
                                bgcolor: alpha(theme.palette.error.main, 0.1),
                                color: theme.palette.error.main,
                                mr: 1.5
                            }}>
                                <SecurityOutlined fontSize="small" />
                            </Box>
                            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem', color: 'error.main' }}>
                                ⚠️ 危险操作
                            </Typography>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontSize: '0.8rem' }}>
                            以下操作可能会影响您的账户数据，请谨慎操作
                        </Typography>
                        
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <Button
                                variant="outlined"
                                color="warning"
                                size="small"
                                onClick={handleResetSettings}
                                sx={{ fontSize: '0.8rem' }}
                            >
                                重置所有设置
                            </Button>
                            
                            <Button
                                variant="outlined"
                                color="error"
                                size="small"
                                onClick={() => showConfirmDialog(
                                    '退出登录',
                                    '确定要退出当前账户吗？',
                                    () => logout(true)
                                )}
                                sx={{ fontSize: '0.8rem' }}
                            >
                                退出登录
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            </Box>

            {/* 确认对话框 */}
            <Dialog
                open={confirmDialog.open}
                onClose={closeConfirmDialog}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>{confirmDialog.title}</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        {confirmDialog.content}
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeConfirmDialog}>
                        取消
                    </Button>
                    <Button 
                        onClick={executeConfirmAction}
                        color="primary"
                        variant="contained"
                    >
                        确认
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}