"""
灵活的报告生成系统
支持多种输出格式和自定义模板
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """输出格式"""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class ReportSection:
    """报告章节"""

    title: str
    content: Any
    visualization: str | None = None
    order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportConfig:
    """报告配置"""

    title: str
    subtitle: str | None = None
    author: str = "System"
    format: OutputFormat = OutputFormat.JSON
    template: str | None = None
    include_toc: bool = True
    include_summary: bool = True
    include_metadata: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseReportGenerator(ABC):
    """报告生成器基类"""

    def __init__(self, config: ReportConfig):
        self.config = config

    @abstractmethod
    def generate(self, sections: list[ReportSection]) -> str:
        """生成报告"""
        pass

    @abstractmethod
    def save(self, content: str, filepath: str) -> bool:
        """保存报告"""
        pass


class JSONReportGenerator(BaseReportGenerator):
    """JSON报告生成器"""

    def generate(self, sections: list[ReportSection]) -> str:
        report_data = {
            "title": self.config.title,
            "subtitle": self.config.subtitle,
            "author": self.config.author,
            "generated_at": datetime.now().isoformat(),
            "sections": [],
        }

        for section in sorted(sections, key=lambda s: s.order):
            report_data["sections"].append(
                {
                    "title": section.title,
                    "content": section.content,
                    "visualization": section.visualization,
                    "metadata": section.metadata,
                }
            )

        return json.dumps(report_data, ensure_ascii=False, indent=2)

    def save(self, content: str, filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"保存JSON报告失败: {e}")
            return False


class MarkdownReportGenerator(BaseReportGenerator):
    """Markdown报告生成器"""

    def generate(self, sections: list[ReportSection]) -> str:
        lines = [f"# {self.config.title}", ""]

        if self.config.subtitle:
            lines.append(f"**{self.config.subtitle}**")
            lines.append("")

        if self.config.include_metadata:
            lines.extend(
                [
                    f"- **作者**: {self.config.author}",
                    f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "",
                ]
            )

        if self.config.include_toc and len(sections) > 1:
            lines.append("## 目录")
            lines.append("")
            for i, section in enumerate(sorted(sections, key=lambda s: s.order), 1):
                lines.append(f"{i}. [{section.title}](#{section.title.lower().replace(' ', '-')})")
            lines.append("")

        for section in sorted(sections, key=lambda s: s.order):
            lines.extend([f"## {section.title}", "", self._format_content(section.content), ""])

            if section.visualization:
                lines.append(f"*图表类型: {section.visualization}*")
                lines.append("")

        return "\n".join(lines)

    def _format_content(self, content: Any) -> str:
        """格式化内容"""
        if isinstance(content, dict):
            return self._format_dict(content)
        elif isinstance(content, list):
            return self._format_list(content)
        elif isinstance(content, str):
            return content
        else:
            return str(content)

    def _format_dict(self, data: dict) -> str:
        """格式化字典"""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict | list):
                lines.append(f"**{key}**: ")
                lines.append(self._format_content(value))
            else:
                lines.append(f"**{key}**: {value}")
        return "\n".join(lines)

    def _format_list(self, data: list) -> str:
        """格式化列表"""
        lines = []
        for item in data:
            lines.append(f"- {self._format_content(item)}")
        return "\n".join(lines)

    def save(self, content: str, filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"保存Markdown报告失败: {e}")
            return False


class HTMLReportGenerator(BaseReportGenerator):
    """HTML报告生成器"""

    def __init__(self, config: ReportConfig):
        super().__init__(config)
        self._css = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }
            h1 { color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
            h2 { color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }
            .metadata { color: #666; font-size: 0.9em; background: #f8f9fa; padding: 10px; border-radius: 5px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background: #667eea; color: white; }
            tr:nth-child(even) { background: #f8f9fa; }
            .kpi { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
            .kpi-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                       padding: 20px; border-radius: 10px; text-align: center; }
            .kpi-value { font-size: 2em; font-weight: bold; }
            .kpi-label { font-size: 0.9em; opacity: 0.9; }
            .insight { background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px; margin: 10px 0; }
            .warning { background: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; }
        </style>
        """

    def generate(self, sections: list[ReportSection]) -> str:
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            f"<title>{self.config.title}</title>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            self._css,
            "</head>",
            "<body>",
            f"<h1>{self.config.title}</h1>",
        ]

        if self.config.subtitle:
            html_parts.append(f"<p class='subtitle'><em>{self.config.subtitle}</em></p>")

        if self.config.include_metadata:
            html_parts.extend(
                [
                    "<div class='metadata'>",
                    f"<p><strong>作者</strong>: {self.config.author} | "
                    f"<strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
                    "</div>",
                ]
            )

        for section in sorted(sections, key=lambda s: s.order):
            html_parts.extend([f"<h2>{section.title}</h2>", self._format_content(section.content)])

        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    def _format_content(self, content: Any) -> str:
        """格式化内容"""
        if isinstance(content, dict):
            return self._format_dict(content)
        elif isinstance(content, list):
            return self._format_list(content)
        elif isinstance(content, str):
            return f"<p>{content}</p>"
        else:
            return f"<p>{content}</p>"

    def _format_dict(self, data: dict) -> str:
        """格式化字典为表格"""
        if not data:
            return "<p>暂无数据</p>"

        rows = []
        for key, value in data.items():
            if isinstance(value, dict | list):
                value_str = self._format_content(value)
            else:
                value_str = str(value)
            rows.append(f"<tr><td><strong>{key}</strong></td><td>{value_str}</td></tr>")

        return f"<table><thead><tr><th>指标</th><th>值</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"

    def _format_list(self, data: list) -> str:
        """格式化列表"""
        items = [f"<li>{self._format_content(item)}</li>" for item in data]
        return f"<ul>{''.join(items)}</ul>"

    def save(self, content: str, filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"保存HTML报告失败: {e}")
            return False


