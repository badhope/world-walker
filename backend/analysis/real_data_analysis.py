"""
真实数据分析模块 - 使用真实经济数据进行探索性分析
"""

from typing import Any

import numpy as np
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None
import logging

logger = logging.getLogger(__name__)


class RealDataAnalyzer:
    """真实数据分析器"""

    def __init__(self):
        self.data_cache = {}

    def fetch_macro_data(self) -> pd.DataFrame:
        """获取真实宏观经济数据"""
        try:
            # 获取中国GDP数据
            logger.info("正在获取GDP数据...")
            gdp_df = ak.macro_china_gdp()

            # 获取CPI数据
            logger.info("正在获取CPI数据...")
            cpi_df = ak.macro_china_cpi_yearly()

            # 获取PMI数据
            logger.info("正在获取PMI数据...")
            pmi_df = ak.macro_china_pmi_yearly()

            # 处理并合并数据
            processed_data = self._process_and_merge_data(gdp_df, cpi_df, pmi_df)

            self.data_cache["macro"] = processed_data
            logger.info(f"数据获取完成，共 {len(processed_data)} 条记录")

            return processed_data

        except Exception as e:
            logger.error(f"获取宏观数据失败: {e}")
            raise

    def _process_and_merge_data(self, gdp_df: pd.DataFrame, cpi_df: pd.DataFrame, pmi_df: pd.DataFrame) -> pd.DataFrame:
        """处理并合并数据"""

        # 处理GDP数据
        gdp_processed = self._process_gdp(gdp_df)

        # 处理CPI数据
        cpi_processed = self._process_cpi(cpi_df)

        # 处理PMI数据
        pmi_processed = self._process_pmi(pmi_df)

        # 合并数据
        merged = pd.merge(gdp_processed, cpi_processed, on="year", how="outer")
        merged = pd.merge(merged, pmi_processed, on="year", how="outer")

        # 按年份排序
        merged = merged.sort_values("year").reset_index(drop=True)

        return merged

    def _process_gdp(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理GDP数据"""
        processed = []

        for _, row in df.iterrows():
            try:
                quarter_str = str(row["季度"])
                # 解析年份和季度
                if "年" in quarter_str and "季度" in quarter_str:
                    year = int(quarter_str.split("年")[0])
                    # 只取年度数据（第四季度或全年）
                    if "4" in quarter_str or "1-4" in quarter_str:
                        processed.append(
                            {
                                "year": year,
                                "gdp": float(row["国内生产总值-绝对值"])
                                if pd.notna(row["国内生产总值-绝对值"])
                                else None,
                                "gdp_primary": float(row["第一产业-绝对值"])
                                if pd.notna(row["第一产业-绝对值"])
                                else None,
                                "gdp_secondary": float(row["第二产业-绝对值"])
                                if pd.notna(row["第二产业-绝对值"])
                                else None,
                                "gdp_tertiary": float(row["第三产业-绝对值"])
                                if pd.notna(row["第三产业-绝对值"])
                                else None,
                            }
                        )
            except Exception:
                continue

        return pd.DataFrame(processed).drop_duplicates(subset=["year"], keep="last")

    def _process_cpi(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理CPI数据"""
        processed = []

        for _, row in df.iterrows():
            try:
                date_str = str(row["日期"])
                date = pd.to_datetime(date_str)
                # 只取每年12月的数据作为年度数据
                if date.month == 12:
                    processed.append(
                        {
                            "year": date.year,
                            "cpi_yoy": float(row["今值"]) if pd.notna(row["今值"]) else None,
                        }
                    )
            except Exception:
                continue

        return pd.DataFrame(processed).drop_duplicates(subset=["year"], keep="last")

    def _process_pmi(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理PMI数据"""
        processed = []

        for _, row in df.iterrows():
            try:
                date_str = str(row["日期"])
                date = pd.to_datetime(date_str)
                # 只取每年12月的数据
                if date.month == 12:
                    processed.append(
                        {
                            "year": date.year,
                            "pmi_manufacturing": float(row["制造业-指数"])
                            if "制造业-指数" in df.columns and pd.notna(row["制造业-指数"])
                            else None,
                        }
                    )
            except Exception:
                continue

        return pd.DataFrame(processed).drop_duplicates(subset=["year"], keep="last")

    def perform_eda(self, df: pd.DataFrame) -> dict[str, Any]:
        """执行探索性数据分析"""

        eda_results = {
            "summary_stats": df.describe().to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "correlation_matrix": self._calculate_correlations(df),
            "trend_analysis": self._analyze_trends(df),
            "data_period": {
                "start_year": int(df["year"].min()),
                "end_year": int(df["year"].max()),
                "total_years": len(df),
            },
        }

        return eda_results

    def _calculate_correlations(self, df: pd.DataFrame) -> dict[str, dict[str, float]]:
        """计算相关系数矩阵"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.drop("year", errors="ignore")
        corr_matrix = df[numeric_cols].corr()

        return corr_matrix.to_dict()

    def _analyze_trends(self, df: pd.DataFrame) -> dict[str, Any]:
        """分析趋势"""
        trends = {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.drop("year", errors="ignore")

        for col in numeric_cols:
            if len(df) >= 2:
                # 计算年均增长率
                valid_data = df[[col, "year"]].dropna()
                if len(valid_data) >= 2:
                    first_val = valid_data.iloc[0][col]
                    last_val = valid_data.iloc[-1][col]
                    years = valid_data.iloc[-1]["year"] - valid_data.iloc[0]["year"]

                    if first_val > 0 and years > 0:
                        cagr = ((last_val / first_val) ** (1 / years) - 1) * 100
                    else:
                        cagr = None

                    # 计算总体趋势方向
                    if len(valid_data) >= 2:
                        x = np.arange(len(valid_data))
                        y = valid_data[col].values
                        slope = np.polyfit(x, y, 1)[0]
                        trend_direction = "up" if slope > 0 else "down" if slope < 0 else "flat"
                    else:
                        trend_direction = "insufficient_data"

                    trends[col] = {
                        "cagr": cagr,
                        "trend_direction": trend_direction,
                        "slope": float(slope) if "slope" in locals() else None,
                        "latest_value": float(last_val) if pd.notna(last_val) else None,
                        "earliest_value": float(first_val) if pd.notna(first_val) else None,
                    }

        return trends

    def generate_insights(self, eda_results: dict[str, Any]) -> list[dict[str, Any]]:
        """生成数据洞察"""
        insights = []

        # 基于趋势分析生成洞察
        trends = eda_results.get("trend_analysis", {})

        if "gdp" in trends:
            gdp_trend = trends["gdp"]
            if gdp_trend.get("trend_direction") == "up":
                insights.append(
                    {
                        "type": "positive",
                        "title": "GDP持续增长",
                        "content": f"GDP呈现上升趋势，年均增长率为 {gdp_trend.get('cagr', 0):.2f}%",
                        "indicator": "gdp",
                    }
                )
            else:
                insights.append(
                    {
                        "type": "warning",
                        "title": "GDP增长放缓",
                        "content": "GDP增长呈现下行趋势，需关注经济发展动力",
                        "indicator": "gdp",
                    }
                )

        if "cpi_yoy" in trends:
            cpi_trend = trends["cpi_yoy"]
            latest_cpi = cpi_trend.get("latest_value", 0)
            if latest_cpi > 5:
                insights.append(
                    {
                        "type": "warning",
                        "title": "通胀压力较大",
                        "content": f"最新CPI同比增长 {latest_cpi:.2f}%，高于3%的温和通胀水平",
                        "indicator": "cpi_yoy",
                    }
                )
            elif latest_cpi < 1:
                insights.append(
                    {
                        "type": "warning",
                        "title": "通缩风险",
                        "content": f"最新CPI同比增长 {latest_cpi:.2f}%，低于1%，需关注通缩风险",
                        "indicator": "cpi_yoy",
                    }
                )

        if "pmi_manufacturing" in trends:
            pmi_trend = trends["pmi_manufacturing"]
            latest_pmi = pmi_trend.get("latest_value", 50)
            if latest_pmi >= 50:
                insights.append(
                    {
                        "type": "positive",
                        "title": "制造业景气",
                        "content": f"最新制造业PMI为 {latest_pmi:.2f}，位于荣枯线以上，制造业扩张",
                        "indicator": "pmi_manufacturing",
                    }
                )
            else:
                insights.append(
                    {
                        "type": "negative",
                        "title": "制造业收缩",
                        "content": f"最新制造业PMI为 {latest_pmi:.2f}，位于荣枯线以下，制造业收缩",
                        "indicator": "pmi_manufacturing",
                    }
                )

        # 基于相关性分析生成洞察
        corr_matrix = eda_results.get("correlation_matrix", {})
        if "gdp" in corr_matrix and "cpi_yoy" in corr_matrix["gdp"]:
            gdp_cpi_corr = corr_matrix["gdp"]["cpi_yoy"]
            if abs(gdp_cpi_corr) > 0.7:
                insights.append(
                    {
                        "type": "info",
                        "title": "GDP与CPI强相关",
                        "content": f"GDP与CPI的相关系数为 {gdp_cpi_corr:.2f}，呈现强{'正' if gdp_cpi_corr > 0 else '负'}相关关系",
                        "indicator": "correlation",
                    }
                )

        return insights

    def get_visualization_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """获取可视化数据"""

        viz_data = {
            "gdp_trend": self._prepare_gdp_chart_data(df),
            "cpi_trend": self._prepare_cpi_chart_data(df),
            "pmi_trend": self._prepare_pmi_chart_data(df),
            "industry_structure": self._prepare_industry_structure_data(df),
        }

        return viz_data

    def _prepare_gdp_chart_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """准备GDP趋势图数据"""
        valid_data = df[["year", "gdp", "gdp_primary", "gdp_secondary", "gdp_tertiary"]].dropna()

        return {
            "years": valid_data["year"].tolist(),
            "total_gdp": valid_data["gdp"].tolist(),
            "primary": valid_data["gdp_primary"].tolist(),
            "secondary": valid_data["gdp_secondary"].tolist(),
            "tertiary": valid_data["gdp_tertiary"].tolist(),
        }

    def _prepare_cpi_chart_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """准备CPI趋势图数据"""
        valid_data = df[["year", "cpi_yoy"]].dropna()

        return {"years": valid_data["year"].tolist(), "cpi_yoy": valid_data["cpi_yoy"].tolist()}

    def _prepare_pmi_chart_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """准备PMI趋势图数据"""
        valid_data = df[["year", "pmi_manufacturing"]].dropna()

        return {"years": valid_data["year"].tolist(), "pmi": valid_data["pmi_manufacturing"].tolist()}

    def _prepare_industry_structure_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """准备产业结构数据"""
        latest_data = (
            df.dropna(subset=["gdp_primary", "gdp_secondary", "gdp_tertiary"]).iloc[-1] if len(df) > 0 else None
        )

        if latest_data is not None:
            total = latest_data["gdp_primary"] + latest_data["gdp_secondary"] + latest_data["gdp_tertiary"]
            return {
                "year": int(latest_data["year"]),
                "primary": float(latest_data["gdp_primary"] / total * 100),
                "secondary": float(latest_data["gdp_secondary"] / total * 100),
                "tertiary": float(latest_data["gdp_tertiary"] / total * 100),
            }

        return {}


# 单例
real_data_analyzer = RealDataAnalyzer()
