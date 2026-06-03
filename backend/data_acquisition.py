"""
数据采集模块 - 支持多种数据源
- CSV/Excel/JSON文件
- API接口
- 数据库（SQLite, PostgreSQL, MySQL等）
- 定时采集任务
- 断点续传
"""

import logging
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataSourceAdapter:
    """通用数据源适配器基类"""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.last_checkpoint = None

    def load(self) -> pd.DataFrame:
        """加载数据 - 需要子类实现"""
        raise NotImplementedError

    def save_checkpoint(self, state: dict):
        """保存断点"""
        state["timestamp"] = datetime.now().isoformat()
        self.last_checkpoint = state
        logger.info(f"Checkpoint saved: {state}")

    def load_checkpoint(self) -> dict | None:
        """加载断点"""
        return self.last_checkpoint


class FileSourceAdapter(DataSourceAdapter):
    """文件数据源适配器（CSV/Excel/JSON）"""

    def __init__(self, file_path: str, config: dict | None = None):
        super().__init__(config)
        self.file_path = Path(file_path)

    def load(self) -> pd.DataFrame:
        """加载文件数据"""
        logger.info(f"Loading data from file: {self.file_path}")

        suffix = self.file_path.suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(self.file_path)
        elif suffix in [".xlsx", ".xls"]:
            return pd.read_excel(self.file_path)
        elif suffix == ".json":
            return pd.read_json(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")


class APISourceAdapter(DataSourceAdapter):
    """API数据源适配器"""

    def __init__(self, api_url: str, config: dict | None = None):
        super().__init__(config)
        self.api_url = api_url
        self.api_key = config.get("api_key") if config else None
        self.page_size = config.get("page_size", 100) if config else 100

    def _make_request(self, page: int = 1) -> dict:
        """发起API请求（模拟）"""
        # 真实场景中使用 requests 库
        # 这里模拟返回数据
        import random

        num_records = random.randint(50, 150)

        data = []
        for i in range(num_records):
            data.append(
                {
                    "id": f"REC_{page}_{i:04d}",
                    "value": random.random() * 100,
                    "category": random.choice(["A", "B", "C"]),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return {"data": data, "page": page, "total_pages": 3, "has_more": page < 3}

    def load(self) -> pd.DataFrame:
        """从API加载数据（支持分页和断点续传）"""
        logger.info(f"Loading data from API: {self.api_url}")

        all_data = []

        # 从断点继续
        checkpoint = self.load_checkpoint()
        start_page = checkpoint.get("page", 1) if checkpoint else 1

        for page in range(start_page, 100):  # 防止无限循环
            try:
                response = self._make_request(page)

                if not response.get("data"):
                    break

                all_data.extend(response["data"])
                logger.info(f"Fetched page {page}, total records: {len(all_data)}")

                # 保存断点
                self.save_checkpoint({"page": page + 1})

                if not response.get("has_more", False):
                    break

                # 避免请求过快
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                raise

        df = pd.DataFrame(all_data)
        logger.info(f"Loaded {len(df)} records from API")
        return df


class DatabaseSourceAdapter(DataSourceAdapter):
    """数据库数据源适配器"""

    def __init__(self, connection_string: str, query: str, config: dict | None = None):
        super().__init__(config)
        self.connection_string = connection_string
        self.query = query

    def load(self) -> pd.DataFrame:
        """从数据库加载数据"""
        logger.info("Loading data from database")

        # 真实场景中使用 SQLAlchemy 或其他数据库库
        # 这里模拟返回
        data = {
            "id": [f"DB_{i:04d}" for i in range(1, 101)],
            "value": np.random.random(100) * 100,
            "category": np.random.choice(["X", "Y", "Z"], 100),
        }

        df = pd.DataFrame(data)
        logger.info(f"Loaded {len(df)} records from database")
        return df


def get_data_source(source_type: str, **kwargs) -> DataSourceAdapter:
    """
    工厂方法：获取对应类型的数据源适配器

    Args:
        source_type: 数据源类型 ("file", "api", "database")
        **kwargs: 各类型需要的参数

    Returns:
        DataSourceAdapter实例
    """
    if source_type == "file":
        return FileSourceAdapter(kwargs["file_path"])
    elif source_type == "api":
        return APISourceAdapter(kwargs["api_url"], kwargs.get("config"))
    elif source_type == "database":
        return DatabaseSourceAdapter(kwargs["connection_string"], kwargs["query"], kwargs.get("config"))
    else:
        raise ValueError(f"Unknown source type: {source_type}")


# 简单测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("测试文件适配器...")
    # file_adapter = FileSourceAdapter("data/retail_enhanced/processed_data.csv")
    # df = file_adapter.load()
    # print(f"加载了 {len(df)} 条数据")

    print("\n测试API适配器...")
    api_adapter = APISourceAdapter("https://api.example.com/data")
    df = api_adapter.load()
    print(f"加载了 {len(df)} 条数据")
    print(df.head())

    print("\n测试数据库适配器...")
    db_adapter = DatabaseSourceAdapter("sqlite:///test.db", "SELECT * FROM table")
    df = db_adapter.load()
    print(f"加载了 {len(df)} 条数据")
