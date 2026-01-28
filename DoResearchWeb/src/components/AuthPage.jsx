import React, { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    TextField,
    Button,
    Typography,
    Tab,
    Tabs,
    Alert,
    InputAdornment,
    IconButton,
    CircularProgress,
    Paper,
    Container
} from '@mui/material';
import {
    Visibility,
    VisibilityOff,
    Person,
    Email,
    Lock,
    LoginOutlined,
    PersonAddOutlined
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

function TabPanel({ children, value, index, ...other }) {
    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`auth-tabpanel-${index}`}
            aria-labelledby={`auth-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ pt: 3 }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

export default function AuthPage() {
    const { login, register, isLoading } = useAuth();
    
    const [tabValue, setTabValue] = useState(0);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [error, setError] = useState('');
    
    // 登录表单状态
    const [loginForm, setLoginForm] = useState({
        username: '',
        password: ''
    });
    
    // 注册表单状态
    const [registerForm, setRegisterForm] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
        setError('');
    };

    const handleLoginSubmit = async (e) => {
        e.preventDefault();
        setError('');
        
        if (!loginForm.username || !loginForm.password) {
            setError('请输入用户名和密码');
            return;
        }
        
        console.log('正在尝试登录:', { username: loginForm.username });
        const result = await login(loginForm.username, loginForm.password);
        if (!result.success) {
            setError(result.error || '登录失败');
        }
    };

    const handleRegisterSubmit = async (e) => {
        e.preventDefault();
        setError('');
        
        if (!registerForm.username || !registerForm.email || !registerForm.password) {
            setError('请填写所有必填字段');
            return;
        }
        
        if (registerForm.password !== registerForm.confirmPassword) {
            setError('两次输入的密码不一致');
            return;
        }
        
        if (registerForm.password.length < 6) {
            setError('密码至少需要6个字符');
            return;
        }
        
        const result = await register(registerForm.username, registerForm.email, registerForm.password);
        if (result.success) {
            // 注册成功后切换到登录页
            setTabValue(0);
            setRegisterForm({ username: '', email: '', password: '', confirmPassword: '' });
        } else {
            setError(result.error || '注册失败');
        }
    };

    return (
        <Container maxWidth="sm" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
            <Paper 
                elevation={8} 
                sx={{ 
                    width: '100%',
                    borderRadius: 3,
                    overflow: 'hidden'
                }}
            >
                {/* 头部 */}
                <Box sx={{ 
                    background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
                    color: 'white',
                    p: 4,
                    textAlign: 'center'
                }}>
                    <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
                        DoResearch
                    </Typography>
                    <Typography variant="body1" sx={{ opacity: 0.9 }}>
                        学术论文管理平台
                    </Typography>
                </Box>

                <CardContent sx={{ p: 4 }}>
                    {/* Tab导航 */}
                    <Tabs 
                        value={tabValue} 
                        onChange={handleTabChange} 
                        variant="fullWidth"
                        sx={{ mb: 2 }}
                    >
                        <Tab 
                            icon={<LoginOutlined />} 
                            label="登录" 
                            iconPosition="start"
                        />
                        <Tab 
                            icon={<PersonAddOutlined />} 
                            label="注册" 
                            iconPosition="start"
                        />
                    </Tabs>

                    {/* 错误提示 */}
                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    {/* 登录表单 */}
                    <TabPanel value={tabValue} index={0}>
                        <Box component="form" onSubmit={handleLoginSubmit}>
                            <TextField
                                fullWidth
                                label="用户名"
                                value={loginForm.username}
                                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                                margin="normal"
                                required
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Person color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <TextField
                                fullWidth
                                label="密码"
                                type={showPassword ? 'text' : 'password'}
                                value={loginForm.password}
                                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                                margin="normal"
                                required
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Lock color="action" />
                                        </InputAdornment>
                                    ),
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={() => setShowPassword(!showPassword)}
                                                edge="end"
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{ mt: 3, mb: 2, py: 1.5 }}
                                disabled={isLoading}
                                startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <LoginOutlined />}
                            >
                                {isLoading ? '登录中...' : '登录'}
                            </Button>
                        </Box>
                    </TabPanel>

                    {/* 注册表单 */}
                    <TabPanel value={tabValue} index={1}>
                        <Box component="form" onSubmit={handleRegisterSubmit}>
                            <TextField
                                fullWidth
                                label="用户名"
                                value={registerForm.username}
                                onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                                margin="normal"
                                required
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Person color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <TextField
                                fullWidth
                                label="邮箱"
                                type="email"
                                value={registerForm.email}
                                onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                                margin="normal"
                                required
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Email color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <TextField
                                fullWidth
                                label="密码"
                                type={showPassword ? 'text' : 'password'}
                                value={registerForm.password}
                                onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                                margin="normal"
                                required
                                helperText="至少6个字符"
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Lock color="action" />
                                        </InputAdornment>
                                    ),
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={() => setShowPassword(!showPassword)}
                                                edge="end"
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <TextField
                                fullWidth
                                label="确认密码"
                                type={showConfirmPassword ? 'text' : 'password'}
                                value={registerForm.confirmPassword}
                                onChange={(e) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
                                margin="normal"
                                required
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Lock color="action" />
                                        </InputAdornment>
                                    ),
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                edge="end"
                                            >
                                                {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{ mt: 3, mb: 2, py: 1.5 }}
                                disabled={isLoading}
                                startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <PersonAddOutlined />}
                            >
                                {isLoading ? '注册中...' : '注册'}
                            </Button>
                        </Box>
                    </TabPanel>

                    {/* 默认账户提示 */}
                    <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                        <Typography variant="body2" color="info.contrastText" sx={{ mb: 1 }}>
                            <strong>默认管理员账户：</strong>
                        </Typography>
                        <Typography variant="body2" color="info.contrastText">
                            用户名: admin | 密码: admin123
                        </Typography>
                    </Box>
                </CardContent>
            </Paper>
        </Container>
    );
}