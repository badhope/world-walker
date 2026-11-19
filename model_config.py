"""Local model configuration for the player runtime.

Only the OpenAI-compatible shape is stored: base_url + api_key + model.  No
provider names, no provider-specific defaults, no hidden fallbacks.  A user can
point this at any gateway that speaks /chat/completions and /models.
"""

from __future__ import annotations

import json
import os
import re
import tempfile

CONFIG_ENV = "WW_MODEL_CONFIG"
DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".world-walker")
DEFAULT_PATH = os.path.join(DEFAULT_DIR, "model.json")

DEFAULTS = {
    "base_url": "",
    "api_key": "",
    "model": "",
    "timeout": 60,
    "temperature": 0.7,
    "max_tokens": 1200,
}


def config_path() -> str:
    return os.path.abspath(os.environ.get(CONFIG_ENV) or DEFAULT_PATH)


def _clean(raw) -> dict:
    out = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return out
    out["base_url"] = str(raw.get("base_url") or "").strip().rstrip("/")
    out["api_key"] = str(raw.get("api_key") or "").strip()
    out["model"] = str(raw.get("model") or "").strip()
    for key in ("timeout", "temperature", "max_tokens"):
        try:
            out[key] = float(raw.get(key, out[key])) if key != "max_tokens" else int(raw.get(key, out[key]))
        except (TypeError, ValueError):
            pass
    out["timeout"] = max(1.0, min(300.0, float(out["timeout"])))
    out["temperature"] = max(0.0, min(2.0, float(out["temperature"])))
    out["max_tokens"] = max(1, min(32000, int(out["max_tokens"])))
    return out


def load_config() -> dict:
    """Read config; environment variables win over the file."""
    raw = {}
    path = config_path()
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError, TypeError):
        raw = {}
    cfg = _clean(raw)
    env = {
        "base_url": os.environ.get("WW_MODEL_BASE_URL"),
        "api_key": os.environ.get("WW_MODEL_API_KEY"),
        "model": os.environ.get("WW_MODEL_NAME"),
        "timeout": os.environ.get("WW_MODEL_TIMEOUT"),
        "temperature": os.environ.get("WW_MODEL_TEMPERATURE"),
        "max_tokens": os.environ.get("WW_MODEL_MAX_TOKENS"),
    }
    for key, value in env.items():
        if value not in (None, ""):
            cfg[key] = value
    return _clean(cfg)


def save_config(payload: dict) -> dict:
    """Persist config atomically with 0600 permissions; never write into the repo."""
    cfg = _clean(payload)
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="model-", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass
    return cfg


def public_config(cfg: dict | None = None) -> dict:
    cfg = load_config() if cfg is None else _clean(cfg)
    key = cfg.get("api_key") or ""
    masked = ""
    if key:
        masked = key[:4] + "…" + key[-4:] if len(key) > 8 else "已设置"
    return {
        "base_url": cfg.get("base_url", ""),
        "model": cfg.get("model", ""),
        "api_key_masked": masked,
        "configured": bool(cfg.get("base_url") and cfg.get("model")),
        "timeout": cfg.get("timeout"),
        "temperature": cfg.get("temperature"),
        "max_tokens": cfg.get("max_tokens"),
    }


def redact(text: str) -> str:
    """Best-effort secret scrub for error messages and logs."""
    text = str(text or "")
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}", "Bearer [redacted]", text)
    text = re.sub(r"sk-[A-Za-z0-9._~+/=-]{8,}", "sk-[redacted]", text)
    return text[:500]
