"""
数据导入导出模块 - 支持多种格式的数据导入导出
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class BaseImporter(ABC):
    """数据导入器基类"""

    @abstractmethod
    def import_data(self, file_path: str | Path) -> list[dict[str, Any]]:
        """导入数据"""
        pass

    @abstractmethod
    def validate(self, data: list[dict[str, Any]]) -> bool:
        """验证数据"""
        pass


class BaseExporter(ABC):
    """数据导出器基类"""

    @abstractmethod
    def export_data(self, data: list[dict[str, Any]], file_path: str | Path) -> bool:
        """导出数据"""
        pass


class JSONImporter(BaseImporter):
    """JSON 格式导入器"""

    def import_data(self, file_path: str | Path) -> list[dict[str, Any]]:
        """
        导入 JSON 数据

        Args:
            file_path: 文件路径

        Returns:
            数据列表
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                logger.error(f"不支持的 JSON 格式: {type(data)}")
                return []

        except Exception as e:
            logger.error(f"JSON 导入失败: {e}")
            return []

    def validate(self, data: list[dict[str, Any]]) -> bool:
        """验证数据格式"""
        if not data:
            return False

        required_fields = ["code", "name", "value", "year"]
        for item in data:
            if not all(field in item for field in required_fields):
                logger.warning(f"数据项缺少必需字段: {item}")
                return False

        return True


class JSONExporter(BaseExporter):
    """JSON 格式导出器"""

    def export_data(self, data: list[dict[str, Any]], file_path: str | Path) -> bool:
        """
        导出 JSON 数据

        Args:
            data: 数据列表
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"JSON 导出成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"JSON 导出失败: {e}")
            return False


class CSVImporter(BaseImporter):
    """CSV 格式导入器"""

    def import_data(self, file_path: str | Path) -> list[dict[str, Any]]:
        """
        导入 CSV 数据

        Args:
            file_path: 文件路径

        Returns:
            数据列表
        """
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            return df.to_dict("records")

        except Exception as e:
            logger.error(f"CSV 导入失败: {e}")
            return []

    def validate(self, data: list[dict[str, Any]]) -> bool:
        """验证数据格式"""
        if not data:
            return False

        required_fields = ["code", "name", "value", "year"]
        for item in data:
            if not all(field in item for field in required_fields):
                logger.warning(f"数据项缺少必需字段: {item}")
                return False

        return True


class CSVExporter(BaseExporter):
    """CSV 格式导出器"""

    def export_data(self, data: list[dict[str, Any]], file_path: str | Path) -> bool:
        """
        导出 CSV 数据

        Args:
            data: 数据列表
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding="utf-8-sig")

            logger.info(f"CSV 导出成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"CSV 导出失败: {e}")
            return False


class ExcelImporter(BaseImporter):
    """Excel 格式导入器"""

    def import_data(self, file_path: str | Path, sheet_name: str | None = None) -> list[dict[str, Any]]:
        """
        导入 Excel 数据

        Args:
            file_path: 文件路径
            sheet_name: 工作表名称

        Returns:
            数据列表
        """
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
            else:
                df = pd.read_excel(file_path, engine="openpyxl")

            return df.to_dict("records")

        except Exception as e:
            logger.error(f"Excel 导入失败: {e}")
            return []

    def validate(self, data: list[dict[str, Any]]) -> bool:
        """验证数据格式"""
        if not data:
            return False

        required_fields = ["code", "name", "value", "year"]
        for item in data:
            if not all(field in item for field in required_fields):
                logger.warning(f"数据项缺少必需字段: {item}")
                return False

        return True


class ExcelExporter(BaseExporter):
    """Excel 格式导出器"""

    def export_data(self, data: list[dict[str, Any]], file_path: str | Path, sheet_name: str = "Sheet1") -> bool:
        """
        导出 Excel 数据

        Args:
            data: 数据列表
            file_path: 文件路径
            sheet_name: 工作表名称

        Returns:
            是否成功
        """
        try:
            df = pd.DataFrame(data)
            df.to_excel(file_path, sheet_name=sheet_name, index=False, engine="openpyxl")

            logger.info(f"Excel 导出成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Excel 导出失败: {e}")
            return False


class DataImportExportManager:
    """数据导入导出管理器"""

    def __init__(self):
        """初始化管理器"""
        self.importers = {
            "json": JSONImporter(),
            "csv": CSVImporter(),
            "xlsx": ExcelImporter(),
            "xls": ExcelImporter(),
        }

        self.exporters = {
            "json": JSONExporter(),
            "csv": CSVExporter(),
            "xlsx": ExcelExporter(),
            "xls": ExcelExporter(),
        }

    def import_data(self, file_path: str | Path, format_type: str | None = None) -> list[dict[str, Any]]:
        """
        导入数据

        Args:
            file_path: 文件路径
            format_type: 格式类型（json, csv, xlsx, xls），如果为 None 则自动推断

        Returns:
            数据列表
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return []

        # 自动推断格式
        if format_type is None:
            format_type = file_path.suffix.lstrip(".")

        if format_type not in self.importers:
            logger.error(f"不支持的导入格式: {format_type}")
            return []

        importer = self.importers[format_type]
        data = importer.import_data(file_path)

        # 验证数据
        if importer.validate(data):
            logger.info(f"数据导入成功: {file_path}, 共 {len(data)} 条")
            return data
        else:
            logger.warning(f"数据验证失败: {file_path}")
            return data  # 仍然返回数据，但记录警告

    def export_data(self, data: list[dict[str, Any]], file_path: str | Path, format_type: str | None = None) -> bool:
        """
        导出数据

        Args:
            data: 数据列表
            file_path: 文件路径
            format_type: 格式类型（json, csv, xlsx, xls），如果为 None 则自动推断

        Returns:
            是否成功
        """
        file_path = Path(file_path)

        # 自动推断格式
        if format_type is None:
            format_type = file_path.suffix.lstrip(".")

        if format_type not in self.exporters:
            logger.error(f"不支持的导出格式: {format_type}")
            return False

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        exporter = self.exporters[format_type]

        # 根据格式调用不同的导出方法
        if format_type in ["xlsx", "xls"]:
            success = exporter.export_data(data, file_path, sheet_name="数据导出")
        else:
            success = exporter.export_data(data, file_path)

        if success:
            logger.info(f"数据导出成功: {file_path}, 共 {len(data)} 条")

        return success

    def get_supported_formats(self) -> dict[str, list[str]]:
        """
        获取支持的格式

        Returns:
            格式字典
        """
        return {"import": list(self.importers.keys()), "export": list(self.exporters.keys())}

    def batch_import(self, file_paths: list[str | Path]) -> dict[str, list[dict[str, Any]]]:
        """
        批量导入数据

        Args:
            file_paths: 文件路径列表

        Returns:
            导入结果字典
        """
        results = {}

        for file_path in file_paths:
            file_name = Path(file_path).name
            data = self.import_data(file_path)
            results[file_name] = data

        return results

    def batch_export(self, data_dict: dict[str, list[dict[str, Any]]], output_dir: str | Path) -> dict[str, bool]:
        """
        批量导出数据

        Args:
            data_dict: 数据字典 {文件名: 数据}
            output_dir: 输出目录

        Returns:
            导出结果字典
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        for file_name, data in data_dict.items():
            file_path = output_dir / file_name
            success = self.export_data(data, file_path)
            results[file_name] = success

        return results


# 全局实例
data_manager = DataImportExportManager()
