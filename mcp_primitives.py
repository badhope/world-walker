"""MCP server primitives beyond tools: resources and tool annotations.

Why this exists
---------------
The server exposes 71 tools and one prompt, but had zero **resources** at first. That matters:
in MCP, tools are *model-controlled* (the model decides to call them), while
resources are *application-controlled* — a host can pin live game state, the
current save, or the active rule set into context without asking the model to
fetch anything, and without burning a tool round-trip per turn.

The second gap was tool annotations. Hosts use `readOnlyHint` to auto-approve
calls and `destructiveHint` to require confirmation. Without them every call
looks equally dangerous, so either the host prompts constantly (bad UX) or it
blanket-approves (unsafe). Annotations are only hints — the spec says so — but
omitting them entirely removes the only signal hosts have.

Everything here is read-only and derives from the same state file the tools use,
so it cannot drift from tool behaviour.
"""

from __future__ import annotations

import json

# Tool names that provably never mutate the state file. Kept as an explicit
# allow-list rather than a heuristic: if a new read-only tool is added and not
# listed here it simply gets no annotation (safe default), it does not get
# mislabelled as read-only.
#
# This list must stay disjoint from `mcp_server._STATE_TRANSACTION_TOOLS`.
# Four tools used to sit in both: `narrative` (writes _emergent_seen + event log),
# `narration_context` (writes lorebook sticky/cooldown + codex), `game_sheet`
# (always writes), and `game_profile` (writes whenever a profile is passed).
# Hosts auto-approve `readOnlyHint`, so a conditional writer cannot be listed
# here — `verify_surface.py` S5d enforces the invariant mechanically.
READ_ONLY_TOOLS = frozenset({
    'world_schema', 'read_state', 'status', 'world_state',
    'playbook_info', 'quest_status', 'lore_lookup', 'model', 'model_list',
    'recall', 'recap', 'templates_list', 'template_info', 'template_apply',
    'system_schema', 'system_status', 'session_list', 'pending_actions',
    'context_search', 'context_pack',
    'canon_brief', 'canon_check',
    'character_card_read',
})

# Tools that can destroy user data if misused. Hosts should confirm these.
DESTRUCTIVE_TOOLS = frozenset({
    'session_manage',   # archive / restore / purge
    'restore',          # overwrites the live save from a snapshot
    'session_import',   # can overwrite a save
    'system_remove',
})


def annotations_for(name: str):
    """Return tool annotations for `name`, or None when nothing is known."""
    try:
        from mcp.types import ToolAnnotations
    except ImportError:  # pragma: no cover - older SDK layouts
        return None

    if name in READ_ONLY_TOOLS:
        return ToolAnnotations(read_only_hint=True, open_world_hint=False,
                               idempotent_hint=True)
    if name in DESTRUCTIVE_TOOLS:
        return ToolAnnotations(read_only_hint=False, destructive_hint=True,
                               idempotent_hint=False, open_world_hint=False)
    # Everything else mutates but is additive/idempotent-per-turn in practice.
    return ToolAnnotations(read_only_hint=False, destructive_hint=False,
                           idempotent_hint=False, open_world_hint=False)


def register_resources(server, load_state, state_path_fn, settings_dir, docs_dir):
    """Attach live, read-only MCP resources to `server`.

    Resources are addressed by URI so a host can subscribe or pin them:
        world://state/current     full game state (JSON)
        world://summary/current   compact summary for prompts (text)
        world://rules/schema      state schema reference (JSON)
        world://settings/index    available setting bundles (JSON)
        world://docs/protocol     the MCP play protocol (markdown)
    """
    try:
        from mcp.types import Resource
    except ImportError:  # pragma: no cover
        Resource = None

    def _state():
        path = state_path_fn()
        if not path:
            raise ValueError('no active game: call world_init or load_setting first')
        return path, load_state(path)

    @server.resource('world://state/current',
                     name='Current game state',
                     description='The full JSON state of the active game. Read-only.',
                     mime_type='application/json')
    def state_resource() -> str:
        _path, state = _state()
        return json.dumps(state, ensure_ascii=False)

    @server.resource('world://summary/current',
                     name='Current game summary',
                     description='A compact, prompt-sized summary: turn, player, place, '
                                 'phase, unsettled karma and the latest prose.',
                     mime_type='application/json')
    def summary_resource() -> str:
        _path, state = _state()
        player = (state.get('entities') or {}).get('player') or {}
        panarchy = state.get('panarchy') or {}
        prose = state.get('prose') or []
        # 状态里的权威字段是 karma_ledger（旧存档/夹具可能只有 karma）。
        # 只读 karma 会永远得到 0：长局欠了几百业债，资源摘要却报 0。
        ledger = state.get('karma_ledger')
        if not isinstance(ledger, list):
            ledger = state.get('karma') or []
        karma = sum(float(entry.get('amount') or 0)
                    for entry in ledger
                    if isinstance(entry, dict) and not entry.get('settled'))
        payload = {
            'tick': state.get('tick', 0),
            'world': (state.get('world_info') or {}).get('name', ''),
            'player': {
                'name': player.get('name', ''),
                'level': player.get('level', ''),
                'location': player.get('location', ''),
                'hp': player.get('hp'),
                'hp_max': player.get('hp_max'),
            },
            'phase': panarchy.get('phase'),
            'unsettled_karma': round(karma, 3),
            'latest_prose': (prose[-1].get('text') if prose else ''),
        }
        return json.dumps(payload, ensure_ascii=False)

    @server.resource('world://settings/index',
                     name='Setting bundles',
                     description='Every installed setting bundle with its world name and genre.',
                     mime_type='application/json')
    def settings_resource() -> str:
        import os
        bundles = []
        if os.path.isdir(settings_dir):
            for name in sorted(os.listdir(settings_dir)):
                if not name.endswith('.setting.json'):
                    continue
                try:
                    with open(os.path.join(settings_dir, name), encoding='utf-8') as fh:
                        data = json.load(fh)
                except (OSError, ValueError):
                    continue
                world = data.get('world') or {}
                bundles.append({
                    'file': name,
                    'path': os.path.join(settings_dir, name).replace('\\', '/'),
                    'name': world.get('name', ''),
                    'era': world.get('era', ''),
                    'genre': (data.get('playbook') or {}).get('loop', ''),
                })
        return json.dumps({'bundles': bundles, 'count': len(bundles)}, ensure_ascii=False)

    @server.resource('world://docs/protocol',
                     name='Game master protocol',
                     description='How a host runs the standalone MCP mode: session zero, '
                                 'turn flow, prose ownership, and invariants.',
                     mime_type='text/markdown')
    def protocol_resource() -> str:
        import os
        path = os.path.join(docs_dir, 'MCP_PLAY.md')
        with open(path, encoding='utf-8') as fh:
            return fh.read()

    return Resource
