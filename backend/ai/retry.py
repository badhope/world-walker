"""反射重试 — tool 失败时构造 hint 引导 LLM 改参数重试。

设计:
- RETRYABLE_TOOL_ERRORS 白名单:可重试的 tool 错误类型
- should_retry(result): 检查 tool 返的 error 字段是否在白名单
- build_retry_hint(tool_name, args, error): 构造 user 消息 hint

重试策略:
- 单 tool 失败 → chat_service 在同一 round 内追加 user hint
- LLM 下一轮会看到 hint + 之前的 tool result,自动改参数再调
- 最多 1 次反射重试(避免无限循环)— 在 chat_service 层面控制
"""
from __future__ import annotations

import json
from typing import Any


# 可重试的 tool 错误白名单(子串匹配,大小写不敏感)
# 这些错误通常是参数问题,改参数可解
RETRYABLE_TOOL_ERRORS: set[str] = {
    "city_not_found",          # 城市名拼写错(中文/拼音)
    "unknown city",            # tool_executor 的实际错误格式
    "data_unavailable",        # 数据缺失,换 scope/indicator
    "no data",                 # tool_executor 实际错误
    "missing_required_fields", # 缺必填参数
    "insufficient data",       # 数据不够
    "timeout",                 # tool 执行超时
}


# 错误类型 → 修复建议(中英混合,因为 LLM 看得懂)
_HINTS: dict[str, str] = {
    "city_not_found": "请检查城市名是否正确(中文/拼音),可调用 list_cities 获取支持的列表。",
    "data_unavailable": "请尝试换 scope(province/city/county)或换 indicator,或减少 years。",
    "missing_required_fields": "请检查并补充所有必填参数(参考 tool schema)。",
    "timeout": "请缩小查询范围(如减少 years)后重试。",
}


def should_retry(tool_result: dict[str, Any]) -> bool:
    """tool 返的 error 字段在 RETRYABLE_TOOL_ERRORS 白名单 → True。"""
    err = tool_result.get("error")
    if not err:
        return False
    # 子串匹配 + 大小写不敏感(支持 "city_not_found: 深圳" / "Unknown city: X" 等)
    err_lower = str(err).lower()
    return any(e.lower() in err_lower for e in RETRYABLE_TOOL_ERRORS)


def build_retry_hint(tool_name: str, original_args: dict[str, Any], error: str) -> str:
    """构造 user 消息 hint 引导 LLM 改参数重试。"""
    # 找匹配的 hint 模板
    template = None
    for key, text in _HINTS.items():
        if key in error:
            template = text
            break
    if not template:
        template = "请检查 tool 参数是否正确后重试。"

    args_str = json.dumps(original_args, ensure_ascii=False, default=str)[:300]
    return (
        f"[系统提示] tool `{tool_name}` 调用失败(错误: {error})。\n"
        f"原参数: {args_str}\n"
        f"建议: {template}"
    )
