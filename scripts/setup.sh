#!/bin/bash
################################################################################
# 一键安装脚本
# 区域产业经济分析平台
#
# 功能：
# 1. 检查Python版本
# 2. 创建虚拟环境（可选）
# 3. 安装依赖
# 4. 配置环境变量
# 5. 初始化目录结构
#
# 使用方法：
#   bash scripts/setup.sh          # 标准安装
#   bash scripts/setup.sh --venv   # 使用虚拟环境
#   bash scripts/setup.sh --help   # 显示帮助
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
区域产业经济分析平台 - 一键安装脚本

使用方法:
    bash scripts/setup.sh [选项]

选项:
    --venv       使用虚拟环境安装（推荐）
    --no-venv    不使用虚拟环境（系统级安装）
    --upgrade    升级已安装的包
    --help       显示此帮助信息

示例:
    bash scripts/setup.sh --venv        # 推荐：使用虚拟环境
    bash scripts/setup.sh --no-venv     # 系统级安装
    bash scripts/setup.sh --upgrade      # 升级依赖

EOF
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        print_error "Python版本过低: $PYTHON_VERSION"
        print_error "需要Python 3.9或更高版本"
        exit 1
    fi
    
    print_success "Python版本: $PYTHON_VERSION ✓"
}

# 检查pip
check_pip() {
    print_info "检查pip..."
    
    if ! command -v pip3 &> /dev/null; then
        print_warning "pip3 未安装，尝试安装..."
        python3 -m ensurepip --default-pip
    fi
    
    print_success "pip可用 ✓"
}

# 创建虚拟环境
create_venv() {
    print_info "创建虚拟环境..."
    
    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在"
        read -p "是否重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            python3 -m venv venv
            print_success "虚拟环境已重新创建 ✓"
        else
            print_info "使用现有虚拟环境"
        fi
    else
        python3 -m venv venv
        print_success "虚拟环境创建成功 ✓"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    print_info "虚拟环境已激活"
}

# 安装依赖
install_dependencies() {
    print_info "安装依赖包..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装核心依赖
    print_info "安装核心依赖..."
    pip install -r requirements.txt
    
    print_success "依赖安装完成 ✓"
}

# 安装开发依赖（可选）
install_dev_dependencies() {
    print_info "安装开发依赖..."
    
    pip install pytest pytest-cov black flake8 mypy
    
    print_success "开发依赖安装完成 ✓"
}

# 配置环境变量
setup_environment() {
    print_info "配置环境变量..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success ".env文件已创建 ✓"
            print_warning "请根据需要修改.env文件中的配置"
        else
            print_warning ".env.example文件不存在，跳过环境变量配置"
        fi
    else
        print_success ".env文件已存在 ✓"
    fi
}

# 初始化目录结构
setup_directories() {
    print_info "初始化目录结构..."
    
    directories=(
        "data"
        "data/raw"
        "data/processed"
        "data/cache"
        "data/exports"
        "logs"
        "tests"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_info "  创建目录: $dir"
        fi
    done
    
    print_success "目录结构初始化完成 ✓"
}

# 运行测试
run_tests() {
    print_info "运行测试..."
    
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short || print_warning "部分测试失败，请检查"
    else
        print_warning "pytest未安装，跳过测试"
    fi
}

# 主函数
main() {
    USE_VENV=false
    INSTALL_DEV=false
    UPGRADE=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --venv)
                USE_VENV=true
                shift
                ;;
            --no-venv)
                USE_VENV=false
                shift
                ;;
            --dev)
                INSTALL_DEV=true
                shift
                ;;
            --upgrade)
                UPGRADE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo ""
    echo "========================================================================"
    echo "  区域产业经济分析平台 - 一键安装脚本"
    echo "========================================================================"
    echo ""
    
    # 检查环境
    check_python
    check_pip
    
    # 创建虚拟环境（如果需要）
    if [ "$USE_VENV" = true ]; then
        create_venv
    fi
    
    # 安装依赖
    if [ "$UPGRADE" = true ]; then
        print_info "升级模式: 安装/升级依赖..."
        pip install --upgrade -r requirements.txt
    else
        install_dependencies
    fi
    
    # 安装开发依赖（如果需要）
    if [ "$INSTALL_DEV" = true ]; then
        install_dev_dependencies
    fi
    
    # 配置环境
    setup_environment
    setup_directories
    
    # 运行测试
    if [ "$INSTALL_DEV" = true ]; then
        run_tests
    fi
    
    # 完成
    echo ""
    echo "========================================================================"
    echo "  安装完成"
    echo "========================================================================"
    echo ""
    
    if [ "$USE_VENV" = true ]; then
        echo "下一步："
        echo "  1. 激活虚拟环境: source venv/bin/activate"
        echo "  2. 运行示例分析:  bash scripts/run_example.sh"
        echo "  3. 启动API服务:   bash scripts/start_api.sh"
    else
        echo "下一步："
        echo "  1. 运行示例分析: python main.py --mode example"
        echo "  2. 启动API服务:  python main.py --mode api"
    fi
    
    echo ""
    echo "文档和帮助："
    echo "  📖 README:     cat README.md"
    echo "  📚 使用指南:   cat docs/USAGE_GUIDE.md"
    echo "  ⚙️  配置指南:  cat docs/CONFIG_GUIDE.md"
    echo ""
}

# 运行主函数
main "$@"
