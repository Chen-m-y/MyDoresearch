import React from 'react';
import {
    Box,
    Skeleton,
    Card,
    CardContent,
    useTheme,
} from '@mui/material';

export function StatsSkeleton() {
    return (
        <Box sx={{
            display: 'grid',
            gridTemplateColumns: { 
                xs: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)'
            },
            gap: { xs: 1.5, md: 3 },
            mb: { xs: 2.5, md: 4 }
        }}>
            {[...Array(4)].map((_, index) => (
                <Card
                    key={index}
                    sx={{
                        height: { xs: 100, md: 120 },
                        // 静态效果代替动画避免性能问题
                        opacity: 1 - (index * 0.05),
                        '@keyframes pulse': {
                            '0%': {
                                opacity: 1,
                            },
                            '50%': {
                                opacity: 0.7,
                            },
                            '100%': {
                                opacity: 1,
                            },
                        },
                    }}
                >
                    <CardContent sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: { xs: 1, md: 2 },
                        height: '100%',
                        p: { xs: 1.5, md: 2.5 },
                        '&:last-child': { pb: { xs: 1.5, md: 2.5 } },
                    }}>
                        <Skeleton
                            variant="rounded"
                            width={{ xs: 40, md: 56 }}
                            height={{ xs: 40, md: 56 }}
                            sx={{ borderRadius: 3 }}
                        />
                        <Box sx={{ flex: 1 }}>
                            <Skeleton
                                variant="text"
                                width="80%"
                                height={{ xs: 24, md: 32 }}
                                sx={{ mb: 0.5 }}
                            />
                            <Skeleton
                                variant="text"
                                width="60%"
                                height={{ xs: 16, md: 20 }}
                            />
                            <Skeleton
                                variant="text"
                                width="40%"
                                height={12}
                                sx={{ mt: 0.25 }}
                            />
                        </Box>
                    </CardContent>
                </Card>
            ))}
        </Box>
    );
}

export function PaperListSkeleton({ count = 5 }) {
    return (
        <Box>
            {[...Array(count)].map((_, index) => (
                <Card
                    key={index}
                    sx={{
                        mb: 1.5,
                        animation: 'slideIn 0.5s ease-out',
                        animationDelay: `${index * 0.1}s`,
                        animationFillMode: 'both',
                        '@keyframes slideIn': {
                            from: {
                                opacity: 0,
                                transform: 'translateY(20px)',
                            },
                            to: {
                                opacity: 1,
                                transform: 'translateY(0)',
                            },
                        },
                    }}
                >
                    <CardContent sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                            <Skeleton
                                variant="rounded"
                                width={8}
                                height={40}
                                sx={{ borderRadius: 2, flexShrink: 0, mt: 0.5 }}
                            />
                            <Box sx={{ flex: 1 }}>
                                <Skeleton
                                    variant="text"
                                    width="90%"
                                    height={24}
                                    sx={{ mb: 1 }}
                                />
                                <Skeleton
                                    variant="text"
                                    width="70%"
                                    height={20}
                                    sx={{ mb: 1 }}
                                />
                                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                    <Skeleton
                                        variant="rounded"
                                        width={60}
                                        height={20}
                                        sx={{ borderRadius: 10 }}
                                    />
                                    <Skeleton
                                        variant="rounded"
                                        width={80}
                                        height={20}
                                        sx={{ borderRadius: 10 }}
                                    />
                                </Box>
                                <Skeleton
                                    variant="text"
                                    width="50%"
                                    height={16}
                                />
                            </Box>
                        </Box>
                    </CardContent>
                </Card>
            ))}
        </Box>
    );
}

export function ChartSkeleton({ height = 280 }) {
    return (
        <Card>
            <CardContent sx={{ p: { xs: 1, md: 2 } }}>
                <Skeleton
                    variant="text"
                    width="40%"
                    height={32}
                    sx={{ mb: { xs: 0.75, md: 2 } }}
                />
                <Box sx={{
                    height: { xs: 160, md: height },
                    display: 'flex',
                    alignItems: 'flex-end',
                    gap: 1,
                    px: 2,
                }}>
                    {[...Array(12)].map((_, index) => (
                        <Skeleton
                            key={index}
                            variant="rectangular"
                            width="100%"
                            height={`${Math.random() * 60 + 20}%`}
                            sx={{
                                borderRadius: '4px 4px 0 0',
                                // 静态效果代替动画
                                opacity: 0.8,
                            }}
                        />
                    ))}
                </Box>
            </CardContent>
        </Card>
    );
}

export function HeatmapSkeleton() {
    const theme = useTheme();
    
    return (
        <Card>
            <CardContent sx={{ p: { xs: 1, md: 2 } }}>
                <Skeleton
                    variant="text"
                    width="50%"
                    height={32}
                    sx={{ mb: { xs: 0.75, md: 1 } }}
                />
                <Box sx={{
                    px: { xs: 0.25, sm: 0.5, md: 2 },
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'auto',
                    minHeight: 150,
                }}>
                    <Box sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(53, 1fr)',
                        gridTemplateRows: 'repeat(7, 1fr)',
                        gap: 0.5,
                        width: '100%',
                        maxWidth: 800,
                    }}>
                        {[...Array(371)].map((_, index) => (
                            <Skeleton
                                key={index}
                                variant="rounded"
                                width={12}
                                height={12}
                                sx={{
                                    // 静态效果代替动画
                                    opacity: 0.6,
                                    '@keyframes shimmer': {
                                        '0%': {
                                            opacity: 0.3,
                                        },
                                        '50%': {
                                            opacity: 0.8,
                                        },
                                        '100%': {
                                            opacity: 0.3,
                                        },
                                    },
                                }}
                            />
                        ))}
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
}

export default {
    StatsSkeleton,
    PaperListSkeleton,
    ChartSkeleton,
    HeatmapSkeleton,
};