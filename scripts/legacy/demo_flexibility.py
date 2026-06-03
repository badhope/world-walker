#!/usr/bin/env python3
"""
灵活扩展功能演示脚本
展示如何使用新增的灵活扩展系统
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.analysis.custom_indicators import (
    DictDataProvider,
    calculate_indicator,
    custom_indicator_engine,
    register_custom_formula,
)
from backend.analysis.indicator_registry import (
    IndicatorCategory,
    IndicatorDefinition,
    indicator_registry,
    search_indicators,
)

# 延迟导入，避免触发有外部依赖的模块
DATA_SOURCE_MANAGER = None

from backend.analysis.dimension_analysis import analysis_engine, analyze_dimension, register_analysis_dimension

try:
    from config.scenario_manager import ScenarioType, list_scenarios, register_scenario, scenario_manager, use_scenario

    SCENARIO_ENABLED = True
except ImportError:
    SCENARIO_ENABLED = False

try:
    from backend.utils.report_generator import (
        OutputFormat,
        ReportConfig,
        create_report_section,
        generate_report,
        report_generator,
    )

    REPORT_ENABLED = True
except ImportError:
    REPORT_ENABLED = False

def demo_indicator_registry():
    """演示指标注册系统"""
    print("\n" + "=" * 70)
    print("演示 1: 灵活的指标注册系统")
    print("=" * 70)

    # 查看现有指标
    print(f"\n[i] 已注册指标总数: {len(indicator_registry.get_all())}")

    # 按分类统计
    print("\n[+] 按分类统计:")
    for cat in IndicatorCategory:
        indicators = indicator_registry.get_by_category(cat)
        if indicators:
            print(f"  {cat.value}: {len(indicators)} 个指标")

    # 搜索指标
    print("\n[scan] 搜索包含 '成本' 的指标:")
    results = search_indicators("成本")
    for ind in results[:5]:
        print(f"  - {ind.code}: {ind.name} ({ind.unit})")

    # 注册自定义指标
    print("\n➕ 注册自定义指标:")
    custom_indicator = IndicatorDefinition(
        code="custom_efficiency",
        name="自定义效率指数",
        category=IndicatorCategory.BUSINESS,
        unit="%",
        description="用户自定义的效率评估指标",
        tags=["custom", "efficiency"],
    )
    indicator_registry.register(custom_indicator)
    print(f"  [ok] 注册成功: {custom_indicator.code}")

    # 导出指标配置
    export_path = Path(__file__).parent / "exports" / "indicators.json"
    export_path.parent.mkdir(exist_ok=True)
    indicator_registry.save_to_file(str(export_path))
    print(f"   指标配置已导出到: {export_path}")

def demo_custom_indicators():
    """演示自定义指标计算"""
    print("\n" + "=" * 70)
    print("演示 2: 自定义指标计算引擎")
    print("=" * 70)

    # 注册自定义公式
    print("\n 注册自定义公式:")
    register_custom_formula(
        "cost_effectiveness",
        "({output} / ({cost} * {time})) * 100",
        dependencies=["output", "cost", "time"],
        description="成本效益指数",
    )
    print("  [ok] 已注册: cost_effectiveness = (output / (cost * time)) * 100")

    # 使用数据计算
    print("\n🧮 计算自定义指标:")
    result = calculate_indicator("deficit_rate", {"revenue": 4512.0, "expenditure": 5056.8, "gdp": 36801.87})
    print(f"  赤字率计算结果: {result.value:.2f}% (状态: {result.status.value})")

    # 使用内置公式
    result2 = calculate_indicator("fiscal_self_sufficiency", {"revenue": 4512.0, "expenditure": 5056.8})
    print(f"  财政自给率: {result2.value:.2f}%")

    # 批量计算
    print("\n 批量计算:")
    provider = DictDataProvider({"revenue": 4512.0, "expenditure": 5056.8, "gdp": 36801.87})

    results = custom_indicator_engine.calculate_batch(
        ["deficit_rate", "fiscal_self_sufficiency", "tax_burden"], provider
    )

    for code, result in results.items():
        if result.status.value == "success":
            print(f"  [ok] {code}: {result.value}")

def demo_data_source_manager():
    """演示数据源管理"""
    print("\n" + "=" * 70)
    print("演示 3: 灵活的数据源管理系统")
    print("=" * 70)

    # 动态导入，避免触发有外部依赖的模块
    global DATA_SOURCE_MANAGER
    if DATA_SOURCE_MANAGER is None:
        import importlib

        dsm = importlib.import_module("backend.data_collection.data_source_manager")
        DATA_SOURCE_MANAGER = dsm

    data_source_manager = DATA_SOURCE_MANAGER.data_source_manager
    register_data_source = DATA_SOURCE_MANAGER.register_data_source
    fetch_from_source = DATA_SOURCE_MANAGER.fetch_from_source
    DataSourceType = DATA_SOURCE_MANAGER.DataSourceType

    # 注册新的数据源
    print("\n 注册数据源:")
    register_data_source(
        name="shenzhen_data",
        source_type="json_file",
        path="examples/shenzhen_semiconductor_2025/data/basic_data.json",
        tables=["basic_data", "semiconductor_industry"],
        priority=10,
    )
    print("  [ok] 注册成功: shenzhen_data")

    # 查看数据源状态
    print("\n[i] 数据源状态:")
    status = data_source_manager.get_status()
    print(f"  总数据源数: {status['total_sources']}")
    print(f"  启用的数据源: {status['enabled_sources']}")

    # 获取数据
    print("\n📥 获取数据:")
    data = fetch_from_source("semiconductor_industry", "shenzhen_data")
    if data:
        print(f"  [ok] 成功获取数据，包含 {len(data)} 个字段")
        if isinstance(data, dict) and "output_value" in data:
            print(f"  产业产值: {data['output_value']}")

def demo_dimension_analysis():
    """演示维度分析"""
    print("\n" + "=" * 70)
    print("演示 4: 灵活的维度分析框架")
    print("=" * 70)

    # 注册自定义分析维度
    print("\n📐 注册自定义分析维度:")
    register_analysis_dimension(
        code="custom_risk_analysis",
        name="风险评估分析",
        data_fields=["deficit_rate", "export_dependency", "concentration"],
        analysis_type="descriptive",
        description="综合风险评估",
    )
    print("  [ok] 注册成功: custom_risk_analysis")

    # 列出所有可用维度
    print("\n[report] 可用分析维度:")
    for dim in analysis_engine.list_dimensions()[:10]:
        print(f"  - {dim.code}: {dim.name} ({dim.analysis_type.value})")

    # 执行维度分析
    print("\n[scan] 执行维度分析:")
    test_data = {
        "gdp": 36801.87,
        "gdp_growth": 5.8,
        "cpi": 102.1,
        "pmi": 50.8,
        "fiscal_revenue": 4512.0,
        "fiscal_expenditure": 5056.8,
        "employment": 1222.56,
    }

    result = analyze_dimension("macro_overview", test_data)
    if result:
        print(f"  [ok] 分析完成: {result.dimension_code}")
        print(f"  [i] 发现洞察: {len(result.insights)} 条")
        for insight in result.insights[:3]:
            print(f"    - {insight}")

def demo_scenario_manager():
    """演示场景管理"""
    if not SCENARIO_ENABLED:
        print("\n跳过场景管理演示（依赖模块未安装）")
        return

    print("\n" + "=" * 70)
    print("演示 5: 灵活的场景配置系统")
    print("=" * 70)

    # 查看现有场景
    print("\n 现有场景:")
    for scenario in list_scenarios()[:5]:
        print(f"  - {scenario.id}: {scenario.name} ({scenario.scenario_type.value})")

    # 创建自定义场景
    print("\n➕ 创建自定义场景:")
    new_scenario = register_scenario(
        name="自定义产业分析",
        scenario_type="industry_analysis",
        description="用于分析任意产业",
        years=[2024, 2025],
        dimensions=["market_analysis", "technology_analysis"],
        thresholds={"growth_min": 5.0},
    )
    print(f"  [ok] 创建成功: {new_scenario.id}")

    # 克隆场景
    print("\n 克隆场景:")
    cloned = scenario_manager.clone_scenario(
        "shenzhen_semiconductor_enterprise", "克隆：广州半导体分析", region={"name": "广州", "code": "440100"}
    )
    if cloned:
        print(f"  [ok] 克隆成功: {cloned.id}")

    # 切换使用场景
    print("\n🔀 切换到自定义场景:")
    if use_scenario(new_scenario.id):
        current = scenario_manager.get_current_scenario()
        print(f"  [ok] 当前场景: {current.name}")
        print(f"  [i] 分析年份: {current.analysis_years}")

    # 保存场景配置
    print("\n 保存场景配置:")
    export_path = Path(__file__).parent / "exports" / "scenarios.json"
    export_path.parent.mkdir(exist_ok=True)
    scenario_manager.save_scenarios(str(export_path))
    print(f"   已保存到: {export_path}")

def demo_report_generator():
    """演示报告生成"""
    if not REPORT_ENABLED:
        print("\n跳过报告生成演示（依赖模块未安装）")
        return

    print("\n" + "=" * 70)
    print("演示 6: 灵活的报告生成系统")
    print("=" * 70)

    # 创建报告章节
    print("\n📄 创建报告章节:")
    sections = [
        create_report_section(
            title="执行摘要",
            content={"分析区域": "深圳", "分析产业": "半导体", "分析年份": 2025, "总体评分": 82.5},
            order=1,
        ),
        create_report_section(
            title="核心指标",
            content={"产业产值": "12000亿元", "GDP占比": "32.6%", "从业人员": "28.5万人", "研发强度": "12.5%"},
            visualization="kpi_cards",
            order=2,
        ),
        create_report_section(
            title="关键发现",
            content=[
                "产业链完整度达85%，核心竞争力显著",
                "研发投入强度高于全国平均水平3个百分点",
                "人才供需缺口约3万人，结构性矛盾突出",
                "出口依存度偏高，面临供应链风险",
            ],
            order=3,
        ),
        create_report_section(
            title="建议措施",
            content=[
                "加大基础研究投入，补齐上游短板",
                "建立校企联合培养机制，缓解人才缺口",
                "开拓国内市场，降低对外依存度",
            ],
            order=4,
        ),
    ]
    print(f"  [ok] 创建了 {len(sections)} 个章节")

    # 生成不同格式的报告
    print("\n[i] 生成报告:")

    for fmt in [OutputFormat.JSON, OutputFormat.MARKDOWN, OutputFormat.HTML]:
        config = ReportConfig(
            title="深圳半导体产业分析报告", subtitle="2025年度综合分析", author="National Stats Team", format=fmt
        )

        content = report_generator.generate_report(sections, config)

        export_dir = Path(__file__).parent / "exports"
        export_dir.mkdir(exist_ok=True)
        output_path = export_dir / f"demo_report.{fmt.value}"

        config_obj = ReportConfig(title="", format=fmt)
        from backend.utils.report_generator import ReportGeneratorFactory

        generator = ReportGeneratorFactory.create(config_obj)
        generator.save(content, str(output_path))

        print(f"  [ok] {fmt.value.upper()} 报告已保存: {output_path.name} ({len(content)} 字节)")

    # 快速报告
    print("\n[perf] 快速生成报告:")
    quick = report_generator.quick_report(
        title="快速测试报告", data={"测试项": "灵活扩展演示", "状态": "成功"}, format="markdown"
    )
    print(f"  [ok] 快速报告长度: {len(quick)} 字节")

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("  区域产业经济分析系统 - 灵活扩展功能演示")
    print("=" * 80)

    demos = [
        ("指标注册系统", demo_indicator_registry),
        ("自定义指标计算", demo_custom_indicators),
        ("数据源管理", demo_data_source_manager),
        ("维度分析框架", demo_dimension_analysis),
        ("场景配置系统", demo_scenario_manager),
        ("报告生成系统", demo_report_generator),
    ]

    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n[x] 演示 '{name}' 执行失败: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print(" 灵活扩展功能演示完成！")
    print("=" * 80)

    print("\n📚 系统新增的灵活扩展能力：")
    print("  1. 指标注册系统 - 支持动态注册和管理各种分析指标")
    print("  2. 自定义指标计算 - 支持自定义公式和计算函数")
    print("  3. 数据源管理 - 支持多种数据源和动态切换")
    print("  4. 维度分析框架 - 支持自定义分析维度和多维度分析")
    print("  5. 场景配置系统 - 支持多场景配置和快速切换")
    print("  6. 报告生成系统 - 支持多种输出格式和自定义模板")

    print("\n[i] 使用示例:")
    print("  # 注册自定义指标")
    print("  from backend.analysis.indicator_registry import register_indicator")
    print("  register_indicator('my_metric', '我的指标', 'macro', '%', '描述')")
    print("")
    print("  # 使用自定义公式计算")
    print("  from backend.analysis.custom_indicators import calculate_indicator")
    print("  result = calculate_indicator('my_ratio', {'a': 100, 'b': 50})")
    print("")
    print("  # 创建分析场景")
    print("  from config.scenario_manager import register_scenario")
    print("  scenario = register_scenario('新场景', 'custom', years=[2025])")

if __name__ == "__main__":
    main()
