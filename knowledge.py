"""SQLite 知识库投影层（Knowledge Base）。

设计边界：
  · **JSON 状态仍是唯一事实源**。SQLite 是旁边的一份可丢弃索引（`*.save.json.knowledge.db`），
    可以从任意存档重建；不把游戏状态搬进数据库，避免破坏现有的原子写/快照/回退。
  · 索引角色卡、世界书、canon、事实台账、事件时间线、地点、关系和摘要；统一成
    `items(kind, item_id, title, body, keys, tick, extra)`，供 `knowledge search` 跨表检索。
  · FTS5 用 `trigram` tokenizer：中文可以按 3 字以上子串检索，英文按词元；1-2 字查询
    自动退回 `LIKE`，不依赖分词器或嵌入模型。
  · 不引入向量库。RAG 的向量检索会让提示词前缀抖动、破坏缓存，而且当前模型层只要求
    OpenAI-compatible，不能假设一定有 embeddings 端点。以后要语义检索，再加可选
    `sqlite-vec`/LanceDB 适配器，不改变 JSON 事实源。

这个模块只读 `state`，不写游戏状态；写操作（NPC 状态、世界书、时间线）由 MCP 工具
先写入 state，再调用 `sync()` 刷新索引。
"""

from __future__ import annotations

import json
import os
import re
import sqlite3

DB_SUFFIX = ".knowledge.db"
MAX_TEXT = 4000
INDEX_KINDS = ("character", "worldbook", "canon", "fact", "event",
               "milestone", "place", "relation", "summary")


def database_path(state_path: str) -> str:
    """存档旁边的可丢弃索引文件；没有存档路径时用内存库。"""
    path = str(state_path or "").strip()
    if not path:
        return ":memory:"
    return path + DB_SUFFIX


def _text(value, limit=MAX_TEXT) -> str:
    return str(value or "").strip()[:limit]


