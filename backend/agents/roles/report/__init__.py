"""
报告生成模块
"""
from .report_generator import (
    EconomicReportGenerator,
    generate_economic_report,
    generate_and_save_report,
)

__all__ = [
    "EconomicReportGenerator",
    "generate_economic_report",
    "generate_and_save_report",
]
