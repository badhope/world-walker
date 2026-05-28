"""
高级可视化模块 - 时间序列分解、相关性分析、区域对比
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class Visualizer:
    """高级可视化器"""
    
    def __init__(self, theme: str = "plotly_white"):
        self.theme = theme
        self.color_palette = [
            "#667eea", "#764ba2", "#f093fb", "#f5576c",
            "#4facfe", "#00f2fe", "#43e97b", "#38f9d7",
            "#fa709a", "#fee140"
        ]
    
    # ==================== 时间序列分析 ====================
    
    def time_series_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "",
        show_trend: bool = True,
        show_ma: bool = True,
        ma_window: int = 12
    ) -> go.Figure:
        """时间序列图（带趋势线和移动平均）"""
        fig = go.Figure()
        
        # 原始数据
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y],
            mode='lines+markers',
            name='原始数据',
            line=dict(color=self.color_palette[0], width=2),
            marker=dict(size=4)
        ))
        
        # 移动平均
        if show_ma and len(df) >= ma_window:
            ma = df[y].rolling(window=ma_window, center=True).mean()
            fig.add_trace(go.Scatter(
                x=df[x], y=ma,
                mode='lines',
                name=f'{ma_window}期移动平均',
                line=dict(color=self.color_palette[1], width=2, dash='dash')
            ))
        
        # 趋势线
        if show_trend and len(df) > 1:
            x_numeric = pd.to_numeric(df[x], errors='coerce')
            mask = ~x_numeric.isna() & ~df[y].isna()
            if mask.sum() > 1:
                slope, intercept, r, p, se = stats.linregress(
                    x_numeric[mask], df.loc[mask, y]
                )
                trend = slope * x_numeric + intercept
                fig.add_trace(go.Scatter(
                    x=df[x], y=trend,
                    mode='lines',
                    name=f'趋势线 (R²={r**2:.3f})',
                    line=dict(color=self.color_palette[2], width=2, dash='dot')
                ))
        
        fig.update_layout(
            title=title,
            template=self.theme,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    def seasonal_decomposition_plot(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        period: int = 12,
        title: str = "时间序列分解"
    ) -> go.Figure:
        """季节分解图（趋势、季节、残差）"""
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # 准备数据
        ts = df.set_index(date_col)[value_col]
        ts = ts.dropna()
        
        if len(ts) < 2 * period:
            raise ValueError(f"数据长度 {len(ts)} 不足以进行周期为 {period} 的分解")
        
        # 季节分解
        result = seasonal_decompose(ts, period=period, model='additive')
        
        # 创建子图
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=['原始数据', '趋势', '季节', '残差'],
            vertical_spacing=0.05
        )
        
        # 原始数据
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts.values,
            mode='lines', name='原始',
            line=dict(color=self.color_palette[0])
        ), row=1, col=1)
        
        # 趋势
        fig.add_trace(go.Scatter(
            x=ts.index, y=result.trend.values,
            mode='lines', name='趋势',
            line=dict(color=self.color_palette[1])
        ), row=2, col=1)
        
        # 季节
        fig.add_trace(go.Scatter(
            x=ts.index, y=result.seasonal.values,
            mode='lines', name='季节',
            line=dict(color=self.color_palette[2])
        ), row=3, col=1)
        
        # 残差
        fig.add_trace(go.Scatter(
            x=ts.index, y=result.resid.values,
            mode='lines', name='残差',
            line=dict(color=self.color_palette[3])
        ), row=4, col=1)
        
        fig.update_layout(
            title=title,
            template=self.theme,
            height=800,
            showlegend=False
        )
        
        return fig
    
    # ==================== 相关性分析 ====================
    
    def correlation_heatmap(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "pearson",
        title: str = "相关性热力图"
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
            zmin=-1, zmax=1,
            title=title
        )
        
        fig.update_layout(template=self.theme)
        
        # 添加数值标注
        for i, row in enumerate(corr_matrix.index):
            for j, col in enumerate(corr_matrix.columns):
                fig.add_annotation(
                    x=j, y=i,
                    text=f"{corr_matrix.loc[row, col]:.2f}",
                    showarrow=False,
                    font=dict(size=10)
                )
        
        return fig
    
    def scatter_matrix(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        color_col: Optional[str] = None,
        title: str = "散点矩阵"
    ) -> go.Figure:
        """散点矩阵图"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()[:5]
        
        fig = px.scatter_matrix(
            df,
            dimensions=columns,
            color=color_col,
            title=title,
            color_continuous_scale=px.colors.diverging.Tealrose
        )
        
        fig.update_layout(template=self.theme)
        fig.update_traces(diagonal_visible=False)
        
        return fig
    
    # ==================== 分布分析 ====================
    
    def distribution_plot(
        self,
        df: pd.DataFrame,
        column: str,
        bins: int = 30,
        show_kde: bool = True,
        title: str = ""
    ) -> go.Figure:
        """分布图（直方图 + KDE）"""
        fig = go.Figure()
        
        data = df[column].dropna()
        
        # 直方图
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=bins,
            name='频数',
            marker=dict(color=self.color_palette[0], opacity=0.7),
            histnorm='probability density' if show_kde else ''
        ))
        
        # KDE
        if show_kde:
            kde = stats.gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 200)
            fig.add_trace(go.Scatter(
                x=x_range, y=kde(x_range),
                mode='lines',
                name='KDE',
                line=dict(color=self.color_palette[1], width=2)
            ))
        
        fig.update_layout(
            title=title or f'{column} 分布',
            template=self.theme,
            barmode='overlay'
        )
        
        return fig
    
    def box_plot(
        self,
        df: pd.DataFrame,
        y_col: str,
        x_col: Optional[str] = None,
        title: str = ""
    ) -> go.Figure:
        """箱线图"""
        fig = px.box(
            df,
            x=x_col, y=y_col,
            title=title or f'{y_col} 箱线图',
            color=x_col,
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(template=self.theme)
        
        return fig
    
    # ==================== 比较分析 ====================
    
    def comparison_bar(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = None,
        barmode: str = "group",
        title: str = ""
    ) -> go.Figure:
        """比较柱状图"""
        fig = px.bar(
            df,
            x=x, y=y,
            color=color,
            barmode=barmode,
            title=title,
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(template=self.theme)
        
        return fig
    
    def radar_chart(
        self,
        df: pd.DataFrame,
        categories: str,
        values: str,
        group: Optional[str] = None,
        title: str = "雷达图"
    ) -> go.Figure:
        """雷达图"""
        fig = go.Figure()
        
        if group:
            for i, g in enumerate(df[group].unique()):
                subset = df[df[group] == g]
                fig.add_trace(go.Scatterpolar(
                    r=subset[values],
                    theta=subset[categories],
                    fill='toself',
                    name=str(g),
                    line=dict(color=self.color_palette[i % len(self.color_palette)])
                ))
        else:
            fig.add_trace(go.Scatterpolar(
                r=df[values],
                theta=df[categories],
                fill='toself',
                name='数据',
                line=dict(color=self.color_palette[0])
            ))
        
        fig.update_layout(
            title=title,
            template=self.theme,
            polar=dict(radialaxis=dict(visible=True))
        )
        
        return fig
    
    # ==================== 综合仪表盘 ====================
    
    def dashboard(
        self,
        df: pd.DataFrame,
        metrics: Dict[str, str],
        time_col: str
    ) -> go.Figure:
        """
        综合仪表盘
        
        Args:
            df: 数据框
            metrics: {指标名: 列名} 字典
            time_col: 时间列
        """
        n_metrics = len(metrics)
        fig = make_subplots(
            rows=n_metrics, cols=1,
            subplot_titles=list(metrics.keys()),
            vertical_spacing=0.05
        )
        
        for i, (name, col) in enumerate(metrics.items(), 1):
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[col],
                mode='lines+markers',
                name=name,
                line=dict(color=self.color_palette[(i - 1) % len(self.color_palette)])
            ), row=i, col=1)
        
        fig.update_layout(
            title="经济指标仪表盘",
            template=self.theme,
            height=200 * n_metrics,
            showlegend=False
        )
        
        return fig


# 单例
visualizer = Visualizer()
