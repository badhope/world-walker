"""
文件工具模块
"""

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class FileUtils:
    """文件工具类"""

    @staticmethod
    def ensure_directory(path: str | Path) -> Path:
        """确保目录存在，不存在则创建"""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
        """保存JSON文件"""
        FileUtils.ensure_directory(Path(path).parent)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"JSON文件已保存: {path}")

    @staticmethod
    def load_json(path: str | Path) -> Any:
        """加载JSON文件"""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_csv(df: pd.DataFrame, path: str | Path, **kwargs) -> None:
        """保存CSV文件"""
        FileUtils.ensure_directory(Path(path).parent)
        df.to_csv(path, index=False, **kwargs)
        logger.info(f"CSV文件已保存: {path}")

    @staticmethod
    def load_csv(path: str | Path, **kwargs) -> pd.DataFrame:
        """加载CSV文件"""
        return pd.read_csv(path, **kwargs)

    @staticmethod
    def save_excel(df: pd.DataFrame, path: str | Path, sheet_name: str = "Sheet1", **kwargs) -> None:
        """保存Excel文件"""
        FileUtils.ensure_directory(Path(path).parent)
        df.to_excel(path, sheet_name=sheet_name, index=False, **kwargs)
        logger.info(f"Excel文件已保存: {path}")

    @staticmethod
    def load_excel(path: str | Path, sheet_name: str = 0, **kwargs) -> pd.DataFrame:
        """加载Excel文件"""
        return pd.read_excel(path, sheet_name=sheet_name, **kwargs)

    @staticmethod
    def list_files(directory: str | Path, pattern: str = "*") -> list[Path]:
        """列出目录下的文件"""
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        return list(dir_path.glob(pattern))

    @staticmethod
    def file_exists(path: str | Path) -> bool:
        """检查文件是否存在"""
        return Path(path).exists()
