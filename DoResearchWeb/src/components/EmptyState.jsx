import React from 'react';
import {
    Box,
    Typography,
    Button,
    Paper,
    useTheme,
    alpha,
} from '@mui/material';
import {
    LibraryBooks as LibraryBooksIcon,
    Search as SearchIcon,
    Add as AddIcon,
    Refresh as RefreshIcon,
    MenuBook as MenuBookIcon,
    Assignment as AssignmentIcon,
} from '@mui/icons-material';

const emptyStateConfigs = {
    papers: {
        icon: LibraryBooksIcon,
        title: '暂无论文',
        subtitle: '这里还没有任何论文',
        description: '添加RSS订阅或搜索论文来开始您的学术之旅',
        actionText: '添加订阅',
        secondaryActionText: '搜索论文',
    },
    feeds: {
        icon: MenuBookIcon,
        title: '暂无论文源',
        subtitle: '您还没有添加任何RSS订阅',
        description: '添加您关注的期刊或会议的RSS源，获取最新的学术动态',
        actionText: '添加订阅源',
    },
    subscriptions: {
        icon: MenuBookIcon,
        title: '暂无订阅',
        subtitle: '使用新订阅系统获取论文',
        description: '点击按钮开始添加智能订阅源',
        actionText: '添加订阅',
    },
    readlater: {
        icon: LibraryBooksIcon,
        title: '稍后阅读列表为空',
        subtitle: '您的待读列表是空的',
        description: '将感兴趣的论文添加到稍后阅读，建立您的知识库',
        actionText: '浏览论文',
        secondaryActionText: '搜索论文',
    },
    tasks: {
        icon: AssignmentIcon,
        title: '暂无研究任务',
        subtitle: '您还没有创建任何研究任务',
        description: '创建研究任务来深度分析论文，系统化您的学术研究',
        actionText: '创建任务',
    },
    search: {
        icon: SearchIcon,
        title: '开始搜索',
        subtitle: '输入关键词搜索相关论文',
        description: '使用高级搜索功能，找到您需要的学术资源',
        actionText: '高级搜索',
    },
    stats: {
        icon: LibraryBooksIcon,
        title: '暂无统计数据',
        subtitle: '开始阅读论文后会显示统计信息',
        description: '您的阅读习惯和学习进度将在这里可视化展示',
        actionText: '重新加载',
        secondaryActionText: '浏览论文',
    },
    error: {
        icon: RefreshIcon,
        title: '加载失败',
        subtitle: '数据加载遇到问题',
        description: '请检查网络连接或稍后重试',
        actionText: '重新加载',
    },
};

