"""Single source of truth for turning a setting/template into a fresh save.

Before this module existed the same sequence was written three times:
``panel.py`` (HTTP new game), ``mcp_server.session_new`` and
``mcp_server.template_start``.  They drifted: the panel path kept importing
the optional MCP SDK, so a pure-stdlib install could not start a game.  Keep
the build/write rules here and let every entry point call the same functions.
"""

from __future__ import annotations

import json
import os

from game_engine import input_policy
from game_engine import sessions as session_store
from game_engine import settings_loader
from game_engine import state_schema
from game_engine import templates


def build_from_setting(setting_path: str, *, seed=None, package_root: str | None = None, mode=None):
    """Load a setting bundle and project it into a runnable state."""
    bundle = input_policy.load_setting(setting_path, package_root=package_root)
    state = settings_loader.build_state(bundle, seed=seed, mode=mode)
    settings_loader.apply_runtime_fields(state, bundle)
    return state, bundle


def build_from_template(template: str, *, overrides=None, name: str = "",
                        player_name: str = "", mode=None):
    """Load a template, validate it, and project it into a runnable state."""
    data = templates.get(template)
    problems = templates.validate(data)
    if problems:
        raise ValueError("模板 %s 结构不完整: %s" % (template, "; ".join(problems[:4])))
    bundle = templates.to_bundle(
        template, overrides=overrides, name=name, player_name=player_name)
    state = settings_loader.build_state(bundle, mode=mode)
    settings_loader.apply_runtime_fields(state, bundle)
    return state, bundle


def build_from_state(state: dict):
    """Validate an explicitly supplied initial state and return a detached copy."""
    input_policy.validate_state_data(state)
    built = json.loads(json.dumps(state, ensure_ascii=False, allow_nan=False))
    return built


def write_new_state(state: dict, *, root: str, name: str, path: str = "") -> tuple[str, str]:
    """Write a fresh state once, refusing an existing target.

    Returns ``(absolute state path, safe display name)``.  The path is
    constrained to ``root`` unless the caller deliberately passes an
    explicit path (template_start does this for host-owned locations).
    """
    input_policy.validate_state_data(state)
    safe = session_store.safe_name(name)
    if path:
        target = input_policy.validate_state_path(path, must_exist=False, root=None)
    else:
        target = session_store.save_path(root, safe, create_dir=True)
        target = input_policy.validate_state_path(target, must_exist=False, root=root)
    if os.path.lexists(target):
        raise ValueError("同名存档已存在（换一个局名，或先归档旧局）")
    state_schema.save_state(state, target, allow_create=True)
    return target, safe
