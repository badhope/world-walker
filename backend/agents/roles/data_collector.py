"""
数据采集智能体 - 从官方数据源获取经济数据
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import List, Dict, Any, Optional
import akshare as ak
import pandas as pd
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


DATA_SOURCE_REGISTRY = {
    "gdp": {
        "name": "国内生产总值(GDP)",
        "source": "国家统计局",
        "function": "macro_china_gdp",
        "description": "季度GDP绝对值和增速"
    },
    "gdp_yearly": {
        "name": "年度GDP",
        "source": "国家统计局",
        "function": "macro_china_gdp_yearly",
        "description": "年度GDP数据"
    },
    "cpi": {
        "name": "居民消费价格指数(CPI)",
        "source": "国家统计局",
        "function": "macro_china_cpi_yearly",
        "description": "CPI同比环比数据"
    },
    "cpi_monthly": {
        "name": "月度CPI",
        "source": "国家统计局",
        "function": "macro_china_cpi_monthly",
        "description": "月度CPI详细数据"
    },
    "ppi": {
        "name": "工业生产者出厂价格指数(PPI)",
        "source": "国家统计局",
        "function": "macro_china_ppi_yearly",
        "description": "PPI同比数据"
    },
    "m2": {
        "name": "货币供应量M2",
        "source": "人民银行",
        "function": "macro_china_m2_yearly",
        "description": "M2同比增速"
    },
    "pmi": {
        "name": "官方制造业PMI",
        "source": "国家统计局",
        "function": "macro_china_pmi_yearly",
        "description": "制造业采购经理指数"
    },
    "cx_pmi": {
        "name": "财新PMI",
        "source": "财新传媒",
        "function": "macro_china_cx_pmi_yearly",
        "description": "财新制造业PMI"
    },
    "cx_services_pmi": {
        "name": "财新服务业PMI",
        "source": "财新传媒",
        "function": "macro_china_cx_services_pmi_yearly",
        "description": "财新服务业PMI"
    },
    "lpr": {
        "name": "贷款市场报价利率(LPR)",
        "source": "人民银行",
        "function": "macro_china_lpr",
        "description": "1年期和5年期LPR"
    },
    "rrr": {
        "name": "存款准备金率",
        "source": "人民银行",
        "function": "macro_china_reserve_requirement_ratio",
        "description": "存款准备金率调整历史"
    },
    "shibor": {
        "name": "上海银行间同业拆借利率",
        "source": "上海外汇交易中心",
        "function": "macro_china_shibor_all",
        "description": "SHIBOR各期限利率"
    },
    "export": {
        "name": "出口数据",
        "source": "海关总署",
        "function": "macro_china_exports_yoy",
        "description": "以美元计算出口年率"
    },
    "import": {
        "name": "进口数据",
        "source": "海关总署",
        "function": "macro_china_imports_yoy",
        "description": "以美元计算进口年率"
    },
    "trade": {
        "name": "进出口贸易数据",
        "source": "海关总署",
        "function": "macro_china_hgjck",
        "description": "进出口商品贸易数据"
    },
    "fx_reserves": {
        "name": "外汇储备",
        "source": "人民银行",
        "function": "macro_china_fx_reserves_yearly",
        "description": "外汇储备月度数据"
    },
    "fx_gold": {
        "name": "央行黄金储备",
        "source": "人民银行",
        "function": "macro_china_fx_gold",
        "description": "央行黄金储备"
    },
    "unemployment": {
        "name": "城镇调查失业率",
        "source": "国家统计局",
        "function": "macro_china_urban_unemployment",
        "description": "城镇调查失业率"
    },
    "hk_unemployment": {
        "name": "香港失业率",
        "source": "香港政府统计处",
        "function": "macro_china_hk_rate_of_unemployment",
        "description": "香港失业率"
    },
    "retail": {
        "name": "社会消费品零售总额",
        "source": "国家统计局",
        "function": "macro_china_consumer_goods_retail",
        "description": "零售总额当月累计"
    },
    "industrial_production": {
        "name": "规模以上工业增加值",
        "source": "国家统计局",
        "function": "macro_china_industrial_production_yoy",
        "description": "工业增加值年率"
    },
    "shrzgm": {
        "name": "社会融资规模",
        "source": "人民银行",
        "function": "macro_china_shrzgm",
        "description": "社融增量数据"
    },
    "insurance": {
        "name": "保险业收入",
        "source": "银保监会",
        "function": "macro_china_insurance_income",
        "description": "保险业原保险收入"
    },
    "fdi": {
        "name": "实际使用外资(FDI)",
        "source": "商务部",
        "function": "macro_china_fdi",
        "description": "外国直接投资"
    },
    "freight_bdi": {
        "name": "波罗的海综合运价指数(BDI)",
        "source": "波罗的海交易所",
        "function": "macro_china_freight_index",
        "description": "BDI指数"
    },
    "bdti": {
        "name": "原油运输指数(BDTI)",
        "source": "波罗的海交易所",
        "function": "macro_china_bdti_index",
        "description": "原油运输指数"
    },
    "bsi": {
        "name": "超灵便型船运价指数(BSI)",
        "source": "波罗的海交易所",
        "function": "macro_china_bsi_index",
        "description": "超灵便型船指数"
    },
    "czsr": {
        "name": "财政收入",
        "source": "财政部",
        "function": "macro_china_czsr",
        "description": "全国财政收入"
    },
    "gyzjz": {
        "name": "工业生产者购进价格指数",
        "source": "国家统计局",
        "function": "macro_china_gyzjz",
        "description": "工业生产者购进价格指数"
    },
    "gdzctz": {
        "name": "固定资产投资",
        "source": "国家统计局",
        "function": "macro_china_gdzctz",
        "description": "固定资产投资完成额"
    },
    "consumer_index": {
        "name": "消费者信心指数",
        "source": "国家统计局",
        "function": "macro_china_enterprise_boom_index",
        "description": "企业景气指数"
    },
    "au_report": {
        "name": "黄金市场报告",
        "source": "中国黄金协会",
        "function": "macro_china_au_report",
        "description": "黄金市场数据"
    },
    "bank_financing": {
        "name": "银行理财",
        "source": "银保监会",
        "function": "macro_china_bank_financing",
        "description": "银行理财数据"
    },
    "energy_index": {
        "name": "能源指数",
        "source": "国家能源局",
        "function": "macro_china_energy_index",
        "description": "能源类价格指数"
    },
    "construction_index": {
        "name": "建筑业指数",
        "source": "国家统计局",
        "function": "macro_china_construction_index",
        "description": "建筑业商务活动指数"
    },
}


class DataFetcherTool(BaseTool):
    """数据采集工具 - 支持全部数据源"""

    name: str = "经济数据采集工具"
    description: str = f"""
    从官方数据源采集中国经济数据，支持以下指标:
    {', '.join(DATA_SOURCE_REGISTRY.keys())}
    
    输入: 指标代码字符串，如 'gdp', 'cpi', 'm2', 'pmi' 等
    或输入 'all' 获取所有数据
    或输入 'list' 获取支持的指标列表
    """

    def _run(self, indicator: str) -> str:
        return fetch_economic_data(indicator)


class DataListTool(BaseTool):
    """数据源列表工具"""

    name: str = "数据源列表工具"
    description: str = "获取所有支持的数据源列表"

    def _run(self, query: str = "") -> str:
        return get_data_source_list()


class DataSearchTool(BaseTool):
    """数据搜索工具"""

    name: str = "经济数据搜索工具"
    description: str = """
    搜索已采集的数据，支持按时间范围和指标类型筛选
    输入格式: JSON字符串如 '{"indicator": "gdp", "start_date": "2024", "end_date": "2025"}'
    """

    def _run(self, query: str) -> str:
        try:
            params = json.loads(query)
            result = search_stored_data(params)
            return result
        except Exception as e:
            return f"数据搜索失败: {str(e)}"


def fetch_economic_data(indicator: str) -> str:
    """采集经济数据"""
    indicator = indicator.strip().lower()

    if indicator == "list":
        return get_data_source_list()

    if indicator == "all":
        return fetch_all_data()

    if indicator not in DATA_SOURCE_REGISTRY:
        available = ", ".join(DATA_SOURCE_REGISTRY.keys())
        return f"未知指标: {indicator}\n支持的指标: {available}"

    try:
        config = DATA_SOURCE_REGISTRY[indicator]
        func_name = config["function"]
        
        if not hasattr(ak, func_name):
            return f"数据函数 {func_name} 不可用"

        func = getattr(ak, func_name)
        df = func()

        if df is None or df.empty:
            return f"{config['name']} 暂无数据"

        result = [
            f"📊 {config['name']}",
            f"📍 数据来源: {config['source']}",
            f"📝 {config['description']}",
            "",
            df.tail(10).to_string(index=False)
        ]

        return "\n".join(result)

    except Exception as e:
        logger.error(f"采集 {indicator} 数据失败: {e}")
        return f"采集 {indicator} 数据失败: {str(e)}"


def fetch_all_data() -> str:
    """获取所有数据"""
    results = ["=" * 60, "📊 中国经济数据总览", "=" * 60, ""]
    
    key_indicators = ["gdp", "cpi", "ppi", "m2", "pmi", "lpr", "export", "import", "unemployment", "retail"]
    
    for indicator in key_indicators:
        try:
            if indicator in DATA_SOURCE_REGISTRY:
                config = DATA_SOURCE_REGISTRY[indicator]
                func = getattr(ak, config["function"])
                df = func()
                
                if df is not None and not df.empty:
                    results.append(f"\n📈 {config['name']} ({indicator})")
                    results.append("-" * 40)
                    results.append(df.tail(5).to_string(index=False))
        except Exception as e:
            results.append(f"\n⚠️  {indicator} 获取失败: {str(e)[:50]}")

    return "\n".join(results)


def get_data_source_list() -> str:
    """获取数据源列表"""
    lines = [
        "=" * 60,
        "📊 支持的经济数据指标列表",
        "=" * 60,
        ""
    ]

    for code, config in DATA_SOURCE_REGISTRY.items():
        lines.append(f"【{code}】 {config['name']}")
        lines.append(f"   来源: {config['source']}")
        lines.append(f"   说明: {config['description']}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"总计: {len(DATA_SOURCE_REGISTRY)} 个数据源")
    lines.append("=" * 60)

    return "\n".join(lines)


def search_stored_data(params: Dict[str, Any]) -> str:
    """搜索数据"""
    return f"搜索条件: {json.dumps(params, ensure_ascii=False)}"


class DataCollectorAgent:
    """数据采集智能体"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [
            DataFetcherTool(),
            DataListTool(),
            DataSearchTool(),
        ]

    def create_agent(self) -> Agent:
        """创建数据采集智能体"""
        return Agent(
            role="数据采集专家",
            goal="准确、高效地从官方数据源获取最新经济数据",
            backstory=f"""
            你是一位专业的数据采集专家，专注于中国经济数据的获取。
            你熟悉国家统计局、人民银行、海关总署等官方数据接口。
            
            支持的数据源 ({len(DATA_SOURCE_REGISTRY)} 个):
            - GDP、CPI、PPI、PMI
            - M2、LPR、SHIBOR
            - 进出口贸易数据
            - 外汇储备、黄金储备
            - 失业率、消费数据
            - 工业生产、投资数据
            - 航运指数等
            
            能够根据需求快速定位和获取所需的宏观经济指标数据。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )

    @staticmethod
    def get_available_indicators() -> List[str]:
        """获取支持的指标列表"""
        return list(DATA_SOURCE_REGISTRY.keys())

    @staticmethod
    def get_data_source_registry() -> Dict[str, Dict[str, str]]:
        """获取数据源注册表"""
        return DATA_SOURCE_REGISTRY
