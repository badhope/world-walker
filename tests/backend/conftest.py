"""
测试配置和共享夹具
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 测试环境默认允许无签名模型,这样所有 save/load 调用不会因缺 key 而抛错;
# 关键路径(safe_model_loader)仍有自己的覆盖测试。
os.environ.setdefault("ALLOW_UNSIGNED_MODELS", "1")
# 给一个固定 SECRET_KEY,避免 settings.py 在 import 时打 RuntimeWarning。
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
# 给 AI fallback 一个 fake API key,避免 load_config() 抛 ConfigError 让单测无法 import。
os.environ.setdefault("LLM_OPENAI_API_KEY", "sk-test-fake-key-for-unit-tests")
os.environ.setdefault("LLM_DEFAULT_BACKEND", "openai")
os.environ.setdefault("LLM_OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """项目根目录路径"""
    return project_root


@pytest.fixture(scope="session")
def test_data_path(project_root_path: Path) -> Path:
    """测试数据目录"""
    test_data_dir = project_root_path / "examples" / "shenzhen_semiconductor_2025" / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    return test_data_dir


@pytest.fixture(scope="session")
def sample_basic_data_path(test_data_path: Path) -> dict:
    """示例基础数据"""
    import json

    basic_data_file = test_data_path / "basic_data.json"
    if basic_data_file.exists():
        with open(basic_data_file, encoding="utf-8") as f:
            return json.load(f)
    return {"region": "深圳", "year": 2025, "gdp": 35000.0, "population": 1750.0}


@pytest.fixture(scope="function")
def mock_env_setup():
    """临时设置环境变量"""
    original_env = dict(os.environ)
    os.environ["TESTING"] = "1"
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def api_client():
    """FastAPI 测试客户端"""
    from backend.api.main import app

    return TestClient(app)


@pytest.fixture
def sample_indicator_data():
    """示例指标数据"""
    return {"name": "GDP增长率", "value": 5.8, "unit": "%", "year": 2025}


@pytest.fixture
def sample_enterprise_analysis_config():
    """企业分析示例配置"""
    return {"region": "深圳", "industry": "半导体", "year": 2025}


@pytest.fixture
def sample_government_analysis_config():
    """政府分析示例配置"""
    return {"region": "深圳", "industry": "半导体", "year": 2025}


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录"""
    return tmp_path


@pytest.fixture
def mock_data_collector_mock(mocker: MockerFixture):
    """数据采集器 Mock"""
    from backend.data_collection.base_collector import BaseCollector

    mock_instance = mocker.MagicMock(spec=BaseCollector)
    mock_instance.collect.return_value = {"success": True, "data": {"test": "data"}}
    return mock_instance


@pytest.fixture
def sample_industry_config():
    """产业配置示例"""
    return {"industry": "半导体", "description": "测试产业"}


@pytest.fixture
def sample_region_config():
    """区域配置示例"""
    return {"region": "深圳", "description": "测试区域"}
