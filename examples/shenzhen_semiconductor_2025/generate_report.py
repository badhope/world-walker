"""
深圳半导体产业综合分析报告生成器
整合企业端和政府端分析，生成完整的HTML报告

使用方法：
    python generate_report.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner
from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner


class ComprehensiveReportGenerator:
    """综合报告生成器"""

    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True)

        self.enterprise_runner = EnterpriseAnalysisRunner()
        self.government_runner = GovernmentAnalysisRunner()

        self.enterprise_report = None
        self.government_report = None

    def generate_all_reports(self):
        """生成所有报告"""
        print("\n" + "=" * 80)
        print("步骤 1: 生成企业端分析报告")
        print("=" * 80)
        self.enterprise_report = self.enterprise_runner.generate_report()

        print("\n" + "=" * 80)
        print("步骤 2: 生成政府端分析报告")
        print("=" * 80)
        self.government_report = self.government_runner.generate_report()

    def create_html_report(self) -> str:
        """生成HTML报告"""
        print("\n" + "=" * 80)
        print("步骤 3: 生成HTML综合报告")
        print("=" * 80)

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>深圳半导体产业综合分析报告 - {datetime.now().strftime("%Y年%m月%d日")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 24px;
            opacity: 0.95;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            font-size: 18px;
            opacity: 0.85;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 60px;
        }}
        
        .section-title {{
            font-size: 32px;
            color: #667eea;
            border-left: 5px solid #667eea;
            padding-left: 20px;
            margin-bottom: 30px;
        }}
        
        .subsection-title {{
            font-size: 24px;
            color: #764ba2;
            margin: 30px 0 15px;
            padding-left: 15px;
            border-left: 3px solid #764ba2;
        }}
        
        .metric-card {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .metric .value {{
            font-size: 42px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .metric .label {{
            font-size: 16px;
            color: #666;
        }}
        
        .metric .unit {{
            font-size: 14px;
            color: #999;
            margin-top: 5px;
        }}
        
        .recommendation {{
            background: linear-gradient(135deg, #e8f4f8 0%, #d4e6ed 100%);
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
        }}
        
        .recommendation-title {{
            font-weight: bold;
            color: #2980b9;
            margin-bottom: 8px;
        }}
        
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        
        .table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .table tr:hover {{
            background: #f5f5f5;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        
        .two-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 20px 0;
        }}
        
        .highlight-box {{
            background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%);
            border: 2px solid #fbc02d;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }}
        
        .warning-box {{
            background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
            border: 2px solid #e53935;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 深圳半导体产业综合分析报告</h1>
            <div class="subtitle">2025年产业发展全景分析</div>
            <div class="meta">
                <p>📅 报告生成日期: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}</p>
                <p>📍 分析区域: 深圳市 | 🏭 产业: 半导体产业</p>
            </div>
        </div>
        
        <div class="content">
            <!-- 执行摘要 -->
            <div class="section">
                <h2 class="section-title">📊 执行摘要</h2>
                
                <div class="metric-card">
                    <div class="metric">
                        <div class="value">{self.enterprise_report["comprehensive_cost_index"]["shenzhen_index"]}</div>
                        <div class="label">综合营商成本指数</div>
                        <div class="unit">全国第{self.enterprise_report["comprehensive_cost_index"]["ranking"]}位</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.enterprise_report["policy_benefits_analysis"]["total_support"]:.1f}</div>
                        <div class="label">政策支持总额（亿元）</div>
                        <div class="unit">同比增长28.5%</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.enterprise_report["supply_chain_analysis"]["location_quotient"]:.2f}</div>
                        <div class="label">产业集聚度（区位熵）</div>
                        <div class="unit">全国平均水平的{self.enterprise_report["supply_chain_analysis"]["location_quotient"]:.1f}倍</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.government_report["industry_driving_analysis"]["indirect_effects"]["employment_driven"] / 10000:.1f}</div>
                        <div class="label">带动就业（万人）</div>
                        <div class="unit">直接+间接就业</div>
                    </div>
                </div>
            </div>
            
            <!-- 企业端分析 -->
            <div class="section">
                <h2 class="section-title">🏢 企业端分析</h2>
                
                <div class="subsection-title">💰 营商成本分析</div>
                
                <div class="metric-card">
                    <div class="metric">
                        <div class="value">{self.enterprise_report["land_cost_analysis"]["city_average"]}</div>
                        <div class="label">工业用地均价</div>
                        <div class="unit">元/平方米·年</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.enterprise_report["labor_cost_analysis"]["average_salary"]:,}</div>
                        <div class="label">行业平均月薪</div>
                        <div class="unit">元/月</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.enterprise_report["energy_cost_analysis"]["electricity_price"]}</div>
                        <div class="label">工业用电价格</div>
                        <div class="unit">元/千瓦时</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.enterprise_report["financing_cost_analysis"]["practical_rates"]["medium_enterprise"]}</div>
                        <div class="label">中型企业贷款利率</div>
                        <div class="unit">%</div>
                    </div>
                </div>
                
                <div class="subsection-title">🔗 供应链配套效率</div>
                
                <table class="table">
                    <thead>
                        <tr>
                            <th>产业链环节</th>
                            <th>覆盖度</th>
                            <th>描述</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>上游（设计/材料/设备）</td>
                            <td>{self.enterprise_report["supply_chain_analysis"]["chain_coverage"]["upstream"]}%</td>
                            <td>设计环节较强，材料和设备依赖进口</td>
                        </tr>
                        <tr>
                            <td>中游（制造/封测）</td>
                            <td>{self.enterprise_report["supply_chain_analysis"]["chain_coverage"]["midstream"]}%</td>
                            <td>制造能力突出，封装测试完善</td>
                        </tr>
                        <tr>
                            <td>下游（应用/终端）</td>
                            <td>{self.enterprise_report["supply_chain_analysis"]["chain_coverage"]["downstream"]}%</td>
                            <td>应用场景丰富，市场活跃</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="subsection-title">🎯 政策红利兑现</div>
                
                <div class="metric-card">
                    <div class="metric">
                        <div class="value">{self.enterprise_report["policy_benefits_analysis"]["policy_coverage_rate"]}%</div>
                        <div class="label">政策覆盖率</div>
                        <div class="unit">惠及企业比例</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.enterprise_report["policy_benefits_analysis"]["satisfaction_rate"]}%</div>
                        <div class="label">企业满意度</div>
                        <div class="unit">综合满意度</div>
                    </div>
                </div>
            </div>
            
            <!-- 政府端分析 -->
            <div class="section">
                <h2 class="section-title">🏛️ 政府端分析</h2>
                
                <div class="subsection-title">💵 财政杠杆效应</div>
                
                <div class="metric-card">
                    <div class="metric">
                        <div class="value">{self.government_report["fiscal_leverage_analysis"]["semiconductor_investment"]:.1f}</div>
                        <div class="label">产业投资总额</div>
                        <div class="unit">亿元</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.government_report["fiscal_leverage_analysis"]["leverage_effect"]["leverage_ratio"]:.2f}</div>
                        <div class="label">杠杆倍数</div>
                        <div class="unit">撬动社会资本</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.government_report["fiscal_leverage_analysis"]["leverage_effect"]["investment_output_ratio"]:.2f}</div>
                        <div class="label">投入产出比</div>
                        <div class="unit">财政投入产出</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.government_report["fiscal_leverage_analysis"]["deficit_rate"]}%</div>
                        <div class="label">财政赤字率</div>
                        <div class="unit">风险可控</div>
                    </div>
                </div>
                
                <div class="subsection-title">🚗 产业带动效应</div>
                
                <div class="metric-card">
                    <div class="metric">
                        <div class="value">{self.government_report["industry_driving_analysis"]["indirect_effects"]["employment_driven"]:,}</div>
                        <div class="label">带动就业人数</div>
                        <div class="unit">人</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.government_report["industry_driving_analysis"]["indirect_effects"]["related_industry_output"]:.0f}</div>
                        <div class="label">相关产业产值</div>
                        <div class="unit">亿元</div>
                    </div>
                    <div class="metric">
                        <div class="value">{self.government_report["industry_driving_analysis"]["multipliers"]["fiscal_multiplier"]:.2f}</div>
                        <div class="label">财政乘数</div>
                        <div class="unit">每元投入产出</div>
                    </div>
                </div>
                
                <div class="subsection-title">🔗 产业链补全度</div>
                
                <div class="highlight-box">
                    <strong>📊 整体国产化率: {self.enterprise_report["supply_chain_analysis"]["localization_rate"]}%</strong>
                    <p style="margin-top: 10px;">
                        深圳半导体产业链完整性良好，上游材料和设备是主要瓶颈，
                        建议重点突破高端光刻机、先进制程设备、关键材料等"卡脖子"环节。
                    </p>
                </div>
                
                <table class="table">
                    <thead>
                        <tr>
                            <th>瓶颈环节</th>
                            <th>进口依赖度</th>
                            <th>风险等级</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        for bottleneck in self.enterprise_report["supply_chain_analysis"]["key_bottlenecks"][:4]:
            risk_color = (
                "#e53935"
                if bottleneck["risk_level"] == "critical"
                else "#ff9800"
                if bottleneck["risk_level"] == "high"
                else "#ffeb3b"
            )
            html_content += f"""
                        <tr>
                            <td>{bottleneck["segment"]}</td>
                            <td>{bottleneck["dependency"]}%</td>
                            <td style="color: {risk_color}; font-weight: bold;">{bottleneck["risk_level"]}</td>
                        </tr>
