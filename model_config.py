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


ENV_KEYS = {
    "base_url": "WW_MODEL_BASE_URL",
    "api_key": "WW_MODEL_API_KEY",
    "model": "WW_MODEL_NAME",
    "timeout": "WW_MODEL_TIMEOUT",
    "temperature": "WW_MODEL_TEMPERATURE",
    "max_tokens": "WW_MODEL_MAX_TOKENS",
}


def _file_config() -> dict:
    """Only the on-disk config, without environment overrides.

    Used for the setup form and for testing values the user has typed but not
    saved yet.  A stale env var must not silently replace what is on screen.
    """
    raw = {}
    try:
        with open(config_path(), encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError, TypeError):
        raw = {}
    return _clean(raw)


def env_keys() -> list[str]:
    """Names (never values) of environment variables currently overriding the file."""
    return [name for name in ENV_KEYS.values() if os.environ.get(name) not in (None, "")]


def load_config() -> dict:
    """Effective config; environment variables win over the file."""
    cfg = _file_config()
    env = {key: os.environ.get(name) for key, name in ENV_KEYS.items()}
    for key, value in env.items():
        if value not in (None, ""):
            cfg[key] = value
    return _clean(cfg)


def candidate_config(payload: dict) -> dict:
    """Merge unsaved form values over the effective config for Test.

    The key is intentionally reused when the form leaves it blank, so a user can
    test a new endpoint or model without retyping a stored secret.
    """
    base = load_config()
    for key in DEFAULTS:
        value = payload.get(key) if isinstance(payload, dict) else None
        if value not in (None, ""):
            base[key] = value
    return _clean(base)


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
    effective = load_config() if cfg is None else _clean(cfg)
    key = effective.get("api_key") or ""
    masked = ""
    if key:
        masked = key[:4] + "…" + key[-4:] if len(key) > 8 else "已设置"
    overrides = env_keys()
    return {
        "base_url": effective.get("base_url", ""),
        "model": effective.get("model", ""),
        "api_key_masked": masked,
        "has_api_key": bool(key),
        "configured": bool(effective.get("base_url") and effective.get("model")),
        "timeout": effective.get("timeout"),
        "temperature": effective.get("temperature"),
        "max_tokens": effective.get("max_tokens"),
        "source": "environment" if overrides else (
            "file" if os.path.exists(config_path()) else "none"),
        "env_keys": overrides,
    }


def redact(text: str) -> str:
    """Best-effort secret scrub for error messages and logs."""
    text = str(text or "")
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}", "Bearer [redacted]", text)
    text = re.sub(r"sk-[A-Za-z0-9._~+/=-]{8,}", "sk-[redacted]", text)
    return text[:500]
