@echo off
chcp 65001 >nul
echo ============================================
echo   DoResearch Docker 环境启动脚本
echo ============================================
echo.

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未安装，请先安装 Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 检查 Docker Compose 是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Compose 未安装
    pause
    exit /b 1
)

echo [1/4] 检查环境配置文件...
if not exist ".env" (
    echo   复制 .env.example 为 .env ...
    copy ".env.example" ".env" >nul
    echo   [提示] 请编辑 .env 文件配置 API 密钥
)

echo.
echo [2/4] 构建并启动所有服务...
docker-compose up -d --build

echo.
echo [3/4] 等待服务启动...
timeout /t 10 /nobreak >nul

echo.
echo [4/4] 检查服务状态...
docker-compose ps

echo.
echo ============================================
echo   服务启动完成！
echo ============================================
echo.
echo   访问地址:
echo   - 前端页面: http://localhost:5173
echo   - 主后端API: http://localhost:5000
echo   - 论文获取API: http://localhost:8000
echo   - Redis: localhost:6379
echo.
echo   常用命令:
echo   - 查看日志: docker-compose logs -f
echo   - 停止服务: docker-compose down
echo   - 重启服务: docker-compose restart
echo.
pause
