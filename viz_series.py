"""
长局态势采样 (viz_series)

把"每一回合的态势"记进一份**侧写文件** `<状态文件>.viz.jsonl`，供面板画长局曲线：
气血/内力/钱财、未清业债、人情均值、物价指数、图鉴规模、所在地。

与状态文件的关系（重要）：
- 本模块**从不写状态文件**，只读写侧写文件；面板仍严格只读（ARCHITECTURE INV-V1）。
- 引擎在每次结算落盘后记一条（mcp_server._finish），面板打开时也会兜底补记（panel.view_model）——
  两边都以 tick 去重：同 tick 覆盖、旧 tick 丢弃，所以重复调用是幂等的，
  且玩家不开面板的回合历史也不会断档（长局可视化的前提）。
"""

import json
import os

SERIES_CAP = 600


def series_path(state_path):
    return state_path + ".viz.jsonl"


def sample_of(state):
    """从状态抽一条态势样本（纯读取；字段固定，前端图表只消费这些 key）。"""
    ents = state.get("entities") or {}
    p = ents.get("player") or {}
    market = state.get("market") or {}
    ratios = []
    for mk in market.values():
        if not isinstance(mk, dict):
            continue
        for it in mk.values():
            if not isinstance(it, dict):
                continue
            base = it.get("base_price") or it.get("price") or 0
            if base:
                ratios.append(float(it.get("price", 0)) / float(base))
    rels = state.get("relations") or {}
    affs = [float(v.get("affinity", 0)) for k, v in rels.items()
            if isinstance(v, dict) and "player" in str(k)]
    codex = state.get("codex") or {}
    codex_total = sum(len(codex.get(k) or []) for k in ("locations", "people", "items", "lore"))
    karma = sum(float(e.get("amount", 0)) for e in (state.get("karma_ledger") or [])
                if e.get("from") == "player" and not e.get("settled"))
    return {
        "tick": int(state.get("tick", 0) or 0),
        "hp": int(p.get("hp", 0) or 0),
        "hp_max": int(p.get("hp_max", 1) or 1),
        "mp": int(p.get("mp", 0) or 0),
        "mp_max": int(p.get("mp_max", 0) or 0),
        "gold": int(p.get("gold", 0) or 0),
        "karma": int(karma),
        "price_index": round(sum(ratios) / len(ratios), 4) if ratios else 1.0,
        "affinity_avg": round(sum(affs) / len(affs), 2) if affs else 0.0,
        "codex_total": int(codex_total),
        "location": str(p.get("location", "") or ""),
        # 世界侧脉搏：长局里"世界自己会动"的可视证据（相位/存量/连接度/烈度）。
        # 旧存档没有 panarchy 时给中性值，图表自动降级。
        "phase": str(((state.get("panarchy") or {}).get("phase") or "")),
        "capital": round(float(((state.get("panarchy") or {}).get("capital") or 0.0)), 4),
        "connectedness": round(float(((state.get("panarchy") or {}).get("connectedness") or 0.0)), 4),
        "intensity": round(float((state.get("panarchy") or {}).get("intensity") or 1.0), 3),
    }


def record_sample(state_path, state):
    """追加（或同 tick 覆盖）一条态势样本；回退/恢复到旧 tick 时丢弃，保持 tick 升序唯一。"""
    if not state_path:
        return
    try:
        s = sample_of(state)
    except Exception:  # aqg: top-level boundary —— 侧写是观测数据，异常绝不影响对局结算
        return
    path = series_path(state_path)
    lines = []
    last = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            if lines:
                last = json.loads(lines[-1])
        except Exception:  # aqg: top-level boundary —— 侧写文件损坏时不抛，退回空历史
            lines = []
    if isinstance(last, dict) and int(last.get("tick", -1)) == s["tick"]:
        if last == s:
            return          # 值未变：不重复写盘（轮询下的常规路径）
        lines[-1] = json.dumps(s, ensure_ascii=False)
    elif isinstance(last, dict) and int(last.get("tick", -1)) > s["tick"]:
        return              # 快照回退：不把旧 tick 追回来
    else:
        lines.append(json.dumps(s, ensure_ascii=False))
    if len(lines) > SERIES_CAP:
        lines = lines[-SERIES_CAP:]
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError:
        return


def load_series(state_path):
    """读回样本（tick 升序、封顶 SERIES_CAP）；坏行跳过，永不抛。"""
    path = series_path(state_path)
    out = []
    if state_path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        s = json.loads(line)
                    except Exception:  # nosec B112; aqg: top-level boundary —— 单行坏样本跳过，不打断整段历史
                        continue
                    if isinstance(s, dict) and "tick" in s:
                        out.append(s)
        except OSError:
            pass
    out.sort(key=lambda x: int(x.get("tick", 0)))
    return out[-SERIES_CAP:]
