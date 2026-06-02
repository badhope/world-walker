#!/usr/bin/env python3
"""
配置系统测试脚本
验证配置加载、地区切换、产业切换等功能
"""
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_config_loader():
    """测试配置加载器"""
    print("=" * 60)
    print("测试 1: 配置加载器")
    print("=" * 60)
    
    from config import config_loader
    
    # 获取完整配置
    full_config = config_loader.get_full_config()
    
    print(f"\n项目名称: {full_config['settings']['project_name']}")
    print(f"可用地区: {', '.join(full_config['available_regions'])}")
    print(f"可用产业: {', '.join(full_config['available_industries'])}")
    
    if full_config['current_region']:
        print(f"\n当前地区: {full_config['current_region']['name']}")
        print(f"地区代码: {full_config['current_region']['code']}")
    
    if full_config['current_industry']:
        print(f"\n当前产业: {full_config['current_industry']['name']}")
        print(f"产业链环节数: {len(full_config['current_industry']['chain_links'])}")
    
    print("\n✅ 配置加载器测试通过！")
    return True

def test_region_switch():
    """测试地区切换"""
    print("\n" + "=" * 60)
    print("测试 2: 地区切换")
    print("=" * 60)
    
    from config import config_loader
    
    # 获取所有可用地区
    regions = config_loader.get_available_regions()
    print(f"\n可用地区: {regions}")
    
    if len(regions) > 0:
        # 尝试切换到第一个地区
        region_name = regions[0]
        success = config_loader.set_current_region(region_name)
        
        if success:
            region_config = config_loader.get_region_config()
            print(f"\n✅ 成功切换到地区: {region_config.name}")
            print(f"   省份: {region_config.province}")
            print(f"   统计口径: {region_config.statistical_caliber}")
        else:
            print(f"❌ 切换地区失败: {region_name}")
            return False
    
    print("\n✅ 地区切换测试通过！")
    return True

def test_industry_switch():
    """测试产业切换"""
    print("\n" + "=" * 60)
    print("测试 3: 产业切换")
    print("=" * 60)
    
    from config import config_loader
    
    # 获取所有可用产业
    industries = config_loader.get_available_industries()
    print(f"\n可用产业: {industries}")
    
    if len(industries) > 0:
        # 尝试切换到第一个产业
        industry_name = industries[0]
        success = config_loader.set_current_industry(industry_name)
        
        if success:
            industry_config = config_loader.get_industry_config()
            print(f"\n✅ 成功切换到产业: {industry_config.name}")
            print(f"   产业分类: {industry_config.category}")
            print(f"   产业链环节: {len(industry_config.chain_links)}个")
        else:
            print(f"❌ 切换产业失败: {industry_name}")
            return False
    
    print("\n✅ 产业切换测试通过！")
    return True

def test_analysis_config():
    """测试分析配置"""
    print("\n" + "=" * 60)
    print("测试 4: 分析配置")
    print("=" * 60)
    
    from config import AnalysisConfig
    
    print(f"\n默认年份: {AnalysisConfig.DEFAULT_YEAR}")
    print(f"默认地区: {AnalysisConfig.DEFAULT_REGION}")
    print(f"默认产业: {AnalysisConfig.DEFAULT_INDUSTRY}")
    
    print(f"\n默认评分: {AnalysisConfig.DEFAULT_SCORES}")
    print(f"\n分析指标: {AnalysisConfig.DATA_COLLECTION['default_indicators']}")
    
    print("\n✅ 分析配置测试通过！")
    return True

def test_settings_config():
    """测试基础配置"""
    print("\n" + "=" * 60)
    print("测试 5: 基础配置")
    print("=" * 60)
    
    from config import settings
    
    print(f"\n项目名称: {settings.PROJECT_NAME}")
    print(f"API Host: {settings.API_HOST}")
    print(f"API Port: {settings.API_PORT}")
    print(f"Debug Mode: {settings.DEBUG}")
    
    print(f"\n数据目录: {settings.DATA_DIR}")
    print(f"导出目录: {settings.EXPORT_DIR}")
    
    print("\n✅ 基础配置测试通过！")
    return True

def test_analyzer_with_config():
    """测试分析器使用配置"""
    print("\n" + "=" * 60)
    print("测试 6: 分析器使用配置")
    print("=" * 60)
    
    from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer
    from backend.analysis.government_analyzer import GovernmentAnalyzer
    
    # 测试数据
    test_data = {
        "land_price": 800.0,
        "salary_level": 15000.0,
        "gdp": 35000.0,
        "revenue": 4500.0,
        "expenditure": 5000.0
    }
    
    print("\n测试企业分析器...")
    ea = EnterpriseAnalyzer()
    enterprise_report = ea.generate_comprehensive_report(test_data)
    print(f"   企业分析报告 - 综合得分: {enterprise_report['overall_score']:.1f}")
    
    print("\n测试政府分析器...")
    ga = GovernmentAnalyzer()
    government_report = ga.generate_comprehensive_report(test_data)
    print(f"   政府分析报告 - 综合得分: {government_report['overall_score']:.1f}")
    print(f"   分析地区: {government_report['region']}")
    print(f"   分析产业: {government_report['industry']}")
    
    print("\n✅ 分析器测试通过！")
    return True

def test_data_collection():
    """测试数据采集模块"""
    print("\n" + "=" * 60)
    print("测试 7: 数据采集模块")
    print("=" * 60)
    
    from backend.data_collection.nbs_collector import nbs_collector
    
    print("\n测试获取财政收入数据...")
    fiscal_data = nbs_collector.get_fiscal_revenue()
    if fiscal_data:
        print(f"   ✅ 获取到 {len(fiscal_data)} 条财政收入数据")
        for item in fiscal_data[:2]:  # 只显示前2条
            print(f"   - {item['year']}: {item['value']} {item['unit']}")
    
    print("\n测试批量获取数据...")
    all_data = nbs_collector.fetch_all(indicators=['gdp', 'fiscal_revenue'])
    print(f"   ✅ 批量获取了 {len(all_data)} 类数据")
    for key, data in all_data.items():
        print(f"   - {key}: {len(data)} 条")
    
    print("\n✅ 数据采集模块测试通过！")
    return True

def test_visualizer():
    """测试可视化模块"""
    print("\n" + "=" * 60)
    print("测试 8: 可视化模块")
    print("=" * 60)
    
    from backend.utils.visualizer import Visualizer
    
    print("\n初始化可视化器...")
    viz = Visualizer()
    print(f"   ✅ 主题: {viz.theme}")
    print(f"   ✅ 配色方案: {len(viz.color_palette)} 种颜色")
    
    print("\n✅ 可视化模块测试通过！")
    return True

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("区域产业经济分析平台 - 配置系统测试")
    print("=" * 60)
    
    tests = [
        test_config_loader,
        test_settings_config,
        test_analysis_config,
        test_region_switch,
        test_industry_switch,
        test_analyzer_with_config,
        test_data_collection,
        test_visualizer
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！配置系统工作正常！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())

