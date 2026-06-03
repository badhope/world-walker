"""
通用数据管理系统 - 支持任意地区和格式的数据
支持从CSV、Excel、JSON、数据库等多种数据源加载
"""

import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# SQL 标识符白名单:字母数字 + 下划线,首字符不能是数字,长度上限 128
_SQL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_SQL_IDENTIFIER_MAX_LEN = 128


def validate_sql_identifier(name: str) -> str:
    """校验 SQL 表名/列名,确保不会被注入。

    拒绝:空值、含特殊字符(`;` `' " --` 等)、含空白、点路径、过长。
    """
    if not name or not isinstance(name, str):
        raise ValueError("SQL identifier must be a non-empty string")
    if len(name) > _SQL_IDENTIFIER_MAX_LEN:
        raise ValueError(f"SQL identifier too long (>{_SQL_IDENTIFIER_MAX_LEN})")
    if not _SQL_IDENTIFIER.match(name):
        raise ValueError(
            f"Invalid SQL identifier: {name!r}. "
            "Must match [A-Za-z_][A-Za-z0-9_]* and contain no whitespace, dots, quotes, or SQL keywords."
        )
    return name


logger = logging.getLogger(__name__)


@dataclass
class RegionData:
    """单个地区的数据"""

    region_id: str
    region_name: str
    data: dict[str, Any]
    year: int
    source: str
    quality_score: float = 0.0


