"""
预警系统模块 - 数据异常检测与预警
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


ALERT_RULES = {
    "cpi": {
        "name": "CPI居民消费价格指数",
        "unit": "%",
        "thresholds": {
            "critical_high": 5.0,
            "warning_high": 3.0,
            "warning_low": 0.5,
            "critical_low": -0.5,
        },
        "description": "通胀预警"
    },
    "ppi": {
        "name": "PPI工业生产者出厂价格",
        "unit": "%",
        "thresholds": {
            "critical_high": 5.0,
            "warning_high": 2.0,
            "warning_low": -2.0,
            "critical_low": -5.0,
        },
        "description": "工业通缩预警"
    },
    "pmi": {
        "name": "PMI制造业采购经理指数",
        "unit": "",
        "thresholds": {
            "critical_low": 45.0,
            "warning_low": 48.0,
            "warning_high": 55.0,
            "critical_high": 58.0,
        },
        "description": "制造业景气预警"
    },
    "m2": {
        "name": "M2货币供应量",
        "unit": "%",
        "thresholds": {
            "critical_low": 6.0,
            "warning_low": 8.0,
            "warning_high": 12.0,
            "critical_high": 15.0,
        },
        "description": "货币供应预警"
    },
    "unemployment": {
        "name": "城镇调查失业率",
        "unit": "%",
        "thresholds": {
            "critical_high": 6.0,
            "warning_high": 5.5,
            "warning_low": 4.5,
            "critical_low": 4.0,
        },
        "description": "就业形势预警"
    },
    "lpr_1y": {
        "name": "LPR 1年期利率",
        "unit": "%",
        "thresholds": {
            "critical_low": 3.0,
            "warning_low": 3.5,
            "warning_high": 4.5,
            "critical_high": 5.0,
        },
        "description": "利率预警"
    },
    "gdp_growth": {
        "name": "GDP增速",
        "unit": "%",
        "thresholds": {
            "critical_low": 4.0,
            "warning_low": 5.0,
            "warning_high": 8.0,
            "critical_high": 10.0,
        },
        "description": "经济增长预警"
    }
}


class RealTimeAlertTool(BaseTool):
    """实时预警工具"""

    name: str = "实时数据预警工具"
    description: str = """
    获取所有关键指标的最新数据并进行预警检测
    输入: 空或 "all"
    """

    def _run(self, indicator: str = "all") -> str:
        return get_all_alerts()


class ThresholdAlertTool(BaseTool):
    """阈值预警工具"""

    name: str = "阈值预警工具"
    description: str = """
    针对特定指标进行阈值预警
    输入格式: JSON {"indicator": "cpi", "value": 2.5}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return check_threshold_alert(
                params.get("indicator"),
                params.get("value")
            )
        except Exception as e:
            return f"预警检查失败: {str(e)}"


class TrendAlertTool(BaseTool):
    """趋势预警工具"""

    name: str = "趋势预警工具"
    description: str = """
    检测指标的趋势异常
    输入格式: JSON {"indicator": "cpi", "periods": 6}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return check_trend_alert(
                params.get("indicator"),
                params.get("periods", 6)
            )
        except Exception as e:
            return f"趋势预警失败: {str(e)}"


class ReportComparisonAlertTool(BaseTool):
    """报告对比预警工具"""

    name: str = "数据一致性预警"
    description: str = """
    检测不同来源数据的矛盾
    输入格式: JSON {"indicator": "gdp"}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return check_data_consistency_alert(params.get("indicator"))
        except Exception as e:
            return f"一致性预警失败: {str(e)}"


