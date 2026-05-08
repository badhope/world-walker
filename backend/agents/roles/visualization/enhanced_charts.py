"""
增强可视化模块 - 支持更多图表类型
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
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class HeatmapTool(BaseTool):
    """相关性热力图工具"""

    name: str = "相关性热力图生成工具"
    description: str = """
    生成经济指标之间的相关性热力图
    输入格式: JSON {"indicators": ["gdp", "cpi", "m2", "pmi"], "title": "标题"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return generate_correlation_heatmap(
                params.get("indicators", []),
                params.get("title", "经济指标相关性热力图")
            )
        except Exception as e:
            return f"热力图生成失败: {str(e)}"


class RadarChartTool(BaseTool):
    """雷达图工具"""

    name: str = "雷达图生成工具"
    description: str = """
    生成多维度雷达图，用于综合评价
    输入格式: JSON {"dimensions": {"GDP": 80, "CPI": 60, ...}, "title": "标题"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return generate_radar_chart(
                params.get("dimensions", {}),
                params.get("title", "经济指标雷达图")
            )
        except Exception as e:
            return f"雷达图生成失败: {str(e)}"


class ProvinceMapTool(BaseTool):
    """省份地图可视化工具"""

    name: str = "省份地图可视化工具"
    description: str = """
    生成中国省份经济数据地图
    输入格式: JSON {"indicator": "gdp", "title": "标题"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return generate_province_map(
                params.get("indicator", "gdp"),
                params.get("title", "各省经济指标")
            )
        except Exception as e:
            return f"地图生成失败: {str(e)}"


class DashboardGeneratorTool(BaseTool):
    """仪表盘生成工具"""

    name: str = "综合仪表盘生成工具"
    description: str = """
    生成综合经济指标仪表盘
    输入格式: JSON {"indicators": ["cpi", "ppi", "m2", "pmi"], "title": "标题"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return generate_dashboard(
                params.get("indicators", []),
                params.get("title", "经济指标仪表盘")
            )
        except Exception as e:
            return f"仪表盘生成失败: {str(e)}"


class TrendForecastTool(BaseTool):
    """趋势预测工具"""

    name: str = "趋势预测工具"
    description: str = """
    基于历史数据预测未来趋势
    输入格式: JSON {"indicator": "gdp", "periods": 6, "method": "linear"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return forecast_trend(
                params.get("indicator", "gdp"),
                params.get("periods", 6),
                params.get("method", "linear")
            )
        except Exception as e:
            return f"预测失败: {str(e)}"


class AnomalyAlertTool(BaseTool):
    """异常预警工具"""

    name: str = "数据异常预警工具"
    description: str = """
    检测数据异常并生成预警
    输入格式: JSON {"indicator": "gdp", "threshold": 2}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return generate_alerts(
                params.get("indicator", "gdp"),
                params.get("threshold", 2)
            )
        except Exception as e:
            return f"预警生成失败: {str(e)}"


# ==================== 核心函数 ====================

def generate_correlation_heatmap(indicators: List[str], title: str) -> str:
    """
    生成相关性热力图
    """
    try:
        import akshare as ak

        data_dict = {}
        for ind in indicators:
            try:
                if ind == "gdp":
                    df = ak.macro_china_gdp()
                    if not df.empty:
                        data_dict[ind] = df["国内生产总值-绝对值"].dropna().values
                elif ind == "cpi":
                    df = ak.macro_china_cpi_yearly()
                    if not df.empty:
                        data_dict[ind] = df["今值"].dropna().values
                elif ind == "m2":
                    df = ak.macro_china_m2_yearly()
                    if not df.empty:
                        data_dict[ind] = df["今值"].dropna().values
                elif ind == "pmi":
                    df = ak.macro_china_pmi_yearly()
                    if not df.empty:
                        data_dict[ind] = df["今值"].dropna().values
            except:
                pass

        if len(data_dict) < 2:
            return "数据不足，无法生成热力图"

        min_len = min(len(v) for v in data_dict.values())
        df_corr = pd.DataFrame({k: v[:min_len] for k, v in data_dict.items()})

        corr_matrix = df_corr.corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 12},
            hovertemplate='%{x}<br>%{y}<br>相关系数: %{z:.3f}<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            height=500,
            template="plotly_white"
        )

        return fig.to_html(full_html=False)

    except Exception as e:
        logger.error(f"热力图生成失败: {e}")
        return f"热力图生成失败: {str(e)}"


def generate_radar_chart(dimensions: Dict[str, float], title: str) -> str:
    """
    生成雷达图
    """
    try:
        categories = list(dimensions.keys())
        values = list(dimensions.values())

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(102, 126, 234, 0.3)',
            line=dict(color='rgba(102, 126, 234, 1)', width=2),
            name='经济指标'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title=title,
            height=500,
            template="plotly_white"
        )

        return fig.to_html(full_html=False)

    except Exception as e:
        return f"雷达图生成失败: {str(e)}"


def generate_province_map(indicator: str, title: str) -> str:
    """
    生成省份地图
    """
    try:
        from backend.agents.roles.comparison import PROVINCE_DATA

        province_data = PROVINCE_DATA.get(indicator, {})
        if not province_data:
            return f"暂无 {indicator} 省份数据"

        df = pd.DataFrame([
            {"省份": k, "数值": v} for k, v in province_data.items()
        ])

        fig = px.choropleth(
            df,
            locations="省份",
            locationmode="China",
            color="数值",
            title=title,
            color_continuous_scale="RdYlGn",
            range_color=[0, df["数值"].max()]
        )

        fig.update_layout(
            height=600,
            geo=dict(
                showframe=False,
                showcoastlines=False,
                projection_type='natural earth'
            ),
            template="plotly_white"
        )

        return fig.to_html(full_html=False)

    except Exception as e:
        logger.error(f"地图生成失败: {e}")
        return f"地图生成失败: {str(e)}"


def generate_dashboard(indicators: List[str], title: str) -> str:
    """
    生成综合仪表盘
    """
    try:
        import akshare as ak
        from datetime import datetime

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[ind.upper() for ind in indicators[:4]],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD93D', '#DDA0DD']

        for i, ind in enumerate(indicators[:4]):
            row = i // 2 + 1
            col = i % 2 + 1

            try:
                if ind == "cpi":
                    df = ak.macro_china_cpi_yearly().dropna(subset=['今值']).tail(20)
                    fig.add_trace(go.Scatter(
                        x=df['日期'], y=df['今值'],
                        mode='lines+markers',
                        line=dict(color=colors[i], width=2),
                        fill='tozeroy'
                    ), row=row, col=col)
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=row, col=col)

                elif ind == "ppi":
                    df = ak.macro_china_ppi_yearly().dropna(subset=['今值']).tail(20)
                    fig.add_trace(go.Scatter(
                        x=df['日期'], y=df['今值'],
                        mode='lines+markers',
                        line=dict(color=colors[i], width=2),
                        fill='tozeroy'
                    ), row=row, col=col)
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=row, col=col)

                elif ind == "m2":
                    df = ak.macro_china_m2_yearly().dropna(subset=['今值']).tail(20)
                    fig.add_trace(go.Scatter(
                        x=df['日期'], y=df['今值'],
                        mode='lines+markers',
                        line=dict(color=colors[i], width=2),
                        fill='tozeroy'
                    ), row=row, col=col)

                elif ind == "pmi":
                    df = ak.macro_china_pmi_yearly().dropna(subset=['今值']).tail(20)
                    fig.add_trace(go.Scatter(
                        x=df['日期'], y=df['今值'],
                        mode='lines+markers',
                        line=dict(color=colors[i], width=2),
                        fill='tozeroy'
                    ), row=row, col=col)
                    fig.add_hline(y=50, line_dash="dash", line_color="orange", row=row, col=col)

            except Exception as e:
                logger.error(f"获取{ind}数据失败: {e}")

        fig.update_layout(
            height=700,
            title_text=f"{title}<br><sup>更新时间: {datetime.now().strftime('%Y-%m-%d')}</sup>",
            showlegend=False,
            template="plotly_white"
        )

        return fig.to_html(full_html=False)

    except Exception as e:
        logger.error(f"仪表盘生成失败: {e}")
        return f"仪表盘生成失败: {str(e)}"


def forecast_trend(indicator: str, periods: int = 6, method: str = "linear") -> str:
    """
    趋势预测
    """
    try:
        import akshare as ak
        from scipy import stats

        if indicator == "gdp":
            df = ak.macro_china_gdp()
            data = df["国内生产总值-绝对值"].dropna().values
            dates = df["季度"].dropna().values
        elif indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            data = df["今值"].dropna().values
            dates = df["日期"].dropna().values
        elif indicator == "m2":
            df = ak.macro_china_m2_yearly()
            data = df["今值"].dropna().values
            dates = df["日期"].dropna().values
        else:
            return f"暂不支持 {indicator} 的预测"

        x = np.arange(len(data))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

        future_x = np.arange(len(data), len(data) + periods)
        future_values = slope * future_x + intercept

        results = [
            f"📊 {indicator.upper()} 趋势预测",
            "=" * 60,
            f"\n历史数据点数: {len(data)}",
            f"线性拟合 R²: {r_value**2:.4f}",
            f"趋势斜率: {slope:.4f}",
            f"\n预测结果 (未来 {periods} 期):",
            "-" * 40
        ]

        for i, val in enumerate(future_values, 1):
            results.append(f"  预测点 {i}: {val:,.2f}")

        trend_direction = "📈 上升" if slope > 0 else "📉 下降"
        results.append(f"\n趋势判断: {trend_direction}")
        results.append(f"置信度: {'高' if abs(r_value) > 0.8 else '中' if abs(r_value) > 0.5 else '低'}")

        return "\n".join(results)

    except Exception as e:
        logger.error(f"预测失败: {e}")
        return f"预测失败: {str(e)}"


def generate_alerts(indicator: str, threshold: float = 2) -> str:
    """
    生成数据异常预警
    """
    try:
        import akshare as ak

        if indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            data = df["今值"].dropna().tail(24).values
            name = "CPI"
            warn_high = 3
            warn_low = 0
        elif indicator == "ppi":
            df = ak.macro_china_ppi_yearly()
            data = df["今值"].dropna().tail(24).values
            name = "PPI"
            warn_high = 3
            warn_low = -5
        elif indicator == "pmi":
            df = ak.macro_china_pmi_yearly()
            data = df["今值"].dropna().tail(24).values
            name = "PMI"
            warn_high = 55
            warn_low = 45
        else:
            return f"暂不支持 {indicator} 的预警"

        mean = np.mean(data)
        std = np.std(data)
        latest = data[-1]
        z_score = (latest - mean) / std if std > 0 else 0

        results = [
            f"⚠️  {name} 数据异常预警",
            "=" * 60,
            f"\n指标: {name}",
            f"最新值: {latest:.2f}",
            f"历史均值: {mean:.2f}",
            f"标准差: {std:.2f}",
            f"Z-Score: {z_score:.2f}",
        ]

        alerts = []

        if abs(z_score) > threshold:
            alerts.append(f"🔴 【严重预警】Z-score = {z_score:.2f}，超过阈值 {threshold}")

        if indicator in ["cpi", "ppi"] and latest < warn_low:
            alerts.append(f"🟠 【通缩预警】{name} = {latest}% 低于{warn_low}%，存在通缩风险")
        elif indicator in ["cpi", "ppi"] and latest > warn_high:
            alerts.append(f"🟠 【通胀预警】{name} = {latest}% 高于{warn_high}%，通胀压力上升")

        if indicator == "pmi" and latest < warn_low:
            alerts.append(f"🟠 【制造业预警】PMI = {latest} 低于{warn_low}，制造业收缩")
        elif indicator == "pmi" and latest > warn_high:
            alerts.append(f"🟢 【景气预警】PMI = {latest} 高于{warn_high}，制造业活跃")

        if alerts:
            results.append("\n" + "=" * 60)
            results.append("📢 预警信息:")
            results.append("-" * 40)
            results.extend(alerts)
        else:
            results.append("\n✅ 无异常预警，数据运行正常")

        results.append("\n" + "=" * 60)
        results.append("💡 建议: 持续关注指标变化，结合多维度数据综合判断")

        return "\n".join(results)

    except Exception as e:
        logger.error(f"预警生成失败: {e}")
        return f"预警生成失败: {str(e)}"


class EnhancedVisualizationAgent:
    """增强可视化 Agent"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [
            HeatmapTool(),
            RadarChartTool(),
            ProvinceMapTool(),
            DashboardGeneratorTool(),
            TrendForecastTool(),
            AnomalyAlertTool(),
        ]

    def create_agent(self) -> Agent:
        """创建增强可视化 Agent"""
        return Agent(
            role="增强可视化专家",
            goal="生成丰富的可视化图表，帮助用户直观理解经济数据",
            backstory="""
            你是一位专业的数据可视化专家，擅长将复杂的经济数据转化为直观的图表。
            你精通各种可视化技术：
            - 热力图：展示指标间的相关性
            - 雷达图：多维度综合评价
            - 地图可视化：地理分布展示
            - 综合仪表盘：一目了然的指标监控
            - 趋势预测：基于历史的未来预测
            - 预警系统：异常数据的自动告警

            你的目标是让数据说话，让决策更简单。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )
