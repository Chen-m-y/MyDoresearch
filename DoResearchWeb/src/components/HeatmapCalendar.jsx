import React from 'react';
import { Box, Typography, Tooltip, useTheme } from '@mui/material';

function HeatmapCalendar({ data = [] }) {
    const theme = useTheme();

    // 确保我们有365天的数据
    if (data.length !== 365) {
        console.warn(`热力图数据长度不正确: ${data.length}, 期望: 365`);
    }

    // 获取颜色
    const getColor = (level) => {
        const colors = {
            0: theme.palette.grey[200],
            1: theme.palette.success.light,
            2: theme.palette.success.main,
            3: theme.palette.success.dark,
            4: '#1b5e20'
        };
        return colors[level] || colors[0];
    };

    // 按周分组
    const groupByWeeks = () => {
        if (data.length === 0) return [];

        const weeks = [];
        let currentWeek = [];

        // 找到第一天是星期几
        const firstDate = new Date(data[0].date);
        const firstDayOfWeek = firstDate.getDay(); // 0=Sunday, 1=Monday, ..., 6=Saturday

        // 在第一周前面填充空白天数
        for (let i = 0; i < firstDayOfWeek; i++) {
            currentWeek.push(null);
        }

        data.forEach((day) => {
            currentWeek.push(day);

            // 如果当前周已满7天，开始新的一周
            if (currentWeek.length === 7) {
                weeks.push([...currentWeek]);
                currentWeek = [];
            }
        });

        // 处理最后一周，如果不满7天则填充空白
        if (currentWeek.length > 0) {
            while (currentWeek.length < 7) {
                currentWeek.push(null);
            }
            weeks.push(currentWeek);
        }

        return weeks;
    };

    // 生成月份标签
    const generateMonthLabels = () => {
        if (data.length === 0) return [];

        const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
        const monthPositions = new Map();
        let currentWeek = 0;
        let dayInWeek = 0;

        // 计算第一天是星期几
        const firstDate = new Date(data[0].date);
        dayInWeek = firstDate.getDay();

        data.forEach((day) => {
            const date = new Date(day.date);
            const monthKey = `${date.getFullYear()}-${date.getMonth()}`;

            // 记录每个月第一次出现的位置
            if (!monthPositions.has(monthKey)) {
                monthPositions.set(monthKey, {
                    week: currentWeek,
                    month: date.getMonth(),
                    year: date.getFullYear()
                });
            }

            dayInWeek++;
            if (dayInWeek >= 7) {
                dayInWeek = 0;
                currentWeek++;
            }
        });

        return Array.from(monthPositions.values())
            .sort((a, b) => a.week - b.week)
            .filter((pos, index, arr) => {
                // 过滤重复的月份和过于接近的标签
                if (index === 0) return true;
                return pos.week - arr[index - 1].week >= 4; // 至少间隔4周
            })
            .map(pos => ({
                week: pos.week,
                label: months[pos.month]
            }));
    };

    const weeks = groupByWeeks();
    const monthLabels = generateMonthLabels();

    // 格式化日期显示
    const formatTooltipDate = (dateString) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch {
            return dateString;
        }
    };

    // 检查是否是今天
    const isToday = (dateString) => {
        const today = new Date();
        const todayStr = today.getFullYear() + '-' +
            String(today.getMonth() + 1).padStart(2, '0') + '-' +
            String(today.getDate()).padStart(2, '0');
        return dateString === todayStr;
    };

    return (
        <Box>
            {/* 月份标签 */}
            <Box sx={{
                display: 'flex',
                position: 'relative',
                height: 20,
                mb: 1,
                fontSize: '12px',
                color: 'text.secondary'
            }}>
                {monthLabels.map((label, index) => (
                    <Typography
                        key={index}
                        variant="caption"
                        sx={{
                            position: 'absolute',
                            left: `${(label.week * 14)}px`, // 每周14px宽度
                            fontSize: '11px'
                        }}
                    >
                        {label.label}
                    </Typography>
                ))}
            </Box>

            {/* 热力图网格 */}
            <Box sx={{
                display: 'flex',
                gap: '3px',
                overflowX: 'auto',
                pb: 1
            }}>
                {weeks.map((week, weekIndex) => (
                    <Box
                        key={weekIndex}
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '3px'
                        }}
                    >
                        {week.map((day, dayIndex) => {
                            if (!day) {
                                return (
                                    <Box
                                        key={`empty-${dayIndex}`}
                                        sx={{
                                            width: 11,
                                            height: 11,
                                            visibility: 'hidden'
                                        }}
                                    />
                                );
                            }

                            const isCurrentDay = isToday(day.date);

                            return (
                                <Tooltip
                                    key={day.date}
                                    title={`${formatTooltipDate(day.date)}: ${day.count} 篇已读文章${isCurrentDay ? ' (今天)' : ''}`}
                                    arrow
                                >
                                    <Box
                                        sx={{
                                            width: 11,
                                            height: 11,
                                            backgroundColor: getColor(day.level),
                                            borderRadius: '2px',
                                            cursor: 'pointer',
                                            border: isCurrentDay ? `2px solid ${theme.palette.primary.main}` : 'none',
                                            transition: 'all 0.1s',
                                            '&:hover': {
                                                transform: 'scale(1.2)',
                                                border: `1px solid ${theme.palette.text.primary}`,
                                                zIndex: 10,
                                                position: 'relative'
                                            }
                                        }}
                                    />
                                </Tooltip>
                            );
                        })}
                    </Box>
                ))}
            </Box>

            {/* 图例 */}
            <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1,
                mt: 2,
                fontSize: '12px',
                color: 'text.secondary'
            }}>
                <Typography variant="caption">少</Typography>
                <Box sx={{ display: 'flex', gap: '2px' }}>
                    {[0, 1, 2, 3, 4].map(level => (
                        <Box
                            key={level}
                            sx={{
                                width: 11,
                                height: 11,
                                backgroundColor: getColor(level),
                                borderRadius: '2px'
                            }}
                        />
                    ))}
                </Box>
                <Typography variant="caption">多</Typography>
            </Box>
        </Box>
    );
}

export default HeatmapCalendar;