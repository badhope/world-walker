#!/usr/bin/env python3
"""
万界·行者 · 实况面板 (World Walker Live Panel)

一个**只读**的小型 HTTP 服务：把状态文件渲染成可以长期挂着的游戏面板
（玩家血量/心流/图鉴/编年史/市场行情实时更新）。

单独用:
    python panel.py --state ww_state.json --port 8765
由 MCP 拉起: 调工具 open_panel（会自动指向当前对局的状态文件）

端点:
    GET /        面板页面（panel.html）
    GET /state   视图模型 JSON（状态 + 引擎推导的心流/相位/身份 + 图鉴）
    GET /events  SSE：状态文件一变就推送
"""

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if "game_engine" not in sys.modules:
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        "game_engine", os.path.join(_SCRIPT_DIR, "__init__.py"),
        submodule_search_locations=[_SCRIPT_DIR])
    _pkg = importlib.util.module_from_spec(_spec)
    _pkg.__path__ = [_SCRIPT_DIR]
    sys.modules["game_engine"] = _pkg

from game_engine.rules.narrative_engine import (  # noqa: E402
    flow_channel_status, panarchy_phase_check, player_identity_vector)
from game_engine.state_schema import load_state  # noqa: E402

HTML_FILE = os.path.join(_SCRIPT_DIR, "panel.html")
HTML_DIR = _SCRIPT_DIR
MORAL_DIMS = ("关怀", "公平", "忠诚", "权威", "圣洁", "自由")
EVENTS_CAP = 40

# 唯一的事件分级表（前端不得再维护关键词表；未知类型走 EVENT_LABELS 兜底）
EVENT_LABELS = {
    "combat": ("交锋", "战"),
    "trade": ("交易", "交"),
    "social": ("人情", "情"),
    "karma": ("因果", "债"),
    "breakthrough": ("突破", "境"),
    "travel": ("行旅", "路"),
    "use_item": ("用物", "药"),
    "emergent": ("风起", "风"),
    "system": ("世界", "启"),
    "tick": ("回合", "回"),
}


def classify_event(ev, milestone_ticks=()):
    """把一条 event_log 映射成前端可直接渲染的条目（kind/severity/title/icon 全在此决定）。"""
    etype = str(ev.get("type") or "system")
    desc = str(ev.get("desc") or "")
    tick = int(ev.get("tick", 0) or 0)
    title, icon = EVENT_LABELS.get(etype, ("事件", "·"))
    kind, severity = "事件", "info"
    if etype == "combat":
        if any(w in desc for w in ("击败", "击杀", "倒下")):
            kind, severity = "击杀", "danger"
        else:
            kind, severity = "交手", "warning"
    elif etype == "trade":
        kind = "购入" if "购买" in desc else ("出售" if "出售" in desc else "交易")
        severity = "success"
    elif etype == "social":
        kind = "人情"
        severity = "success" if any(w in desc for w in ("好感", "敬重", "结盟", "帮助")) else "info"
    elif etype == "karma":
        kind, severity = "因果", "warning"
    elif etype == "breakthrough":
        if any(w in desc for w in ("失败", "反噬")):
            kind, severity = "突破受挫", "danger"
        else:
            kind, severity = "突破", "success"
    elif etype == "travel":
        kind = "初探" if "初次" in desc else "行旅"
    elif etype == "use_item":
        kind, severity = "用物", "success"
    elif etype == "emergent":
        kind, severity = "涌现", "warning"
    elif etype == "system":
        kind = "入局"
    digest = hashlib.sha1(desc.encode("utf-8")).hexdigest()[:8]
    return {"id": "%d:%s:%s" % (tick, etype, digest), "tick": tick, "type": etype,
            "kind": kind, "severity": severity, "title": title, "desc": desc,
            "icon": icon, "milestone": tick in set(milestone_ticks or ())}


def build_scene(state, events, player):
    """叙事主舞台标题/描述/氛围：只用状态里已有的文字，不编造剧情。"""
    world = state.get("world_info", {}) or {}
    loc = str(player.get("location", "") or "")
    summaries = state.get("summaries") or []
    desc = str(summaries[-1].get("text", "") if summaries else "") or str(world.get("location_desc", "") or "")
    focus = None
    for e in reversed(events):
        if e["severity"] != "info":
            focus = e["desc"]
            break
    if not focus and events:
        focus = events[-1]["desc"]
    if not desc and focus:
        desc = focus
    mood = "neutral"
    if events:
        last = events[-1]
        if last["type"] == "trade":
            mood = "trade"
        elif last["type"] == "social":
            mood = "social"
        elif last["type"] == "travel":
            mood = "discovery"
        elif last["severity"] == "danger":
            mood = "danger"
        elif last["severity"] == "success":
            mood = "growth"
    return {"location": loc, "title": loc or str(world.get("name", "") or ""),
            "description": desc, "mood": mood, "focus_event": focus}