@dataclass
class Dataset:
    """完整数据集"""

    name: str
    description: str
    data: list[RegionData]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame"""
        records = []
        for region_data in self.data:
            record = {
                "region_id": region_data.region_id,
                "region_name": region_data.region_name,
                "year": region_data.year,
                "source": region_data.source,
                "quality_score": region_data.quality_score,
            }
            record.update(region_data.data)
            records.append(record)
        return pd.DataFrame(records)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, name: str = "dataset", description: str = "") -> "Dataset":
        """从DataFrame创建Dataset"""
        required_cols = ["region_id", "region_name", "year", "source"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = f"unknown_{col}"

        data = []
        for _, row in df.iterrows():
            cols_to_drop = list(required_cols)
            if "quality_score" in row.index:
                cols_to_drop.append("quality_score")
            data_dict = row.drop(cols_to_drop).to_dict()
            data_dict = {k: v for k, v in data_dict.items() if pd.notna(v)}

            region_data = RegionData(
                region_id=str(row["region_id"]),
                region_name=str(row["region_name"]),
                data=data_dict,
                year=int(row["year"]) if pd.notna(row["year"]) else 2025,
                source=str(row["source"]) if pd.notna(row["source"]) else "unknown",
                quality_score=float(row["quality_score"]) if "quality_score" in row.index else 85.0,
            )
            data.append(region_data)

        return cls(
            name=name,
            description=description,
            data=data,
            metadata={"created_from": "dataframe"},
        )


class DataManager:
    """数据管理器"""

    def __init__(self, data_dir: str | None = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self._datasets: dict[str, Dataset] = {}

    def load_csv(self, file_path: str, name: str | None = None) -> Dataset:
        """从CSV加载数据"""
        df = pd.read_csv(file_path)
        name = name or Path(file_path).stem
        return Dataset.from_dataframe(df, name=name, description=f"Loaded from {file_path}")

    def load_excel(self, file_path: str, sheet_name: str = 0, name: str | None = None) -> Dataset:
        """从Excel加载数据"""
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        name = name or Path(file_path).stem
        return Dataset.from_dataframe(df, name=name, description=f"Loaded from {file_path}")

    def load_json(self, file_path: str, name: str | None = None) -> Dataset:
        """从JSON加载数据"""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame([data])

        name = name or Path(file_path).stem
        return Dataset.from_dataframe(df, name=name, description=f"Loaded from {file_path}")

    def load_database(self, db_path: str, table_name: str, name: str | None = None) -> Dataset:
        """从SQLite数据库加载数据"""
        # L-01:防止 SQL 注入
        safe_table = validate_sql_identifier(table_name)
        conn = sqlite3.connect(db_path)
        # safe_table 已经过 validate_sql_identifier 白名单(只允许字母/数字/下划线),无注入风险。
        df = pd.read_sql(f"SELECT * FROM {safe_table}", conn)  # nosec B608
        conn.close()

        name = name or safe_table
        return Dataset.from_dataframe(df, name=name, description=f"Loaded from {db_path}")

    def save_dataset(self, dataset: Dataset, format: str = "csv"):
        """保存数据集"""
        df = dataset.to_dataframe()
        output_dir = self.data_dir / "processed"
        output_dir.mkdir(exist_ok=True)

        if format == "csv":
            file_path = output_dir / f"{dataset.name}.csv"
            df.to_csv(file_path, index=False, encoding="utf-8")
        elif format == "excel":
            file_path = output_dir / f"{dataset.name}.xlsx"
            df.to_excel(file_path, index=False)
        elif format == "json":
            file_path = output_dir / f"{dataset.name}.json"
            df.to_json(file_path, orient="records", force_ascii=False, indent=2)
        elif format == "database":
            file_path = output_dir / f"{dataset.name}.db"
            conn = sqlite3.connect(file_path)
            df.to_sql(dataset.name, conn, if_exists="replace", index=False)
            conn.close()

        logger.info(f"Dataset saved to {file_path}")
        return file_path

    def register_dataset(self, name: str, dataset: Dataset):
        """注册数据集到内存"""
        self._datasets[name] = dataset
        logger.info(f"Dataset registered: {name}")

    def get_dataset(self, name: str) -> Dataset | None:
        """获取已注册的数据集"""
        return self._datasets.get(name)

    def calculate_benchmarks(self, dataset: Dataset, metric: str, method: str = "percentile") -> dict[str, float]:
        """计算指标基准值"""
        df = dataset.to_dataframe()
        values = df[metric].dropna()

        if len(values) == 0:
            return {}

        if method == "percentile":
            return {
                "min": float(values.min()),
                "low": float(values.quantile(0.25)),
                "medium": float(values.quantile(0.50)),
                "high": float(values.quantile(0.75)),
                "max": float(values.max()),
                "mean": float(values.mean()),
                "std": float(values.std()),
            }
        elif method == "mean_std":
            mean = values.mean()
            std = values.std()
            return {
                "mean": float(mean),
                "std": float(std),
                "low": float(mean - std),
                "medium": float(mean),
                "high": float(mean + std),
            }
        else:
            return {
                "min": float(values.min()),
                "max": float(values.max()),
                "mean": float(values.mean()),
            }

    def clean_data(
        self, dataset: Dataset, remove_na: bool = True, remove_outliers: bool = False, outlier_threshold: float = 3.0
    ) -> Dataset:
        """数据清洗"""
        df = dataset.to_dataframe()

        if remove_na:
            df = df.dropna()

        if remove_outliers:
            for col in df.select_dtypes(include=[np.number]).columns:
                mean = df[col].mean()
                std = df[col].std()
                df = df[(df[col] >= mean - outlier_threshold * std) & (df[col] <= mean + outlier_threshold * std)]

        return Dataset.from_dataframe(df, name=dataset.name, description=f"{dataset.description} (cleaned)")

    def normalize_data(self, dataset: Dataset, method: str = "minmax") -> Dataset:
        """数据标准化/归一化"""
        df = dataset.to_dataframe()

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if method == "minmax":
            for col in numeric_cols:
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val > min_val:
                    df[f"{col}_normalized"] = (df[col] - min_val) / (max_val - min_val)

        elif method == "zscore":
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df[f"{col}_zscore"] = (df[col] - mean) / std

        return Dataset.from_dataframe(
            df, name=f"{dataset.name}_normalized", description=f"{dataset.description} (normalized)"
        )


# 单例
_data_manager: DataManager | None = None


def get_data_manager(data_dir: str | None = None) -> DataManager:
    """获取数据管理器单例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager(data_dir)
    return _data_manager
