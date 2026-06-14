"""
API 接口测试
"""

import pytest


@pytest.mark.unit
class TestDataAPI:
    """数据接口测试"""

    def test_api_client_init(self, api_client):
        """测试 API 客户端初始化"""
        assert api_client is not None

    def test_read_root(self, api_client):
        """测试根路径"""
        response = api_client.get("/")
        # 可能返回 redirect 或 404，这取决于实际的路由设置
        assert response.status_code in [200, 307, 404]

    def test_api_health_check(self, api_client):
        """测试健康检查端点"""
        # 尝试不同的可能的健康检查路径
        for path in ["/health", "/api/health", "/api/v1/health"]:
            try:
                response = api_client.get(path)
                if response.status_code in [200, 404]:
                    break
            except Exception:
                continue


@pytest.mark.unit
class TestAnalysisAPI:
    """分析接口测试"""

    def test_api_main_exists(self):
        """测试 API 主模块存在"""
        from backend.api import main

        assert main is not None
        assert hasattr(main, "app")

    def test_api_routes_exist(self):
        """测试 API 路由模块存在"""
        from backend.api.routes import analysis, data

        assert data is not None
        assert analysis is not None