def build_inventory(state, player):
    """随身物品：以 player.items 为准，用市场元数据补显示名与类别。"""
    items = player.get("items")
    if not isinstance(items, dict):
        return []
    meta = {}
    for mk in (state.get("market") or {}).values():
        if isinstance(mk, dict):
            for k, it in mk.items():
                if isinstance(it, dict) and k not in meta:
                    meta[k] = it
    out = []
    for k in sorted(items):
        try:
            n = int(items[k])
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        it = meta.get(k) or {}
        out.append({"key": str(k), "name": str(it.get("name") or k),
                    "quantity": n, "type": str(it.get("type") or "")})
    return out


def build_relations(state, player_id="player"):
    """只返回与玩家有关的关系（键为字母序 a:b），带对方名字。"""
    rels = state.get("relations") or {}
    ents = state.get("entities") or {}
    out = []
    if not isinstance(rels, dict):
        return out
    for key, val in rels.items():
        if not isinstance(val, dict):
            continue
        parts = str(key).split(":")
        if len(parts) != 2 or player_id not in parts:
            continue
        other = parts[0] if parts[1] == player_id else parts[1]
        ent = ents.get(other) or {}
        out.append({"id": other, "name": str(ent.get("name") or other),
                    "affinity": int(val.get("affinity", 0) or 0),
                    "respect": int(val.get("respect", 0) or 0)})
    out.sort(key=lambda r: r["id"])
    return out


def view_model(state_path):
    """把状态文件转成面板要用的视图模型（只读，不改状态）。"""
    s = load_state(state_path)
    record_sample(state_path, s)   # 侧写：态势采样（写的是 <state>.viz.jsonl，不碰状态文件）
    player = s.get("entities", {}).get("player", {})
    loc = player.get("location", "")
    try:
        insights = {
            "flow": flow_channel_status(s),
            "phase": panarchy_phase_check(s),
            "identity": player_identity_vector(s),
        }
    except Exception as e:
        insights = {"error": str(e)[:120]}

    milestone_ticks = {int(m.get("tick", 0) or 0) for m in (s.get("milestones") or [])}
    events = [classify_event(e, milestone_ticks)
              for e in (s.get("event_log") or [])[-EVENTS_CAP:]]
    karma = sum(e.get("amount", 0) for e in s.get("karma_ledger", [])
                if e.get("from") == "player" and not e.get("settled"))

    market = []
    for mLoc, items in sorted(s.get("market", {}).items()):
        rows = []
        for key, it in sorted(items.items()):
            base = it.get("base_price") or it.get("price") or 0
            price = it.get("price", 0)
            rows.append({
                "key": key, "name": it.get("name", key), "price": price,
                "base_price": base, "supply": it.get("supply", 0),
                "delta": price - base, "type": it.get("type", ""),
            })
        market.append({"location": mLoc, "items": rows})

    codex = s.get("codex", {})
    return {
        "updated_at": time.strftime("%H:%M:%S"),
        "world": s.get("world_info", {}) or {},
        "tick": s.get("tick", 0),
        "seed": s.get("rng_seed"),
        "skin": skin_for_world(s),
        "meta": {
            "state_path": os.path.abspath(state_path),
            "sidecar": os.path.abspath(series_path(state_path)),
            "read_only": True,
            "panel": "万界·行者 实况主舞台（只读）",
        },
        "scene": build_scene(s, events, player),
        "events": events,
        "relations": build_relations(s),
        "player": {
            "name": player.get("name", "玩家"), "level": player.get("level", ""),
            "stage": int(player.get("stage", 0) or 0),
            "stage_max": int((s.get("config") or {}).get("stage_max", 20) or 20),
            "mind_scars": int(player.get("mind_scars", 0) or 0),
            "near_death_count": int(player.get("near_death_count", 0) or 0),
            "hp": player.get("hp", 0), "hp_max": player.get("hp_max", 1),
            "mp": player.get("mp", 0), "mp_max": player.get("mp_max", 0),
            "gold": player.get("gold", 0), "location": loc,
            "currency": str(s.get("currency", "灵石")),
            "karma": karma,
            "attrs": player.get("attrs", {}),
            "inventory": build_inventory(s, player),
        },
        "insights": insights,
        "moral": {
            "dims": MORAL_DIMS,
            "values": (player.get("morality") or [0, 0, 0, 0, 0, 0])[:6],
        },
        "karma": karma,
        "present": [{"id": k, "name": e.get("name", k), "level": e.get("level", ""),
                     "hp": e.get("hp"), "hp_max": e.get("hp_max"),
                     "desc": (e.get("desc") or "")[:90]}
                    for k, e in s.get("entities", {}).items()
                    if k != "player" and (not loc or e.get("location") == loc)],
        "others": [{"id": k, "name": e.get("name", k), "location": e.get("location", "")}
                   for k, e in s.get("entities", {}).items() if k != "player" and e.get("location") != loc],
        "codex": {
            "locations": codex.get("locations", []),
            "people": codex.get("people", []),
            "items": codex.get("items", []),
            "lore": codex.get("lore", []),
        },
        "lore_total": len(s.get("lore", [])),
        "market": market,
        "chronicle": [e for e in s.get("event_log", [])[-24:]][::-1],
        "milestones": ["第%d回合·%s" % (m.get("tick", 0), m.get("desc", ""))
                       for m in s.get("milestones", [])[-10:]][::-1],
        "summaries": len(s.get("summaries", [])),
        "archived_events": int(s.get("archived_events", 0)),
        "flags": s.get("world_flags", []),
    }


