"""
导出工具模块
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class ExportUtils:
    """导出工具类"""

    @staticmethod
    def export_csv(df: pd.DataFrame, path: str, **kwargs) -> str:
        """导出为CSV"""
        df.to_csv(path, index=False, **kwargs)
        logger.info(f"CSV已导出: {path}")
        return path

    @staticmethod
    def export_excel(df: pd.DataFrame, path: str, sheet_name: str = "Sheet1", **kwargs) -> str:
        """导出为Excel"""
        df.to_excel(path, sheet_name=sheet_name, index=False, **kwargs)
        logger.info(f"Excel已导出: {path}")
        return path

    @staticmethod
    def export_json(data: Any, path: str, indent: int = 2, **kwargs) -> str:
        """导出为JSON"""
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, **kwargs)
        logger.info(f"JSON已导出: {path}")
        return path

    @staticmethod
    def export_html(df: pd.DataFrame, path: str, title: str = "数据报表", **kwargs) -> str:
        """导出为HTML"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                h1 {{ color: #333; font-family: Arial, sans-serif; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {df.to_html(index=False, **kwargs)}
        </body>
        </html>
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_template)
        logger.info(f"HTML已导出: {path}")
        return path

    @staticmethod
    def export_dict_to_csv(data: dict[str, list[Any]], path: str) -> str:
        """将字典导出为CSV"""
        df = pd.DataFrame(data)
        return ExportUtils.export_csv(df, path)

    @staticmethod
    def merge_dataframes(dfs: dict[str, pd.DataFrame], path: str) -> str:
        """合并多个DataFrame导出到同一个Excel文件的不同sheet"""
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"多Sheet Excel已导出: {path}")
        return path


export_utils = ExportUtils()
