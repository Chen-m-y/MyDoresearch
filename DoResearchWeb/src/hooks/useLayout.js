import { useMediaQuery, useTheme } from '@mui/material';
import { LAYOUT_CONSTANTS } from '../constants/layout';

/**
 * 布局相关的自定义Hook
 * 提供响应式布局值和工具函数
 */
export const useLayout = () => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down(LAYOUT_CONSTANTS.BREAKPOINTS.MOBILE_DRAWER_THRESHOLD));
    // 底部导航栏显示判断 - 必须与App.jsx中的逻辑保持一致
    const showBottomNavigation = useMediaQuery(theme.breakpoints.down('lg'));
    
    return {
        // 底部导航栏
        bottomNavigation: {
            height: LAYOUT_CONSTANTS.BOTTOM_NAVIGATION.HEIGHT,
            heightSpacing: LAYOUT_CONSTANTS.BOTTOM_NAVIGATION.HEIGHT_SPACING,
            isVisible: showBottomNavigation,
        },
        
        // 响应式值
        isMobile,
        isDesktop: !isMobile,
        
        // 工具函数
        getBottomSpacing: () => showBottomNavigation ? LAYOUT_CONSTANTS.BOTTOM_NAVIGATION.HEIGHT_SPACING : 0,
        
        // 样式对象
        styles: {
            // 主内容区域的底部间距 - 基于实际导航栏显示状态
            mainContentPadding: {
                pb: showBottomNavigation ? LAYOUT_CONSTANTS.BOTTOM_NAVIGATION.HEIGHT_SPACING : 0
            },
            
            // 底部导航栏样式
            bottomNavigationContainer: {
                height: LAYOUT_CONSTANTS.BOTTOM_NAVIGATION.HEIGHT,
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                zIndex: theme.zIndex.appBar,
            }
        }
    };
};