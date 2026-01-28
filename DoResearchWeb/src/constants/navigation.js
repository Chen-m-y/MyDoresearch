import {
    BarChart as StatsIcon,
    Bookmark as ReadLaterIcon,
    Assignment as TasksIcon,
    Search as SearchIcon,
    Subscriptions as SubscriptionsIcon,
} from '@mui/icons-material';

export const navigationItems = [
    {
        id: 'stats',
        label: '统计',
        fullLabel: '统计分析',
        path: '/stats',
        icon: StatsIcon,
        subtitle: '阅读数据统计',
        description: '查看您的阅读统计和趋势分析',
        color: '#1976d2', // primary
    },
    {
        id: 'subscriptions',
        label: '订阅',
        fullLabel: '订阅管理',
        path: '/subscriptions',
        icon: SubscriptionsIcon,
        subtitle: '智能订阅管理',
        description: '使用智能订阅系统管理论文来源',
        color: '#7b1fa2', // purple
    },
    {
        id: 'readlater',
        label: '稍后读',
        fullLabel: '稍后阅读',
        path: '/readlater',
        icon: ReadLaterIcon,
        subtitle: '待深度阅读',
        description: '管理您的阅读队列和优先级',
        color: '#2e7d32', // success
    },
    {
        id: 'search',
        label: '搜索',
        fullLabel: '论文搜索',
        path: '/search',
        icon: SearchIcon,
        subtitle: '查找相关文献',
        description: '搜索和发现相关学术论文',
        color: '#0288d1', // info
    },
    {
        id: 'tasks',
        label: '任务',
        fullLabel: '任务管理',
        path: '/tasks',
        icon: TasksIcon,
        subtitle: '深度分析任务',
        description: '管理您的研究任务和进度',
        color: '#ed6c02', // warning
    },
];

export const getNavigationItemById = (id) => {
    return navigationItems.find(item => item.id === id);
};

export const getNavigationItemByPath = (path) => {
    return navigationItems.find(item => path.startsWith(item.path));
};

export default navigationItems;