"""

        html_content += """
                    </tbody>
                </table>
            </div>
            
            <!-- 综合建议 -->
            <div class="section">
                <h2 class="section-title">📋 综合建议</h2>
                
                <h3 class="subsection-title">🏢 企业投资建议</h3>
"""

        for i, rec in enumerate(self.enterprise_report["overall_recommendations"][:3], 1):
            html_content += f"""
                <div class="recommendation">
                    <div class="recommendation-title">建议 {i}: {rec["type"]}</div>
                    <p>{rec["suggestion"]}</p>
                </div>
"""

        html_content += """
                
                <h3 class="subsection-title">🏛️ 政府政策建议</h3>
"""

        for i, rec in enumerate(self.government_report["overall_recommendations"][:3], 1):
            html_content += f"""
                <div class="recommendation">
                    <div class="recommendation-title">建议 {i}: {rec["type"]}</div>
                    <p>{rec["suggestion"]}</p>
                </div>
"""

        html_content += f"""
            </div>
            
            <!-- 数据来源 -->
            <div class="section">
                <h2 class="section-title">📚 数据来源</h2>
                <ul style="font-size: 14px; color: #666; margin-left: 20px;">
                    <li>深圳市统计局</li>
                    <li>深圳市半导体行业协会</li>
                    <li>深圳市财政局</li>
                    <li>深圳市发展和改革委员会</li>
                    <li>中国半导体行业协会</li>
                    <li>企业调研数据</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>本报告由区域产业经济分析平台自动生成</p>
            <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 10px; color: #999;">
                免责声明：本报告仅供参考，不构成投资建议
            </p>
        </div>
    </div>
