"""
上下文管理 (Context) —— 互动对话里"AI 该记住什么"的确定性台账

为什么需要：互动对话游戏的长局质量，取决于宿主 AI 每回合能看到什么。原内核只有
`write_summary` / `recap` / `recall` / 世界书触发，缺三样东西：
  · **结构化事实库**：NPC 说过什么、承诺过什么、线索指向谁——可增删改查，不靠 LLM 记忆；
  · **上下文预算打包**：在字符预算内，按优先级拼出"这一回合该给 AI 看的材料"；
  · **冲突与过期**：事实有有效期与置信度，避免旧设定一直压在上下文里。

设计原则：
  · 事实是**数据**，不是指令——输出统一带 `untrusted` 与来源，与角色卡同规格；
  · 全部确定性：不随机、不读时钟、不读网络；
  · 与现有三层记忆互补：summary/milestones/archive 是"叙事历史"，这里是"结构化知识"。
"""

MAX_FACTS = 400
MAX_TEXT = 600
MAX_KEYS = 8
MAX_SUMMARY_LINES = 40

KINDS = ("fact", "clue", "promise", "npc", "place", "item", "rule", "note")
STATUSES = ("open", "done", "expired")


def _now_tick(state: dict) -> int:
    return int(state.get("tick", 0) or 0)


def _fact_id(seq: int) -> str:
    # %04d 在 seq>9999 时自然变宽（f10000），永不回绕——旧写法 % 10000 会让
    # 第 10000 条与第 1 条同 id，context_forget(id) 会误删活事实（实测碰撞）。
    return "f%d" % int(seq)


def _normalize_keys(keys):
    if isinstance(keys, str):
        keys = [keys]
    out = []
    for key in keys or []:
        text = str(key or "").strip()[:40]
        if text and text not in out:
            out.append(text)
        if len(out) >= MAX_KEYS:
            break
    return out


def _next_seq(state: dict) -> int:
    ctx = state.setdefault("context", {})
    # seq 缺失时从现有最大 id 推导（旧存档里 facts 先于 seq 字段存在）：
    # 直接从 0 起数会与既有 f0001 撞 id（实测 remember 立刻产生第二个 f0001）。
    seq = int(ctx.get("seq", 0) or 0)
    if seq <= 0:
        for fact in ctx.get("facts") or []:
            fid = str(fact.get("id") or "")
            if fid.startswith("f") and fid[1:].isdigit():
                seq = max(seq, int(fid[1:]))
    seq += 1
    ctx["seq"] = seq
    return seq


def remember(state: dict, text: str, kind: str = "fact", keys=None,
             source: str = "", confidence: float = 1.0, ttl: int = 0,
             subject: str = "") -> dict:
    """记一条结构化事实。重复文本（同 kind + 同正文）会刷新而不是重复追加。"""
    body = str(text or "").strip()
    if not body:
        raise ValueError("text 不能为空")
    body = body[:MAX_TEXT]
    kind = str(kind or "fact").strip().lower()
    if kind not in KINDS:
        raise ValueError("kind 只能是: %s" % " / ".join(KINDS))
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        raise ValueError("confidence 必须在 0..1")
    try:
        ttl = max(0, int(ttl or 0))
    except (TypeError, ValueError):
        raise ValueError("ttl 必须是非负整数")

    ctx = state.setdefault("context", {})
    facts = ctx.setdefault("facts", [])
    tick = _now_tick(state)
    for fact in facts:
        if fact.get("kind") == kind and fact.get("text") == body:
            fact["tick"] = tick
            fact["confidence"] = round(confidence, 3)
            fact["ttl"] = ttl
            fact["source"] = str(source or fact.get("source") or "")[:120]
            if keys:
                merged = fact.get("keys") or []
                for key in _normalize_keys(keys):
                    if key not in merged:
                        merged.append(key)
                fact["keys"] = merged[:MAX_KEYS]
            fact["status"] = "open"
            return {"fact": dict(fact), "created": False, "total": len(facts)}

    fact = {
        "id": _fact_id(_next_seq(state)),
        "tick": tick,
        "kind": kind,
        "subject": str(subject or "").strip()[:60],
        "text": body,
        "keys": _normalize_keys(keys),
        "source": str(source or "")[:120],
        "confidence": round(confidence, 3),
        "ttl": ttl,
        "status": "open",
    }
    facts.append(fact)
    # 线索计数：模板/成就常用 counter_gte:{key:"clues"} 判断"找到第一条线索"
    if kind == "clue":
        from game_engine.state_schema import bump
        bump(state, "clues")
    if len(facts) > MAX_FACTS:
        # 先淘汰已结案/过期，再淘汰最旧的低置信度条目；绝不动未结案的高置信度
        closed = [i for i, f in enumerate(facts) if f.get("status") != "open"]
        for i in reversed(closed):
            if len(facts) <= MAX_FACTS:
                break
            del facts[i]
        while len(facts) > MAX_FACTS:
            weakest = min(range(len(facts)), key=lambda i: (facts[i].get("confidence", 0),
                                                           facts[i].get("tick", 0)))
            del facts[weakest]
    return {"fact": dict(fact), "created": True, "total": len(facts)}


