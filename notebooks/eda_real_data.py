"""
真实数据探索性分析 - Jupyter Notebook 风格的脚本

注意：这是一个可以生成真实数据 EDA 的脚本，
可以保存为 .ipynb 运行，或者直接运行这个脚本
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")  # 非交互式后端
from pathlib import Path

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

from backend.analysis.enterprise_analyzer_v2 import enterprise_analyzer_v2
from backend.analysis.real_data_analysis import real_data_analyzer


def run_eda():
    """运行完整 EDA"""
    print("=" * 80)
    print("区域产业经济分析 - 真实数据探索性分析")
    print("=" * 80)
    print()

    # 1. 获取数据
    print("📥 第1步：获取真实宏观经济数据")
    print("-" * 80)
    df = real_data_analyzer.fetch_macro_data()
    print(f"数据获取成功！数据形状: {df.shape}")
    print(f"数据时间范围: {df['year'].min()} - {df['year'].max()}")
    print()

    # 2. 数据预览
    print("📊 第2步：数据预览")
    print("-" * 80)
    print(df.head(10).to_string())
    print()

    # 3. 数据清洗
    print("🔧 第3步：数据清洗与质量检查")
    print("-" * 80)
    print("缺失值统计：")
    print(df.isnull().sum())
    print()
    print("数据类型：")
    print(df.dtypes)
    print()

    # 4. 描述性统计
    print("📈 第4步：描述性统计")
    print("-" * 80)
    desc_stats = df.describe(include=[np.number])
    print(desc_stats.to_string())
    print()

    # 5. 相关性分析
    print("🔗 第5步：相关性分析")
    print("-" * 80)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr_matrix = df[numeric_cols].corr()
    print("相关性矩阵 (部分):")
    print(corr_matrix[["gdp", "cpi_yoy", "gdp_primary", "gdp_secondary", "gdp_tertiary"]].head())
    print()

    # 6. 生成可视化
    print("🎨 第6步：生成可视化图表")
    print("-" * 80)
    viz_data = real_data_analyzer.get_visualization_data(df)

    # 创建输出目录
    output_dir = Path(__file__).parent.parent / "data" / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 图表1: GDP趋势图
    if viz_data.get("gdp_trend"):
        gt = viz_data["gdp_trend"]
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(gt["years"], gt["total_gdp"], marker="o", linewidth=2, label="总GDP")
        ax.plot(gt["years"], gt["primary"], marker="s", linewidth=1.5, label="第一产业")
        ax.plot(gt["years"], gt["secondary"], marker="^", linewidth=1.5, label="第二产业")
        ax.plot(gt["years"], gt["tertiary"], marker="d", linewidth=1.5, label="第三产业")
        ax.set_xlabel("年份", fontsize=12)
        ax.set_ylabel("GDP (亿元)", fontsize=12)
        ax.set_title("中国 GDP 及三次产业增长趋势 (2006-2025)", fontsize=14, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        gdp_chart_path = output_dir / "gdp_trend.png"
        plt.savefig(gdp_chart_path, dpi=150)
        plt.close()
        print(f"✅ GDP趋势图已保存至: {gdp_chart_path}")

    # 图表2: CPI趋势
    if viz_data.get("cpi_trend"):
        ct = viz_data["cpi_trend"]
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(ct["years"], ct["cpi_yoy"], marker="o", linewidth=2, color="#e74c3c")
        ax.axhline(y=3, color="green", linestyle="--", alpha=0.5, label="温和通胀线(3%)")
        ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
        ax.set_xlabel("年份", fontsize=12)
        ax.set_ylabel("CPI同比 (%)", fontsize=12)
        ax.set_title("中国 CPI 同比增长率趋势", fontsize=14, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        cpi_chart_path = output_dir / "cpi_trend.png"
        plt.savefig(cpi_chart_path, dpi=150)
        plt.close()
        print(f"✅ CPI趋势图已保存至: {cpi_chart_path}")

    # 图表3: 产业结构饼图
    if viz_data.get("industry_structure"):
        ist = viz_data["industry_structure"]
        fig, ax = plt.subplots(figsize=(10, 10))
        labels = ["第一产业", "第二产业", "第三产业"]
        sizes = [ist["primary"], ist["secondary"], ist["tertiary"]]
        colors = ["#3498db", "#e74c3c", "#2ecc71"]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, textprops={"fontsize": 12}
        )
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
        ax.set_title(f"中国三次产业结构 ({ist['year']})", fontsize=14, fontweight="bold")
        ax.axis("equal")
        plt.tight_layout()
        industry_chart_path = output_dir / "industry_structure.png"
        plt.savefig(industry_chart_path, dpi=150)
        plt.close()
        print(f"✅ 产业结构图已保存至: {industry_chart_path}")

    print()

    # 7. 企业端分析测试
    print("🏢 第7步：企业端分析测试")
    print("-" * 80)
    sample_data = {
        "region": "深圳",
        "industry": "半导体",
        "year": 2025,
        "land_price": 950.0,
        "salary_level": 18000.0,
        "energy_cost": 1.3,
        "financing_cost": 4.8,
        "local_support_rate": 82.0,
        "avg_delivery_time": 3.5,
        "location_quotient": 2.8,
        "tax_reduction": 600.0,
        "tax_coverage": 88.0,
        "rd_subsidy": 250.0,
        "avg_approval_time": 4.5,
    }

    report = enterprise_analyzer_v2.generate_comprehensive_report(sample_data)
    print("企业端分析报告已生成！")
    print(f"总体评分: {report['overall_score']:.1f}")
    print(f"营商成本评分: {report['business_costs']['total_cost_score']:.1f}")
    print(f"供应链配套评分: {report['supply_chain']['supply_chain_score']:.1f}")
    print(f"政策红利评分: {report['policy_benefits']['policy_benefit_score']:.1f}")
    print()
    print("智能建议:")
    for rec in report["recommendations"]:
        print(f"  [{rec['priority']}] {rec['content']}")
    print()

    # 8. 生成洞察
    print("💡 第8步：生成数据洞察")
    print("-" * 80)
    eda_results = real_data_analyzer.perform_eda(df)
    insights = real_data_analyzer.generate_insights(eda_results)
    print(f"共生成 {len(insights)} 条洞察：")
    for i, insight in enumerate(insights, 1):
        icon = (
            "✅"
            if insight["type"] == "positive"
            else "⚠️"
            if insight["type"] == "warning"
            else "❌"
            if insight["type"] == "negative"
            else "ℹ️"
        )
        print(f"{icon} 洞察 {i}: {insight['title']}")
        print(f"   {insight['content']}")

    print()
    print("=" * 80)
    print("✅ EDA完成！")
    print("=" * 80)
    print(f"图表保存在: {output_dir}")
    print()
    return report


if __name__ == "__main__":
    run_eda()
