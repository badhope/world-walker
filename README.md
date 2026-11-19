# World Walker

**v1.12.0** · **English** · [简体中文](README.zh-CN.md) · [Architecture](ARCHITECTURE.md) · [Gameplay](docs/GAMEPLAY.md) · [Changelog](CHANGELOG.md)

> **You talk. The AI performs. The engine decides. The save remembers.**

World Walker is a **single-player AI tabletop RPG / interactive narrative engine**, not a
game-assistant dashboard. You open one page, say what kind of game you want, and then talk to the
GM in ordinary language. There is no external host to wire up and no second app to keep open.

The model layer is deliberately vendor-neutral: any endpoint that speaks the OpenAI-compatible
`/chat/completions` shape works. Set `base_url`, `api_key` and `model`; bring your own gateway,
local model or aggregator. No provider names, no SDK lock-in.

What stays deterministic is the part a narrator should never improvise: HP, prices, inventory,
relationships, clocks, clues, saves and replay. The AI writes the scene; the engine owns the truth.

`206 rule functions` · `67 MCP tools` · `26 player tools` · `4 setting bundles` · `8 templates` ·
`20 self-check suites` · `0 runtime dependencies`

---

## Why this exists

Most "AI RPG" attempts fail in the same three places. World Walker fixes them in the contract,
not in a longer prompt.

| Failure | What usually happens | What World Walker does |
|---|---|---|
| **The AI plays your character** | It writes what you feel, decide or say next | The GM may describe the world and NPCs, never your inner decision; player agency is a hard rule |
| **NPCs know everything** | Every NPC answers from the whole plot bible | An NPC may only use facts returned by `memory(action=known, character=...)`; otherwise they evade, lie or ask back |
| **Turns have no cost** | Beautiful prose, but no HP, clue, clock or relationship ever changes | Every turn carries a scene card and an audit; a turn without a visible change is flagged |

The campaign is built **during play**, like a GM running a table — not pre-written like a novel.
Session Zero sets genre, play style, role, tone, lethality and boundaries. After that, each turn is
`scene card → player action → world reaction → state change → next hook`.

---

## Install

```bash
pip install -e ".[mcp]"      # core is standard library only; the mcp extra is for MCP mode
```

**No Python?** Download `world-games.exe` — one file, ~30 MB, runs standalone.
Same program, same data.

```bash
wg init my-game.json      # create a starter save
wg play --state my-game.json
```

`wg` is the single front door: `init`, `play`, `serve`, `mcp`, `run`, `doctor`, `version`.
Run `wg --help` for the full list.

### Hook it to an agent

```json
{ "mcpServers": { "world-games": { "command": "world-games-mcp" } } }
```

Works with Claude Code, Codex, Cursor, opencode, or any MCP client. `world-walker-mcp` is a
compatibility alias.

Remote agents can connect over HTTP instead of stdio:

```bash
wg mcp --http --port 8620   # then point any MCP client at http://127.0.0.1:8620/mcp
```

Then:

```
load_setting(path="settings/玄枢界.setting.json")
trade(location="临川城", item="ningyuan_dan", direction="buy", quantity=1)
```

That is a complete game: world, protagonist, NPCs, market, relations, tiers, lorebook, questline,
subsystems. The host calls tools only when a number is needed.

---

## Play it directly

```bash
pip install -e ".[mcp]"
wg init my-game.json
wg play --state my-game.json
```

`wg play` starts the local page. Open `http://127.0.0.1:8899/` and you are in the lobby:
continue a save, or start a new world. No host, no plugin, no second app.

The player surface is one screen: narrative stream on the left, a thin character/quest rail on
the right, one input at the bottom. The old admin console, translation layer, theme scripts and
offline chart bundle are gone; the player shell is a native HTML/CSS/JS trio with no build chain.

## The model

World Walker is vendor-neutral. The model layer only assumes an OpenAI-compatible
`/chat/completions` endpoint:

```json
{ "base_url": "https://your-gateway/v1", "api_key": "sk-...", "model": "any-model" }
```

Set it in the page (`模型 · 去设置`) or with `WW_MODEL_BASE_URL / WW_MODEL_API_KEY /
WW_MODEL_NAME`. The file lives at `~/.world-walker/model.json` with `0600` permissions.
There is no provider list, no vendor SDK and no hidden fallback.

