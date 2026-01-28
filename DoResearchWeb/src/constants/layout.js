// 布局相关常量
export const LAYOUT_CONSTANTS = {
    // 底部导航栏
    BOTTOM_NAVIGATION: {
        HEIGHT: 48, // px
        HEIGHT_SPACING: 6, // MUI spacing units (48px / 8px = 6)
    },
    
    // 顶部应用栏
    APP_BAR: {
        HEIGHT: 64, // px
        HEIGHT_SPACING: 8, // MUI spacing units
    },
    
    // 侧边栏
    SIDEBAR: {
        WIDTH: 240, // px
        COLLAPSED_WIDTH: 64, // px
    },
    
    // 断点
    BREAKPOINTS: {
        MOBILE_DRAWER_THRESHOLD: 'md', // 小于md时显示移动端抽屉
        MOBILE_THRESHOLD: 'sm', // 小于sm时显示手机端布局 (600px)
    }
};

// 便捷的spacing计算函数
export const getSpacing = (px) => px / 8;

// 便捷的获取函数
export const getLayoutValues = () => LAYOUT_CONSTANTS;