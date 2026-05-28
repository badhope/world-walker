"""
经济指标推演引擎 - 真正的经济学模型
"""
import numpy as np
from typing import Dict, Tuple, Optional, Any
from scipy import stats
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """推演结果"""
    value: float
    unit: str
    confidence_interval: Tuple[float, float]
    method: str
    r_squared: Optional[float] = None
    formula: Optional[str] = None
    description: Optional[str] = None


# ==================== 指标关系定义 ====================
# 基于经济学理论的指标推演关系

INDICATOR_RELATIONS = {
    # 财政类
    "fiscal_deficit": {
        "name": "财政赤字",
        "formula": lambda x: x.get("expenditure", 0) - x.get("revenue", 0),
        "unit": "亿元",
        "required": ["expenditure", "revenue"],
        "description": "财政赤字 = 财政支出 - 财政收入",
        "category": "fiscal"
    },
    "deficit_rate": {
        "name": "赤字率",
        "formula": lambda x: (x.get("expenditure", 0) - x.get("revenue", 0)) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["expenditure", "revenue", "gdp"],
        "description": "赤字率 = 财政赤字 / GDP × 100%",
        "category": "fiscal"
    },
    "tax_ratio": {
        "name": "宏观税负",
        "formula": lambda x: x.get("tax_revenue", 0) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["tax_revenue", "gdp"],
        "description": "宏观税负 = 税收收入 / GDP × 100%",
        "category": "fiscal"
    },
    "fiscal_self_sufficiency": {
        "name": "财政自给率",
        "formula": lambda x: x.get("revenue", 0) / x.get("expenditure", 1) * 100,
        "unit": "%",
        "required": ["revenue", "expenditure"],
        "description": "财政自给率 = 财政收入 / 财政支出 × 100%",
        "category": "fiscal"
    },
    
    # 产业结构类
    "primary_ratio": {
        "name": "第一产业占比",
        "formula": lambda x: x.get("primary_industry", 0) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["primary_industry", "gdp"],
        "description": "第一产业增加值占GDP比重",
        "category": "industry"
    },
    "secondary_ratio": {
        "name": "第二产业占比",
        "formula": lambda x: x.get("secondary_industry", 0) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["secondary_industry", "gdp"],
        "description": "第二产业增加值占GDP比重",
        "category": "industry"
    },
    "tertiary_ratio": {
        "name": "第三产业占比",
        "formula": lambda x: x.get("tertiary_industry", 0) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["tertiary_industry", "gdp"],
        "description": "第三产业增加值占GDP比重",
        "category": "industry"
    },
    
    # 收入分配类
    "urban_rural_gap": {
        "name": "城乡收入差距",
        "formula": lambda x: x.get("urban_income", 0) / x.get("rural_income", 1),
        "unit": "倍",
        "required": ["urban_income", "rural_income"],
        "description": "城镇人均可支配收入 / 农村人均可支配收入",
        "category": "income"
    },
    "consumption_rate": {
        "name": "消费率",
        "formula": lambda x: x.get("consumption", 0) / x.get("disposable_income", 1) * 100,
        "unit": "%",
        "required": ["consumption", "disposable_income"],
        "description": "消费率 = 居民消费支出 / 可支配收入 × 100%",
        "category": "income"
    },
    "savings_rate": {
        "name": "储蓄率",
        "formula": lambda x: 100 - x.get("consumption_rate", 50),
        "unit": "%",
        "required": ["consumption_rate"],
        "description": "储蓄率 = 100% - 消费率",
        "category": "income"
    },
    
    # 金融类
    "m2_growth_contribution": {
        "name": "M2对GDP贡献",
        "formula": lambda x: x.get("gdp_growth", 0) / x.get("m2_growth", 1) if x.get("m2_growth", 0) != 0 else 0,
        "unit": "",
        "required": ["gdp_growth", "m2_growth"],
        "description": "GDP增速 / M2增速，衡量货币效率",
        "category": "financial"
    },
    
    # 贸易类
    "trade_balance": {
        "name": "贸易顺差",
        "formula": lambda x: x.get("export", 0) - x.get("import", 0),
        "unit": "亿美元",
        "required": ["export", "import"],
        "description": "贸易顺差 = 出口 - 进口",
        "category": "trade"
    },
    "trade_dependence": {
        "name": "贸易依存度",
        "formula": lambda x: (x.get("export", 0) + x.get("import", 0)) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["export", "import", "gdp"],
        "description": "贸易依存度 = (出口+进口) / GDP × 100%",
        "category": "trade"
    },
    
    # 创新类
    "rd_intensity": {
        "name": "R&D强度",
        "formula": lambda x: x.get("rd_expenditure", 0) / x.get("gdp", 1) * 100,
        "unit": "%",
        "required": ["rd_expenditure", "gdp"],
        "description": "R&D强度 = 研发支出 / GDP × 100%",
        "category": "innovation"
    },
}


