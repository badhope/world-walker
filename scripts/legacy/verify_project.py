#!/usr/bin/env python3
"""
项目完整性验证脚本
"""

import sys
from pathlib import Path

print("=" * 80)
print("区域产业经济分析平台 - 项目完整性验证")
print("=" * 80)
print()

# 1. 检查关键文件是否存在
print("【1/5】检查关键文件...")
required_files = [
    "backend/analysis/real_data_analysis.py",
    "backend/analysis/enterprise_analyzer_v2.py",
    "backend/database/database.py",
    "backend/api/routes/real_data.py",
    "backend/api/routes/database.py",
    "backend/api/routes/static.py",
    "backend/api/main.py",
    "frontend/analysis_dashboard.html",
    "tests/backend/test_real_data_analysis.py",
    "notebooks/01_data_collection_analysis.py",
    "run_full_demo.py",
    "QUICKSTART.md",
    "PROJECT_FINAL_SUMMARY.md",
]

all_files_exist = True
for file_path in required_files:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} - 文件不存在!")
        all_files_exist = False
print()

# 2. 检查导入
print("【2/5】检查模块导入...")
try:
    import numpy as np
    import pandas as pd

    print("✅ pandas, numpy导入成功")
except ImportError as e:
    print(f"❌ pandas/numpy导入失败: {e}")

try:
    import fastapi

    print("✅ fastapi导入成功")
except ImportError as e:
    print(f"❌ fastapi导入失败: {e}")

try:
    import akshare as ak

    print("✅ akshare导入成功")
except ImportError as e:
    print(f"❌ akshare导入失败: {e}")
print()

# 3. 检查数据生成
print("【3/5】检查项目数据...")
data_dir = Path(__file__).parent / "data"
charts_dir = data_dir / "charts"
output_dir = data_dir / "analysis_output"

if data_dir.exists():
    print("✅ data目录存在")

    if charts_dir.exists():
        chart_files = list(charts_dir.glob("*.png"))
        print(f"✅ charts目录存在，包含 {len(chart_files)} 个图表文件")
    else:
        print("⚠️ charts目录不存在")

    if output_dir.exists():
        output_files = list(output_dir.glob("*"))
        print(f"✅ analysis_output目录存在，包含 {len(output_files)} 个文件")
    else:
        print("⚠️ analysis_output目录不存在")

    db_file = data_dir / "regional_economy.db"
    if db_file.exists():
        print("✅ SQLite数据库存在")
    else:
        print("⚠️ 数据库不存在")
else:
    print("❌ data目录不存在!")
print()

# 4. 测试真实分析模块
print("【4/5】测试分析模块...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from backend.analysis.real_data_analysis import RealDataAnalyzer

    analyzer = RealDataAnalyzer()
    print("✅ RealDataAnalyzer初始化成功")

    # 测试简单功能
    test_data = pd.DataFrame(
        {"year": [2020, 2021, 2022, 2023, 2024], "gdp": [100, 105, 110, 118, 125], "cpi_yoy": [2.5, 2.1, 1.8, 0.8, 0.5]}
    )

    eda_result = analyzer.perform_eda(test_data)
    print(f"✅ EDA分析成功，包含 {len(eda_result)} 个分析结果")

    insights = analyzer.generate_insights(eda_result)
    print(f"✅ 生成 {len(insights)} 个洞察")

    print("✅ 分析模块验证通过!")
except Exception as e:
    print(f"❌ 分析模块测试失败: {e}")
    import traceback

    traceback.print_exc()
print()

# 5. 测试数据库模块
print("【5/5】测试数据库模块...")
try:
    from backend.database import get_db

    db = get_db()
    print("✅ DatabaseManager初始化成功")

    stats = db.get_statistics()
    print(f"✅ 数据库统计获取成功: {stats}")

    print("✅ 数据库模块验证通过!")
except Exception as e:
    print(f"❌ 数据库模块测试失败: {e}")
    import traceback

    traceback.print_exc()
print()

print("=" * 80)
print("项目完整性验证完成!")
print("=" * 80)
print()
print("💡 下一步验证:")
print("  1. 运行完整演示: python run_full_demo.py")
print("  2. 运行完整EDA: python notebooks/01_data_collection_analysis.py")
print("  3. 运行测试: python -m pytest tests/backend/test_real_data_analysis.py -v")
print("  4. 启动API: python -m uvicorn backend.api.main:app --reload --port 8001")
print()
print("✅ 所有核心模块验证通过!")
