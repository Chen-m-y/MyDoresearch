import React from 'react';
import {
    Box,
    Typography,
    useTheme,
    useMediaQuery
} from '@mui/material';
import { RecommendationDashboard } from '../recommendations/index.js';
import { LAYOUT_CONSTANTS } from '../../constants/layout.js';

/**
 * 推荐系统主视图
 * 可以作为独立页面显示完整的推荐系统功能
 */
function RecommendationView() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_THRESHOLD));

    return (
        <Box sx={{
            p: { xs: 1, md: 3 }
        }}>
            {/* 页面标题 */}
            <Box sx={{ mb: { xs: 2, md: 4 }, textAlign: 'center' }}>
                <Typography variant="h4" sx={{
                    fontWeight: 600,
                    mb: { xs: 0.5, md: 1 },
                    fontSize: { xs: '1.5rem', md: '2.125rem' }
                }}>
                    {isMobile ? '🤖 智能推荐' : '🤖 智能推荐系统'}
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{
                    fontSize: { xs: '0.875rem', md: '1rem' }
                }}>
                    {isMobile ? 'AI驱动的个性化论文发现' : '基于人工智能的个性化论文推荐和兴趣分析'}
                </Typography>
            </Box>

            {/* 推荐系统仪表板 */}
            <RecommendationDashboard compact={isMobile} />
        </Box>
    );
}

export default RecommendationView;