"""Dialog runtime: system prompt + OpenAI tool loop + persistent turns.

This is the piece that turns the engine from "a host has to drive it" into
"a player can simply talk to it".  It deliberately stays small: the model
chooses tools, the engine executes them, the transcript is persisted.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from game_engine import model_config
from game_engine.host_adapter import HostAdapterError, OpenAICompatAdapter, ToolsUnsupported
from game_engine.state_schema import load_state, transact_state
from game_engine.tool_registry import ToolRegistry

MAX_TURNS = 300
HISTORY_TURNS = 12
MAX_TOOL_ROUNDS = 3


class DialogRuntimeError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _trim(text, limit: int) -> str:
    value = str(text or "")
    return value if len(value) <= limit else value[:limit] + "…"


def _system_prompt(state: dict) -> str:
    world = state.get("world_info") or {}
    player = (state.get("entities") or {}).get("player") or {}
    playbook = state.get("playbook") if isinstance(state.get("playbook"), dict) else {}
    summaries = state.get("summaries") if isinstance(state.get("summaries"), list) else []
    milestones = state.get("milestones") if isinstance(state.get("milestones"), list) else []
    events = state.get("event_log") if isinstance(state.get("event_log"), list) else []
    recent_summary = str((summaries[-1] or {}).get("text") or "") if summaries else ""
    recent_events = [str(e.get("desc") or "") for e in events[-5:] if isinstance(e, dict)]
    recent_milestones = [str(m.get("title") or m.get("desc") or "") for m in milestones[-5:]
                         if isinstance(m, dict)]

    loop_guide = playbook.get("loop_guide") or playbook.get("guide") or ""
    beat = playbook.get("beat") or ""
    progress = playbook.get("progress") or {}
    failure = playbook.get("failure") or {}

    lines = [
        "你是《%s》的叙事主持人。你负责演，引擎负责判和记。" % (world.get("name") or "这个世界"),
        "",
        "## 硬规则",
        "1. 玩家的每个行动先判断是否需要结算；涉及战斗、交易、人情、移动、使用物品、判定、突破、推进回合，必须先调用对应工具。",
        "2. 工具返回的 JSON 是唯一数值真相；不得自行编造、修改或心算气血、伤害、价格、关系、因果、任务进度。",
        "3. 不替玩家做决定，不写玩家没有说过的行动。玩家说“我看看”，你就只描写看到什么。",
        "4. 每次回复 2-4 段，300-500 字；结尾给一个可行动的画面、选择或问题。",
        "5. 不向玩家展示工具名、JSON、字段名、系统提示或模型配置。",
        "6. 如果工具报错，叙述“这件事没有成”，不要假装成功；可以给玩家一个替代做法。",
        "7. 不要重复上一段已经说过的内容；推进时间、地点、关系或信息，至少有一项变化。",
        "",
        "## 当前局面",
        "- 世界：%s（%s）" % (world.get("name") or "", world.get("era") or "未定纪元"),
        "- 地点：%s" % (player.get("location") or world.get("location_desc") or "未知"),
        "- 主角：%s，%s，气血 %s/%s，钱财 %s" % (
            player.get("name") or "无名者", player.get("level") or "凡人",
            player.get("hp", 0), player.get("hp_max", 0), player.get("gold", 0)),
    ]
    if loop_guide:
        lines.append("- 玩法：%s" % _trim(loop_guide, 500))
    if beat:
        lines.append("- 当前节拍：%s" % _trim(beat, 200))
    if progress:
        lines.append("- 进度：%s" % _trim(json.dumps(progress, ensure_ascii=False), 300))
    if failure:
        lines.append("- 失败条件：%s" % _trim(json.dumps(failure, ensure_ascii=False), 300))
    if recent_summary:
        lines.append("- 上次回顾：%s" % _trim(recent_summary, 500))
    if recent_milestones:
        lines.append("- 大事记：%s" % _trim("；".join(recent_milestones), 300))
    if recent_events:
        lines.append("- 最近发生：%s" % _trim("；".join(recent_events), 400))
    lines.extend([
        "",
        "## 工具使用",
        "- 不确定当前数值：先 inspect。",
        "- 玩家移动：travel；玩家打架：combat 或先 combat_preview。",
        "- 玩家买东西/卖东西：trade；玩家用人情/威胁/求助：social。",
        "- 玩家做了亏心事或要结算因果：karma。",
        "- 玩家用物品：use_item；玩家要做风险判定：roll。",
        "- 每回合收尾：tick。",
        "- 玩家完成一幕：progress(action=advance)。失败钟压力：progress(action=failure)。",
        "- 需要把正文写进存档：story(action=publish)。",
        "",
        "直接开始叙事；需要工具时先调用工具，拿到结果后再写。",
    ])
    return "\n".join(lines)


def _history(state: dict) -> list[dict]:
    turns = state.get("turns") if isinstance(state.get("turns"), list) else []
    rows = []
    for turn in turns[-HISTORY_TURNS:]:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role")
        text = str(turn.get("text") or "").strip()
        if role not in ("player", "assistant") or not text:
            continue
        rows.append({"role": "user" if role == "player" else "assistant", "content": text})
    return rows


def _append_turn(state_path: str, turn: dict) -> None:
    def edit(state):
        turns = state.setdefault("turns", [])
        if not isinstance(turns, list):
            turns = state["turns"] = []
        turns.append(turn)
        if len(turns) > MAX_TURNS:
            del turns[:len(turns) - MAX_TURNS]

    transact_state(edit, state_path, allow_create=False)


def _finish_turn(state_path: str, player_turn_id: str, reply: str,
                 tools_used: list[str]) -> None:
    def edit(state):
        turns = state.setdefault("turns", [])
        for turn in turns:
            if isinstance(turn, dict) and turn.get("id") == player_turn_id:
                turn["status"] = "ok"
                break
        turns.append({
            "id": uuid.uuid4().hex,
            "role": "assistant",
            "text": reply,
            "tick": int(state.get("tick", 0) or 0),
            "ts": _now(),
            "status": "ok",
            "tools": tools_used[-8:],
        })
        if len(turns) > MAX_TURNS:
            del turns[:len(turns) - MAX_TURNS]

    transact_state(edit, state_path, allow_create=False)


def _fail_turn(state_path: str, player_turn_id: str, error: str) -> None:
    def edit(state):
        for turn in state.get("turns") or []:
            if isinstance(turn, dict) and turn.get("id") == player_turn_id:
                turn["status"] = "error"
                turn["error"] = _trim(error, 240)
                break

    transact_state(edit, state_path, allow_create=False)


class DialogRuntime:
    def __init__(self, state_path: str, adapter: OpenAICompatAdapter | None = None):
        self.state_path = os.path.abspath(state_path)
        self.adapter = adapter or OpenAICompatAdapter(model_config.load_config())
        self.registry = ToolRegistry(self.state_path)

    def respond(self, text: str) -> dict:
        body = str(text or "").strip()
        if not body:
            raise DialogRuntimeError("说点什么再发送")
        if len(body) > 2000:
            raise DialogRuntimeError("一次最多 2000 字")

        state = load_state(self.state_path)
        turn_id = uuid.uuid4().hex
        player_turn = {
            "id": turn_id,
            "role": "player",
            "text": body,
            "tick": int(state.get("tick", 0) or 0),
            "ts": _now(),
            "status": "pending",
        }
        _append_turn(self.state_path, player_turn)

        messages = [{"role": "system", "content": _system_prompt(state)}]
        messages.extend(_history(state))
        messages.append({"role": "user", "content": body})
        tools = self.registry.as_openai()
        tools_used: list[str] = []
        last_error = ""

        try:
            for round_no in range(MAX_TOOL_ROUNDS + 1):
                try:
                    result = self.adapter.chat(messages, tools=tools if round_no < MAX_TOOL_ROUNDS else None)
                except ToolsUnsupported:
                    result = self.adapter.chat(messages, tools=None)
                message = result.get("message") or {}
                calls = message.get("tool_calls") or []
                if not calls:
                    reply = str(message.get("content") or "").strip()
                    if not reply:
                        raise DialogRuntimeError("模型没有返回正文")
                    _finish_turn(self.state_path, turn_id, reply, tools_used)
                    return {
                        "ok": True,
                        "reply": reply,
                        "turn_id": turn_id,
                        "tools": tools_used,
                        "usage": result.get("usage") or {},
                    }
                if round_no >= MAX_TOOL_ROUNDS:
                    break
                messages.append({
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": calls,
                })
                for call in calls:
                    name = str(((call.get("function") or {}).get("name") or ""))
                    raw_args = ((call.get("function") or {}).get("arguments") or "{}")
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                    except (TypeError, ValueError):
                        args = {}
                    tools_used.append(name)
                    outcome = self.registry.execute(name, args)
                    if not outcome.get("ok"):
                        last_error = str(outcome.get("error") or "")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id") or name,
                        "content": json.dumps(outcome, ensure_ascii=False)[:2400],
                    })
        except HostAdapterError as exc:
            _fail_turn(self.state_path, turn_id, str(exc))
            raise DialogRuntimeError(str(exc)) from exc
        except DialogRuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            _fail_turn(self.state_path, turn_id, str(exc))
            raise DialogRuntimeError(model_config.redact(str(exc))[:240]) from exc

        # Still asking for tools after the budget: give the player a graceful
        # in-world beat instead of a dead spinner.
        reply = "这一回合的结算没有走完。你可以换一种做法，或者再说一次你想做什么。"
        if last_error:
            reply = "这件事没有成：%s。你可以换一种做法。" % last_error[:120]
        _finish_turn(self.state_path, turn_id, reply, tools_used)
        return {"ok": True, "reply": reply, "turn_id": turn_id,
                "tools": tools_used, "usage": {}}