class ReportGeneratorFactory:
    """报告生成器工厂"""

    _generators = {
        OutputFormat.JSON: JSONReportGenerator,
        OutputFormat.MARKDOWN: MarkdownReportGenerator,
        OutputFormat.HTML: HTMLReportGenerator,
    }

    @classmethod
    def register(cls, output_format: OutputFormat, generator_class: type):
        """注册自定义生成器"""
        cls._generators[output_format] = generator_class

    @classmethod
    def create(cls, config: ReportConfig) -> BaseReportGenerator:
        """创建生成器"""
        generator_class = cls._generators.get(config.format, JSONReportGenerator)
        return generator_class(config)


class FlexibleReportGenerator:
    """灵活的报告生成器"""

    def __init__(self):
        self._default_config = ReportConfig(title="分析报告", author="Regional Economic Analysis Team")

    def generate_report(
        self, sections: list[ReportSection], config: ReportConfig | None = None, output_path: str | None = None
    ) -> str:
        """
        生成报告

        Args:
            sections: 报告章节列表
            config: 报告配置
            output_path: 输出路径

        Returns:
            生成的报告内容
        """
        if config is None:
            config = self._default_config

        generator = ReportGeneratorFactory.create(config)
        content = generator.generate(sections)

        if output_path:
            generator.save(content, output_path)
            logger.info(f"报告已保存到 {output_path}")

        return content

    def create_section(
        self, title: str, content: Any, visualization: str | None = None, order: int = 0, **metadata
    ) -> ReportSection:
        """创建报告章节"""
        return ReportSection(title=title, content=content, visualization=visualization, order=order, metadata=metadata)

    def quick_report(
        self, title: str, data: dict[str, Any], format: str = "markdown", output_path: str | None = None
    ) -> str:
        """快速生成简单报告"""
        config = ReportConfig(title=title, format=OutputFormat(format))

        section = self.create_section(title="数据概览", content=data, order=0)

        return self.generate_report([section], config, output_path)


# 全局实例
report_generator = FlexibleReportGenerator()


# 便捷函数
def generate_report(
    sections: list[ReportSection], config: ReportConfig | None = None, output_path: str | None = None
) -> str:
    """生成报告"""
    return report_generator.generate_report(sections, config, output_path)


def create_report_section(title: str, content: Any, **kwargs) -> ReportSection:
    """创建报告章节"""
    return report_generator.create_section(title, content, **kwargs)


def quick_report(title: str, data: dict[str, Any], format: str = "markdown", output_path: str | None = None) -> str:
    """快速生成报告"""
    return report_generator.quick_report(title, data, format, output_path)
