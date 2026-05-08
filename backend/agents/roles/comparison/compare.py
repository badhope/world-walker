"""
对比分析模块

功能：
1. 省际数据对比
2. 历史趋势对比
3. 地区经济对比
4. 结构对比
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging

logger = logging.getLogger(__name__)


# 模拟省份数据 (实际需从各省市统计局API获取)
PROVINCE_DATA = {
    "gdp_2024": {
        "广东": 135000, "江苏": 128000, "山东": 95000, "浙江": 82000,
        "河南": 59000, "四川": 56000, "湖北": 55000, "福建": 54000,
        "湖南": 51000, "安徽": 47000, "河北": 45000, "上海": 48000,
        "北京": 44000, "陕西": 33000, "江西": 32000, "重庆": 30000,
        "云南": 29000, "广西": 27000, "山西": 25000, "内蒙古": 24000,
        "贵州": 22000, "黑龙江": 20000, "新疆": 19000, "吉林": 15000,
        "甘肃": 12000, "海南": 8000, "宁夏": 5500, "青海": 4000,
        "西藏": 2500
    },
    "gdp_growth_2024": {
        "广东": 4.2, "江苏": 4.7, "山东": 5.1, "浙江": 5.0,
        "河南": 3.8, "四川": 5.0, "湖北": 5.3, "福建": 5.5,
        "湖南": 4.2, "安徽": 5.5, "河北": 4.0, "上海": 4.8,
        "北京": 5.2, "陕西": 4.3, "江西": 4.5, "重庆": 5.6,
        "云南": 3.5, "广西": 3.6, "山西": 4.5, "内蒙古": 5.0,
        "贵州": 4.5, "黑龙江": 3.0, "新疆": 5.0, "吉林": 4.0,
        "甘肃": 4.0, "海南": 5.5, "宁夏": 4.8, "青海": 4.5,
        "西藏": 5.5
    },
    "fiscal_revenue_2024": {
        "广东": 14000, "江苏": 13000, "山东": 10000, "浙江": 12000,
        "河南": 4500, "四川": 4800, "湖北": 4200, "福建": 3800,
        "湖南": 3800, "安徽": 3500, "河北": 3800, "上海": 9500,
        "北京": 6800, "陕西": 3200, "江西": 3000, "重庆": 2600,
        "云南": 2200, "广西": 2000, "山西": 2800, "内蒙古": 2000,
    },
    "fiscal_expenditure_2024": {
        "广东": 18000, "江苏": 16500, "山东": 13500, "浙江": 14500,
        "河南": 9500, "四川": 11000, "湖北": 9000, "福建": 7500,
        "湖南": 8500, "安徽": 8000, "河北": 8500, "上海": 10500,
        "北京": 8000, "陕西": 6800, "江西": 6800, "重庆": 5500,
        "云南": 6500, "广西": 6200, "山西": 5800, "内蒙古": 5500,
    }
}


class ProvinceComparisonTool(BaseTool):
    """省际对比工具"""

    name: str = "省际经济数据对比工具"
    description: str = """
    对比各省份的经济数据
    输入格式: JSON {"indicator": "gdp_2024", "top_n": 10}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return compare_provinces(
                params.get("indicator"),
                params.get("top_n", 10)
            )
        except Exception as e:
            return f"省际对比失败: {str(e)}"


class TrendAnalysisTool(BaseTool):
    """趋势分析工具"""

    name: str = "历史趋势分析工具"
    description: str = """
    分析指标的历史趋势
    输入: 指标名称字符串，如 'gdp', 'cpi', 'm2'
    """

    def _run(self, indicator: str) -> str:
        return analyze_trend(indicator)


