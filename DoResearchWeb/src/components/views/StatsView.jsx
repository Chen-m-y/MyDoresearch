import React, {useState, useEffect, useContext, useRef, useMemo} from 'react';
import {
    Box,
    Paper,
    Typography,
    Card,
    CardContent,
    CircularProgress,
    useTheme,
    useMediaQuery,
    Button,
    alpha
} from '@mui/material';
import {
    LibraryBooks as LibraryBooksIcon,
    CheckCircle as CheckCircleIcon,
    LocalFireDepartment as LocalFireDepartmentIcon,
    TrendingUp as TrendingUpIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import * as Chart from 'chart.js';

import CalendarHeatmap from 'react-calendar-heatmap';
import 'react-calendar-heatmap/dist/styles.css';
import { Tooltip as ReactTooltip } from 'react-tooltip'; // 引入Tooltip组件
import 'react-tooltip/dist/react-tooltip.css'; // 引入Tooltip的CSS

import { DataContext } from '../../contexts/DataContext';
import { PaperContext } from '../../contexts/PaperContext';
import StatsCard from '../StatsCard';
import { StatsSkeleton, ChartSkeleton, HeatmapSkeleton } from '../SkeletonLoader';
import { LAYOUT_CONSTANTS } from '../../constants/layout.js';

const heatmapStyles = `
.react-calendar-heatmap .color-empty {
  fill: #ebedf0;
}
.react-calendar-heatmap .color-github-1 {
  fill: #9be9a8;
}
.react-calendar-heatmap .color-github-2 {
  fill: #40c463;
}
.react-calendar-heatmap .color-github-3 {
  fill: #30a14e;
}
.react-calendar-heatmap .color-github-4 {
  fill: #216e39;
}

.react-calendar-heatmap text {
    font-size: 0.4em !important; /* 调整字体大小，可以根据需要修改 0.6 这个比例 */
}

.react-calendar-heatmap rect {
    rx: 4px !important; /* 设置 x 轴方向的圆角半径 */
    ry: 4px !important; /* 设置 y 轴方向的圆角半径，保持和 rx 一致可以得到圆形角 */
}
`;

function StatsView() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD));
    const {getStatsData} = useContext(DataContext);
    const {setCurrentView} = useContext(PaperContext);

    const [statsData, setStatsData] = useState(null);
    const [loading, setLoading] = useState(true);

    // Chart.js 引用
    const barChartRef = useRef(null);
    const lineChartRef = useRef(null);
    const barChartInstance = useRef(null);
    const lineChartInstance = useRef(null);
    const heatmapChartInstance = useRef(null);
    const heatmapChartRef = useRef(null);

    // --- 变更: 新增 useMemo 来处理热力图数据 ---
    const heatmapDataWithLevels = useMemo(() => {
        if (!statsData || !statsData.last_year_read_papers) {
            return [];
        }
        // 根据后端返回的每日已读数量，在前端计算出用于渲染颜色的 level
        return statsData.last_year_read_papers.map(item => {
            const count = item.count;
            const level = count === 0 ? 0 : count <= 2 ? 1 : count <= 5 ? 2 : count <= 10 ? 3 : 4;
            return { ...item, level };
        });
    }, [statsData]);

    // 注册 Chart.js 组件
    useEffect(() => {
        Chart.Chart.register(
            Chart.CategoryScale, Chart.LinearScale, Chart.BarElement, Chart.LineElement,
            Chart.PointElement, Chart.Title, Chart.Tooltip, Chart.Legend, Chart.Filler,
            Chart.BarController, Chart.LineController, Chart.ScatterController
        );
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            const data = await getStatsData();
            setStatsData(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        } finally {
            setLoading(false);
        }
    };

    // 创建柱状图
    const createBarChart = (data) => {
        // 销毁现有图表
        if (barChartInstance.current) {
            try {
                barChartInstance.current.destroy();
            } catch (e) {
                console.warn('销毁柱状图时出错:', e);
            }
            barChartInstance.current = null;
        }

        const canvas = barChartRef.current;
        if (!canvas) {
            console.warn('柱状图Canvas元素不存在');
            return;
        }

        // 清理canvas
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('无法获取Canvas上下文');
            return;
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        try {
            barChartInstance.current = new Chart.Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(item => item.date),
                    datasets: [{
                        label: '新增文章',
                        data: data.map(item => item.count),
                        backgroundColor: theme.palette.primary.main + '80',
                        borderColor: theme.palette.primary.main,
                        borderWidth: 1,
                        borderRadius: 6,
                        borderSkipped: false,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'white',
                            titleColor: '#333',
                            bodyColor: '#666',
                            borderColor: '#e0e0e0',
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                title: (context) => {
                                    const index = context[0].dataIndex;
                                    return data[index].fullDate;
                                },
                                label: (context) => `${context.parsed.y} 篇新增文章`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#666',
                                font: {
                                    size: 11
                                }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#f0f0f0',
                                borderDash: [3, 3]
                            },
                            ticks: {
                                color: '#666',
                                font: {
                                    size: 11
                                },
                                stepSize: 1,
                                callback: function(value) {
                                    return Number.isInteger(value) ? value : '';
                                }
                            },
                            title: {
                                display: true,
                                text: '文章数',
                                color: '#666',
                                font: {
                                    size: 12
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('创建柱状图失败:', error);
            barChartInstance.current = null;
        }
    };

    // 创建折线图
    const createLineChart = (data) => {
        // 销毁现有图表
        if (lineChartInstance.current) {
            try {
                lineChartInstance.current.destroy();
            } catch (e) {
                console.warn('销毁折线图时出错:', e);
            }
            lineChartInstance.current = null;
        }

        const canvas = lineChartRef.current;
        if (!canvas) {
            console.warn('折线图Canvas元素不存在');
            return;
        }

        // 清理canvas
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('无法获取Canvas上下文');
            return;
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        try {
            lineChartInstance.current = new Chart.Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(item => item.date),
                    datasets: [{
                        label: '已读文章',
                        data: data.map(item => item.count),
                        borderColor: theme.palette.success.main,
                        backgroundColor: theme.palette.success.main + '20',
                        borderWidth: 3,
                        pointBackgroundColor: theme.palette.success.main,
                        pointBorderColor: 'white',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'white',
                            titleColor: '#333',
                            bodyColor: '#666',
                            borderColor: '#e0e0e0',
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                title: (context) => {
                                    const index = context[0].dataIndex;
                                    return data[index].fullDate;
                                },
                                label: (context) => `${context.parsed.y} 篇已读文章`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#666',
                                font: {
                                    size: 11
                                }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#f0f0f0',
                                borderDash: [3, 3]
                            },
                            ticks: {
                                color: '#666',
                                font: {
                                    size: 11
                                },
                                stepSize: 1,
                                callback: function(value) {
                                    return Number.isInteger(value) ? value : '';
                                }
                            },
                            title: {
                                display: true,
                                text: '文章数',
                                color: '#666',
                                font: {
                                    size: 12
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('创建折线图失败:', error);
            lineChartInstance.current = null;
        }
    };

    // 创建热力图
    const createHeatmapChart = (data) => {
        // 销毁现有图表
        if (heatmapChartInstance.current) {
            try {
                heatmapChartInstance.current.destroy();
            } catch (e) {
                console.warn('销毁热力图时出错:', e);
            }
            heatmapChartInstance.current = null;
        }

        const canvas = heatmapChartRef.current;
        if (!canvas) {
            console.warn('热力图Canvas元素不存在');
            return;
        }

        // 清理canvas
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('无法获取Canvas上下文');
            return;
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 转换热力图数据为散点图格式
        const heatmapData = data.map((item, index) => {
            const date = new Date(item.date);
            const dayOfYear = Math.floor((date - new Date(date.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
            const week = Math.floor(dayOfYear / 7);
            const dayOfWeek = date.getDay();

            return {
                x: week,
                y: dayOfWeek,
                v: item.count,
                date: item.date,
                level: item.level
            };
        });

        // 获取颜色
        const getColor = (level) => {
            const colors = {
                0: '#ebedf0',
                1: theme.palette.success.light,
                2: theme.palette.success.main,
                3: theme.palette.success.dark,
                4: '#1b5e20'
            };
            return colors[level] || colors[0];
        };

        try {
            heatmapChartInstance.current = new Chart.Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: '阅读热力图',
                        data: heatmapData,
                        backgroundColor: (context) => {
                            const point = context.parsed;
                            const dataPoint = heatmapData.find(d => d.x === point.x && d.y === point.y);
                            return dataPoint ? getColor(dataPoint.level) : '#ebedf0';
                        },
                        borderColor: '#ffffff',
                        borderWidth: 2,
                        pointRadius: 8,
                        pointHoverRadius: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'white',
                            titleColor: '#333',
                            bodyColor: '#666',
                            borderColor: '#e0e0e0',
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                title: (context) => {
                                    const point = context[0];
                                    const dataPoint = heatmapData.find(d => d.x === point.parsed.x && d.y === point.parsed.y);
                                    if (dataPoint) {
                                        const date = new Date(dataPoint.date);
                                        return date.toLocaleDateString('zh-CN', {
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric'
                                        });
                                    }
                                    return '';
                                },
                                label: (context) => {
                                    const point = context.parsed;
                                    const dataPoint = heatmapData.find(d => d.x === point.x && d.y === point.y);
                                    return dataPoint ? `${dataPoint.v} 篇已读文章` : '0 篇已读文章';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'top',
                            min: 0,
                            max: 53,
                            grid: {
                                display: false
                            },
                            ticks: {
                                display: false
                            },
                            title: {
                                display: false
                            }
                        },
                        y: {
                            type: 'linear',
                            min: -0.5,
                            max: 6.5,
                            grid: {
                                display: false
                            },
                            ticks: {
                                stepSize: 1,
                                callback: function(value) {
                                    const days = ['日', '一', '二', '三', '四', '五', '六'];
                                    return days[value] || '';
                                },
                                color: '#666',
                                font: {
                                    size: 11
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false
                    }
                }
            });
        } catch (error) {
            console.error('创建热力图失败:', error);
            heatmapChartInstance.current = null;
        }
    };

    useEffect(() => {
        setCurrentView('stats');
    }, [setCurrentView]);

    useEffect(() => {
        loadStats();
    }, [getStatsData]);

    // 当数据更新时重新创建图表
    useEffect(() => {
        if (statsData) {
            // --- 变更: 使用新的数据键名 ---
            const sortedNewPapers = [...(statsData.last_30_days_new_papers || [])].sort((a, b) => new Date(a.date) - new Date(b.date));
            const sortedReadPapers = [...(statsData.last_30_days_read_papers || [])].sort((a, b) => new Date(a.date) - new Date(b.date));

            const newPapersData = prepareChartData(sortedNewPapers);
            const readPapersData = prepareChartData(sortedReadPapers);

            const timer = setTimeout(() => {
                try {
                    if (barChartRef.current) createBarChart(newPapersData);
                    if (lineChartRef.current) createLineChart(readPapersData);
                    // --- 变更: 使用处理过的热力图数据 ---
                    if (heatmapChartRef.current) createHeatmapChart(heatmapDataWithLevels);
                } catch (error) {
                    console.error('创建图表时发生错误:', error);
                }
            }, 300);

            return () => clearTimeout(timer);
        }
    }, [statsData, heatmapDataWithLevels]); // 添加 heatmapDataWithLevels 作为依赖


    // 组件卸载时清理图表
    useEffect(() => {
        return () => {
            [barChartInstance, lineChartInstance, heatmapChartInstance].forEach((instance, index) => {
                if (instance.current) {
                    try {
                        instance.current.destroy();
                    } catch (e) {
                        console.warn(`销毁图表${index}时出错:`, e);
                    }
                    instance.current = null;
                }
            });
        };
    }, []);

    if (loading) {
        return (
            <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 2
            }}>
                <CircularProgress size={48}/>
                <Typography variant="h6" color="text.secondary">
                    正在加载统计数据...
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    正在收集阅读数据
                </Typography>
            </Box>
        );
    }

    if (!statsData) {
        return (
            <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 2,
                textAlign: 'center'
            }}>
                <Typography variant="h5" color="text.secondary">
                    暂无统计数据
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    开始阅读论文后会显示统计信息
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<RefreshIcon/>}
                    onClick={loadStats}
                    sx={(theme) => ({
                        background: `linear-gradient(135deg, ${theme.palette.warning.main}80 0%, ${theme.palette.warning.main}90 100%)`,
                        border: `1px solid ${theme.palette.warning.main}30`,
                        color: 'white',
                        position: 'relative',
                        overflow: 'hidden',
                        '&::before': {
                            content: '""',
                            position: 'absolute',
                            top: 0,
                            right: 0,
                            width: '40px',
                            height: '40px',
                            background: `radial-gradient(circle, ${theme.palette.warning.main}20 0%, transparent 70%)`,
                            transform: 'translate(15px, -15px)',
                        },
                        '& .MuiButton-startIcon': {
                            position: 'relative',
                            zIndex: 1,
                        },
                        '&:hover': {
                            background: `linear-gradient(135deg, ${theme.palette.warning.main}90 0%, ${theme.palette.warning.main} 100%)`,
                            transform: 'translateY(-1px)',
                            boxShadow: `0px 4px 12px ${theme.palette.warning.main}30`,
                        },
                        transition: 'all 0.2s ease'
                    })}
                >
                    重新加载
                </Button>
            </Box>
        );
    }

    const readingRate = statsData.total_papers > 0
        ? Math.round((statsData.read_papers / statsData.total_papers) * 100)
        : 0;

    const statsCards = [
        {
            title: '总文章数',
            value: statsData.total_papers,
            icon: <LibraryBooksIcon/>,
            color: theme.palette.primary.main,
            gradient: true,
            subtitle: '已收录的全部论文'
        },
        {
            title: '已读文章',
            value: statsData.read_papers,
            icon: <CheckCircleIcon/>,
            color: theme.palette.success.main,
            gradient: true,
            trend: statsData.reading_trend || 0,
            subtitle: '深度阅读完成'
        },
        {
            title: '连续阅读天数',
            value: statsData.reading_streak_days,
            icon: <LocalFireDepartmentIcon/>,
            color: theme.palette.warning.main,
            gradient: true,
            subtitle: '保持学习习惯'
        },
        {
            title: '阅读完成率',
            value: `${readingRate}%`,
            icon: <TrendingUpIcon/>,
            color: theme.palette.info.main,
            gradient: true,
            trend: readingRate > 50 ? 5 : -2,
            subtitle: '知识掌握程度'
        }
    ];

    // 准备图表数据
    const prepareChartData = (dailyData) => {
        return dailyData.map(item => ({
            date: new Date(item.date).toLocaleDateString('zh-CN', {month: 'numeric', day: 'numeric'}),
            fullDate: item.date,
            count: item.count
        }));
    };

    const getHeatmapDateRange = () => {
        const today = new Date();
        const startDate = new Date();
        
        if (isMobile) {
            // 移动端显示四个月
            startDate.setMonth(today.getMonth() - 4);
        } else {
            // 桌面端显示一年
            startDate.setFullYear(today.getFullYear() - 1);
            startDate.setDate(startDate.getDate() + 1);
        }
        
        return {
            startDate,
            endDate: today,
        };
    };
    const { startDate, endDate } = getHeatmapDateRange();
    
    // 过滤热力图数据，只显示指定日期范围内的数据
    const getFilteredHeatmapData = () => {
        if (!statsData?.last_year_read_papers) return [];
        
        return statsData.last_year_read_papers.filter(item => {
            const itemDate = new Date(item.date);
            return itemDate >= startDate && itemDate <= endDate;
        });
    };

    return (
        <Box sx={{
            p: { xs: 1, md: 3 } // 移动端进一步减少边距
        }}>
            <style>
                {heatmapStyles}
            </style>


            {/* 阅读统计卡片 */}
            <Paper sx={{ p: { xs: 1.5, md: 2 }, mb: { xs: 2.5, md: 4 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 1.5, md: 2 } }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                        📊 阅读统计
                    </Typography>
                </Box>
                
                {loading ? (
                    <StatsSkeleton />
                ) : (
                    <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: { 
                            xs: 'repeat(2, 1fr)',
                            md: 'repeat(4, 1fr)'
                        },
                        gap: { xs: 1.5, md: 2 }
                    }}>
                        {statsCards.map((card, index) => (
                            <StatsCard
                                key={`stats-card-${index}`}
                                title={card.title}
                                value={card.value}
                                icon={card.icon}
                                color={card.color}
                                gradient={card.gradient}
                                trend={card.trend}
                                subtitle={card.subtitle}
                                loading={loading}
                            />
                        ))}
                    </Box>
                )}
            </Paper>

            {/* 图表区域 */}
            {loading ? (
                <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                    gap: { xs: 1, md: 3 },
                    mb: { xs: 1.5, md: 4 }
                }}>
                    <ChartSkeleton />
                    <ChartSkeleton />
                </Box>
            ) : (
                <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                    gap: { xs: 1, md: 3 },
                    mb: { xs: 1.5, md: 4 }
                }}>
                    {/* 新增文章图表 */}
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
                        <CardContent sx={{ 
                            p: { xs: 1, md: 2 },
                            '&:last-child': { pb: { xs: 1, md: 2 } }
                        }}>
                            <Typography variant="h6" sx={{
                                mb: { xs: 0.75, md: 2 },
                                fontWeight: 600,
                                fontSize: '1rem'
                            }}>
                                {isMobile ? '📊 新增文章' : '📊 近30天新增文章'}
                            </Typography>
                            <Box sx={{
                                height: { xs: 160, md: 280 },
                                width: '100%', 
                                position: 'relative'
                            }}>
                                <canvas
                                    ref={barChartRef}
                                    style={{width: '100%', height: '100%'}}
                                    key="bar-chart-canvas"
                                />
                            </Box>
                        </CardContent>
                    </Card>

                    {/* 已读文章图表 */}
                    <Card sx={{
                        animation: 'fadeInUp 0.6s ease-out 0.1s',
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
                        <CardContent sx={{ 
                            p: { xs: 1, md: 2 },
                            '&:last-child': { pb: { xs: 1, md: 2 } }
                        }}>
                            <Typography variant="h6" sx={{
                                mb: { xs: 0.75, md: 2 },
                                fontWeight: 600,
                                fontSize: '1rem'
                            }}>
                                {isMobile ? '📖 已读文章' : '📖 近30天已读文章'}
                            </Typography>
                            <Box sx={{
                                height: { xs: 160, md: 280 },
                                width: '100%', 
                                position: 'relative'
                            }}>
                                <canvas
                                    ref={lineChartRef}
                                    style={{width: '100%', height: '100%'}}
                                    key="line-chart-canvas"
                                />
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            )}

            {/* 热力图 */}
            {loading ? (
                <HeatmapSkeleton />
            ) : (
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
                    <CardContent sx={{ 
                        p: { xs: 1, md: 2 },
                        '&:last-child': { pb: { xs: 1, md: 2 } }
                    }}>
                        <Typography variant="h6" sx={{ 
                            mb: { xs: 0.75, md: 1 },
                            fontWeight: 600,
                            fontSize: '1rem'
                        }}>
                            {isMobile ? '🔥 阅读热力图（近四个月）' : '🔥 阅读热力图（过去一年）'}
                        </Typography>

                        {/* 热力图容器 */}
                        <Box
                            sx={{
                                px: { xs: 0, sm: 0.5, md: 2 },
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                overflow: 'auto',
                            }}
                        >
                            {/* 移动端简化版热力图说明 */}
                            {isMobile && (
                                <Box sx={{ 
                                    mb: 2, 
                                    p: 1.5, 
                                    backgroundColor: 'grey.50', 
                                    borderRadius: 2,
                                    width: '100%',
                                    textAlign: 'center'
                                }}>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                        阅读活跃度图表
                                    </Typography>
                                    <Box sx={{ 
                                        display: 'flex', 
                                        justifyContent: 'center', 
                                        alignItems: 'center',
                                        gap: 1,
                                        flexWrap: 'wrap'
                                    }}>
                                        <Typography variant="caption" color="text.secondary">少</Typography>
                                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                                            {['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'].map((color, index) => (
                                                <Box
                                                    key={index}
                                                    sx={{
                                                        width: 12,
                                                        height: 12,
                                                        backgroundColor: color,
                                                        borderRadius: 1,
                                                    }}
                                                />
                                            ))}
                                        </Box>
                                        <Typography variant="caption" color="text.secondary">多</Typography>
                                    </Box>
                                </Box>
                            )}
                            
                            {/* 热力图 */}
                            <Box
                                sx={{
                                    width: '100%',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    overflow: 'auto',
                                }}
                            >
                                <CalendarHeatmap
                                    startDate={startDate}
                                    endDate={endDate}
                                    values={getFilteredHeatmapData()}
                                    classForValue={(value) => {
                                        if (!value || value.count === 0) return 'color-empty';
                                        if (value.count <= 2) return 'color-github-1';
                                        if (value.count <= 5) return 'color-github-2';
                                        if (value.count <= 10) return 'color-github-3';
                                        return 'color-github-4';
                                    }}
                                    tooltipDataAttrs={value => {
                                        if (!value) return {};
                                        const date = value.date || '';
                                        const count = value.count || 0;
                                        return {
                                            'data-tooltip-id': 'heatmap-tooltip',
                                            'data-tooltip-content': `${date}: ${count} 篇已读`,
                                        };
                                    }}
                                    showWeekdayLabels={!isMobile}
                                    showMonthLabels={true}
                                />
                            </Box>

                            {/* 移动端统计摘要 */}
                            {isMobile && getFilteredHeatmapData().length > 0 && (
                                <Box sx={{ 
                                    mt: 2, 
                                    display: 'grid', 
                                    gridTemplateColumns: 'repeat(3, 1fr)', 
                                    gap: 1,
                                    width: '100%'
                                }}>
                                    {[
                                        { 
                                            label: '阅读天数', 
                                            value: getFilteredHeatmapData().filter(d => d.count > 0).length,
                                            color: theme.palette.success.main
                                        },
                                        { 
                                            label: '最长连续', 
                                            value: `${statsData.reading_streak_days}天`,
                                            color: theme.palette.warning.main
                                        },
                                        { 
                                            label: '四月已读', 
                                            value: getFilteredHeatmapData().reduce((sum, d) => sum + d.count, 0) || 0,
                                            color: theme.palette.info.main
                                        }
                                    ].map((stat, index) => (
                                        <Box
                                            key={index}
                                            sx={{
                                                textAlign: 'center',
                                                p: 1,
                                                backgroundColor: alpha(stat.color, 0.08),
                                                borderRadius: 2,
                                            }}
                                        >
                                            <Typography 
                                                variant="h6" 
                                                sx={{ 
                                                    fontWeight: 600, 
                                                    color: stat.color,
                                                    fontSize: '1rem',
                                                    mb: 0.5
                                                }}
                                            >
                                                {stat.value}
                                            </Typography>
                                            <Typography 
                                                variant="caption" 
                                                color="text.secondary"
                                                sx={{ fontSize: '0.7rem' }}
                                            >
                                                {stat.label}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Box>
                            )}
                        </Box>
                    </CardContent>
                </Card>
            )}

            {/* --- 变更 4: 在页面上渲染Tooltip组件，使其生效 --- */}
            <ReactTooltip id="heatmap-tooltip" />
        </Box>
    );
}

export default StatsView;