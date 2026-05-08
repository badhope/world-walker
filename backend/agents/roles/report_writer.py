"""
报告撰写智能体 - 生成经济分析报告
"""
from crewai import Agent
from crewai.tools import BaseTool
from crewai.llm import LLM
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportGeneratorTool(BaseTool):
    """报告生成工具"""

    name: str = "经济报告生成工具"
    description: str = """
    生成结构化的经济分析报告，包含：
    - 执行摘要
    - 数据概览
    - 关键发现
    - 趋势分析
    - 政策建议
    输入格式：JSON字符串包含 analysis_results, data_summary, insights 等字段
    """

    def _run(self, request: str) -> str:
        import json
        try:
            data = json.loads(request)
            report = generate_economic_report(
                data.get("analysis_results", {}),
                data.get("data_summary", {}),
                data.get("insights", [])
            )
            return report
        except Exception as e:
            return f"报告生成失败: {str(e)}"


class SummaryTool(BaseTool):
    """摘要生成工具"""

    name: str = "分析摘要工具"
    description: str = """
    生成简短的分析摘要，用于快速了解关键结论
    输入：关键发现列表或分析结果
    """

    def _run(self, findings: str) -> str:
        return generate_summary(findings)


def generate_economic_report(
    analysis: Dict[str, Any],
    data_summary: Dict[str, Any],
    insights: List[str]
) -> str:
    """生成经济分析报告"""
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    report = f"""
# 📊 经济数据分析报告

**生成时间**: {timestamp}

---

## 📋 执行摘要

本报告基于最新宏观经济数据，对当前经济形势进行了综合分析。

**核心发现**:
{chr(10).join(f"- {insight}" for insight in insights[:3]) if insights else "- 数据正在收集中..."}

---

## 📈 数据概览

| 指标 | 最新值 | 同比变化 |
|------|--------|----------|
"""
    for key, value in data_summary.items():
        if isinstance(value, dict):
            report += f"| {value.get('name', key)} | {value.get('value', 'N/A')} | {value.get('change', 'N/A')} |\n"
        else:
            report += f"| {key} | {value} | N/A |\n"

    report += f"""
---

## 🔍 关键发现

{chr(10).join(f"### {i+1}. {insight}" for i, insight in enumerate(insights)) if insights else "正在分析中..."}

---

## 📊 详细分析

"""
    for key, value in analysis.items():
        if isinstance(value, dict):
            report += f"### {value.get('title', key)}\n\n"
            report += f"{value.get('content', str(value))}\n\n"
        else:
            report += f"### {key}\n\n{value}\n\n"

    report += f"""
---

## 💡 政策建议

1. **稳健货币政策**: 保持流动性合理充裕
2. **积极财政政策**: 加大民生投入力度
3. **结构性改革**: 推动产业升级转型

---

## ⚠️ 风险提示

本报告仅供研究参考，不构成投资建议。经济形势复杂多变，请结合实际情况判断。

---

*报告由 NEDAP AI 分析系统自动生成*
"""

    return report


def generate_summary(findings: str) -> str:
    """生成摘要"""
    lines = findings.strip().split("\n")
    if len(lines) <= 3:
        return findings

    summary = ["## 📌 核心摘要", ""]
    summary.append(lines[0] if lines else "无关键发现")

    if len(lines) > 1:
        summary.append("")
        summary.append("**次要发现**:")
        for line in lines[1:4]:
            if line.strip():
                summary.append(f"- {line.strip()}")

    return "\n".join(summary)


class ReportWriterAgent:
    """报告撰写智能体"""

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.tools = [ReportGeneratorTool(), SummaryTool()]

    def create_agent(self) -> Agent:
        """创建报告撰写智能体"""
        return Agent(
            role="经济报告撰写专家",
            goal="将分析结果转化为清晰、专业的经济分析报告",
            backstory="""
            你是一位专业财经记者和经济报告撰写人，
            擅长将复杂的 经济分析结果转化为通俗易懂的专业报告。
            你的报告结构清晰、逻辑严谨、用词精准，
            深受决策者和投资者信赖。
            """,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )

    @staticmethod
    def get_report_templates() -> List[str]:
        """获取报告模板"""
        return ["comprehensive", "summary", "policy_brief", "investor"]