class InferenceEngine:
    """推演引擎"""
    
    def __init__(self):
        self.relations = INDICATOR_RELATIONS
    
    def list_available_indicators(self) -> Dict[str, Any]:
        """列出所有可推演指标"""
        return {
            "indicators": {
                code: {
                    "name": config["name"],
                    "unit": config["unit"],
                    "required": config["required"],
                    "description": config["description"],
                    "category": config["category"]
                }
                for code, config in self.relations.items()
            },
            "total": len(self.relations)
        }
    
    def calculate(
        self,
        target: str,
        inputs: Dict[str, float],
        method: str = "linear",
        confidence_level: float = 0.95
    ) -> InferenceResult:
        """
        计算推演结果
        
        Args:
            target: 目标指标代码
            inputs: 输入指标字典
            method: 计算方法 (linear, monte_carlo)
            confidence_level: 置信水平
        
        Returns:
            InferenceResult
        """
        if target not in self.relations:
            raise ValueError(f"未知指标: {target}，可用指标: {list(self.relations.keys())}")
        
        config = self.relations[target]
        
        # 检查必需字段
        missing = [f for f in config["required"] if f not in inputs]
        if missing:
            raise ValueError(f"缺少必需字段: {missing}")
        
        # 计算基础值
        base_value = config["formula"](inputs)
        
        # 根据方法计算置信区间
        if method == "monte_carlo":
            # 蒙特卡洛模拟
            ci, r2 = self._monte_carlo_simulation(
                config["formula"], inputs, confidence_level
            )
        else:
            # 线性方法：基于输入不确定性传播
            ci, r2 = self._linear_uncertainty(
                base_value, inputs, confidence_level
            )
        
        return InferenceResult(
            value=round(base_value, 4),
            unit=config["unit"],
            confidence_interval=(round(ci[0], 4), round(ci[1], 4)),
            method=method,
            r_squared=r2,
            formula=config["description"],
            description=config["name"]
        )
    
    def _linear_uncertainty(
        self,
        value: float,
        inputs: Dict[str, float],
        confidence_level: float
    ) -> Tuple[Tuple[float, float], float]:
        """线性不确定性传播"""
        # 假设每个输入有5%的相对不确定性
        uncertainties = {k: abs(v) * 0.05 for k, v in inputs.items()}
        
        # 总不确定性（简化：取最大相对误差）
        if value != 0:
            relative_error = max(uncertainties.values()) / abs(value) if uncertainties else 0.05
        else:
            relative_error = 0.05
        
        # 置信区间
        z = stats.norm.ppf((1 + confidence_level) / 2)
        margin = abs(value) * relative_error * z
        
        return (value - margin, value + margin), 1.0  # 公式计算 R²=1
    
    def _monte_carlo_simulation(
        self,
        formula,
        inputs: Dict[str, float],
        confidence_level: float,
        n_simulations: int = 10000
    ) -> Tuple[Tuple[float, float], float]:
        """蒙特卡洛模拟"""
        results = []
        
        for _ in range(n_simulations):
            # 对每个输入添加随机扰动（假设正态分布，5%标准差）
            perturbed = {
                k: v * (1 + np.random.normal(0, 0.05))
                for k, v in inputs.items()
            }
            try:
                results.append(formula(perturbed))
            except Exception:
                continue
        
        if not results:
            return (0, 0), 0
        
        results = np.array(results)
        
        # 置信区间
        lower = np.percentile(results, (1 - confidence_level) / 2 * 100)
        upper = np.percentile(results, (1 + confidence_level) / 2 * 100)
        
        # R² 基于模拟结果的方差
        variance_explained = 1 - np.var(results) / (np.mean(results) ** 2) if np.mean(results) != 0 else 0
        
        return (lower, upper), max(0, min(1, variance_explained))
    
    def infer_all(
        self,
        inputs: Dict[str, float],
        method: str = "linear"
    ) -> Dict[str, Any]:
        """推演所有可计算的指标"""
        results = {}
        
        for code, config in self.relations.items():
            missing = [f for f in config["required"] if f not in inputs]
            
            if not missing:
                try:
                    result = self.calculate(code, inputs, method)
                    results[code] = {
                        "name": config["name"],
                        "value": result.value,
                        "unit": result.unit,
                        "confidence_interval": result.confidence_interval,
                        "method": method,
                        "status": "success"
                    }
                except Exception as e:
                    results[code] = {
                        "name": config["name"],
                        "status": "error",
                        "error": str(e)
                    }
            else:
                results[code] = {
                    "name": config["name"],
                    "status": "insufficient_data",
                    "missing": missing
                }
        
        return {
            "input_count": len(inputs),
            "output_count": sum(1 for r in results.values() if r.get("status") == "success"),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }


# ==================== 经济学模型 ====================

