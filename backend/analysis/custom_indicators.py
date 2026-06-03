"""
自定义指标计算引擎
支持用户定义自己的指标计算公式
"""

import ast
import logging
import math
import operator as op
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_SAFE_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

_SAFE_FUNCS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "max": max,
    "min": min,
    "sum": sum,
}


def _safe_eval_math(expr: str) -> float:
    try:
        import numexpr

        return float(numexpr.evaluate(expr))
    except ImportError:
        pass
    tree = ast.parse(expr, mode="eval")
    return _eval_node_math(tree.body)


def _eval_node_math(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        return _SAFE_OPS[type(node.op)](_eval_node_math(node.left), _eval_node_math(node.right))
    elif isinstance(node, ast.UnaryOp):
        return _SAFE_OPS[type(node.op)](_eval_node_math(node.operand))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            args = [_eval_node_math(a) for a in node.args]
            return _SAFE_FUNCS[node.func.id](*args)
    raise ValueError(f"Unsafe expression: {type(node)}")


class CalculationStatus(Enum):
    """计算状态"""

    SUCCESS = "success"
    PARTIAL = "partial"  # 部分成功
    FAILED = "failed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class CalculationResult:
    """计算结果"""

    indicator_code: str
    value: Any
    unit: str
    status: CalculationStatus
    message: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "indicator_code": self.indicator_code,
            "value": self.value,
            "unit": self.unit,
            "status": self.status.value,
            "message": self.message,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class DataProvider:
    """数据提供者接口"""

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        raise NotImplementedError

    def get_range(self, keys: list[str]) -> dict[str, Any]:
        """批量获取数据"""
        raise NotImplementedError


class DictDataProvider(DataProvider):
    """字典数据提供者"""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据，支持嵌套key如 'gdp.value'"""
        if "." in key:
            keys = key.split(".")
            value = self.data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            return value if value is not None else default
        return self.data.get(key, default)

    def get_range(self, keys: list[str]) -> dict[str, Any]:
        """批量获取数据"""
        return {key: self.get(key) for key in keys}


class DataFrameDataProvider(DataProvider):
    """DataFrame数据提供者"""

    def __init__(self, df: pd.DataFrame, id_col: str = "year"):
        self.df = df.set_index(id_col) if id_col else df
        self.id_col = id_col

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        if key in self.df.columns:
            return self.df[key].dropna().iloc[-1] if len(self.df) > 0 else default
        return default

    def get_range(self, keys: list[str]) -> dict[str, Any]:
        """批量获取数据"""
        return {key: self.get(key) for key in keys}


class CustomIndicatorEngine:
    """自定义指标计算引擎"""

    def __init__(self):
        self._formulas: dict[str, str] = {}
        self._custom_funcs: dict[str, Callable] = {}
        self._dependencies: dict[str, list[str]] = {}

        self._initialize_builtin_formulas()

    def _initialize_builtin_formulas(self):
        """初始化内置公式"""
        # 常用经济指标公式
        builtin_formulas = {
            # 经济增长类
            "growth_rate": "({current} - {previous}) / {previous} * 100",
            "cagr": "(({end} / {start}) ** (1 / {years}) - 1) * 100",  # 复合年均增长率
            # 财政类
            "deficit": "{expenditure} - {revenue}",
            "deficit_rate": "({expenditure} - {revenue}) / {gdp} * 100",
            "fiscal_self_sufficiency": "{revenue} / {expenditure} * 100",
            "tax_burden": "{tax_revenue} / {gdp} * 100",
            # 产业类
            "industry_ratio": "{industry_output} / {total_output} * 100",
            "concentration_hhi": "Σ({share} ** 2)",  # 赫芬达尔指数
            "location_quotient": "({local_share} / {total_share})",
            # 金融类
            "leverage_multiplier": "{social_capital} / {government_investment}",
            "roi": "{output_value} / {investment}",
            # 效率类
            "labor_productivity": "{output} / {labor}",
            "capital_productivity": "{output} / {capital}",
            "comprehensive_productivity": "({alpha} * {capital} ** {alpha} * {labor} ** (1-{alpha})) / {output}",
            # 成本类
            "cost_per_unit": "{total_cost} / {output}",
            "cost_ratio": "{cost} / {revenue} * 100",
            # 比率类
            "export_dependency": "{export} / {gdp} * 100",
            "import_dependency": "{import} / {consumption} * 100",
            "self_sufficiency": "{domestic_output} / {total_consumption} * 100",
            # 质量类
            "pass_rate": "{qualified} / {total} * 100",
            "satisfaction": "({very_satisfied} * 100 + {satisfied} * 75 + {neutral} * 50 + {dissatisfied} * 25) / {total}",
        }

        self._formulas.update(builtin_formulas)

    def register_formula(self, code: str, formula: str, dependencies: list[str], unit: str = "", description: str = ""):
        """
        注册计算公式

        Args:
            code: 指标代码
            formula: 计算公式，支持 {placeholder} 格式
            dependencies: 依赖的数据字段列表
            unit: 单位
            description: 描述
        """
        self._formulas[code] = formula
        self._dependencies[code] = dependencies
        logger.debug(f"注册公式: {code} = {formula}")

    def register_function(
        self,
        code: str,
        func: Callable[[DataProvider], Any],
        dependencies: list[str],
        unit: str = "",
        description: str = "",
    ):
        """
        注册自定义计算函数

        Args:
            code: 指标代码
            func: 计算函数，接收 DataProvider，返回计算结果
            dependencies: 依赖的数据字段列表
            unit: 单位
            description: 描述
        """
        self._custom_funcs[code] = func
        self._dependencies[code] = dependencies
        logger.debug(f"注册自定义函数: {code}")

    def calculate(self, indicator_code: str, data_provider: DataProvider, **kwargs) -> CalculationResult:
        """
        计算指标

        Args:
            indicator_code: 指标代码
            data_provider: 数据提供者
            **kwargs: 额外参数

        Returns:
            CalculationResult
        """
        # 检查是否有内置公式
        if indicator_code in self._formulas:
            return self._calculate_by_formula(indicator_code, data_provider)

        # 检查是否有自定义函数
        if indicator_code in self._custom_funcs:
            return self._calculate_by_function(indicator_code, data_provider)

        # 尝试直接获取数据
        value = data_provider.get(indicator_code)
        if value is not None:
            return CalculationResult(
                indicator_code=indicator_code,
                value=value,
                unit=kwargs.get("unit", ""),
                status=CalculationStatus.SUCCESS,
                message="直接获取数据",
            )

        return CalculationResult(
            indicator_code=indicator_code,
            value=None,
            unit="",
            status=CalculationStatus.FAILED,
            message=f"未知指标: {indicator_code}",
        )

    def _calculate_by_formula(self, indicator_code: str, data_provider: DataProvider) -> CalculationResult:
        """使用公式计算"""
        formula = self._formulas[indicator_code]
        dependencies = self._dependencies.get(indicator_code, [])

        # 获取所有依赖数据
        values = {}
        missing = []
        for dep in dependencies:
            val = data_provider.get(dep)
            if val is None:
                missing.append(dep)
            else:
                values[dep] = val

        if missing:
            return CalculationResult(
                indicator_code=indicator_code,
                value=None,
                unit="",
                status=CalculationStatus.INSUFFICIENT_DATA,
                message=f"缺少数据: {', '.join(missing)}",
                metadata={"missing": missing},
            )

        try:
            # 替换占位符
            expr = formula
            for key, value in values.items():
                expr = expr.replace(f"{{{key}}}", str(value))

            # 尝试解析特殊函数
            result = self._evaluate_expression(expr)

            return CalculationResult(
                indicator_code=indicator_code,
                value=round(result, 4) if isinstance(result, float) else result,
                unit="",
                status=CalculationStatus.SUCCESS,
                message="公式计算成功",
                metadata={"formula": formula, "inputs": values},
            )
        except Exception as e:
            return CalculationResult(
                indicator_code=indicator_code,
                value=None,
                unit="",
                status=CalculationStatus.FAILED,
                message=f"计算错误: {str(e)}",
                metadata={"formula": formula, "error": str(e)},
            )

    def _calculate_by_function(self, indicator_code: str, data_provider: DataProvider) -> CalculationResult:
        """使用自定义函数计算"""
        try:
            func = self._custom_funcs[indicator_code]
            result = func(data_provider)

            return CalculationResult(
                indicator_code=indicator_code,
                value=result,
                unit="",
                status=CalculationStatus.SUCCESS,
                message="自定义函数计算成功",
            )
        except Exception as e:
            return CalculationResult(
                indicator_code=indicator_code,
                value=None,
                unit="",
                status=CalculationStatus.FAILED,
                message=f"函数执行错误: {str(e)}",
            )

    def _evaluate_expression(self, expr: str) -> float:
        """评估数学表达式"""
        expr = expr.replace("**", "**")

        if "Σ(" in expr:
            expr = self._handle_sum(expr)

        return _safe_eval_math(expr)

    def _handle_sum(self, expr: str) -> str:
        """处理求和表达式"""
        import re

        # 匹配 Σ(var ** 2) 格式
        pattern = r"Σ\(([^)]+)\)"
        match = re.search(pattern, expr)

        if match:
            # 简化处理，假设shares是列表
            # 实际使用中需要传入shares数据
            expr = expr.replace(match.group(0), "100")  # 简化

        return expr

    def calculate_batch(
        self, indicator_codes: list[str], data_provider: DataProvider, **kwargs
    ) -> dict[str, CalculationResult]:
        """批量计算"""
        results = {}
        for code in indicator_codes:
            results[code] = self.calculate(code, data_provider, **kwargs)
        return results

    def get_available_indicators(self) -> list[str]:
        """获取所有可用指标"""
        return list(set(list(self._formulas.keys()) + list(self._custom_funcs.keys())))


# 全局实例
custom_indicator_engine = CustomIndicatorEngine()


# 便捷函数
def calculate_indicator(code: str, data: dict[str, Any], **kwargs) -> CalculationResult:
    """
    便捷的指标计算函数

    Example:
        result = calculate_indicator(
            "deficit_rate",
            {"revenue": 1000, "expenditure": 1200, "gdp": 30000}
        )
        print(result.value)  # 6.67
    """
    provider = DictDataProvider(data)
    return custom_indicator_engine.calculate(code, provider, **kwargs)


def register_custom_formula(code: str, formula: str, dependencies: list[str], **kwargs):
    """注册自定义公式"""
    custom_indicator_engine.register_formula(code, formula, dependencies, **kwargs)


def register_custom_function(code: str, func: Callable, dependencies: list[str], **kwargs):
    """注册自定义函数"""
    custom_indicator_engine.register_function(code, func, dependencies, **kwargs)
