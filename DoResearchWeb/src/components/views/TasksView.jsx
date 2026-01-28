import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Paper,
    Typography,
    Button,
    Chip,
    Grid,
    Card,
    CardContent,
    CircularProgress,
    LinearProgress,
    Stack,
    IconButton,
    Collapse,
    Alert,
    List,
    ListItem,
    ListItemText,
    Divider, 
    TableContainer, 
    Table, 
    TableHead, 
    TableRow, 
    TableCell, 
    TableBody,
    useTheme,
    useMediaQuery,
    Pagination,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    alpha
} from '@mui/material';
import {
    Assignment as TaskIcon,
    SmartToy as AgentIcon,
    Refresh as RefreshIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
    Cancel as CancelIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Schedule as ScheduleIcon,
    KeyboardArrowUp as KeyboardArrowUpIcon,
    KeyboardArrowDown as KeyboardArrowDownIcon,
    PlayArrow as PlayArrowIcon,
    Download as DownloadIcon,
    Search as SearchIcon,
    Psychology as PsychologyIcon,
    Translate as TranslateIcon,
    FilterList as FilterListIcon, TaskOutlined
} from '@mui/icons-material';

import { TaskContext } from '../../contexts/TaskContext.jsx';
import { PaperContext } from '../../contexts/PaperContext';
import apiClient from '../../services/apiClient.jsx';
import { formatDateTime, formatHeartbeatTime } from '../../utils/dateUtils.jsx';
import { LAYOUT_CONSTANTS } from '../../constants/layout.js';

// 任务类型配置
const TASK_TYPE_CONFIG = {
    pdf_download_only: { icon: '📥', label: '仅下载PDF', iconComponent: DownloadIcon },
    full_analysis: { icon: '🔍', label: '完整分析', iconComponent: SearchIcon },
    deep_analysis: { icon: '🧠', label: '深度分析', iconComponent: PsychologyIcon },
    pdf_download: { icon: '📄', label: 'PDF下载', iconComponent: DownloadIcon },
    translation: { icon: '🌐', label: '翻译任务', iconComponent: TranslateIcon }
};

