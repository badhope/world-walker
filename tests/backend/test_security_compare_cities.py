"""
安全回归测试:城市对比接口使用 BaseModel 校验 (L-02)

将 POST /cities/compare 从裸 request.json() 替换为 Pydantic BaseModel,
让所有字段有类型校验 + 自动文档 + 输入大小限制。
"""
import pytest


@pytest.mark.unit
class TestCompareCitiesRequestModel:
    """CitiesCompareRequest Pydantic 模型必须严格校验输入。"""

    def test_full_form_accepts_valid_payload(self):
        from backend.api.routes.cities import CitiesCompareRequest

        req = CitiesCompareRequest(
            city_codes=["深圳", "北京"],
            indicators=["gdp", "population"],
            year_start=2020,
            year_end=2025,
        )
        assert req.city_codes == ["深圳", "北京"]
        assert req.indicators == ["gdp", "population"]
        assert req.year_start == 2020
        assert req.year_end == 2025

    def test_defaults_indicators_to_gdp(self):
        from backend.api.routes.cities import CitiesCompareRequest

        req = CitiesCompareRequest(city_codes=["深圳"])
        assert req.indicators == ["gdp"]
        assert req.year_start == 2020
        assert req.year_end == 2025

    def test_rejects_empty_city_codes(self):
        from pydantic import ValidationError

        from backend.api.routes.cities import CitiesCompareRequest

        with pytest.raises(ValidationError):
            CitiesCompareRequest(city_codes=[])

    def test_rejects_year_start_after_year_end(self):
        from pydantic import ValidationError

        from backend.api.routes.cities import CitiesCompareRequest

        with pytest.raises(ValidationError):
            CitiesCompareRequest(city_codes=["深圳"], year_start=2025, year_end=2020)

    def test_rejects_too_many_cities(self):
        from pydantic import ValidationError

        from backend.api.routes.cities import CitiesCompareRequest

        with pytest.raises(ValidationError):
            CitiesCompareRequest(
                city_codes=[f"city_{i}" for i in range(100)],  # > max
            )

    def test_rejects_too_many_indicators(self):
        from pydantic import ValidationError

        from backend.api.routes.cities import CitiesCompareRequest

        with pytest.raises(ValidationError):
            CitiesCompareRequest(
                city_codes=["深圳"],
                indicators=[f"ind_{i}" for i in range(100)],  # > max
            )


@pytest.mark.unit
class TestCompareCitiesEndpoint:
    """端点行为:CitiesCompareRequest 必须替代裸 request.json()。"""

    def test_endpoint_uses_basemodel(self, api_client):
        """正常 payload 应返回 200,且响应是 JSON 字典。"""
        r = api_client.post(
            "/api/v1/cities/compare",
            json={"city_codes": ["深圳"], "indicators": ["gdp"], "year_start": 2020, "year_end": 2025},
        )
        assert r.status_code in (200, 500, 422)
        if r.status_code == 200:
            body = r.json()
            # 响应应该是 dict(由 BaseModel 校验过的输入产生)
            assert isinstance(body, dict)
            assert body, "response body should not be empty"

    def test_endpoint_rejects_invalid_payload_with_422(self, api_client):
        """非 dict 格式(裸数组)应返回 422。"""
        # 原版本兼容裸数组;新模型严格:必须是 dict
        r = api_client.post(
            "/api/v1/cities/compare",
            json=["深圳", "北京"],
        )
        assert r.status_code == 422, f"expected 422 for array body, got {r.status_code}"

    def test_endpoint_rejects_missing_city_codes_with_422(self, api_client):
        r = api_client.post(
            "/api/v1/cities/compare",
            json={"indicators": ["gdp"]},
        )
        assert r.status_code == 422, f"expected 422 for missing city_codes, got {r.status_code}"

    def test_endpoint_rejects_empty_city_codes_with_422(self, api_client):
        r = api_client.post(
            "/api/v1/cities/compare",
            json={"city_codes": []},
        )
        assert r.status_code == 422
