"""
Chat service — 主循环:用户问题 → LLM + tool 循环 → 最终答案。

v8.0 增强:
- 多模型 fallback(run_with_fallback)
- 并行 tool(execute_tools_parallel)
- Trace 日志(Step + TraceStore)
- 反射重试(should_retry + build_retry_hint)
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from backend.ai import conversation
from backend.ai.config import AIConfig
from backend.ai.fallback import FallbackError, FatalLLMError, run_with_fallback
from backend.ai.llm_client import LLMError
from backend.ai.parallel_tools import execute_tools_parallel
from backend.ai.prompts import SYSTEM_PROMPT
from backend.ai.retry import build_retry_hint, should_retry
from backend.ai.tool_registry import TOOLS
from backend.ai.trace import Step, TraceStore

logger = logging.getLogger(__name__)

# 通过模块属性访问,让 monkeypatch.setattr(chat_service, "llm_client", ...) 能拦截
llm_client = __import__("backend.ai.llm_client", fromlist=["chat"])


def _build_messages(session_id: str, user_message: str) -> list[dict[str, Any]]:
    """构造发给 LLM 的 messages: system + 历史 + 当前 user。"""
    history = conversation.get_history(session_id)
    msgs: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # 历史(已经存的是 user/assistant,可能含 tool/tool_result)
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_message})
    return msgs


def chat(cfg: AIConfig, session_id: str, user_message: str) -> dict[str, Any]:
    """单轮对话(老接口,不改)— v7.1 兼容。"""
    messages = _build_messages(session_id, user_message)
    tool_rounds = 0
    tool_calls_log: list[dict[str, Any]] = []

    try:
        for _ in range(cfg.max_tool_rounds + 1):
            resp, _ = run_with_fallback(cfg, messages, TOOLS)
            tool_rounds += 1

            if not resp.tool_calls:
                content = resp.content or ""
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds - 1,
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                    "tool_calls": tool_calls_log,
                }

            messages.append({
                "role": "assistant",
                "content": resp.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    }
                    for tc in resp.tool_calls
                ],
            })

            for tc in resp.tool_calls:
                raw = execute_tool_safe(tc.name, tc.arguments)
                if "data" in raw:
                    result = raw["data"]
                    nav = raw.get("navigate_to")
                else:
                    result = raw
                    nav = None
                tool_calls_log.append({
                    "name": tc.name,
                    "args": tc.arguments,
                    "navigate_to": nav,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            if tool_rounds >= cfg.max_tool_rounds:
                messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
                resp2, _ = run_with_fallback(cfg, messages, TOOLS)
                content = resp2.content or "(问题过于复杂,无法在限定步数内回答)"
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds,
                    "forced_stop": True,
                    "tool_calls": tool_calls_log,
                }

        return {"content": "(达到 max_tool_rounds)", "tool_rounds": tool_rounds, "tool_calls": tool_calls_log}
    except (FatalLLMError, FallbackError) as e:
        logger.warning("LLM fallback error in chat: %s", e)
        return {"content": f"AI 服务配置错误: {e}", "tool_rounds": tool_rounds, "error": str(e)}
    except LLMError as e:
        logger.warning("LLM error in chat: %s", e)
        return {"content": f"AI 服务配置错误: {e}", "tool_rounds": tool_rounds, "error": str(e)}


def execute_tool_safe(name: str, args: dict) -> dict:
    """执行 tool,捕获所有异常(给 chat() 老接口用)。

    v7.1 时代 chat() 老接口顺序执行 tool,我们保留这个语义(不动 parallel_tools)。
    """
    from backend.ai.tool_executor import execute_tool
    try:
        return execute_tool(name, args)
    except Exception as e:
        return {"error": f"{name}: {type(e).__name__}: {e}", "navigate_to": None}


# 向后兼容别名 — 老 v7.1 测试 monkeypatch.setattr(chat_service, "execute_tool", ...)
execute_tool = execute_tool_safe


def chat_stream_with_trace(
    cfg: AIConfig,
    session_id: str,
    user_message: str,
) -> Any:
    """v8.0 流式 chat — 多模型 fallback + 并行 tool + trace + 反射重试。

    事件类型:
    - {"type": "thinking"}                          启动
    - {"type": "tool_call", "name", "args", ...}    一次 tool dispatch
    - {"type": "token", "content": "..."}           文本片段
    - {"type": "done", "finish_reason", "trace":[]} 结束(含 trace)
    - {"type": "error", "message", "trace":[]}      失败
    """
    yield {"type": "thinking"}
    messages = _build_messages(session_id, user_message)
    trace = TraceStore()
    tool_rounds = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # cfg 可为 None(老 API routes 用 load_config)— 缺省 5 轮
    max_rounds = getattr(cfg, "max_tool_rounds", 5) if cfg is not None else 5
    tool_timeout = getattr(cfg, "tool_timeout_sec", 30) if cfg is not None else 30
    max_workers = getattr(cfg, "parallel_max_workers", 5) if cfg is not None else 5

    # 当 cfg 为 None 时,fallback 仍需 base_cfg → 临时从 env 加载(老兼容)
    # 当 cfg 显式传时,完全走 cfg 不读 env(新设计)
    if cfg is None:
        from backend.ai.config import load_config
        base_cfg = load_config()
    else:
        base_cfg = cfg

    try:
        for _ in range(max_rounds + 1):
            # 1. LLM (带 fallback)
            t0 = time.perf_counter()
            try:
                resp, used_model = run_with_fallback(base_cfg, messages, TOOLS)
            except FatalLLMError as e:
                trace.append(Step(round=0, type="llm_call", error=str(e),
                                  duration_ms=int((time.perf_counter()-t0)*1000)))
                yield {"type": "error", "message": str(e), "trace": trace.get_all()}
                return
            except FallbackError as e:
                trace.append(Step(round=0, type="llm_call", error=str(e),
                                  duration_ms=int((time.perf_counter()-t0)*1000)))
                yield {"type": "error", "message": f"所有模型都不可用: {e}", "trace": trace.get_all()}
                return

            total_prompt_tokens += resp.prompt_tokens
            total_completion_tokens += resp.completion_tokens
            trace.append(Step(
                round=tool_rounds + 1,
                type="llm_call",
                model_used=used_model.model,
                duration_ms=int((time.perf_counter()-t0)*1000),
                metadata={"prompt_tokens": resp.prompt_tokens, "completion_tokens": resp.completion_tokens},
            ))

            if not resp.tool_calls:
                # 最终答案
                content = resp.content or ""
                yield {"type": "token", "content": content}
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                trace.append(Step(round=tool_rounds+1, type="done",
                                  metadata={"reason": "stop", "total_tokens": total_prompt_tokens+total_completion_tokens}))
                yield {
                    "type": "done",
                    "finish_reason": "stop",
                    "tool_rounds": tool_rounds,
                    "tool_calls": [],
                    "trace": trace.get_all(),
                }
                return

            # 2. LLM 决策加进 messages
            messages.append({
                "role": "assistant",
                "content": resp.content or "",
                "tool_calls": [
                    {
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    }
                    for tc in resp.tool_calls
                ],
            })

            # 3. 并行执行 tool
            t1 = time.perf_counter()
            results = execute_tools_parallel(resp.tool_calls, max_workers=max_workers, tool_timeout_sec=tool_timeout)
            parallel_ms = int((time.perf_counter()-t1)*1000)
            for tc, result in zip(resp.tool_calls, results):
                preview = json.dumps(result.get("data") or result, ensure_ascii=False, default=str)[:200]
                tool_event: dict[str, Any] = {
                    "type": "tool_call",
                    "name": tc.name,
                    "args": tc.arguments,
                    "navigate_to": result.get("navigate_to"),
                    "data_preview": preview if "data" in result else None,
                    "error": result.get("error"),
                }
                yield tool_event
                trace.append(Step(
                    round=tool_rounds+1, type="tool_call",
                    tool_name=tc.name, tool_args=tc.arguments,
                    tool_result_preview=preview,
                    duration_ms=parallel_ms // max(1, len(resp.tool_calls)),
                    error=result.get("error"),
                ))

            # 4. 反射重试 hint(单 tool 失败)
            for tc, result in zip(resp.tool_calls, results):
                if should_retry(result):
                    hint = build_retry_hint(tc.name, tc.arguments, result["error"])
                    messages.append({"role": "user", "content": hint})
                    trace.append(Step(round=tool_rounds+1, type="retry", tool_name=tc.name, error=result["error"]))

            # 5. tool results 进 messages
            for tc, result in zip(resp.tool_calls, results):
                messages.append({
                    "role": "tool", "tool_call_id": tc.id, "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            tool_rounds += 1
            if tool_rounds >= max_rounds:
                messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
                try:
                    resp2, used_model2 = run_with_fallback(base_cfg, messages, TOOLS)
                    content = resp2.content or "(问题过于复杂,无法在限定步数内回答)"
                except (FatalLLMError, FallbackError) as e:
                    content = f"(强制总结时 LLM 失败: {e})"
                yield {"type": "token", "content": content}
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                trace.append(Step(round=tool_rounds+1, type="done", metadata={"reason": "tool_rounds_exhausted", "forced_stop": True, "total_tokens": total_prompt_tokens+total_completion_tokens}))
                yield {
                    "type": "done", "finish_reason": "tool_rounds_exhausted",
                    "tool_rounds": tool_rounds, "forced_stop": True, "tool_calls": [],
                    "trace": trace.get_all(),
                }
                return

        yield {
            "type": "done", "finish_reason": "max_rounds",
            "tool_rounds": tool_rounds, "tool_calls": [],
            "trace": trace.get_all(),
        }
    except LLMError as e:
        logger.warning("LLM error in chat_stream: %s", e)
        yield {"type": "error", "message": str(e), "trace": trace.get_all()}