function TasksView() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD));
    const navigate = useNavigate();
    
    const {
        tasks,
        agents,
        taskStats,
        loading,
        loadTasks,
        loadAgents,
        loadTaskStats,
        cancelTask,
        getTaskStatusText,
        getTaskStatusColor,
        getAgentStatusText,
        getAgentStatusColor,
        createAnalysisTask,
    } = useContext(TaskContext);

    const { setCurrentView, selectPaper, currentPaper, currentPaperId } = useContext(PaperContext);

    const [expandedTasks, setExpandedTasks] = useState(new Set());
    const [currentPage, setCurrentPage] = useState(1);
    const [taskTypeFilter, setTaskTypeFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [filteredTasks, setFilteredTasks] = useState([]);
    const itemsPerPage = 20; // 每页显示20个论文分组

    // 获取任务类型显示信息
    const getTaskTypeInfo = (task) => {
        const typeConfig = TASK_TYPE_CONFIG[task.task_type];
        if (typeConfig) {
            return {
                icon: typeConfig.icon,
                label: typeConfig.label,
                iconComponent: typeConfig.iconComponent
            };
        }
        
        // 使用后端返回的信息作为回退
        return {
            icon: task.task_type_icon || '📋',
            label: task.task_type_desc || task.task_type || '未知任务',
            iconComponent: TaskIcon
        };
    };

    useEffect(() => {
        setCurrentView('tasks');
    }, [setCurrentView]);

    useEffect(() => {
        loadAllData();
    }, []);

    const loadAllData = async () => {
        const taskOptions = {
            limit: 200,
            include_steps: false
        };
        
        if (statusFilter) taskOptions.status = statusFilter;
        if (taskTypeFilter) taskOptions.task_type = taskTypeFilter;
        
        try {
            const [tasksResult] = await Promise.all([
                apiClient.getTasks(taskOptions),
                loadAgents(),
                loadTaskStats()
            ]);
            
            setFilteredTasks(tasksResult || []);
        } catch (error) {
            console.error('Failed to load tasks:', error);
            setFilteredTasks([]);
        }
    };

    // 筛选器变更处理
    useEffect(() => {
        loadAllData();
    }, [statusFilter, taskTypeFilter]);

    const handleCancelTask = async (taskId) => {
        const result = await cancelTask(taskId);
        if (result.success) {
            // 刷新数据
            loadAllData();
        }
    };

    const toggleTaskExpansion = (taskId) => {
        const newExpanded = new Set(expandedTasks);
        if (newExpanded.has(taskId)) {
            newExpanded.delete(taskId);
        } else {
            newExpanded.add(taskId);
        }
        setExpandedTasks(newExpanded);
    };

    const handleNavigateToPaper = async (paperId) => {
        try {
            // 获取论文详情
            const paperDetail = await apiClient.getPaperDetail(paperId);
            
            if (!paperDetail) {
                alert('获取论文信息失败：返回数据为空');
                return;
            }
            
            // 处理可能的包装格式
            const actualPaper = paperDetail.data || paperDetail;
            
            // 检查是否有有效的订阅ID
            if (actualPaper.subscription_id && actualPaper.subscription_id !== 0) {
                // 跳转到对应的订阅论文页面
                navigate(`/subscription/${actualPaper.subscription_id}/papers/paper/${paperId}`);
            } else {
                // 如果有旧的 feed_id，提示迁移
                if (actualPaper.feed_id) {
                    alert(`该论文使用的是旧的论文源系统，请联系管理员迁移数据到新的订阅系统`);
                } else {
                    alert('该论文没有关联的订阅源信息，可能需要重新添加到订阅中');
                }
            }
        } catch (error) {
            console.error('获取论文详情失败:', error);
            alert(`获取论文信息失败: ${error.message}`);
        }
    };

    // 任务聚合逻辑
    const groupTasksByPaper = () => {
        const grouped = {};
        
        // 首先处理现有的任务
        filteredTasks.forEach(task => {
            const paperTitle = task.title || '未知论文';
            if (!grouped[paperTitle]) {
                grouped[paperTitle] = {
                    paper: paperTitle,
                    paperId: task.paper_id,
                    tasks: []
                };
            }
            grouped[paperTitle].tasks.push(task);
        });

        // 如果当前正在查看某个论文，确保它出现在列表中
        if (currentPaper && currentPaperId) {
            const currentPaperTitle = currentPaper.title || '未知论文';
            let foundCurrentPaper = false;
            
            // 检查当前论文是否已经在任务分组中（通过paperId匹配）
            Object.values(grouped).forEach(group => {
                if (group.paperId === currentPaperId) {
                    foundCurrentPaper = true;
                    // 更新分组的论文标题，确保使用最新的标题
                    if (group.paper !== currentPaperTitle) {
                        delete grouped[group.paper];
                        grouped[currentPaperTitle] = { ...group, paper: currentPaperTitle };
                    }
                }
            });
            
            if (!foundCurrentPaper) {
                // 如果当前论文不在任务列表中，添加一个空的分组
                grouped[currentPaperTitle] = {
                    paper: currentPaperTitle,
                    paperId: currentPaperId,
                    tasks: []
                };
            }
        }

        // 为每个分组计算状态和最新任务
        Object.values(grouped).forEach(group => {
            if (group.tasks.length > 0) {
                // 有任务的分组
                group.tasks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                group.latestTask = group.tasks[0];
                group.aggregatedStatus = group.latestTask.status;
            } else {
                // 没有任务的分组（比如当前正在查看的论文）
                group.latestTask = null;
                group.aggregatedStatus = 'no_task';
            }
        });

        return Object.values(grouped).sort((a, b) => {
            // 如果是当前正在查看的论文，放在最前面
            if (currentPaper && currentPaperId) {
                if (a.paperId === currentPaperId) return -1;
                if (b.paperId === currentPaperId) return 1;
            }
            
            // 其他按时间排序，没有任务的放在最后
            if (!a.latestTask && !b.latestTask) return 0;
            if (!a.latestTask) return 1;
            if (!b.latestTask) return -1;
            return new Date(b.latestTask.created_at) - new Date(a.latestTask.created_at);
        });
    };

    // 分页逻辑
    const getPagedGroups = () => {
        const allGroups = groupTasksByPaper();
        const totalPages = Math.ceil(allGroups.length / itemsPerPage);
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pagedGroups = allGroups.slice(startIndex, endIndex);
        
        return {
            groups: pagedGroups,
            totalPages,
            totalCount: allGroups.length
        };
    };

    const handlePageChange = (event, value) => {
        setCurrentPage(value);
        // 收起所有展开的任务，避免跨页状态混乱
        setExpandedTasks(new Set());
    };

    // 当当前论文变化时，自动跳转到包含它的页面
    useEffect(() => {
        if (currentPaper && currentPaperId) {
            const allGroups = groupTasksByPaper();
            const groupIndex = allGroups.findIndex(group => group.paperId === currentPaperId);
            if (groupIndex !== -1) {
                const targetPage = Math.ceil((groupIndex + 1) / itemsPerPage);
                if (targetPage !== currentPage) {
                    setCurrentPage(targetPage);
                }
            }
        }
    }, [currentPaper, currentPaperId, currentPage, itemsPerPage]);


    const renderStatsCards = () => {
        // 基于前端加载的实际任务数据计算统计
        const taskStatusCounts = {
            pending: 0,
            in_progress: 0,
            downloading: 0,
            analyzing: 0,
            completed: 0,
            failed: 0
        };

        // 统计各种状态的任务数量
        filteredTasks.forEach(task => {
            if (taskStatusCounts.hasOwnProperty(task.status)) {
                taskStatusCounts[task.status]++;
            }
        });

        // 统计在线Agent数量
        const onlineAgentsCount = agents.filter(agent => agent.status === 'online').length;

        const cards = [
            {
                title: '等待任务',
                value: taskStatusCounts.pending,
                icon: <ScheduleIcon />,
                color: 'warning'
            },
            {
                title: '进行中',
                value: taskStatusCounts.in_progress + taskStatusCounts.downloading + taskStatusCounts.analyzing,
                icon: <PlayArrowIcon />,
                color: 'info'
            },
            {
                title: '已完成',
                value: taskStatusCounts.completed,
                icon: <CheckCircleIcon />,
                color: 'success'
            },
            {
                title: '在线Agent',
                value: onlineAgentsCount,
                icon: <AgentIcon />,
                color: 'primary'
            }
        ];

        return (
            <Box sx={{
                display: 'grid',
                gridTemplateColumns: { 
                    xs: 'repeat(2, 1fr)',
                    sm: 'repeat(2, 1fr)',
                    md: 'repeat(4, 1fr)'
                },
                gap: { xs: 1, md: 2 }, // 移动端减少间距
                mb: { xs: 1.5, md: 4 } // 移动端减少下边距
            }}>
                {cards.map((card, index) => (
                    <Card 
                        key={index} 
                        sx={{ 
                            height: { xs: 70, md: 100 }, // 移动端进一步减少高度
                            transition: 'transform 0.2s, box-shadow 0.2s',
                            '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: theme.shadows[4]
                            }
                        }}
                    >
                        <CardContent sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: { xs: 0.75, md: 2 }, // 移动端减少内部间距
                            height: '100%',
                            p: { xs: 1, md: 2 }, // 移动端减少内边距
                            '&:last-child': { pb: { xs: 1, md: 2 } }
                        }}>
                            <Box sx={{ 
                                color: `${card.color}.main`,
                                '& .MuiSvgIcon-root': {
                                    fontSize: { xs: '1rem', md: '1.5rem' } // 移动端减少图标尺寸
                                }
                            }}>
                                {card.icon}
                            </Box>
                            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                                <Typography variant="h4" sx={{ 
                                    fontWeight: 700,
                                    mb: { xs: 0.25, md: 0.5 }, // 移动端减少数值和标题间距
                                    fontSize: { xs: '0.95rem', sm: '1.1rem', md: '1.75rem' }
                                }}>
                                    {card.value}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{
                                    fontSize: { xs: '0.7rem', md: '0.875rem' },
                                    lineHeight: { xs: 1.1, md: 1.4 }
                                }}>
                                    {card.title}
                                </Typography>
                            </Box>
                        </CardContent>
                    </Card>
                ))}
            </Box>
        );
    };

    const renderAgentGrid = () => {
        if (agents.length === 0) {
            return (
                <Alert severity="info" sx={{ mb: 3 }}>
                    <Typography variant="body2">
                        暂无在线Agent，请启动IEEE下载Agent以支持深度分析功能
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                        启动方法: <code>python start_ieee_agent.py</code>
                    </Typography>
                </Alert>
            );
        }

        return (
            <Box sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                gap: { xs: 1, md: 2 }, // 移动端减少间距
                mb: { xs: 1.5, md: 3 } // 移动端减少下边距
            }}>
                {agents.map((agent) => (
                    <Card key={agent.id} variant="outlined">
                        <CardContent sx={{ 
                            p: { xs: 1, md: 2 }, // 移动端减少内边距
                            '&:last-child': { pb: { xs: 1, md: 2 } }
                        }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: { xs: 0.75, md: 1 } }}>
                                <Typography variant="subtitle1" sx={{ 
                                    fontWeight: 600,
                                    fontSize: { xs: '0.9rem', md: '1rem' }
                                }}>
                                    {agent.name}
                                </Typography>
                                <Chip
                                    label={getAgentStatusText(agent.status)}
                                    size="small"
                                    sx={{
                                        height: { xs: 18, md: 24 },
                                        fontSize: { xs: '0.6rem', md: '0.75rem' },
                                        background: (theme) => {
                                            const color = getAgentStatusColor(agent.status);
                                            const colorValue = color === 'success' ? theme.palette.success.main :
                                                             color === 'error' ? theme.palette.error.main :
                                                             color === 'warning' ? theme.palette.warning.main :
                                                             color === 'info' ? theme.palette.info.main :
                                                             theme.palette.primary.main;
                                            return `linear-gradient(135deg, ${colorValue}80 0%, ${colorValue}90 100%)`;
                                        },
                                        color: 'white',
                                        border: (theme) => {
                                            const color = getAgentStatusColor(agent.status);
                                            const colorValue = color === 'success' ? theme.palette.success.main :
                                                             color === 'error' ? theme.palette.error.main :
                                                             color === 'warning' ? theme.palette.warning.main :
                                                             color === 'info' ? theme.palette.info.main :
                                                             theme.palette.primary.main;
                                            return `1px solid ${colorValue}40`;
                                        },
                                        '&:hover': {
                                            background: (theme) => {
                                                const color = getAgentStatusColor(agent.status);
                                                const colorValue = color === 'success' ? theme.palette.success.main :
                                                                 color === 'error' ? theme.palette.error.main :
                                                                 color === 'warning' ? theme.palette.warning.main :
                                                                 color === 'info' ? theme.palette.info.main :
                                                                 theme.palette.primary.main;
                                                return `linear-gradient(135deg, ${colorValue}90 0%, ${colorValue} 100%)`;
                                            },
                                            transform: 'translateY(-1px)',
                                            boxShadow: (theme) => {
                                                const color = getAgentStatusColor(agent.status);
                                                const colorValue = color === 'success' ? theme.palette.success.main :
                                                                 color === 'error' ? theme.palette.error.main :
                                                                 color === 'warning' ? theme.palette.warning.main :
                                                                 color === 'info' ? theme.palette.info.main :
                                                                 theme.palette.primary.main;
                                                return `0px 2px 6px ${colorValue}30`;
                                            }
                                        },
                                        transition: 'all 0.2s ease'
                                    }}
                                />
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ 
                                mb: { xs: 0.5, md: 1 }, // 移动端减少间距
                                fontSize: { xs: '0.75rem', md: '0.875rem' }
                            }}>
                                类型: {agent.type}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ 
                                mb: { xs: 0.5, md: 1 },
                                fontSize: { xs: '0.75rem', md: '0.875rem' }
                            }}>
                                能力: {agent.capabilities.join(', ')}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{
                                fontSize: { xs: '0.65rem', md: '0.75rem' }
                            }}>
                                最后心跳: {formatHeartbeatTime(agent.last_heartbeat)}
                            </Typography>
                        </CardContent>
                    </Card>
                ))}
            </Box>
        );
    };

    const renderTaskSteps = (task) => {
        if (!task.steps || task.steps.length === 0) return null;

        const stepNames = {
            'download_pdf': '📥 下载PDF文件',
            'analyze_with_deepseek': '🧠 DeepSeek AI分析',
            'save_results': '💾 保存分析结果'
        };

        return (
            <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    处理步骤:
                </Typography>
                <List dense>
                    {task.steps.map((step, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                                <Box sx={{
                                    width: 20,
                                    height: 20,
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '12px',
                                    fontWeight: 'bold',
                                    color: 'white',
                                    bgcolor: getStepColor(step.status)
                                }}>
                                    {getStepIcon(step.status, index + 1)}
                                </Box>
                                <Typography variant="body2" sx={{ flex: 1 }}>
                                    {stepNames[step.step_name] || step.step_name}
                                </Typography>
                                {step.completed_at && (
                                    <Typography variant="caption" color="text.secondary">
                                        {formatDateTime(step.completed_at)}
                                    </Typography>
                                )}
                            </Box>
                        </ListItem>
                    ))}
                </List>
            </Box>
        );
    };

    const getStepColor = (status) => {
        const colorMap = {
            'pending': '#6c757d',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545'
        };
        return colorMap[status] || '#6c757d';
    };

    const getStepIcon = (status, index) => {
        switch (status) {
            case 'completed':
                return '✓';
            case 'in_progress':
                return '⟳';
            case 'failed':
                return '✗';
            default:
                return index.toString();
        }
    };

    return (
        <Box sx={{ p: { xs: 1, md: 3 } }}>

            {/* 任务统计卡片 */}
            <Paper sx={{ p: { xs: 1.5, md: 2 }, mb: { xs: 1.5, md: 3 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 1.5, md: 2 } }}>
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
                        <TaskOutlined fontSize="small" />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                        任务统计
                    </Typography>
                </Box>
                
                {renderStatsCards()}
            </Paper>

            {/* Agent状态 */}
            <Paper sx={{ p: { xs: 1, md: 3 }, mb: { xs: 1.5, md: 3 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: { xs: 1, md: 2 } }}>
                    <Typography variant="h6" sx={{
                        fontWeight: 600,
                        fontSize: '1rem'
                    }}>
                        {isMobile ? '🤖 Agent' : '🤖 Agent状态'}
                    </Typography>
                    <Button
                        variant="outlined"
                        size="small"
                        startIcon={<RefreshIcon sx={{ fontSize: { xs: '0.9rem', md: '1.2rem' } }} />}
                        onClick={loadAgents}
                        disabled={loading}
                        sx={{
                            fontSize: { xs: '0.7rem', md: '0.875rem' },
                            px: { xs: 0.75, md: 1.5 }, // 移动端减少按钮内边距
                            py: { xs: 0.25, md: 0.5 }
                        }}
                    >
                        刷新
                    </Button>
                </Box>
                {renderAgentGrid()}
            </Paper>

            {/* 任务列表 */}
            <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: { xs: 1.5, md: 3 }
            }}>
                {/* 任务筛选器 */}
                <Paper sx={{ p: { xs: 1.5, md: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600, fontSize: '1rem' }}>
                            🔍 任务筛选
                        </Typography>
                        <Button
                            size="small"
                            onClick={() => {
                                setTaskTypeFilter('');
                                setStatusFilter('');
                            }}
                            sx={{ fontSize: '0.75rem' }}
                        >
                            清除
                        </Button>
                    </Box>
                    
                    <Box sx={{ 
                        display: 'grid', 
                        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                        gap: 2 
                    }}>
                        <FormControl size="small" fullWidth>
                            <InputLabel>任务类型</InputLabel>
                            <Select
                                value={taskTypeFilter}
                                label="任务类型"
                                onChange={(e) => setTaskTypeFilter(e.target.value)}
                            >
                                <MenuItem value="">全部类型</MenuItem>
                                {Object.entries(TASK_TYPE_CONFIG).map(([type, config]) => (
                                    <MenuItem key={type} value={type}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <span>{config.icon}</span>
                                            <span>{config.label}</span>
                                        </Box>
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        
                        <FormControl size="small" fullWidth>
                            <InputLabel>任务状态</InputLabel>
                            <Select
                                value={statusFilter}
                                label="任务状态"
                                onChange={(e) => setStatusFilter(e.target.value)}
                            >
                                <MenuItem value="">全部状态</MenuItem>
                                <MenuItem value="pending">等待中</MenuItem>
                                <MenuItem value="in_progress">处理中</MenuItem>
                                <MenuItem value="downloading">下载中</MenuItem>
                                <MenuItem value="analyzing">分析中</MenuItem>
                                <MenuItem value="completed">已完成</MenuItem>
                                <MenuItem value="failed">已失败</MenuItem>
                                <MenuItem value="cancelled">已取消</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>


                    {loading && filteredTasks.length === 0 ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                            <CircularProgress />
                        </Box>
                    ) : filteredTasks.length === 0 ? (
                        <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                            <Typography variant="body1">暂无任务</Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                                在论文详情页点击深度分析按钮创建任务
                            </Typography>
                        </Box>
                    ) : isMobile ? (
                        // 移动端：卡片列表
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                            {getPagedGroups().groups.map((group) => {
                                const isGroupExpanded = expandedTasks.has(`group-${group.paper}`);

                                return (
                                    <Card key={group.paper} variant="outlined" sx={{
                                        border: currentPaper && group.paperId === currentPaperId ? 2 : 1,
                                        borderColor: currentPaper && group.paperId === currentPaperId ? 'primary.main' : 'divider'
                                    }}>
                                        <CardContent sx={{ p: 1.5 }}>
                                            {/* 论文组头部 */}
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                                <Typography variant="h6" sx={{
                                                    fontWeight: 600,
                                                    fontSize: '1rem',
                                                    flex: 1,
                                                    pr: 1,
                                                    lineHeight: 1.3,
                                                    color: currentPaper && group.paperId === currentPaperId ? 'primary.main' : 'text.primary'
                                                }}>
                                                    {currentPaper && group.paperId === currentPaperId && '🔖 '}
                                                    {group.paper}
                                                </Typography>
                                                <Chip
                                                    label={group.aggregatedStatus === 'no_task' ? '无任务' : getTaskStatusText(group.aggregatedStatus)}
                                                    size="small"
                                                    color={group.aggregatedStatus === 'no_task' ? 'default' : getTaskStatusColor(group.aggregatedStatus)}
                                                    sx={{ height: 20, fontSize: '0.65rem' }}
                                                />
                                            </Box>

                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                                                    {group.tasks.length} 个任务{group.latestTask ? ` • 最新: ${formatDateTime(group.latestTask.created_at)}` : (currentPaper && group.paperId === currentPaperId ? ' • 当前查看论文' : ' • 暂无任务记录')}
                                                </Typography>
                                                <Box sx={{ display: 'flex', gap: 0.5 }}>
                                                    <Button
                                                        size="small"
                                                        variant="text"
                                                        onClick={() => toggleTaskExpansion(`group-${group.paper}`)}
                                                        sx={{ fontSize: '0.75rem', px: 1 }}
                                                    >
                                                        {isGroupExpanded ? '收起' : '展开'}
                                                    </Button>
                                                    <Button
                                                        size="small"
                                                        variant="text"
                                                        onClick={() => handleNavigateToPaper(group.paperId)}
                                                        sx={{ fontSize: '0.75rem', px: 1 }}
                                                    >
                                                        详情
                                                    </Button>
                                                </Box>
                                            </Box>

                                            {/* 可折叠的任务列表 */}
                                            <Collapse in={isGroupExpanded} timeout="auto" unmountOnExit>
                                                <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                    {group.tasks.length === 0 ? (
                                                        <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
                                                            <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                                                                该论文暂无深度分析任务记录
                                                            </Typography>
                                                            <Button
                                                                size="small"
                                                                variant="outlined"
                                                                color="primary"
                                                                onClick={() => createAnalysisTask(group.paperId)}
                                                                sx={{ fontSize: '0.7rem', mt: 1 }}
                                                            >
                                                                创建分析任务
                                                            </Button>
                                                        </Box>
                                                    ) : group.tasks.map((task) => {
                                                        const isActive = ['pending', 'in_progress', 'downloading', 'analyzing'].includes(task.status);
                                                        const isTaskExpanded = expandedTasks.has(task.id);

                                                        return (
                                                            <Box key={task.id} sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                                                        <Chip
                                                                            label={getTaskStatusText(task.status)}
                                                                            size="small"
                                                                            sx={{ height: 18, fontSize: '0.6rem' }}
                                                                            color={getTaskStatusColor(task.status)}
                                                                        />
                                                                        {/* 任务类型显示 */}
                                                                        {(() => {
                                                                            const typeInfo = getTaskTypeInfo(task);
                                                                            return (
                                                                                <Chip
                                                                                    label={
                                                                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                                                            <span style={{ fontSize: '0.5rem' }}>{typeInfo.icon}</span>
                                                                                            <span>{typeInfo.label}</span>
                                                                                        </Box>
                                                                                    }
                                                                                    size="small"
                                                                                    variant="outlined"
                                                                                    sx={{
                                                                                        height: 18,
                                                                                        fontSize: '0.6rem',
                                                                                        '& .MuiChip-label': { px: 0.75 }
                                                                                    }}
                                                                                />
                                                                            );
                                                                        })()}
                                                                    </Box>
                                                                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                                                                        {formatDateTime(task.created_at)}
                                                                    </Typography>
                                                                </Box>

                                                                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                                    {isActive && (
                                                                        <Button
                                                                            size="small"
                                                                            variant="outlined"
                                                                            color="error"
                                                                            onClick={() => handleCancelTask(task.id)}
                                                                            sx={{ fontSize: '0.7rem', px: 0.75 }}
                                                                        >
                                                                            取消
                                                                        </Button>
                                                                    )}
                                                                    {task.status === 'failed' && (
                                                                        <Button
                                                                            size="small"
                                                                            variant="outlined"
                                                                            color="primary"
                                                                            onClick={() => createAnalysisTask(task.paper_id)}
                                                                            sx={{ fontSize: '0.7rem', px: 0.75 }}
                                                                        >
                                                                            重试
                                                                        </Button>
                                                                    )}
                                                                    <Button
                                                                        size="small"
                                                                        variant="text"
                                                                        onClick={() => toggleTaskExpansion(task.id)}
                                                                        sx={{ fontSize: '0.7rem', px: 0.75 }}
                                                                    >
                                                                        {isTaskExpanded ? '收起' : '详情'}
                                                                    </Button>
                                                                </Box>

                                                                {/* 任务详情 */}
                                                                <Collapse in={isTaskExpanded} timeout="auto" unmountOnExit>
                                                                    <Box sx={{ mt: 1, p: 1, bgcolor: 'white', borderRadius: 0.5 }}>
                                                                        <Typography variant="caption" color="text.secondary" display="block">任务ID: {task.id}</Typography>
                                                                        <Typography variant="caption" color="text.secondary" display="block">IEEE编号: {task.ieee_article_number || '无'}</Typography>
                                                                        <Typography variant="caption" color="text.secondary" display="block">完成时间: {task.completed_at ? formatDateTime(task.completed_at) : '—'}</Typography>
                                                                        {renderTaskSteps && renderTaskSteps(task)}
                                                                    </Box>
                                                                </Collapse>
                                                            </Box>
                                                        );
                                                    })}
                                                </Box>
                                            </Collapse>
                                        </CardContent>
                                    </Card>
                                );
                            })}
                        </Box>
                    ) : (
                        // 桌面端：表格
                        <TableContainer component={Paper}>
                            <Table sx={{ minWidth: 650 }} aria-label="任务列表表格" size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell align="center" sx={{ fontWeight: 'bold' }}>论文标题</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 'bold' }}>状态</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 'bold' }}>最新任务类型</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 'bold' }}>任务数量</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 'bold' }}>操作</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {getPagedGroups().groups.map((group) => {
                                        const isGroupExpanded = expandedTasks.has(`group-${group.paper}`);

                                        return (
                                            <React.Fragment key={group.paper}>
                                                <TableRow sx={{
                                                    '& > *': { borderBottom: 'unset' },
                                                    bgcolor: currentPaper && group.paperId === currentPaperId ? 'primary.50' : 'grey.50',
                                                    border: currentPaper && group.paperId === currentPaperId ? 2 : 0,
                                                    borderColor: currentPaper && group.paperId === currentPaperId ? 'primary.main' : 'transparent'
                                                }}>
                                                    <TableCell align="center" sx={{
                                                        fontWeight: 600,
                                                        color: currentPaper && group.paperId === currentPaperId ? 'primary.main' : 'text.primary'
                                                    }}>
                                                        {currentPaper && group.paperId === currentPaperId && '🔖 '}
                                                        {group.paper}
                                                    </TableCell>
                                                    <TableCell align="center">
                                                        <Chip
                                                            label={group.aggregatedStatus === 'no_task' ? '无任务' : getTaskStatusText(group.aggregatedStatus)}
                                                            size="small"
                                                            color={group.aggregatedStatus === 'no_task' ? 'default' : getTaskStatusColor(group.aggregatedStatus)}
                                                        />
                                                    </TableCell>
                                                    <TableCell align="center">
                                                        {group.latestTask ? (
                                                            (() => {
                                                                const typeInfo = getTaskTypeInfo(group.latestTask);
                                                                return (
                                                                    <Chip
                                                                        label={
                                                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                                                <span style={{ fontSize: '0.75rem' }}>{typeInfo.icon}</span>
                                                                                <span>{typeInfo.label}</span>
                                                                            </Box>
                                                                        }
                                                                        size="small"
                                                                        variant="outlined"
                                                                        sx={{
                                                                            height: 24,
                                                                            fontSize: '0.75rem',
                                                                            '& .MuiChip-label': { px: 1 }
                                                                        }}
                                                                    />
                                                                );
                                                            })()
                                                        ) : (
                                                            <Typography variant="body2" color="text.secondary">
                                                                —
                                                            </Typography>
                                                        )}
                                                    </TableCell>
                                                    <TableCell align="center">
                                                        {group.tasks.length} 个任务
                                                    </TableCell>
                                                    <TableCell align="center">
                                                        <Stack direction="row" spacing={1} justifyContent="center">
                                                            <Button
                                                                size="small"
                                                                variant="text"
                                                                onClick={() => toggleTaskExpansion(`group-${group.paper}`)}
                                                            >
                                                                {isGroupExpanded ? '收起' : '展开'}
                                                            </Button>
                                                            <Button
                                                                size="small"
                                                                variant="text"
                                                                onClick={() => handleNavigateToPaper(group.paperId)}
                                                            >
                                                                详情
                                                            </Button>
                                                        </Stack>
                                                    </TableCell>
                                                </TableRow>
                                                <TableRow>
                                                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
                                                        <Collapse in={isGroupExpanded} timeout="auto" unmountOnExit>
                                                            <Box sx={{ margin: 1 }}>
                                                                <Table size="small" aria-label="任务详情">
                                                                    <TableHead>
                                                                        <TableRow>
                                                                            <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.8rem' }}>序号</TableCell>
                                                                            <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.8rem' }}>任务类型</TableCell>
                                                                            <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.8rem' }}>创建时间</TableCell>
                                                                            <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.8rem' }}>状态</TableCell>
                                                                            <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.8rem' }}>操作</TableCell>
                                                                        </TableRow>
                                                                    </TableHead>
                                                                    <TableBody>
                                                                        {group.tasks.length === 0 ? (
                                                                            <TableRow>
                                                                                <TableCell colSpan={5} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                                                                                    <Typography variant="body2" sx={{ mb: 1 }}>
                                                                                        该论文暂无深度分析任务记录
                                                                                    </Typography>
                                                                                    <Button
                                                                                        size="small"
                                                                                        variant="outlined"
                                                                                        color="primary"
                                                                                        onClick={() => createAnalysisTask(group.paperId)}
                                                                                    >
                                                                                        创建分析任务
                                                                                    </Button>
                                                                                </TableCell>
                                                                            </TableRow>
                                                                        ) : group.tasks.map((task, index) => {
                                                                            const isActive = ['pending', 'in_progress', 'downloading', 'analyzing'].includes(task.status);
                                                                            const isTaskExpanded = expandedTasks.has(task.id);

                                                                            return (
                                                                                <React.Fragment key={task.id}>
                                                                                    <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
                                                                                        <TableCell align="center">{index + 1}</TableCell>
                                                                                        <TableCell align="center">
                                                                                            {(() => {
                                                                                                const typeInfo = getTaskTypeInfo(task);
                                                                                                return (
                                                                                                    <Chip
                                                                                                        label={
                                                                                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                                                                                <span style={{ fontSize: '0.65rem' }}>{typeInfo.icon}</span>
                                                                                                                <span>{typeInfo.label}</span>
                                                                                                            </Box>
                                                                                                        }
                                                                                                        size="small"
                                                                                                        variant="outlined"
                                                                                                        sx={{
                                                                                                            height: 20,
                                                                                                            fontSize: '0.7rem',
                                                                                                            '& .MuiChip-label': { px: 0.75 }
                                                                                                        }}
                                                                                                    />
                                                                                                );
                                                                                            })()}
                                                                                        </TableCell>
                                                                                        <TableCell align="center">{formatDateTime(task.created_at)}</TableCell>
                                                                                        <TableCell align="center">
                                                                                            <Chip
                                                                                                label={getTaskStatusText(task.status)}
                                                                                                size="small"
                                                                                                color={getTaskStatusColor(task.status)}
                                                                                            />
                                                                                        </TableCell>
                                                                                        <TableCell align="center">
                                                                                            <Stack direction="row" spacing={1} justifyContent="flex-end">
                                                                                                {isActive && (
                                                                                                    <Button
                                                                                                        size="small"
                                                                                                        variant="outlined"
                                                                                                        color="error"
                                                                                                        onClick={() => handleCancelTask(task.id)}
                                                                                                    >
                                                                                                        取消
                                                                                                    </Button>
                                                                                                )}
                                                                                                {task.status === 'failed' && (
                                                                                                    <Button
                                                                                                        size="small"
                                                                                                        variant="outlined"
                                                                                                        color="primary"
                                                                                                        onClick={() => createAnalysisTask(task.paper_id)}
                                                                                                    >
                                                                                                        重试
                                                                                                    </Button>
                                                                                                )}
                                                                                                <Button
                                                                                                    size="small"
                                                                                                    variant="text"
                                                                                                    onClick={() => toggleTaskExpansion(task.id)}
                                                                                                >
                                                                                                    {isTaskExpanded ? '收起' : '详情'}
                                                                                                </Button>
                                                                                            </Stack>
                                                                                        </TableCell>
                                                                                    </TableRow>
                                                                                    <TableRow>
                                                                                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
                                                                                            <Collapse in={isTaskExpanded} timeout="auto" unmountOnExit>
                                                                                                <Box sx={{ margin: 1, p: 2, bgcolor: 'grey.25', borderRadius: 1 }}>
                                                                                                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                                                                                        任务详情
                                                                                                    </Typography>
                                                                                                    <Grid container spacing={2}>
                                                                                                        <Grid item xs={12} md={6}>
                                                                                                            <Typography variant="caption" color="text.secondary">任务ID</Typography>
                                                                                                            <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                                                                                                {task.id}
                                                                                                            </Typography>
                                                                                                        </Grid>
                                                                                                        <Grid item xs={12} md={6}>
                                                                                                            <Typography variant="caption" color="text.secondary">IEEE编号</Typography>
                                                                                                            <Typography variant="body2">
                                                                                                                {task.ieee_article_number || '无'}
                                                                                                            </Typography>
                                                                                                        </Grid>
                                                                                                        <Grid item xs={12}>
                                                                                                            <Typography variant="caption" color="text.secondary">完成时间</Typography>
                                                                                                            <Typography variant="body2">
                                                                                                                {task.completed_at ? formatDateTime(task.completed_at) : '—'}
                                                                                                            </Typography>
                                                                                                        </Grid>
                                                                                                    </Grid>
                                                                                                    {renderTaskSteps && renderTaskSteps(task)}
                                                                                                </Box>
                                                                                            </Collapse>
                                                                                        </TableCell>
                                                                                    </TableRow>
                                                                                </React.Fragment>
                                                                            );
                                                                        })}
                                                                    </TableBody>
                                                                </Table>
                                                            </Box>
                                                        </Collapse>
                                                    </TableCell>
                                                </TableRow>
                                            </React.Fragment>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}

                    {/* 分页组件 */}
                    {(() => {
                        const { totalPages, totalCount } = getPagedGroups();
                        return totalPages > 1 && (
                            <Box sx={{
                                display: 'flex',
                                flexDirection: { xs: 'column', md: 'row' },
                                justifyContent: 'space-between',
                                alignItems: { xs: 'center', md: 'center' },
                                mt: { xs: 2, md: 3 },
                                gap: { xs: 1, md: 0 }
                            }}>
                                <Typography variant="body2" color="text.secondary" sx={{
                                    fontSize: { xs: '0.8rem', md: '0.875rem' }
                                }}>
                                    共 {totalCount} 个论文分组，第 {currentPage} 页，共 {totalPages} 页
                                </Typography>
                                <Pagination
                                    count={totalPages}
                                    page={currentPage}
                                    onChange={handlePageChange}
                                    color="primary"
                                    size={isMobile ? "medium" : "large"}
                                    showFirstButton={!isMobile}
                                    showLastButton={!isMobile}
                                />
                            </Box>
                        );
                    })()}
                </Paper>
            </Box>
        </Box>
    );
}

export default TasksView;