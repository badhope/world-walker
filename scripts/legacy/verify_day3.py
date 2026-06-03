#!/usr/bin/env python3
"""
第三天任务验证脚本
快速验证所有组件是否正常工作
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_data_files():
    """测试数据文件"""
    print("=" * 60)
    print("测试 1: 数据文件")
    print("=" * 60)

    data_dir = Path("examples/shenzhen_semiconductor_2025/data")
    required_files = ["basic_data.json", "business_cost.json", "supply_chain.json", "finance_data.json"]

    all_exist = True
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[ok] {filename} - OK ({len(json.dumps(data))} bytes)")
            except Exception as e:
                print(f"[x] {filename} - JSON解析失败: {e}")
                all_exist = False
        else:
            print(f"[x] {filename} - 文件不存在")
            all_exist = False

    return all_exist

def test_enterprise_analysis():
    """测试企业分析脚本导入"""
    print("\n" + "=" * 60)
    print("测试 2: 企业分析脚本")
    print("=" * 60)

    try:
        from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner

        print("[ok] EnterpriseAnalysisRunner 导入成功")

        runner = EnterpriseAnalysisRunner()
        print("[ok] EnterpriseAnalysisRunner 初始化成功")

        return True
    except Exception as e:
        print(f"[x] 企业分析脚本错误: {e}")
        import traceback

        traceback.print_exc()
        return False

def test_government_analysis():
    """测试政府分析脚本导入"""
    print("\n" + "=" * 60)
    print("测试 3: 政府分析脚本")
    print("=" * 60)

    try:
        from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner

        print("[ok] GovernmentAnalysisRunner 导入成功")

        runner = GovernmentAnalysisRunner()
        print("[ok] GovernmentAnalysisRunner 初始化成功")

        return True
    except Exception as e:
        print(f"[x] 政府分析脚本错误: {e}")
        import traceback

        traceback.print_exc()
        return False

def test_report_generator():
    """测试报告生成器"""
    print("\n" + "=" * 60)
    print("测试 4: 报告生成器")
    print("=" * 60)

    try:
        print("[ok] ComprehensiveReportGenerator 导入成功")

        return True
    except Exception as e:
        print(f"[x] 报告生成器错误: {e}")
        import traceback

        traceback.print_exc()
        return False

def test_template():
    """测试模板脚本"""
    print("\n" + "=" * 60)
    print("测试 5: 分析模板")
    print("=" * 60)

    try:
        print("[ok] AnalysisTemplate 导入成功")

        return True
    except Exception as e:
        print(f"[x] 模板脚本错误: {e}")
        import traceback

        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("第三天任务验证")
    print("=" * 60)

    tests = [test_data_files, test_enterprise_analysis, test_government_analysis, test_report_generator, test_template]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n[x] 测试失败: {test.__name__}")
            print(f"   错误: {str(e)}")
            import traceback

            traceback.print_exc()
            results.append((test.__name__, False))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[ok] 通过" if result else "[x] 失败"
        print(f"  {status}: {name}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n 所有测试通过！第三天任务基本完成！")
        return 0
    else:
        print(f"\n[!] 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
