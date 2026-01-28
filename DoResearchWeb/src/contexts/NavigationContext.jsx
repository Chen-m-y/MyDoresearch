import React, { createContext, useContext, useState } from 'react';

/**
 * 导航栏状态上下文
 * 用于在组件间共享导航栏的可见状态
 */
const NavigationContext = createContext({
    isBottomNavVisible: true,
    setBottomNavVisible: () => {},
});

export const NavigationProvider = ({ children }) => {
    const [isBottomNavVisible, setIsBottomNavVisible] = useState(true);
    
    const setBottomNavVisible = (visible) => {
        setIsBottomNavVisible(visible);
    };

    return (
        <NavigationContext.Provider 
            value={{ 
                isBottomNavVisible, 
                setBottomNavVisible 
            }}
        >
            {children}
        </NavigationContext.Provider>
    );
};

export const useNavigationContext = () => {
    const context = useContext(NavigationContext);
    if (!context) {
        throw new Error('useNavigationContext must be used within NavigationProvider');
    }
    return context;
};

export default NavigationProvider;