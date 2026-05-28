#!/usr/bin/env python3
"""
简化版功能测试脚本 - 确保所有核心功能正常
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_economic_models():
    """测试经济学模型"""
    print("\n" + "=" * 60)
    print("测试 1: 经济学模型计算")
    print("=" * 60)
    
    try:
        from backend.analysis.economic_models import economic_models
        
        # 测试菲利普斯曲线
        print("\n🔵 菲利普斯曲线测试...")
        phillips_result = economic_models.phillips_curve(unemployment=4.2, natural_unemployment=5.0)
        print(f"   ✅ 模型运行成功")
        print(f"   - 预期通胀率: {phillips_result['output']['inflation']}%")
        print(f"   - 解释: {phillips_result['interpretation']}")
        
        # 测试奥肯定律
        print("\n🟢 奥肯定律测试...")
        okun_result = economic_models.okun_law(gdp_growth=5.8, potential_growth=6.0)
        print(f"   ✅ 模型运行成功")
        print(f"   - 产出缺口: {okun_result['output']['output_gap']}%")
        print(f"   - 失业率变化: {okun_result['output']['unemployment_change']}%")
        print(f"   - 解释: {okun_result['interpretation']}")
        
        # 测试柯布-道格拉斯生产函数
        print("\n🟡 柯布-道格拉斯生产函数测试...")
        cd_result = economic_models.cobb_douglas(capital=100, labor=50, alpha=0.3)
        print(f"   ✅ 模型运行成功")
        print(f"   - 产出: {cd_result['output']['output']}")
        print(f"   - 资本边际产出: {cd_result['output']['marginal_product_capital']}")
        print(f"   - 劳动边际产出: {cd_result['output']['marginal_product_labor']}")
        
        return True
    except Exception as e:
        print(f"❌ 经济学模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_integrity():
    """测试数据完整性"""
    print("\n" + "=" * 60)
    print("测试 2: 数据完整性验证")
    print("=" * 60)
    
    data_dir = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data"
    required_files = [
        "basic_data.json",
        "business_cost.json",
        "supply_chain.json",
        "finance_data.json"
    ]
    
    all_valid = True
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                size = len(json.dumps(data))
                print(f"✅ {filename} - 加载成功 ({size} 字节)")
            except Exception as e:
                print(f"❌ {filename} - 加载失败: {e}")
                all_valid = False
        else:
            print(f"❌ {filename} - 文件不存在")
            all_valid = False
    
    return all_valid


def test_basic_data_calculations():
    """测试基本数据计算"""
    print("\n" + "=" * 60)
    print("测试 3: 基本数据计算")
    print("=" * 60)
    
    try:
        data_path = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data" / "basic_data.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            basic_data = json.load(f)
        
        gdp = basic_data['macro_economy']['gdp']['value']
        industry_output = basic_data['semiconductor_industry']['output_value']['value']
        
        # 计算产业占比
        industry_ratio = (industry_output / gdp) * 100
        print(f"✅ 数据加载成功")
        print(f"   - GDP: {gdp} 亿元")
        print(f"   - 半导体产值: {industry_output} 亿元")
        print(f"   - 产业占比: {industry_ratio:.2f}%")
        
        # 验证合理性
        passed = True
        if not (0.5 < industry_ratio < 50):
            print(f"⚠️  产业占比可能异常: {industry_ratio:.2f}%")
            passed = False
        
        return passed
    except Exception as e:
        print(f"❌ 基本数据计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enterprise_analysis_module():
    """测试企业分析模块"""
    print("\n" + "=" * 60)
    print("测试 4: 企业分析模块")
    print("=" * 60)
    
    try:
        from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner
        
        runner = EnterpriseAnalysisRunner()
        print(f"✅ 分析器初始化成功")
        print(f"   - 已加载 {len(runner.data)} 个数据文件")
        
        # 测试土地成本分析
        land_result = runner.analyze_land_cost()
        print(f"\n📊 土地成本分析:")
        print(f"   - 平均价格: {land_result['city_average']} 元/㎡·年")
        print(f"   - 同比增长: {land_result['city_average_yoy']}%")
        
        # 测试人力成本分析
        labor_result = runner.analyze_labor_cost()
        print(f"\n👥 人力成本分析:")
        print(f"   - 平均薪资: {labor_result['average_salary']} 元/月")
        print(f"   - 薪资同比: {labor_result['yoy_growth']}%")
        
        # 测试供应链分析
        supply_result = runner.analyze_supply_chain()
        print(f"\n🔗 供应链分析:")
        print(f"   - 上游覆盖度: {supply_result['chain_coverage']['upstream']}%")
        print(f"   - 中游覆盖度: {supply_result['chain_coverage']['midstream']}%")
        print(f"   - 下游覆盖度: {supply_result['chain_coverage']['downstream']}%")
        print(f"   - 本地化率: {supply_result['localization_rate']}%")
        
        return True
    except Exception as e:
        print(f"❌ 企业分析模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_government_analysis_module():
    """测试政府分析模块"""
    print("\n" + "=" * 60)
    print("测试 5: 政府分析模块")
    print("=" * 60)
    
    try:
        from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner
        
        runner = GovernmentAnalysisRunner()
        print(f"✅ 政府分析器初始化成功")
        print(f"   - 已加载 {len(runner.data)} 个数据文件")
        
        # 测试财政杠杆分析
        fiscal_result = runner.analyze_fiscal_leverage()
        print(f"\n💰 财政杠杆分析:")
        print(f"   - 财政投入强度: {fiscal_result.get('investment_intensity', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 政府分析模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_system():
    """测试配置系统"""
    print("\n" + "=" * 60)
    print("测试 6: 配置系统")
    print("=" * 60)
    
    try:
        from config import config_loader
        
        full_config = config_loader.get_full_config()
        
        print(f"✅ 配置系统加载成功")
        print(f"   - 区域: {full_config.get('current_region', {}).get('name', 'N/A')}")
        print(f"   - 产业: {full_config.get('current_industry', {}).get('name', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_entry():
    """测试主入口文件"""
    print("\n" + "=" * 60)
    print("测试 7: 主入口文件")
    print("=" * 60)
    
    try:
        from main import EnvironmentChecker, ExampleMode
        
        # 测试环境检查器
        checker = EnvironmentChecker()
        print(f"✅ EnvironmentChecker 初始化成功")
        print(f"   - 检查Python版本: {hasattr(checker, 'check_python_version')}")
        print(f"   - 检查依赖: {hasattr(checker, 'check_dependencies')}")
        
        return True
    except Exception as e:
        print(f"❌ 主入口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_results():
    """验证计算结果的合理性"""
    print("\n" + "=" * 60)
    print("验证: 计算结果合理性检查")
    print("=" * 60)
    
    all_valid = True
    
    # 1. 验证基本商业成本
    try:
        data_path = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data" / "business_cost.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            cost_data = json.load(f)
        
        # 检查土地成本
        land_price = cost_data['land_cost']['city_average']
        if 600 <= land_price <= 1200:
            print(f"✅ 土地成本合理: {land_price} 元/㎡·年")
        else:
            print(f"⚠️  土地成本可能异常: {land_price}")
            all_valid = False
        
        # 检查人力成本
        labor_data = cost_data['labor_cost']['data']['semiconductor_industry']
        avg_salary = labor_data['average_salary']['value']
        if 15000 <= avg_salary <= 25000:
            print(f"✅ 人力成本合理: {avg_salary} 元/月")
        else:
            print(f"⚠️  人力成本可能异常: {avg_salary}")
            all_valid = False
        
        # 检查能源成本
        elec_price = cost_data['energy_cost']['data']['industrial_electricity']['price']
        if 0.6 <= elec_price <= 1.0:
            print(f"✅ 能源成本合理: {elec_price} 元/kWh")
        else:
            print(f"⚠️  能源成本可能异常: {elec_price}")
            all_valid = False
    except Exception as e:
        print(f"⚠️  商业成本验证失败: {e}")
        all_valid = False
    
    # 2. 验证产业指标
    try:
        data_path = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data" / "basic_data.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            industry_data = json.load(f)
        
        output = industry_data['semiconductor_industry']['output_value']['value']
        if 5000 <= output <= 15000:
            print(f"✅ 产业产值合理: {output} 亿元")
        else:
            print(f"⚠️  产业产值可能异常: {output}")
            all_valid = False
        
        rd_intensity = industry_data['semiconductor_industry']['rd_intensity']['value']
        if 5 <= rd_intensity <= 20:
            print(f"✅ 研发强度合理: {rd_intensity}%")
        else:
            print(f"⚠️  研发强度可能异常: {rd_intensity}")
            all_valid = False
    except Exception as e:
        print(f"⚠️  产业指标验证失败: {e}")
        all_valid = False
    
    return all_valid


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("区域产业经济分析系统 - 功能完整性测试")
    print("=" * 80)
    
    tests = [
        ("经济学模型", test_economic_models),
        ("数据完整性", test_data_integrity),
        ("基本数据计算", test_basic_data_calculations),
        ("企业分析模块", test_enterprise_analysis_module),
        ("政府分析模块", test_government_analysis_module),
        ("配置系统", test_config_system),
        ("主入口", test_main_entry)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 验证结果
    print("\n" + "=" * 80)
    print("计算结果合理性验证")
    print("=" * 80)
    validation_passed = validate_results()
    
    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 功能测试: {passed}/{total} 通过")
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}: {name}")
    
    validation_status = "✅ 通过" if validation_passed else "⚠️  警告"
    print(f"\n🔍 结果合理性验证: {validation_status}")
    
    print("\n" + "=" * 80)
    if passed == total and validation_passed:
        print("🎉 所有测试通过！系统功能完整且计算合理。")
        print("   可以继续进行可视化和其他开发工作。")
    elif passed == total:
        print("✅ 主要功能正常，部分计算结果可能需要检查。")
    else:
        print(f"⚠️  {total - passed} 个测试失败，请检查相关功能。")
    print("=" * 80)
    
    return passed == total and validation_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
