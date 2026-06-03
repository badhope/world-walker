"""
时间序列预测模块 - 使用Prophet
用于预测GDP、CPI等宏观经济指标
"""

import logging
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

# 尝试导入prophet，如果没有则fallback到简单方法
try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available, using simple forecasting methods")

from backend.data.city_data import get_all_cities, get_historical_data

logger = logging.getLogger(__name__)


class EconomicForecaster:
    """
    经济指标预测器
    支持：
    1. Prophet时间序列预测（推荐）
    2. 简单线性回归预测（fallback）
    3. 移动平均预测（fallback）
    """

    def __init__(self):
        self.model_cache = {}  # 缓存已训练模型

    def forecast_gdp(
        self,
        city: str,
        forecast_years: int = 5,
        method: str = "auto",
    ) -> dict[str, Any]:
        """
        预测指定城市的GDP

        参数:
            city: 城市名称
            forecast_years: 预测年份数
            method: 预测方法 ('prophet', 'linear', 'auto')

        返回:
            预测结果字典
        """
        logger.info(f"Forecasting GDP for {city}, method={method}")

        # 获取历史数据
        historical_data = get_historical_data(city)
        if historical_data.empty or "gdp" not in historical_data.columns:
            return {"error": f"No GDP data available for {city}"}

        # 准备预测数据
        df = historical_data[["year", "gdp"]].copy()
        df["ds"] = pd.to_datetime(df["year"], format="%Y")
        df["y"] = df["gdp"]

        # 选择预测方法
        if method == "auto":
            method = "prophet" if PROPHET_AVAILABLE else "linear"

        # 执行预测
        if method == "prophet" and PROPHET_AVAILABLE:
            forecast_result = self._forecast_prophet(df, forecast_years)
        elif method == "linear":
            forecast_result = self._forecast_linear(df, forecast_years)
        else:
            return {"error": f"Unknown method: {method}"}

        # 计算增长率
        growth_rates = self._calculate_growth_rates(forecast_result)

        return {
            "city": city,
            "indicator": "GDP",
            "forecast_method": method,
            "historical_data": df[["year", "gdp"]].to_dict(orient="records"),
            "forecast_data": forecast_result["forecast_data"],
            "growth_rates": growth_rates,
            "model_metrics": forecast_result.get("metrics", {}),
        }

    def forecast_multiple_cities(
        self,
        cities: list[str],
        forecast_years: int = 5,
    ) -> dict[str, Any]:
        """批量预测多个城市"""
        results = {}
        for city in cities:
            try:
                results[city] = self.forecast_gdp(city, forecast_years)
            except Exception as e:
                logger.warning(f"Failed to forecast {city}: {e}")
                results[city] = {"error": str(e)}

        # 生成对比分析
        comparison = self._generate_forecast_comparison(results)

        return {
            "city_forecasts": results,
            "comparison": comparison,
            "forecast_period": forecast_years,
        }

    def _forecast_prophet(
        self,
        df: pd.DataFrame,
        forecast_years: int,
    ) -> dict[str, Any]:
        """使用Prophet进行预测"""
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="additive",
            changepoint_prior_scale=0.05,
        )
        model.fit(df[["ds", "y"]])

        # 创建未来日期
        last_year = df["year"].max()
        future_years = pd.date_range(
            start=f"{last_year + 1}-01-01",
            periods=forecast_years,
            freq="YS",
        )
        future = pd.DataFrame({"ds": future_years})

        # 预测
        forecast = model.predict(future)

        # 准备结果
        forecast_data = []
        for i in range(forecast_years):
            forecast_data.append(
                {
                    "year": last_year + 1 + i,
                    "gdp": forecast["yhat"].iloc[i],
                    "gdp_lower": forecast["yhat_lower"].iloc[i],
                    "gdp_upper": forecast["yhat_upper"].iloc[i],
                }
            )

        # 计算拟合指标（用历史数据）
        historical_pred = model.predict(df[["ds"]])
        mae = np.mean(np.abs(historical_pred["yhat"] - df["y"]))
        mape = np.mean(np.abs((historical_pred["yhat"] - df["y"]) / df["y"])) * 100

        return {
            "forecast_data": forecast_data,
            "metrics": {
                "model": "Prophet",
                "mae": mae,
                "mape": mape,
                "r_squared": 1
                - (np.sum((df["y"] - historical_pred["yhat"]) ** 2) / np.sum((df["y"] - df["y"].mean()) ** 2)),
            },
        }

    def _forecast_linear(
        self,
        df: pd.DataFrame,
        forecast_years: int,
    ) -> dict[str, Any]:
        """使用简单线性回归进行预测"""
        # 拟合线性模型
        x = df["year"].values
        y = df["gdp"].values

        # 计算斜率和截距
        slope, intercept = np.polyfit(x, y, 1)

        # 计算历史拟合值
        y_pred = intercept + slope * x

        # 预测未来
        last_year = df["year"].max()
        forecast_data = []
        for i in range(forecast_years):
            future_year = last_year + 1 + i
            future_gdp = intercept + slope * future_year
            forecast_data.append(
                {
                    "year": future_year,
                    "gdp": future_gdp,
                    "gdp_lower": future_gdp * 0.9,  # 假设±10%置信区间
                    "gdp_upper": future_gdp * 1.1,
                }
            )

        # 计算拟合指标
        mae = np.mean(np.abs(y_pred - y))
        mape = np.mean(np.abs((y_pred - y) / y)) * 100

        return {
            "forecast_data": forecast_data,
            "metrics": {
                "model": "Linear Regression",
                "slope": slope,
                "intercept": intercept,
                "mae": mae,
                "mape": mape,
                "r_squared": 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2)),
            },
        }

    def _calculate_growth_rates(self, forecast_result: dict) -> dict:
        """计算增长率"""
        forecast_data = forecast_result["forecast_data"]
        historical_data = forecast_result.get("historical_data", [])

        growth_rates = {}

        # 历史年均增长率
        if len(historical_data) >= 2:
            first_val = historical_data[0]["gdp"]
            last_val = historical_data[-1]["gdp"]
            years = historical_data[-1]["year"] - historical_data[0]["year"]
            if first_val > 0 and years > 0:
                cagr = ((last_val / first_val) ** (1 / years) - 1) * 100
                growth_rates["historical_cagr"] = cagr

        # 预测年均增长率
        if len(forecast_data) >= 2:
            first_val = forecast_data[0]["gdp"]
            last_val = forecast_data[-1]["gdp"]
            years = forecast_data[-1]["year"] - forecast_data[0]["year"] + 1
            if first_val > 0 and years > 0:
                forecast_cagr = ((last_val / first_val) ** (1 / years) - 1) * 100
                growth_rates["forecast_cagr"] = forecast_cagr

        return growth_rates

    def _generate_forecast_comparison(self, forecasts: dict) -> dict:
        """生成多城市预测对比"""
        comparison_data = []

        for city, result in forecasts.items():
            if "error" in result:
                continue

            forecast_data = result.get("forecast_data", [])
            growth_rates = result.get("growth_rates", {})

            if forecast_data:
                last_forecast = forecast_data[-1]
                comparison_data.append(
                    {
                        "城市": city,
                        "预测年份": last_forecast["year"],
                        "预测GDP": last_forecast["gdp"],
                        "历史年均增速": growth_rates.get("historical_cagr", 0),
                        "预测年均增速": growth_rates.get("forecast_cagr", 0),
                    }
                )

        # 按预测GDP排序
        comparison_data.sort(key=lambda x: x["预测GDP"], reverse=True)

        return {
            "comparison_table": comparison_data,
            "summary": {
                "total_cities": len(comparison_data),
                "top_city": comparison_data[0]["城市"] if comparison_data else None,
            },
        }