function EmptyState({ 
    type = 'papers', 
    onAction, 
    onSecondaryAction,
    customConfig = {},
    size = 'medium'
}) {
    const theme = useTheme();
    const config = { ...emptyStateConfigs[type], ...customConfig };
    const IconComponent = config.icon;

    const sizeConfig = {
        small: {
            iconSize: 64,
            titleVariant: 'h6',
            subtitleVariant: 'body1',
            descriptionVariant: 'body2',
            buttonSize: 'medium',
            spacing: 2,
        },
        medium: {
            iconSize: 96,
            titleVariant: 'h5',
            subtitleVariant: 'h6',
            descriptionVariant: 'body1',
            buttonSize: 'large',
            spacing: 3,
        },
        large: {
            iconSize: 128,
            titleVariant: 'h4',
            subtitleVariant: 'h5',
            descriptionVariant: 'h6',
            buttonSize: 'large',
            spacing: 4,
        },
    };

    const currentSize = sizeConfig[size];

    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: { xs: 300, md: 400 },
                textAlign: 'center',
                p: currentSize.spacing,
            }}
        >
            {/* 背景装饰 */}
            <Paper
                elevation={0}
                sx={{
                    position: 'relative',
                    p: currentSize.spacing * 2,
                    backgroundColor: alpha(theme.palette.primary.main, 0.02),
                    border: `2px dashed ${alpha(theme.palette.primary.main, 0.1)}`,
                    borderRadius: 4,
                    maxWidth: 480,
                    width: '100%',
                    overflow: 'hidden',
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: -50,
                        right: -50,
                        width: 100,
                        height: 100,
                        background: `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.05)} 0%, transparent 70%)`,
                        borderRadius: '50%',
                    },
                    '&::after': {
                        content: '""',
                        position: 'absolute',
                        bottom: -30,
                        left: -30,
                        width: 60,
                        height: 60,
                        background: `radial-gradient(circle, ${alpha(theme.palette.secondary.main, 0.05)} 0%, transparent 70%)`,
                        borderRadius: '50%',
                    },
                }}
            >
                {/* 图标 */}
                <Box
                    sx={{
                        mb: currentSize.spacing,
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    <Box
                        sx={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: currentSize.iconSize + 32,
                            height: currentSize.iconSize + 32,
                            borderRadius: '50%',
                            backgroundColor: alpha(theme.palette.primary.main, 0.08),
                            mb: 2,
                            animation: 'float 3s ease-in-out infinite',
                            '@keyframes float': {
                                '0%, 100%': {
                                    transform: 'translateY(0px)',
                                },
                                '50%': {
                                    transform: 'translateY(-10px)',
                                },
                            },
                        }}
                    >
                        <IconComponent
                            sx={{
                                fontSize: currentSize.iconSize,
                                color: theme.palette.primary.main,
                                opacity: 0.8,
                            }}
                        />
                    </Box>
                </Box>

                {/* 标题 */}
                <Typography
                    variant={currentSize.titleVariant}
                    sx={{
                        mb: 1,
                        fontWeight: 600,
                        color: 'text.primary',
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    {config.title}
                </Typography>

                {/* 副标题 */}
                <Typography
                    variant={currentSize.subtitleVariant}
                    sx={{
                        mb: 1.5,
                        color: 'text.secondary',
                        fontWeight: 500,
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    {config.subtitle}
                </Typography>

                {/* 描述 */}
                <Typography
                    variant={currentSize.descriptionVariant}
                    sx={{
                        mb: currentSize.spacing,
                        color: 'text.secondary',
                        maxWidth: 360,
                        lineHeight: 1.6,
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    {config.description}
                </Typography>

                {/* 操作按钮 */}
                <Box
                    sx={{
                        display: 'flex',
                        flexDirection: { xs: 'column', sm: 'row' },
                        gap: 1.5,
                        justifyContent: 'center',
                        alignItems: 'center',
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    {config.actionText && onAction && (
                        <Button
                            variant="contained"
                            size={currentSize.buttonSize}
                            onClick={onAction}
                            startIcon={type === 'error' ? <RefreshIcon /> : <AddIcon />}
                            sx={{
                                minWidth: { xs: 200, sm: 'auto' },
                                boxShadow: `0px 4px 12px ${alpha(theme.palette.primary.main, 0.3)}`,
                                '&:hover': {
                                    boxShadow: `0px 6px 16px ${alpha(theme.palette.primary.main, 0.4)}`,
                                    transform: 'translateY(-2px)',
                                },
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            }}
                        >
                            {config.actionText}
                        </Button>
                    )}

                    {config.secondaryActionText && onSecondaryAction && (
                        <Button
                            variant="outlined"
                            size={currentSize.buttonSize}
                            onClick={onSecondaryAction}
                            startIcon={<SearchIcon />}
                            sx={{
                                minWidth: { xs: 200, sm: 'auto' },
                                borderColor: alpha(theme.palette.primary.main, 0.3),
                                color: theme.palette.primary.main,
                                '&:hover': {
                                    borderColor: theme.palette.primary.main,
                                    backgroundColor: alpha(theme.palette.primary.main, 0.04),
                                    transform: 'translateY(-1px)',
                                },
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            }}
                        >
                            {config.secondaryActionText}
                        </Button>
                    )}
                </Box>
            </Paper>
        </Box>
    );
}

export default EmptyState;