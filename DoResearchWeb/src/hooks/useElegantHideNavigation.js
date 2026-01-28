import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * 优雅的导航栏自动隐藏 Hook
 * 采用简单而直观的交互逻辑
 */
export const useElegantHideNavigation = (options = {}) => {
    const {
        // 无操作后隐藏的延迟时间（毫秒）
        autoHideDelay = 3500,
        // 触摸区域高度（像素）
        touchZoneHeight = 30,
        // 是否启用功能
        enabled = true,
    } = options;

    const [isVisible, setIsVisible] = useState(true);
    const hideTimer = useRef(null);
    const location = useLocation();
    const lastPathname = useRef(location.pathname);

    // 清除隐藏定时器
    const clearHideTimer = useCallback(() => {
        if (hideTimer.current) {
            clearTimeout(hideTimer.current);
            hideTimer.current = null;
        }
    }, []);

    // 启动隐藏定时器
    const startHideTimer = useCallback(() => {
        clearHideTimer();
        if (enabled) {
            hideTimer.current = setTimeout(() => {
                setIsVisible(false);
            }, autoHideDelay);
        }
    }, [enabled, autoHideDelay, clearHideTimer]);

    // 显示导航栏并重置定时器
    const showAndResetTimer = useCallback(() => {
        setIsVisible(true);
        startHideTimer();
    }, [startHideTimer]);

    // 立即显示导航栏
    const show = useCallback(() => {
        showAndResetTimer();
    }, [showAndResetTimer]);

    // 立即隐藏导航栏
    const hide = useCallback(() => {
        setIsVisible(false);
        clearHideTimer();
    }, [clearHideTimer]);

    // 检测滚动到顶部
    const handleScroll = useCallback((event) => {
        if (!enabled) return;

        let scrollTop = 0;
        
        if (event && event.target && event.target !== window) {
            scrollTop = event.target.scrollTop;
        } else {
            scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        }

        // 如果滚动到顶部（前50px），显示导航栏
        if (scrollTop <= 50) {
            showAndResetTimer();
        }
    }, [enabled, showAndResetTimer]);

    // 处理触摸事件 - 更精确的判断
    const handleTouch = useCallback((event) => {
        if (!enabled) return;
        
        const touch = event.touches[0];
        if (!touch) return;
        
        const windowHeight = window.innerHeight;
        const touchY = touch.clientY;
        
        // 只有触摸底部区域时才显示导航栏
        if (windowHeight - touchY <= touchZoneHeight) {
            // 确保不是在内容元素上的触摸
            const target = event.target;
            const isContentTouch = target && (
                target.closest('button, a, input, textarea, select') ||
                target.closest('.MuiButton-root, .MuiIconButton-root, .MuiCard-root')
            );
            
            if (!isContentTouch) {
                showAndResetTimer();
            }
        }
    }, [enabled, touchZoneHeight, showAndResetTimer]);

    // 处理鼠标移动（桌面端） - 降低敏感度并排除按钮区域
    const lastMouseMoveTime = useRef(0);
    const handleMouseMove = useCallback((event) => {
        if (!enabled) return;
        
        // 节流：限制处理频率
        const now = Date.now();
        if (now - lastMouseMoveTime.current < 200) { // 200ms 节流
            return;
        }
        lastMouseMoveTime.current = now;
        
        const windowHeight = window.innerHeight;
        const mouseY = event.clientY;
        
        // 检查鼠标是否在导航按钮区域
        const target = event.target;
        const isOverNavButton = target && (
            target.closest('[data-testid="ArrowBackIcon"], [data-testid="ArrowForwardIcon"]') ||
            target.closest('.MuiIconButton-root') ||
            target.closest('[aria-label*="导航"], [aria-label*="前一个"], [aria-label*="后一个"]')
        );
        
        // 如果鼠标在导航按钮上，不触发导航栏显示
        if (isOverNavButton) {
            return;
        }
        
        // 鼠标靠近底部时显示导航栏
        if (windowHeight - mouseY <= touchZoneHeight + 10) {
            showAndResetTimer();
        }
    }, [enabled, touchZoneHeight, showAndResetTimer]);

    // 处理用户交互（点击、键盘等） - 更智能的判断
    const handleUserActivity = useCallback((event) => {
        if (!enabled) return;
        
        // 排除一些不应该触发导航栏显示的交互
        const target = event.target;
        const eventType = event.type;
        
        // 如果是键盘事件，只响应导航相关的按键
        if (eventType === 'keydown') {
            const key = event.key;
            // 只有这些按键才显示导航栏
            const navigationKeys = ['Tab', 'Escape', 'Home', 'End', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
            if (!navigationKeys.includes(key)) {
                return; // 忽略其他按键
            }
        }
        
        // 如果是点击事件，检查点击的元素
        if (eventType === 'click' && target) {
            // 排除一些内容交互元素
            const excludedElements = ['BUTTON', 'A', 'INPUT', 'TEXTAREA', 'SELECT'];
            const excludedClasses = [
                'MuiCollapse-root',
                'MuiAccordion-root', 
                'MuiCard-root',
                'MuiCardContent-root',
                'MuiCardActions-root',
                'MuiExpansionPanel-root',
                'MuiTab-root',
                'MuiTabs-root'
            ];
            
            // 检查元素标签
            if (excludedElements.includes(target.tagName)) {
                return;
            }
            
            // 检查元素类名
            const hasExcludedClass = excludedClasses.some(className => 
                target.classList?.contains(className) || 
                target.closest(`.${className}`)
            );
            
            if (hasExcludedClass) {
                return;
            }
            
            // 检查是否在主内容区域内的交互
            const isInMainContent = target.closest('main') || target.closest('[role="main"]');
            if (isInMainContent) {
                // 主内容区域的点击不触发导航栏显示，除非点击的是空白区域
                const isContentElement = target.closest('article, section, .paper-detail, .paper-content, .MuiPaper-root');
                if (isContentElement) {
                    return;
                }
            }
        }
        
        // 通过所有检查，触发显示导航栏
        showAndResetTimer();
    }, [enabled, showAndResetTimer]);

    // 监听各种事件 - 精简版本
    useEffect(() => {
        if (!enabled) {
            setIsVisible(true);
            return;
        }

        // 初始启动定时器
        startHideTimer();

        const scrollOptions = { passive: true };

        // 滚动检测 - 保留，用于滚动到顶部显示
        window.addEventListener('scroll', handleScroll, scrollOptions);
        const mainElement = document.querySelector('main');
        if (mainElement) {
            mainElement.addEventListener('scroll', handleScroll, scrollOptions);
        }

        // 触摸事件 - 保留，用于底部区域触摸
        document.addEventListener('touchstart', handleTouch, scrollOptions);
        
        // 暂时禁用鼠标移动检测，避免与导航按钮冲突
        // document.addEventListener('mousemove', handleMouseMove, scrollOptions);
        
        // 只监听导航相关的键盘事件
        document.addEventListener('keydown', handleUserActivity, scrollOptions);
        
        // 移除点击事件监听，避免内容交互误触

        return () => {
            clearHideTimer();
            
            window.removeEventListener('scroll', handleScroll, scrollOptions);
            if (mainElement) {
                mainElement.removeEventListener('scroll', handleScroll, scrollOptions);
            }
            
            document.removeEventListener('touchstart', handleTouch, scrollOptions);
            // document.removeEventListener('mousemove', handleMouseMove, scrollOptions);
            document.removeEventListener('keydown', handleUserActivity, scrollOptions);
        };
    }, [enabled, handleScroll, handleTouch, handleMouseMove, handleUserActivity, startHideTimer, clearHideTimer]);

    // 路由变化时的处理 - 完全保持当前状态不变
    useEffect(() => {
        if (!enabled) return;
        
        const currentPathname = location.pathname;
        
        // 检查路由是否真的发生了变化
        if (lastPathname.current !== currentPathname) {
            lastPathname.current = currentPathname;
            
            // 路由切换时完全保持当前状态，不做任何改变
            // 不重新启动定时器，避免在论文切换等场景下导航栏闪现
            // 用户如果需要显示导航栏，可以通过其他交互方式触发
        }
    }, [location.pathname, enabled]);

    // 组件卸载时清理
    useEffect(() => {
        return () => clearHideTimer();
    }, [clearHideTimer]);

    return {
        isVisible,
        show,
        hide,
        toggle: () => isVisible ? hide() : show(),
    };
};

export default useElegantHideNavigation;