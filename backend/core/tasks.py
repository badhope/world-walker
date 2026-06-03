"""
Celery 任务队列模块 - 异步任务处理系统
"""

import logging
import os
import sys
from datetime import timedelta

from celery import Celery

# 确保项目根目录在路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.cache import cache_manager

logger = logging.getLogger(__name__)

# 配置 Celery
app = Celery(
    "regional_economic_analysis",
    broker="redis://localhost:6379/1",  # Redis 作为 broker
    backend="redis://localhost:6379/2",  # Redis 作为结果存储
)

# 配置 Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分钟超时
    task_soft_time_limit=25 * 60,  # 25 分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=60 * 60 * 24,  # 24 小时结果过期
)

# 配置定时任务
app.conf.beat_schedule = {
    "daily-data-update": {
        "task": "backend.core.tasks.daily_data_update",
        "schedule": timedelta(hours=24),  # 每天执行
        "args": (),
    },
    "weekly-data-quality-check": {
        "task": "backend.core.tasks.weekly_data_quality_check",
        "schedule": timedelta(days=7),  # 每周执行
        "args": (),
    },
}

# 导入数据采集器
from backend.data_collection.finance_collector import FinanceCollector
from backend.data_collection.industry_collector import IndustryCollector
from backend.data_collection.nbs_collector import nbs_collector


@app.task(bind=True, name="backend.core.tasks.fetch_and_cache_data")
def fetch_and_cache_data(self, collector_name: str, **kwargs):
    """
    通用的数据采集和缓存任务

    Args:
        collector_name: 采集器名称
        **kwargs: 采集器参数

    Returns:
        采集结果
    """
    logger.info(f"开始数据采集任务: {collector_name}")

    try:
        # 根据采集器名称实例化
        if collector_name == "nbs":
            collector = nbs_collector
        elif collector_name == "industry":
            collector = IndustryCollector()
        elif collector_name == "finance":
            collector = FinanceCollector()
        else:
            raise ValueError(f"未知采集器: {collector_name}")

        # 执行采集
        if hasattr(collector, "fetch_all"):
            results = collector.fetch_all()
        else:
            results = collector.fetch_data(**kwargs)

        # 缓存结果（24小时）
        cache_key = f"data:{collector_name}:latest"
        cache_manager.set(cache_key, results, expire=86400)

        logger.info(
            f"数据采集任务完成: {collector_name}, 结果数: {len(results) if isinstance(results, list) else 'multiple'}"
        )
        return results

    except Exception as e:
        logger.error(f"数据采集任务失败: {e}", exc_info=True)
        self.retry(exc=e, countdown=60, max_retries=3)


@app.task(bind=True, name="backend.core.tasks.daily_data_update")
def daily_data_update(self):
    """
    每日数据更新任务
    """
    logger.info("开始每日数据更新任务")

    results = {}

    try:
        # 依次更新各个数据源
        for collector_name in ["nbs", "industry", "finance"]:
            try:
                result = fetch_and_cache_data.delay(collector_name)
                results[collector_name] = f"任务已提交: {result.id}"
            except Exception as e:
                logger.error(f"{collector_name} 数据更新失败: {e}")
                results[collector_name] = f"失败: {str(e)}"

        logger.info(f"每日数据更新任务完成: {results}")
        return results

    except Exception as e:
        logger.error(f"每日数据更新任务失败: {e}", exc_info=True)
        self.retry(exc=e, countdown=300, max_retries=5)


@app.task(bind=True, name="backend.core.tasks.weekly_data_quality_check")
def weekly_data_quality_check(self):
    """
    每周数据质量检查任务
    """
    logger.info("开始每周数据质量检查任务")

    quality_report = {"timestamp": __import__("datetime").datetime.now().isoformat(), "checks": [], "warnings": []}

    try:
        # 检查各数据源缓存状态
        for collector_name in ["nbs", "industry", "finance"]:
            cache_key = f"data:{collector_name}:latest"
            if cache_manager.exists(cache_key):
                quality_report["checks"].append({"source": collector_name, "status": "ok", "cached": True})
            else:
                quality_report["warnings"].append({"source": collector_name, "warning": "无缓存数据"})

        # 保存检查报告
        report_cache_key = "data_quality:latest_report"
        cache_manager.set(report_cache_key, quality_report, expire=604800)  # 1周过期

        logger.info(f"每周数据质量检查完成: {quality_report}")
        return quality_report

    except Exception as e:
        logger.error(f"每周数据质量检查失败: {e}", exc_info=True)
        self.retry(exc=e, countdown=3600, max_retries=3)


@app.task(bind=True, name="backend.core.tasks.custom_analysis_task")
def custom_analysis_task(self, analysis_type: str, params: dict):
    """
    自定义分析任务

    Args:
        analysis_type: 分析类型
        params: 分析参数

    Returns:
        分析结果
    """
    logger.info(f"开始自定义分析任务: {analysis_type}")

    try:
        # 根据分析类型导入相应的分析器
        if analysis_type == "enterprise":
            from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer

            analyzer = EnterpriseAnalyzer()
        elif analysis_type == "government":
            from backend.analysis.government_analyzer import GovernmentAnalyzer

            analyzer = GovernmentAnalyzer()
        else:
            raise ValueError(f"未知分析类型: {analysis_type}")

        # 执行分析
        city_name = params.get("city_name", "")
        if not city_name:
            raise ValueError(f"params.city_name is required for {analysis_type} analysis")
        result = analyzer.analyze_city(city_name)

        # 缓存结果（6小时）
        cache_key = f"analysis:{analysis_type}:{hash(str(params))}"
        cache_manager.set(cache_key, result, expire=21600)

        logger.info(f"自定义分析任务完成: {analysis_type}")
        return result

    except Exception as e:
        logger.error(f"自定义分析任务失败: {e}", exc_info=True)
        self.retry(exc=e, countdown=300, max_retries=3)


# 用于启动 Celery Worker 的函数
def start_worker():
    """启动 Celery Worker"""
    import subprocess
    import sys

    # 使用 subprocess 启动 Worker(列表参数 + shell=False 默认,无注入风险)
    subprocess.Popen(  # nosec B404 B603 - trusted internal command
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "backend.core.tasks",
            "worker",
            "--loglevel=info",
            "--concurrency=4",
            "-Q",
            "default",
        ]
    )
    logger.info("Celery Worker 已启动")


def start_beat():
    """启动 Celery Beat（定时任务调度器）"""
    import subprocess
    import sys

    subprocess.Popen([sys.executable, "-m", "celery", "-A", "backend.core.tasks", "beat", "--loglevel=info"])
    logger.info("Celery Beat 已启动")


if __name__ == "__main__":
    start_worker()