STATIC_WHITELIST = {
    "/": ("panel.html", "text/html; charset=utf-8"),
    "/panel.html": ("panel.html", "text/html; charset=utf-8"),
    "/panel.css": ("panel.css", "text/css; charset=utf-8"),
    "/panel.js": ("panel.js", "text/javascript; charset=utf-8"),
    "/assets/echarts.min.js": (os.path.join("assets", "echarts.min.js"),
                               "text/javascript; charset=utf-8"),
}

from game_engine.viz_series import SERIES_CAP, load_series, record_sample, series_path  # noqa: E402


# 皮肤注册表：id → 视觉与图表调色板（前端只消费，不在 JS 里写配色表）
SKINS = {
    "xuanshu": {
        "id": "xuanshu", "accent": "#e8b04b", "motif": "玄门·墨金",
        "palette": {"line": "#e8b04b", "area": "rgba(232,176,75,.18)", "bar": "#c07a3a",
                    "hp": "#d9534f", "mp": "#4a90d9", "grid": "#2b3341", "text": "#a3abb9"},
    },
    "neutral": {
        "id": "neutral", "accent": "#8aa6c8", "motif": "通用·石墨",
        "palette": {"line": "#8aa6c8", "area": "rgba(138,166,200,.16)", "bar": "#6f8cab",
                    "hp": "#d9534f", "mp": "#4a90d9", "grid": "#2b3341", "text": "#a3abb9"},
    },
    "ink": {
        "id": "ink", "accent": "#a8b6c1", "motif": "水墨·宣纸",
        "palette": {"line": "#8fb0c9", "area": "rgba(143,176,201,.14)", "bar": "#7d8b96",
                    "hp": "#b4553f", "mp": "#5d7fa3", "grid": "#333a44", "text": "#9aa4b0"},
    },
    "neon": {
        "id": "neon", "accent": "#4fe0c0", "motif": "霓虹·夜城",
        "palette": {"line": "#4fe0c0", "area": "rgba(79,224,192,.16)", "bar": "#c74fe0",
                    "hp": "#ff5d7d", "mp": "#4fa8ff", "grid": "#243044", "text": "#93a4bd"},
    },
}


# 品牌默认值（单一信源，BRAND.md 与 README 引用此处；ui.brand/tagline 可整局覆盖）
DEFAULT_BRAND = "万界·行者"
DEFAULT_TAGLINE = "万界为卷 · 因果为墨"


def skin_for_world(state):
    """世界皮肤：优先取状态里的 ui 配置（设定包可写），否则按世界名启发式，未知一律回退 neutral。
    ui.brand / ui.tagline 让基于本引擎的其他游戏带上自己的品牌。"""
    world = state.get("world_info", {}) or {}
    ui = state.get("ui") if isinstance(state.get("ui"), dict) else {}
    sid = str(ui.get("skin") or "").strip().lower()
    if sid not in SKINS:
        text = ("%s %s" % (world.get("name", ""), " ".join(str(f) for f in (state.get("world_flags") or [])))).lower()
        sid = "xuanshu" if ("xuanshu" in text or "玄枢" in text) else "neutral"
    skin = dict(SKINS[sid])
    skin["palette"] = dict(SKINS[sid]["palette"])
    if ui.get("accent"):
        skin["accent"] = str(ui["accent"])
    if ui.get("motif"):
        skin["motif"] = str(ui["motif"])
    skin["brand"] = str(ui.get("brand") or DEFAULT_BRAND)[:24]
    skin["tagline"] = str(ui.get("tagline") or DEFAULT_TAGLINE)[:48]
    return skin


