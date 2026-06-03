#!/usr/bin/env python3
"""
完整功能测试脚本
测试所有分析功能的计算准确性和合理性
"""

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))


class EconomicModelTester:
    """经济学模型测试器"""

    def __init__(self):
        self.results = []

    def test_phillips_curve(self) -> dict[str, Any]:
        """测试菲利普斯曲线计算"""
        print("\n" + "=" * 60)
        print("测试 1: 菲利普斯曲线 (通胀率 vs 失业率)")
        print("=" * 60)

        from backend.analysis.economic_models import PhillipsCurve

        try:
            pc = PhillipsCurve()

            # 测试数据
            inflation_rates = [2.1, 2.5, 3.0, 2.8, 2.3]
            unemployment_rates = [4.5, 4.2, 3.8, 4.0, 4.3]

            result = pc.fit(inflation_rates, unemployment_rates)

            print("\n✅ 菲利普斯曲线模型拟合成功")
            print(f"   - 拟合优度 (R²): {result.get('r_squared', 'N/A'):.4f}")
            print(f"   - NAIRU (自然失业率): {result.get('nairu', 'N/A'):.2f}%")

            # 验证合理性
            passed = True
            if result.get("r_squared", 0) < 0.5:
                print("⚠️  拟合优度较低，建议检查数据")
                passed = False

            return {"name": "菲利普斯曲线", "status": "passed" if passed else "warning", "details": result}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return {"name": "菲利普斯曲线", "status": "failed", "error": str(e)}

    def test_okun_law(self) -> dict[str, Any]:
        """测试奥肯定律计算"""
        print("\n" + "=" * 60)
        print("测试 2: 奥肯定律 (GDP增长 vs 失业率)")
        print("=" * 60)

        from backend.analysis.economic_models import OkunLaw

        try:
            okun = OkunLaw()

            # 测试数据
            gdp_growth_rates = [6.5, 6.8, 7.2, 6.9, 5.8]
            unemployment_rates = [4.5, 4.2, 3.8, 4.0, 4.3]

            result = okun.fit(gdp_growth_rates, unemployment_rates)

            print("\n✅ 奥肯定律模型拟合成功")
            print(f"   - 拟合优度 (R²): {result.get('r_squared', 'N/A'):.4f}")
            print(f"   - 奥肯系数: {result.get('okun_coefficient', 'N/A'):.2f}")

            # 验证合理性
            passed = True
            okun_coeff = result.get("okun_coefficient", 0)
            if not (-3 <= okun_coeff <= -1):
                print(f"⚠️  奥肯系数异常 (期望在-2左右): {okun_coeff}")
                passed = False

            return {"name": "奥肯定律", "status": "passed" if passed else "warning", "details": result}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return {"name": "奥肯定律", "status": "failed", "error": str(e)}

    def test_cobb_douglas(self) -> dict[str, Any]:
        """测试柯布-道格拉斯生产函数"""
        print("\n" + "=" * 60)
        print("测试 3: 柯布-道格拉斯生产函数")
        print("=" * 60)

        from backend.analysis.economic_models import CobbDouglasProductionFunction

        try:
            cd = CobbDouglasProductionFunction()

            # 测试数据
            outputs = [100, 105, 110, 115, 120]
            labor = [50, 52, 54, 55, 57]
            capital = [80, 82, 85, 87, 90]

            result = cd.fit(outputs, labor, capital)

            print("\n✅ 柯布-道格拉斯生产函数拟合成功")
            print(f"   - 拟合优度 (R²): {result.get('r_squared', 'N/A'):.4f}")
            print(f"   - 劳动弹性 (α): {result.get('alpha', 'N/A'):.3f}")
            print(f"   - 资本弹性 (β): {result.get('beta', 'N/A'):.3f}")
            print(
                f"   - 规模报酬: {'递增' if result.get('returns_to_scale', 1) > 1.01 else '递减' if result.get('returns_to_scale', 1) < 0.99 else '不变'}"
            )

            # 验证合理性
            passed = True
            alpha = result.get("alpha", 0)
            beta = result.get("beta", 0)

            if not (0 < alpha < 1 and 0 < beta < 1):
                print("⚠️  弹性系数异常 (应在0-1之间)")
                passed = False

            return {"name": "柯布-道格拉斯生产函数", "status": "passed" if passed else "warning", "details": result}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return {"name": "柯布-道格拉斯生产函数", "status": "failed", "error": str(e)}

    def run_all(self) -> list[dict[str, Any]]:
        """运行所有经济学模型测试"""
        print("\n" + "=" * 60)
        print("经济学模型功能测试")
        print("=" * 60)

        self.results = [self.test_phillips_curve(), self.test_okun_law(), self.test_cobb_douglas()]

        return self.results