def forget(state: dict, fact_id: str = "", keys=None, kind: str = "") -> dict:
    """删除事实：按 id、按关键词或按类型。返回删除条数。"""
    ctx = state.get("context") or {}
    facts = ctx.get("facts") or []
    target_keys = set(_normalize_keys(keys))
    removed = []
    keep = []
    for fact in facts:
        hit = False
        if fact_id and fact.get("id") == str(fact_id):
            hit = True
        elif target_keys and target_keys & set(fact.get("keys") or []):
            hit = True
        elif kind and fact.get("kind") == str(kind):
            hit = True
        if hit:
            removed.append(fact.get("id"))
        else:
            keep.append(fact)
    if not (fact_id or target_keys or kind):
        raise ValueError("forget 需要 fact_id / keys / kind 至少一个条件")
    ctx["facts"] = keep
    state["context"] = ctx
    return {"removed": removed, "count": len(removed), "remaining": len(keep)}


def set_status(state: dict, fact_id: str, status: str = "done") -> dict:
    """把一条事实标为已结案/过期（承诺兑现、线索用掉）。"""
    status = str(status or "done").strip().lower()
    if status not in STATUSES:
        raise ValueError("status 只能是: %s" % " / ".join(STATUSES))
    ctx = state.get("context") or {}
    for fact in ctx.get("facts") or []:
        if fact.get("id") == str(fact_id):
            fact["status"] = status
            fact["closed_tick"] = _now_tick(state)
            state["context"] = ctx
            return {"fact": dict(fact), "status": status}
    raise ValueError("事实不存在: %s" % fact_id)


def _expire(state: dict) -> list:
    """把 ttl 到期的事实标为 expired（纯读语义：只在查询时计算，不反复写盘）。"""
    ctx = state.get("context") or {}
    tick = _now_tick(state)
    expired = []
    for fact in ctx.get("facts") or []:
        ttl = int(fact.get("ttl", 0) or 0)
        if ttl and fact.get("status") == "open" and tick - int(fact.get("tick", 0) or 0) > ttl:
            expired.append(fact)
    return expired


def search(state: dict, query: str = "", keys=None, kind: str = "", status: str = "open",
           limit: int = 12) -> list:
    """检索事实：query 匹配正文/主题，keys 精确匹配，kind 过滤，status 过滤（"" = 全部）。"""
    q = str(query or "").strip().lower()
    wanted = set(_normalize_keys(keys))
    limit = max(1, min(100, int(limit or 12)))
    expired_ids = {f.get("id") for f in _expire(state)}
    hits = []
    for fact in (state.get("context") or {}).get("facts") or []:
        fstatus = fact.get("status", "open")
        if fact.get("id") in expired_ids and fstatus == "open":
            fstatus = "expired"
        if status and fstatus != status:
            continue
        if kind and fact.get("kind") != str(kind):
            continue
        if wanted and not (wanted & set(fact.get("keys") or [])):
            continue
        if q:
            blob = " ".join([str(fact.get("subject") or ""), str(fact.get("text") or ""),
                             " ".join(fact.get("keys") or [])]).lower()
            if q not in blob:
                continue
        row = dict(fact)
        row["status"] = fstatus
        if fstatus == "expired":
            row["expired"] = True
        hits.append(row)
    hits.sort(key=lambda f: (f.get("confidence", 0), f.get("tick", 0)), reverse=True)
    return hits[:limit]


