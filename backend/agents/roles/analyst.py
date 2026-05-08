"""
经济分析智能体 - 执行指标计算和经济学模型分析
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class IndicatorCalculatorTool(BaseTool):
    """指标计算工具"""

    name: str = "经济指标计算工具"
    description: str = """
    根据经济学公式计算衍生指标：
    - 财政赤字 = 支出 - 收入
    - 赤字率 = 赤字 / GDP × 100%
    - 宏观税负 = 税收 / GDP × 100%
    - 城乡差距 = 城镇收入 / 农村收入
    - 贸易顺差 = 出口 - 进口
    - 三次产业占比
    输入格式：JSON字符串如 '{"indicator": "deficit_rate", "inputs": {"revenue": 200000, "expenditure": 250000, "gdp": 1200000}}'
    """

    def _run(self, request: str) -> str:
        import json
        try:
            data = json.loads(request)
            result = calculate_indicator(data["indicator"], data.get("inputs", {}))
            return result
        except Exception as e:
            return f"指标计算失败: {str(e)}"


class EconomicModelTool(BaseTool):
    """经济学模型工具"""

    name: str = "经济学模型分析工具"
    description: str = """
    运行经典经济学模型进行分析：
    - phillips: 菲利普斯曲线 (通胀与失业关系)
    - okun: 奥肯定律 (GDP与失业关系)
    - cobb_douglas: 柯布-道格拉斯生产函数
    - solow: 索洛增长模型
    输入格式：JSON字符串如 '{"model": "phillips", "params": {"unemployment": 5.5, "natural_unemployment": 5.0}}'
    """

    def _run(self, request: str) -> str:
        import json
        try:
            data = json.loads(request)
            result = run_economic_model(data["model"], data.get("params", {}))
            return result
        except Exception as e:
            return f"模型运行失败: {str(e)}"


class CorrelationAnalysisTool(BaseTool):
    """相关性分析工具"""

    name: str = "相关性分析工具"
    description: str = """
    分析多个经济指标之间的相关性，计算皮尔逊相关系数矩阵
    输入格式：JSON字符串如 '{"indicators": ["gdp", "cpi", "m2"], "data": [[...], [...], [...]]}'
    """

    def _run(self, request: str) -> str:
        import json
        try:
            data = json.loads(request)
            result = analyze_correlation(data.get("indicators", []), data.get("data", []))
            return result
        except Exception as e:
            return f"相关性分析失败: {str(e)}"


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
        return f"未知指标: {indicator}，可用: {list(formulas.keys())}"

    try:
        value = formulas[indicator](inputs)
        return f"{indicator} = {value:.4f}"
    except Exception as e:
        return f"计算{indicator}失败: {str(e)}"


def run_economic_model(model: str, params: Dict[str, Any]) -> str:
    """运行经济学模型"""
    results = []

    if model == "phillips":
        u = params.get("unemployment", 5.0)
        u_star = params.get("natural_unemployment", 5.0)
        pi_e = params.get("expected_inflation", 2.0)
        beta = params.get("beta", 0.5)
        inflation = pi_e - beta * (u - u_star)
        results.append(f"菲利普斯曲线分析")
        results.append(f"失业率: {u}% (自然失业率: {u_star}%)")
        results.append(f"预期通胀: {pi_e}%")
        results.append(f"计算通胀率: π = {pi_e} - {beta}×({u} - {u_star}) = {inflation:.2f}%")
        if inflation > 5:
            results.append("解读: 通胀压力较大")
        elif inflation < 0:
            results.append("解读: 存在通缩风险")
        else:
            results.append("解读: 通胀处于温和区间")

    elif model == "okun":
        gdp_growth = params.get("gdp_growth", 5.0)
        potential_growth = params.get("potential_growth", 6.0)
        beta = params.get("okun_coefficient", 2.0)
        output_gap = gdp_growth - potential_growth
        unemp_change = -output_gap / beta
        results.append(f"奥肯定律分析")
        results.append(f"实际GDP增速: {gdp_growth}% (潜在增速: {potential_growth}%)")
        results.append(f"产出缺口: {output_gap:.2f}%")
        results.append(f"失业率变化: {unemp_change:.2f}%")
        results.append(f"解读: {'经济过热' if output_gap > 0 else '经济下行压力'}")

    elif model == "cobb_douglas":
        k = params.get("capital", 100)
        l = params.get("labor", 100)
        alpha = params.get("alpha", 0.3)
        a = params.get("technology", 1.0)
        y = a * (k ** alpha) * (l ** (1 - alpha))
        results.append(f"柯布-道格拉斯生产函数")
        results.append(f"资本K={k}, 劳动L={l}, α={alpha}, 技术A={a}")
        results.append(f"产出Y = A×K^α×L^(1-α) = {y:.2f}")
        results.append(f"资本边际产出 = α×Y/K = {alpha*y/k:.4f}")
        results.append(f"劳动边际产出 = (1-α)×Y/L = {(1-alpha)*y/l:.4f}")

    elif model == "solow":
        s = params.get("savings_rate", 0.3)
        n = params.get("population_growth", 0.01)
        delta = params.get("depreciation", 0.05)
        alpha = params.get("alpha", 0.3)
        k_star = (s / (n + delta)) ** (1 / (1 - alpha))
        y_star = (k_star ** alpha)
        results.append(f"索洛增长模型稳态")
        results.append(f"储蓄率s={s}, 人口增长率n={n}, 折旧率δ={delta}")
        results.append(f"稳态人均资本: k* = {k_star:.4f}")
        results.append(f"稳态人均产出: y* = {y_star:.4f}")
        results.append(f"黄金律储蓄率: s* = α = {alpha:.2f}")

    else:
        return f"未知模型: {model}"

    return "\n".join(results)


def analyze_correlation(indicators: List[str], data: List[List[float]]) -> str:
    """相关性分析"""
    if len(indicators) < 2 or len(data) < 2:
        return "需要至少2个指标的数据"

    try:
        n = len(data[0])
        matrix = []
        for i, ind1 in enumerate(indicators):
            row = []
            for j, ind2 in enumerate(indicators):
                if i == j:
                    row.append(1.0)
                elif j < i:
                    row.append(matrix[j][i])
                else:
                    r, _ = stats.pearsonr(data[i][:n], data[j][:n])
                    row.append(r)
            matrix.append(row)

        results = ["相关性矩阵:"]
        header = "        " + "  ".join(f"{ind[:8]:>8}" for ind in indicators)
        results.append(header)
        for i, row in enumerate(matrix):
            line = f"{indicators[i][:8]:>8}" + "  ".join(f"{r:>8.3f}" for r in row)
            results.append(line)

        return "\n".join(results)
    except Exception as e:
        return f"相关性分析失败: {str(e)}"


class AnalystAgent:
    """经济分析智能体"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [
            IndicatorCalculatorTool(),
            EconomicModelTool(),
            CorrelationAnalysisTool(),
        ]

    def create_agent(self) -> Agent:
        """创建分析智能体"""
        return Agent(
            role="经济分析专家",
            goal="基于数据提供深入的经济洞察和政策建议",
            backstory="""
            你是一位资深的经济学家，精通宏观经济理论和经济模型。
            你擅长从数据中发现规律、识别趋势，并提供有价值的分析见解。
            你熟悉菲利普斯曲线、奥肯定律、柯布-道格拉斯函数等经典经济学模型，
            能够将复杂的理论应用于实际经济问题分析。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )

    @staticmethod
    def get_supported_models() -> List[str]:
        """获取支持的模型列表"""
        return ["phillips", "okun", "cobb_douglas", "solow"]

    @staticmethod
    def get_supported_indicators() -> List[str]:
        """获取支持的指标列表"""
        return [
            "fiscal_deficit",
            "deficit_rate",
            "tax_ratio",
            "urban_rural_gap",
            "trade_balance",
            "primary_ratio",
            "secondary_ratio",
            "tertiary_ratio",
        ]
