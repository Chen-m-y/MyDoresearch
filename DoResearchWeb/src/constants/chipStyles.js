// 共享的Chip样式配置

/**
 * 创建计数Chip的统一样式（基于FeedsView原来的淡蓝色样式）
 * @param {object} theme - MUI主题对象
 * @param {object} options - 可选配置
 * @param {string} options.size - 尺寸，默认为 'small' 
 * @returns {object} Chip的sx样式对象
 */
export const createCountChipStyles = (theme, options = {}) => {
    const {
        size = 'small'
    } = options;
    
    return {
        height: size === 'small' ? '20px' : '24px',
        minWidth: size === 'small' ? '20px' : '24px',
        borderRadius: size === 'small' ? '10px' : '12px',
        fontSize: size === 'small' ? '0.65rem' : '0.7rem',
        fontWeight: 600,
        background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
        color: '#1976d2',
        border: '1px solid rgba(25, 118, 210, 0.2)',
        '& .MuiChip-label': {
            px: size === 'small' ? 0.5 : 0.75,
        }
    };
};

/**
 * 状态Chip样式（如活跃/暂停状态）
 * @param {object} theme - MUI主题对象
 * @param {boolean} active - 是否为活跃状态
 * @returns {object} Chip的sx样式对象
 */
export const createStatusChipStyles = (theme, active) => {
    if (active) {
        return {
            background: `linear-gradient(135deg, ${theme.palette.success.main}80 0%, ${theme.palette.success.main}90 100%)`,
            color: 'white',
            border: `1px solid ${theme.palette.success.main}30`,
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                right: 0,
                width: '12px',
                height: '12px',
                background: `radial-gradient(circle, ${theme.palette.success.main}20 0%, transparent 70%)`,
                transform: 'translate(4px, -4px)',
            },
            '& .MuiChip-label': {
                position: 'relative',
                zIndex: 1,
            },
        };
    }
    
    return {
        background: `linear-gradient(135deg, ${theme.palette.grey[300]}50 0%, ${theme.palette.grey[400]}60 100%)`,
        color: theme.palette.grey[700],
        border: `1px solid ${theme.palette.grey[400]}40`,
    };
};

export default {
    createCountChipStyles,
    createStatusChipStyles
};