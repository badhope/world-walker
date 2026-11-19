"""World bible / canon layer.

The model is allowed to improvise at the edge of the map, not to rewrite the
map.  This module is the deterministic half of that contract:

* ``normalize`` converts a template/setting bible into a stable shape;
* ``brief`` returns the facts relevant to the current scene;
* ``check`` rejects a proposed fact that collides with a locked fact;
* ``commit`` appends a revealed/rumour fact and promotes an unknown.

Nothing here calls a model.  The prose can be creative; canon is data.
"""

from __future__ import annotations

import copy
import hashlib
import re
from datetime import datetime, timezone

STATUSES = ("immutable", "revealed", "rumor", "unknown", "hidden")
LOCKED_STATUSES = ("immutable", "hidden")
MAX_FACT_TEXT = 600
MAX_FACTS = 500


def _text(value, limit=MAX_FACT_TEXT):
    text = str(value or "").strip()
    return text[:limit]


def _list(value, limit=12):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    out = []
    for item in value:
        text = _text(item, 80)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _slug(value):
    text = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", _text(value, 120)).strip("_")
    return text or "fact"


def _stable_id(*parts):
    raw = "|".join(str(p or "") for p in parts).encode("utf-8")
    return "f_" + hashlib.sha1(raw).hexdigest()[:12]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fact(raw, default_status="revealed", default_source="play"):
    """Normalize one fact.  Returns None for an empty item."""
    if not isinstance(raw, dict):
        return None
    subject = _text(raw.get("subject") or raw.get("about") or raw.get("name"), 120)
    predicate = _text(raw.get("predicate") or raw.get("relation"), 120)
    value = _text(raw.get("value") or raw.get("object") or raw.get("detail"), 300)
    statement = _text(raw.get("statement") or raw.get("truth") or raw.get("text"), 600)
    if not statement:
        statement = "；".join(part for part in (subject, predicate, value) if part)
    if not statement:
        return None
    status = _text(raw.get("status"), 20) or default_status
    if status not in STATUSES:
        status = default_status
    fid = _text(raw.get("id"), 120) or _stable_id(subject, predicate, value, statement)
    if not re.fullmatch(r"[0-9A-Za-z_\-\u4e00-\u9fff]{1,120}", fid):
        fid = _stable_id(fid)
    locked = bool(raw.get("locked", status in LOCKED_STATUSES))
    return {
        "id": fid,
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "statement": statement,
        "status": status,
        "locked": locked,
        "source": _text(raw.get("source"), 180) or default_source,
        "tags": _list(raw.get("tags")),
        "spoiler": _text(raw.get("spoiler"), 20) or ("gm" if status == "immutable" else "public"),
        "tick": int(raw.get("tick", 0) or 0),
    }


def _unknown(raw):
    if not isinstance(raw, dict):
        return None
    question = _text(raw.get("question") or raw.get("statement") or raw.get("text"), 300)
    if not question:
        return None
    uid = _text(raw.get("id"), 120) or _stable_id("unknown", question)
    return {
        "id": uid,
        "question": question,
        "hint": _text(raw.get("hint") or raw.get("tags"), 180),
        "status": "unknown",
    }


