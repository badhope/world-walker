"""Local GM harness configuration.

The engine owns facts and settlement; this module only owns the layer a
player-host can safely tune without editing Python:

* director note (style preferences appended to the GM system prompt)
* table rules (plain-language constraints the model must follow)
* narrative skills (small markdown prompt packs, off by default)
* runtime knobs (history window, tool rounds, audit)
* rule event switches (when the deterministic rulebook is applied)
* local hook settings (executed by ``harness_hooks``)

Everything is data under ``~/.world-walker/harness.json``.  The file is
written atomically with mode 0600 because a hook directory may reveal local
paths.  No secret is stored here.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(ROOT, "narrative_skills")
CONFIG_PATH = os.path.expanduser(
    os.environ.get("WW_HARNESS_CONFIG") or "~/.world-walker/harness.json")
HOOK_DIR = os.path.expanduser(
    os.environ.get("WW_HOOKS_DIR") or "~/.world-walker/hooks")

MAX_NOTE = 2400
MAX_TABLE_RULES = 16
MAX_RULE_CHARS = 240
MAX_SKILLS = 8
MAX_SKILL_BODY = 1800
RUNTIME_DEFAULT = {"audit": True, "history_turns": 12, "tool_rounds": 3}
RULE_EVENTS_DEFAULT = {"turn": True, "tool": True}
HOOK_EVENTS = ("before_turn", "after_tool", "after_turn")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value, limit: int, default: str = "") -> str:
    text = str(value if value is not None else "").strip()
    if not text:
        return default
    return text[:limit]


def _bounded_int(value, default: int, lo: int, hi: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return int(default)
    return max(lo, min(hi, number))


def _bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if value is None:
        return bool(default)
    return bool(value)


def _list(value) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines()]
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _default_config() -> dict:
    return {
        "director_note": "",
        "table_rules": [],
        "skills": [],
        "runtime": dict(RUNTIME_DEFAULT),
        "rule_events": dict(RULE_EVENTS_DEFAULT),
        "hooks": {
            "enabled": False,
            "dir": HOOK_DIR,
            "timeout": 3,
            "events": list(HOOK_EVENTS),
        },
    }


def _skill_files(dir_path: str = SKILLS_DIR) -> list[str]:
    try:
        names = [n for n in os.listdir(dir_path) if n.endswith(".md")]
    except OSError:
        return []
    return sorted(names)


def _parse_skill(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return None
    stem = os.path.basename(path)[:-3]
    name = stem
    summary = ""
    body_lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not summary and stripped.startswith(">"):
            summary = stripped[1:].strip()[:160]
            continue
        if not body_lines and stripped.startswith("# "):
            name = stripped[2:].strip()[:40] or stem
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip()
    if not body:
        return None
    return {
        "id": stem,
        "name": name,
        "summary": summary,
        "body": body[:MAX_SKILL_BODY],
    }


def skill_catalog(dir_path: str = SKILLS_DIR) -> list[dict]:
    rows = []
    for fname in _skill_files(dir_path):
        item = _parse_skill(os.path.join(dir_path, fname))
        if item:
            rows.append(item)
    return rows


def skill_map(dir_path: str = SKILLS_DIR) -> dict:
    return {row["id"]: row for row in skill_catalog(dir_path)}


def normalize(raw, catalog: dict | None = None) -> dict:
    """Return a safe, bounded config. Unknown skills are dropped, never fatal."""
    src = raw if isinstance(raw, dict) else {}
    catalog = catalog if isinstance(catalog, dict) else skill_map()

    note = _text(src.get("director_note") or src.get("note"), MAX_NOTE)
    rules = []
    seen = set()
    for item in _list(src.get("table_rules") or src.get("rules")):
        rule = _text(item, MAX_RULE_CHARS)
        if not rule or rule in seen:
            continue
        seen.add(rule)
        rules.append(rule)
        if len(rules) >= MAX_TABLE_RULES:
            break

    skills = []
    for item in _list(src.get("skills")):
        skill_id = _text(item, 60)
        if skill_id in catalog and skill_id not in skills:
            skills.append(skill_id)
        if len(skills) >= MAX_SKILLS:
            break

    runtime_raw = src.get("runtime") if isinstance(src.get("runtime"), dict) else {}
    runtime = {
        "audit": _bool(runtime_raw.get("audit"), RUNTIME_DEFAULT["audit"]),
        "history_turns": _bounded_int(
            runtime_raw.get("history_turns"), RUNTIME_DEFAULT["history_turns"], 4, 30),
        "tool_rounds": _bounded_int(
            runtime_raw.get("tool_rounds"), RUNTIME_DEFAULT["tool_rounds"], 1, 6),
    }

    events_raw = src.get("rule_events") if isinstance(src.get("rule_events"), dict) else {}
    rule_events = {
        "turn": _bool(events_raw.get("turn"), RULE_EVENTS_DEFAULT["turn"]),
        "tool": _bool(events_raw.get("tool"), RULE_EVENTS_DEFAULT["tool"]),
    }

    hooks_raw = src.get("hooks") if isinstance(src.get("hooks"), dict) else {}
    hook_dir = _text(hooks_raw.get("dir") or HOOK_DIR, 500, HOOK_DIR)
    hook_dir = os.path.expanduser(hook_dir)
    hook_events = []
    for item in _list(hooks_raw.get("events") or HOOK_EVENTS):
        event = _text(item, 40)
        if event in HOOK_EVENTS and event not in hook_events:
            hook_events.append(event)
    if not hook_events:
        hook_events = list(HOOK_EVENTS)
    hooks = {
        "enabled": _bool(hooks_raw.get("enabled"), False),
        "dir": hook_dir,
        "timeout": _bounded_int(hooks_raw.get("timeout"), 3, 1, 10),
        "events": hook_events,
    }

    return {
        "director_note": note,
        "table_rules": rules,
        "skills": skills,
        "runtime": runtime,
        "rule_events": rule_events,
        "hooks": hooks,
    }


def load(path: str | None = None) -> dict:
    """Load the config; a malformed file falls back to defaults, never crashes a turn."""
    target = os.path.expanduser(path or CONFIG_PATH)
    try:
        with open(target, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError, TypeError):
        return normalize({})
    return normalize(raw)


def save(raw, path: str | None = None) -> dict:
    """Atomically persist a normalized config with mode 0600."""
    target = os.path.expanduser(path or CONFIG_PATH)
    cfg = normalize(raw)
    folder = os.path.dirname(target) or "."
    os.makedirs(folder, exist_ok=True, mode=0o700)
    if cfg["hooks"]["enabled"]:
        try:
            os.makedirs(os.path.expanduser(cfg["hooks"]["dir"]), exist_ok=True, mode=0o700)
        except OSError:
            pass
    fd, tmp = tempfile.mkstemp(prefix=".harness-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return cfg


def public_config(path: str | None = None) -> dict:
    target = os.path.expanduser(path or CONFIG_PATH)
    cfg = load(target)
    catalog = skill_catalog()
    enabled = set(cfg["skills"])
    rows = []
    for item in catalog:
        rows.append({
            "id": item["id"],
            "name": item["name"],
            "summary": item["summary"],
            "enabled": item["id"] in enabled,
        })
    source = "file" if os.path.isfile(target) else "default"
    return {
        "ok": True,
        "config": cfg,
        "skills": rows,
        "source": source,
        "updated": _now(),
    }


def prompt_sections(cfg: dict | None = None) -> str:
    """Render the player-authored layer. It is appended after the engine policy."""
    cfg = normalize(cfg or load())
    parts = []
    note = cfg.get("director_note") or ""
    if note:
        parts.extend([
            "## DIRECTOR NOTE（玩家给的导演偏好）",
            "以下只改叙述口味，不得覆盖上面的 POLICY、CANON 与工具结算。",
            note,
        ])
    rules = cfg.get("table_rules") or []
    if rules:
        parts.append("## TABLE RULES（玩家定的桌面规则）")
        parts.extend("- %s" % rule for rule in rules)
    skills = cfg.get("skills") or []
    if skills:
        catalog = skill_map()
        parts.append("## ACTIVE SKILLS（玩家启用的叙事技能）")
        for skill_id in skills:
            item = catalog.get(skill_id)
            if not item:
                continue
            parts.append("### %s" % item["name"])
            if item.get("summary"):
                parts.append("> %s" % item["summary"])
            parts.append(item["body"])
    return "\n".join(parts)


def hook_status(cfg: dict | None = None) -> dict:
    """Describe the local hook slot without reading script contents."""
    cfg = normalize(cfg or load())
    hooks = cfg["hooks"]
    folder = os.path.expanduser(hooks.get("dir") or HOOK_DIR)
    scripts = []
    for event in HOOK_EVENTS:
        path = os.path.join(folder, event + ".py")
        scripts.append({
            "event": event,
            "exists": os.path.isfile(path),
            "path": path,
        })
    summary = {
        "enabled": bool(hooks.get("enabled")),
        "dir": folder,
        "timeout": hooks.get("timeout"),
        "events": list(hooks.get("events") or []),
        "scripts": scripts,
        "ready": any(row["exists"] for row in scripts),
    }
    return summary
