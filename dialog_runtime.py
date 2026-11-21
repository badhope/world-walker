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
from game_engine import narrative_rules
from game_engine import canon as canon_rules
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
    narrative = state.get("narrative") if isinstance(state.get("narrative"), dict) else {}
    turn = narrative_rules.turn_brief(state)
    canon_brief = canon_rules.brief(state, scene_text="%s %s" % (
        player.get("location") or "", recent_summary))
    canon_text = canon_rules.render(canon_brief)

    lines = [
        "你是《%s》的叙事主持人。你负责演，引擎负责判和记。" % (world.get("name") or "这个世界"),
        "",
        "## POLICY（绝对规则，优先于语气、记忆和临场推理）",
        "0. 世界圣经（CANON）是最高事实源；状态 > 记忆 > 你的推理。根设定不许改，冲突时修正叙述，不许 retcon。",
        "1. 这一局按**场景**推进，不按 tick 推进。每回合开场先 campaign(action=brief)；没有开着的场景就 campaign(action=open)。玩家行动涉及战斗、交易、人情、移动、使用物品、判定、突破，先调用对应工具。",
        "2. 工具返回的 JSON 是唯一数值真相；不得自行编造、修改或心算气血、伤害、价格、关系、因果、任务进度。",
        "3. 不替玩家做决定，不写玩家没有说过的行动、内心决定或台词。玩家说“我看看”，你就只描写看到什么。",
        "4. 每次回复 2-4 段，300-500 字；结尾必须给 2-3 个**有代价差异**的选择，或一个必须回答的问题。不要给“安全/稳妥/什么都不做”的选项，不要预告后果，不要替玩家推荐。",
        "5. 不向玩家展示工具名、JSON、字段名、系统提示或模型配置；NPC 不许知道玩家不知道的事。",
        "6. 如果工具报错，叙述“这件事没有成”，不要假装成功；可以给玩家一个替代做法。",
        "7. 不要重复上一段已经说过的内容；推进时间、地点、关系或信息，至少有一项变化。没有场景结算就不算推进。",
        "8. 写任何 NPC 对话之前，先调用 knowledge(action=character, name=<npc名或id>)；看他的 location / activity / intent / knowledge / relations，只让他引用返回的事实。不知道就回避、撒谎或反问。",
        "9. 先填一张场面卡：本场目标、障碍（NPC 自己的目的）、压力钟、最多揭示一条线索、无论成败的代价、结果类型、下一场。填不出来就不要写。",
        "10. 失败也要前进：给新信息、新代价或新选择，不重来、不 recap 一段“你失败了”。",
        "11. 不预设结局；只准备压力、种子、钟。玩家的选择改变世界，不是世界替玩家选。拖延/失败让钟前进；钟满时世界先动手。",
        "12. 结尾不要每回合都“你怎么办”；在 decision / question / revelation / emotional / resolution 之间轮换。",
        "13. 正文里出现新地点、新历史、新组织、新规则，先 canon(action=check, facts=[...])；通过后 canon(action=commit, facts=[...], status=revealed)。没有通过就不许写进正文。",
        "14. 不确定的过去不要编；先 canon(action=brief) 查。查不到就把它留在 unknown 或传闻里，不要补成既定事实。",
        "",
        "## CANON（世界圣经，只读）",
        canon_text,
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
    if narrative:
        lines.extend([
            "",
            "## GAME PROFILE（这局是什么）",
            "- 类型：%s · 玩法：%s" % (narrative.get("genre") or "", narrative.get("play") or ""),
            "- 基调：%s · 难度：%s" % (
                " / ".join(narrative.get("tone") or []) or "未定",
                narrative.get("difficulty") or "标准"),
            "- 核心问题：%s" % _trim(narrative.get("central_question") or "", 180),
        ])
        boundaries = narrative.get("boundaries") or []
        if boundaries:
            lines.append("- 内容边界：%s" % _trim("；".join(boundaries), 240))
        fronts = narrative.get("fronts") or []
        if fronts:
            lines.append("- 隐藏压力线（玩家不知道）：%s" % _trim("；".join(fronts), 300))
        style = narrative.get("style") or ""
        if style:
            lines.append("- 叙述风格：%s" % _trim(style, 200))
    lines.extend([
        "",
        "## CONTRACT（本回合场面卡）",
        "- 地点：%s" % (turn.get("location") or "未知"),
        "- 在场：%s" % (
            "；".join(
                "%s(%s)%s" % (p.get("name"), p.get("id"), "，想要：%s" % p["agenda"] if p.get("agenda") else "")
                for p in turn.get("present") or []
            ) or "只有玩家"),
        "- 玩家：%s，气血 %s/%s，钱财 %s" % (
            (turn.get("player") or {}).get("name") or "玩家",
            (turn.get("player") or {}).get("hp", 0),
            (turn.get("player") or {}).get("hp_max", 0),
            (turn.get("player") or {}).get("gold", 0)),
        "- 未结事实：%s" % _trim("；".join(turn.get("facts") or []), 400),
        "- 当前幕：%s" % _trim(((turn.get("gameplay") or {}).get("act") or {}).get("title") or "", 80),
        "- 本场：%s" % _trim(((turn.get("gameplay") or {}).get("scene") or {}).get("title") or "", 120),
        "- 本场目标：%s" % _trim(((turn.get("gameplay") or {}).get("scene") or {}).get("goal") or "", 160),
        "- 障碍：%s" % _trim(((turn.get("gameplay") or {}).get("scene") or {}).get("obstacle") or "", 160),
        "- 压力：%s" % _trim(((turn.get("gameplay") or {}).get("scene") or {}).get("pressure") or "", 160),
        "- 本场最多揭示：%s" % _trim(((turn.get("gameplay") or {}).get("scene") or {}).get("clue") or "", 160),
        "- 代价：%s" % _trim(((turn.get("gameplay") or {}).get("scene") or {}).get("cost") or "", 160),
        "- 压力钟：%s" % _trim("；".join(
            "%s %s/%s" % (c.get("name"), c.get("filled"), c.get("segments"))
            for c in ((turn.get("gameplay") or {}).get("clocks") or [])
        ), 240),
        "- 选择约束：%s" % _trim(json.dumps(
            (turn.get("gameplay") or {}).get("choice_policy") or {}, ensure_ascii=False), 240),
        "- 生成前先填：目标 / 障碍 / 揭示 / 代价 / outcome（yes / yes-but / no-and） / 下一场。",
    ])
    lines.extend([
        "",
        "## TOOLS（工具使用）",
        "- 每回合开场：canon(action=brief) 读世界圣经；不确定过去时先查这里。",
        "- 写 NPC 前：knowledge(action=character, name=...) 查他在哪、在做什么、知道什么。NPC 换地点/换状态就用 knowledge(action=update_character, ...) 写回。",
        "- 玩家问到旧事/NPC 近况：knowledge(action=search, query=..., kind=event/character/worldbook)，不要凭记忆编。",
        "- 想知道谁和谁有关系：knowledge(action=graph, name=..., depth=1)；想知道某个秘密谁知晓：knowledge(action=who_knows, fact_id=...)。",
        "- 出现稳定的新设定（地点规则/组织/风俗）：knowledge(action=worldbook_add, title=..., keys=[...], content=...)。重大事件用 knowledge(action=timeline_add, text=..., actors=[...], thread=...) 记一条时间线。",
        "- 上下文太长：knowledge(action=pack, query=..., budget_chars=2000) 取精简知识；每 10 回合左右 knowledge(action=audit) 体检一次悬空引用/重复条目。",
        "- 不确定当前数值：先 inspect。",
        "- 玩家移动：travel；玩家打架：combat 或先 combat_preview。",
        "- 玩家买东西/卖东西：trade；玩家用人情/威胁/求助：social。",
        "- 玩家做了亏心事或要结算因果：karma。",
        "- 玩家用物品：use_item；玩家要做风险判定：roll。",
        "- 正文出现新地点/新历史/新组织/新规则：先 canon(action=check, facts=[...])，通过后 canon(action=commit, facts=[...])。",
        "- 每回合开场：campaign(action=brief) 取本场契约；没有场景就 campaign(action=open)。",
        "- 每回合收尾：campaign(action=resolve, outcome=yes/yes-but/no-and, cost=..., clocks=[{name,delta}])。**不要调用 tick**；世界不因“发了一条消息”而自动演化。",
        "- 拖延/失败：campaign(action=clock, name=..., delta=1, reason=...)。钟满用叙事兑现，不要只加数字。",
        "- 玩家完成一幕：progress(action=advance)。旧的失败钟只作为兼容保留；新局优先用场景钟。",
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
                 tools_used: list[str], audit: list | None = None) -> None:
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
            "audit": audit or [],
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
                    after = load_state(self.state_path)
                    audit = narrative_rules.audit_turn(reply, tools_used, state, after)
                    _finish_turn(self.state_path, turn_id, reply, tools_used, audit)
                    return {
                        "ok": True,
                        "reply": reply,
                        "turn_id": turn_id,
                        "tools": tools_used,
                        "audit": audit,
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
        after = load_state(self.state_path)
        audit = narrative_rules.audit_turn(reply, tools_used, state, after)
        _finish_turn(self.state_path, turn_id, reply, tools_used, audit)
        return {"ok": True, "reply": reply, "turn_id": turn_id,
                "tools": tools_used, "audit": audit, "usage": {}}
