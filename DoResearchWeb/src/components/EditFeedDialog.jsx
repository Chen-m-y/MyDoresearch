import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Box,
    Typography,
    Alert,
    CircularProgress,
    Switch,
    FormControlLabel
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

import apiClient from '../services/apiClient';

function EditFeedDialog({ open, onClose, feed, onFeedUpdated }) {
    const [formData, setFormData] = useState({
        name: '',
        url: '',
        journal: '',
        active: true
    });

    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    // 当对话框打开且有feed数据时，填充表单
    useEffect(() => {
        if (open && feed) {
            setFormData({
                name: feed.name || '',
                url: feed.url || '',
                journal: feed.journal || '',
                active: feed.active !== undefined ? feed.active : true
            });
            setErrors({});
        }
    }, [open, feed]);

    const handleChange = (field) => (event) => {
        const value = field === 'active' ? event.target.checked : event.target.value;
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));

        // 清除对应字段的错误
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: ''
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = '请输入源名称';
        }

        if (!formData.url.trim()) {
            newErrors.url = '请输入API地址';
        } else {
            // 简单的URL格式验证
            try {
                new URL(formData.url);
            } catch {
                newErrors.url = '请输入有效的URL格式';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async () => {
        if (!validateForm() || !feed) return;

        setLoading(true);
        try {
            await apiClient.editFeed(feed.id, formData);
            
            // 通知父组件更新成功
            if (onFeedUpdated) {
                onFeedUpdated();
            }
            
            handleClose();
        } catch (error) {
            console.error('Failed to edit feed:', error);
            setErrors({ 
                submit: error.response?.data?.message || '更新失败，请重试' 
            });
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setFormData({ name: '', url: '', journal: '', active: true });
        setErrors({});
        setLoading(false);
        onClose();
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter' && !loading) {
            event.preventDefault();
            handleSubmit();
        }
    };

    if (!feed) return null;

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="md"
            fullWidth
        >
            <DialogTitle sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                pb: 1
            }}>
                <Typography variant="h6" component="div">编辑论文源</Typography>
                <Button
                    onClick={handleClose}
                    sx={{ minWidth: 'auto', p: 1 }}
                >
                    <CloseIcon />
                </Button>
            </DialogTitle>

            <DialogContent sx={{ pt: 3, pb: 1 }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {/* 错误提示 */}
                    {errors.submit && (
                        <Alert severity="error">
                            {errors.submit}
                        </Alert>
                    )}

                    {/* 表单部分 */}
                    <Box sx={{ mt: 1 }}>
                        <TextField
                            fullWidth
                            label="源名称"
                            placeholder="例如: IEEE IoT 论文库"
                            value={formData.name}
                            onChange={handleChange('name')}
                            onKeyPress={handleKeyPress}
                            error={!!errors.name}
                            helperText={errors.name}
                            autoFocus
                            sx={{
                                '& .MuiInputLabel-root': {
                                    zIndex: 1
                                }
                            }}
                        />
                    </Box>

                    <Box>
                        <TextField
                            fullWidth
                            label="API地址"
                            placeholder="https://example.com/api/papers"
                            value={formData.url}
                            onChange={handleChange('url')}
                            onKeyPress={handleKeyPress}
                            error={!!errors.url}
                            helperText={errors.url}
                            sx={{
                                '& .MuiInputLabel-root': {
                                    zIndex: 1
                                }
                            }}
                        />
                    </Box>

                    <Box>
                        <TextField
                            fullWidth
                            label="期刊名称 (可选)"
                            placeholder="例如: IEEE Internet of Things Journal"
                            value={formData.journal}
                            onChange={handleChange('journal')}
                            onKeyPress={handleKeyPress}
                            sx={{
                                '& .MuiInputLabel-root': {
                                    zIndex: 1
                                }
                            }}
                        />
                    </Box>

                    {/* 激活状态开关 */}
                    <Box>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={formData.active}
                                    onChange={handleChange('active')}
                                    color="primary"
                                />
                            }
                            label={
                                <Box>
                                    <Typography variant="body2">
                                        {formData.active ? '激活状态' : '暂停状态'}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {formData.active ? '论文源将正常更新' : '论文源将暂停更新'}
                                    </Typography>
                                </Box>
                            }
                        />
                    </Box>

                    {/* 论文源信息 */}
                    <Box sx={{
                        p: 2,
                        background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}08 0%, ${theme.palette.info.main}12 100%)`,
                        border: (theme) => `1px solid ${theme.palette.info.light}30`,
                        borderRadius: 2
                    }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            论文源信息
                        </Typography>
                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                            <Box>
                                <Typography variant="caption" color="text.secondary">
                                    创建时间
                                </Typography>
                                <Typography variant="body2">
                                    {feed.created_at ? new Date(feed.created_at).toLocaleDateString('zh-CN') : '未知'}
                                </Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="text.secondary">
                                    最后更新
                                </Typography>
                                <Typography variant="body2">
                                    {feed.last_updated ? new Date(feed.last_updated).toLocaleDateString('zh-CN') : '从未更新'}
                                </Typography>
                            </Box>
                        </Box>
                    </Box>
                </Box>
            </DialogContent>

            <DialogActions sx={{ px: 3, pb: 3 }}>
                <Button onClick={handleClose} disabled={loading}>
                    取消
                </Button>
                <Button
                    variant="contained"
                    onClick={handleSubmit}
                    disabled={loading || !formData.name.trim() || !formData.url.trim()}
                    startIcon={loading ? <CircularProgress size={16} /> : null}
                >
                    {loading ? '保存中...' : '保存更改'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default EditFeedDialog;