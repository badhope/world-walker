"""
可视化工具模块
"""

import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from config import config_loader

logger = logging.getLogger(__name__)


class Visualizer:
    """可视化器"""

    def __init__(self, theme: str | None = None, color_palette: list[str] | None = None):
        # 从配置获取默认值
        self.analysis_config = config_loader.get_analysis_config()
        self.visualization_config = self.analysis_config.VISUALIZATION

        self.theme = theme or self.visualization_config["theme"]
        self.color_palette = color_palette or self.visualization_config["color_palette"]

    def time_series_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "",
        show_trend: bool = True,
        show_ma: bool = True,
        ma_window: int = 12,
    ) -> go.Figure:
        """时间序列图（带趋势线和移动平均）"""
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[y],
                mode="lines+markers",
                name="原始数据",
                line=dict(color=self.color_palette[0], width=2),
                marker=dict(size=4),
            )
        )

        if show_ma and len(df) >= ma_window:
            ma = df[y].rolling(window=ma_window, center=True).mean()
            fig.add_trace(
                go.Scatter(
                    x=df[x],
                    y=ma,
                    mode="lines",
                    name=f"{ma_window}期移动平均",
                    line=dict(color=self.color_palette[1], width=2, dash="dash"),
                )
            )

        if show_trend and len(df) > 1:
            x_numeric = pd.to_numeric(df[x], errors="coerce")
            mask = ~x_numeric.isna() & ~df[y].isna()
            if mask.sum() > 1:
                slope, intercept, r, p, se = stats.linregress(x_numeric[mask], df.loc[mask, y])
                trend = slope * x_numeric + intercept
                fig.add_trace(
                    go.Scatter(
                        x=df[x],
                        y=trend,
                        mode="lines",
                        name=f"趋势线 (R²={r**2:.3f})",
                        line=dict(color=self.color_palette[2], width=2, dash="dot"),
                    )
                )

        fig.update_layout(
            title=title,
            template=self.theme,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        return fig

    def correlation_heatmap(
        self, df: pd.DataFrame, columns: list[str] | None = None, method: str = "pearson", title: str = "相关性热力图"
    ) -> go.Figure:
        """相关性热力图"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        corr_matrix = df[columns].corr(method=method)

        fig = px.imshow(
            corr_matrix,
            labels=dict(x="指标", y="指标", color="相关系数"),
            x=corr_matrix.columns,
            y=corr_matrix.index,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title=title,
        )

        fig.update_layout(template=self.theme)

        for i, row in enumerate(corr_matrix.index):
            for j, col in enumerate(corr_matrix.columns):
                fig.add_annotation(
                    x=j, y=i, text=f"{corr_matrix.loc[row, col]:.2f}", showarrow=False, font=dict(size=10)
                )

        return fig

    def distribution_plot(
        self, df: pd.DataFrame, column: str, bins: int = 30, show_kde: bool = True, title: str = ""
    ) -> go.Figure:
        """分布图（直方图 + KDE）"""
        fig = go.Figure()

        data = df[column].dropna()

        fig.add_trace(
            go.Histogram(
                x=data,
                nbinsx=bins,
                name="频数",
                marker=dict(color=self.color_palette[0], opacity=0.7),
                histnorm="probability density" if show_kde else "",
            )
        )

        if show_kde:
            kde = stats.gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 200)
            fig.add_trace(
                go.Scatter(
                    x=x_range, y=kde(x_range), mode="lines", name="KDE", line=dict(color=self.color_palette[1], width=2)
                )
            )

        fig.update_layout(title=title or f"{column} 分布", template=self.theme, barmode="overlay")

        return fig

    def comparison_bar(
        self, df: pd.DataFrame, x: str, y: str, color: str | None = None, barmode: str = "group", title: str = ""
    ) -> go.Figure:
        """比较柱状图"""
        fig = px.bar(
            df, x=x, y=y, color=color, barmode=barmode, title=title, color_discrete_sequence=self.color_palette
        )

        fig.update_layout(template=self.theme)

        return fig

    def radar_chart(
        self, df: pd.DataFrame, categories: str, values: str, group: str | None = None, title: str = "雷达图"
    ) -> go.Figure:
        """雷达图"""
        fig = go.Figure()

        if group:
            for i, g in enumerate(df[group].unique()):
                subset = df[df[group] == g]
                fig.add_trace(
                    go.Scatterpolar(
                        r=subset[values],
                        theta=subset[categories],
                        fill="toself",
                        name=str(g),
                        line=dict(color=self.color_palette[i % len(self.color_palette)]),
                    )
                )
        else:
            fig.add_trace(
                go.Scatterpolar(
                    r=df[values],
                    theta=df[categories],
                    fill="toself",
                    name="数据",
                    line=dict(color=self.color_palette[0]),
                )
            )

        fig.update_layout(title=title, template=self.theme, polar=dict(radialaxis=dict(visible=True)))

        return fig

    def dashboard(self, df: pd.DataFrame, metrics: dict[str, str], time_col: str) -> go.Figure:
        """综合仪表盘"""
        n_metrics = len(metrics)
        fig = make_subplots(rows=n_metrics, cols=1, subplot_titles=list(metrics.keys()), vertical_spacing=0.05)

        for i, (name, col) in enumerate(metrics.items(), 1):
            fig.add_trace(
                go.Scatter(
                    x=df[time_col],
                    y=df[col],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=self.color_palette[(i - 1) % len(self.color_palette)]),
                ),
                row=i,
                col=1,
            )

        fig.update_layout(title="经济指标仪表盘", template=self.theme, height=200 * n_metrics, showlegend=False)

        return fig


visualizer = Visualizer()
