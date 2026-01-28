// 文件: src/main.jsx

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'; // 1. 导入 BrowserRouter
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
    <StrictMode>
        {/* 2. 用 BrowserRouter 包裹 App 组件 */}
        <BrowserRouter>
            <App />
        </BrowserRouter>
    </StrictMode>,
)