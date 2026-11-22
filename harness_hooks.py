"""Local lifecycle hooks for the panel GM.

Hooks are plain Python files under ``~/.world-walker/hooks`` (override with
``WW_HOOKS_DIR``).  Each event file is named exactly like the event:

    before_turn.py   fn(ctx) -> {"prompt": "...", "block": "..."} | None
    after_tool.py    fn(ctx) -> {"note": "..."} | {"notes": [...]} | None
    after_turn.py    fn(ctx) -> {"note": "..."} | {"notes": [...]} | None

The child process is started with ``-I``, receives one JSON document on stdin,
and must print one JSON object on stdout.  A short audit hook blocks ordinary
socket / subprocess / shell calls; that is a courtesy rail, not a security
sandbox.  Hooks are off by default, the panel never writes a hook from a
model-facing endpoint, and the UI warns that a hook runs with the user's own
permissions.  Treat a hook exactly like a script you chose to run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

from game_engine import harness_config

MAX_OUTPUT = 16 * 1024
MAX_PROMPT = 1800
MAX_NOTE = 240
MAX_NOTES = 3
LOG_PATH = os.path.expanduser(
    os.environ.get("WW_HOOKS_LOG") or "~/.world-walker/hooks.log")

_BOOTSTRAP = r"""
import json, sys
payload = json.load(sys.stdin)
_DENY = (
    "socket.__new__", "socket.connect", "socket.bind", "socket.getaddrinfo",
    "socket.getnameinfo", "subprocess.Popen", "os.system", "os.exec",
    "os.spawn", "urllib.Request", "http.client.connect", "ftplib.connect",
    "smtplib.connect", "ctypes.dlopen", "ctypes.dlsym",
)
def _guard(event, args):
    if event in _DENY:
        raise PermissionError("hook 不允许网络/子进程调用: " + event)
sys.addaudithook(_guard)
script = payload["script"]
namespace = {"__name__": "ww_hook", "__file__": script, "WW_EVENT": payload}
with open(script, encoding="utf-8") as fh:
    code = compile(fh.read(), script, "exec")
exec(code, namespace)
fn = namespace.get(payload["event"])
if not callable(fn):
    print(json.dumps({"ok": True, "skipped": True}))
else:
    result = fn(payload)
    if result is None:
        result = {}
    if not isinstance(result, dict):
        result = {"note": str(result)}
    print(json.dumps(result, ensure_ascii=False))
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value, limit: int = MAX_NOTE) -> str:
    return str(value if value is not None else "").strip()[:limit]


def _notes(raw) -> list[str]:
    values = raw.get("notes") if isinstance(raw, dict) else None
    if not isinstance(values, (list, tuple)):
        values = []
    single = raw.get("note") if isinstance(raw, dict) else None
    out = []
    for value in list(values) + ([single] if single else []):
        note = _text(value, MAX_NOTE)
        if note and note not in out:
            out.append(note)
        if len(out) >= MAX_NOTES:
            break
    return out


def _sanitize(raw: dict) -> dict:
    prompt = _text(raw.get("prompt"), MAX_PROMPT)
    block = _text(raw.get("block"), 200)
    notes = _notes(raw)
    return {
        "ok": True,
        "ran": True,
        "skipped": bool(raw.get("skipped")),
        "prompt": prompt,
        "block": block,
        "notes": notes,
    }


def _log(event: str, ok: bool, message: str = "") -> None:
    line = "%s %s %s%s\n" % (
        _now(), event, "ok" if ok else "error",
        (" " + _text(message, 220)) if message else "",
    )
    try:
        folder = os.path.dirname(LOG_PATH) or "."
        os.makedirs(folder, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line)
        try:
            os.chmod(LOG_PATH, 0o600)
        except OSError:
            pass
    except OSError:
        pass


def _trim_state(state: dict) -> dict:
    """Keep hook payloads bounded without removing the facts a hook needs."""
    if not isinstance(state, dict):
        return {}
    copy = {}
    for key in ("tick", "world_info", "entities", "game", "gameplay", "narrative",
                "playbook", "rulebook", "world_flags", "relations", "market",
                "config", "event_log", "turns", "summaries", "questlines"):
        if key not in state:
            continue
        value = state[key]
        if key in ("event_log", "turns", "summaries"):
            value = value[-12:] if isinstance(value, list) else value
        copy[key] = value
    return copy


def run(event: str, context: dict | None = None,
        config: dict | None = None) -> dict:
    """Run one hook event.  A broken hook returns an error, never breaks a turn."""
    if event not in harness_config.HOOK_EVENTS:
        return {"ok": False, "ran": False, "error": "未知 hook 事件：%s" % event}
    cfg = harness_config.normalize(config or harness_config.load())
    hooks = cfg["hooks"]
    if not hooks.get("enabled") or event not in (hooks.get("events") or []):
        return {"ok": True, "ran": False, "prompt": "", "block": "", "notes": []}

    folder = os.path.expanduser(hooks.get("dir") or harness_config.HOOK_DIR)
    script = os.path.join(folder, event + ".py")
    if not os.path.isfile(script):
        return {"ok": True, "ran": False, "prompt": "", "block": "", "notes": []}

    ctx = dict(context or {})
    if "state" in ctx:
        ctx["state"] = _trim_state(ctx["state"])
    payload = {
        "event": event,
        "script": script,
        "cwd": os.path.dirname(os.path.abspath(script)),
        "ts": _now(),
    }
    payload.update(ctx)
    try:
        raw = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        return {"ok": False, "ran": False, "error": "hook 上下文不可序列化：%s" % str(exc)[:160]}

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.path.expanduser("~"),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "WW_HOOK_EVENT": event,
    }
    timeout = int(hooks.get("timeout") or 3)
    started = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _BOOTSTRAP, script],
            input=raw, text=True, capture_output=True, timeout=timeout,
            cwd=os.path.dirname(os.path.abspath(script)), env=env,
        )
    except subprocess.TimeoutExpired:
        _log(event, False, "timeout %ss" % timeout)
        return {"ok": False, "ran": True, "error": "hook 超时（%ss）" % timeout}
    except OSError as exc:
        _log(event, False, "spawn %s" % exc)
        return {"ok": False, "ran": True, "error": "hook 无法启动：%s" % str(exc)[:160]}

    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "").strip()[-300:]
        _log(event, False, message)
        return {"ok": False, "ran": True, "error": "hook 退出码 %s：%s" % (
            proc.returncode, message[:180])}

    stdout = (proc.stdout or "").strip()
    if len(stdout) > MAX_OUTPUT:
        message = "hook 输出超过 %d 字节" % MAX_OUTPUT
        _log(event, False, message)
        return {"ok": False, "ran": True, "error": message}
    if not stdout:
        _log(event, True, "empty")
        return {"ok": True, "ran": True, "skipped": True, "prompt": "", "block": "", "notes": []}
    try:
        raw_result = json.loads(stdout.splitlines()[-1])
    except (ValueError, IndexError) as exc:
        _log(event, False, "bad json")
        return {"ok": False, "ran": True, "error": "hook 输出不是 JSON：%s" % str(exc)[:120]}
    result = _sanitize(raw_result if isinstance(raw_result, dict) else {})
    result["latency_ms"] = int((time.time() - started) * 1000)
    _log(event, True, "ran %dms" % result["latency_ms"])
    return result


def status(config: dict | None = None) -> dict:
    cfg = harness_config.normalize(config or harness_config.load())
    info = harness_config.hook_status(cfg)
    tail = []
    try:
        with open(LOG_PATH, encoding="utf-8") as fh:
            tail = [line.rstrip() for line in fh.readlines()[-8:]]
    except OSError:
        pass
    info["log_tail"] = tail
    return info
