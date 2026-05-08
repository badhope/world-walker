"""
Agent 角色定义
"""
from .data_collector import DataCollectorAgent
from .analyst import AnalystAgent
from .visualizer import VisualizerAgent
from .report_writer import ReportWriterAgent

__all__ = [
    "DataCollectorAgent",
    "AnalystAgent",
    "VisualizerAgent",
    "ReportWriterAgent",
]
