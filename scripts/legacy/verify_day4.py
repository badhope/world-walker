#!/usr/bin/env python3
"""
第四天任务验证脚本
验证启动流程和文档功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_main_entry():
    """测试主入口"""
    print("=" * 60)
    print("测试 1: main.py 统一入口")
    print("=" * 60)

    try:
        from main import EnvironmentChecker

        # 测试环境检查
        checker = EnvironmentChecker()
        print("✅ EnvironmentChecker 导入成功")

        # 测试检查方法
        assert hasattr(checker, "check_python_version")
        assert hasattr(checker, "check_dependencies")
        assert hasattr(checker, "check_directories")
        print("✅ 检查方法完整")

        return True
    except Exception as e:
        print(f"❌ main.py 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_setup_py():
    """测试 setup.py"""
    print("\n" + "=" * 60)
    print("测试 2: setup.py 配置")
    print("=" * 60)

    setup_file = Path("setup.py")
    if not setup_file.exists():
        print("❌ setup.py 不存在")
        return False

    print("✅ setup.py 存在")

    try:
        with open(setup_file, encoding="utf-8") as f:
            content = f.read()
            if "setuptools" in content and "find_packages" in content:
                print("✅ setup.py 配置正确")
                return True
            else:
                print("❌ setup.py 配置不完整")
                return False
    except Exception as e:
        print(f"❌ 读取 setup.py 失败: {e}")
        return False


def test_scripts():
    """测试便捷脚本"""
    print("\n" + "=" * 60)
    print("测试 3: 便捷脚本")
    print("=" * 60)

    scripts_dir = Path("scripts")
    required_scripts = ["setup.sh", "run_example.sh", "start_api.sh"]

    all_exist = True
    for script in required_scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            print(f"✅ {script} 存在")
        else:
            print(f"❌ {script} 不存在")
            all_exist = False

    return all_exist


def test_documentation():
    """测试文档"""
    print("\n" + "=" * 60)
    print("测试 4: 文档完整性")
    print("=" * 60)

    docs_dir = Path("docs")
    required_docs = ["README.md", "USAGE_GUIDE.md", "CONFIG_GUIDE.md", "EXAMPLE_ANALYSIS.md", "DEVELOPER_GUIDE.md"]

    all_exist = True
    for doc in required_docs:
        if doc == "README.md":
            doc_path = Path(doc)
        else:
            doc_path = docs_dir / doc

        if doc_path.exists():
            # 检查文件大小
            size = doc_path.stat().st_size
            print(f"✅ {doc} 存在 ({size} bytes)")

            # 检查是否为空
            if size < 100:
                print(f"⚠️ {doc} 内容过少")
        else:
            print(f"❌ {doc} 不存在")
            all_exist = False

    return all_exist


def test_project_structure():
    """测试项目结构"""
    print("\n" + "=" * 60)
    print("测试 5: 项目结构")
    print("=" * 60)

    required_dirs = [
        "backend",
        "backend/api",
        "backend/data_collection",
        "backend/data_processing",
        "backend/analysis",
        "backend/utils",
        "config",
        "config/regions",
        "config/industries",
        "examples",
        "examples/shenzhen_semiconductor_2025",
        "examples/template",
        "scripts",
        "docs",
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ 不存在")
            all_exist = False

    return all_exist


def test_examples():
    """测试示例脚本"""
    print("\n" + "=" * 60)
    print("测试 6: 示例脚本")
    print("=" * 60)

    example_dir = Path("examples/shenzhen_semiconductor_2025")

    required_files = ["enterprise_analysis.py", "government_analysis.py", "generate_report.py"]

    data_dir = example_dir / "data"
    if not data_dir.exists():
        print("❌ 示例数据目录不存在")
        return False

    data_files = list(data_dir.glob("*.json"))
    print(f"✅ 找到 {len(data_files)} 个数据文件")

    all_exist = True
    for file in required_files:
        file_path = example_dir / file
        if file_path.exists():
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 不存在")
            all_exist = False

    return all_exist


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("第四天任务验证 - 启动流程和文档")
    print("=" * 60)

    tests = [
        ("main.py 统一入口", test_main_entry),
        ("setup.py 配置", test_setup_py),
        ("便捷脚本", test_scripts),
        ("文档完整性", test_documentation),
        ("项目结构", test_project_structure),
        ("示例脚本", test_examples),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试失败: {name}")
            print(f"   错误: {str(e)}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！第四天任务完成！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
