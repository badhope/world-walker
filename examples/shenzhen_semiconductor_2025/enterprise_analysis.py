"""
深圳半导体产业企业端分析脚本
面向企业视角的营商环境分析

主要功能：
1. 营商成本分析（土地、人力、能源、融资）
2. 供应链配套效率分析
3. 政策红利兑现率分析
4. 可视化展示

使用方法：
    python enterprise_analysis.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer


class EnterpriseAnalysisRunner:
    """企业端分析运行器"""

    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True)

        self.data = {}
        self.analysis_results = {}

        self.analyzer = EnterpriseAnalyzer()
        self.load_data()

    def load_data(self):
        """加载数据文件"""
        print("=" * 60)
        print("步骤 1: 加载数据")
        print("=" * 60)

        data_files = ["basic_data.json", "business_cost.json", "supply_chain.json", "finance_data.json"]

        for filename in data_files:
            filepath = self.data_dir / filename
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    key = filename.replace(".json", "")
                    self.data[key] = json.load(f)
                    print(f"✅ 加载 {filename}")
            else:
                print(f"❌ 文件不存在: {filename}")

        print(f"\n已加载 {len(self.data)} 个数据文件")

    def analyze_land_cost(self) -> dict[str, Any]:
        """分析土地成本"""
        print("\n" + "=" * 60)
        print("步骤 2.1: 土地成本分析")
        print("=" * 60)

        land_data = self.data["business_cost"]["land_cost"]
        results = {
            "city_average": land_data["city_average"],
            "city_average_unit": land_data["unit"],
            "city_average_yoy": land_data["city_average_yoy"],
            "area_comparison": {},
            "city_ranking": {},
            "recommendations": [],
        }

        print(f"\n📊 深圳工业用地均价: {land_data['city_average']} 元/平方米·年")
        print(f"📈 同比增长率: {land_data['city_average_yoy']}%")

        for area_data in land_data["data"]:
            results["area_comparison"][area_data["area"]] = {
                "price": area_data["industrial_price"],
                "change_yoy": area_data["change_yoy"],
            }
            print(
                f"  - {area_data['area']}: {area_data['industrial_price']} 元/㎡·年 (同比+{area_data['change_yoy']}%)"
            )

        print("\n🏙️ 与其他一线城市对比:")
        results["city_ranking"] = land_data["comparison_cities"]
        results["city_ranking"]["深圳"] = land_data["city_average"]

        sorted_cities = sorted(results["city_ranking"].items(), key=lambda x: x[1])
        for rank, (city, price) in enumerate(sorted_cities, 1):
            marker = "⭐" if city == "深圳" else "  "
            print(f"  {marker} {rank}. {city}: {price} 元/㎡·年")

        if land_data["city_average"] > 1000:
            results["recommendations"].append(
                {"type": "土地成本", "suggestion": "建议选址龙岗、坪山等区域，可降低土地成本30-40%"}
            )

        return results

    def analyze_labor_cost(self) -> dict[str, Any]:
        """分析人力成本"""
        print("\n" + "=" * 60)
        print("步骤 2.2: 人力成本分析")
        print("=" * 60)

        labor_data = self.data["business_cost"]["labor_cost"]
        semiconductor_salary = labor_data["data"]["semiconductor_industry"]
        social_insurance = labor_data["data"]["social_insurance"]
        turnover_rate = labor_data["data"]["turnover_rate"]

        results = {
            "average_salary": semiconductor_salary["average_salary"]["value"],
            "median_salary": semiconductor_salary["median_salary"]["value"],
            "salary_unit": "元/月",
            "yoy_growth": semiconductor_salary["average_salary"]["yoy_growth"],
            "position_salary": semiconductor_salary["position_salary"],
            "social_insurance_rate": social_insurance["rate"],
            "turnover_rate": turnover_rate["industry_avg"],
            "recommendations": [],
        }

        print(f"\n💰 半导体行业平均月薪: {semiconductor_salary['average_salary']['value']} 元/月")
        print(f"📈 同比增长: {semiconductor_salary['average_salary']['yoy_growth']}%")
        print(f"📊 中位数月薪: {semiconductor_salary['median_salary']['value']} 元/月")

        print("\n👔 各层级薪资水平:")
        for position, salary in semiconductor_salary["position_salary"].items():
            print(f"  - {position}: {salary} 元/月")

        print(f"\n🏛️ 五险一金比例: {social_insurance['rate']}%")
        print(f"🔄 行业离职率: {turnover_rate['industry_avg']}%")

        if semiconductor_salary["average_salary"]["value"] > 15000:
            results["recommendations"].append(
                {"type": "人力成本", "suggestion": "建议通过校企合作、培养自有团队降低招聘成本"}
            )

        return results

    def analyze_energy_cost(self) -> dict[str, Any]:
        """分析能源成本"""
        print("\n" + "=" * 60)
        print("步骤 2.3: 能源成本分析")
        print("=" * 60)

        energy_data = self.data["business_cost"]["energy_cost"]

        results = {
            "electricity_price": energy_data["data"]["industrial_electricity"]["price"],
            "electricity_unit": "元/千瓦时",
            "water_price": energy_data["data"]["industrial_water"]["price"],
            "water_unit": "元/立方米",
            "comparison": energy_data["data"]["industrial_electricity"]["comparison"],
            "fab_consumption": energy_data["data"]["semiconductor_fab_consumption"],
            "recommendations": [],
        }

        print(f"\n⚡ 工业用电价格: {energy_data['data']['industrial_electricity']['price']} 元/kWh")
        print(f"📊 对比全国平均: {energy_data['data']['industrial_electricity']['comparison']['national_avg']} 元/kWh")

        print("\n🏭 与其他城市工业用电对比:")
        for city, price in energy_data["data"]["industrial_electricity"]["comparison"].items():
            marker = "⭐" if city == "national_avg" else "  "
            print(f"  {marker} {city}: {price} 元/kWh")

        print(f"\n💧 工业用水价格: {energy_data['data']['industrial_water']['price']} 元/立方米")

        print("\n🏗️ 晶圆厂能耗指标:")
        fab_data = energy_data["data"]["semiconductor_fab_consumption"]
        print(f"  - 每片晶圆耗水量: {fab_data['water_per_wafer']} 立方米")
        print(f"  - 每片晶圆耗电量: {fab_data['electricity_per_wafer']} kWh")
        print(f"  - 万片产能年成本: {fab_data['annual_cost_per_10000_wafer']} 万元")

        return results

    def analyze_financing_cost(self) -> dict[str, Any]:
        """分析融资成本"""
        print("\n" + "=" * 60)
        print("步骤 2.4: 融资成本分析")
        print("=" * 60)

        financing_data = self.data["business_cost"]["financing_cost"]

        results = {
            "practical_rates": financing_data["data"]["loan_rates"]["practical_rates"],
            "subsidized_loan_rate": financing_data["data"]["government_subsidized_loan"]["rate"],
            "bond_rates": financing_data["data"]["bond_financing"],
            "equity_valuation": financing_data["data"]["equity_financing"],
            "recommendations": [],
        }

        print("\n💳 实际贷款利率:")
        for enterprise_type, rate in financing_data["data"]["loan_rates"]["practical_rates"].items():
            print(f"  - {enterprise_type}: {rate}%")

        print(f"\n🏛️ 政府贴息贷款: {financing_data['data']['government_subsidized_loan']['rate']}%")
        print(f"   额度上限: {financing_data['data']['government_subsidized_loan']['limit']} 万元/企业")

        print("\n📈 股权融资估值水平:")
        for stage, valuation in financing_data["data"]["equity_financing"].items():
            print(f"  - {stage}: {valuation}")

        if financing_data["data"]["government_subsidized_loan"]["rate"] < 2:
            results["recommendations"].append(
                {"type": "融资成本", "suggestion": "建议积极申请政府贴息贷款，可节省融资成本50%以上"}
            )

        return results

    def calculate_comprehensive_cost_index(self) -> dict[str, Any]:
        """计算综合成本指数"""
        print("\n" + "=" * 60)
        print("步骤 2.5: 综合营商成本指数")
        print("=" * 60)

        cost_index_data = self.data["business_cost"]["comprehensive_cost_index"]

        results = {
            "shenzhen_index": cost_index_data["indices"]["shenzhen"],
            "all_cities": cost_index_data["indices"],
            "weights": cost_index_data["weights"],
            "ranking": cost_index_data["ranking"],
            "interpretation": cost_index_data["description"],
        }

        print(f"\n📊 深圳综合营商成本指数: {cost_index_data['indices']['shenzhen']} (以深圳为100)")
        print(f"🏆 全国排名: 第{cost_index_data['ranking']}位")
        print(f"📝 {cost_index_data['description']}")

        print("\n📈 各城市对比:")
        sorted_cities = sorted(cost_index_data["indices"].items(), key=lambda x: x[1])
        for rank, (city, index) in enumerate(sorted_cities, 1):
            marker = "⭐" if city == "shenzhen" else "  "
            print(f"  {marker} {rank}. {city}: {index}")

        return results

    def analyze_supply_chain(self) -> dict[str, Any]:
        """分析供应链配套"""
        print("\n" + "=" * 60)
        print("步骤 3: 供应链配套效率分析")
        print("=" * 60)

        supply_chain = self.data["supply_chain"]
        basic_data = self.data["basic_data"]

        results = {
            "chain_coverage": {
                "upstream": supply_chain["upstream_segment"]["coverage_rate"],
                "midstream": supply_chain["midstream_segment"]["coverage_rate"],
                "downstream": supply_chain["downstream_segment"]["coverage_rate"],
            },
            "localization_rate": supply_chain["localization_metrics"]["overall_localization_rate"],
            "location_quotient": supply_chain["agglomeration_metrics"]["location_quotient"]["value"],
            "delivery_performance": supply_chain["supply_chain_efficiency"]["delivery_performance"],
            "key_bottlenecks": supply_chain["localization_metrics"]["key_bottlenecks"],
            "recommendations": [],
        }

        print("\n🔗 产业链覆盖度:")
        print(f"  - 上游（设计/材料/设备）: {results['chain_coverage']['upstream']}%")
        print(f"  - 中游（制造/封测）: {results['chain_coverage']['midstream']}%")
        print(f"  - 下游（应用/终端）: {results['chain_coverage']['downstream']}%")

        print(f"\n🎯 整体国产化率: {results['localization_rate']}%")

        print(f"\n📊 区位熵: {results['location_quotient']}")
        print(f"   解读: 深圳半导体产业集聚度是全国平均水平的{results['location_quotient']}倍")

        print("\n⏱️ 供应链效率:")
        delivery = supply_chain["supply_chain_efficiency"]["delivery_performance"]
        print(f"  - 平均交货周期: {delivery['average_lead_time']}天")
        print(f"  - 准时交货率: {delivery['on_time_delivery_rate']}%")

        print("\n⚠️ 关键瓶颈环节:")
        for bottleneck in supply_chain["localization_metrics"]["key_bottlenecks"][:3]:
            print(f"  - {bottleneck['segment']}: 进口依赖{bottleneck['dependency']}%")

        return results

    def analyze_policy_benefits(self) -> dict[str, Any]:
        """分析政策红利"""
        print("\n" + "=" * 60)
        print("步骤 4: 政策红利兑现率分析")
        print("=" * 60)

        finance_data = self.data["finance_data"]
        policy = finance_data["fiscal_policy_details"]

        results = {
            "total_tax_incentive": policy["tax_incentives"]["total_amount"],
            "total_rd_subsidy": policy["subsidy_programs"]["rd_subsidy"]["total"],
            "total_loan_support": policy["loan_support"]["total"],
            "total_support": finance_data["semiconductor_fiscal_support"]["total_investment"],
            "policy_coverage_rate": policy["tax_incentives"]["policy_coverage_rate"],
            "satisfaction_rate": finance_data["policy_effectiveness"]["enterprise_satisfaction"],
            "recommendations": [],
        }

        print(f"\n💰 税收优惠总额: {policy['tax_incentives']['total_amount']} 亿元")
        print(f"🔬 研发补贴总额: {policy['subsidy_programs']['rd_subsidy']['total']} 亿元")
        print(f"💳 贷款支持总额: {policy['loan_support']['total']} 亿元")
        print(f"📊 产业财政支持总额: {finance_data['semiconductor_fiscal_support']['total_investment']} 亿元")

        print("\n📋 税收优惠明细:")
        for item in policy["tax_incentives"]["items"][:3]:
            print(f"  - {item['policy']}: {item['amount']}亿元 (惠及{item['beneficiaries']}家企业)")

        print(f"\n🏆 政策覆盖率: {policy['tax_incentives']['policy_coverage_rate']}%")
        print(f"😊 企业满意度: {finance_data['policy_effectiveness']['enterprise_satisfaction']}%")

        print("\n🎯 政策有效性指标:")
        effectiveness = finance_data["policy_effectiveness"]["measurement_items"]
        for item, value in effectiveness.items():
            print(f"  - {item}: {value}%")

        return results

    def generate_report(self) -> dict[str, Any]:
        """生成综合报告"""
        print("\n" + "=" * 60)
        print("步骤 5: 生成企业端分析报告")
        print("=" * 60)

        report = {
            "title": "深圳半导体产业企业端分析报告",
            "region": "深圳市",
            "industry": "半导体产业",
            "year": 2025,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "land_cost_analysis": self.analyze_land_cost(),
            "labor_cost_analysis": self.analyze_labor_cost(),
            "energy_cost_analysis": self.analyze_energy_cost(),
            "financing_cost_analysis": self.analyze_financing_cost(),
            "comprehensive_cost_index": self.calculate_comprehensive_cost_index(),
            "supply_chain_analysis": self.analyze_supply_chain(),
            "policy_benefits_analysis": self.analyze_policy_benefits(),
            "overall_recommendations": [],
        }

        all_recommendations = []
        for analysis_name in [
            "land_cost_analysis",
            "labor_cost_analysis",
            "financing_cost_analysis",
            "supply_chain_analysis",
        ]:
            if "recommendations" in report[analysis_name]:
                all_recommendations.extend(report[analysis_name]["recommendations"])

        report["overall_recommendations"] = all_recommendations

        return report

    def save_report(self, report: dict[str, Any]):
        """保存报告"""
        output_file = self.output_dir / f"enterprise_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 报告已保存: {output_file}")
        return output_file

    def visualize_results(self, report: dict[str, Any]):
        """可视化结果"""
        print("\n" + "=" * 60)
        print("步骤 6: 生成可视化图表")
        print("=" * 60)

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("各区工业用地价格对比", "半导体行业薪资水平", "城市营商成本指数对比", "产业链覆盖度"),
            specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "bar"}, {"type": "bar"}]],
        )

        land_data = self.data["business_cost"]["land_cost"]
        areas = [d["area"] for d in land_data["data"]]
        prices = [d["industrial_price"] for d in land_data["data"]]

        fig.add_trace(go.Bar(x=areas, y=prices, name="工业用地价格", marker_color="#667eea"), row=1, col=1)

        position_salary = report["labor_cost_analysis"]["position_salary"]
        positions = list(position_salary.keys())
        salaries = list(position_salary.values())

        fig.add_trace(go.Bar(x=positions, y=salaries, name="薪资水平", marker_color="#764ba2"), row=1, col=2)

        cost_indices = report["comprehensive_cost_index"]["all_cities"]
        cities = list(cost_indices.keys())
        indices = list(cost_indices.values())

        fig.add_trace(go.Bar(x=cities, y=indices, name="成本指数", marker_color="#f093fb"), row=2, col=1)

        chain_coverage = report["chain_coverage"]
        segments = list(chain_coverage.keys())
        coverage = list(chain_coverage.values())

        fig.add_trace(go.Bar(x=segments, y=coverage, name="产业链覆盖度", marker_color="#4facfe"), row=2, col=2)

        fig.update_layout(title_text="深圳半导体产业企业端分析", height=800, showlegend=False)

        output_file = self.output_dir / f"enterprise_analysis_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(str(output_file))
        print(f"✅ 图表已保存: {output_file}")

        return output_file

    def run(self):
        """运行完整分析流程"""
        print("\n" + "=" * 60)
        print("深圳半导体产业企业端分析")
        print("=" * 60)

        report = self.generate_report()

        report_file = self.save_report(report)

        chart_file = self.visualize_results(report)

        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)
        print(f"\n📄 报告文件: {report_file}")
        print(f"📊 图表文件: {chart_file}")
        print(f"📁 输出目录: {self.output_dir}")

        return report


def main():
    """主函数"""
    runner = EnterpriseAnalysisRunner()
    report = runner.run()

    print("\n" + "=" * 60)
    print("核心发现汇总")
    print("=" * 60)

    print(f"\n💰 综合营商成本指数: {report['comprehensive_cost_index']['shenzhen_index']}")
    print(f"🏆 全国排名: 第{report['comprehensive_cost_index']['ranking']}位")

    print(
        f"\n🔗 产业链覆盖度: 上游{report['chain_coverage']['upstream']}% / 中游{report['chain_coverage']['midstream']}% / 下游{report['chain_coverage']['downstream']}%"
    )

    print(f"\n💵 政策红利总额: {report['policy_benefits_analysis']['total_support']}亿元")
    print(f"😊 企业满意度: {report['policy_benefits_analysis']['satisfaction_rate']}%")

    print(f"\n📋 优化建议数量: {len(report['overall_recommendations'])}条")
    for i, rec in enumerate(report["overall_recommendations"], 1):
        print(f"  {i}. [{rec['type']}] {rec['suggestion']}")


if __name__ == "__main__":
    main()
