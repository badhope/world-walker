#!/usr/bin/env python3
"""
================================================================================
区域产业经济分析平台 - 完整演示脚本
================================================================================

这个脚本执行完整的项目演示：
1. 数据收集（真实宏观经济数据）
2. 数据清洗和预处理
3. 探索性数据分析（EDA）
4. 可视化分析
5. 时间序列预测
6. 企业端分析
7. 数据库存储
8. 生成完整报告

适用于数据分析师简历展示
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 100)
print("🚀 区域产业经济分析平台 - 完整演示")
print("=" * 100)
print()

# =============================================================================
# 导入模块
# =============================================================================
print("[1/7] 导入必要模块...")

try:
    import pandas as pd
    import numpy as np
    
    from backend.analysis.real_data_analysis import real_data_analyzer
    from backend.analysis.enterprise_analyzer_v2 import enterprise_analyzer_v2
    from backend.database import get_db
    
    print("   ✅ 模块导入成功")
except ImportError as e:
    print(f"   ❌ 导入失败: {e}")
    print("   请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)

print()

# =============================================================================
# 步骤 1: 获取真实数据
# =============================================================================
print("[2/7] 获取真实宏观经济数据...")

try:
    df = real_data_analyzer.fetch_macro_data()
    print(f"   ✅ 数据获取成功: {df.shape[0]} 条记录")
    print(f"   📊 数据时间范围: {df['year'].min()} - {df['year'].max()}")
    print(f"   📈 可用指标: {', '.join([col for col in df.columns if col != 'year'])}")
except Exception as e:
    print(f"   ❌ 数据获取失败: {e}")
    sys.exit(1)

print()

# =============================================================================
# 步骤 2: 数据清洗和EDA
# =============================================================================
print("[3/7] 执行探索性数据分析（EDA）...")

try:
    eda_results = real_data_analyzer.perform_eda(df)
    print(f"   ✅ EDA完成")
    print(f"   📊 描述性统计已生成")
    
    stats = eda_results['summary_stats']
    if 'gdp' in stats:
        gdp_stats = stats['gdp']
        print(f"   💰 GDP均值: {gdp_stats.get('mean', 'N/A'):.2f} 亿元")
        print(f"   📈 GDP标准差: {gdp_stats.get('std', 'N/A'):.2f}")
except Exception as e:
    print(f"   ❌ EDA失败: {e}")
    sys.exit(1)

print()

# =============================================================================
# 步骤 3: 生成智能洞察
# =============================================================================
print("[4/7] 生成智能数据洞察...")

try:
    insights = real_data_analyzer.generate_insights(eda_results)
    print(f"   ✅ 生成了 {len(insights)} 条洞察")
    print()
    for i, insight in enumerate(insights[:3], 1):
        print(f"   {i}. [{insight['type']}] {insight['title']}")
        print(f"      {insight['content']}")
    if len(insights) > 3:
        print(f"      ... 还有 {len(insights) - 3} 条")
except Exception as e:
    print(f"   ❌ 洞察生成失败: {e}")
    sys.exit(1)

print()

# =============================================================================
# 步骤 4: 企业分析演示
# =============================================================================
print("[5/7] 企业端分析演示...")

sample_data = {
    "region": "深圳",
    "industry": "半导体",
    "year": 2025,
    "land_price": 850.0,
    "salary_level": 18000.0,
    "energy_cost": 1.3,
    "financing_cost": 4.8,
    "local_support_rate": 78.0,
    "avg_delivery_time": 3.5,
    "location_quotient": 2.8,
    "tax_reduction": 600.0,
    "tax_coverage": 88.0,
    "rd_subsidy": 280.0,
    "avg_approval_time": 4.2
}

try:
    enterprise_report = enterprise_analyzer_v2.generate_comprehensive_report(sample_data)
    print(f"   ✅ 企业分析完成")
    print()
    print(f"   📊 分析结果:")
    print(f"   ├─ 综合评分: {enterprise_report['overall_score']:.1f}/100")
    print(f"   ├─ 营商成本评分: {enterprise_report['business_costs']['total_cost_score']:.1f}")
    print(f"   ├─ 供应链配套评分: {enterprise_report['supply_chain']['supply_chain_score']:.1f}")
    print(f"   └─ 政策红利评分: {enterprise_report['policy_benefits']['policy_benefit_score']:.1f}")
    print()
    print(f"   💡 智能建议:")
    for i, rec in enumerate(enterprise_report['recommendations'][:3], 1):
        print(f"   {i}. [{rec['priority']}] {rec['content']}")
except Exception as e:
    print(f"   ❌ 企业分析失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# =============================================================================
# 步骤 5: 数据库存储
# =============================================================================
print("[6/7] 数据库存储演示...")

try:
    db = get_db()
    
    # 保存经济数据
    db.save_economic_dataframe(df)
    
    # 保存企业分析结果
    analysis_id = db.save_enterprise_analysis(
        sample_data['region'],
        sample_data['industry'],
        sample_data['year'],
        enterprise_report
    )
    
    # 获取统计信息
    stats = db.get_statistics()
    
    print(f"   ✅ 数据库存储成功")
    print(f"   📊 经济数据: {stats['economic_data_count']} 条")
    print(f"   🏢 企业分析: {stats['enterprise_analysis_count']} 条")
    print(f"   📆 数据年份: {stats['data_year_range']}")
except Exception as e:
    print(f"   ❌ 数据库操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# =============================================================================
# 步骤 6: 可视化生成
# =============================================================================
print("[7/7] 生成分析图表...")

try:
    viz_data = real_data_analyzer.get_visualization_data(df)
    
    charts_dir = project_root / "data" / "charts"
    charts_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"   ✅ 可视化数据准备完成")
    print(f"   📁 图表目录: {charts_dir}")
except Exception as e:
    print(f"   ❌ 可视化生成失败: {e}")
    sys.exit(1)

print()

# =============================================================================
# 总结
# =============================================================================
print("=" * 100)
print("🎉 完整演示执行成功！")
print("=" * 100)
print()
print("📁 项目文件结构:")
print()
print("  ├── backend/")
print("  │   ├── analysis/")
print("  │   │   ├── real_data_analysis.py     - 真实数据分析模块")
print("  │   │   └── enterprise_analyzer_v2.py  - 企业分析模块 v2")
print("  │   └── database/")
print("  │       └── database.py                - 数据库管理模块")
print("  │")
print("  ├── notebooks/")
print("  │   └── 01_data_collection_analysis.py  - 完整EDA流程")
print("  │")
print("  ├── tests/")
print("  │   └── backend/")
print("  │       └── test_real_data_analysis.py - 单元测试")
print("  │")
print("  └── data/")
print("      ├── regional_economy.db           - SQLite数据库")
print("      ├── charts/                        - 分析图表")
print("      └── analysis_output/                - 分析结果")
print()
print("💼 简历展示要点:")
print()
print("  1. 数据采集与清洗")
print("     - 使用 AKShare 获取真实宏观经济数据（GDP、CPI、PMI等）")
print("     - 处理缺失值和异常值，使用线性插值填充")
print()
print("  2. 探索性数据分析（EDA）")
print("     - 计算描述性统计量（均值、标准差、分位数）")
print("     - 相关性分析（使用 seaborn 热力图）")
print("     - 时间序列趋势分析")
print()
print("  3. 数据可视化")
print("     - Matplotlib 绘制 GDP 增长趋势图")
print("     - CPI 通胀率趋势图")
print("     - 产业结构饼图和演变图")
print()
print("  4. 评分模型")
print("     - 基于经济基准的多维度评分系统")
print("     - 营商成本、供应链配套、政策红利综合评估")
print()
print("  5. 数据持久化")
print("     - SQLite 数据库存储分析结果")
print("     - 支持历史数据查询")
print()
print("🎯 下一步:")
print()
print("  - 运行 EDA 完整流程: python notebooks/01_data_collection_analysis.py")
print("  - 运行单元测试: python -m pytest tests/backend/ -v")
print("  - 启动 API 服务: python -m uvicorn backend.api.main:app --reload --port 8001")
print()
print("=" * 100)
print("现在这个项目真的可以作为数据分析师作品展示了！")
print("=" * 100)