def _json(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return "{}"


def _connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def _create(con: sqlite3.Connection) -> bool:
    """建表；返回 FTS5 是否可用。每次 sync 重建，索引永远与 state 同代。"""
    con.executescript("""
        DROP TABLE IF EXISTS items;
        DROP TABLE IF EXISTS search_fts;
        DROP TABLE IF EXISTS meta;
        CREATE TABLE items (
            kind TEXT NOT NULL,
            item_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            keys TEXT NOT NULL DEFAULT '',
            tick INTEGER NOT NULL DEFAULT 0,
            extra TEXT NOT NULL DEFAULT '{}',
            PRIMARY KEY (kind, item_id)
        );
        CREATE INDEX items_kind_tick ON items(kind, tick);
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    fts = True
    try:
        con.execute("""CREATE VIRTUAL TABLE search_fts USING fts5(
            kind, item_id, title, body, keys, tick UNINDEXED,
            tokenize='trigram'
        )""")
    except sqlite3.OperationalError:
        fts = False
    return fts


def _archived_events(state_path: str, limit: int = 800) -> list:
    """读 `<save>.log*.jsonl` 的近期归档；只用于时间线索引，不改变 JSON 事实源。"""
    path = str(state_path or "").strip()
    if not path or path == ":memory:":
        return []
    import glob
    records = []
    try:
        files = sorted(glob.glob(path + ".log*.jsonl"))[-4:]
    except OSError:
        return []
    for filename in files:
        try:
            with open(filename, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(item, dict):
                        records.append(item)
        except OSError:
            continue
    return records[-limit:]


def _item(con, fts: bool, kind: str, item_id: str, title: str, body: str,
          keys, tick: int = 0, extra=None):
    keys_text = " ".join(str(k) for k in (keys or []) if str(k).strip())[:600]
    con.execute(
        "INSERT OR REPLACE INTO items(kind,item_id,title,body,keys,tick,extra) "
        "VALUES(?,?,?,?,?,?,?)",
        (kind, str(item_id), _text(title, 300), _text(body), keys_text,
         int(tick or 0), _json(extra or {})),
    )
    if fts:
        con.execute(
            "INSERT INTO search_fts(kind,item_id,title,body,keys,tick) "
            "VALUES(?,?,?,?,?,?)",
            (kind, str(item_id), _text(title, 300), _text(body), keys_text, int(tick or 0)),
        )


def sync(state: dict, state_path: str = "") -> dict:
    """从 state 重建索引。返回统计；调用方决定是否持久化。"""
    path = database_path(state_path)
    con = _connect(path)
    try:
        fts = _create(con)
        counts = {kind: 0 for kind in INDEX_KINDS}
        tick = int(state.get("tick", 0) or 0)

        for eid, ent in (state.get("entities") or {}).items():
            if not isinstance(ent, dict):
                continue
            body_parts = [
                ent.get("name"), ent.get("faction"), ent.get("level"),
                ent.get("location"), ent.get("activity"), ent.get("intent"),
                ent.get("mood"), ent.get("routine"), ent.get("status"), ent.get("agenda"),
                "、".join(str(a) for a in (ent.get("aliases") or [])),
                ent.get("desc"), ent.get("personality"), ent.get("speech"),
            ]
            _item(con, fts, "character", eid, ent.get("name") or eid,
                  "；".join(str(x) for x in body_parts if x),
                  [ent.get("name"), ent.get("faction"), ent.get("location"),
                   ent.get("activity"), ent.get("status"), ent.get("agenda")]
                  + [str(a) for a in (ent.get("aliases") or [])],
                  int(ent.get("last_seen_tick", tick) or tick),
                  {"entity": ent, "is_player": eid == "player"})
            counts["character"] += 1

        for i, entry in enumerate(state.get("lore") or []):
            if not isinstance(entry, dict):
                continue
            eid = str(entry.get("id") or "lore-%d" % i)
            title = entry.get("comment") or entry.get("name") or eid
            _item(con, fts, "worldbook", eid, title, entry.get("content") or "",
                  list(entry.get("keys") or []) + list(entry.get("secondary_keys") or []),
                  int(entry.get("tick", tick) or tick),
                  {"entry": entry})
            counts["worldbook"] += 1

        bible = state.get("world_bible") or {}
        for status in ("immutable", "revealed", "rumors", "hidden", "unknown"):
            for i, fact in enumerate(bible.get(status) or []):
                if not isinstance(fact, dict):
                    continue
                eid = str(fact.get("id") or "%s-%d" % (status, i))
                title = fact.get("subject") or status
                body = fact.get("statement") or fact.get("question") or fact.get("value") or ""
                _item(con, fts, "canon", "%s:%s" % (status, eid), title, body,
                      [fact.get("subject"), fact.get("predicate"), status],
                      int(fact.get("tick", tick) or tick), {"bible": fact, "status": status})
                counts["canon"] += 1

        ctx = state.get("context") or {}
        for i, fact in enumerate(ctx.get("facts") or []):
            if not isinstance(fact, dict):
                continue
            eid = str(fact.get("id") or "fact-%d" % i)
            _item(con, fts, "fact", eid, fact.get("subject") or fact.get("kind") or "事实",
                  fact.get("text") or "", list(fact.get("keys") or []),
                  int(fact.get("tick", tick) or tick), {"fact": fact})
            counts["fact"] += 1

        for i, event in enumerate(state.get("event_log") or []):
            if not isinstance(event, dict):
                continue
            eid = str(event.get("seq") or "event-%d" % i)
            actors = []
            for key in ("actors", "attacker", "defender", "target", "character", "npc"):
                val = event.get(key)
                if isinstance(val, (list, tuple)):
                    actors.extend(str(x) for x in val)
                elif val:
                    actors.append(str(val))
            _item(con, fts, "event", eid, event.get("type") or "事件",
                  event.get("desc") or "",
                  actors + [event.get("location"), event.get("thread")]
                  + list(event.get("causes") or []),
                  int(event.get("tick", tick) or tick),
                  {"event": event, "actors": actors})
            counts["event"] += 1

        for i, event in enumerate(_archived_events(state_path)):
            if not isinstance(event, dict):
                continue
            eid = "archive-%d-%s" % (i, event.get("seq") or "")
            actors = []
            for key in ("actors", "attacker", "defender", "target", "character", "npc"):
                val = event.get(key)
                if isinstance(val, (list, tuple)):
                    actors.extend(str(x) for x in val)
                elif val:
                    actors.append(str(val))
            _item(con, fts, "event", eid, event.get("type") or "事件",
                  event.get("desc") or "",
                  actors + [event.get("location"), event.get("thread")]
                  + list(event.get("causes") or []),
                  int(event.get("tick", tick) or tick),
                  {"event": event, "actors": actors, "archived": True})
            counts["event"] += 1

        for i, ms in enumerate(state.get("milestones") or []):
            if not isinstance(ms, dict):
                continue
            _item(con, fts, "milestone", "milestone-%d" % i,
                  ms.get("type") or "大事记", ms.get("desc") or "",
                  [ms.get("type")], int(ms.get("tick", tick) or tick), {"milestone": ms})
            counts["milestone"] += 1

        map_nodes = {n.get("name"): n for n in ((state.get("map") or {}).get("nodes") or [])
                     if isinstance(n, dict)}
        for i, (name, info) in enumerate((state.get("places") or {}).items()):
            if not isinstance(info, dict):
                info = {"desc": str(info)}
            node = map_nodes.get(name) or {}
            _item(con, fts, "place", str(name), name, info.get("desc") or "",
                  [name, node.get("role"), node.get("danger")], tick,
                  {"place": info, "map": node})
            counts["place"] += 1

        for key, rel in (state.get("relations") or {}).items():
            if not isinstance(rel, dict):
                continue
            a, _, b = str(key).partition(":")
            _item(con, fts, "relation", str(key), "%s ↔ %s" % (a, b),
                  "好感 %s / 尊重 %s" % (rel.get("affinity", 0), rel.get("respect", 0)),
                  [a, b], tick, {"relation": rel})
            counts["relation"] += 1

        for i, summary in enumerate(state.get("summaries") or []):
            if not isinstance(summary, dict):
                continue
            _item(con, fts, "summary", "summary-%d" % i,
                  "第%s回合摘要" % summary.get("upto_tick", "?"),
                  summary.get("text") or "", ["摘要"], int(summary.get("upto_tick", tick) or tick),
                  {"summary": summary})
            counts["summary"] += 1

        con.executemany("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                        [("version", "1"), ("tick", str(tick)), ("fts", "1" if fts else "0")])
        con.commit()
        return {"path": path, "fts": fts, "counts": counts,
                "total": sum(counts.values()), "tick": tick}
    finally:
        con.close()


def _where_kind(kind: str, params: list) -> str:
    kind = str(kind or "").strip()
    if kind and kind not in INDEX_KINDS:
        raise ValueError("kind 只能是: %s" % " / ".join(INDEX_KINDS))
    if kind:
        params.append(kind)
        return " AND kind = ?"
    return ""


def search(state_path: str, query: str = "", kind: str = "", limit: int = 12) -> dict:
    """跨角色卡/世界书/canon/事实/事件/地点/关系/摘要检索。"""
    path = database_path(state_path)
    if not os.path.isfile(path) and path != ":memory:":
        raise ValueError("知识库尚未建立，请先 knowledge sync")
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    q = str(query or "").strip()
    terms = [t for t in re.split(r"\s+", q) if t][:6]
    limit = max(1, min(50, int(limit or 12)))
    params = []
    kind_clause = _where_kind(kind, params)
    rows = []
    try:
        if terms:
            try:
                fts_q = " OR ".join('"%s"' % t.replace('"', '""') for t in terms)
                sql = ("SELECT kind,item_id,title,body,tick,bm25(search_fts) AS score "
                       "FROM search_fts WHERE search_fts MATCH ?" + kind_clause +
                       " ORDER BY score LIMIT ?")
                rows = [dict(r) for r in con.execute(sql, [fts_q] + params + [limit])]
            except sqlite3.OperationalError:
                rows = []
        if not rows:
            if terms:
                clauses = []
                like_params = []
                for term in terms:
                    like = "%" + term + "%"
                    clauses.append("(title LIKE ? OR body LIKE ? OR keys LIKE ?)")
                    like_params.extend([like, like, like])
                where = " OR ".join(clauses)
            else:
                where = "(title LIKE ? OR body LIKE ? OR keys LIKE ?)"
                like_params = ["%", "%", "%"]
            sql = ("SELECT kind,item_id,title,body,tick,0.0 AS score FROM items "
                   "WHERE (" + where + ")" + kind_clause +
                   " ORDER BY tick DESC, kind, item_id LIMIT ?")
            rows = [dict(r) for r in con.execute(sql, like_params + params + [limit])]
        for row in rows:
            row["snippet"] = str(row.get("body") or "")[:220].replace("\n", " ")
            row["tick"] = int(row.get("tick", 0) or 0)
            row["score"] = round(-float(row.get("score", 0) or 0), 6)
        return {"query": q, "kind": kind, "count": len(rows), "results": rows}
    finally:
        con.close()


def stats(state_path: str) -> dict:
    path = database_path(state_path)
    if not os.path.isfile(path) and path != ":memory:":
        raise ValueError("知识库尚未建立，请先 knowledge sync")
    con = sqlite3.connect(path, timeout=10)
    try:
        counts = {row[0]: int(row[1]) for row in
                  con.execute("SELECT kind,count(*) FROM items GROUP BY kind")}
        total = sum(counts.values())
        size = os.path.getsize(path) if path != ":memory:" and os.path.isfile(path) else 0
        return {"path": path, "total": total, "counts": counts, "bytes": size}
    finally:
        con.close()


def audit(state: dict) -> dict:
    """确定性数据体检：悬空引用、重复条目、坏卡、过期索引源。

    不改状态、不猜测修复；只把“知识库/存档哪里不可信”列出来，交给 GM 或开发者处理。
    """
    issues = []
    entities = state.get("entities") or {}
    relations = state.get("relations") or {}
    lore = state.get("lore") or []
    facts = (state.get("context") or {}).get("facts") or []
    events = state.get("event_log") or []
    map_data = state.get("map") or {}

    def add(severity, code, detail, ref=""):
        issues.append({"severity": severity, "code": code, "detail": str(detail)[:240], "ref": str(ref)})

    for eid, ent in entities.items():
        if not isinstance(ent, dict):
            add("error", "entity_not_object", "实体不是对象", eid)
            continue
        if eid != "player" and not str(ent.get("activity") or "").strip():
            add("info", "npc_without_activity", "NPC 还没有 activity；查不到“现在在干嘛”", eid)
        card = ent.get("card_json")
        if isinstance(card, dict):
            data = card.get("data") if isinstance(card.get("data"), dict) else {}
            if data.get("name") and data.get("name") != ent.get("name"):
                add("warn", "card_name_mismatch", "角色卡名与实体名不一致", eid)
            if not data.get("name"):
                add("warn", "card_missing_name", "角色卡缺 data.name", eid)
        aliases = ent.get("aliases") or []
        if aliases and len(set(map(str, aliases))) != len(aliases):
            add("warn", "duplicate_aliases", "别名有重复", eid)

    for key in relations:
        parts = str(key).split(":")
        if len(parts) != 2:
            add("error", "relation_bad_key", "关系键必须是 a:b", key)
            continue
        for eid in parts:
            if eid not in entities:
                add("error", "relation_dangling", "关系指向不存在的实体", key)

    seen_lore = {}
    for i, entry in enumerate(lore):
        if not isinstance(entry, dict):
            add("error", "lore_not_object", "世界书条目不是对象", "lore-%d" % i)
            continue
        if not str(entry.get("content") or "").strip():
            add("error", "lore_empty", "世界书条目缺 content", entry.get("id") or "lore-%d" % i)
        if not entry.get("keys"):
            add("warn", "lore_no_keys", "世界书条目没有触发键，永远不会命中", entry.get("id") or "lore-%d" % i)
        if entry.get("id") and str(entry.get("id")) in seen_lore:
            add("warn", "duplicate_lore_id", "世界书 id 重复", entry.get("id"))
        seen_lore[str(entry.get("id") or "lore-%d" % i)] = True
        key_sig = tuple(sorted(str(k) for k in (entry.get("keys") or [])))
        if key_sig and key_sig in seen_lore:
            add("info", "duplicate_lore_keys", "两条世界书主键完全相同，可能该合并", entry.get("id") or "lore-%d" % i)
        seen_lore[key_sig] = True

    for i, fact in enumerate(facts):
        if not isinstance(fact, dict):
            add("error", "fact_not_object", "事实不是对象", "fact-%d" % i)
            continue
        witnesses = fact.get("witnesses") or []
        if "*" not in witnesses:
            for who in witnesses:
                if who not in entities:
                    add("warn", "fact_witness_unknown", "事实见证人不在实体表", who)
        if fact.get("status") not in (None, "open", "done", "expired", "superseded"):
            add("warn", "fact_bad_status", "事实 status 不在枚举内", fact.get("id") or "fact-%d" % i)

    seen_seq = set()
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            add("error", "event_not_object", "事件不是对象", "event-%d" % i)
            continue
        seq = event.get("seq")
        if seq is not None and seq in seen_seq:
            add("error", "event_duplicate_seq", "事件 seq 重复", seq)
        if seq is not None:
            seen_seq.add(seq)
        for key in ("actor", "target"):
            eid = event.get(key)
            if eid and eid not in entities:
                add("warn", "event_actor_unknown", "事件角色不在实体表", eid)
        for eid in event.get("actors") or []:
            if eid not in entities:
                add("warn", "event_actor_unknown", "事件 actors 含未知实体", eid)

    nodes = set()
    for n in (map_data.get("nodes") or []):
        if isinstance(n, dict):
            nodes.add(n.get("id"))
            nodes.add(n.get("name"))
    nodes.discard(None)
    for edge in map_data.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        for side in ("a", "b"):
            if edge.get(side) not in nodes:
                add("warn", "map_edge_dangling", "地图边指向未知节点", edge.get(side))

    summary_max = max([int((x or {}).get("upto_tick", 0) or 0) for x in (state.get("summaries") or [])
                       if isinstance(x, dict)] or [0])
    if summary_max > int(state.get("tick", 0) or 0):
        add("error", "summary_future", "摘要回合超过当前 tick", summary_max)

    return {"ok": not any(x["severity"] == "error" for x in issues),
            "issues": issues[:100],
            "counts": {"entities": len(entities), "relations": len(relations), "lore": len(lore),
                       "facts": len(facts), "events": len(events),
                       "errors": sum(1 for x in issues if x["severity"] == "error"),
                       "warnings": sum(1 for x in issues if x["severity"] == "warn"),
                       "infos": sum(1 for x in issues if x["severity"] == "info")}}


def get_character(state_path: str, name: str = "") -> dict:
    path = database_path(state_path)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        needle = str(name or "").strip()
        row = con.execute(
            "SELECT * FROM items WHERE kind='character' AND (item_id=? OR title=?) "
            "ORDER BY tick DESC LIMIT 1", (needle, needle)).fetchone()
        if not row and needle:
            row = con.execute(
                "SELECT * FROM items WHERE kind='character' AND (item_id LIKE ? OR title LIKE ?) "
                "ORDER BY tick DESC LIMIT 1", ("%" + needle + "%", "%" + needle + "%")).fetchone()
        if not row:
            return {}
        out = dict(row)
        try:
            out["extra"] = json.loads(out.get("extra") or "{}")
        except ValueError:
            out["extra"] = {}
        return out
    finally:
        con.close()
