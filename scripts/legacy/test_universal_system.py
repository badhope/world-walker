#!/usr/bin/env python3
"""
测试通用数据分析系统
验证所有功能是否正常工作
"""

import logging
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

print("=" * 80)
print("通用数据分析系统 - 完整测试")
print("=" * 80)

# 1. 测试导入
print("\n" + "=" * 80)
print("1. 测试模块导入")
print("=" * 80)
try:
    from backend import (
        UniversalAnalyzer,
        create_sample_data,
        get_available_models,
        quick_start_demo,
    )

    print("✓ 核心模块导入成功")
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 2. 测试模型可用性
print("\n" + "=" * 80)
print("2. 检查可用模型")
print("=" * 80)
try:
    models = get_available_models()
    print(f"✓ 可用模型: {models}")
except Exception as e:
    print(f"✗ 获取模型列表失败: {e}")

# 3. 测试创建示例数据
print("\n" + "=" * 80)
print("3. 测试创建示例数据")
print("=" * 80)
try:
    sample_df = create_sample_data(n_regions=5, n_years=3)
    print(f"✓ 示例数据创建成功: {sample_df.shape}")
    print(f"✓ 数据列: {sample_df.columns.tolist()}")
    print("\n✓ 数据预览:")
    print(sample_df.head())
except Exception as e:
    print(f"✗ 创建示例数据失败: {e}")
    import traceback

    traceback.print_exc()

# 4. 测试快速开始演示
print("\n" + "=" * 80)
print("4. 运行快速开始演示")
print("=" * 80)
try:
    result = quick_start_demo()
    print("\n✓ 快速演示运行成功")
except Exception as e:
    print(f"✗ 快速演示失败: {e}")
    import traceback

    traceback.print_exc()

# 5. 测试单独功能
print("\n" + "=" * 80)
print("5. 测试单独功能")
print("=" * 80)
try:
    from backend import UniversalAnalyzer

    analyzer = UniversalAnalyzer()
    print(f"✓ 分析器创建成功: {analyzer.config.project_name}")

    # 加载数据
    df = create_sample_data()
    dataset = analyzer.load_data_from_dataframe(df, name="test_data")
    print(f"✓ 数据加载成功: {len(dataset.data)} 条记录")

    # 简单分析（不运行ML）
    analysis_result = analyzer.analyze(run_ml=False)
    print(f"✓ 基础分析完成: {len(analysis_result.insights)} 条洞察")

except Exception as e:
    print(f"✗ 单独功能测试失败: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成!")
print("=" * 80)