def run_forecast_comparison_report() -> dict[str, Any]:
    """
    运行多城市预测对比分析报告
    展示Prophet时间序列预测的真实能力
    """
    logger.info("Running forecast comparison report...")

    forecaster = EconomicForecaster()
    cities = get_all_cities()

    # 预测所有城市
    forecast_results = forecaster.forecast_multiple_cities(cities, forecast_years=5)

    # 生成分析洞察
    insights = _generate_forecast_insights(forecast_results)

    return {
        "report_title": "主要城市GDP预测对比分析报告",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "forecast_results": forecast_results,
        "insights": insights,
        "methodology": {
            "primary_method": "Prophet" if PROPHET_AVAILABLE else "Linear Regression",
            "prophet_available": PROPHET_AVAILABLE,
            "forecast_period": "5年（2026-2030）",
        },
    }


def _generate_forecast_insights(forecast_results: dict) -> list[dict]:
    """基于预测结果生成洞察"""
    insights = []
    comparison = forecast_results.get("comparison", {})
    table = comparison.get("comparison_table", [])

    if not table:
        return insights

    # 找出增速最高的城市
    table_sorted_by_growth = sorted(table, key=lambda x: x["预测年均增速"], reverse=True)
    fastest_growth = table_sorted_by_growth[0]

    insights.append(
        {
            "type": "positive",
            "title": "增长最快城市",
            "content": f"{fastest_growth['城市']}预测年均增速{fastest_growth['预测年均增速']:.2f}%，在主要城市中增长最快",
            "related_city": fastest_growth["城市"],
        }
    )

    # 对比历史和预测增速
    for row in table:
        hist_growth = row.get("历史年均增速", 0)
        forecast_growth = row.get("预测年均增速", 0)

        if forecast_growth > hist_growth * 1.1:  # 预测增速高于历史10%
            insights.append(
                {
                    "type": "positive",
                    "title": f"{row['城市']}增长加速",
                    "content": f"预测年均增速{forecast_growth:.2f}%，较历史增速{hist_growth:.2f}%有所提升",
                    "related_city": row["城市"],
                }
            )
        elif forecast_growth < hist_growth * 0.9:  # 预测增速低于历史10%
            insights.append(
                {
                    "type": "warning",
                    "title": f"{row['城市']}增长放缓",
                    "content": f"预测年均增速{forecast_growth:.2f}%，较历史增速{hist_growth:.2f}%有所放缓",
                    "related_city": row["城市"],
                }
            )

    return insights


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_forecast_comparison_report()
    print(f"预测报告生成完成！分析了{len(result['forecast_results']['city_forecasts'])}个城市")
