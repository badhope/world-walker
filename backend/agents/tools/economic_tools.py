"""
经济分析工具集
"""
from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional
import akshare as ak
import pandas as pd
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DataFetcherTool(BaseTool):
    """数据采集工具"""

    name: str = "经济数据采集工具"
    description: str = """
    从官方数据源采集中国经济数据，包括：
    - GDP数据（季度/年度）
    - CPI/PPI价格指数
    - 货币供应量M0/M1/M2
    - PMI采购经理指数
    - 外汇储备
    - 贸易数据（进出口）
    - 财政数据（收入/支出）
    """

    def _run(self, indicator: str) -> str:
        return fetch_economic_data(indicator)


class IndicatorCalculatorTool(BaseTool):
    """指标计算工具"""

    name: str = "经济指标计算工具"
    description: str = """
    根据经济学公式计算衍生指标：
    - 财政赤字、赤字率、宏观税负
    - 城乡差距、贸易顺差
    - 三次产业占比
    """

    def _run(self, request: str) -> str:
        try:
            data = json.loads(request)
            return calculate_indicator(
                data["indicator"],
                data.get("inputs", {})
            )
        except Exception as e:
            return f"计算失败: {str(e)}"


class EconomicModelTool(BaseTool):
    """经济学模型工具"""

    name: str = "经济学模型分析工具"
    description: str = """
    运行经典经济学模型：
    - phillips: 菲利普斯曲线
    - okun: 奥肯定律
    - cobb_douglas: 柯布-道格拉斯生产函数
    - solow: 索洛增长模型
    """

    def _run(self, request: str) -> str:
        try:
            data = json.loads(request)
            return run_economic_model(
                data["model"],
                data.get("params", {})
            )
        except Exception as e:
            return f"模型运行失败: {str(e)}"


class ChartGeneratorTool(BaseTool):
    """图表生成工具"""

    name: str = "图表生成工具"
    description: str = """
    生成经济数据图表：
    - line: 折线图
    - bar: 柱状图
    - scatter: 散点图
    - pie: 饼图
    """

    def _run(self, request: str) -> str:
        try:
            data = json.loads(request)
            return generate_chart_html(
                data["chart_type"],
                data["data"],
                data.get("title", "")
            )
        except Exception as e:
            return f"图表生成失败: {str(e)}"


class ReportGeneratorTool(BaseTool):
    """报告生成工具"""

    name: str = "经济报告生成工具"
    description: str = "生成结构化的经济分析报告"

    def _run(self, request: str) -> str:
        try:
            data = json.loads(request)
            return generate_report(
                data.get("analysis_results", {}),
                data.get("data_summary", {}),
                data.get("insights", [])
            )
        except Exception as e:
            return f"报告生成失败: {str(e)}"


def fetch_economic_data(indicator: str) -> str:
    """采集经济数据"""
    results = []

    try:
        if indicator == "gdp":
            df = ak.macro_china_gdp()
            for _, row in df.tail(8).iterrows():
                results.append(f"{row['季度']}: GDP={row['国内生产总值-绝对值']}亿元")

        elif indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            for _, row in df.tail(12).iterrows():
                results.append(f"{row['日期']}: CPI={row['今值']}%")

        elif indicator == "m2":
            df = ak.macro_china_m2_yearly()
            for _, row in df.tail(12).iterrows():
                results.append(f"{row['日期']}: M2={row['今值']}%")

        elif indicator == "pmi":
            df = ak.macro_china_pmi_yearly()
            for _, row in df.tail(12).iterrows():
                results.append(f"{row['日期']}: PMI={row['制造业-指数']}")

        else:
            return f"未知指标: {indicator}"

        return "\n".join(results)

    except Exception as e:
        return f"采集失败: {str(e)}"