## Session Zero

A new game starts with a conversation, not a template picker:

1. **类型** — mystery, fantasy, wuxia, sci-fi, urban, historical, romance, horror, survival, slice-of-life.
2. **玩法** — investigate, survive, scheme, relate, fight/grow, horror investigation, cozy.
3. **角色** — random, write one line yourself, or use the template's preset.
4. **体验** — tone, difficulty, content boundaries, optional world override.

The engine picks the rule skeleton from the genre (for example wuxia → `tabletop`,
mystery → `mystery`), starts the save and writes a **start card**: where you are, who you are,
what is already moving, the death rule, three hooks and the central question. Templates provide
a skeleton and a seed, not a pre-written plot.

## What the engine owns

| Layer | What it resolves |
|---|---|
| `checks` | d20 / 2d6 / d100 / 4dF / dice pools, roll-under, opposed rolls, success bands |
| `combat` · `economy` · `social` · `karma` | hits and damage, prices, relationships, structured debt |
| `cognition` · `narrative_engine` · `progression` | flow channel, Panarchy phase, tier progression |
| `world_evolution` | factions, rumors, culture, roaming NPCs, world flags |
| `action_log` | command-level replay with per-step state fingerprints |

The engine also owns the **turn contract**: before the model writes, it receives a scene card
(location, present NPCs, what each NPC wants, pressure, open facts, clocks). The model is told to
fill `reveal / cost / outcome / next` before producing prose. After the turn, a lightweight audit
flags a reply that is too short, repeats an opening, makes a decision for the player or leaves no
visible state change.

## One turn, end to end

**Player:** I push the door open and look behind the counter.

```
scene card      → 你在灰岩堡的酒馆；罗兰在柜台后；他不想让你下墓穴；悬赏还贴着
player action   → 推门、观察
world reaction  → 罗兰先开口，试图把话题岔开
state change    → 关系/线索/钟至少变一项
next hook       → 他手边有一把不属于他的钥匙
```

The model writes the prose. The engine settles the numbers and writes the save. If the turn has
no consequence, the audit says so; the next turn can correct it.

## Tools

The model sees 26 player tools, not the old 67-tool MCP surface:

`inspect` `progress` `story` `memory` `context` `characters` `sheet` `systems` `worlds` `calc`
`panel` `new_game` `open_game` `saves` `snapshot` `combat` `combat_preview` `trade` `social`
`karma` `tick` `advance` `travel` `use_item` `roll` `configure`

MCP remains available for advanced hosts, but it is no longer the front door. The player page is.

## Scope

**In scope:** single-player AI GM, Session Zero, turn contract and audit, deterministic rule
settlement, setting bundles, saves, context ledger, NPC knowledge boundaries, replay.

**Out of scope, deliberately:** multiplayer, cloud accounts, a plugin marketplace, pre-written
campaigns sold as content, image generation.

---

## Quality

No pytest suite, by design. Verification is `scripts/verify_*.py` plus behaviour regressions plus
mutation testing: **an assertion must be killable, not merely covered.**

