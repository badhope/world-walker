#!/usr/bin/env python3
"""
区域产业经济分析平台 - 统一启动入口

提供多种启动模式：
- API模式：启动FastAPI服务
- 脚本模式：运行示例分析脚本
- 分析模式：执行自定义分析
- 检查模式：检查系统环境和依赖

使用方法：
    python main.py --mode api          # 启动API服务
    python main.py --mode example      # 运行示例分析
    python main.py --mode check        # 检查环境
    python main.py --help              # 显示帮助信息
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EnvironmentChecker:
    """环境检查器"""

    @staticmethod
    def check_python_version() -> bool:
        """检查Python版本"""
        required_version = (3, 9)
        current_version = sys.version_info[:2]

        if current_version < required_version:
            logger.error(f"❌ Python版本过低: {sys.version}")
            logger.error(f"   需要Python >= {required_version[0]}.{required_version[1]}")
            return False

        logger.info(f"✅ Python版本: {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")
        return True

    @staticmethod
    def check_dependencies() -> bool:
        """检查依赖包"""
        required_packages = {
            "fastapi": "FastAPI",
            "uvicorn": "uvicorn",
            "pandas": "pandas",
            "numpy": "numpy",
            "plotly": "plotly",
            "akshare": "akshare",
            "pydantic_settings": "pydantic-settings",
            "scipy": "scipy",
        }

        missing_packages = []

        for package, display_name in required_packages.items():
            try:
                __import__(package)
                logger.info(f"✅ {display_name}")
            except ImportError:
                logger.warning(f"❌ {display_name} (未安装)")
                missing_packages.append(package)

        if missing_packages:
            logger.error(f"\n缺少依赖包: {', '.join(missing_packages)}")
            logger.info("\n请运行以下命令安装依赖:")
            logger.info(f"  pip install {' '.join(missing_packages)}")
            logger.info("\n或运行一键安装:")
            logger.info("  bash scripts/setup.sh")
            return False

        return True

    @staticmethod
    def check_directories() -> bool:
        """检查必要目录"""
        required_dirs = [
            "data",
            "data/raw",
            "data/processed",
            "data/cache",
            "data/exports",
            "config",
            "backend",
            "examples",
        ]

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                logger.warning(f"❌ 目录不存在: {dir_name}")
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"   ✅ 已创建: {dir_name}")
            else:
                logger.info(f"✅ 目录存在: {dir_name}")

        return True

    @staticmethod
    def check_config() -> bool:
        """检查配置文件"""
        config_file = project_root / ".env"

        if not config_file.exists():
            env_example = project_root / ".env.example"
            if env_example.exists():
                logger.warning("⚠️ .env文件不存在，已从.env.example复制")
                import shutil

                shutil.copy(env_example, config_file)
                logger.info("✅ 已创建.env文件，请根据需要修改配置")
            else:
                logger.warning("⚠️ .env.example也不存在")

        return True

    @classmethod
    def run_check(cls) -> bool:
        """运行环境检查"""
        print("\n" + "=" * 60)
        print("🔍 环境检查")
        print("=" * 60)

        checks = [
            ("Python版本", cls.check_python_version),
            ("依赖包", cls.check_dependencies),
            ("目录结构", cls.check_directories),
            ("配置文件", cls.check_config),
        ]

        results = []
        for name, check_func in checks:
            print(f"\n--- {name} ---")
            result = check_func()
            results.append((name, result))

        print("\n" + "=" * 60)
        print("检查结果汇总")
        print("=" * 60)

        all_passed = True
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {status}: {name}")
            if not result:
                all_passed = False

        if all_passed:
            print("\n🎉 环境检查全部通过！")
        else:
            print("\n⚠️ 部分检查未通过，请根据提示修复问题")

        return all_passed


class APIMode:
    """API模式"""

    @staticmethod
    def run(port: int = 8000, host: str = "0.0.0.0", reload: bool = False):
        """启动API服务"""
        print("\n" + "=" * 60)
        print("🚀 启动API服务")
        print("=" * 60)

        try:
            import uvicorn

            from backend.api.main import app

            logger.info("📡 API服务配置:")
            logger.info(f"   地址: http://{host}:{port}")
            logger.info(f"   文档: http://{host}:{port}/docs")
            logger.info(f"   重载: {reload}")

            uvicorn.run(app, host=host, port=port, reload=reload, log_level="info")

        except Exception as e:
            logger.error(f"❌ API启动失败: {e}")
            logger.info("\n请确保已安装所有依赖:")
            logger.info("  pip install fastapi uvicorn")
            sys.exit(1)


class ExampleMode:
    """示例模式"""

    @staticmethod
    def run(analysis_type: str | None = None):
        """运行示例分析"""
        print("\n" + "=" * 60)
        print("📊 运行示例分析")
        print("=" * 60)

        try:
            if analysis_type == "enterprise":
                logger.info("🏢 运行企业端分析...")
                from examples.shenzhen_semiconductor_2025.enterprise_analysis import main as enterprise_main

                enterprise_main()

            elif analysis_type == "government":
                logger.info("🏛️ 运行政府端分析...")
                from examples.shenzhen_semiconductor_2025.government_analysis import main as government_main

                government_main()

            elif analysis_type == "comprehensive":
                logger.info("📋 生成综合分析报告...")
                from examples.shenzhen_semiconductor_2025.generate_report import main as report_main

                report_main()

            else:
                # 运行所有示例
                logger.info("🏢 运行企业端分析...")
                from examples.shenzhen_semiconductor_2025.enterprise_analysis import main as enterprise_main

                enterprise_main()

                print("\n" + "-" * 60)
                logger.info("🏛️ 运行政府端分析...")
                from examples.shenzhen_semiconductor_2025.government_analysis import main as government_main

                government_main()

                print("\n" + "-" * 60)
                logger.info("📋 生成综合分析报告...")
                from examples.shenzhen_semiconductor_2025.generate_report import main as report_main

                report_main()

            print("\n" + "=" * 60)
            print("✅ 示例分析完成！")
            print("=" * 60)
            print("\n📁 报告输出目录: examples/shenzhen_semiconductor_2025/outputs/")
            print("📄 查看HTML报告: examples/shenzhen_semiconductor_2025/outputs/*.html")

        except Exception as e:
            logger.error(f"❌ 示例运行失败: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


class AnalysisMode:
    """分析模式"""

    @staticmethod
    def run(config_file: str | None = None):
        """运行自定义分析"""
        print("\n" + "=" * 60)
        print("🔬 运行自定义分析")
        print("=" * 60)

        if not config_file:
            logger.warning("未提供 --config 参数。")
            print("\n用法:")
            print("  python main.py --mode analysis --config <path-to-config.json>")
            print("\n配置文件示例 (analysis_config.json):")
            print(json.dumps(_example_analysis_config(), indent=2, ensure_ascii=False))
            return

        config_path = Path(config_file)
        if not config_path.exists():
            logger.error(f"❌ 配置文件不存在: {config_path}")
            sys.exit(1)

        try:
            with open(config_path, encoding="utf-8") as fh:
                config = json.load(fh)
        except json.JSONDecodeError as exc:
            logger.error(f"❌ 配置文件不是合法 JSON: {exc}")
            sys.exit(1)

        analysis_kind = config.get("type", "enterprise")
        logger.info(f"分析类型: {analysis_kind}")

        if analysis_kind == "enterprise":
            _run_enterprise_from_config(config)
        elif analysis_kind == "government":
            _run_government_from_config(config)
        elif analysis_kind == "compare":
            _run_compare_from_config(config)
        else:
            logger.error(f"❌ 不支持的 type: {analysis_kind!r}")
            sys.exit(1)

        print("\n✅ 自定义分析完成！")


def _example_analysis_config() -> dict:
    """返回一份用于演示的最小配置文件结构。"""
    return {
        "type": "enterprise",
        "city_name": "深圳",
        "industry": "半导体",
        "company_size": "中型",
    }


def _run_enterprise_from_config(config: dict) -> None:
    """根据配置运行企业端分析。"""
    from backend.analysis.enterprise_analyzer_v3 import EnterpriseAnalyzerV3

    city = config.get("city_name", "深圳")

    analyzer = EnterpriseAnalyzerV3()
    result = analyzer.analyze(region=city)
    score = None
    if hasattr(result, "overall_score"):
        score = result.overall_score
    elif isinstance(result, dict):
        score = result.get("overall_score") or result.get("score") or result.get("comprehensive_score")

    if score is not None:
        print(f"\n{city} 企业端综合得分: {score}")
    else:
        print(f"\n{city} 企业端分析结果: {str(result)[:500]}")


def _run_government_from_config(config: dict) -> None:
    """根据配置运行政府端分析。"""
    from backend.analysis.government_analyzer import GovernmentAnalyzer

    city = config.get("city_name", "深圳")
    analyzer = GovernmentAnalyzer()
    # 构造用于 fiscal_leverage / industry_driving 的最小数据
    payload = {
        "city": city,
        "fiscal_input": 1000.0,
        "industry_growth": 0.05,
    }
    try:
        result = analyzer.analyze_fiscal_leverage(payload)
    except Exception as exc:
        result = {"info": f"政府端分析已注册: {exc}"}
    print(f"\n{city} 政府端分析结果: {json.dumps(result, ensure_ascii=False)[:500]}")


def _run_compare_from_config(config: dict) -> None:
    """根据配置运行城市对比。"""
    from backend.data.city_data import compare_cities as _compare

    cities = config.get("cities", ["深圳", "上海", "北京"])
    df = _compare(cities)
    if df is None or len(df) == 0:
        print(f"\n对比 {cities} 失败：没有可用数据。")
        return
    print(f"\n城市对比结果:\n{df.to_string(index=False)[:1500]}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="区域产业经济分析平台 - 统一启动入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --mode api                    # 启动API服务（默认端口8000）
  %(prog)s --mode api --port 8080        # 自定义端口
  %(prog)s --mode example                 # 运行所有示例
  %(prog)s --mode example --type enterprise  # 仅运行企业端分析
  %(prog)s --mode check                  # 检查环境
  %(prog)s --mode analysis               # 运行自定义分析

更多信息:
  API文档: http://localhost:8000/docs
  项目主页: https://github.com/your-org/regional-economic-analysis
        """,
    )

    parser.add_argument(
        "--mode", choices=["api", "example", "analysis", "check"], default="check", help="启动模式 (默认: check)"
    )

    parser.add_argument("--port", type=int, default=8000, help="API服务端口 (默认: 8000)")

    parser.add_argument("--host", type=str, default="0.0.0.0", help="API服务地址 (默认: 0.0.0.0)")

    parser.add_argument("--reload", action="store_true", help="启用代码热重载 (仅开发模式)")

    parser.add_argument("--type", choices=["enterprise", "government", "comprehensive"], help="示例分析类型")

    parser.add_argument("--config", type=str, help="自定义分析配置文件")

    parser.add_argument("--verbose", action="store_true", help="显示详细日志")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 执行对应模式
    if args.mode == "check":
        EnvironmentChecker.run_check()

    elif args.mode == "api":
        # 先检查环境
        if not EnvironmentChecker.run_check():
            print("\n⚠️ 环境检查未完全通过，但尝试启动API...")
        APIMode.run(port=args.port, host=args.host, reload=args.reload)

    elif args.mode == "example":
        # 先检查环境
        if not EnvironmentChecker.run_check():
            print("\n⚠️ 环境检查未完全通过，但尝试运行示例...")
        ExampleMode.run(analysis_type=args.type)

    elif args.mode == "analysis":
        # 先检查环境
        if not EnvironmentChecker.run_check():
            print("\n⚠️ 环境检查未完全通过，但尝试运行分析...")
        AnalysisMode.run(config_file=args.config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 发生未预期的错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
