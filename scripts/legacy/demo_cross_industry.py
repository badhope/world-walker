"""
通用框架跨行业分析演示
展示如何将同一个框架应用于不同行业
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import UniversalAnalyzer, get_available_models


def demo_default_industry():
    """演示1：默认通用行业分析"""
    print("\n" + "=" * 80)
    print("演示1：默认通用行业分析")
    print("=" * 80)
    
    analyzer = UniversalAnalyzer(config_name='default')
    
    n_regions = 15
    n_years = 5
    
    np.random.seed(42)
    regions = [f"Region_{i:02d}" for i in range(n_regions)]
    years = list(range(2020, 2020 + n_years))
    
    data = []
    for region in regions:
        base_val = regions.index(region) * 10
        
        for year in years:
            data.append({
                'region_id': region,
                'region_name': f"{region} ({year})",
                'year': year,
                'source': 'sample',
                'land_price': 500 + base_val + np.random.normal(0, 50),
                'labor_cost': 3000 + base_val * 50 + np.random.normal(0, 200),
                'energy_cost': 0.8 + base_val * 0.02 + np.random.normal(0, 0.1),
                'market_size': 100 + base_val * 2 + (year - 2020) * 10 + np.random.normal(0, 20),
                'talent_pool': 50 + base_val + np.random.normal(0, 10),
                'infrastructure': 70 + base_val * 0.5 + np.random.normal(0, 10),
                'tax_incentive': 5 + base_val * 0.3 + np.random.normal(0, 1),
                'subsidy': 3 + base_val * 0.2 + np.random.normal(0, 0.5),
                'approval_efficiency': 10 - base_val * 0.5 + np.random.normal(0, 1),
            })
    
    df = pd.DataFrame(data)
    
    print(f"\n行业: {analyzer.config.industry.industry_name}")
    print(f"行业类型: {analyzer.config.industry.industry_type}")
    print(f"分析维度: {[d.display_name for d in analyzer.config.industry.dimensions]}")
    print(f"数据规模: {len(df)} 条记录")
    
    dataset = analyzer.load_data_from_dataframe(df, name='default_industry')
    
    result = analyzer.analyze(
        run_ml=True,
        target_column='market_size',
        feature_columns=['land_price', 'labor_cost', 'energy_cost', 'talent_pool', 'infrastructure'],
        model_names=['linear_regression', 'random_forest', 'gbdt'],
        hyperparameter_tuning=False,
        test_size=0.2,
    )
    
    print(f"\n✓ 最佳模型: {result.ml_result.best_model.model_name}")
    print(f"✓ R²分数: {result.ml_result.best_model.metrics.r2:.4f}")
    
    return result


def demo_custom_industry():
    """演示2：自定义零售行业分析"""
    print("\n" + "=" * 80)
    print("演示2：零售行业选址分析")
    print("=" * 80)
    
    np.random.seed(42)
    
    n_stores = 20
    n_years = 4
    
    stores = [f"Store_{i:03d}" for i in range(n_stores)]
    years = list(range(2020, 2020 + n_years))
    
    data = []
    for store in stores:
        base_quality = np.random.uniform(0.6, 1.0)
        
        for year in years:
            base = stores.index(store) * 5
            
            record = {
                'region_id': store,
                'region_name': f"{store} - Location {stores.index(store)}",
                'year': year,
                'source': 'retail_sample',
                'foot_traffic': int(500 + base * 10 + base_quality * 200 + np.random.normal(0, 50)),
                'rental_cost': 5 + base * 0.2 + np.random.normal(0, 0.5),
                'competition_density': 10 - base * 0.5 + np.random.normal(0, 2),
                'accessibility': 70 + base * 0.3 + np.random.normal(0, 5),
                'population': 50 + base * 2 + np.random.normal(0, 5),
                'income_level': 8000 + base * 100 + base_quality * 500 + np.random.normal(0, 200),
                'age_distribution': 30 + base * 0.5 + np.random.normal(0, 5),
                'spending_habit': 60 + base * 0.8 + np.random.normal(0, 5),
                'labor_cost': 4000 + base * 50 + np.random.normal(0, 200),
                'utilities_cost': 5000 + base * 20 + np.random.normal(0, 300),
                'logistics_cost': 15 + base * 0.3 + np.random.normal(0, 2),
                'inventory_turnover': 8 + base_quality * 4 + (year - 2020) * 0.5 + np.random.normal(0, 1),
            }
            
            record['foot_traffic'] = max(0, record['foot_traffic'])
            record['competition_density'] = max(0, record['competition_density'])
            record['inventory_turnover'] = max(0, record['inventory_turnover'])
            
            data.append(record)
    
    df = pd.DataFrame(data)
    
    print(f"\n行业: 零售行业")
    print(f"业务场景: 门店选址与经营预测")
    print(f"分析目标: 预测库存周转率")
    print(f"数据规模: {len(df)} 条记录")
    
    analyzer = UniversalAnalyzer(config_name='default')
    dataset = analyzer.load_data_from_dataframe(df, name='retail_stores')
    
    result = analyzer.analyze(
        run_ml=True,
        target_column='inventory_turnover',
        feature_columns=['foot_traffic', 'rental_cost', 'competition_density', 'income_level', 
                        'labor_cost', 'logistics_cost'],
        model_names=['linear_regression', 'random_forest', 'gbdt', 'ridge'],
        hyperparameter_tuning=False,
        test_size=0.2,
    )
    
    print(f"\n✓ 最佳模型: {result.ml_result.best_model.model_name}")
    print(f"✓ R²分数: {result.ml_result.best_model.metrics.r2:.4f}")
    
    if result.ml_result.best_model.feature_importance:
        print(f"\n特征重要性排名:")
        sorted_features = sorted(
            result.ml_result.best_model.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for feat, imp in sorted_features[:5]:
            print(f"  {feat}: {imp:.4f}")
    
    return result


def demo_time_series_forecast():
    """演示3：时间序列预测"""
    print("\n" + "=" * 80)
    print("演示3：时间序列预测")
    print("=" * 80)
    
    np.random.seed(42)
    
    n_periods = 60
    
    dates = pd.date_range(start='2020-01-01', periods=n_periods, freq='ME')
    
    trend = np.arange(n_periods) * 0.5
    seasonal = 10 * np.sin(np.arange(n_periods) * 2 * np.pi / 12)
    noise = np.random.normal(0, 5, n_periods)
    
    sales = 100 + trend + seasonal + noise
    
    df = pd.DataFrame({
        'region_id': 'Store_001',
        'region_name': '旗舰门店',
        'year': dates.year,
        'month': dates.month,
        'source': 'time_series',
        'sales': sales,
        'marketing_spend': 10 + trend * 0.3 + np.random.normal(0, 2, n_periods),
        'customer_count': (sales * 0.5 + np.random.normal(0, 10, n_periods)).astype(int),
        'avg_transaction': sales / (sales * 0.5 + np.random.normal(0, 10, n_periods)),
    })
    
    print(f"\n场景: 销售时间序列预测")
    print(f"时间范围: {dates[0].strftime('%Y-%m')} 至 {dates[-1].strftime('%Y-%m')}")
    print(f"数据点: {len(df)} 个")
    
    analyzer = UniversalAnalyzer(config_name='default')
    dataset = analyzer.load_data_from_dataframe(df, name='time_series_sales')
    
    result = analyzer.analyze(
        run_ml=True,
        target_column='sales',
        feature_columns=['marketing_spend', 'customer_count', 'month'],
        model_names=['linear_regression', 'random_forest', 'gbdt'],
        hyperparameter_tuning=False,
        test_size=0.2,
    )
    
    print(f"\n✓ 最佳模型: {result.ml_result.best_model.model_name}")
    print(f"✓ R²分数: {result.ml_result.best_model.metrics.r2:.4f}")
    print(f"✓ MAE: {result.ml_result.best_model.metrics.mae:.4f}")
    
    return result


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("通用数据分析框架 - 跨行业应用演示")
    print("=" * 80)
    
    print(f"\n可用机器学习模型: {get_available_models()}")
    
    demo_default_industry()
    demo_custom_industry()
    demo_time_series_forecast()
    
    print("\n" + "=" * 80)
    print("✓ 所有演示完成！")
    print("=" * 80)
    
    print("\n框架特点总结：")
    print("1. ✓ 通用配置系统 - YAML驱动，易于扩展")
    print("2. ✓ 多源数据支持 - CSV、Excel、JSON、数据库")
    print("3. ✓ 8+种机器学习算法 - 涵盖回归、时间序列")
    print("4. ✓ AutoML自动化 - 一键训练，自动选优")
    print("5. ✓ 行业无关性 - 同一框架，适用任意行业")
    print("6. ✓ 地区无关性 - 支持全球任意地区")
    print("7. ✓ 持续可优化 - 模型可迭代更新")
    print("\n立即使用，只需提供数据！")


if __name__ == '__main__':
    main()