| Suite | Assertions | What it locks |
|---|---|---|
| `verify_formulas.py` | 122 | recompute 77 functions from their docstring math |
| `verify_branches.py` | 192 | exception paths and state branches of low-coverage modules |
| `verify_cli.py` | 21 | read-only invariants, write effects, cross-channel determinism |
| `verify_panel.py` | 103 | view-model contract, legacy saves, static whitelist, inbox guards, theme wiring |
| `verify_mcp_stdio.py` | 67 | real stdio e2e, HTTP transport handshake, tavern ecosystem, read-only zero side effects |
| `verify_world.py` | 54 | self-evolution, phase, flow, morality, terms, prose, ledger |
| `verify_settings.py` | 17 | all four bundles load and evolve (zero-dependency path) |
| `verify_docs.py` | — | version single source, tool count, assertion counts, asset references |
| `verify_i18n.py` | 12 | panel dictionary: unique keys, unambiguous templates, bilingual wiring |
| `verify_mechanics.py` | 44 | rulebook priority/stop, loop detection, NPC knowledge boundary, combat preview, quest DAG, visit predicates, prefix hash, rumor heat, faction intents |
| `verify_theme.py` | 25 | light-first theme, measured WCAG AA contrast in both themes, chart repaint, boot skeleton |
| `verify_replay.py` | 15 | action log chain, seq persistence, canonical hashing, deterministic fingerprint |
| `verify_gameplay.py` | 65 | playbook loops, questline DAG, lorebook semantics |
| `verify_generic.py` | 104 | generic checks, game profile, context ledger, save library, brand |
| `verify_systems.py` | 161 | seven subsystem kinds, eight templates, counters, panel contract |
| `verify_injection.py` | 23 | injection signatures and `untrusted` marking |
| `verify_near_death.py` | 7 | near-death protection |
| `verify_audit_fix.py` | 22 | snapshot restore, concurrent RMW, finite JSON, input boundaries |
| `verify_memory.py` | 7 | leak check and three bounded structures |
| `user_playtest.py` | 47 | player-perspective abuse cases and error readability |
| `smoke_ui.py` | 20 | real Edge render, cards and drawers, responsive, zero JS errors |
| `verify_tests.py` | — | AST-level rejection of tautological assertions |
| `verify_mutation.py` | 53 mutants | **break the code, require tests to go red**; survival must be 0% |

```bash
bash scripts/pre_push_gate.sh     # 32 steps; missing required dependencies fail the gate
```

Coverage gate: core domain ≥70% (measured 82%, including the generic layer); `pyflakes` 0.

---

## Project layout

```
world-walker/                  # repo root IS the game_engine package
├── panel.py                   # player HTTP/SSE server + session-zero/new/chat APIs
├── panel.html / .css / .js    # native player shell: lobby, wizard, play, rail
├── dialog_runtime.py          # GM system prompt, tool loop, turn finish + audit
├── narrative_rules.py         # Session Zero, start card, scene card, turn audit
├── player_view.py             # save -> player-facing payload
├── model_config.py            # OpenAI-compatible base_url / key / model
├── tool_registry.py           # 26 player tools
├── game_service.py            # thin intent layer over the engine
├── host_adapter.py            # optional external-host bridge (not the default path)
├── state_schema.py            # state model / atomic write / transaction lock
├── templates.py               # 8 rule skeletons
├── rules/                     # deterministic settlement functions
├── settings/                  # ready-to-play setting bundles
├── saves/                     # local save library
└── scripts/                   # verification + build tooling
```

---

## FAQ

**Does it need network access?** Only if your model endpoint is remote. The engine and saves are
local; any OpenAI-compatible gateway, local model or aggregator works.

**Does it need an API key?** A real model endpoint usually does. The key is stored in
`~/.world-walker/model.json` with `0600` permissions and is never returned in clear text.

**Can I use it commercially?** MIT. Every name, faction and place in the demo bundles is original.

**Why no pytest?** Assertions must survive "break the code, watch the test go red".
`verify_tests.py` statically rejects tautological assertions; `verify_mutation.py` injects 50 real
defects and requires every one to be killed.

**Who writes the save?** The engine. The player page talks to the local API; the model calls tools;
every mutation goes through one transactional writer, so determinism and rollback stay intact.

**Is power-loss safety guaranteed?** No, and we do not claim it. Saves use atomic replacement with
`.bak` fallback and a re-entrant Windows/POSIX lock, and crash tests cover several interruption
windows. If `<state>.archive-pending` or `.ww-session-transaction-pending` exists, protected reads
and writes are refused and there is no automatic recovery — stop writing, preserve the evidence and
review it manually. Restoring the caller's in-memory state after a failed save is
**not an archive rollback**. See [the archive recovery guide](docs/ARCHIVE_RECOVERY.md).

---

## Regenerate the demo assets

```bash
python scripts/make_demo.py          # 4 real demo saves → docs/demo/
python scripts/shots.py --lang en    # assert, screenshot, record → docs/screenshots/
python scripts/build_exe.py          # standalone executable → dist/
```

---

## License

MIT. Charts by [ECharts](https://echarts.apache.org/) 5.5.1 (Apache-2.0).
Tavern-ecosystem compatibility follows the publicly documented character-card and world-info
conventions; no names or settings from existing works are reused.
