"""
区域产业经济分析模板
可复用的分析框架，支持配置化切换地区和产业

使用方法：
1. 复制此模板到具体项目目录
2. 修改 REGION_CONFIG 和 INDUSTRY_CONFIG
3. 准备对应的数据文件
4. 运行分析脚本

模板特点：
- 配置化：轻松切换不同地区和产业
- 模块化：各分析功能独立
- 可扩展：方便添加新的分析维度
- 标准化：统一的输出格式和可视化
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置区域
REGION_CONFIG = {
    "name": "深圳",
    "code": "440300",
    "province": "广东省"
}

# 配置产业
INDUSTRY_CONFIG = {
    "name": "半导体",
    "code": "C39",
    "category": "制造业"
}


class AnalysisTemplate:
    """分析模板基类"""
    
    def __init__(self, region: Dict[str, Any], industry: Dict[str, Any]):
        self.region = region
        self.industry = industry
        self.data_dir = Path(__file__).parent.parent / f"{region['name']}_{industry['name']}_" / "data"
        self.output_dir = Path(__file__).parent.parent / f"{region['name']}_{industry['name']}_" / "outputs"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.data = {}
        self.analysis_results = {}
    
    def load_data(self) -> bool:
        """加载数据"""
        print(f"📂 加载 {self.region['name']} {self.industry['name']} 数据...")
        
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
                    print(f"  ✅ 加载 {filename}")
            else:
                print(f"  ⚠️ 文件不存在: {filename}")
        
        return len(self.data) > 0
    
    def analyze_business_cost(self) -> Dict[str, Any]:
        """分析营商成本"""
        raise NotImplementedError("子类必须实现此方法")
    
    def analyze_supply_chain(self) -> Dict[str, Any]:
        """分析供应链"""
        raise NotImplementedError("子类必须实现此方法")
    
    def analyze_policy(self) -> Dict[str, Any]:
        """分析政策"""
        raise NotImplementedError("子类必须实现此方法")
    
    def visualize(self, results: Dict[str, Any]) -> str:
        """可视化结果"""
        raise NotImplementedError("子类必须实现此方法")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        report = {
            "title": f"{self.region['name']}{self.industry['name']}产业分析报告",
            "region": self.region,
            "industry": self.industry,
            "year": datetime.now().year,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "business_cost_analysis": self.analyze_business_cost(),
            "supply_chain_analysis": self.analyze_supply_chain(),
            "policy_analysis": self.analyze_policy()
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], format: str = "json") -> str:
        """保存报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "json":
            filename = f"report_{timestamp}.json"
            output_file = self.output_dir / filename
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        elif format == "html":
            filename = f"report_{timestamp}.html"
            output_file = self.output_dir / filename
            html_content = self._generate_html_report(report)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        print(f"✅ 报告已保存: {output_file}")
        return str(output_file)
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """生成HTML报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #667eea; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f7fa; border-radius: 8px; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .metric .label {{ font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <h1>{report['title']}</h1>
    <p>📅 {report['generated_at']}</p>
    <p>📍 {report['region']['name']} | 🏭 {report['industry']['name']}</p>
    <hr>
    <div id="content">
        <h2>分析结果</h2>
        <pre>{json.dumps(report, ensure_ascii=False, indent=2)}</pre>
    </div>
</body>
</html>
"""
        return html
    
    def run(self, output_format: str = "json"):
        """运行完整分析流程"""
        print("\n" + "=" * 60)
        print(f"开始 {self.region['name']} {self.industry['name']} 产业分析")
        print("=" * 60)
        
        if not self.load_data():
            print("❌ 数据加载失败，退出分析")
            return None
        
        report = self.generate_report()
        
        output_file = self.save_report(report, format=output_format)
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)
        
        return report


