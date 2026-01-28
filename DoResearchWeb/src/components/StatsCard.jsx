import React from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    useTheme,
    alpha,
} from '@mui/material';

function StatsCard({ 
    title, 
    value, 
    icon, 
    color, 
    gradient = false,
    trend = null,
    subtitle = null,
    loading = false
}) {
    const theme = useTheme();

    const cardStyles = gradient ? {
        background: `linear-gradient(135deg, ${color}15 0%, ${color}25 100%)`,
        border: `1px solid ${alpha(color, 0.2)}`,
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100px',
            height: '100px',
            background: `radial-gradient(circle, ${alpha(color, 0.1)} 0%, transparent 70%)`,
            transform: 'translate(30px, -30px)',
        }
    } : {
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
    };

    return (
        <Card
            sx={{
                height: { xs: 100, md: 120 },
                position: 'relative',
                ...cardStyles,
                '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: `0px 12px 32px ${alpha(color, 0.15)}`,
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
        >
            <CardContent sx={{
                display: 'flex',
                alignItems: 'center',
                gap: { xs: 1, md: 2 },
                height: '100%',
                p: { xs: 1.5, md: 2.5 },
                '&:last-child': { pb: { xs: 1.5, md: 2.5 } },
                position: 'relative',
                zIndex: 1,
            }}>
                {/* 图标区域 */}
                <Box
                    sx={{
                        p: { xs: 1, md: 1.5 },
                        borderRadius: 3,
                        backgroundColor: alpha(color, 0.1),
                        color: color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minWidth: { xs: 40, md: 56 },
                        minHeight: { xs: 40, md: 56 },
                        boxShadow: `0px 4px 12px ${alpha(color, 0.15)}`,
                        '& .MuiSvgIcon-root': {
                            fontSize: { xs: '1.4rem', md: '2rem' },
                        }
                    }}
                >
                    {icon}
                </Box>

                {/* 内容区域 */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography 
                            variant="h4" 
                            sx={{
                                fontWeight: 700,
                                fontSize: { xs: '1.2rem', sm: '1.4rem', md: '2rem' },
                                color: loading ? 'text.secondary' : 'text.primary',
                                background: loading ? 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)' : 'none',
                                backgroundSize: loading ? '200% 100%' : 'auto',
                                // 静态渐变代替动画避免性能问题
                                opacity: loading ? 0.7 : 1,
                                borderRadius: loading ? 1 : 0,
                                minHeight: loading ? '1.5rem' : 'auto',
                                minWidth: loading ? '60px' : 'auto',
                            }}
                        >
                            {loading ? '' : value}
                        </Typography>
                        
                        {trend && (
                            <Typography
                                variant="caption"
                                sx={{
                                    color: trend > 0 ? theme.palette.success.main : theme.palette.error.main,
                                    fontWeight: 600,
                                    fontSize: '0.75rem',
                                    backgroundColor: trend > 0 ? alpha(theme.palette.success.main, 0.1) : alpha(theme.palette.error.main, 0.1),
                                    px: 0.5,
                                    py: 0.25,
                                    borderRadius: 1,
                                }}
                            >
                                {trend > 0 ? '+' : ''}{trend}%
                            </Typography>
                        )}
                    </Box>
                    
                    <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{
                            fontSize: { xs: '0.75rem', md: '0.875rem' },
                            fontWeight: 500,
                            lineHeight: 1.2,
                        }}
                    >
                        {title}
                    </Typography>
                    
                    {subtitle && (
                        <Typography 
                            variant="caption" 
                            color="text.secondary" 
                            sx={{
                                fontSize: '0.65rem',
                                opacity: 0.8,
                                display: 'block',
                                mt: 0.25,
                            }}
                        >
                            {subtitle}
                        </Typography>
                    )}
                </Box>
            </CardContent>
        </Card>
    );
}

export default StatsCard;