def normalize(raw):
    """Return a stable world bible.  Unknown or malformed input never raises."""
    src = raw if isinstance(raw, dict) else {}
    world = src.get("world") if isinstance(src.get("world"), dict) else {}
    sections = {}
    for key, status in (("immutable", "immutable"),
                        ("revealed", "revealed"),
                        ("rumors", "rumor"),
                        ("rumor", "rumor"),
                        ("hidden", "hidden"),
                        ("world_default", "hidden"),
                        ("gm_only", "hidden")):
        raw_section = src.get(key)
        if isinstance(raw_section, dict):
            raw_section = list(raw_section.values())
        if not isinstance(raw_section, list):
            raw_section = []
        sections.setdefault(status, [])
        for item in raw_section:
            fact = _fact(item, default_status=status)
            if fact:
                sections[status].append(fact)

    # A generic ``facts`` list is accepted too: split it by its own status.
    if isinstance(src.get("facts"), list):
        for item in src["facts"]:
            fact = _fact(item)
            if fact:
                sections.setdefault(fact["status"], []).append(fact)

    # De-duplicate by id, and by subject+predicate when ids were auto-generated.
    out = {}
    seen = set()
    for status in ("immutable", "revealed", "rumor", "hidden"):
        bucket = []
        for fact in sections.get(status, []):
            key = (fact["subject"].lower(), fact["predicate"].lower()) if fact["subject"] else ("id", fact["id"])
            if fact["id"] in seen:
                continue
            if key in seen:
                continue
            seen.add(fact["id"])
            seen.add(key)
            bucket.append(fact)
            if len(bucket) >= MAX_FACTS:
                break
        out[status] = bucket

    unknown = []
    raw_unknown = src.get("unknown") if isinstance(src.get("unknown"), list) else []
    for item in raw_unknown:
        entry = _unknown(item)
        if entry:
            unknown.append(entry)

    return {
        "version": 1,
        "world": {
            "name": _text(world.get("name") or src.get("name"), 80),
            "era": _text(world.get("era") or src.get("era"), 80),
            "premise": _text(world.get("premise") or src.get("premise"), 300),
            "genre": _text(world.get("genre") or src.get("genre"), 40),
            "tone": _text(world.get("tone") or src.get("tone"), 120),
        },
        "immutable": out["immutable"],
        "revealed": out["revealed"],
        "rumors": out["rumor"],
        "hidden": out["hidden"],
        "unknown": unknown[:120],
        "updated_tick": int(src.get("updated_tick", 0) or 0),
        "updated_at": _text(src.get("updated_at"), 40) or _now(),
    }


def is_configured(bible):
    bible = bible if isinstance(bible, dict) else {}
    return bool(bible.get("immutable"))


def _tokens(text):
    text = str(text or "").lower()
    words = re.findall(r"[a-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", text)
    out = set(words)
    # Chinese has no spaces: use bigrams so place names and names still match.
    for run in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        for i in range(len(run) - 1):
            out.add(run[i:i + 2])
    return out


def _score(fact, scene_tokens):
    text = " ".join((fact.get("subject") or "", fact.get("predicate") or "",
                     fact.get("value") or "", fact.get("statement") or "",
                     " ".join(fact.get("tags") or []))).lower()
    tokens = _tokens(text)
    return len(tokens & scene_tokens)


def _public(fact):
    return {
        "id": fact.get("id"),
        "subject": fact.get("subject"),
        "predicate": fact.get("predicate"),
        "value": fact.get("value"),
        "statement": fact.get("statement"),
        "status": fact.get("status"),
        "tags": fact.get("tags") or [],
        "source": fact.get("source"),
    }


def brief(state, scene_text="", limit=14):
    """Return the canon facts a GM should read before narrating this scene."""
    bible = normalize((state or {}).get("world_bible") or {})
    if not is_configured(bible):
        return {
            "configured": False,
            "world": bible.get("world") or {},
            "facts": [],
            "unknowns": [],
            "hidden": [],
            "counts": {"immutable": 0, "revealed": 0, "rumors": 0, "hidden": 0, "unknown": 0},
            "message": "本局还没有世界圣经。不要编造底层历史、地图或规则；先调用 canon_init 建立根设定。",
        }
    scene_tokens = _tokens(scene_text)
    immutable = list(bible.get("immutable") or [])
    revealed = sorted(bible.get("revealed") or [],
                      key=lambda f: (_score(f, scene_tokens), f.get("tick", 0)), reverse=True)
    rumors = sorted(bible.get("rumors") or [],
                    key=lambda f: _score(f, scene_tokens), reverse=True)
    hidden = sorted(bible.get("hidden") or [],
                    key=lambda f: (_score(f, scene_tokens), f.get("tick", 0)), reverse=True)
    facts = immutable + revealed[:max(0, limit - len(immutable))]
    facts = facts[:limit]
    unknown = sorted(bible.get("unknown") or [],
                     key=lambda u: len(_tokens(u.get("question")) & scene_tokens), reverse=True)[:4]
    return {
        "configured": True,
        "world": bible.get("world") or {},
        "facts": [_public(f) for f in facts],
        "unknowns": unknown,
        "rumors": [_public(f) for f in rumors[:3]],
        "hidden": [_public(f) for f in hidden[:20]],
        "counts": {
            "immutable": len(immutable),
            "revealed": len(revealed),
            "rumors": len(rumors),
            "hidden": len(hidden),
            "unknown": len(bible.get("unknown") or []),
        },
        "message": "canon 优先于记忆与临场推理；hidden 是世界真相但主角不知道，只能用于判定，不能直接讲给玩家。",
    }


