"""
数据库模块 - SQLite数据库集成
为区域产业经济分析平台提供数据持久化功能
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理类
    负责SQLite数据库的初始化、数据存储和查询
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "regional_economy.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. 经济数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS economic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                region TEXT,
                indicator TEXT NOT NULL,
                value REAL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. 分析记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                industry TEXT NOT NULL,
                year INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                analysis_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. 企业分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enterprise_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                industry TEXT NOT NULL,
                year INTEGER NOT NULL,
                overall_score REAL,
                business_cost_score REAL,
                supply_chain_score REAL,
                policy_benefit_score REAL,
                raw_data TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_economic_year_region 
            ON economic_data (year, region)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_region_industry 
            ON analysis_records (region, industry, year)
        """)

        conn.commit()
        conn.close()

        logger.info(f"数据库初始化完成: {self.db_path}")

    def save_economic_data(
        self, year: int, indicator: str, value: float, source: str = "akshare", region: str = "全国"
    ):
        """保存经济数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 先检查是否已存在，存在则更新
        cursor.execute(
            """
            SELECT id FROM economic_data 
            WHERE year = ? AND region = ? AND indicator = ?
        """,
            (year, region, indicator),
        )

        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE economic_data 
                SET value = ?, source = ?, created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (value, source, existing[0]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO economic_data (year, region, indicator, value, source)
                VALUES (?, ?, ?, ?, ?)
            """,
                (year, region, indicator, value, source),
            )

        conn.commit()
        conn.close()

    def save_economic_dataframe(self, df: pd.DataFrame, region: str = "全国"):
        """批量保存DataFrame格式的经济数据"""
        conn = sqlite3.connect(self.db_path)

        for _, row in df.iterrows():
            year = int(row["year"])
            for col in df.columns:
                if col != "year" and pd.notna(row[col]):
                    self.save_economic_data(year, col, float(row[col]), region=region)

        conn.commit()
        conn.close()

        logger.info(f"批量保存了 {len(df)} 条经济数据")

    def get_economic_data(
        self, indicator: str = None, start_year: int = None, end_year: int = None, region: str = "全国"
    ) -> pd.DataFrame:
        """获取经济数据"""
        conn = sqlite3.connect(self.db_path)

        query = "SELECT year, indicator, value FROM economic_data WHERE region = ?"
        params = [region]

        if indicator:
            query += " AND indicator = ?"
            params.append(indicator)

        if start_year:
            query += " AND year >= ?"
            params.append(start_year)

        if end_year:
            query += " AND year <= ?"
            params.append(end_year)

        query += " ORDER BY year"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    def save_enterprise_analysis(self, region: str, industry: str, year: int, analysis_result: dict[str, Any]):
        """保存企业分析结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        overall_score = analysis_result.get("overall_score", 0)
        business_cost_score = analysis_result.get("business_costs", {}).get("total_cost_score", 0)
        supply_chain_score = analysis_result.get("supply_chain", {}).get("supply_chain_score", 0)
        policy_benefit_score = analysis_result.get("policy_benefits", {}).get("policy_benefit_score", 0)
        recommendations = json.dumps(analysis_result.get("recommendations", []), ensure_ascii=False)
        raw_data = json.dumps(analysis_result.get("data_used", {}), ensure_ascii=False)

        cursor.execute(
            """
            INSERT INTO enterprise_analysis 
            (region, industry, year, overall_score, business_cost_score,
             supply_chain_score, policy_benefit_score, raw_data, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                region,
                industry,
                year,
                overall_score,
                business_cost_score,
                supply_chain_score,
                policy_benefit_score,
                raw_data,
                recommendations,
            ),
        )

        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"企业分析结果已保存 (ID: {analysis_id})")
        return analysis_id

    def get_enterprise_analysis_history(
        self, region: str = None, industry: str = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """获取企业分析历史记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT id, region, industry, year, overall_score, 
                   business_cost_score, supply_chain_score, policy_benefit_score,
                   recommendations, created_at
            FROM enterprise_analysis
        """

        params = []
        conditions = []

        if region:
            conditions.append(" region = ?")
            params.append(region)

        if industry:
            conditions.append(" industry = ?")
            params.append(industry)

        if conditions:
            query += " WHERE" + " AND".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "region": row[1],
                    "industry": row[2],
                    "year": row[3],
                    "overall_score": row[4],
                    "business_cost_score": row[5],
                    "supply_chain_score": row[6],
                    "policy_benefit_score": row[7],
                    "recommendations": json.loads(row[8]) if row[8] else [],
                    "created_at": row[9],
                }
            )

        conn.close()
        return results

    def get_statistics(self) -> dict[str, int]:
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM economic_data")
        economic_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM enterprise_analysis")
        enterprise_count = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(year), MAX(year) FROM economic_data")
        year_range = cursor.fetchone()

        conn.close()

        return {
            "economic_data_count": economic_count,
            "enterprise_analysis_count": enterprise_count,
            "data_year_range": {"start": year_range[0], "end": year_range[1]} if year_range[0] else None,
        }


# 单例实例
_db_instance: DatabaseManager | None = None


def get_db() -> DatabaseManager:
    """获取数据库管理器单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