class AnalysisWorkflowTester:
    """分析工作流测试器"""

    def __init__(self):
        self.data_dir = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data"
        self.results = []

    def test_data_loading(self) -> dict[str, Any]:
        """测试数据加载"""
        print("\n" + "=" * 60)
        print("测试 4: 数据加载和验证")
        print("=" * 60)

        required_files = ["basic_data.json", "business_cost.json", "supply_chain.json", "finance_data.json"]

        all_passed = True
        data_sizes = {}

        for filename in required_files:
            filepath = self.data_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, encoding="utf-8") as f:
                        data = json.load(f)
                    size = len(json.dumps(data))
                    data_sizes[filename] = size
                    print(f"✅ {filename} - 加载成功 ({size} 字节)")
                except Exception as e:
                    print(f"❌ {filename} - 加载失败: {e}")
                    all_passed = False
            else:
                print(f"❌ {filename} - 文件不存在")
                all_passed = False

        return {"name": "数据加载", "status": "passed" if all_passed else "failed", "data_sizes": data_sizes}

    def test_enterprise_analysis_runner(self) -> dict[str, Any]:
        """测试企业分析运行器"""
        print("\n" + "=" * 60)
        print("测试 5: 企业端分析流程")
        print("=" * 60)

        try:
            from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner

            # 创建运行器（仅测试，不保存文件）
            runner = EnterpriseAnalysisRunner()

            # 测试各分析模块
            print("\n📊 测试土地成本分析...")
            land_result = runner.analyze_land_cost()
            print(f"   结果包含 {len(land_result)} 个字段")

            print("\n👥 测试人力成本分析...")
            labor_result = runner.analyze_labor_cost()
            print(f"   平均薪资: {labor_result['average_salary']} 元/月")
            print(f"   同比增长: {labor_result['yoy_growth']}%")

            print("\n⚡ 测试能源成本分析...")
            energy_result = runner.analyze_energy_cost()
            print(f"   工业电价: {energy_result['electricity_price']} 元/kWh")

            print("\n💳 测试融资成本分析...")
            financing_result = runner.analyze_financing_cost()

            print("\n📈 测试综合成本指数...")
            cost_index = runner.calculate_comprehensive_cost_index()
            print(f"   深圳成本指数: {cost_index['shenzhen_index']}")

            print("\n🔗 测试供应链分析...")
            supply_chain = runner.analyze_supply_chain()
            print(f"   上游覆盖度: {supply_chain['chain_coverage']['upstream']}%")
            print(f"   本地化率: {supply_chain['localization_rate']}%")

            print("\n🏛️ 测试政策红利分析...")
            policy = runner.analyze_policy_benefits()
            print(f"   税收优惠: {policy['total_tax_incentive']} 亿元")

            # 验证结果合理性
            passed = True
            checks = []

            # 检查土地成本
            if not (500 < land_result["city_average"] < 1500):
                checks.append("⚠️  土地成本可能异常")
                passed = False

            # 检查人力成本
            if not (10000 < labor_result["average_salary"] < 30000):
                checks.append("⚠️  人力成本可能异常")
                passed = False

            # 检查能源成本
            if not (0.5 < energy_result["electricity_price"] < 1.5):
                checks.append("⚠️  能源成本可能异常")
                passed = False

            if checks:
                print("\n" + "\n".join(checks))

            return {"name": "企业端分析流程", "status": "passed" if passed else "warning", "checks": checks}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return {"name": "企业端分析流程", "status": "failed", "error": str(e)}

    def test_government_analysis_runner(self) -> dict[str, Any]:
        """测试政府分析运行器"""
        print("\n" + "=" * 60)
        print("测试 6: 政府端分析流程")
        print("=" * 60)

        try:
            from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner

            runner = GovernmentAnalysisRunner()

            # 简单测试初始化和数据加载
            print("\n✅ 政府分析运行器初始化成功")
            print(f"   已加载 {len(runner.data)} 个数据文件")

            # 测试财政杠杆分析
            print("\n💰 测试财政杠杆分析...")
            fiscal_result = runner.analyze_fiscal_leverage()
            print(f"   财政投入强度: {fiscal_result['investment_intensity']}")

            # 测试产业带动分析
            print("\n📈 测试产业带动分析...")
            multiplier_result = runner.analyze_industry_multiplier()
            print(f"   带动就业: {multiplier_result['employment_effect']['total']} 万人")

            return {"name": "政府端分析流程", "status": "passed"}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return {"name": "政府端分析流程", "status": "failed", "error": str(e)}

    def test_config_system(self) -> dict[str, Any]:
        """测试配置系统"""
        print("\n" + "=" * 60)
        print("测试 7: 配置系统")
        print("=" * 60)

        try:
            from config import config_loader

            config = config_loader.load_config()

            print("\n✅ 配置系统加载成功")
            print(f"   区域: {config.get('region', {}).get('name', 'N/A')}")
            print(f"   产业: {config.get('industry', {}).get('name', 'N/A')}")
            print(f"   年份: {config.get('analysis', {}).get('year', 'N/A')}")

            return {"name": "配置系统", "status": "passed", "config": {k: v for k, v in list(config.items())[:5]}}
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return {"name": "配置系统", "status": "failed", "error": str(e)}

    def run_all(self) -> list[dict[str, Any]]:
        """运行所有工作流测试"""
        self.results = [
            self.test_data_loading(),
            self.test_enterprise_analysis_runner(),
            self.test_government_analysis_runner(),
            self.test_config_system(),
        ]
        return self.results


