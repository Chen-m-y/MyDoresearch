export const formatDate = (dateString) => {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);

        // 检查日期是否有效
        if (isNaN(date.getTime())) {
            console.warn('Invalid date:', dateString);
            return dateString; // 返回原始字符串
        }

        // 直接显示具体日期，不再显示相对时间
        return date.toLocaleDateString('zh-CN');
    } catch (error) {
        console.error('Date formatting error:', error, 'for date:', dateString);
        return dateString;
    }
};

export const formatDateTime = (dateString) => {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            return dateString;
        }

        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        console.error('DateTime formatting error:', error);
        return dateString;
    }
};

// 专门处理Agent心跳时间，显示相对时间
export const formatHeartbeatTime = (timestamp) => {
    if (!timestamp) return '从未';

    try {
        // 如果是Unix时间戳（秒），需要转换为毫秒
        const date = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);
        
        if (isNaN(date.getTime())) {
            console.warn('Invalid heartbeat timestamp:', timestamp);
            return String(timestamp);
        }

        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffSeconds = Math.floor(diffMs / 1000);
        const diffMinutes = Math.floor(diffSeconds / 60);
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSeconds < 60) {
            return `${diffSeconds}秒前`;
        } else if (diffMinutes < 60) {
            return `${diffMinutes}分钟前`;
        } else if (diffHours < 24) {
            return `${diffHours}小时前`;
        } else if (diffDays < 7) {
            return `${diffDays}天前`;
        } else {
            // 超过7天显示具体时间
            return date.toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    } catch (error) {
        console.error('Heartbeat time formatting error:', error, 'for timestamp:', timestamp);
        return String(timestamp);
    }
};

export const getDateKey = (date = new Date()) => {
    return date.getFullYear() + '-' +
        String(date.getMonth() + 1).padStart(2, '0') + '-' +
        String(date.getDate()).padStart(2, '0');
};

export const parseDate = (dateString) => {
    try {
        return new Date(dateString);
    } catch (error) {
        console.error('Date parsing error:', error);
        return new Date();
    }
};

// 专门用于"添加于"等场景的日期格式化：七天内显示相对时间，超过七天显示具体日期
export const formatRelativeDate = (dateString) => {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);

        // 检查日期是否有效
        if (isNaN(date.getTime())) {
            console.warn('Invalid date:', dateString);
            return dateString; // 返回原始字符串
        }

        const now = new Date();

        // 获取本地日期，避免时区问题
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const paperDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

        const diffTime = today.getTime() - paperDate.getTime();
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return '今天';
        } else if (diffDays === 1) {
            return '昨天';
        } else if (diffDays === -1) {
            return '明天'; // 未来的日期
        } else if (diffDays > 0 && diffDays <= 7) {
            return `${diffDays}天前`;
        } else {
            // 超过7天，显示具体日期
            return date.toLocaleDateString('zh-CN');
        }
    } catch (error) {
        console.error('Date formatting error:', error, 'for date:', dateString);
        return dateString;
    }
};