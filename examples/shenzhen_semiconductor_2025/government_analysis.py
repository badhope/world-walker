"""
深圳半导体产业政府端分析脚本
面向政府视角的产业政策分析

主要功能：
1. 财政杠杆率分析
2. 产业带动系数分析
3. 产业链补全度分析
4. 可视化展示

使用方法：
    python government_analysis.py
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.analysis.government_analyzer import GovernmentAnalyzer
from config import config_loader


class GovernmentAnalysisRunner:
    """政府端分析运行器"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        
        self.data = {}
        self.analysis_results = {}
        
        self.analyzer = GovernmentAnalyzer()
        self.load_data()
    
    def load_data(self):
        """加载数据文件"""
        print("=" * 60)
        print("步骤 1: 加载数据")
        print("=" * 60)
        
        data_files = [
            "basic_data.json",
            "business_cost.json",
            "supply_chain.json",
            "finance_data.json"
        ]
        
        for filename in data_files:
            filepath = self.data_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    key = filename.replace('.json', '')
                    self.data[key] = json.load(f)
                    print(f"✅ 加载 {filename}")
            else:
                print(f"❌ 文件不存在: {filename}")
        
        print(f"\n已加载 {len(self.data)} 个数据文件")
    
    def analyze_fiscal_leverage(self) -> Dict[str, Any]:
        """分析财政杠杆率"""
        print("\n" + "=" * 60)
        print("步骤 2.1: 财政杠杆率分析")
        print("=" * 60)
        
        finance_data = self.data['finance_data']
        basic_data = self.data['basic_data']
        
        results = {
            "fiscal_revenue": finance_data['general_fiscal']['revenue']['total'],
            "fiscal_expenditure": finance_data['general_fiscal']['expenditure']['total'],
            "deficit": finance_data['general_fiscal']['expenditure']['balance'],
            "deficit_rate": finance_data['general_fiscal']['deficit_rate'],
            "fiscal_self_sufficiency": finance_data['sustainability_metrics']['fiscal_self_sufficiency'],
            "debt_ratio": finance_data['sustainability_metrics']['debt_ratio'],
            "semiconductor_investment": finance_data['semiconductor_fiscal_support']['total_investment'],
            "leverage_effect": finance_data['semiconductor_fiscal_support']['leverage_effect'],
            "sustainability": finance_data['sustainability_metrics'],
            "recommendations": []
        }
        
        print(f"\n💰 一般公共预算:")
        print(f"  - 财政收入: {finance_data['general_fiscal']['revenue']['total']} 亿元")
        print(f"  - 财政支出: {finance_data['general_fiscal']['expenditure']['total']} 亿元")
        print(f"  - 财政赤字: {abs(finance_data['general_fiscal']['expenditure']['balance'])} 亿元")
        print(f"  - 赤字率: {finance_data['general_fiscal']['deficit_rate']}%")
        
        print(f"\n🏭 半导体产业财政支持:")
        print(f"  - 投资总额: {finance_data['semiconductor_fiscal_support']['total_investment']} 亿元")
        print(f"  - 撬动社会资本: {finance_data['semiconductor_fiscal_support']['leverage_effect']['social_capital_raised']} 亿元")
        print(f"  - 杠杆倍数: {finance_data['semiconductor_fiscal_support']['leverage_effect']['leverage_ratio']} 倍")
        print(f"  - 投入产出比: {finance_data['semiconductor_fiscal_support']['leverage_effect']['investment_output_ratio']}")
        
        print(f"\n📊 财政可持续性指标:")
        print(f"  - 财政自给率: {finance_data['sustainability_metrics']['fiscal_self_sufficiency']}%")
        print(f"  - 政府债务率: {finance_data['sustainability_metrics']['debt_ratio']}%")
        print(f"  - 债务覆盖率: {finance_data['sustainability_metrics']['debt_service']['debt_service_coverage_ratio']}")
        
        if results['deficit_rate'] < 15:
            results['recommendations'].append({
                "type": "财政杠杆",
                "suggestion": "财政赤字率控制在合理范围，风险可控"
            })
        
        if results['leverage_effect']['leverage_ratio'] > 1.5:
            results['recommendations'].append({
                "type": "财政杠杆",
                "suggestion": f"财政杠杆效应良好，1元投入撬动{results['leverage_effect']['leverage_ratio']}元社会资本"
            })
        
        return results
    
    def analyze_industry_driving(self) -> Dict[str, Any]:
        """分析产业带动系数"""
        print("\n" + "=" * 60)
        print("步骤 2.2: 产业带动系数分析")
        print("=" * 60)
        
        finance_data = self.data['finance_data']
        basic_data = self.data['basic_data']
        
        results = {
            "direct_effects": {
                "output_increase": finance_data['fiscal_leverage_analysis']['direct_effects']['industry_output_increase'],
                "yoy_growth": finance_data['fiscal_leverage_analysis']['direct_effects']['yoy_growth']
            },
            "indirect_effects": finance_data['fiscal_leverage_analysis']['indirect_effects'],
            "multipliers": finance_data['fiscal_leverage_analysis']['multipliers'],
            "employment_driven": basic_data['semiconductor_industry']['employment']['total'],
            "tax_contribution": basic_data['macro_economy']['industrial_output']['value'] * 0.15,
            "recommendations": []
        }
        
        print(f"\n🚗 直接带动效应:")
        print(f"  - 产业产值增长: {finance_data['fiscal_leverage_analysis']['direct_effects']['industry_output_increase']} 亿元")
        print(f"  - 同比增长: {finance_data['fiscal_leverage_analysis']['direct_effects']['yoy_growth']}%")
        
        print(f"\n🔄 间接带动效应:")
        print(f"  - 带动就业: {finance_data['fiscal_leverage_analysis']['indirect_effects']['employment_driven']} 人")
        print(f"  - 相关产业产值: {finance_data['fiscal_leverage_analysis']['indirect_effects']['related_industry_output']} 亿元")
        print(f"  - 税收贡献: {finance_data['fiscal_leverage_analysis']['indirect_effects']['tax_contribution']} 亿元")
        
        print(f"\n📈 乘数效应:")
        print(f"  - 财政支出乘数: {finance_data['fiscal_leverage_analysis']['multipliers']['fiscal_multiplier']}")
        print(f"  - 就业乘数: {finance_data['fiscal_leverage_analysis']['multipliers']['employment_multiplier']}")
        print(f"  - 产业产出乘数: {finance_data['fiscal_leverage_analysis']['multipliers']['output_multiplier']}")
        
        print(f"\n👥 就业带动:")
        print(f"  - 半导体行业从业人员: {basic_data['semiconductor_industry']['employment']['total']} 万人")
        print(f"  - 同比增长: {basic_data['semiconductor_industry']['employment']['growth_rate']}%")
        
        if results['multipliers']['fiscal_multiplier'] > 2.5:
            results['recommendations'].append({
                "type": "产业带动",
                "suggestion": f"财政乘数效应优秀，每元投入带动{results['multipliers']['fiscal_multiplier']}元产出"
            })
        
        return results
    
    def analyze_industry_chain(self) -> Dict[str, Any]:
        """分析产业链补全度"""
        print("\n" + "=" * 60)
        print("步骤 2.3: 产业链补全度分析")
        print("=" * 60)
        
        supply_chain = self.data['supply_chain']
        basic_data = self.data['basic_data']
        
        results = {
            "upstream_coverage": supply_chain['upstream_segment']['coverage_rate'],
            "midstream_coverage": supply_chain['midstream_segment']['coverage_rate'],
            "downstream_coverage": supply_chain['downstream_segment']['coverage_rate'],
            "overall_localization": supply_chain['localization_metrics']['overall_localization_rate'],
            "chain_outputs": supply_chain['industry_chain_overview'],
            "bottlenecks": supply_chain['localization_metrics']['key_bottlenecks'],
            "leading_companies": basic_data['leading_enterprises'],
            "recommendations": []
        }
        
        print(f"\n🔗 产业链覆盖度:")
        print(f"  - 上游（设计/材料/设备）: {supply_chain['upstream_segment']['coverage_rate']}%")
        print(f"  - 中游（制造/封测）: {supply_chain['midstream_segment']['coverage_rate']}%")
        print(f"  - 下游（应用/终端）: {supply_chain['downstream_segment']['coverage_rate']}%")
        
        print(f"\n🎯 整体国产化率: {supply_chain['localization_metrics']['overall_localization_rate']}%")
        print(f"🎯 2026年目标: {supply_chain['localization_metrics']['target_2026']}%")
        print(f"🎯 2030年目标: {supply_chain['localization_metrics']['target_2030']}%")
        
        print(f"\n⚠️ 关键瓶颈环节:")
        for i, bottleneck in enumerate(supply_chain['localization_metrics']['key_bottlenecks'], 1):
            print(f"  {i}. {bottleneck['segment']}")
            print(f"     进口依赖: {bottleneck['dependency']}%")
            print(f"     主要供应商: {bottleneck['supplier']}")
            print(f"     本地替代: {bottleneck['local_alternative']}")
            print(f"     风险等级: {bottleneck['risk_level']}")
        
        print(f"\n🏢 龙头企业:")
        for company in basic_data['leading_enterprises'][:5]:
            print(f"  - {company['name']} ({company['type']}): 营收{company['revenue']}亿元")
        
        if results['overall_localization'] > 60:
            results['recommendations'].append({
                "type": "产业链",
                "suggestion": "产业链完整性较好，建议重点突破上游设备和材料环节"
            })
        
        return results
    
    def analyze_policy_effectiveness(self) -> Dict[str, Any]:
        """分析政策有效性"""
        print("\n" + "=" * 60)
        print("步骤 2.4: 政策有效性评估")
        print("=" * 60)
        
        finance_data = self.data['finance_data']
        
        results = {
            "enterprise_satisfaction": finance_data['policy_effectiveness']['enterprise_satisfaction'],
            "measurement_items": finance_data['policy_effectiveness']['measurement_items'],
            "impact_indicators": finance_data['policy_effectiveness']['impact_indicators'],
            "cross_year_comparison": finance_data['cross_year_comparison'],
            "recommendations": []
        }
        
        print(f"\n😊 企业满意度: {finance_data['policy_effectiveness']['enterprise_satisfaction']}%")
        
        print(f"\n📊 各项指标评分:")
        for item, value in finance_data['policy_effectiveness']['measurement_items'].items():
            bar = "█" * int(value / 5)
            print(f"  {item}: {value}% {bar}")
        
        print(f"\n📈 政策成效指标:")
        for item, value in finance_data['policy_effectiveness']['impact_indicators'].items():
            print(f"  - {item}: +{value}%")
        
        print(f"\n📅 历年对比:")
        comparison = finance_data['cross_year_comparison']
        print(f"  财政支持: {comparison['fiscal_support']['2021']} → {comparison['fiscal_support']['2025']} 亿元")
        print(f"  杠杆倍数: {comparison['leverage_ratio']['2021']} → {comparison['leverage_ratio']['2025']}")
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        print("\n" + "=" * 60)
        print("步骤 3: 生成政府端分析报告")
        print("=" * 60)
        
        report = {
            "title": "深圳半导体产业政府端分析报告",
            "region": "深圳市",
            "industry": "半导体产业",
            "year": 2025,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fiscal_leverage_analysis": self.analyze_fiscal_leverage(),
            "industry_driving_analysis": self.analyze_industry_driving(),
            "industry_chain_analysis": self.analyze_industry_chain(),
            "policy_effectiveness_analysis": self.analyze_policy_effectiveness(),
            "overall_recommendations": []
        }
        
        all_recommendations = []
        for analysis_name in ['fiscal_leverage_analysis', 'industry_driving_analysis', 'industry_chain_analysis']:
            if 'recommendations' in report[analysis_name]:
                all_recommendations.extend(report[analysis_name]['recommendations'])
        
        report['overall_recommendations'] = all_recommendations
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """保存报告"""
        output_file = self.output_dir / f"government_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 报告已保存: {output_file}")
        return output_file
    
    def visualize_results(self, report: Dict[str, Any]):
        """可视化结果"""
        print("\n" + "=" * 60)
        print("步骤 4: 生成可视化图表")
        print("=" * 60)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '财政支出结构',
                '产业链覆盖度',
                '历年财政支持增长',
                '政策满意度评分'
            ),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        finance_data = self.data['finance_data']
        expenditure = finance_data['general_fiscal']['expenditure']
        expenditure_breakdown = expenditure['breakdown']
        
        labels = list(expenditure_breakdown.keys())[:-1]
        values = list(expenditure_breakdown.values())[:-1]
        
        fig.add_trace(
            go.Pie(labels=labels, values=values, name="支出结构"),
            row=1, col=1
        )
        
        chain_coverage = report['industry_chain_analysis']
        segments = ['上游', '中游', '下游']
        coverage = [chain_coverage['upstream_coverage'], 
                   chain_coverage['midstream_coverage'],
                   chain_coverage['downstream_coverage']]
        
        fig.add_trace(
            go.Bar(x=segments, y=coverage, name='产业链覆盖度', marker_color='#667eea'),
            row=1, col=2
        )
        
        years = [2021, 2022, 2023, 2024, 2025]
        fiscal_support = [report['fiscal_leverage_analysis']['semiconductor_investment'] * 
                         (report['policy_effectiveness_analysis']['cross_year_comparison']['fiscal_support'][str(y)] / 
                          report['policy_effectiveness_analysis']['cross_year_comparison']['fiscal_support']['2025'])
                          for y in years]
        
        fig.add_trace(
            go.Scatter(x=years, y=fiscal_support, mode='lines+markers', 
                       name='财政支持', line=dict(color='#764ba2', width=3)),
            row=2, col=1
        )
        
        satisfaction_items = report['policy_effectiveness_analysis']['measurement_items']
        items = list(satisfaction_items.keys())
        scores = list(satisfaction_items.values())
        
        fig.add_trace(
            go.Bar(x=items, y=scores, name='满意度', marker_color='#f093fb'),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="深圳半导体产业政府端分析",
            height=900,
            showlegend=False
        )
        
        output_file = self.output_dir / f"government_analysis_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(str(output_file))
        print(f"✅ 图表已保存: {output_file}")
        
        return output_file
    
    def run(self):
        """运行完整分析流程"""
        print("\n" + "=" * 60)
        print("深圳半导体产业政府端分析")
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
    runner = GovernmentAnalysisRunner()
    report = runner.run()
    
    print("\n" + "=" * 60)
    print("核心发现汇总")
    print("=" * 60)
    
    print(f"\n💰 半导体产业财政支持: {report['fiscal_leverage_analysis']['semiconductor_investment']}亿元")
    print(f"📈 杠杆倍数: {report['fiscal_leverage_analysis']['leverage_effect']['leverage_ratio']}倍")
    
    print(f"\n🚗 产业带动效应:")
    print(f"  - 带动就业: {report['industry_driving_analysis']['indirect_effects']['employment_driven']}人")
    print(f"  - 相关产业产值: {report['industry_driving_analysis']['indirect_effects']['related_industry_output']}亿元")
    
    print(f"\n🔗 产业链覆盖度:")
    print(f"  - 上游: {report['industry_chain_analysis']['upstream_coverage']}%")
    print(f"  - 中游: {report['industry_chain_analysis']['midstream_coverage']}%")
    print(f"  - 下游: {report['industry_chain_analysis']['downstream_coverage']}%")
    
    print(f"\n😊 企业满意度: {report['policy_effectiveness_analysis']['enterprise_satisfaction']}%")
    
    print(f"\n📋 政策建议数量: {len(report['overall_recommendations'])}条")
    for i, rec in enumerate(report['overall_recommendations'], 1):
        print(f"  {i}. [{rec['type']}] {rec['suggestion']}")


if __name__ == "__main__":
    main()