def check(state, facts, allow_override=False, status="revealed"):
    """Check proposed facts against the current bible, without mutating it."""
    bible = normalize((state or {}).get("world_bible") or {})
    if not is_configured(bible):
        return {"ok": False, "configured": False, "conflicts": [],
                "message": "本局还没有世界圣经；先 canon_init 建立根设定。"}
    proposed = []
    for item in facts or []:
        if not isinstance(item, dict):
            continue
        fact = _fact(item, default_status=status)
        if fact:
            proposed.append(fact)
    existing = {}
    for bucket in ("immutable", "revealed", "rumors", "hidden"):
        for fact in bible.get(bucket) or []:
            existing[fact["id"]] = fact
            existing.setdefault((fact["subject"].lower(), fact["predicate"].lower()), fact)
    conflicts = []
    warnings = []
    for fact in proposed:
        if fact["status"] != "immutable" and status == "immutable":
            conflicts.append({
                "code": "status_mismatch",
                "proposed": _public(fact),
                "message": "canon_commit 的 status=immutable 只能提交 immutable 事实。",
            })
            continue
        prior = existing.get(fact["id"]) if fact.get("id") in existing and isinstance(existing.get(fact["id"]), dict) else None
        key_prior = existing.get((fact["subject"].lower(), fact["predicate"].lower())) if fact.get("subject") else None
        prior = prior or key_prior
        if prior and ((prior.get("value") or "") != (fact.get("value") or "")
                      or (prior.get("locked") and (prior.get("statement") or "") != (fact.get("statement") or ""))):
            same = (prior.get("value") or "") == (fact.get("value") or "") \
                and (prior.get("statement") or "") == (fact.get("statement") or "")
            code = "locked_change" if prior.get("locked") else "same_key"
            item = {
                "code": code,
                "existing_id": prior.get("id"),
                "proposed": _public(fact),
                "existing": _public(prior),
                "message": "与已有 canon 冲突：%s / %s" % (prior.get("subject"), prior.get("predicate")),
            }
            if prior.get("locked") and allow_override:
                if fact.get("status") != "immutable":
                    item["code"] = "override_requires_immutable"
                    item["message"] = "改根设定必须同时以 status=immutable 提交。"
                    conflicts.append(item)
                else:
                    item["code"] = "locked_change_override"
                    warnings.append(item)
            elif same:
                warnings.append(item)
            else:
                conflicts.append(item)
        elif fact.get("status") == "immutable" and not allow_override:
            conflicts.append({
                "code": "immutable_without_override",
                "proposed": _public(fact),
                "message": "新增或修改 immutable 事实需要 allow_override=true 和 reason。",
            })
    return {
        "ok": not conflicts,
        "configured": True,
        "conflicts": conflicts,
        "warnings": warnings,
        "proposed_count": len(proposed),
        "message": "通过：可以提交。" if not conflicts else "有冲突：先修正或显式 override。",
    }


