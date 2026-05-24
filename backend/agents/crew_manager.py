"""
Crew 管理器 - 管理多智能体协作工作流

支持两种 LLM 模式:
1. OpenAI (在线)
2. Ollama (本地离线)
"""
from crewai import Crew, Process, Agent, Task
from crewai.llm import LLM
from typing import Dict, Any, List, Optional, Literal
import logging
import os

from .roles.data_collector import DataCollectorAgent
from .roles.analyst import AnalystAgent
from .roles.visualizer import VisualizerAgent
from .roles.report_writer import ReportWriterAgent
from .roles.verification import VerificationAgent
from .roles.comparison import ComparisonAgent

logger = logging.getLogger(__name__)


LLMProvider = Literal["openai", "ollama", "lmstudio"]


def create_llm(
    provider: LLMProvider = "openai",
    model: str = "gpt-4",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
) -> LLM:
    """
    创建 LLM 实例

    Args:
        provider: LLM 提供商
            - "openai": OpenAI API (默认 gpt-4)
            - "ollama": Ollama 本地模型 (默认 llama3.2)
            - "lmstudio": LM Studio 本地模型
        model: 模型名称
        base_url: API 基础地址 (Ollama/LM Studio 本地部署时需要)
        api_key: API Key (OpenAI 需要)
        temperature: 温度参数
    """
    if provider == "ollama":
        base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        model = model or os.environ.get("OLLAMA_MODEL", "llama3.2")
        logger.info(f"使用 Ollama 本地模型: {model} @ {base_url}")
        return LLM(
            model=f"ollama/{model}",
            base_url=base_url,
            temperature=temperature,
        )

    elif provider == "lmstudio":
        base_url = base_url or os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = model or os.environ.get("LMSTUDIO_MODEL", "local-model")
        logger.info(f"使用 LM Studio 本地模型: {model} @ {base_url}")
        return LLM(
            model=model,
            base_url=base_url,
            api_key="lm-studio",
            temperature=temperature,
        )

    else:
        api_key = api_key or os.environ.get("OPENAI_API_KEY", "dummy")
        model = model or os.environ.get("OPENAI_MODEL", "gpt-4")
        logger.info(f"使用 OpenAI 模型: {model}")
        return LLM(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )


class EconomicAnalysisCrew:
    """经济分析 Crew - 多智能体协作完成经济分析"""

    def __init__(
        self,
        llm: Optional[LLM] = None,
        provider: LLMProvider = "auto",
        **llm_kwargs,
    ):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm

        self.data_collector = DataCollectorAgent(llm=self.llm).create_agent()
        self.analyst = AnalystAgent(llm=self.llm).create_agent()
        self.visualizer = VisualizerAgent(llm=self.llm).create_agent()
        self.report_writer = ReportWriterAgent(llm=self.llm).create_agent()

        self.crew = None

    def setup_crew(self) -> Crew:
        """设置 Crew"""
        self.crew = Crew(
            agents=[
                self.data_collector,
                self.analyst,
                self.visualizer,
                self.report_writer,
            ],
            tasks=self._create_tasks(),
            process=Process.hierarchical,
            manager_llm=self.llm,
            verbose=True,
        )
        return self.crew

    def _create_tasks(self) -> List[Task]:
        """创建任务列表"""
        tasks = [
            Task(
                description="采集中国最新GDP、CPI、M2、PMI等宏观经济指标数据",
                agent=self.data_collector,
                expected_output="包含各指标最新值和近期变化趋势的数据汇总",
            ),
            Task(
                description="基于采集的数据计算衍生指标（赤字率、贸易顺差等），运行经济学模型分析",
                agent=self.analyst,
                expected_output="详细的经济分析结果，包括关键发现和趋势判断",
            ),
            Task(
                description="为分析结果生成配套的可视化图表",
                agent=self.visualizer,
                expected_output="HTML格式的图表，包含时间序列图、对比分析图等",
            ),
            Task(
                description="整合数据和洞察，生成结构化的经济分析报告",
                agent=self.report_writer,
                expected_output="Markdown格式的完整分析报告，包含摘要、发现和建议",
            ),
        ]
        return tasks

    def kickoff(self, topic: str = "当前宏观经济形势分析") -> Dict[str, Any]:
        """启动分析流程"""
        if not self.crew:
            self.setup_crew()

        result = self.crew.kickoff(inputs={"topic": topic})

        return {
            "status": "completed",
            "result": result,
        }