class StructureComparisonTool(BaseTool):
    """结构对比工具"""

    name: str = "经济结构对比工具"
    description: str = """
    对比经济结构变化
    输入格式: JSON {"type": "industry", "years": [2020, 2024]}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return compare_structure(
                params.get("type"),
                params.get("years", [2020, 2024])
            )
        except Exception as e:
            return f"结构对比失败: {str(e)}"


class VisualizationTool(BaseTool):
    """可视化生成工具"""

    name: str = "对比可视化生成工具"
    description: str = """
    生成对比图表
    输入格式: JSON {"chart_type": "bar", "data": {...}, "title": "标题"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return generate_comparison_chart(
                params.get("chart_type", "bar"),
                params.get("data", {}),
                params.get("title", "对比分析")
            )
        except Exception as e:
            return f"可视化生成失败: {str(e)}"


# ==================== 核心对比函数 ====================

def compare_provinces(indicator: str, top_n: int = 10) -> str:
    """
    省际数据对比
    """
    results = []
    results.append(f"📊 省际对比: {indicator}")
    results.append(f"显示前 {top_n} 名")
    results.append("=" * 60)

    if indicator not in PROVINCE_DATA:
        available = ", ".join(PROVINCE_DATA.keys())
        return f"暂不支持指标 {indicator}，可用: {available}"

    data = PROVINCE_DATA[indicator]

    # 排序
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    results.append("\n排名  省份           数值")
    results.append("-" * 40)

    total = sum(data.values())

    for i, (province, value) in enumerate(sorted_data[:top_n], 1):
        share = value / total * 100 if total else 0
        results.append(f"{i:2d}.  {province:8s}  {value:>12,.0f}  ({share:>5.1f}%)")

    if top_n < len(sorted_data):
        others_value = sum(v for _, v in sorted_data[top_n:])
        others_share = others_value / total * 100 if total else 0
        results.append(f"     其他{len(sorted_data)-top_n}省    {others_value:>12,.0f}  ({others_share:>5.1f}%)")

    # 计算集中度
    top3_share = sum(v for _, v in sorted_data[:3]) / total * 100 if total else 0
    top5_share = sum(v for _, v in sorted_data[:5]) / total * 100 if total else 0
    top10_share = sum(v for _, v in sorted_data[:10]) / total * 100 if total else 0

    results.append("\n" + "-" * 40)
    results.append("集中度分析:")
    results.append(f"  前3省占比: {top3_share:.1f}%")
    results.append(f"  前5省占比: {top5_share:.1f}%")
    results.append(f"  前10省占比: {top10_share:.1f}%")

    return "\n".join(results)


def analyze_trend(indicator: str) -> str:
    """
    历史趋势分析
    """
    results = []
    results.append(f"📈 趋势分析: {indicator}")
    results.append("=" * 60)

    try:
        import akshare as ak

        if indicator == "gdp":
            df = ak.macro_china_gdp()
            if not df.empty:
                results.append(f"\nGDP历史数据 (近10期):")
                results.append("-" * 40)

                for _, row in df.tail(10).iterrows():
                    quarter = row["季度"]
                    value = row["国内生产总值-绝对值"]
                    results.append(f"  {quarter}: {value:,.0f} 亿元")

                # 计算增速
                values = df["国内生产总值-绝对值"].dropna().values
                if len(values) >= 2:
                    growth = (values[-1] - values[-2]) / values[-2] * 100
                    results.append(f"\n同比增速: {growth:.2f}%")

                    if len(values) >= 4:
                        growths = [(values[i] - values[i-1]) / values[i-1] * 100 for i in range(1, len(values))]
                        avg_growth = np.mean(growths[-4:])
                        results.append(f"平均增速: {avg_growth:.2f}%")

                        # 趋势判断
                        recent_3 = growths[-3:]
                        if all(g > avg_growth for g in recent_3):
                            results.append(f"趋势: 📈 上升中")
                        elif all(g < avg_growth for g in recent_3):
                            results.append(f"趋势: 📉 下降中")
                        else:
                            results.append(f"趋势: ➡️ 平稳")

        elif indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            if not df.empty:
                results.append(f"\nCPI历史数据 (近10期):")
                results.append("-" * 40)

                for _, row in df.tail(10).iterrows():
                    date = row["日期"]
                    value = row["今值"]
                    results.append(f"  {date}: {value:.1f}%")

        elif indicator == "m2":
            df = ak.macro_china_m2_yearly()
            if not df.empty:
                results.append(f"\nM2历史数据 (近10期):")
                results.append("-" * 40)

                for _, row in df.tail(10).iterrows():
                    date = row["日期"]
                    value = row["今值"]
                    results.append(f"  {date}: {value:.1f}%")

        else:
            results.append(f"\n暂支持指标: gdp, cpi, m2")

        return "\n".join(results)

    except Exception as e:
        logger.error(f"趋势分析失败: {e}")
        return f"趋势分析失败: {str(e)}"


def compare_structure(compare_type: str, years: List[int]) -> str:
    """
    经济结构对比
    """
    results = []
    results.append(f"🔄 结构对比: {compare_type}")
    results.append(f"对比年份: {years}")
    results.append("=" * 60)

    if compare_type == "industry":
        # 模拟产业结构数据
        data_2020 = {"第一产业": 7.7, "第二产业": 37.8, "第三产业": 54.5}
        data_2024 = {"第一产业": 6.2, "第二产业": 38.3, "第三产业": 55.5}

        results.append("\n产业结构变化 (%):")
        results.append("-" * 40)
        results.append(f"{'产业':12s}  {'2020':>8s}  {'2024':>8s}  {'变化':>8s}")
        results.append("-" * 40)

        for sector in ["第一产业", "第二产业", "第三产业"]:
            v2020 = data_2020.get(sector, 0)
            v2024 = data_2024.get(sector, 0)
            change = v2024 - v2020
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            results.append(f"{sector:12s}  {v2020:>7.1f}%  {v2024:>7.1f}%  {arrow}{abs(change):.1f}%")

        results.append("\n📝 分析:")
        results.append("  - 第三产业占比提升，经济结构持续优化")
        results.append("  - 第一产业比重下降，符合发达国家规律")
        results.append("  - 第二产业保持稳定，制造业转型中")

    return "\n".join(results)


def generate_comparison_chart(chart_type: str, data: Dict, title: str) -> str:
    """
    生成对比图表
    """
    try:
        df = pd.DataFrame(data)

        if chart_type == "bar":
            fig = px.bar(
                df, x=df.columns[0], y=df.columns[1:].tolist(),
                title=title, barmode='group'
            )
        elif chart_type == "line":
            fig = px.line(df, x=df.columns[0], y=df.columns[1:].tolist(), title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=df.columns[0], values=df.columns[1], title=title)
        elif chart_type == "treemap":
            fig = px.treemap(df, names=df.columns[0], values=df.columns[1], title=title)
        else:
            return f"不支持的图表类型: {chart_type}"

        fig.update_layout(template="plotly_white")
        return fig.to_html(full_html=False)

    except Exception as e:
        return f"图表生成失败: {str(e)}"


class ComparisonAgent:
    """对比分析 Agent"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [
            ProvinceComparisonTool(),
            TrendAnalysisTool(),
            StructureComparisonTool(),
            VisualizationTool(),
        ]

    def create_agent(self) -> Agent:
        """创建对比分析 Agent"""
        return Agent(
            role="对比分析专家",
            goal="深入挖掘数据关系，发现趋势和规律",
            backstory="""
            你是一位资深的经济分析师，擅长多维度对比分析：
            - 纵向对比: 历史趋势分析，发现增长规律
            - 横向对比: 不同地区/行业对比，发现差异
            - 结构对比: 产业结构演变分析
            - 增速对比: 增长动力分析

            你能从对比中发现隐藏的规律和异常，为决策提供依据。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )
