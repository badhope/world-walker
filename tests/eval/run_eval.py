"""Eval CLI 入口。

用法:
    # 单模型
    python -m tests.eval.run_eval --model qwen-max

    # 多模型对比
    python -m tests.eval.run_eval --compare qwen-max deepseek-v3 kimi-k2.5

    # 跑指定 case 子集
    python -m tests.eval.run_eval --model qwen-max --ids shenzhen-gdp-forecast-3y
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from backend.ai.config import AIConfig
from backend.ai.fallback import ModelEntry, DEFAULT_FALLBACK_CHAIN
from backend.ai import chat_service
from tests.eval.scorer import score_case, CaseResult
from tests.eval.reporter import save_report, save_comparison


def _load_cases(path: Path, ids: list[str] | None = None) -> list[dict]:
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if ids:
        cases = [c for c in cases if c["id"] in ids]
    return cases


def _cfg_for_model(model: str) -> AIConfig:
    """构造一个只含指定模型的 AIConfig + fallback chain 仅含自己(避免链干扰评分)。"""
    return AIConfig(
        default_backend="openai",
        active_backend="openai",
        model=model,
        temperature=0.3,
        max_tokens=2000,
        timeout_sec=60,
        max_tool_rounds=5,
        available_backends=["openai"],
        fallback_chain=(ModelEntry("openai", model, 0, model),),
        tool_timeout_sec=30,
        parallel_max_workers=5,
    )


def _run_case(case: dict, cfg: AIConfig) -> CaseResult:
    """跑单 case,收集实际 tool/answer/fallback/tokens/duration,评分。"""
    actual_tools: list[str] = []
    actual_args: list[dict] = []
    fallback_count = 0
    total_tokens = 0
    answer_parts: list[str] = []
    t0 = time.perf_counter()
    try:
        for ev in chat_service.chat_stream_with_trace(cfg, f"eval-{case['id']}", case["query"]):
            if ev["type"] == "tool_call":
                actual_tools.append(ev["name"])
                actual_args.append(ev.get("args") or {})
            elif ev["type"] == "token":
                answer_parts.append(ev.get("content", ""))
            elif ev["type"] == "done":
                # 从 trace 统计 fallback 和 tokens
                for step in ev.get("trace", []):
                    if step.get("type") == "llm_call" and step.get("model_used") != cfg.model:
                        fallback_count += 1
                    total_tokens += step.get("metadata", {}).get("prompt_tokens", 0)
                    total_tokens += step.get("metadata", {}).get("completion_tokens", 0)
    except Exception as e:
        answer_parts.append(f"(eval error: {e})")
    duration = time.perf_counter() - t0
    return score_case(
        case=case,
        actual_tools=actual_tools,
        actual_args=actual_args,
        actual_answer="".join(answer_parts),
        actual_fallback_count=fallback_count,
        actual_total_tokens=total_tokens,
        actual_duration_sec=duration,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run eval against golden cases")
    parser.add_argument("--model", help="single model to evaluate")
    parser.add_argument("--compare", nargs="+", help="multiple models to compare")
    parser.add_argument("--ids", nargs="+", help="filter to specific case ids")
    args = parser.parse_args()

    cases_path = Path(__file__).parent / "golden_cases.jsonl"
    cases = _load_cases(cases_path, args.ids)
    print(f"Loaded {len(cases)} cases from {cases_path}")

    models = [args.model] if args.model else args.compare
    if not models:
        models = [e.model for e in DEFAULT_FALLBACK_CHAIN]
    print(f"Models: {models}")

    all_results: dict[str, list[CaseResult]] = {}
    for model in models:
        print(f"\n=== {model} ===")
        cfg = _cfg_for_model(model)
        results = []
        for case in cases:
            r = _run_case(case, cfg)
            marker = "PASS" if r.pass_ else "FAIL"
            print(f"  {marker} {case['id']:35s} score={r.score:5.1f} tools={r.actual_tools}")
            results.append(r)
        all_results[model] = results
        report_path = save_report(model, results)
        print(f"  Report: {report_path}")

    if len(all_results) > 1:
        cmp_path = save_comparison(list(all_results.keys()), all_results)
        print(f"\nComparison: {cmp_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