class EnterpriseAnalysisTemplate(AnalysisTemplate):
    """企业端分析模板"""
    
    def analyze_business_cost(self) -> Dict[str, Any]:
        """分析营商成本"""
        print("\n🏢 分析营商成本...")
        
        if 'business_cost' not in self.data:
            return {}
        
        cost_data = self.data['business_cost']
        
        return {
            "land_cost": cost_data.get('land_cost', {}),
            "labor_cost": cost_data.get('labor_cost', {}),
            "energy_cost": cost_data.get('energy_cost', {}),
            "financing_cost": cost_data.get('financing_cost', {})
        }
    
    def analyze_supply_chain(self) -> Dict[str, Any]:
        """分析供应链"""
        print("\n🔗 分析供应链...")
        
        if 'supply_chain' not in self.data:
            return {}
        
        supply_data = self.data['supply_chain']
        
        return {
            "chain_coverage": supply_data.get('industry_chain_overview', {}),
            "localization_rate": supply_data.get('localization_metrics', {}).get('overall_localization_rate', 0),
            "bottlenecks": supply_data.get('localization_metrics', {}).get('key_bottlenecks', [])
        }
    
    def analyze_policy(self) -> Dict[str, Any]:
        """分析政策"""
        print("\n🎯 分析政策...")
        
        if 'finance_data' not in self.data:
            return {}
        
        finance_data = self.data['finance_data']
        
        return {
            "policy_support": finance_data.get('semiconductor_fiscal_support', {}),
            "tax_incentives": finance_data.get('fiscal_policy_details', {}).get('tax_incentives', {}),
            "effectiveness": finance_data.get('policy_effectiveness', {})
        }


class GovernmentAnalysisTemplate(AnalysisTemplate):
    """政府端分析模板"""
    
    def analyze_business_cost(self) -> Dict[str, Any]:
        """分析财政投入"""
        print("\n💰 分析财政投入...")
        
        if 'finance_data' not in self.data:
            return {}
        
        finance_data = self.data['finance_data']
        
        return {
            "fiscal_revenue": finance_data.get('general_fiscal', {}).get('revenue', {}),
            "fiscal_expenditure": finance_data.get('general_fiscal', {}).get('expenditure', {}),
            "sustainability": finance_data.get('sustainability_metrics', {})
        }
    
    def analyze_supply_chain(self) -> Dict[str, Any]:
        """分析产业链"""
        print("\n🔗 分析产业链...")
        
        if 'supply_chain' not in self.data:
            return {}
        
        supply_data = self.data['supply_chain']
        
        return {
            "upstream": supply_data.get('upstream_segment', {}),
            "midstream": supply_data.get('midstream_segment', {}),
            "downstream": supply_data.get('downstream_segment', {})
        }
    
    def analyze_policy(self) -> Dict[str, Any]:
        """分析政策效果"""
        print("\n📊 分析政策效果...")
        
        if 'finance_data' not in self.data:
            return {}
        
        finance_data = self.data['finance_data']
        
        return {
            "leverage_effect": finance_data.get('fiscal_leverage_analysis', {}),
            "driving_effects": finance_data.get('fiscal_leverage_analysis', {}).get('indirect_effects', {}),
            "multipliers": finance_data.get('fiscal_leverage_analysis', {}).get('multipliers', {})
        }


def main():
    """主函数示例"""
    print("=" * 60)
    print("区域产业经济分析模板")
    print("=" * 60)
    
    print(f"\n📍 分析区域: {REGION_CONFIG['name']}")
    print(f"🏭 分析产业: {INDUSTRY_CONFIG['name']}")
    
    enterprise_analyzer = EnterpriseAnalysisTemplate(REGION_CONFIG, INDUSTRY_CONFIG)
    government_analyzer = GovernmentAnalysisTemplate(REGION_CONFIG, INDUSTRY_CONFIG)
    
    enterprise_report = enterprise_analyzer.run(output_format="json")
    government_report = government_analyzer.run(output_format="json")
    
    if enterprise_report and government_report:
        print("\n✅ 企业端和政府端分析均已完成！")
        print(f"📁 报告保存在: {enterprise_analyzer.output_dir}")
    else:
        print("\n❌ 分析过程中出现问题，请检查数据文件")


if __name__ == "__main__":
    main()
