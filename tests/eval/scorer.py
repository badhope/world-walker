"""Eval 评分 — 6 维度,每 case 0-100 分。

维度(权重):
- tool 选择(30)   集合完全匹配 = 30,部分匹配按比例
- args 匹配(20)   expected_args_match 全 key 命中 = 20,按命中比例
- 关键词(20)      expected_keywords 命中 >= 50% = 20,按比例
- 延迟(15)        < 10s = 15,< 30s = 10,< 60s = 5,>= 60s = 0
- fallback(10)     0 次 = 10,1 次 = 5,>= 2 次 = 0
- token 效率(5)   < 2K = 5,< 5K = 3,>= 5K = 1
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CaseResult:
    case_id: str
    query: str
    actual_tools: list[str]
    actual_args: list[dict]
    actual_answer: str
    actual_fallback_count: int
    actual_total_tokens: int
    actual_duration_sec: float
    score: float
    breakdown: dict[str, float]
    pass_: bool


def score_case(
    case: dict[str, Any],
    actual_tools: list[str],
    actual_args: list[dict],
    actual_answer: str,
    actual_fallback_count: int,
    actual_total_tokens: int,
    actual_duration_sec: float,
) -> CaseResult:
    """单 case 评分。"""
    breakdown: dict[str, float] = {}

    # 1. tool 选择(30)
    expected_tools = set(case["expected_tools"])
    actual_tools_set = set(actual_tools)
    if expected_tools:
        tool_match_ratio = len(expected_tools & actual_tools_set) / len(expected_tools)
    else:
        tool_match_ratio = 1.0
    breakdown["tool"] = round(tool_match_ratio * 30, 2)

    # 2. args 匹配(20)
    expected_args = case.get("expected_args_match", {})
    if expected_args:
        # 任一 actual_args 包含 expected_args 所有 key+value → 满分
        max_match = 0.0
        for a in actual_args:
            matches = sum(1 for k, v in expected_args.items() if a.get(k) == v)
            ratio = matches / len(expected_args)
            max_match = max(max_match, ratio)
        breakdown["args"] = round(max_match * 20, 2)
    else:
        breakdown["args"] = 20.0

    # 3. 关键词(20)
    expected_kw = case.get("expected_keywords", [])
    if expected_kw:
        kw_hits = sum(1 for kw in expected_kw if kw in actual_answer)
        kw_ratio = kw_hits / len(expected_kw)
        # 50% 命中即满分(用 min(1, ratio*2) 缩放)
        breakdown["keywords"] = round(min(1.0, kw_ratio * 2) * 20, 2)
    else:
        breakdown["keywords"] = 20.0

    # 4. 延迟(15)
    if actual_duration_sec < 10:
        breakdown["latency"] = 15.0
    elif actual_duration_sec < 30:
        breakdown["latency"] = 10.0
    elif actual_duration_sec < 60:
        breakdown["latency"] = 5.0
    else:
        breakdown["latency"] = 0.0

    # 5. fallback(10)
    if actual_fallback_count == 0:
        breakdown["fallback"] = 10.0
    elif actual_fallback_count == 1:
        breakdown["fallback"] = 5.0
    else:
        breakdown["fallback"] = 0.0

    # 6. token 效率(5)
    if actual_total_tokens < 2000:
        breakdown["tokens"] = 5.0
    elif actual_total_tokens < 5000:
        breakdown["tokens"] = 3.0
    else:
        breakdown["tokens"] = 1.0

    total = sum(breakdown.values())
    # pass 条件:总分 >= 70 AND tool 分 >= 20
    pass_ = total >= 70 and breakdown["tool"] >= 20

    return CaseResult(
        case_id=case["id"],
        query=case["query"],
        actual_tools=actual_tools,
        actual_args=actual_args,
        actual_answer=actual_answer,
        actual_fallback_count=actual_fallback_count,
        actual_total_tokens=actual_total_tokens,
        actual_duration_sec=actual_duration_sec,
        score=round(total, 2),
        breakdown=breakdown,
        pass_=pass_,
    )
