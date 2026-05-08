"""
数据一致性验证模块

功能：
1. 中央 vs 地方数据一致性校验
2. 多源数据交叉验证
3. 异常数据检测
4. 数据漏洞发现
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import akshare as ak
import json
import logging

logger = logging.getLogger(__name__)


class DataConsistencyCheckerTool(BaseTool):
    """数据一致性检查工具"""

    name: str = "数据一致性检查工具"
    description: str = """
    检查中央和地方数据的一致性，发现数据矛盾
    输入格式: JSON字符串 {"indicator": "gdp", "tolerance": 0.05}
    - indicator: 指标类型 (gdp, revenue, expenditure)
    - tolerance: 允许的误差范围 (默认5%)
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return check_data_consistency(
                params.get("indicator"),
                params.get("tolerance", 0.05)
            )
        except Exception as e:
            return f"一致性检查失败: {str(e)}"


class CrossValidationTool(BaseTool):
    """交叉验证工具"""

    name: str = "多源数据交叉验证工具"
    description: str = """
    使用多个数据源交叉验证同一指标
    输入: 指标名称字符串，如 'gdp', 'cpi'
    """

    def _run(self, indicator: str) -> str:
        return cross_validate_indicator(indicator)


class AnomalyDetectionTool(BaseTool):
    """异常检测工具"""

    name: str = "数据异常检测工具"
    description: str = """
    检测数据中的异常值和突变点
    输入格式: JSON {"data": [...], "method": "zscore", "threshold": 3}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return detect_anomalies(
                params.get("data", []),
                params.get("method", "zscore"),
                params.get("threshold", 3)
            )
        except Exception as e:
            return f"异常检测失败: {str(e)}"


class ReportComparatorTool(BaseTool):
    """报告对比工具"""

    name: str = "报告对比工具"
    description: str = """
    对比两份报告中的数据，发现差异和矛盾
    输入格式: JSON {"report1": {...}, "report2": {...}}
    """

    def _run(self, request: str) -> str:
        try:
            params = json.loads(request)
            return compare_reports(
                params.get("report1", {}),
                params.get("report2", {})
            )
        except Exception as e:
            return f"报告对比失败: {str(e)}"


# ==================== 核心验证函数 ====================

def check_data_consistency(indicator: str, tolerance: float = 0.05) -> str:
    """
    检查中央和地方数据的一致性

    验证规则:
    - 地方GDP总和 ≈ 全国GDP
    - 地方财政收入总和 ≈ 中央财政收入
    - 地方财政支出总和 ≈ 中央财政支出
    """
    results = []
    results.append(f"📊 数据一致性检查: {indicator}")
    results.append(f"容忍误差: {tolerance * 100:.1f}%")
    results.append("=" * 60)

    try:
        if indicator in ["gdp", "revenue", "expenditure"]:
            # 获取全国数据
            if indicator == "gdp":
                national_df = ak.macro_china_gdp()
                national_total = national_df["国内生产总值-绝对值"].iloc[-1]
                national_unit = "亿元"
            elif indicator == "revenue":
                national_df = ak.macro_china_czsr()
                national_total = national_df["累计"].iloc[-1]
                national_unit = "亿元"
            else:
                national_df = ak.macro_china_czsr()
                national_total = national_df["累计"].iloc[-1] * 1.3  # 估算
                national_unit = "亿元"

            results.append(f"\n📍 全国总计: {national_total:,.2f} {national_unit}")

            # 模拟省份数据 (实际需要从各省市统计局获取)
            provinces = get_provincial_data(indicator)
            if provinces:
                province_total = sum(provinces.values())
                diff = abs(national_total - province_total)
                diff_pct = diff / national_total * 100 if national_total else 0

                results.append(f"\n📍 省份合计: {province_total:,.2f} {national_unit}")
                results.append(f"\n⚖️  差异: {diff:,.2f} ({diff_pct:.2f}%)")

                if diff_pct <= tolerance * 100:
                    results.append(f"\n✅ 一致性检验: 通过 (误差 {diff_pct:.2f}% <= {tolerance*100}%)")
                else:
                    results.append(f"\n❌ 一致性检验: 不通过 (误差 {diff_pct:.2f}% > {tolerance*100}%)")
                    results.append(f"\n⚠️  可能原因:")
                    results.append("   - 地方数据未完全公布")
                    results.append("   - 统计口径不一致")
                    results.append("   - 存在数据造假嫌疑")
            else:
                results.append("\n⚠️  省份数据暂不可用")

            return "\n".join(results)

        else:
            return f"暂不支持对 {indicator} 的一致性检验"

    except Exception as e:
        logger.error(f"一致性检查失败: {e}")
        return f"一致性检查失败: {str(e)}"


def get_provincial_data(indicator: str) -> Dict[str, float]:
    """
    获取省份数据 (模拟数据，实际需接入各省市API)
    这里返回模拟数据用于演示
    """
    # 模拟31个省市的GDP数据 (实际需从各省统计局获取)
    if indicator == "gdp":
        return {
            "广东": 135000,
            "江苏": 128000,
            "山东": 95000,
            "浙江": 82000,
            "河南": 59000,
            "四川": 56000,
            "湖北": 55000,
            "福建": 54000,
            "湖南": 51000,
            "安徽": 47000,
            # ... 其他省份
        }
    return {}


def cross_validate_indicator(indicator: str) -> str:
    """
    多源数据交叉验证
    """
    results = []
    results.append(f"🔍 交叉验证: {indicator}")
    results.append("=" * 60)

    data_sources = []

    try:
        if indicator == "gdp":
            # 来源1: 统计局GDP
            try:
                df = ak.macro_china_gdp()
                if not df.empty:
                    latest = df["国内生产总值-绝对值"].iloc[-1]
                    data_sources.append(("国家统计局GDP", latest))
            except:
                pass

            # 来源2: 社融数据推算
            try:
                df = ak.macro_china_shrzgm()
                if not df.empty:
                    # 简单推算
                    latest = df["当月"].iloc[-1] * 100 if not pd.isna(df["当月"].iloc[-1]) else None
                    if latest:
                        data_sources.append(("社融推算GDP", latest))
            except:
                pass

            # 来源3: 贸易数据验证
            try:
                export = ak.macro_china_exports_yoy()
                import_df = ak.macro_china_imports_yoy()
                if not export.empty and not import_df.empty:
                    trade_balance = 0  # 简化
                    data_sources.append(("贸易数据参考", trade_balance))
            except:
                pass

        elif indicator == "inflation" or indicator == "cpi":
            try:
                df = ak.macro_china_cpi_yearly()
                if not df.empty:
                    latest = df["今值"].iloc[-1]
                    data_sources.append(("CPI年率", latest))
            except:
                pass

            try:
                df = ak.macro_china_ppi_yearly()
                if not df.empty:
                    latest = df["今值"].iloc[-1]
                    data_sources.append(("PPI年率", latest))
            except:
                pass

        # 输出验证结果
        results.append(f"\n找到 {len(data_sources)} 个数据源:")
        for source, value in data_sources:
            results.append(f"  📌 {source}: {value}")

        if len(data_sources) >= 2:
            # 计算一致性
            values = [v for _, v in data_sources if v is not None]
            if values:
                mean_val = np.mean(values)
                std_val = np.std(values) if len(values) > 1 else 0
                cv = std_val / mean_val * 100 if mean_val else 0

                results.append(f"\n📊 统计摘要:")
                results.append(f"   平均值: {mean_val:.2f}")
                results.append(f"   标准差: {std_val:.2f}")
                results.append(f"   变异系数: {cv:.2f}%")

                if cv < 10:
                    results.append(f"\n✅ 交叉验证: 通过 (数据一致性高)")
                elif cv < 20:
                    results.append(f"\n⚠️  交叉验证: 警告 (存在一定差异)")
                else:
                    results.append(f"\n❌ 交叉验证: 不通过 (数据差异较大，需核查)")

        return "\n".join(results)

    except Exception as e:
        logger.error(f"交叉验证失败: {e}")
        return f"交叉验证失败: {str(e)}"


def detect_anomalies(data: List[float], method: str = "zscore", threshold: float = 3) -> str:
    """
    异常值检测

    方法:
    - zscore: Z分数法，超过threshold个标准差为异常
    - iqr: 四分位距法，超出Q1-1.5*IQR或Q3+1.5*IQR为异常
    """
    results = []
    results.append(f"🔎 异常检测")
    results.append(f"方法: {method}, 阈值: {threshold}")
    results.append("=" * 60)

    if not data or len(data) < 3:
        return "数据量不足，无法进行异常检测"

    arr = np.array(data)

    anomalies = []
    anomaly_indices = []

    if method == "zscore":
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return "标准差为0，无法进行Z-score检测"

        z_scores = np.abs((arr - mean) / std)
        anomaly_indices = np.where(z_scores > threshold)[0]
        anomalies = arr[anomaly_indices]

        results.append(f"\n统计量:")
        results.append(f"   均值: {mean:.4f}")
        results.append(f"   标准差: {std:.4f}")
        results.append(f"\n异常值 (Z-score > {threshold}):")

    elif method == "iqr":
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomaly_indices = np.where((arr < lower_bound) | (arr > upper_bound))[0]
        anomalies = arr[anomaly_indices]

        results.append(f"\n统计量:")
        results.append(f"   Q1: {q1:.4f}")
        results.append(f"   Q3: {q3:.4f}")
        results.append(f"   IQR: {iqr:.4f}")
        results.append(f"   正常范围: [{lower_bound:.4f}, {upper_bound:.4f}]")
        results.append(f"\n异常值:")

    if len(anomaly_indices) == 0:
        results.append("   未发现异常值 ✓")
    else:
        for i, idx in enumerate(anomaly_indices):
            results.append(f"   索引 {idx}: {anomalies[i]:.4f}")
            results.append(f"   ⚠️  可能原因: 数据录入错误/统计口径变化/异常事件")

    return "\n".join(results)


def compare_reports(report1: Dict, report2: Dict) -> str:
    """
    对比两份报告的数据差异
    """
    results = []
    results.append("📄 报告对比分析")
    results.append("=" * 60)

    # 提取报告标题
    title1 = report1.get("title", "报告1")
    title2 = report2.get("title", "报告2")
    results.append(f"\n对比: {title1} vs {title2}")

    # 提取数据指标
    data1 = report1.get("data", {})
    data2 = report2.get("data", {})

    if not data1 or not data2:
        return "报告缺少数据，无法对比"

    all_keys = set(data1.keys()) | set(data2.keys())

    results.append(f"\n发现 {len(all_keys)} 个可对比指标:")
    results.append("-" * 60)

    differences = []

    for key in sorted(all_keys):
        v1 = data1.get(key)
        v2 = data2.get(key)

        if v1 is not None and v2 is not None:
            try:
                val1 = float(v1)
                val2 = float(v2)
                diff = abs(val1 - val2)
                diff_pct = diff / val1 * 100 if val1 != 0 else 0

                status = "✅" if diff_pct < 1 else "⚠️" if diff_pct < 5 else "❌"

                results.append(f"\n{key}:")
                results.append(f"   {title1}: {val1:,.2f}")
                results.append(f"   {title2}: {val2:,.2f}")
                results.append(f"   差异: {diff:,.2f} ({diff_pct:.2f}%) {status}")

                if diff_pct >= 5:
                    differences.append((key, diff_pct, val1, val2))

            except (ValueError, TypeError):
                results.append(f"\n{key}: 类型不兼容")

    if differences:
        results.append("\n" + "=" * 60)
        results.append("⚠️  发现显著差异:")
        for key, pct, v1, v2 in differences:
            results.append(f"   - {key}: 差异 {pct:.1f}% ({v1:.0f} vs {v2:.0f})")
            results.append(f"     可能原因: 统计时间点不同/口径差异/数据修正")

    return "\n".join(results)


class VerificationAgent:
    """数据验证专家 Agent"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [
            DataConsistencyCheckerTool(),
            CrossValidationTool(),
            AnomalyDetectionTool(),
            ReportComparatorTool(),
        ]

    def create_agent(self) -> Agent:
        """创建验证 Agent"""
        return Agent(
            role="数据验证专家",
            goal="确保数据准确性，发现数据矛盾和漏洞",
            backstory="""
            你是一位资深的数据审计师，精通统计学和经济学数据验证。
            你擅长：
            - 发现数据不一致和异常
            - 交叉验证多源数据
            - 对比分析不同报告的差异
            - 识别潜在的数据造假和统计问题

            你的工作对于确保数据质量和报告可信度至关重要。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )


class ComparisonAgent:
    """对比分析专家 Agent"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = []

    def create_agent(self) -> Agent:
        """创建对比分析 Agent"""
        return Agent(
            role="对比分析专家",
            goal="深入挖掘数据关系，发现趋势和规律",
            backstory="""
            你是一位经济分析专家，擅长多维度对比分析：
            - 纵向对比: 历史趋势分析
            - 横向对比: 不同地区/行业对比
            - 结构对比: 产业结构变化
            - 增速对比: 增长动力分析

            你能从对比中发现隐藏的规律和异常。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )
