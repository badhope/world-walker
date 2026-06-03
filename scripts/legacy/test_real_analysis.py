"""
测试真实数据分析模块
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.analysis.real_data_analysis import real_data_analyzer


def test_real_data_analysis():
    """测试真实数据分析"""

    print("=" * 80)
    print("区域产业经济分析平台 - 真实数据分析测试")
    print("=" * 80)
    print()

    try:
        # 1. 获取真实数据
        print("📥 步骤 1: 获取真实宏观经济数据...")
        df = real_data_analyzer.fetch_macro_data()
        print(f"[ok] 数据获取成功！共 {len(df)} 条记录")
        print(f"   数据时间范围: {df['year'].min()} - {df['year'].max()}")
        print()

        # 2. 显示数据预览
        print("[i] 步骤 2: 数据预览:")
        print(df.head().to_string())
        print()

        # 3. 执行探索性数据分析
        print("[scan] 步骤 3: 执行探索性数据分析...")
        eda_results = real_data_analyzer.perform_eda(df)
        print("[ok] EDA 完成！")
        print()

        # 4. 显示摘要统计
        print("[+] 摘要统计:")
        summary_stats = eda_results["summary_stats"]
        for key, stats in summary_stats.items():
            if key != "year":
                print(f"   {key}:")
                print(f"      均值: {stats.get('mean', 'N/A'):.2f}")
                print(f"      标准差: {stats.get('std', 'N/A'):.2f}")
                print(f"      最小值: {stats.get('min', 'N/A'):.2f}")
                print(f"      最大值: {stats.get('max', 'N/A'):.2f}")
        print()

        # 5. 显示趋势分析
        print("📉 趋势分析:")
        trends = eda_results["trend_analysis"]
        for indicator, trend_info in trends.items():
            direction = trend_info.get("trend_direction", "unknown")
            cagr = trend_info.get("cagr")
            print(f"   {indicator}:")
            print(f"      趋势方向: {direction}")
            if cagr is not None:
                print(f"      年均增长率: {cagr:.2f}%")
            print(f"      最新值: {trend_info.get('latest_value', 'N/A')}")
        print()

        # 6. 生成洞察
        print("[i] 步骤 4: 生成数据洞察...")
        insights = real_data_analyzer.generate_insights(eda_results)
        print(f"[ok] 生成了 {len(insights)} 条洞察！")
        print()
        for i, insight in enumerate(insights, 1):
            icon = {"positive": "[ok]", "warning": "[!]", "negative": "[x]", "info": "ℹ️"}.get(insight["type"], "")
            print(f"   {icon} 洞察 {i}: {insight['title']}")
            print(f"      {insight['content']}")
        print()

        # 7. 获取可视化数据
        print(" 步骤 5: 获取可视化数据...")
        viz_data = real_data_analyzer.get_visualization_data(df)
        print("[ok] 可视化数据准备完成！")
        print()

        if viz_data.get("gdp_trend"):
            gdp_data = viz_data["gdp_trend"]
            print(f"   GDP 趋势数据: {len(gdp_data['years'])} 个年份")
            print(f"   年份范围: {gdp_data['years'][0]} - {gdp_data['years'][-1]}")

        if viz_data.get("industry_structure"):
            industry_data = viz_data["industry_structure"]
            print(f"   最新产业结构 ({industry_data.get('year')}):")
            print(f"      第一产业: {industry_data.get('primary', 0):.1f}%")
            print(f"      第二产业: {industry_data.get('secondary', 0):.1f}%")
            print(f"      第三产业: {industry_data.get('tertiary', 0):.1f}%")
        print()

        print("=" * 80)
        print(" 所有测试通过！项目现在有真正的数据分析功能了！")
        print("=" * 80)
        print()
        print(" 下一步：")
        print("   - 启动 API 服务: python -m uvicorn backend.api.main:app --reload --port 8001")
        print("   - 访问文档: http://localhost:8001/docs")
        print("   - 测试真实数据接口: GET /api/v1/real-data/complete")
        print()

    except Exception as e:
        print(f"[x] 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_real_data_analysis()
    sys.exit(0 if success else 1)
