"""
Chat service — 主循环:用户问题 → LLM + tool 循环 → 最终答案。

设计:
- 单轮 chat() 返回 dict
- 内部用 conversation.append_message 维护历史
- LLM 调 tool → execute_tool → 把结果追加到 messages → 再调 LLM
- 超过 max_tool_rounds 强制结束
"""
from __future__ import annotations

import json
import logging
from typing import Any

from backend.ai import conversation
from backend.ai.config import AIConfig
from backend.ai.llm_client import LLMError
from backend.ai.prompts import SYSTEM_PROMPT
from backend.ai.tool_executor import execute_tool
from backend.ai.tool_registry import TOOLS

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
    """单轮对话,返回 {"content": str, "tool_rounds": int, "tool_calls": [...], "error": str?}。"""
    messages = _build_messages(session_id, user_message)
    tool_rounds = 0
    tool_calls_log: list[dict[str, Any]] = []  # v7.1: 累积 tool call trace

    try:
        for _ in range(cfg.max_tool_rounds + 1):  # 多给 1 次,留最后一轮无 tool
            resp = llm_client.chat(cfg, messages=messages, tools=TOOLS)
            tool_rounds += 1

            if not resp.tool_calls:
                # LLM 给了最终答案
                content = resp.content or ""
                # 存历史
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds - 1,  # 不算最后一轮
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                    "tool_calls": tool_calls_log,
                }

            # LLM 调了 tool,把 tool_call 加进 messages,等执行
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
                raw = execute_tool(tc.name, tc.arguments)
                # v7.1: execute_tool 返 {data, navigate_to} 包装;拆出 data 给 LLM
                if "data" in raw:
                    result = raw["data"]
                    nav = raw.get("navigate_to")
                else:
                    result = raw  # 老格式或 error
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
                # 强制结束:再加一条 user 让 LLM 总结
                messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
                resp2 = llm_client.chat(cfg, messages=messages, tools=TOOLS)
                content = resp2.content or "(问题过于复杂,无法在限定步数内回答)"
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds,
                    "forced_stop": True,
                    "tool_calls": tool_calls_log,
                }

        # 不会到这里
        return {"content": "(达到 max_tool_rounds)", "tool_rounds": tool_rounds, "tool_calls": tool_calls_log}
    except LLMError as e:
        logger.warning("LLM error in chat: %s", e)
        return {"content": f"AI 服务配置错误: {e}", "tool_rounds": tool_rounds, "error": str(e)}


def chat_stream_with_trace(
    cfg: AIConfig,
    session_id: str,
    user_message: str,
) -> Any:
    """流式 chat — yield 事件供 SSE 透传。

    事件类型(v7.0):
    - {"type": "thinking"} — 启动
    - {"type": "token", "content": "..."} — 文本片段(当前实现:整段 final 一次性 yield)
    - {"type": "done", "finish_reason": "stop", "tool_rounds": N}

    事件类型(v7.1 新增):
    - {"type": "tool_call", "name": ..., "args": {...}, "navigate_to": ...}
    """
    yield {"type": "thinking"}
    messages = _build_messages(session_id, user_message)
    tool_rounds = 0
    all_tool_calls: list[dict[str, Any]] = []
    # cfg 可为 None(单测/未来 plugin 模式)— 缺省 5 轮
    max_rounds = getattr(cfg, "max_tool_rounds", 5) if cfg is not None else 5

    try:
        for _ in range(max_rounds + 1):
            resp = llm_client.chat(cfg, messages=messages, tools=TOOLS)
            tool_rounds += 1

            if not resp.tool_calls:
                # LLM 给了最终答案 — 整段 yield(后续 v7.2 改增量)
                content = resp.content or ""
                yield {"type": "token", "content": content}
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                yield {
                    "type": "done",
                    "finish_reason": "stop",
                    "tool_rounds": tool_rounds - 1,
                    "tool_calls": all_tool_calls,
                }
                return

            # LLM 调了 tool — 先 yield tool_call 事件(给前端 chip 渲染),再喂回 LLM
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
                result = execute_tool(tc.name, tc.arguments)
                # v7.1: 把 tool_call trace + navigate_to 暴露给前端
                tool_event: dict[str, Any] = {
                    "type": "tool_call",
                    "name": tc.name,
                    "args": tc.arguments,
                    "navigate_to": result.get("navigate_to"),
                }
                # 成功时附带 data 摘要(前 200 字符)
                if "data" in result and isinstance(result["data"], dict):
                    preview = json.dumps(result["data"], ensure_ascii=False, default=str)[:200]
                    tool_event["data_preview"] = preview
                elif "error" in result:
                    tool_event["error"] = result["error"]
                yield tool_event
                all_tool_calls.append(tool_event)

                # 把 tool result 追加到 messages 给 LLM 看
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            if tool_rounds >= max_rounds:
                messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
                resp2 = llm_client.chat(cfg, messages=messages, tools=TOOLS)
                content = resp2.content or "(问题过于复杂,无法在限定步数内回答)"
                yield {"type": "token", "content": content}
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                yield {
                    "type": "done",
                    "finish_reason": "tool_rounds_exhausted",
                    "tool_rounds": tool_rounds,
                    "forced_stop": True,
                    "tool_calls": all_tool_calls,
                }
                return

        yield {"type": "done", "finish_reason": "max_rounds", "tool_rounds": tool_rounds, "tool_calls": all_tool_calls}
    except LLMError as e:
        logger.warning("LLM error in chat_stream: %s", e)
        yield {"type": "error", "message": str(e)}