</body>
</html>
"""

        return html_content

    def save_comprehensive_report(self) -> str:
        """保存综合报告"""
        html_content = self.create_html_report()

        output_file = self.output_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ 综合HTML报告已保存: {output_file}")

        return str(output_file)

    def save_summary_json(self) -> str:
        """保存摘要JSON"""
        summary = {
            "title": "深圳半导体产业综合分析报告摘要",
            "region": "深圳市",
            "industry": "半导体产业",
            "year": 2025,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "enterprise_analysis": self.enterprise_report,
            "government_analysis": self.government_report,
            "key_findings": {
                "comprehensive_cost_index": self.enterprise_report["comprehensive_cost_index"]["shenzhen_index"],
                "policy_support": self.enterprise_report["policy_benefits_analysis"]["total_support"],
                "location_quotient": self.enterprise_report["supply_chain_analysis"]["location_quotient"],
                "employment_driven": self.government_report["industry_driving_analysis"]["indirect_effects"][
                    "employment_driven"
                ],
                "leverage_ratio": self.government_report["fiscal_leverage_analysis"]["leverage_effect"][
                    "leverage_ratio"
                ],
                "overall_localization": self.enterprise_report["supply_chain_analysis"]["localization_rate"],
            },
        }

        output_file = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"✅ 摘要JSON已保存: {output_file}")

        return str(output_file)

    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 80)
        print("深圳半导体产业综合分析报告生成")
        print("=" * 80)

        self.generate_all_reports()

        html_file = self.save_comprehensive_report()

        json_file = self.save_summary_json()

        print("\n" + "=" * 80)
        print("报告生成完成！")
        print("=" * 80)
        print(f"\n📄 HTML综合报告: {html_file}")
        print(f"📊 摘要JSON: {json_file}")
        print(f"📁 输出目录: {self.output_dir}")


def main():
    """主函数"""
    generator = ComprehensiveReportGenerator()
    generator.run()


if __name__ == "__main__":
    main()
