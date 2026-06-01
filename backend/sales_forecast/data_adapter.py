"""
销售预测数据适配器
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class SalesDataAdapter:
    """销售预测数据适配器"""
    
    def __init__(self, config=None):
        self.config = config
    
    def generate_sample_data(self, num_records: int = 1000, num_products: int = 10):
        logger.info(f"Generating {num_records} sales records...")

        start_date = pd.to_datetime("2024-01-01")
        dates = pd.date_range(start=start_date, periods=num_records, freq='D')

        categories = ['Electronics', 'Clothing', 'Food', 'Home', 'Beauty']
        rng = np.random.default_rng(42)

        data = {
            "date": dates,
            "product_id": [f"PROD_{str(i).zfill(3)}" for i in rng.integers(1, num_products+1, num_records)],
            "category": rng.choice(categories, num_records),
            "price": rng.uniform(10, 1000, num_records).round(2),
            "discount": rng.uniform(0, 0.5, num_records).round(2),
            "inventory": rng.integers(10, 1000, num_records),
            "promotion_budget": rng.uniform(0, 5000, num_records).round(2),
            "is_holiday": rng.choice([0, 1], num_records, p=[0.9, 0.1])
        }

        df = pd.DataFrame(data)

        base_sales = 100
        price_effect = np.maximum(0, -0.3 * df['price'] / 100)
        discount_effect = 2 * df['discount']
        inventory_effect = 0.1 * df['inventory'] / 100
        promotion_effect = 0.5 * df['promotion_budget'] / 1000
        holiday_effect = 50 * df['is_holiday']

        df['sales'] = (
            base_sales +
            price_effect * 1000 +
            discount_effect * 100 +
            inventory_effect * 100 +
            promotion_effect * 100 +
            holiday_effect +
            rng.normal(0, 50, num_records)
        )

        df['sales'] = df['sales'].round().astype(int)
        df.loc[df['sales'] < 0, 'sales'] = 0

        for col in ['price', 'discount', 'inventory']:
            mask = rng.random(len(df)) < 0.05
            df.loc[mask, col] = np.nan

        logger.info(f"Generated data: {df.shape}")
        return df
    
    def load_data(self, file_path: Union[str, Path]):
        """从文件加载数据"""
        file_path = Path(file_path)
        
        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif file_path.suffix == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def save_data(self, df: pd.DataFrame, file_path: Union[str, Path]):
        """保存数据到文件"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.suffix == '.csv':
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        elif file_path.suffix in ['.xlsx', '.xls']:
            df.to_excel(file_path, index=False)
        elif file_path.suffix == '.json':
            df.to_json(file_path, orient='records', force_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