def _context_budget(state: dict) -> int:
    cfg = state.get("config") or {}
    try:
        return max(200, int(cfg.get("context_budget_chars", 4000) or 4000))
    except (TypeError, ValueError):
        return 4000


def pack(state: dict, scene_text: str = "", recent: int = 8, budget_chars: int = 0) -> dict:
    """按字符预算打包这一回合给宿主的上下文材料。

    顺序（也是裁剪优先级，从高到低）：
      1. 任务/玩法（playbook + 事业线）
      2. 未结案的承诺与线索（按置信度）
      3. 与场景/最近事件相关的事实
      4. 最近事件与摘要
      5. 其余开放事实（低置信度先砍）
    """
    budget = max(200, int(budget_chars or _context_budget(state)))
    out = {"budget_chars": budget, "sections": [], "used_chars": 0, "truncated": []}

    def push(title, lines, priority):
        out["sections"].append({"title": title, "lines": lines, "priority": priority})

    playbook = state.get("playbook") or {}
    pb_lines = []
    if playbook:
        progress = playbook.get("progress") or {}
        pb_lines.append("玩法：%s · 进度 %s %s/%s" % (
            playbook.get("loop", "freeform"), progress.get("label", "进度"),
            progress.get("value", 0), progress.get("max", 0)))
    quests = state.get("questlines") or []
    if quests:
        active = [q for q in quests if (q.get("status") or "") != "done"]
        pb_lines.append("事业线：%d 条（%s）" % (len(active), "、".join(
            str(q.get("title") or q.get("id")) for q in active[:4]) or "无"))
    if pb_lines:
        push("本局玩法", pb_lines, 1)

    open_facts = search(state, status="open", limit=MAX_FACTS)
    promises = [f for f in open_facts if f.get("kind") in ("promise", "clue")]
    if promises:
        push("未结案", ["[%s] %s" % (f.get("kind"), f.get("text")) for f in promises[:8]], 2)

    scene_hits = []
    if scene_text:
        scene_hits = search(state, query=scene_text, status="open", limit=6)
    if scene_hits:
        push("与场景相关", ["%s" % f.get("text") for f in scene_hits], 3)

    recent_events = [e for e in (state.get("event_log") or [])[-max(1, int(recent)):] if e.get("desc")]
    if recent_events:
        push("最近事件", ["第%s回合·%s" % (e.get("tick", 0), e.get("desc")) for e in recent_events], 4)

    rest = [f for f in open_facts if f not in promises and f not in scene_hits]
    if rest:
        push("其他事实", [f.get("text") for f in rest[:10]], 5)

    kept, used = [], 0
    for section in sorted(out["sections"], key=lambda s: s["priority"]):
        lines = []
        for line in section["lines"]:
            text = str(line)
            if used + len(text) > budget:
                out["truncated"].append({"section": section["title"], "line": text[:60]})
                continue
            lines.append(text)
            used += len(text)
        if lines:
            kept.append({"title": section["title"], "lines": lines, "priority": section["priority"]})
    out["sections"] = kept
    out["used_chars"] = used
    return out


def summary(state: dict) -> dict:
    """面板用的上下文概览：事实统计与最近几条。"""
    ctx = state.get("context") or {}
    facts = ctx.get("facts") or []
    stats = {kind: 0 for kind in KINDS}
    for fact in facts:
        kind = fact.get("kind", "fact")
        if kind in stats:
            stats[kind] += 1
    open_rows = search(state, status="open", limit=10)
    return {
        "total": len(facts),
        "by_kind": stats,
        "open": sum(1 for f in facts if f.get("status") == "open"),
        "recent": [{"id": f.get("id"), "kind": f.get("kind"), "text": f.get("text", "")[:120],
                    "keys": f.get("keys") or [], "tick": f.get("tick", 0)}
                   for f in open_rows],
        "budget_chars": _context_budget(state),
    }
