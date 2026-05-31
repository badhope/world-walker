"""
零售门店数据适配器 - 支持多种数据源导入
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class RetailDataAdapter:
    """零售门店数据适配器"""
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.data_sources = {}
        self.loaded_data = {}
        self.loading_report = {}
    
    # ==================== 多源数据加载 ====================
    
    def load_csv(
        self,
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> pd.DataFrame:
        """加载 CSV 文件"""
        logger.info(f"Loading CSV file: {file_path}")
        df = pd.read_csv(file_path, encoding=encoding, **kwargs)
        self.loaded_data["csv"] = df
        self.loading_report["csv"] = {
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": list(df.columns)
        }
        return df
    
    def load_excel(
        self,
        file_path: str,
        sheet_name: Union[str, int] = 0,
        **kwargs
    ) -> pd.DataFrame:
        """加载 Excel 文件"""
        logger.info(f"Loading Excel file: {file_path}, sheet: {sheet_name}")
        df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
        self.loaded_data["excel"] = df
        self.loading_report["excel"] = {
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": list(df.columns)
        }
        return df
    
    def load_json(
        self,
        file_path: str,
        **kwargs
    ) -> pd.DataFrame:
        """加载 JSON 文件"""
        logger.info(f"Loading JSON file: {file_path}")
        df = pd.read_json(file_path, **kwargs)
        self.loaded_data["json"] = df
        self.loading_report["json"] = {
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": list(df.columns)
        }
        return df
    
    def load_dataframe(
        self,
        df: pd.DataFrame,
        source_name: str = "dataframe"
    ) -> pd.DataFrame:
        """加载已有的 DataFrame"""
        logger.info(f"Loading DataFrame from: {source_name}")
        self.loaded_data[source_name] = df.copy()
        self.loading_report[source_name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": list(df.columns)
        }
        return df
    
    def load_from_dict(
        self,
        data_dict: Dict[str, List],
        source_name: str = "dict"
    ) -> pd.DataFrame:
        """从字典加载数据"""
        logger.info(f"Loading data from dictionary: {source_name}")
        df = pd.DataFrame(data_dict)
        self.loaded_data[source_name] = df
        self.loading_report[source_name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": list(df.columns)
        }
        return df
    
    # ==================== 数据合并与整合 ====================
    
    def merge_data_sources(
        self,
        source_key: str = "main"
    ) -> pd.DataFrame:
        """
        合并多个数据源
        
        简单实现：返回第一个加载的数据源
        实际项目中需要根据业务逻辑做更复杂的合并
        """
        if source_key in self.loaded_data:
            return self.loaded_data[source_key]
        
        if self.loaded_data:
            first_key = list(self.loaded_data.keys())[0]
            return self.loaded_data[first_key]
        
        raise ValueError("No data loaded yet")
    
    # ==================== 数据标准化与重命名 ====================
    
    def standardize_columns(
        self,
        df: pd.DataFrame,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        标准化列名
        
        Args:
            df: 输入 DataFrame
            column_mapping: 列名映射 {原始列名: 标准列名}
        
        Returns:
            标准化后的 DataFrame
        """
        df_std = df.copy()
        
        if column_mapping:
            df_std = df_std.rename(columns=column_mapping)
        
        # 列名统一处理：转小写，空格转下划线
        df_std.columns = [
            col.strip().lower().replace(" ", "_").replace("-", "_")
            for col in df_std.columns
        ]
        
        return df_std
    
    # ==================== 数据验证 ====================
    
    def validate_required_fields(
        self,
        df: pd.DataFrame,
        required_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        验证必填字段
        
        Returns:
            (是否通过, 缺失的字段列表)
        """
        missing_fields = []
        for field in required_fields:
            if field not in df.columns:
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
        else:
            logger.info("All required fields are present")
        
        return is_valid, missing_fields
    
    # ==================== 生成样本数据（用于演示） ====================
    
    @staticmethod
    def generate_sample_data(
        num_stores: int = 50,
        random_seed: int = 42
    ) -> pd.DataFrame:
        """
        生成零售门店样本数据
        
        Args:
            num_stores: 门店数量
            random_seed: 随机种子
        
        Returns:
            样本 DataFrame
        """
        np.random.seed(random_seed)
        
        # 基础门店信息
        store_ids = [f"STORE_{i:03d}" for i in range(1, num_stores + 1)]
        store_names = [f"便利店 {i}号店" for i in range(1, num_stores + 1)]
        addresses = [f"上海市浦东新区某某路 {i}号" for i in range(1, num_stores + 1)]
        
        # GPS坐标（上海范围内）
        latitudes = np.random.uniform(31.1, 31.3, num_stores)
        longitudes = np.random.uniform(121.4, 121.6, num_stores)
        
        # 门店面积
        store_areas = np.random.randint(40, 150, num_stores)
        
        # 位置特征
        distance_to_subway = np.random.exponential(300, num_stores)
        bus_stop_count = np.random.poisson(4, num_stores)
        parking_count = np.random.poisson(30, num_stores)
        is_main_street = np.random.choice([0, 1], num_stores, p=[0.4, 0.6])
        business_types = np.random.choice(
            ["business_district", "residential", "mixed"],
            num_stores,
            p=[0.3, 0.4, 0.3]
        )
        
        # 人口特征
        population_1km = np.random.randint(5000, 50000, num_stores)
        population_2km = population_1km * np.random.uniform(2.5, 3.5, num_stores)
        avg_age = np.random.normal(35, 5, num_stores)
        young_ratio = np.random.beta(2, 3, num_stores)
        avg_income = np.random.randint(60000, 150000, num_stores)
        
        # 竞争特征
        competitor_count_1km = np.random.poisson(2, num_stores)
        competitor_count_2km = competitor_count_1km + np.random.poisson(3, num_stores)
        distance_to_competitor = np.random.exponential(400, num_stores)
        
        # 租金特征
        rent_per_sqm = np.random.uniform(5, 20, num_stores)
        regional_avg_rent = rent_per_sqm * np.random.uniform(0.8, 1.2, num_stores)
        
        # 目标变量：月均销售额（有业务逻辑的模拟）
        # 销售额 = 基础销量 + 面积影响 + 人口影响 - 竞争影响 + 噪音
        base_sales = 150000
        area_effect = store_areas * 500
        population_effect = np.log1p(population_1km) * 8000
        competition_effect = competitor_count_1km * 10000
        subway_effect = np.maximum(0, 50000 - distance_to_subway * 50)
        noise = np.random.normal(0, 25000, num_stores)
        
        monthly_sales = base_sales + area_effect + population_effect - competition_effect + subway_effect + noise
        monthly_sales = np.maximum(monthly_sales, 30000)  # 最低3万
        
        # 构造 DataFrame
        data = {
            "store_id": store_ids,
            "store_name": store_names,
            "address": addresses,
            "latitude": latitudes,
            "longitude": longitudes,
            "store_area": store_areas,
            "distance_to_subway": distance_to_subway,
            "bus_stop_count_500m": bus_stop_count,
            "parking_lot_count": parking_count,
            "is_main_street": is_main_street,
            "business_district_type": business_types,
            "population_1km": population_1km,
            "population_2km": population_2km,
            "avg_age": avg_age,
            "young_ratio_18_30": young_ratio,
            "avg_income": avg_income,
            "competitor_count_1km": competitor_count_1km,
            "competitor_count_2km": competitor_count_2km,
            "distance_to_nearest_competitor": distance_to_competitor,
            "rent_per_sqm": rent_per_sqm,
            "regional_avg_rent": regional_avg_rent,
            "monthly_sales": monthly_sales
        }
        
        df = pd.DataFrame(data)
        
        # 随机引入一些缺失值，测试清洗能力
        for col in df.columns:
            if col not in ["store_id", "store_name", "monthly_sales"]:
                mask = np.random.random(len(df)) < 0.05
                df.loc[mask, col] = np.nan
        
        return df
    
    def get_loading_report(self) -> Dict[str, Any]:
        """获取数据加载报告"""
        return self.loading_report
