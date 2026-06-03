"""
零售门店分析框架 - 健壮性测试
测试各种边界情况、错误处理等
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from backend.retail_location import RetailDataAdapter, RetailLocationAnalyzer, RetailLocationConfig


def test_case_1_normal_data():
    """测试1: 正常数据量（100条）"""
    print("\n" + "=" * 80)
    print("测试1: 正常数据量（100条）")
    print("=" * 80)

    try:
        adapter = RetailDataAdapter()
        data = adapter.generate_sample_data(num_stores=100)
        print(f"✅ 生成数据: {data.shape}")

        config = RetailLocationConfig.get_default_config()
        analyzer = RetailLocationAnalyzer(config)
        results = analyzer.run_full_analysis(data, save_results=True, output_dir="data/test_case1")

        print(f"✅ 最佳模型: {results['insights']['best_model']['name']}")
        print(f"✅ R²: {results['insights']['best_model']['r2_score']:.4f}")

        return True, analyzer
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False, None


def test_case_2_small_data():
    """测试2: 小数据量（20条）"""
    print("\n" + "=" * 80)
    print("测试2: 小数据量（20条）")
    print("=" * 80)

    try:
        adapter = RetailDataAdapter()
        data = adapter.generate_sample_data(num_stores=20)
        print(f"✅ 生成数据: {data.shape}")

        config = RetailLocationConfig.get_default_config()
        analyzer = RetailLocationAnalyzer(config)
        results = analyzer.run_full_analysis(data, save_results=False)

        print(f"✅ 最佳模型: {results['insights']['best_model']['name']}")
        print(f"✅ R²: {results['insights']['best_model']['r2_score']:.4f}")

        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_case_3_minimum_data():
    """测试3: 最小数据量（15条）"""
    print("\n" + "=" * 80)
    print("测试3: 最小数据量（15条）")
    print("=" * 80)

    try:
        adapter = RetailDataAdapter()
        data = adapter.generate_sample_data(num_stores=15)
        print(f"✅ 生成数据: {data.shape}")

        config = RetailLocationConfig.get_default_config()
        analyzer = RetailLocationAnalyzer(config)
        results = analyzer.run_full_analysis(data, save_results=False)

        print(f"✅ 最佳模型: {results['insights']['best_model']['name']}")
        print(f"✅ R²: {results['insights']['best_model']['r2_score']:.4f}")

        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_case_4_save_and_load(analyzer):
    """测试4: 模型保存和加载"""
    print("\n" + "=" * 80)
    print("测试4: 模型保存和加载")
    print("=" * 80)

    try:
        # 保存
        save_dir = "data/test_save_load"
        analyzer.save_analyzer(save_dir)
        print(f"✅ 模型保存到: {save_dir}")

        # 加载
        loaded_analyzer = RetailLocationAnalyzer.load_analyzer(save_dir)
        print("✅ 模型加载成功")

        return True, loaded_analyzer
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False, None


def test_case_5_prediction(loaded_analyzer):
    """测试5: 预测功能"""
    print("\n" + "=" * 80)
    print("测试5: 预测功能")
    print("=" * 80)

    try:
        # 生成测试数据
        adapter = RetailDataAdapter()
        test_data = adapter.generate_sample_data(num_stores=5)

        # 预测
        predictions = loaded_analyzer.predict_new_location(test_data)

        print(f"✅ 预测完成: {predictions.shape}")
        print("预测结果:")
        print(predictions[["store_id", "store_area", "predicted_sales"]])

        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_case_6_prediction_missing_features(loaded_analyzer):
    """测试6: 预测时缺失特征"""
    print("\n" + "=" * 80)
    print("测试6: 预测时缺失特征")
    print("=" * 80)

    try:
        # 生成测试数据，然后删除一些特征
        adapter = RetailDataAdapter()
        test_data = adapter.generate_sample_data(num_stores=3)

        # 删除一些特征
        if "population_3km" in test_data.columns:
            test_data = test_data.drop(columns=["population_3km"])
            print("⚠️ 删除了特征: population_3km")

        if "rent_per_sqm" in test_data.columns:
            test_data = test_data.drop(columns=["rent_per_sqm"])
            print("⚠️ 删除了特征: rent_per_sqm")

        # 预测
        predictions = loaded_analyzer.predict_new_location(test_data)

        print(f"✅ 预测完成: {predictions.shape}")
        print("预测结果:")
        print(predictions[["store_id", "store_area", "predicted_sales"]])

        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_case_7_error_handling_too_few_data():
    """测试7: 数据量太少（10条以下）的错误处理"""
    print("\n" + "=" * 80)
    print("测试7: 错误处理 - 数据量太少（8条）")
    print("=" * 80)

    try:
        adapter = RetailDataAdapter()
        data = adapter.generate_sample_data(num_stores=8)
        print(f"✅ 生成数据: {data.shape}")

        config = RetailLocationConfig.get_default_config()
        analyzer = RetailLocationAnalyzer(config)

        # 应该抛出异常
        results = analyzer.run_full_analysis(data, save_results=False)
        print("❌ 应该抛出异常但没有！")
        return False
    except ValueError as e:
        print(f"✅ 正确抛出异常: {str(e)}")
        return True
    except Exception as e:
        print(f"❌ 抛出了意外的异常: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 80)
    print("零售门店分析框架 - 健壮性测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {}

    # 测试1: 正常数据
    success1, analyzer = test_case_1_normal_data()
    results["测试1: 正常数据"] = success1

    if not success1:
        print("\n❌ 测试1失败，无法继续后续测试")
        return

    # 测试2: 小数据
    results["测试2: 小数据(20条)"] = test_case_2_small_data()

    # 测试3: 最小数据
    results["测试3: 最小数据(15条)"] = test_case_3_minimum_data()

    # 测试4: 保存和加载
    success4, loaded_analyzer = test_case_4_save_and_load(analyzer)
    results["测试4: 模型保存加载"] = success4

    if success4:
        # 测试5: 预测
        results["测试5: 预测功能"] = test_case_5_prediction(loaded_analyzer)

        # 测试6: 预测时缺失特征
        results["测试6: 预测缺失特征"] = test_case_6_prediction_missing_features(loaded_analyzer)

    # 测试7: 错误处理
    results["测试7: 太少数据错误处理"] = test_case_7_error_handling_too_few_data()

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")

    passed_count = sum(1 for passed in results.values() if passed)
    total_count = len(results)
    print(f"\n总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 有测试失败，请检查")


if __name__ == "__main__":
    main()
