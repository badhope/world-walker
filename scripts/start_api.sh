#!/bin/bash
################################################################################
# 启动API服务脚本
# 区域产业经济分析平台
#
# 功能：
# 1. 检查环境依赖
# 2. 启动FastAPI服务
# 3. 自动打开API文档页面
#
# 使用方法：
#   bash scripts/start_api.sh              # 默认配置启动
#   bash scripts/start_api.sh --port 8080  # 自定义端口
#   bash scripts/start_api.sh --reload     # 开发模式（代码热重载）
#   bash scripts/start_api.sh --host 127.0.0.1  # 本地访问
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 默认配置
HOST="0.0.0.0"
PORT=8001
RELOAD=false
AUTO_OPEN=true

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --reload)
            RELOAD=true
            shift
            ;;
        --no-open)
            AUTO_OPEN=false
            shift
            ;;
        --help)
            echo "使用方法:"
            echo "  bash scripts/start_api.sh              # 默认配置"
            echo "  bash scripts/start_api.sh --port 8080 # 自定义端口"
            echo "  bash scripts/start_api.sh --reload     # 开发模式"
            echo "  bash scripts/start_api.sh --host 127.0.0.1  # 本地访问"
            echo "  bash scripts/start_api.sh --no-open   # 不自动打开浏览器"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# 检查环境
check_environment() {
    print_info "检查运行环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查必要模块
    python3 -c "import fastapi" 2>/dev/null || {
        print_error "FastAPI 未安装"
        print_info "请运行: pip install fastapi uvicorn"
        exit 1
    }
    
    python3 -c "import uvicorn" 2>/dev/null || {
        print_error "uvicorn 未安装"
        print_info "请运行: pip install uvicorn"
        exit 1
    }
    
    print_success "环境检查通过 ✓"
}

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $PORT 已被占用"
        print_info "尝试关闭占用进程..."
        
        # 获取进程ID
        PID=$(lsof -ti:$PORT)
        
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null || {
                print_error "无法关闭占用端口的进程"
                print_info "请手动关闭或使用其他端口: --port $((PORT+1))"
                exit 1
            }
            
            sleep 2
            print_success "已关闭占用端口的进程"
        fi
    fi
}

# 自动打开浏览器
open_browser() {
    if [ "$AUTO_OPEN" = true ]; then
        print_info "将在3秒后自动打开浏览器..."
        sleep 3
        
        case "$(uname)" in
            Darwin)
                open "http://localhost:$PORT/docs"
                ;;
            Linux)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:$PORT/docs" 2>/dev/null || {
                        print_warning "无法自动打开浏览器，请手动访问:"
                        print_info "  http://localhost:$PORT/docs"
                    }
                fi
                ;;
            MINGW*|CYGWIN*)
                start "http://localhost:$PORT/docs"
                ;;
            *)
                print_info "请手动访问: http://localhost:$PORT/docs"
                ;;
        esac
    fi
}

# 启动API
start_api() {
    print_info "启动API服务..."
    echo ""
    
    # 构建命令
    CMD="python3 -m uvicorn backend.api.main:app --host $HOST --port $PORT"
    
    if [ "$RELOAD" = true ]; then
        CMD="$CMD --reload"
        print_warning "开发模式已启用（代码热重载）"
    fi
    
    print_info "API配置:"
    echo "  地址: http://$HOST:$PORT"
    echo "  文档: http://$HOST:$PORT/docs"
    echo "  API:  http://$HOST:$PORT/api/v1"
    echo ""
    
    # 检查端口
    check_port
    
    # 启动服务
    eval $CMD
}

# 主函数
main() {
    echo ""
    echo "========================================================================"
    echo "  区域产业经济分析平台 - API服务"
    echo "========================================================================"
    echo ""
    
    # 检查环境
    check_environment
    
    # 启动API
    start_api
}

# 运行主函数
main
