#!/bin/bash

# =================================
# do_research_fetch 微服务部署脚本
# =================================

set -e  # 遇到错误时退出

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_NC='\033[0m' # No Color

echo -e "${COLOR_BLUE}==================================${COLOR_NC}"
echo -e "${COLOR_BLUE}do_research_fetch 微服务部署脚本${COLOR_NC}"
echo -e "${COLOR_BLUE}==================================${COLOR_NC}"
echo

# 检查系统要求
check_requirements() {
    echo -e "${COLOR_YELLOW}1. 检查系统要求...${COLOR_NC}"
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        echo -e "${COLOR_GREEN}✓ Python3 版本: $python_version${COLOR_NC}"
    else
        echo -e "${COLOR_RED}✗ Python3 未安装${COLOR_NC}"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        echo -e "${COLOR_GREEN}✓ pip3 已安装${COLOR_NC}"
    else
        echo -e "${COLOR_RED}✗ pip3 未安装${COLOR_NC}"
        exit 1
    fi
    
    # 检查Docker（可选）
    if command -v docker &> /dev/null; then
        echo -e "${COLOR_GREEN}✓ Docker 已安装${COLOR_NC}"
        DOCKER_AVAILABLE=true
    else
        echo -e "${COLOR_YELLOW}⚠ Docker 未安装 (可选)${COLOR_NC}"
        DOCKER_AVAILABLE=false
    fi
    
    echo
}

# 创建必要目录
create_directories() {
    echo -e "${COLOR_YELLOW}2. 创建必要目录...${COLOR_NC}"
    
    mkdir -p logs
    echo -e "${COLOR_GREEN}✓ 创建 logs 目录${COLOR_NC}"
    
    echo
}

# 安装Python依赖
install_dependencies() {
    echo -e "${COLOR_YELLOW}3. 安装Python依赖...${COLOR_NC}"
    
    if [ -f "requirements.txt" ]; then
        echo "正在安装依赖包..."
        pip3 install -r requirements.txt
        echo -e "${COLOR_GREEN}✓ 依赖包安装完成${COLOR_NC}"
    else
        echo -e "${COLOR_RED}✗ requirements.txt 文件不存在${COLOR_NC}"
        exit 1
    fi
    
    echo
}

# 配置环境变量
setup_environment() {
    echo -e "${COLOR_YELLOW}4. 配置环境变量...${COLOR_NC}"
    
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${COLOR_GREEN}✓ 已创建 .env 文件（从 .env.example 复制）${COLOR_NC}"
        echo -e "${COLOR_YELLOW}⚠ 请编辑 .env 文件设置API密钥${COLOR_NC}"
    elif [ -f ".env" ]; then
        echo -e "${COLOR_GREEN}✓ .env 文件已存在${COLOR_NC}"
    else
        echo -e "${COLOR_RED}✗ .env.example 文件不存在${COLOR_NC}"
        exit 1
    fi
    
    echo
}

# 验证项目结构
validate_structure() {
    echo -e "${COLOR_YELLOW}5. 验证项目结构...${COLOR_NC}"
    
    required_files=("app.py" "config.py" "requirements.txt" "adapters/registry.py")
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${COLOR_GREEN}✓ $file${COLOR_NC}"
        else
            echo -e "${COLOR_RED}✗ $file 缺失${COLOR_NC}"
            exit 1
        fi
    done
    
    echo
}

# 运行基本测试
run_tests() {
    echo -e "${COLOR_YELLOW}6. 运行基本测试...${COLOR_NC}"
    
    if [ -f "test_basic.py" ]; then
        echo "运行基本测试..."
        python3 test_basic.py
        echo -e "${COLOR_GREEN}✓ 基本测试通过${COLOR_NC}"
    else
        echo -e "${COLOR_YELLOW}⚠ test_basic.py 不存在，跳过测试${COLOR_NC}"
    fi
    
    echo
}

# 启动服务
start_service() {
    echo -e "${COLOR_YELLOW}7. 服务启动选项...${COLOR_NC}"
    echo
    echo "选择启动方式:"
    echo "1) 开发模式 (python3 run.py)"
    echo "2) 生产模式 (gunicorn)"
    echo "3) Docker 模式 (docker-compose up)"
    echo "4) 仅验证配置，不启动服务"
    echo
    
    read -p "请选择 [1-4]: " choice
    
    case $choice in
        1)
            echo -e "${COLOR_GREEN}启动开发模式...${COLOR_NC}"
            python3 run.py
            ;;
        2)
            echo -e "${COLOR_GREEN}启动生产模式...${COLOR_NC}"
            gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 app:app
            ;;
        3)
            if [ "$DOCKER_AVAILABLE" = true ]; then
                echo -e "${COLOR_GREEN}启动Docker模式...${COLOR_NC}"
                docker-compose up -d
                echo -e "${COLOR_GREEN}✓ 服务已在后台启动${COLOR_NC}"
                echo "查看日志: docker-compose logs -f"
                echo "停止服务: docker-compose down"
            else
                echo -e "${COLOR_RED}✗ Docker 不可用${COLOR_NC}"
            fi
            ;;
        4)
            echo -e "${COLOR_GREEN}✓ 配置验证完成${COLOR_NC}"
            ;;
        *)
            echo -e "${COLOR_RED}无效选择${COLOR_NC}"
            exit 1
            ;;
    esac
}

# 显示API信息
show_api_info() {
    echo
    echo -e "${COLOR_BLUE}==================================${COLOR_NC}"
    echo -e "${COLOR_BLUE}API 接口信息${COLOR_NC}"
    echo -e "${COLOR_BLUE}==================================${COLOR_NC}"
    echo
    echo "基础地址: http://localhost:8000"
    echo
    echo "主要接口:"
    echo "• 健康检查: GET /api/v1/health"
    echo "• 数据源列表: GET /api/v1/sources"
    echo "• 抓取论文: POST /api/v1/fetch"
    echo "• 批量抓取: POST /api/v1/fetch/batch"
    echo "• 服务指标: GET /api/v1/metrics"
    echo "• 缓存统计: GET /api/v1/cache/stats"
    echo "• 清空缓存: POST /api/v1/cache/clear"
    echo
    echo "测试命令:"
    echo "curl http://localhost:8000/api/v1/health"
    echo
    echo "支持的数据源:"
    echo "• IEEE Xplore (需要API密钥)"
    echo "• ScienceDirect (需要API密钥)"  
    echo "• DBLP (无需API密钥)"
    echo
}

# 主函数
main() {
    check_requirements
    create_directories
    install_dependencies
    setup_environment
    validate_structure
    run_tests
    start_service
    show_api_info
}

# 脚本选项处理
case "${1:-}" in
    "install")
        check_requirements
        install_dependencies
        setup_environment
        echo -e "${COLOR_GREEN}✓ 安装完成${COLOR_NC}"
        ;;
    "test")
        run_tests
        ;;
    "start")
        python3 run.py
        ;;
    "docker")
        if [ "$DOCKER_AVAILABLE" = true ]; then
            docker-compose up -d
        else
            echo -e "${COLOR_RED}✗ Docker 不可用${COLOR_NC}"
            exit 1
        fi
        ;;
    "help")
        echo "用法: $0 [命令]"
        echo
        echo "命令:"
        echo "  install  仅安装依赖和配置环境"
        echo "  test     仅运行测试"
        echo "  start    直接启动服务（开发模式）"
        echo "  docker   使用Docker启动"
        echo "  help     显示帮助"
        echo
        echo "无参数运行时将进入交互式设置"
        ;;
    *)
        main
        ;;
esac