class Handler(BaseHTTPRequestHandler):
    state_path = None

    def log_message(self, *args):  # 静音访问日志
        pass

    def handle_one_request(self):
        """浏览器/SSE 客户端随时可能掐断连接（刷新、关页签）——这是常态，不是错误。
        默认实现会把 ConnectionAbortedError 抛给 socketserver 打一整篇栈，这里吞掉。"""
        try:
            super().handle_one_request()
        except (ConnectionError, TimeoutError):
            self.close_connection = True

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path):
        """只发白名单里的固定文件；其余路径一律 404（不拼用户输入进文件系统）。"""
        entry = STATIC_WHITELIST.get(path)
        if not entry:
            self._send(404, "text/plain; charset=utf-8", b"not found")
            return
        fname, ctype = entry
        try:
            with open(os.path.join(HTML_DIR, fname), "rb") as f:
                self._send(200, ctype, f.read())
        except OSError:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/state":
            try:
                vm = json.dumps(view_model(self.state_path), ensure_ascii=False).encode("utf-8")
            except FileNotFoundError:
                vm = json.dumps({
                    "error": "对局状态文件不存在：%s" % self.state_path,
                    "hint": "先在对话里开一局（world_init / load_setting），本页会自动接上。",
                }, ensure_ascii=False).encode("utf-8")
            except Exception as e:  # aqg: top-level boundary —— HTTP 端点：任何读取失败都转成页面可读错误，不抛栈
                vm = json.dumps({
                    "error": "状态文件读取失败：%s" % str(e)[:180],
                    "hint": "文件可能正在写入或格式不合法；稍候重试，或先用 snapshot 校验存档。",
                }, ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", vm)
        elif path == "/series":
            body = json.dumps(self._series_payload(), ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
        elif path == "/events":
            self._sse()
        else:
            self._static(path)

    def _series_payload(self):
        """长局态势序列：直接读侧写文件（不读也不写状态文件）。"""
        try:
            samples = load_series(self.state_path)
        except (OSError, ValueError, TypeError):
            samples = []          # 侧写坏行/缺文件 → 图表空态，接口照常 200
        skin = SKINS["neutral"]
        try:
            skin = skin_for_world(load_state(self.state_path))
        except (OSError, ValueError, TypeError):
            pass                  # 状态不可读时调色板退回 neutral；错误态由 /state 负责展示
        return {"samples": samples, "cap": SERIES_CAP, "palette": skin.get("palette", {})}

    def _state_payload(self):
        """SSE 每帧的 JSON：状态不可读时不是断流，而是把原因推给页面显示。"""
        try:
            return json.dumps(view_model(self.state_path), ensure_ascii=False)
        except FileNotFoundError:
            return json.dumps({
                "error": "对局状态文件不存在：%s" % self.state_path,
                "hint": "先在对话里开一局（world_init / load_setting），本页会自动接上。",
            }, ensure_ascii=False)
        except Exception as e:  # aqg: top-level boundary —— SSE 端点：状态不可读时推错误帧而不是断流
            return json.dumps({
                "error": "状态文件读取失败：%s" % str(e)[:180],
                "hint": "文件可能正在写入或格式不合法；稍候重试，或先用 snapshot 校验存档。",
            }, ensure_ascii=False)

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last = object()
        try:
            while True:
                try:
                    st = os.stat(self.state_path)
                    sig = (st.st_mtime_ns, st.st_size)
                except OSError:
                    sig = None
                if sig != last:
                    last = sig
                    body = self._state_payload()
                    self.wfile.write(("event: state\ndata: %s\n\n" % body).encode("utf-8"))
                else:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
                time.sleep(0.5)
        except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
            return


def start(state_path, port=8765, host="127.0.0.1"):
    """启动面板服务（后台线程），返回 (server, 实际端口)。端口被占则自动顺延。"""
    Handler.state_path = os.path.abspath(state_path)
    srv = None
    for p in range(int(port), int(port) + 10):
        try:
            srv = ThreadingHTTPServer((host, p), Handler)
            break
        except OSError:
            continue
    if srv is None:
        raise RuntimeError("端口 %s~%s 都被占用" % (port, int(port) + 9))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main():
    ap = argparse.ArgumentParser(description="万界·行者 实况面板")
    ap.add_argument("--state", default="ww_state.json", help="状态文件路径")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    if not os.path.exists(args.state):
        print("状态文件不存在: %s" % args.state)
        return 1
    srv, port = start(args.state, args.port, args.host)
    print("面板已启动: http://%s:%d/   （盯住 %s，Ctrl+C 退出）" % (args.host, port, args.state))
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
