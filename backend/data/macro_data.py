"""
宏观协变量数据 (NBSC 公开数据) — 2010-2025。

包含 4 个核心协变量 + 衍生指标:
- national_gdp: 全国实际 GDP (亿元)
- cpi_yoy: 同比 CPI (%)
- lpr_1y: 1 年期 LPR 贷款利率 (年末, %)
- fdi_inflow: 实际利用外资 (亿美元)

来源:
- NBSC 年度国民经济和社会发展统计公报
  http://www.stats.gov.cn/sj/ndsj/
- 中国人民银行 LPR 公告
  http://www.pbc.gov.cn/

注意:
- 2024-2025 部分指标为预测/估算值
- LPR 改革从 2019 年 8 月开始,之前用贷款基准利率
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

NBSC_URL = "http://www.stats.gov.cn/sj/ndsj/"
PBOC_URL = "http://www.pbc.gov.cn/zhengwugongkai/4081330/4081344/4081395/4081686/index.html"


# --------------------------------------------------------------------------- #
# 2010-2025 宏观数据
# --------------------------------------------------------------------------- #

MACRO_HISTORICAL: dict[int, dict[str, Any]] = {
    2010: {"national_gdp": 413582, "cpi_yoy": 3.3, "lpr_1y": 5.81, "fdi_inflow": 1088},
    2011: {"national_gdp": 484124, "cpi_yoy": 5.4, "lpr_1y": 6.56, "fdi_inflow": 1170},
    2012: {"national_gdp": 534123, "cpi_yoy": 2.6, "lpr_1y": 5.85, "fdi_inflow": 1211},
    2013: {"national_gdp": 588019, "cpi_yoy": 2.6, "lpr_1y": 5.60, "fdi_inflow": 1240},
    2014: {"national_gdp": 635910, "cpi_yoy": 2.0, "lpr_1y": 5.60, "fdi_inflow": 1285},
    2015: {"national_gdp": 685506, "cpi_yoy": 1.4, "lpr_1y": 4.35, "fdi_inflow": 1356},
    2016: {"national_gdp": 744127, "cpi_yoy": 2.0, "lpr_1y": 4.35, "fdi_inflow": 1340},
    2017: {"national_gdp": 827122, "cpi_yoy": 1.6, "lpr_1y": 4.35, "fdi_inflow": 1360},
    2018: {"national_gdp": 900310, "cpi_yoy": 2.1, "lpr_1y": 4.31, "fdi_inflow": 1383},
    2019: {"national_gdp": 990865, "cpi_yoy": 2.9, "lpr_1y": 4.15, "fdi_inflow": 1381},
    2020: {"national_gdp": 1013567, "cpi_yoy": 2.5, "lpr_1y": 3.85, "fdi_inflow": 1444},
    2021: {"national_gdp": 1149237, "cpi_yoy": 0.9, "lpr_1y": 3.70, "fdi_inflow": 1735},
    2022: {"national_gdp": 1231048, "cpi_yoy": 2.0, "lpr_1y": 3.65, "fdi_inflow": 1891},
    2023: {"national_gdp": 1260582, "cpi_yoy": 0.2, "lpr_1y": 3.45, "fdi_inflow": 1633},
    2024: {"national_gdp": 1315000, "cpi_yoy": 0.5, "lpr_1y": 3.10, "fdi_inflow": 1500},
    2025: {"national_gdp": 1370000, "cpi_yoy": 1.0, "lpr_1y": 3.00, "fdi_inflow": 1450},
}


INDICATOR_META = {
    "national_gdp": {
        "name": "全国实际 GDP",
        "unit": "亿元",
        "category": "absolute",
        "source": "NBSC 年度统计公报",
        "url": NBSC_URL,
    },
    "cpi_yoy": {
        "name": "CPI 同比",
        "unit": "%",
        "category": "rate",
        "source": "NBSC 居民消费价格指数",
        "url": NBSC_URL,
    },
    "lpr_1y": {
        "name": "1 年期 LPR",
        "unit": "%",
        "category": "rate",
        "source": "中国人民银行 LPR 公告",
        "url": PBOC_URL,
        "note": "2019-08 前为贷款基准利率",
    },
    "fdi_inflow": {
        "name": "实际利用外资",
        "unit": "亿美元",
        "category": "absolute",
        "source": "商务部外资统计",
        "url": "http://www.mofcom.gov.cn/",
    },
}


# --------------------------------------------------------------------------- #
# 公开 API
# --------------------------------------------------------------------------- #


def list_macro_indicators() -> list[str]:
    return sorted(INDICATOR_META.keys())


def get_macro_timeseries() -> pd.DataFrame:
    """返回 2010-2025 宏观时序 DataFrame"""
    records = []
    for year in sorted(MACRO_HISTORICAL.keys()):
        rec = {"year": year}
        rec.update(MACRO_HISTORICAL[year])
        records.append(rec)
    return pd.DataFrame(records)


def get_macro_value(indicator: str, year: int) -> dict[str, Any] | None:
    """返回某年某宏观指标 + provenance"""
    if year not in MACRO_HISTORICAL:
        return None
    if indicator not in MACRO_HISTORICAL[year]:
        return None
    meta = INDICATOR_META.get(indicator, {})
    value = MACRO_HISTORICAL[year][indicator]
    return {
        "indicator": indicator,
        "year": int(year),
        "value": value,
        "unit": meta.get("unit"),
        "provenance": {
            "source": meta.get("source", "NBSC"),
            "url": meta.get("url", NBSC_URL),
            "estimated": year >= 2024,  # 2024-2025 部分为初步核算
            "confidence": 0.85 if year >= 2024 else 0.98,
            "note": meta.get("note"),
            "last_updated": "2026-06-04",
        },
    }


def compute_growth_rates() -> pd.DataFrame:
    """衍生:YoY 增长率"""
    df = get_macro_timeseries().sort_values("year").reset_index(drop=True)
    for col in ["national_gdp", "fdi_inflow"]:
        df[f"{col}_yoy"] = df[col].pct_change() * 100
    return df


if __name__ == "__main__":
    df = get_macro_timeseries()
    print(f"Macro: {df.shape[0]}y × {df.shape[1]} indicators")
    print(df.to_string(index=False))
    print("\nYoY growth:")
    print(compute_growth_rates()[["year", "national_gdp", "national_gdp_yoy"]].tail().to_string(index=False))