def get_all_alerts() -> str:
    """
    获取所有指标的预警状态
    """
    results = [
        "🚨 " + "=" * 60,
        "📊 全局经济指标预警监控",
        "=" * 60,
        f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]

    alerts_found = []
    normal_count = 0

    for ind, config in ALERT_RULES.items():
        try:
            value, status, message = get_indicator_alert(ind, config)
            if status == "normal":
                normal_count += 1
            else:
                alerts_found.append((status, ind, config["name"], message, value))
        except Exception as e:
            logger.error(f"获取{ind}预警失败: {e}")

    results.append(f"📈 共监测 {len(ALERT_RULES)} 项指标")
    results.append(f"✅ 正常: {normal_count} 项")
    results.append(f"⚠️ 预警: {len(alerts_found)} 项")
    results.append("")

    if alerts_found:
        results.append("=" * 60)
        results.append("🚨 预警详情:")
        results.append("-" * 60)

        critical = [a for a in alerts_found if a[0] == "critical"]
        warning = [a for a in alerts_found if a[0] == "warning"]

        for status, ind, name, msg, value in critical:
            results.append(f"🔴 严重 | {name}: {value}{config['unit']}")
            results.append(f"   {msg}")
            results.append("")

        for status, ind, name, msg, value in warning:
            results.append(f"🟠 警告 | {name}: {value}{config['unit']}")
            results.append(f"   {msg}")
            results.append("")

    else:
        results.append("✅ 所有指标运行正常，无预警信息")

    results.append("=" * 60)

    return "\n".join(results)


def get_indicator_alert(indicator: str, config: Dict) -> tuple:
    """
    获取单个指标的预警状态
    """
    thresholds = config["thresholds"]

    try:
        if indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            value = float(df["今值"].dropna().iloc[-1])
        elif indicator == "ppi":
            df = ak.macro_china_ppi_yearly()
            value = float(df["今值"].dropna().iloc[-1])
        elif indicator == "pmi":
            df = ak.macro_china_pmi_yearly()
            value = float(df["今值"].dropna().iloc[-1])
        elif indicator == "m2":
            df = ak.macro_china_m2_yearly()
            value = float(df["今值"].dropna().iloc[-1])
        elif indicator == "unemployment":
            df = ak.macro_china_urban_unemployment()
            value = float(df["value"].dropna().iloc[-1])
        elif indicator == "lpr_1y":
            df = ak.macro_china_lpr()
            value = float(df["LPR1Y"].iloc[-1])
        elif indicator == "gdp_growth":
            df = ak.macro_china_gdp()
            value = float(df["国内生产总值-同比增长"].dropna().iloc[-1])
        else:
            return None, "unknown", "不支持该指标"

        if "critical_low" in thresholds and value < thresholds["critical_low"]:
            return value, "critical", f"低于严重阈值 {thresholds['critical_low']}"
        if "critical_high" in thresholds and value > thresholds["critical_high"]:
            return value, "critical", f"高于严重阈值 {thresholds['critical_high']}"
        if "warning_low" in thresholds and value < thresholds["warning_low"]:
            return value, "warning", f"低于警戒阈值 {thresholds['warning_low']}"
        if "warning_high" in thresholds and value > thresholds["warning_high"]:
            return value, "warning", f"高于警戒阈值 {thresholds['warning_high']}"

        return value, "normal", "运行正常"

    except Exception as e:
        logger.error(f"获取{indicator}数据失败: {e}")
        return None, "error", str(e)


def check_threshold_alert(indicator: str, value: float) -> str:
    """
    检查阈值预警
    """
    if indicator not in ALERT_RULES:
        return f"不支持指标: {indicator}"

    config = ALERT_RULES[indicator]
    thresholds = config["thresholds"]

    results = [
        f"🔍 {config['name']} 阈值预警检查",
        "=" * 60,
        f"输入值: {value}{config['unit']}",
        f"阈值设置:",
        f"  严重下限: {thresholds.get('critical_low', 'N/A')}",
        f"  警戒下限: {thresholds.get('warning_low', 'N/A')}",
        f"  警戒上限: {thresholds.get('warning_high', 'N/A')}",
        f"  严重上限: {thresholds.get('critical_high', 'N/A')}",
        ""
    ]

    if "critical_low" in thresholds and value < thresholds["critical_low"]:
        results.append(f"🔴 【严重预警】值 {value} 低于严重下限 {thresholds['critical_low']}")
    elif "critical_high" in thresholds and value > thresholds["critical_high"]:
        results.append(f"🔴 【严重预警】值 {value} 高于严重上限 {thresholds['critical_high']}")
    elif "warning_low" in thresholds and value < thresholds["warning_low"]:
        results.append(f"🟠 【警戒预警】值 {value} 低于警戒下限 {thresholds['warning_low']}")
    elif "warning_high" in thresholds and value > thresholds["warning_high"]:
        results.append(f"🟠 【警戒预警】值 {value} 高于警戒上限 {thresholds['warning_high']}")
    else:
        results.append(f"✅ 值在正常范围内")

    return "\n".join(results)


