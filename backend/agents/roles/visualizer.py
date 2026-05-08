"""
可视化智能体 - 生成经济数据图表和可视化
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class ChartGeneratorTool(BaseTool):
    """图表生成工具"""

    name: str = "图表生成工具"
    description: str = """
    生成各类经济数据图表：
    - line: 折线图（时间序列）
    - bar: 柱状图（对比分析）
    - scatter: 散点图（相关性）
    - pie: 饼图（结构占比）
    输入格式：JSON字符串如 '{"chart_type": "line", "data": {"x": [...], "y": [...]}, "title": "标题"}'
    """

    def _run(self, request: str) -> str:
        import json
        try:
            data = json.loads(request)
            chart = generate_chart(
                data["chart_type"],
                data["data"],
                data.get("title", "")
            )
            return chart
        except Exception as e:
            return f"图表生成失败: {str(e)}"


class DashboardTool(BaseTool):
    """仪表盘生成工具"""

    name: str = "经济仪表盘工具"
    description: str = """
    生成综合经济指标仪表盘，展示多个关键指标的时序变化
    输入格式：JSON字符串如 '{"metrics": [{"name": "GDP", "data": [...]}, ...], "title": "仪表盘标题"}'
    """

    def _run(self, request: str) -> str:
        import json
        try:
            data = json.loads(request)
            dashboard = generate_dashboard(
                data["metrics"],
                data.get("title", "经济指标仪表盘")
            )
            return dashboard
        except Exception as e:
            return f"仪表盘生成失败: {str(e)}"


def generate_chart(chart_type: str, data: Dict[str, List], title: str) -> str:
    """生成图表"""
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


def generate_dashboard(metrics: List[Dict[str, Any]], title: str) -> str:
    """生成仪表盘"""
    from plotly.subplots import make_subplots

    n = len(metrics)
    fig = make_subplots(
        rows=n, cols=1,
        subplot_titles=[m["name"] for m in metrics],
        vertical_spacing=0.08
    )

    colors = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#00f2fe"]

    for i, metric in enumerate(metrics, 1):
        fig.add_trace(
            go.Scatter(
                x=metric.get("x", list(range(len(metric["data"])))),
                y=metric["data"],
                mode="lines+markers",
                name=metric["name"],
                line=dict(color=colors[(i-1) % len(colors)])
            ),
            row=i, col=1
        )

    fig.update_layout(
        title=title,
        height=200 * n,
        showlegend=False,
        template="plotly_white"
    )

    return fig.to_html(full_html=False)


class VisualizerAgent:
    """可视化智能体"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [ChartGeneratorTool(), DashboardTool()]

    def create_agent(self) -> Agent:
        """创建可视化智能体"""
        return Agent(
            role="数据可视化专家",
            goal="将复杂的经济数据转化为直观、美观的可视化图表",
            backstory="""
            你是一位专业的数据可视化专家，擅长将枯燥的数字转化为有说服力的图表。
            你精通各种图表类型的适用场景：
            - 折线图适合展示趋势变化
            - 柱状图适合比较分析
            - 散点图适合展示相关性
            - 饼图适合展示结构占比
            你的图表不仅美观，而且信息传达准确有效。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )

    @staticmethod
    def get_supported_chart_types() -> List[str]:
        """获取支持的图表类型"""
        return ["line", "bar", "scatter", "pie"]