def calculate_indicator(indicator: str, inputs: Dict[str, float]) -> str:
    """计算经济指标"""
    formulas = {
        "fiscal_deficit": lambda x: x.get("expenditure", 0) - x.get("revenue", 0),
        "deficit_rate": lambda x: (x.get("expenditure", 0) - x.get("revenue", 0)) / max(x.get("gdp", 1), 1) * 100,
        "tax_ratio": lambda x: x.get("tax_revenue", 0) / max(x.get("gdp", 1), 1) * 100,
        "urban_rural_gap": lambda x: x.get("urban_income", 0) / max(x.get("rural_income", 1), 1),
        "trade_balance": lambda x: x.get("export", 0) - x.get("import", 0),
        "primary_ratio": lambda x: x.get("primary_industry", 0) / max(x.get("gdp", 1), 1) * 100,
        "secondary_ratio": lambda x: x.get("secondary_industry", 0) / max(x.get("gdp", 1), 1) * 100,
        "tertiary_ratio": lambda x: x.get("tertiary_industry", 0) / max(x.get("gdp", 1), 1) * 100,
    }

    if indicator not in formulas:
        return f"未知指标: {indicator}"

    try:
        value = formulas[indicator](inputs)
        return f"{indicator} = {value:.4f}"
    except Exception as e:
        return f"计算失败: {str(e)}"


def run_economic_model(model: str, params: Dict[str, Any]) -> str:
    """运行经济学模型"""
    results = []

    if model == "phillips":
        u = params.get("unemployment", 5.0)
        u_star = params.get("natural_unemployment", 5.0)
        pi_e = params.get("expected_inflation", 2.0)
        beta = params.get("beta", 0.5)
        inflation = pi_e - beta * (u - u_star)
        results.append(f"菲利普斯曲线: π = {inflation:.2f}%")
        results.append(f"解读: {'通胀压力' if inflation > 3 else '温和通胀'}")

    elif model == "okun":
        gdp_growth = params.get("gdp_growth", 5.0)
        potential_growth = params.get("potential_growth", 6.0)
        output_gap = gdp_growth - potential_growth
        results.append(f"奥肯定律: 产出缺口 = {output_gap:.2f}%")
        results.append(f"解读: {'经济过热' if output_gap > 0 else '经济下行'}")

    elif model == "cobb_douglas":
        k = params.get("capital", 100)
        l = params.get("labor", 100)
        alpha = params.get("alpha", 0.3)
        a = params.get("technology", 1.0)
        y = a * (k ** alpha) * (l ** (1 - alpha))
        results.append(f"柯布-道格拉斯: Y = {y:.2f}")

    elif model == "solow":
        s = params.get("savings_rate", 0.3)
        n = params.get("population_growth", 0.01)
        delta = params.get("depreciation", 0.05)
        alpha = params.get("alpha", 0.3)
        k_star = (s / (n + delta)) ** (1 / (1 - alpha))
        results.append(f"索洛模型: 稳态资本 k* = {k_star:.4f}")

    else:
        return f"未知模型: {model}"

    return "\n".join(results)


def generate_chart_html(chart_type: str, data: Dict[str, List], title: str) -> str:
    """生成图表 HTML"""
    import plotly.express as px
    import plotly.graph_objects as go

    df = pd.DataFrame(data)

    if chart_type == "line":
        fig = px.line(df, x=df.columns[0], y=df.columns[1:], title=title)
    elif chart_type == "bar":
        fig = px.bar(df, x=df.columns[0], y=df.columns[1:], title=title)
    elif chart_type == "scatter":
        fig = px.scatter(df, x=df.columns[0], y=df.columns[1], title=title)
    elif chart_type == "pie":
        fig = px.pie(df, names=df.columns[0], values=df.columns[1], title=title)
    else:
        return f"未知图表类型: {chart_type}"

    fig.update_layout(template="plotly_white")
    return fig.to_html(full_html=False)


def generate_report(
    analysis: Dict[str, Any],
    data_summary: Dict[str, Any],
    insights: List[str]
) -> str:
    """生成报告"""
    timestamp = datetime.now().strftime("%Y年%m月%d日")

    report = f"""
# 经济分析报告

**生成时间**: {timestamp}

## 执行摘要

{chr(10).join(f"- {i}" for i in insights[:3]) if insights else "数据收集中..."}

## 数据概览

| 指标 | 值 |
|------|-----|
"""
    for key, value in data_summary.items():
        report += f"| {key} | {value} |\n"

    report += """
## 详细分析

"""
    for key, value in analysis.items():
        report += f"### {key}\n{value}\n\n"

    report += "\n*报告由 NEDAP AI 系统自动生成*"
    return report