def check_trend_alert(indicator: str, periods: int = 6) -> str:
    """
    趋势预警 - 检测连续变化趋势
    """
    try:
        if indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            data = df["今值"].dropna().tail(periods).values
        elif indicator == "ppi":
            df = ak.macro_china_ppi_yearly()
            data = df["今值"].dropna().tail(periods).values
        elif indicator == "pmi":
            df = ak.macro_china_pmi_yearly()
            data = df["今值"].dropna().tail(periods).values
        else:
            return f"暂不支持 {indicator} 的趋势分析"

        if len(data) < periods:
            return "数据不足，无法进行趋势分析"

        name = ALERT_RULES.get(indicator, {}).get("name", indicator)
        unit = ALERT_RULES.get(indicator, {}).get("unit", "")

        changes = np.diff(data)
        avg_change = np.mean(changes)
        consecutive_direction = "下降" if all(c < 0 for c in changes) else "上升" if all(c > 0 for c in changes) else "波动"

        results = [
            f"📈 {name} 趋势预警分析",
            "=" * 60,
            f"分析周期: 近 {periods} 期",
            f"数据序列: {[f'{v:.1f}{unit}' for v in data]}",
            f"变化量: {[f'{c:+.1f}{unit}' for c in changes]}",
            "",
            f"平均变化: {avg_change:+.2f}{unit}/期",
            f"变化趋势: {consecutive_direction}",
            ""
        ]

        alert = False

        if all(c < 0 for c in changes) and abs(avg_change) > 0.5:
            results.append(f"🔴 【持续下降预警】连续{periods}期下降，平均每期下降 {abs(avg_change):.2f}{unit}")
            alert = True
        elif all(c > 0 for c in changes) and avg_change > 0.5:
            results.append(f"🔴 【持续上升预警】连续{periods}期上升，平均每期上升 {avg_change:.2f}{unit}")
            alert = True

        if not alert:
            results.append("✅ 趋势运行正常，无明显异常")

        return "\n".join(results)

    except Exception as e:
        logger.error(f"趋势分析失败: {e}")
        return f"趋势分析失败: {str(e)}"


def check_data_consistency_alert(indicator: str) -> str:
    """
    数据一致性预警
    """
    results = [
        f"🔍 {indicator.upper()} 数据一致性检查",
        "=" * 60,
    ]

    try:
        if indicator == "gdp":
            national_df = ak.macro_china_gdp()
            national_total = national_df["国内生产总值-绝对值"].dropna().iloc[-1]

            results.append(f"全国GDP: {national_total:,.0f} 亿元")

            if national_total > 500000:
                results.append("⚠️ 检测到异常: GDP数据可能为季度累计值")
            else:
                results.append("✅ GDP数据一致性正常")

        results.append("")
        results.append("说明: 此功能需接入地方数据才能进行完整的一致性验证")

    except Exception as e:
        results.append(f"❌ 一致性检查失败: {str(e)}")

    return "\n".join(results)


class AlertAgent:
    """预警监控 Agent"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [
            RealTimeAlertTool(),
            ThresholdAlertTool(),
            TrendAlertTool(),
            ReportComparisonAlertTool(),
        ]

    def create_agent(self) -> Agent:
        """创建预警 Agent"""
        return Agent(
            role="经济预警专家",
            goal="实时监控经济数据，及时发现异常并预警",
            backstory="""
            你是一位专业的经济预警分析师，负责实时监控各类经济指标。
            你熟悉各种经济指标的健康范围和预警阈值：
            - CPI: 正常0-3%，超过5%为严重通胀
            - PPI: 负值表示工业通缩
            - PMI: 50为荣枯线，低于45为严重收缩
            - 失业率: 超过6%为严重就业问题

            你的职责是及时发现数据异常，为决策提供预警支持。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )
