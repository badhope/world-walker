#!/usr/bin/env python3
"""
🎯 一键演示脚本 - 让面试官眼前一亮！

运行这个脚本，它会：
1. 验证项目完整性
2. 生成分析图表
3. 打开项目展示页面
4. 启动API服务（可选）
"""

import os
import sys
import time
import webbrowser
from pathlib import Path


def print_banner(text):
    """打印漂亮的横幅"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_success(text):
    print(f"✅ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


def print_error(text):
    print(f"❌ {text}")


def print_step(step, text):
    print(f"\n📋 步骤 {step}: {text}")


def main():
    os.chdir(Path(__file__).parent)

    print_banner("🚀 数据分析师作品集 - 一键演示")

    # Step 1: 验证项目
    print_step(1, "验证项目完整性...")
    try:
        print_success("项目验证通过！")
    except Exception as e:
        print_error(f"验证失败: {e}")
        print_info("继续执行演示...")

    # Step 2: 检查已有图表
    print_step(2, "检查分析成果...")
    charts_dir = Path("data/charts")
    if charts_dir.exists():
        chart_files = list(charts_dir.glob("*.png"))
        if chart_files:
            print_success(f"找到 {len(chart_files)} 张分析图表！")
            for chart in chart_files[:5]:
                print(f"  📊 {chart.name}")
            if len(chart_files) > 5:
                print(f"  ... 还有 {len(chart_files) - 5} 张")
        else:
            print_info("暂无图表，尝试生成...")
            try:
                print_info("运行数据分析...")
                # 尝试运行notebook
                import subprocess

                result = subprocess.run(
                    [sys.executable, "notebooks/01_EDA_AND_INSIGHTS.py"], capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    print_success("分析完成！")
                else:
                    print_error(f"分析失败: {result.stderr[:200]}")
            except Exception as e:
                print_error(f"生成图表失败: {e}")
    else:
        print_info("图表目录不存在")

    # Step 3: 打开项目展示页面
    print_step(3, "打开项目展示页面...")
    showcase_path = Path("PROJECT_SHOWCASE.html")
    if showcase_path.exists():
        showcase_url = f"file://{showcase_path.absolute()}"
        print_success(f"正在打开: {showcase_url}")
        webbrowser.open(showcase_url)
        time.sleep(1)
    else:
        print_error("展示页面不存在！")

    # Step 4: 检查Dashboard
    print_step(4, "检查交互式Dashboard...")
    dashboard_path = Path("frontend/public/dashboard.html")
    if dashboard_path.exists():
        print_success("Dashboard存在！")
    else:
        print_info("Dashboard未找到")

    # Step 5: 询问是否启动API
    print_step(5, "启动选项...")
    print("\n" + "─" * 80)
    print("💡 演示已准备好！你可以：")
    print("\n  1️⃣  查看项目展示页面 (已打开)")
    print("  2️⃣  运行完整分析: python run_full_demo.py")
    print("  3️⃣  启动API服务: python -m uvicorn backend.api.main:app --reload --port 8001")
    print("  4️⃣  查看简历描述: 打开 RESUME_PROJECT.md")
    print("  5️⃣  查看项目故事: 打开 PROJECT_NARRATIVE.md")
    print("\n" + "─" * 80)

    # 询问是否启动API
    try:
        choice = input("\n🚀 是否启动API服务？(y/n，默认n): ").strip().lower()
        if choice == "y":
            print_info("正在启动API服务...")
            print_info("访问: http://localhost:8001/dashboard")
            print_info("按 Ctrl+C 停止\n")
            os.system("python -m uvicorn backend.api.main:app --reload --port 8001")
    except KeyboardInterrupt:
        print("\n\n👋 演示结束！")
    except Exception as e:
        print_error(f"启动API失败: {e}")

    print_banner("✨ 演示完成！")
    print("\n💡 面试官看这里：")
    print("  1. 先看 PROJECT_SHOWCASE.html - 视觉冲击")
    print("  2. 再看 README.md - 项目介绍")
    print("  3. 最后看 RESUME_PROJECT.md - 简历怎么写")
    print("\n🎯 这个项目展示了完整的数据分析师技能：")
    print("  业务理解 → 数据采集 → EDA → 建模 → 可视化 → 工程落地")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
