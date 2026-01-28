import React, { useState, useContext, useMemo } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    Chip,
    Grid,
    Link,
    CircularProgress,
    Divider,
    Stack,
    Card,
    CardContent,
    IconButton,
    Collapse,
    useTheme,
    useMediaQuery,
    FormControl,
    Select,
    MenuItem,
    Fade
} from '@mui/material';
import {
    OpenInNew as OpenInNewIcon,
    Translate as TranslateIcon,
    Bookmark as BookmarkIcon,
    BookmarkBorder as BookmarkBorderIcon,
    CheckCircle as CheckCircleIcon,
    RadioButtonUnchecked as RadioButtonUncheckedIcon,
    Science as ScienceIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
    Settings as SettingsIcon,
    Download as DownloadIcon,
    PictureAsPdf as PictureAsPdfIcon
} from '@mui/icons-material';

import { PaperContext } from '../contexts/PaperContext.jsx';
import { TaskContext } from '../contexts/TaskContext.jsx';
import { formatDate } from '../utils/dateUtils.jsx';
import { LAYOUT_CONSTANTS } from '../constants/layout.js';
import { useNotification } from './NotificationProvider.jsx';
import apiClient from '../services/apiClient.jsx';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function PaperDetail({ paper: propPaper }) {
    const theme = useTheme(); // 获取MUI主题对象
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD)); // 检测移动端
    const isMediumOrSmaller = useMediaQuery(theme.breakpoints.down('md')); // 检测中等屏幕或更小
    
    // 从localStorage获取阅读设置
    const [readingMode, setReadingMode] = useState(() => {
        return localStorage.getItem('paperDetail_readingMode') === 'true';
    });
    const [fontSize, setFontSize] = useState(() => {
        return localStorage.getItem('paperDetail_fontSize') || 'medium';
    });
    const [fontFamily, setFontFamily] = useState(() => {
        return localStorage.getItem('paperDetail_fontFamily') || 'system';
    });
    const {
        currentPaper,
        togglePaperStatus,
        translateAbstract,
        loading,
        paperLoading,
        handleAddToReadLater,
        handleRemoveFromReadLater
    } = useContext(PaperContext);

    // 使用props传入的paper或者context中的currentPaper
    const paper = propPaper || currentPaper;
    
    // 用于控制内容显示的状态
    const [showContent, setShowContent] = React.useState(!!paper);
    
    // 当 paper 改变时，控制过渡效果
    React.useEffect(() => {
        if (paper && !paperLoading) {
            // 延迟一点显示内容，确保加载状态正确切换
            const timer = setTimeout(() => setShowContent(true), 50);
            return () => clearTimeout(timer);
        } else {
            setShowContent(false);
        }
    }, [paper?.id, paperLoading]);


    const {
        createAnalysisTask,
        loading: taskLoading
    } = useContext(TaskContext);

    const { showNotification } = useNotification();

    // 字体映射函数
    const getFontFamilyCSS = (family) => {
        const fontMap = {
            'system': '"Times New Roman", "Georgia", "DejaVu Serif", serif',
            'song': '"Songti SC", "SimSun", "NSimSun", "STSong", serif',
            'kai': '"Kaiti SC", "KaiTi", "STKaiti", cursive',
            'hei': '"Heiti SC", "SimHei", "STHeiti", sans-serif',
            'ping': '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif'
        };
        return fontMap[family] || fontMap.system;
    };

    // 缓存复杂的样式对象避免重复计算
    const buttonGridStyles = useMemo(() => ({
        display: 'grid',
        gridTemplateColumns: isMobile ? 'repeat(5, 1fr)' : 'repeat(auto-fit, minmax(80px, 1fr))',
        gap: isMobile ? 0.25 : 0.5,
        mb: { xs: 1.5, md: 2 },
        '& .MuiButton-root': {
            minWidth: 'auto',
            px: isMobile ? 0.5 : 1.5,
            py: 0.5,
            fontSize: '0.75rem',
            height: 32,
            '& .MuiSvgIcon-root': {
                fontSize: isMobile ? '0.9rem' : '1rem'
            },
            ...(isMediumOrSmaller && {
                '& .MuiButton-startIcon': {
                    margin: 0
                }
            })
        }
    }), [isMobile, isMediumOrSmaller]);

    // 缓存摘要样式对象
    const abstractStyles = useMemo(() => ({
        fontSize: {
            xs: fontSize === 'small' ? '0.8rem' : fontSize === 'large' ? '0.95rem' : '0.85rem',
            sm: fontSize === 'small' ? '0.85rem' : fontSize === 'large' ? '1.05rem' : '0.9rem',
            md: fontSize === 'small' ? '0.9rem' : fontSize === 'large' ? '1.1rem' : '1rem'
        },
        lineHeight: { xs: 1.6, sm: 1.7 },
        textAlign: 'justify',
        p: { xs: 1.5, sm: 2, md: 2.5 },
        background: readingMode 
            ? `linear-gradient(135deg, ${theme.palette.success.main}08 0%, ${theme.palette.success.main}12 100%)`
            : `linear-gradient(135deg, ${theme.palette.primary.main}08 0%, ${theme.palette.primary.main}12 100%)`,
        border: readingMode ? `1px solid ${theme.palette.success.light}` : `1px solid ${theme.palette.divider}`,
        boxShadow: `0px 2px 8px ${theme.palette.primary.main}08`,
        borderRadius: 2,
        letterSpacing: '0.02em',
        wordBreak: 'break-word',
        hyphens: 'auto',
        fontFamily: getFontFamilyCSS(fontFamily),
        '& p': {
            textIndent: '2em',
            marginBottom: '1em'
        },
        color: readingMode ? '#2d3436' : 'inherit',
        '&::selection': {
            backgroundColor: 'primary.light',
            color: 'primary.contrastText'
        },
        ...(paper.isLoadingDetails && {
            opacity: 0.7,
            transition: 'opacity 0.3s ease-in-out'
        })
    }), [fontSize, readingMode, theme, fontFamily, paper.isLoadingDetails]);

    const [translating, setTranslating] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [showAnalysis, setShowAnalysis] = useState(false);
    const [showReadingSettings, setShowReadingSettings] = useState(false);
    const [showPaperInfo, setShowPaperInfo] = useState(false);

    // 保存阅读设置到localStorage
    const updateReadingMode = (mode) => {
        setReadingMode(mode);
        localStorage.setItem('paperDetail_readingMode', mode.toString());
    };

    // 识别IEEE论文并提取article_number
    const extractIEEEArticleNumber = (paper) => {
        if (!paper) return null;
        
        // 从DOI中提取article_number (IEEE DOI格式: 10.1109/XXX.2023.1234567)
        if (paper.doi && paper.doi.includes('10.1109')) {
            const parts = paper.doi.split('.');
            if (parts.length >= 3) {
                return parts[parts.length - 1]; // 取最后一部分作为article_number
            }
        }
        
        // 从URL中提取article_number (IEEE URL通常包含article number)
        if (paper.url && paper.url.includes('ieee')) {
            const urlMatch = paper.url.match(/(?:document|arnumber)\/(\d+)/i);
            if (urlMatch) {
                return urlMatch[1];
            }
        }
        
        // 如果有直接的ieee_article_number字段
        if (paper.ieee_article_number) {
            return paper.ieee_article_number;
        }
        
        return null;
    };

    // 判断是否为IEEE论文
    const isIEEEPaper = (paper) => {
        if (!paper) return false;
        return (paper.doi && paper.doi.includes('10.1109')) || 
               (paper.url && paper.url.includes('ieee')) ||
               paper.ieee_article_number;
    };

    // 处理PDF下载
    const handleDownloadPdf = async () => {
        if (!paper || !paper.id || downloading) return;

        const articleNumber = extractIEEEArticleNumber(paper);
        if (!articleNumber) {
            showNotification('无法从论文中提取IEEE article number，可能不是IEEE论文', {
                severity: 'warning',
                title: '下载失败'
            });
            return;
        }

        setDownloading(true);
        
        showNotification('PDF下载任务已创建，正在后台处理...', {
            severity: 'info',
            title: '开始下载',
            autoHideDuration: 3000
        });

        try {
            const result = await apiClient.downloadPdfAsync(paper.id, articleNumber, 5);
            if (result.success) {
                showNotification(
                    `PDF下载任务已成功创建！
                    
                    任务ID: ${result.task_id || '未知'}
                    任务类型: ${result.task_type || 'pdf_download_only'}
                    
                    您可以在任务页面查看下载进度。`, 
                    {
                        severity: 'success',
                        title: '📥 仅下载PDF任务创建成功',
                        autoHideDuration: 7000
                    }
                );
            } else {
                showNotification(result.error || result.message || '创建下载任务失败', {
                    severity: 'error',
                    title: '下载失败'
                });
            }
        } catch (error) {
            showNotification(`下载失败: ${error.message}`, {
                severity: 'error',
                title: '下载错误'
            });
        } finally {
            setDownloading(false);
        }
    };

    const updateFontSize = (size) => {
        setFontSize(size);
        localStorage.setItem('paperDetail_fontSize', size);
    };

    const updateFontFamily = (family) => {
        setFontFamily(family);
        localStorage.setItem('paperDetail_fontFamily', family);
    };

    // 字体映射函数已移动到上面

    const handleToggleStatus = () => {
        if (paper && paper.id && paper.status) {
            togglePaperStatus(paper.id, paper.status);
        }
    };

    const handleTranslate = async () => {
        if (!paper || !paper.id) return;
        
        setTranslating(true);
        try {
            await translateAbstract(paper.id);
        } finally {
            setTranslating(false);
        }
    };

    const handleToggleReadLater = () => {
        if (!paper || !paper.id) return;
        
        // 直接使用 paper prop 中已包含的 is_marked 状态
        if (paper.is_marked) {
            handleRemoveFromReadLater(paper.id);
        } else {
            handleAddToReadLater(paper.id);
        }
    };

    const handleCreateAnalysis = async () => {
        if (paper && paper.id) {
            await createAnalysisTask(paper.id);
        }
    };

    // 解析作者字符串为数组
    const parseAuthors = (authorsString) => {
        if (!authorsString) return [];
        return authorsString.split(',').map(author => author.trim()).filter(author => author.length > 0);
    };

    // 渲染作者列表
    const renderAuthors = (authorsString) => {
        const authors = parseAuthors(authorsString);
        if (authors.length === 0) return null;

        return (
            <Box sx={{ mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                    作者
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {authors.map((author, index) => (
                        <Chip
                            key={index}
                            label={author}
                            size="small"
                            variant="outlined"
                            sx={{
                                height: 24,
                                fontSize: '0.7rem',
                                background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main}08 0%, ${theme.palette.primary.main}15 100%)`,
                                borderColor: (theme) => `${theme.palette.primary.main}30`,
                                color: (theme) => theme.palette.primary.main,
                                '& .MuiChip-label': {
                                    px: 1,
                                    py: 0
                                },
                                '&:hover': {
                                    background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main}12 0%, ${theme.palette.primary.main}20 100%)`,
                                    transform: 'translateY(-1px)',
                                    boxShadow: (theme) => `0px 4px 8px ${theme.palette.primary.main}15`
                                },
                                transition: 'all 0.2s ease'
                            }}
                        />
                    ))}
                </Box>
            </Box>
        );
    };

    // 渲染简单元数据项
    const renderMetaItem = (label, value, isLink = false) => {
        if (!value) return null;

        return (
            <Box sx={{ mb: 1 }}>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                    {label}
                </Typography>
                {isLink ? (
                    <Link
                        href={value}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ 
                            wordBreak: 'break-all',
                            fontSize: '0.85rem'
                        }}
                    >
                        {value}
                    </Link>
                ) : (
                    <Typography variant="body2" sx={{ fontSize: '0.85rem', lineHeight: 1.4 }}>
                        {value}
                    </Typography>
                )}
            </Box>
        );
    };

    const renderAnalysisSection = () => {
        if (!paper.analysis_result) return null;

        return (
            <Card sx={{ mt: 3 }}>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <ScienceIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6" sx={{ flexGrow: 1 }}>
                            AI深度分析
                        </Typography>
                        {paper.analysis_task_status && (
                            <Chip
                                label={getTaskStatusText(paper.analysis_task_status)}
                                color={getTaskStatusColor(paper.analysis_task_status)}
                                size="small"
                            />
                        )}
                        <IconButton
                            onClick={() => setShowAnalysis(!showAnalysis)}
                            size="small"
                        >
                            {showAnalysis ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                    </Box>

                    <Collapse in={showAnalysis}>
                        {!paper.analysis_result && (
                            <Box sx={{ mb: 2 }}>
                                {renderTaskProgress(paper.analysis_task_status)}
                            </Box>
                        )}

                        {paper.analysis_result && (
                            <Box>
                                <Box
                                    sx={{
                                        p: 1,
                                        background: `linear-gradient(135deg, ${theme.palette.info.main}08 0%, ${theme.palette.info.main}12 100%)`,
                                        border: `1px solid ${theme.palette.info.light}30`,
                                        boxShadow: `0px 2px 6px ${theme.palette.info.main}06`,
                                        borderRadius: 1,
                                        // 以下样式确保 Markdown 渲染效果与MUI主题一致
                                        '& h1': { ...theme.typography.h4, mb: 1 },
                                        '& h2': { ...theme.typography.h5, mt: 1, mb: 1 },
                                        '& h3': { ...theme.typography.h6, mt: 2, mb: 1 },
                                        '& p': { ...theme.typography.body1, lineHeight: 1.4, mb: 1.5 },
                                        '& ul, & ol': { pl: 2.5, ...theme.typography.body1 },
                                        '& li': { mb: 0.5 },
                                        '& code': {
                                            backgroundColor: theme.palette.grey[200],
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            fontFamily: 'monospace',
                                            fontSize: '0.875rem'
                                        },
                                        '& pre > code': {
                                            display: 'block',
                                            whiteSpace: 'pre-wrap',
                                            wordBreak: 'break-all',
                                        },
                                        '& blockquote': {
                                            borderLeft: `4px solid ${theme.palette.grey[300]}`,
                                            pl: 2,
                                            ml: 0,
                                            color: theme.palette.text.secondary
                                        }
                                    }}
                                >
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {paper.analysis_result}
                                    </ReactMarkdown>
                                </Box>

                                {paper.pdf_path && (
                                    <Box sx={{ mt: 2 }}>
                                        <Button
                                            variant="contained"
                                            size="small"
                                            href={`/${paper.pdf_path}`}
                                            target="_blank"
                                            startIcon={<PictureAsPdfIcon />}
                                            sx={{
                                                backgroundColor: 'success.main',
                                                color: 'white',
                                                '&:hover': {
                                                    backgroundColor: 'success.dark',
                                                    transform: 'translateY(-1px)',
                                                    boxShadow: '0px 4px 12px rgba(0,0,0,0.15)',
                                                },
                                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                                            }}
                                        >
                                            查看PDF原文
                                        </Button>
                                    </Box>
                                )}
                            </Box>
                        )}
                    </Collapse>
                </CardContent>
            </Card>
        );
    };

    const renderTaskProgress = (task) => {
        const progress = task.progress || 0;

        return (
            <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {getProgressText(task.status, progress)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {progress}%
                    </Typography>
                </Box>

                <Box sx={{
                    width: '100%',
                    height: 8,
                    bgcolor: 'grey.200',
                    borderRadius: 1,
                    overflow: 'hidden'
                }}>
                    <Box
                        sx={{
                            width: `${progress}%`,
                            height: '100%',
                            bgcolor: 'primary.main',
                            transition: 'width 0.3s ease',
                        }}
                    />
                </Box>

                {task.error_message && (
                    <Typography
                        variant="body2"
                        color="error"
                        sx={{ mt: 1, p: 1, bgcolor: 'error.lighter', borderRadius: 1 }}
                    >
                        错误: {task.error_message}
                    </Typography>
                )}
            </Box>
        );
    };

    const getTaskStatusText = (status) => {
        const statusMap = {
            'pending': '等待中',
            'in_progress': '处理中',
            'downloading': '下载PDF',
            'analyzing': 'AI分析中',
            'completed': '分析完成',
            'failed': '分析失败',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    };

    const getTaskStatusColor = (status) => {
        const colorMap = {
            'pending': 'default',
            'in_progress': 'info',
            'downloading': 'info',
            'analyzing': 'info',
            'completed': 'success',
            'failed': 'error',
            'cancelled': 'default'
        };
        return colorMap[status] || 'default';
    };

    const getProgressText = (status, progress) => {
        const textMap = {
            'pending': '任务已创建，等待处理...',
            'in_progress': '任务开始处理...',
            'downloading': '正在通过Agent下载PDF文件...',
            'analyzing': 'DeepSeek正在深度分析论文内容...'
        };

        let text = textMap[status] || '处理中...';
        if (progress && progress > 0) {
            text += ` (${progress}%)`;
        }
        return text;
    };

    // 如果没有paper数据，显示加载状态或提示
    // 如果正在加载论文，显示骨架屏
    if (paperLoading) {
        return (
            <Box sx={{ p: 3 }}>
                <Fade in={true}>
                    <Box>
                        {/* 标题骨架 - 使用静态渐变代替动画 */}
                        <Box sx={{ 
                            height: 32, 
                            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
                            borderRadius: 1, 
                            mb: 2
                        }} />
                        <Box sx={{ 
                            height: 24, 
                            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
                            borderRadius: 1, 
                            mb: 3,
                            width: '70%'
                        }} />
                        
                        {/* 内容骨架 - 使用不同透明度模拟延迟效果 */}
                        {[...Array(6)].map((_, i) => (
                            <Box key={i} sx={{ 
                                height: 16, 
                                background: `linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)`,
                                borderRadius: 1, 
                                mb: 1,
                                width: i % 3 === 0 ? '90%' : i % 3 === 1 ? '85%' : '95%',
                                opacity: 1 - (i * 0.05) // 渐进透明度代替动画延迟
                            }} />
                        ))}
                    </Box>
                </Fade>
            </Box>
        );
    }

    if (!paper) {
        return (
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                height: '100%',
                p: 3
            }}>
                <Typography variant="body1" color="text.secondary">
                    请选择一篇论文查看详情
                </Typography>
            </Box>
        );
    }

    // 如果是加载状态的临时paper对象，显示加载界面
    if (paper.title === '正在加载中...' || paper.error || !paper.abstract) {
        return (
            <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'center', 
                alignItems: 'center', 
                height: '100%',
                p: 3
            }}>
                {paper.error ? (
                    <>
                        <Typography variant="h6" color="error" gutterBottom>
                            加载失败
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {paper.error}
                        </Typography>
                    </>
                ) : (
                    <>
                        <Box sx={{ 
                        width: 40, 
                        height: 40, 
                        borderRadius: '50%', 
                        bgcolor: 'primary.main', 
                        opacity: 0.6,
                        mb: 2,
                        mx: 'auto'
                    }} />
                        <Typography variant="body1" color="text.secondary">
                            正在加载论文详情...
                        </Typography>
                    </>
                )}
            </Box>
        );
    }

    return (
        <Box key={paper.id} sx={{ opacity: showContent ? 1 : 0 }}>
            <Box sx={{ 
                p: { xs: 1.5, md: 2 },
                minHeight: '100%',
                WebkitOverflowScrolling: 'touch',
                // 添加细微的过渡效果
                transition: 'all 0.2s ease-in-out'
            }}>
                {/* 论文标题 */}
                <Typography variant="h5" sx={{ 
                    mb: { xs: 2, md: 3 },
                    fontWeight: 600, 
                    lineHeight: 1.1,
                    fontSize: { xs: '1.25rem', md: '1.5rem' },
                    // 添加加载状态效果（静态渐变代替动画）
                    ...(paper.isLoadingDetails && {
                        background: 'linear-gradient(90deg, transparent 25%, rgba(0,0,0,0.08) 50%, transparent 75%)',
                        opacity: 0.7
                    })
                }}>
                    {paper.title}
                </Typography>

            {/* 操作按钮 */}
            <Box sx={buttonGridStyles}>
                <Button
                    variant={paper.status === 'read' ? 'contained' : 'outlined'}
                    color={paper.status === 'read' ? 'success' : 'primary'}
                    size="small"
                    startIcon={paper.status === 'read' ? <CheckCircleIcon /> : <RadioButtonUncheckedIcon />}
                    onClick={handleToggleStatus}
                    disabled={loading || !paper.status}
                >
                    {isMediumOrSmaller ? '' : (paper.status === 'read' ? '已读' : '标已读')}
                </Button>

                <Button
                    variant={paper.is_marked ? 'contained' : 'outlined'}
                    color={paper.is_marked ? 'secondary' : 'primary'}
                    size="small"
                    startIcon={paper.is_marked ? <BookmarkIcon /> : <BookmarkBorderIcon />}
                    onClick={handleToggleReadLater}
                >
                    {isMediumOrSmaller ? '' : (paper.is_marked ? '已收藏' : '稍后读')}
                </Button>

                {paper.abstract && (
                    <Button
                        variant="outlined"
                        size="small"
                        startIcon={translating ? <Box sx={{ width: 14, height: 14, bgcolor: 'primary.main', borderRadius: '50%', opacity: 0.6 }} /> : <TranslateIcon />}
                        onClick={handleTranslate}
                        disabled={translating || loading}
                    >
                        {isMediumOrSmaller ? '' : (paper.abstract_cn ? '重译' : '翻译')}
                    </Button>
                )}

                {!paper.analysis_task && !paper.analysis_result && (
                    <Button
                        variant="outlined"
                        color="secondary"
                        size="small"
                        startIcon={taskLoading ? <Box sx={{ width: 14, height: 14, bgcolor: 'secondary.main', borderRadius: '50%', opacity: 0.6 }} /> : <ScienceIcon />}
                        onClick={handleCreateAnalysis}
                        disabled={taskLoading}
                    >
                        {isMediumOrSmaller ? '' : '分析'}
                    </Button>
                )}

                {paper.url && (
                    <Button
                        variant="outlined"
                        size="small"
                        startIcon={<OpenInNewIcon />}
                        href={paper.url}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {isMediumOrSmaller ? '' : '原文'}
                    </Button>
                )}

                {/* 如果没有PDF但是IEEE论文，显示下载按钮 */}
                {!paper.pdf_path && isIEEEPaper(paper) && (
                    <Button
                        variant="outlined"
                        color="info"
                        size="small"
                        startIcon={downloading ? <Box sx={{ width: 14, height: 14, bgcolor: 'info.main', borderRadius: '50%', opacity: 0.6 }} /> : <DownloadIcon />}
                        onClick={handleDownloadPdf}
                        disabled={downloading}
                        sx={{
                            borderColor: 'info.main',
                            color: 'info.main',
                            '&:hover': {
                                backgroundColor: 'info.light',
                                borderColor: 'info.main',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(33, 150, 243, 0.2)',
                            },
                            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                        }}
                    >
                        {isMediumOrSmaller ? '' : (downloading ? '下载中' : '下载PDF')}
                    </Button>
                )}

                {paper.pdf_path && (
                    <Button
                        variant="contained"
                        size="small"
                        startIcon={<PictureAsPdfIcon />}
                        href={`/${paper.pdf_path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{
                            backgroundColor: 'success.main',
                            color: 'white',
                            '&:hover': {
                                backgroundColor: 'success.dark',
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 12px rgba(46, 125, 50, 0.3)',
                            },
                            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                        }}
                    >
                        {isMediumOrSmaller ? '' : 'PDF'}
                    </Button>
                )}

                {paper.doi && (
                    <Button
                        variant="outlined"
                        size="small"
                        startIcon={<OpenInNewIcon />}
                        href={`https://doi.org/${paper.doi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {isMediumOrSmaller ? '' : 'DOI'}
                    </Button>
                )}

            </Box>

            {/* --- 核心变更：根据 isLoadingDetails 决定显示内容还是加载动画 --- */}
            {paper.isLoadingDetails ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh' }}>
                    <Box sx={{ 
                        width: 40, 
                        height: 40, 
                        borderRadius: '50%', 
                        bgcolor: 'primary.main', 
                        opacity: 0.6
                    }} />
                </Box>
            ) : (
                <>
                {/* 论文元信息 */}
                <Paper variant="outlined" sx={{ mb: 2 }}>
                    <Box 
                        sx={{ 
                            p: 1.5, 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                            minHeight: '48px'
                        }}
                        onClick={() => setShowPaperInfo(!showPaperInfo)}
                    >
                        <Typography variant="caption" color="text.secondary">
                            文章信息
                        </Typography>
                        <IconButton size="small">
                            {showPaperInfo ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                    </Box>
                    
                    <Collapse in={showPaperInfo}>
                        <Box sx={{ px: 1.5, pb: 1.5 }}>
                            {/* 作者信息 */}
                            {renderAuthors(paper.authors || paper.author)}
                            
                            {/* 其他元信息 */}
                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                                {renderMetaItem('期刊', paper.journal)}
                                {renderMetaItem('发布时间', formatDate(paper.published_date || paper.published_at))}
                            </Box>
                            
                            {/* DOI */}
                            {paper.doi && renderMetaItem('DOI', `https://doi.org/${paper.doi}`, true)}
                        </Box>
                    </Collapse>
                </Paper>

                {/* 阅读设置工具栏 */}
                <Paper variant="outlined" sx={{ mb: { xs: 1.5, md: 2 } }}>
                    <Box 
                        sx={{ 
                            p: 1.5, 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'space-between',
                            cursor: isMobile ? 'pointer' : 'default',
                            minHeight: '48px'
                        }}
                        onClick={isMobile ? () => setShowReadingSettings(!showReadingSettings) : undefined}
                    >
                        <Typography variant="caption" color="text.secondary">
                            阅读设置
                        </Typography>
                        {isMobile && (
                            <IconButton size="small">
                                {showReadingSettings ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                        )}
                    </Box>
                    
                    <Collapse in={!isMobile || showReadingSettings}>
                        <Box sx={{ 
                            px: 1.5, 
                            pb: 1.5,
                            pt: isMobile ? 0 : 0,
                            display: 'grid', 
                            gridTemplateColumns: isMobile ? '1fr 1fr 1fr' : 'auto auto 1fr',
                            gap: 1.5,
                            alignItems: 'center'
                        }}>
                            {/* 护眼模式 */}
                            <Button
                                size="small"
                                variant={readingMode ? 'contained' : 'outlined'}
                                onClick={() => updateReadingMode(!readingMode)}
                                sx={{ 
                                    fontSize: '0.7rem', 
                                    py: 0.25, 
                                    px: 1,
                                    minWidth: 'auto',
                                    width: '100%'
                                }}
                            >
                                护眼
                            </Button>
                            
                            {/* 字号设置 */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Typography variant="caption" sx={{ fontSize: '0.7rem', whiteSpace: 'nowrap' }}>字号:</Typography>
                                <Box sx={{ display: 'flex', gap: 0.25 }}>
                                    <Button
                                        size="small"
                                        variant={fontSize === 'small' ? 'contained' : 'outlined'}
                                        onClick={() => updateFontSize('small')}
                                        sx={{ fontSize: '0.65rem', py: 0.25, px: 0.5, minWidth: 'auto' }}
                                    >
                                        小
                                    </Button>
                                    <Button
                                        size="small"
                                        variant={fontSize === 'medium' ? 'contained' : 'outlined'}
                                        onClick={() => updateFontSize('medium')}
                                        sx={{ fontSize: '0.65rem', py: 0.25, px: 0.5, minWidth: 'auto' }}
                                    >
                                        中
                                    </Button>
                                    <Button
                                        size="small"
                                        variant={fontSize === 'large' ? 'contained' : 'outlined'}
                                        onClick={() => updateFontSize('large')}
                                        sx={{ fontSize: '0.65rem', py: 0.25, px: 0.5, minWidth: 'auto' }}
                                    >
                                        大
                                    </Button>
                                </Box>
                            </Box>

                            {/* 字体设置 */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Typography variant="caption" sx={{ fontSize: '0.7rem', whiteSpace: 'nowrap' }}>字体:</Typography>
                                <FormControl size="small" sx={{ minWidth: 80, flex: 1 }}>
                                    <Select
                                        value={fontFamily}
                                        onChange={(e) => updateFontFamily(e.target.value)}
                                        sx={{
                                            fontSize: '0.7rem',
                                            height: 28,
                                            '& .MuiSelect-select': {
                                                py: 0.25,
                                                px: 0.75
                                            }
                                        }}
                                    >
                                        <MenuItem value="system" sx={{ fontSize: '0.7rem' }}>系统</MenuItem>
                                        <MenuItem value="song" sx={{ fontSize: '0.7rem' }}>宋体</MenuItem>
                                        <MenuItem value="kai" sx={{ fontSize: '0.7rem' }}>楷体</MenuItem>
                                        <MenuItem value="hei" sx={{ fontSize: '0.7rem' }}>黑体</MenuItem>
                                        <MenuItem value="ping" sx={{ fontSize: '0.7rem' }}>苹方</MenuItem>
                                    </Select>
                                </FormControl>
                            </Box>
                        </Box>
                    </Collapse>
                </Paper>

                {/* 摘要部分 */}
                {paper.abstract && (
                    <Box sx={{ mb: { xs: 2, md: 3 } }}>
                        <Typography variant="h6" sx={{ 
                            mb: { xs: 1.5, md: 2 }, 
                            fontWeight: 600, 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 1,
                            fontSize: { xs: '1rem', md: '1.25rem' }
                        }}>
                            {isMobile ? '摘要' : '📄 摘要'}
                            {!isMobile && (
                                <Chip 
                                    label={`${paper.abstract.length} 字符`} 
                                    size="small" 
                                    variant="outlined"
                                    sx={{ 
                                        height: 20, 
                                        fontSize: '0.65rem',
                                        background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}08 0%, ${theme.palette.info.main}15 100%)`,
                                        borderColor: (theme) => `${theme.palette.info.main}30`,
                                        color: (theme) => theme.palette.info.main,
                                        '&:hover': {
                                            background: (theme) => `linear-gradient(135deg, ${theme.palette.info.main}12 0%, ${theme.palette.info.main}20 100%)`,
                                            transform: 'translateY(-1px)',
                                            boxShadow: (theme) => `0px 2px 6px ${theme.palette.info.main}15`
                                        },
                                        transition: 'all 0.2s ease'
                                    }}
                                />
                            )}
                        </Typography>
                        <Typography
                            variant="body1"
                            sx={abstractStyles}
                        >
                            {paper.abstract}
                            {paper.isLoadingDetails && (
                                <Box sx={{ 
                                    display: 'inline-flex', 
                                    alignItems: 'center', 
                                    ml: 1,
                                    opacity: 0.6 
                                }}>
                                    <Box sx={{ 
                                        width: 14, 
                                        height: 14, 
                                        borderRadius: '50%', 
                                        bgcolor: 'primary.main', 
                                        opacity: 0.6,
                                        ml: 1
                                    }} />
                                </Box>
                            )}
                        </Typography>
                    </Box>
                )}

                {/* 中文翻译 */}
                {paper.abstract_cn && (
                    <Box sx={{ mb: { xs: 2, md: 3 } }}>
                        <Typography variant="h6" sx={{ 
                            mb: { xs: 1.5, md: 2 }, 
                            fontWeight: 600, 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 1,
                            fontSize: { xs: '1rem', md: '1.25rem' }
                        }}>
                            {isMobile ? '中文翻译' : '🇨🇳 中文翻译'}
                            {!isMobile && (
                                <Chip 
                                    label="AI翻译" 
                                    size="small" 
                                    color="primary"
                                    variant="outlined"
                                    sx={{ 
                                        height: 20, 
                                        fontSize: '0.65rem',
                                        background: (theme) => `linear-gradient(135deg, ${theme.palette.secondary.main}08 0%, ${theme.palette.secondary.main}15 100%)`,
                                        borderColor: (theme) => `${theme.palette.secondary.main}30`,
                                        color: (theme) => theme.palette.secondary.main,
                                        '&:hover': {
                                            background: (theme) => `linear-gradient(135deg, ${theme.palette.secondary.main}12 0%, ${theme.palette.secondary.main}20 100%)`,
                                            transform: 'translateY(-1px)',
                                            boxShadow: (theme) => `0px 2px 6px ${theme.palette.secondary.main}15`
                                        },
                                        transition: 'all 0.2s ease'
                                    }}
                                />
                            )}
                        </Typography>
                        <Typography
                            variant="body1"
                            sx={{
                                // 动态字体大小
                                fontSize: {
                                    xs: fontSize === 'small' ? '0.85rem' : fontSize === 'large' ? '1rem' : '0.9rem',
                                    sm: fontSize === 'small' ? '0.9rem' : fontSize === 'large' ? '1.05rem' : '0.95rem',
                                    md: fontSize === 'small' ? '0.95rem' : fontSize === 'large' ? '1.1rem' : '1rem'
                                },
                                lineHeight: 1.8,
                                textAlign: 'justify',
                                p: { xs: 1.5, sm: 2, md: 2.5 },
                                // 护眼模式背景
                                background: readingMode 
                                    ? `linear-gradient(135deg, ${theme.palette.info.main}08 0%, ${theme.palette.info.main}15 100%)`
                                    : `linear-gradient(135deg, ${theme.palette.secondary.main}08 0%, ${theme.palette.secondary.main}15 100%)`,
                                border: readingMode ? `1px solid ${theme.palette.info.light}` : `1px solid ${theme.palette.secondary.light}40`,
                                boxShadow: `0px 2px 8px ${theme.palette.secondary.main}08`,
                                borderRadius: 2,
                                // 中文阅读优化
                                fontFamily: getFontFamilyCSS(fontFamily),
                                letterSpacing: '0.05em',
                                // 护眼模式文字颜色
                                color: readingMode ? '#2d3436' : 'inherit',
                                // 段落样式
                                '& p': {
                                    textIndent: '2em',
                                    marginBottom: '1em'
                                }
                            }}
                        >
                            {paper.abstract_cn}
                        </Typography>
                    </Box>
                )}

                {/* AI分析结果 */}
                {renderAnalysisSection()}

                {!paper.abstract && (
                    <Box sx={{
                        textAlign: 'center',
                        py: 6,
                        color: 'text.secondary'
                    }}>
                        <Typography>暂无摘要</Typography>
                    </Box>
                )}

            </>
            )}
        </Box>
        </Box>
    );
}

export default PaperDetail;