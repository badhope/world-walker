"""eval 框架单元测试 — 不跑真 LLM,只测 scorer/reporter/case loader。"""

import json
import pytest
from pathlib import Path
from tests.eval.scorer import score_case
from tests.eval.reporter import save_report, save_comparison
from tests.eval.run_eval import _load_cases


def test_score_case_perfect_match():
    case = {
        "id": "t1", "query": "q", "expected_tools": ["get_forecast"],
        "expected_args_match": {"scope": "city", "name": "shenzhen"},
        "expected_keywords": ["深圳"],
    }
    r = score_case(
        case=case,
        actual_tools=["get_forecast"],
        actual_args=[{"scope": "city", "name": "shenzhen", "years": 3}],
        actual_answer="深圳 2026 GDP 4.42 万亿",
        actual_fallback_count=0,
        actual_total_tokens=1500,
        actual_duration_sec=8.0,
    )
    assert r.score == 100.0
    assert r.pass_ is True


def test_score_case_wrong_tool_fails():
    case = {
        "id": "t2", "query": "q", "expected_tools": ["get_forecast"],
        "expected_args_match": {}, "expected_keywords": [],
    }
    r = score_case(
        case=case,
        actual_tools=["list_cities"],  # 错
        actual_args=[],
        actual_answer="x", actual_fallback_count=0,
        actual_total_tokens=100, actual_duration_sec=2.0,
    )
    assert r.breakdown["tool"] == 0.0
    assert r.pass_ is False  # tool 分 < 20


def test_score_case_partial_args_match():
    case = {
        "id": "t3", "query": "q", "expected_tools": ["get_forecast"],
        "expected_args_match": {"scope": "city", "name": "shenzhen"},
        "expected_keywords": [],
    }
    r = score_case(
        case=case,
        actual_tools=["get_forecast"],
        actual_args=[{"scope": "city", "name": "shanghai"}],  # 错 1 个
        actual_answer="x", actual_fallback_count=0,
        actual_total_tokens=100, actual_duration_sec=2.0,
    )
    assert r.breakdown["args"] == 10.0  # 50% match


def test_load_cases_filters_by_ids():
    cases = _load_cases(Path("tests/eval/golden_cases.jsonl"), ids=["shenzhen-gdp-forecast-3y"])
    assert len(cases) == 1
    assert cases[0]["id"] == "shenzhen-gdp-forecast-3y"


def test_load_cases_all():
    cases = _load_cases(Path("tests/eval/golden_cases.jsonl"))
    assert len(cases) == 10


def test_save_report_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("tests.eval.reporter.REPORTS_DIR", tmp_path)
    case = {"id": "r1", "query": "q", "expected_tools": ["get_forecast"],
            "expected_args_match": {}, "expected_keywords": []}
    r = score_case(case, ["get_forecast"], [{}], "深圳", 0, 100, 5.0)
    path = save_report("test-model", [r])
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["model"] == "test-model"
    assert data["summary"]["total_cases"] == 1
    assert data["cases"][0]["id"] == "r1"
