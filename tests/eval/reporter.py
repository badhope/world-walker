"""Eval 报表生成 — JSON + Markdown 两种格式。

输出:tests/eval/reports/<date>-<model>.{json,md}
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from tests.eval.scorer import CaseResult

REPORTS_DIR = Path(__file__).parent / "reports"


def _summary(results: list[CaseResult]) -> dict[str, Any]:
    if not results:
        return {"avg_score": 0, "pass_rate": 0, "total_cases": 0}
    avg = sum(r.score for r in results) / len(results)
    pass_rate = sum(1 for r in results if r.pass_) / len(results)
    return {
        "avg_score": round(avg, 2),
        "pass_rate": round(pass_rate, 3),
        "total_cases": len(results),
    }


def save_report(
    model: str,
    results: list[CaseResult],
    date_str: str | None = None,
) -> Path:
    """保存 JSON 报表。"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    # 清理模型名(替换 / 为 - 避免文件名问题)
    safe_model = model.replace("/", "-")
    path = REPORTS_DIR / f"{date_str}-{safe_model}.json"
    payload = {
        "model": model,
        "date": date_str,
        "summary": _summary(results),
        "cases": [
            {
                "id": r.case_id, "query": r.query,
                "actual_tools": r.actual_tools, "actual_args": r.actual_args,
                "actual_answer": r.actual_answer[:300],
                "actual_fallback_count": r.actual_fallback_count,
                "actual_total_tokens": r.actual_total_tokens,
                "actual_duration_sec": round(r.actual_duration_sec, 2),
                "score": r.score, "breakdown": r.breakdown, "pass": r.pass_,
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return path


def save_comparison(
    models: list[str],
    all_results: dict[str, list[CaseResult]],
    date_str: str | None = None,
) -> Path:
    """保存多模型对比报表(每个模型一份 JSON,加一份总览 MD 含 case 级别对比表)。"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    # 每个模型独立 JSON
    for m, results in all_results.items():
        save_report(m, results, date_str)
    # 总览 MD
    md_path = REPORTS_DIR / f"{date_str}-compare.md"
    lines = [f"# Eval 对比报告 — {date_str}", ""]
    # 汇总
    lines.append("## 汇总")
    lines.append("")
    lines.append("| 模型 | 平均分 | 通过率 | Case 数 |")
    lines.append("|------|--------|--------|---------|")
    for m, results in all_results.items():
        s = _summary(results)
        lines.append(f"| {m} | {s['avg_score']} | {s['pass_rate']*100:.0f}% | {s['total_cases']} |")
    lines.append("")

    # Case 级别对比
    if models and all_results:
        first_model = models[0]
        case_ids = [r.case_id for r in all_results[first_model]]
        lines.append("## Case 级别对比")
        lines.append("")
        header = "| Case | " + " | ".join(models) + " | 胜出 |"
        sep = "|------|" + "|".join("----" for _ in models) + "|------|"
        lines.append(header)
        lines.append(sep)
        for cid in case_ids:
            scores = []
            for m in models:
                # 找到该 case 的分数
                match = next((r.score for r in all_results[m] if r.case_id == cid), None)
                scores.append(f"{match:.0f}" if match is not None else "-")
            best_score = max(
                (next((r.score for r in all_results[m] if r.case_id == cid), -1) for m in models),
                default=-1,
            )
            winner = "平" if scores.count(scores[0]) == len(scores) else (
                models[scores.index(max(scores))] if any(s != "-" for s in scores) else "-"
            )
            lines.append(f"| {cid} | " + " | ".join(scores) + f" | {winner} |")
        lines.append("")

    md_path.write_text("\n".join(lines))
    return md_path