class ResultsValidator:
    """结果验证器"""

    def __init__(self):
        pass

    def validate_business_costs(self) -> dict[str, Any]:
        """验证营商成本合理性"""
        print("\n" + "=" * 60)
        print("验证 1: 营商成本合理性检查")
        print("=" * 60)

        data_path = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data" / "business_cost.json"

        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        checks = []
        passed = True

        # 检查土地成本
        land_price = data["land_cost"]["city_average"]
        if 600 <= land_price <= 1200:
            print(f"✅ 土地成本合理: {land_price} 元/㎡·年")
        else:
            print(f"⚠️  土地成本可能异常: {land_price}")
            passed = False
            checks.append("土地成本异常")

        # 检查人力成本
        labor_data = data["labor_cost"]["data"]["semiconductor_industry"]
        avg_salary = labor_data["average_salary"]["value"]
        if 15000 <= avg_salary <= 25000:
            print(f"✅ 人力成本合理: {avg_salary} 元/月")
        else:
            print(f"⚠️  人力成本可能异常: {avg_salary}")
            passed = False
            checks.append("人力成本异常")

        # 检查能源成本
        elec_price = data["energy_cost"]["data"]["industrial_electricity"]["price"]
        if 0.6 <= elec_price <= 1.0:
            print(f"✅ 能源成本合理: {elec_price} 元/kWh")
        else:
            print(f"⚠️  能源成本可能异常: {elec_price}")
            passed = False
            checks.append("能源成本异常")

        return {"name": "营商成本合理性", "status": "passed" if passed else "warning", "checks": checks}

    def validate_industry_metrics(self) -> dict[str, Any]:
        """验证产业指标合理性"""
        print("\n" + "=" * 60)
        print("验证 2: 产业指标合理性检查")
        print("=" * 60)

        data_path = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data" / "basic_data.json"

        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        checks = []
        passed = True

        # 检查产业产值
        output = data["semiconductor_industry"]["output_value"]["value"]
        if 5000 <= output <= 15000:
            print(f"✅ 产业产值合理: {output} 亿元")
        else:
            print(f"⚠️  产业产值可能异常: {output}")
            passed = False
            checks.append("产业产值异常")

        # 检查研发强度
        rd_intensity = data["semiconductor_industry"]["rd_intensity"]["value"]
        if 5 <= rd_intensity <= 20:
            print(f"✅ 研发强度合理: {rd_intensity}%")
        else:
            print(f"⚠️  研发强度可能异常: {rd_intensity}")
            passed = False
            checks.append("研发强度异常")

        # 检查市场份额
        domestic_share = data["semiconductor_industry"]["market_share"]["domestic"]
        if 20 <= domestic_share <= 40:
            print(f"✅ 国内市场份额合理: {domestic_share}%")
        else:
            print(f"⚠️  国内市场份额可能异常: {domestic_share}")
            passed = False
            checks.append("市场份额异常")

        return {"name": "产业指标合理性", "status": "passed" if passed else "warning", "checks": checks}

    def validate_fiscal_data(self) -> dict[str, Any]:
        """验证财政数据合理性"""
        print("\n" + "=" * 60)
        print("验证 3: 财政数据合理性检查")
        print("=" * 60)

        data_path = Path(__file__).parent / "examples" / "shenzhen_semiconductor_2025" / "data" / "finance_data.json"

        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        checks = []
        passed = True

        # 检查财政支持规模
        fiscal_support = data["semiconductor_fiscal_support"]["total_investment"]
        if 500 <= fiscal_support <= 2000:
            print(f"✅ 财政支持规模合理: {fiscal_support} 亿元")
        else:
            print(f"⚠️  财政支持规模可能异常: {fiscal_support}")
            passed = False
            checks.append("财政支持规模异常")

        return {"name": "财政数据合理性", "status": "passed" if passed else "warning", "checks": checks}

    def run_all(self) -> list[dict[str, Any]]:
        """运行所有验证"""
        return [self.validate_business_costs(), self.validate_industry_metrics(), self.validate_fiscal_data()]


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.all_results = {}

    def run(self):
        """运行完整测试套件"""
        print("\n" + "=" * 80)
        print("区域产业经济分析系统 - 完整功能测试")
        print("=" * 80)

        # 1. 经济学模型测试
        print("\n" + "=" * 80)
        print("阶段 1: 经济学模型测试")
        print("=" * 80)
        model_tester = EconomicModelTester()
        model_results = model_tester.run_all()
        self.all_results["economic_models"] = model_results

        # 2. 工作流测试
        print("\n" + "=" * 80)
        print("阶段 2: 分析工作流测试")
        print("=" * 80)
        workflow_tester = AnalysisWorkflowTester()
        workflow_results = workflow_tester.run_all()
        self.all_results["workflows"] = workflow_results

        # 3. 结果验证
        print("\n" + "=" * 80)
        print("阶段 3: 结果合理性验证")
        print("=" * 80)
        validator = ResultsValidator()
        validation_results = validator.run_all()
        self.all_results["validation"] = validation_results

        # 4. 打印总结
        self.print_summary()

        return self.all_results

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)

        all_tests = []
        for category, tests in self.all_results.items():
            all_tests.extend(tests)

        passed = sum(1 for t in all_tests if t["status"] == "passed")
        warnings = sum(1 for t in all_tests if t["status"] == "warning")
        failed = sum(1 for t in all_tests if t["status"] == "failed")
        total = len(all_tests)

        print(f"\n📊 总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"⚠️  警告: {warnings}")
        print(f"❌ 失败: {failed}")

        print("\n📝 详细结果:")
        for category, tests in self.all_results.items():
            print(f"\n  {category.replace('_', ' ').title()}:")
            for test in tests:
                status_icon = {"passed": "✅", "warning": "⚠️", "failed": "❌"}.get(test["status"], "?")
                print(f"    {status_icon} {test['name']}")

        print(f"\n{'=' * 80}")
        if failed == 0:
            if warnings == 0:
                print("🎉 所有测试通过！系统功能完整且计算合理。")
            else:
                print("✅ 主要功能正常，部分警告请留意。")
        else:
            print("⚠️  部分测试失败，请检查相关功能。")
        print("=" * 80)


def main():
    """主函数"""
    runner = TestRunner()
    runner.run()


if __name__ == "__main__":
    main()