class DataCollectionCrew:
    """数据采集 Crew - 专注数据采集任务"""

    def __init__(self, llm: Optional[LLM] = None, provider: LLMProvider = "auto", **llm_kwargs):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.collector = DataCollectorAgent(llm=self.llm).create_agent()

    def run(self, indicators: List[str]) -> Dict[str, Any]:
        """运行数据采集"""
        indicator_str = ", ".join(indicators)
        task = Task(
            description=f"采集以下经济指标数据: {indicator_str}",
            agent=self.collector,
            expected_output="各指标的详细数据",
        )

        crew = Crew(agents=[self.collector], tasks=[task], verbose=True)
        result = crew.kickoff()

        return {
            "status": "completed",
            "indicators": indicators,
            "result": str(result),
        }


class AnalysisCrew:
    """分析 Crew - 专注分析任务"""

    def __init__(self, llm: Optional[LLM] = None, provider: LLMProvider = "auto", **llm_kwargs):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.analyst = AnalystAgent(llm=self.llm).create_agent()

    def run(self, data: Dict[str, Any], analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """运行经济分析"""
        task = Task(
            description=f"对以下数据进行{analysis_type}分析: {data}",
            agent=self.analyst,
            expected_output="详细的经济分析结果",
        )

        crew = Crew(agents=[self.analyst], tasks=[task], verbose=True)
        result = crew.kickoff()

        return {
            "status": "completed",
            "analysis_type": analysis_type,
            "result": str(result),
        }


class VisualizationCrew:
    """可视化 Crew - 专注图表生成"""

    def __init__(self, llm: Optional[LLM] = None, provider: LLMProvider = "auto", **llm_kwargs):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.visualizer = VisualizerAgent(llm=self.llm).create_agent()

    def run(self, data: Dict[str, Any], chart_types: List[str]) -> Dict[str, Any]:
        """生成可视化图表"""
        chart_str = ", ".join(chart_types)
        task = Task(
            description=f"为以下数据生成{chart_str}图表: {data}",
            agent=self.visualizer,
            expected_output="HTML格式的图表",
        )

        crew = Crew(agents=[self.visualizer], tasks=[task], verbose=True)
        result = crew.kickoff()

        return {
            "status": "completed",
            "charts": chart_types,
            "result": str(result),
        }


class ReportCrew:
    """报告生成 Crew - 专注报告撰写"""

    def __init__(self, llm: Optional[LLM] = None, provider: LLMProvider = "auto", **llm_kwargs):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.report_writer = ReportWriterAgent(llm=self.llm).create_agent()

    def run(
        self,
        analysis_results: Dict[str, Any],
        data_summary: Dict[str, Any],
        insights: List[str]
    ) -> Dict[str, Any]:
        """生成分析报告"""
        task = Task(
            description="根据分析结果和数据汇总生成经济分析报告",
            agent=self.report_writer,
            expected_output="Markdown格式的完整报告",
        )

        crew = Crew(agents=[self.report_writer], tasks=[task], verbose=True)
        result = crew.kickoff(
            inputs={
                "analysis_results": analysis_results,
                "data_summary": data_summary,
                "insights": insights,
            }
        )

        return {
            "status": "completed",
            "report": str(result),
        }


class VerificationCrew:
    """数据验证 Crew - 数据一致性和异常检测"""

    def __init__(self, llm: Optional[LLM] = None, provider: LLMProvider = "auto", **llm_kwargs):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.verifier = VerificationAgent(llm=self.llm).create_agent()

    def run_consistency_check(self, indicator: str, tolerance: float = 0.05) -> Dict[str, Any]:
        """运行一致性检查"""
        from .roles.verification import check_data_consistency
        result = check_data_consistency(indicator, tolerance)
        return {
            "status": "completed",
            "indicator": indicator,
            "result": result,
        }

    def run_cross_validation(self, indicator: str) -> Dict[str, Any]:
        """运行交叉验证"""
        from .roles.verification import cross_validate_indicator
        result = cross_validate_indicator(indicator)
        return {
            "status": "completed",
            "indicator": indicator,
            "result": result,
        }

    def run_anomaly_detection(self, data: List[float], method: str = "zscore") -> Dict[str, Any]:
        """运行异常检测"""
        from .roles.verification import detect_anomalies
        result = detect_anomalies(data, method)
        return {
            "status": "completed",
            "result": result,
        }

    def compare_reports(self, report1: Dict, report2: Dict) -> Dict[str, Any]:
        """对比两份报告"""
        from .roles.verification import compare_reports
        result = compare_reports(report1, report2)
        return {
            "status": "completed",
            "result": result,
        }


class ComparisonCrew:
    """对比分析 Crew - 省际和历史对比"""

    def __init__(self, llm: Optional[LLM] = None, provider: LLMProvider = "auto", **llm_kwargs):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.comparator = ComparisonAgent(llm=self.llm).create_agent()

    def run_province_comparison(self, indicator: str, top_n: int = 10) -> Dict[str, Any]:
        """运行省际对比"""
        from .roles.comparison import compare_provinces
        result = compare_provinces(indicator, top_n)
        return {
            "status": "completed",
            "indicator": indicator,
            "result": result,
        }

    def run_trend_analysis(self, indicator: str) -> Dict[str, Any]:
        """运行趋势分析"""
        from .roles.comparison import analyze_trend
        result = analyze_trend(indicator)
        return {
            "status": "completed",
            "indicator": indicator,
            "result": result,
        }

    def run_structure_comparison(self, compare_type: str, years: List[int]) -> Dict[str, Any]:
        """运行结构对比"""
        from .roles.comparison import compare_structure
        result = compare_structure(compare_type, years)
        return {
            "status": "completed",
            "type": compare_type,
            "years": years,
            "result": result,
        }


class CrewManager:
    """Crew 管理器 - 统一管理所有 Crew"""

    def __init__(
        self,
        llm: Optional[LLM] = None,
        provider: LLMProvider = "auto",
        **llm_kwargs,
    ):
        if llm is None:
            llm = create_llm(provider=provider, **llm_kwargs)
        self.llm = llm
        self.provider = provider

        self.economic_analysis_crew = EconomicAnalysisCrew(llm=self.llm)
        self.data_collection_crew = DataCollectionCrew(llm=self.llm)
        self.analysis_crew = AnalysisCrew(llm=self.llm)
        self.visualization_crew = VisualizationCrew(llm=self.llm)
        self.report_crew = ReportCrew(llm=self.llm)
        self.verification_crew = VerificationCrew(llm=self.llm)
        self.comparison_crew = ComparisonCrew(llm=self.llm)

    def run_full_analysis(
        self,
        indicators: Optional[List[str]] = None,
        topic: str = "当前宏观经济形势分析"
    ) -> Dict[str, Any]:
        """运行完整的经济分析流程"""
        logger.info(f"启动完整经济分析 (provider={self.provider}): {topic}")

        try:
            result = self.economic_analysis_crew.kickoff(topic=topic)
            return {
                "status": "success",
                "crew": "EconomicAnalysisCrew",
                "provider": self.provider,
                "result": result,
            }
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def run_data_collection(self, indicators: List[str]) -> Dict[str, Any]:
        """仅运行数据采集"""
        return self.data_collection_crew.run(indicators)

    def run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """仅运行分析"""
        return self.analysis_crew.run(data)

    def run_visualization(self, data: Dict[str, Any], charts: List[str]) -> Dict[str, Any]:
        """仅生成可视化"""
        return self.visualization_crew.run(data, charts)

    def run_report(
        self,
        analysis: Dict[str, Any],
        data_summary: Dict[str, Any],
        insights: List[str]
    ) -> Dict[str, Any]:
        """仅生成报告"""
        return self.report_crew.run(analysis, data_summary, insights)
