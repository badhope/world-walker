#!/bin/bash
################################################################################
# 运行示例分析脚本
# 区域产业经济分析平台
#
# 功能：
# 1. 检查环境依赖
# 2. 运行企业端分析
# 3. 运行政府端分析
# 4. 生成综合报告
#
# 使用方法：
#   bash scripts/run_example.sh              # 运行所有示例
#   bash scripts/run_example.sh enterprise   # 仅企业端分析
#   bash scripts/run_example.sh government   # 仅政府端分析
#   bash scripts/run_example.sh report       # 仅生成报告
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

# 检查环境
check_environment() {
    print_info "检查运行环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查必要目录
    if [ ! -d "examples/shenzhen_semiconductor_2025" ]; then
        print_error "示例目录不存在"
        exit 1
    fi
    
    print_success "环境检查通过 ✓"
}

# 运行企业端分析
run_enterprise() {
    print_info "🏢 运行企业端分析..."
    echo ""
    
    python3 examples/shenzhen_semiconductor_2025/enterprise_analysis.py
    
    if [ $? -eq 0 ]; then
        print_success "企业端分析完成 ✓"
    else
        print_error "企业端分析失败"
        exit 1
    fi
}

# 运行政府端分析
run_government() {
    print_info "🏛️ 运行政府端分析..."
    echo ""
    
    python3 examples/shenzhen_semiconductor_2025/government_analysis.py
    
    if [ $? -eq 0 ]; then
        print_success "政府端分析完成 ✓"
    else
        print_error "政府端分析失败"
        exit 1
    fi
}

# 生成综合报告
generate_report() {
    print_info "生成综合分析报告..."
    echo ""
    
    python3 examples/shenzhen_semiconductor_2025/generate_report.py
    
    if [ $? -eq 0 ]; then
        print_success "综合报告生成完成 ✓"
    else
        print_error "综合报告生成失败"
        exit 1
    fi
}

# 显示示例输出
show_outputs() {
    print_info "📁 示例输出文件:"
    echo ""
    
    if [ -d "examples/shenzhen_semiconductor_2025/outputs" ]; then
        ls -lh examples/shenzhen_semiconductor_2025/outputs/ 2>/dev/null | grep -E '\.(json|html)$' | awk '{print "  " $9 " (" $5 ")"}'
    fi
    
    echo ""
}

# 主函数
main() {
    MODE="${1:-all}"
    
    echo ""
    echo "========================================================================"
    echo "  区域产业经济分析平台 - 运行示例"
    echo "========================================================================"
    echo ""
    
    # 检查环境
    check_environment
    
    # 根据模式运行
    case $MODE in
        enterprise)
            print_info "模式: 仅企业端分析"
            run_enterprise
            ;;
        government)
            print_info "模式: 仅政府端分析"
            run_government
            ;;
        report)
            print_info "模式: 仅生成报告"
            generate_report
            ;;
        all|*)
            print_info "模式: 运行所有示例"
            run_enterprise
            echo ""
            echo "------------------------------------------------------------------------"
            echo ""
            run_government
            echo ""
            echo "------------------------------------------------------------------------"
            echo ""
            generate_report
            ;;
    esac
    
    # 显示输出
    show_outputs
    
    # 完成
    echo ""
    echo "========================================================================"
    echo "  示例运行完成"
    echo "========================================================================"
    echo ""
    echo "查看HTML报告："
    echo "  打开 examples/shenzhen_semiconductor_2025/outputs/ 目录"
    echo "  找到 comprehensive_report_*.html 文件用浏览器打开"
    echo ""
}

# 运行主函数
main "$@"
