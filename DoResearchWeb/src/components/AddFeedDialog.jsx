import React, { useState, useContext } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Box,
    Typography,
    List,
    ListItem,
    ListItemText,
    Paper,
    Alert,
    CircularProgress
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

import { PaperContext } from '../contexts/PaperContext';

const helpInfo = {
    title: "API说明",
    description: "API应该返回JSON格式的论文数组，每个论文对象应包含以下字段：",
    fields: [
        { name: 'title', description: '论文标题 (必需)', required: true },
        { name: 'abstract', description: '摘要' },
        { name: 'journal', description: '期刊名称' },
        { name: 'authors', description: '作者' },
        { name: 'status', description: '状态 (read/unread)' },
        { name: 'url', description: '论文链接' },
        { name: 'doi', description: 'DOI' },
        { name: 'ieee_article_number', description: 'IEEE文章编号 (用于深度分析)' },
        { name: 'published_date', description: '发布日期' }
    ],
    testApi: "/api/test/papers"
};

function AddFeedDialog({ open, onClose }) {
    const { addFeed, loading } = useContext(PaperContext);

    const [formData, setFormData] = useState({
        name: '',
        url: '',
        journal: ''
    });

    const [errors, setErrors] = useState({});

    const handleChange = (field) => (event) => {
        setFormData(prev => ({
            ...prev,
            [field]: event.target.value
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
        if (!validateForm()) return;

        try {
            const result = await addFeed(formData);
            if (result.success) {
                handleClose();
            }
        } catch (error) {
            console.error('Failed to add feed:', error);
        }
    };

    const handleClose = () => {
        setFormData({ name: '', url: '', journal: '' });
        setErrors({});
        onClose();
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter' && !loading) {
            event.preventDefault();
            handleSubmit();
        }
    };

    const fillTestData = () => {
        setFormData({
            name: '测试论文库',
            url: '/api/test/papers',
            journal: 'Test Journal'
        });
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="md"
            fullWidth
            PaperProps={{
                sx: { minHeight: '500px' }
            }}
        >
            <DialogTitle sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                pb: 1
            }}>
                <Typography variant="h6" component="div">添加论文源</Typography>
                <Button
                    onClick={handleClose}
                    sx={{ minWidth: 'auto', p: 1 }}
                >
                    <CloseIcon />
                </Button>
            </DialogTitle>

            <DialogContent sx={{ pt: 2 }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {/* 表单部分 */}
                    <Box>
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
                        />
                    </Box>

                    {/* 快速填充测试数据 */}
                    <Alert
                        severity="info"
                        action={
                            <Button
                                size="small"
                                onClick={fillTestData}
                                sx={{ whiteSpace: 'nowrap' }}
                            >
                                使用测试数据
                            </Button>
                        }
                    >
                        想要快速体验？点击使用内置测试API
                    </Alert>

                    {/* 帮助信息 */}
                    <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            {helpInfo.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {helpInfo.description}
                        </Typography>

                        <List dense sx={{ py: 0 }}>
                            {helpInfo.fields.map((field, index) => (
                                <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                                    <ListItemText
                                        primary={
                                            <Typography variant="body2">
                                                <code style={{
                                                    backgroundColor: '#f5f5f5',
                                                    padding: '2px 6px',
                                                    borderRadius: '4px',
                                                    fontFamily: 'monospace'
                                                }}>
                                                    {field.name}
                                                </code>
                                                {field.required && (
                                                    <span style={{ color: '#d32f2f', marginLeft: '4px' }}>*</span>
                                                )}
                                                {' - ' + field.description}
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>

                        <Box sx={{ 
                            mt: 2, 
                            p: 1.5, 
                            background: (theme) => `linear-gradient(135deg, ${theme.palette.secondary.main}08 0%, ${theme.palette.secondary.main}12 100%)`,
                            border: (theme) => `1px solid ${theme.palette.secondary.light}30`,
                            borderRadius: 2,
                            boxShadow: (theme) => `0px 2px 6px ${theme.palette.secondary.main}06`
                        }}>
                            <Typography variant="caption" color="text.secondary">
                                <strong>测试API:</strong>
                                <code style={{
                                    backgroundColor: 'white',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    marginLeft: '8px',
                                    fontFamily: 'monospace'
                                }}>
                                    {helpInfo.testApi}
                                </code>
                            </Typography>
                        </Box>
                    </Paper>
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
                    {loading ? '添加中...' : '添加'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default AddFeedDialog;