def _upsert(bucket, fact):
    for i, old in enumerate(bucket):
        if old.get("id") == fact.get("id"):
            bucket[i] = fact
            return False
        if old.get("subject") and fact.get("subject") \
                and old.get("subject").lower() == fact.get("subject").lower() \
                and old.get("predicate").lower() == fact.get("predicate").lower():
            bucket[i] = fact
            return False
    bucket.append(fact)
    return True


def commit(state, facts, status="revealed", source="play", allow_override=False, reason=""):
    """Validate and commit facts into the state's world bible.

    Returns ``(bible, result)``.  No write happens on conflict.
    """
    bible = normalize((state or {}).get("world_bible") or {})
    result = check(state, facts, allow_override=allow_override, status=status)
    if not result.get("ok"):
        return bible, result
    tick = int((state or {}).get("tick", 0) or 0)
    normalized = []
    for item in facts or []:
        if not isinstance(item, dict):
            continue
        fact = _fact(item, default_status=status, default_source=source)
        if fact:
            fact["tick"] = tick
            fact["source"] = _text(item.get("source"), 180) or source
            normalized.append(fact)
    for fact in normalized:
        if fact["status"] == "immutable":
            _upsert(bible["immutable"], fact)
            # An immutable fact supersedes a revealed/rumour/hidden one with the same key.
            for bucket in ("revealed", "rumors", "hidden"):
                bible[bucket][:] = [f for f in bible[bucket]
                                    if (f.get("subject"), f.get("predicate")) !=
                                    (fact.get("subject"), fact.get("predicate"))]
        elif fact["status"] == "rumor":
            _upsert(bible["rumors"], fact)
        elif fact["status"] == "hidden":
            _upsert(bible["hidden"], fact)
        else:
            _upsert(bible["revealed"], fact)
            # 主角已经知道这件事：从“世界默认但主角未知”里移出，避免同一事实
            # 同时挂在 hidden 和 revealed 两栏，把 GM 的上下文预算吃掉。
            bible["hidden"][:] = [f for f in bible["hidden"]
                                  if f.get("id") != fact.get("id")
                                  and (f.get("subject"), f.get("predicate")) !=
                                  (fact.get("subject"), fact.get("predicate"))]
        # A revealed answer closes a matching unknown question.
        bible["unknown"][:] = [u for u in bible["unknown"]
                               if u.get("id") != fact.get("id")
                               and u.get("question") != fact.get("statement")]
    bible["updated_tick"] = tick
    bible["updated_at"] = _now()
    state["world_bible"] = bible
    return bible, {"ok": True, "committed": len(normalized), "bible": bible,
                   "message": "已写入 canon。"}


def render(brief_data):
    """Render a brief as compact text for the GM system prompt."""
    data = brief_data if isinstance(brief_data, dict) else {}
    if not data.get("configured"):
        return "（未配置世界圣经：不要编造底层设定；先 canon_init。）"
    world = data.get("world") or {}
    head = "世界：%s（%s）" % (world.get("name") or "未命名", world.get("era") or "未定纪元")
    if world.get("premise"):
        head += "；前提：%s" % world["premise"]
    lines = [head, "Canon（只读，优先级高于记忆和临场推理）："]
    for fact in data.get("facts") or []:
        tag = "锁" if fact.get("status") == "immutable" else "揭"
        lines.append("- [%s] %s" % (tag, fact.get("statement")))
    for u in data.get("unknowns") or []:
        lines.append("- [未知] %s" % u.get("question"))
    for r in data.get("rumors") or []:
        lines.append("- [传闻，可能为假] %s" % r.get("statement"))
    hidden = data.get("hidden") or []
    if hidden:
        lines.append("世界默认（主角未知；GM 只能用于判定，不得直接讲给玩家）：")
        for f in hidden:
            lines.append("- [底] %s" % f.get("statement"))
    counts = data.get("counts") or {}
    lines.append("台账：immutable %s / revealed %s / rumors %s / hidden %s / unknown %s" % (
        counts.get("immutable", 0), counts.get("revealed", 0),
        counts.get("rumors", 0), counts.get("hidden", 0), counts.get("unknown", 0)))
    return "\n".join(lines)
