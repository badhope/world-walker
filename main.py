#!/usr/bin/env python3
"""Top-level entry point.

Run modes:

    python main.py --mode api          # start the FastAPI service
    python main.py --mode example      # run the example analyses
    python main.py --mode analysis --config <file>
    python main.py --mode check        # verify env
"""

import argparse
import json
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class EnvironmentChecker:
    @staticmethod
    def check_python_version() -> bool:
        required = (3, 9)
        current = sys.version_info[:2]
        if current < required:
            logger.error("Python %s.%s is too old, need >= %s.%s", *current, *required)
            return False
        logger.info("Python %s.%s.%s", *sys.version_info[:3])
        return True

    @staticmethod
    def check_dependencies() -> bool:
        packages = {
            "fastapi": "FastAPI",
            "uvicorn": "uvicorn",
            "pandas": "pandas",
            "numpy": "numpy",
            "pydantic_settings": "pydantic-settings",
            "scipy": "scipy",
        }
        missing = []
        for pkg, label in packages.items():
            try:
                __import__(pkg)
            except ImportError:
                missing.append(label)
        if missing:
            logger.error("Missing: %s", ", ".join(missing))
            logger.info("Run: pip install -r requirements.txt")
            return False
        return True

    @staticmethod
    def check_directories() -> bool:
        for d in ("data", "data/raw", "data/processed", "data/cache",
                  "data/exports", "config", "backend", "examples"):
            p = project_root / d
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                logger.info("Created %s", d)
        return True

    @staticmethod
    def check_config() -> bool:
        env = project_root / ".env"
        if env.exists():
            return True
        example = project_root / ".env.example"
        if example.exists():
            import shutil

            shutil.copy(example, env)
            logger.info("Copied .env.example -> .env (edit it before deploying)")
        return True

    @classmethod
    def run_check(cls) -> bool:
        logger.info("== environment check ==")
        checks = [
            ("python", cls.check_python_version),
            ("deps", cls.check_dependencies),
            ("dirs", cls.check_directories),
            ("config", cls.check_config),
        ]
        ok = True
        for name, fn in checks:
            try:
                ok = fn() and ok
            except Exception as exc:  # noqa: BLE001
                logger.error("check %s failed: %s", name, exc)
                ok = False
        return ok


def start_api(port: int, host: str, reload: bool) -> None:
    import uvicorn

    from backend.api.main import app

    uvicorn.run(app, host=host, port=port, reload=reload, log_level="info")


def run_example(analysis_type: str | None) -> None:
    if analysis_type == "enterprise":
        from examples.shenzhen_semiconductor_2025.enterprise_analysis import main as run

        run()
    elif analysis_type == "government":
        from examples.shenzhen_semiconductor_2025.government_analysis import main as run

        run()
    elif analysis_type == "comprehensive":
        from examples.shenzhen_semiconductor_2025.generate_report import main as run

        run()
    else:
        for kind in ("enterprise", "government", "comprehensive"):
            run_example(kind)


def run_analysis(config_file: str | None) -> None:
    if not config_file:
        logger.warning("no --config given, here's the shape I expect:")
        print(json.dumps(_example_analysis_config(), indent=2, ensure_ascii=False))
        return
    path = Path(config_file)
    if not path.exists():
        logger.error("config not found: %s", path)
        sys.exit(1)
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("invalid JSON: %s", exc)
        sys.exit(1)
    kind = cfg.get("type", "enterprise")
    dispatch = {
        "enterprise": _run_enterprise_from_config,
        "government": _run_government_from_config,
        "compare": _run_compare_from_config,
    }
    fn = dispatch.get(kind)
    if fn is None:
        logger.error("unsupported type %r (expected enterprise/government/compare)", kind)
        sys.exit(1)
    fn(cfg)


def _example_analysis_config() -> dict:
    return {
        "type": "enterprise",
        "city_name": "深圳",
        "industry": "半导体",
        "company_size": "中型",
    }


def _run_enterprise_from_config(cfg: dict) -> None:
    from backend.analysis.enterprise_analyzer_v3 import EnterpriseAnalyzerV3

    city = cfg.get("city_name", "深圳")
    result = EnterpriseAnalyzerV3().analyze(region=city)
    score = getattr(result, "overall_score", None)
    if score is None and isinstance(result, dict):
        score = result.get("overall_score") or result.get("score")
    if score is not None:
        print(f"{city}  score={score}")
    else:
        print(f"{city}  result={str(result)[:500]}")


def _run_government_from_config(cfg: dict) -> None:
    from backend.analysis.government_analyzer import GovernmentAnalyzer

    city = cfg.get("city_name", "深圳")
    payload = {"city": city, "fiscal_input": 1000.0, "industry_growth": 0.05}
    try:
        out = GovernmentAnalyzer().analyze_fiscal_leverage(payload)
    except Exception as exc:  # noqa: BLE001
        out = {"info": f"registered: {exc}"}
    print(json.dumps(out, ensure_ascii=False, indent=2)[:500])


def _run_compare_from_config(cfg: dict) -> None:
    from backend.data.city_data import compare_cities

    cities = cfg.get("cities", ["深圳", "上海", "北京"])
    df = compare_cities(cities)
    if df is None or len(df) == 0:
        print("no data for", cities)
        return
    print(df.to_string(index=False)[:1500])


def main() -> None:
    parser = argparse.ArgumentParser(description="Regional Economic Analysis — entry point")
    parser.add_argument(
        "--mode",
        choices=["api", "example", "analysis", "check"],
        default="check",
        help="what to run (default: check)",
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--reload", action="store_true", help="uvicorn --reload (dev only)")
    parser.add_argument("--type", choices=["enterprise", "government", "comprehensive"])
    parser.add_argument("--config", help="path to analysis config json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    EnvironmentChecker.run_check()

    if args.mode == "check":
        return
    if args.mode == "api":
        start_api(args.port, args.host, args.reload)
    elif args.mode == "example":
        run_example(args.type)
    elif args.mode == "analysis":
        run_analysis(args.config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        logger.exception("unexpected error: %s", exc)
        sys.exit(1)
