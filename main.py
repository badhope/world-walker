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
import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
            'fastapi': 'FastAPI',
            'uvicorn': 'uvicorn',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'plotly': 'plotly',
            'akshare': 'akshare',
            'pydantic_settings': 'pydantic-settings',
            'scipy': 'scipy'
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
            'data',
            'data/raw',
            'data/processed',
            'data/cache',
            'data/exports',
            'config',
            'backend',
            'examples'
        ]
        
        all_exist = True
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                logger.warning(f"❌ 目录不存在: {dir_name}")
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"   ✅ 已创建: {dir_name}")
                all_exist = False
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
            ("配置文件", cls.check_config)
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
    def run(port: int = 8001, host: str = "0.0.0.0", reload: bool = False):
        """启动API服务"""
        print("\n" + "=" * 60)
        print("🚀 启动API服务")
        print("=" * 60)
        
        try:
            import uvicorn
            from backend.api.main import app
            
            logger.info(f"📡 API服务配置:")
            logger.info(f"   地址: http://{host}:{port}")
            logger.info(f"   文档: http://{host}:{port}/docs")
            logger.info(f"   重载: {reload}")
            
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=reload,
                log_level="info"
            )
            
        except Exception as e:
            logger.error(f"❌ API启动失败: {e}")
            logger.info("\n请确保已安装所有依赖:")
            logger.info("  pip install fastapi uvicorn")
            sys.exit(1)


class ExampleMode:
    """示例模式"""
    
    @staticmethod
    def run(analysis_type: Optional[str] = None):
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
    def run(config_file: Optional[str] = None):
        """运行自定义分析"""
        print("\n" + "=" * 60)
        print("🔬 运行自定义分析")
        print("=" * 60)
        
        logger.info("自定义分析功能开发中...")
        logger.info("请使用 --config 参数指定配置文件")
        
        # TODO: 实现自定义分析功能
        print("\n示例:")
        print("  python main.py --mode analysis --config my_config.json")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="区域产业经济分析平台 - 统一启动入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --mode api                    # 启动API服务（默认端口8001）
  %(prog)s --mode api --port 8080        # 自定义端口
  %(prog)s --mode example                 # 运行所有示例
  %(prog)s --mode example --type enterprise  # 仅运行企业端分析
  %(prog)s --mode check                  # 检查环境
  %(prog)s --mode analysis               # 运行自定义分析

更多信息:
  API文档: http://localhost:8001/docs
  项目主页: https://github.com/your-project
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['api', 'example', 'analysis', 'check'],
        default='check',
        help='启动模式 (默认: check)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8001,
        help='API服务端口 (默认: 8001)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='API服务地址 (默认: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='启用代码热重载 (仅开发模式)'
    )
    
    parser.add_argument(
        '--type',
        choices=['enterprise', 'government', 'comprehensive'],
        help='示例分析类型'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='自定义分析配置文件'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 执行对应模式
    if args.mode == 'check':
        EnvironmentChecker.run_check()
        
    elif args.mode == 'api':
        # 先检查环境
        if not EnvironmentChecker.run_check():
            print("\n⚠️ 环境检查未完全通过，但尝试启动API...")
        APIMode.run(port=args.port, host=args.host, reload=args.reload)
        
    elif args.mode == 'example':
        # 先检查环境
        if not EnvironmentChecker.run_check():
            print("\n⚠️ 环境检查未完全通过，但尝试运行示例...")
        ExampleMode.run(analysis_type=args.type)
        
    elif args.mode == 'analysis':
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