class EconomicModels:
    """经典经济学模型"""
    
    @staticmethod
    def phillips_curve(
        unemployment: float,
        natural_unemployment: float = 5.0,
        expected_inflation: float = 2.0,
        beta: float = 0.5
    ) -> Dict[str, Any]:
        """
        菲利普斯曲线: π = πₑ - β(u - u*)
        
        Args:
            unemployment: 实际失业率
            natural_unemployment: 自然失业率
            expected_inflation: 预期通胀率
            beta: 敏感系数
        """
        inflation = expected_inflation - beta * (unemployment - natural_unemployment)
        
        return {
            "model": "Phillips Curve",
            "formula": "π = πₑ - β(u - u*)",
            "inputs": {
                "unemployment": unemployment,
                "natural_unemployment": natural_unemployment,
                "expected_inflation": expected_inflation,
                "beta": beta
            },
            "output": {
                "inflation": round(inflation, 4),
                "unit": "%"
            },
            "interpretation": f"当失业率为 {unemployment}% 时，预期通胀率为 {inflation:.2f}%"
        }
    
    @staticmethod
    def okun_law(
        gdp_growth: float,
        potential_growth: float = 6.0,
        okun_coefficient: float = 2.0
    ) -> Dict[str, Any]:
        """
        奥肯定律: (Y - Y*)/Y* = -β(u - u*)
        
        Args:
            gdp_growth: 实际GDP增速
            potential_growth: 潜在GDP增速
            okun_coefficient: 奥肯系数
        """
        output_gap = gdp_growth - potential_growth
        unemployment_change = -output_gap / okun_coefficient
        
        return {
            "model": "Okun's Law",
            "formula": "(Y - Y*)/Y* = -β(u - u*)",
            "inputs": {
                "gdp_growth": gdp_growth,
                "potential_growth": potential_growth,
                "okun_coefficient": okun_coefficient
            },
            "output": {
                "output_gap": round(output_gap, 4),
                "unemployment_change": round(unemployment_change, 4),
                "unit": "%"
            },
            "interpretation": f"GDP增速低于潜在增速 {abs(output_gap):.2f}%，失业率预计上升 {abs(unemployment_change):.2f}%"
        }
    
    @staticmethod
    def cobb_douglas(
        capital: float,
        labor: float,
        alpha: float = 0.3,
        technology: float = 1.0
    ) -> Dict[str, Any]:
        """
        柯布-道格拉斯生产函数: Y = A × K^α × L^(1-α)
        
        Args:
            capital: 资本存量
            labor: 劳动力
            alpha: 资本产出弹性
            technology: 技术水平
        """
        output = technology * (capital ** alpha) * (labor ** (1 - alpha))
        
        # 边际产出
        mpk = alpha * output / capital  # 资本边际产出
        mpl = (1 - alpha) * output / labor  # 劳动边际产出
        
        return {
            "model": "Cobb-Douglas Production Function",
            "formula": "Y = A × K^α × L^(1-α)",
            "inputs": {
                "capital": capital,
                "labor": labor,
                "alpha": alpha,
                "technology": technology
            },
            "output": {
                "output": round(output, 4),
                "marginal_product_capital": round(mpk, 4),
                "marginal_product_labor": round(mpl, 4),
                "returns_to_scale": "constant"  # 规模报酬不变
            },
            "interpretation": f"产出 Y = {output:.2f}，资本边际产出 = {mpk:.4f}，劳动边际产出 = {mpl:.4f}"
        }
    
    @staticmethod
    def solow_growth(
        savings_rate: float,
        population_growth: float,
        depreciation: float,
        alpha: float = 0.3,
        technology: float = 1.0
    ) -> Dict[str, Any]:
        """
        索洛增长模型稳态
        
        Args:
            savings_rate: 储蓄率
            population_growth: 人口增长率
            depreciation: 折旧率
            alpha: 资本份额
            technology: 技术水平
        """
        # 稳态人均资本
        k_star = (savings_rate / (population_growth + depreciation)) ** (1 / (1 - alpha))
        
        # 稳态人均产出
        y_star = technology * (k_star ** alpha)
        
        # 黄金律储蓄率
        s_golden = alpha * (population_growth + depreciation) / (population_growth + depreciation)
        
        return {
            "model": "Solow Growth Model",
            "formula": "k* = (s/(n+δ))^(1/(1-α))",
            "inputs": {
                "savings_rate": savings_rate,
                "population_growth": population_growth,
                "depreciation": depreciation,
                "alpha": alpha
            },
            "output": {
                "steady_state_capital_per_worker": round(k_star, 4),
                "steady_state_output_per_worker": round(y_star, 4),
                "golden_rule_savings_rate": round(s_golden, 4)
            },
            "interpretation": f"稳态人均资本 = {k_star:.4f}，稳态人均产出 = {y_star:.4f}"
        }


# 单例
inference_engine = InferenceEngine()
economic_models = EconomicModels()
