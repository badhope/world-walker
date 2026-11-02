# World Games

**v1.5.1** · **English** · [简体中文](README.zh-CN.md) · [Architecture](ARCHITECTURE.md) · [Gameplay](docs/GAMEPLAY.md) · [Benchmark](docs/BENCHMARK.md) · [Changelog](CHANGELOG.md) · [Live site](https://badhope.github.io/world-walker/)

> **The AI narrates. The engine decides.**

World Games is the rules layer for AI-driven interactive games. Your agent writes prose;
a deterministic engine resolves every hit, price, relationship and faction shift, then
persists it to one auditable state file.

`188 rule functions` · `64 MCP tools` · `4 playable worlds` · `8 game templates` · `0 runtime dependencies`

<p align="center">
  <img src="docs/screenshots/stage-xuanshu.png" alt="Live stage — turn 500 of a real save" width="100%">
</p>

<p align="center">
  <a href="docs/screenshots/walkthrough.mp4">▶ 16-second recording of a real session</a>
</p>

---

## What it gives you

Three problems kill long AI-run games. World Games fixes each one with code, not prompt wording.

| Problem | What usually happens | What World Games does |
|---|---|---|
| Numbers drift | The model invents damage, prices, HP | **Rule functions** resolve them; same state + seed + actions replay byte-identically |
| The AI forgets | Context window overflows, old facts vanish | **Context ledger** persists clues, promises and facts to disk; `context_pack` returns what fits the budget |
| Saves become chaos | One JSON file, hand-managed | **Save library** — multiple runs, snapshots, trash, all through `session_*` |

Two more things most frameworks skip:

- **The world moves on its own.** Every `tick` advances factions (logistic growth + Lotka–Volterra pressure),
  rumors (SIR), culture (Deffuant), roaming NPCs and a Panarchy `r → K → Ω → α` cycle driven by real stock.
  Do not call `tick` and the world stands still — that is intentional, not a bug.
- **The panel is read-only, and bilingual.** A local web stage renders the real state in
  English by default, with a one-click Chinese switch. It never writes.
  Players can queue actions to a sidecar file; the host drains them with `pending_actions` and settles normally.
  One writer, one truth.

---

## Install

```bash
pip install -e ".[mcp]"      # core is standard library only; the mcp extra is for MCP mode
```

Register with any MCP client (Claude Code / Codex / Cursor / opencode):

```json
{ "mcpServers": { "world-games": { "command": "world-games-mcp" } } }
```

`world-walker-mcp` still works as a compatibility alias.

## Start a game

```
load_setting(path="settings/玄枢界.setting.json")
```

That is a full game: world, protagonist, NPCs, market, relations, tiers, lorebook, questline, subsystems.

Then play. The host calls tools when a number is needed:

```
You: I walk into the Wanshi trading house and slap the torn page on the counter.

Agent → trade(location="临川城", item="ningyuan_dan", direction="buy", quantity=1)
      → social(actor="player", target="shi_sanniang", event="cooperate")
      → narration_context(scene_text="万石商行")
      → publish_prose(text="...")
      → tick()
```

No MCP client? The CLI covers the same engine:

```bash
python init_game.py
python engine.py world_state --state game_state.json
python engine.py combat --state game_state.json --attacker player --defender goblin --action_type heavy
python panel.py --state game_state.json     # open the read-only stage
```

## Play something that is not cultivation

No setting bundle needed. Define your own profile and go:

```
session_new(name="my table")
game_profile({title:"Investigation", kind:"investigation",
              resources:[{key:"sanity", label:"Sanity", value:8, min:0, max:10}],
              meters:[{key:"clue", label:"Clues", value:0, min:0, max:12}]})
roll(attribute="per", difficulty=12, dice="2d6", reason="search the archive")
context_remember("The janitor says the lighthouse lit last night", kind="clue", keys=["lighthouse"])
context_pack(scene_text="lighthouse")
```

Or start from a template:

```
template_start(template="mystery", name="my case",
               overrides={"world": {"name": "Rain Harbor"}})
```

---

## Screens

Every image below is a real render of a real save, asserted element-by-element in Edge by
`scripts/shots.py`. Source saves live in [`docs/demo/`](docs/demo/).

| Xuanshu · Eastern fantasy · ink-gold | Zhejian · Wuxia · ink |
|---|---|
| ![Xuanshu](docs/screenshots/stage-xuanshu.png) | ![Zhejian](docs/screenshots/stage-ink.png) |
| **Neon Abyss · cyberpunk · neon** | **Fogport · investigation · graphite** |
| ![Neon](docs/screenshots/stage-neon.png) | ![Fogport](docs/screenshots/stage-neutral.png) |

Skins are the surface. What actually changes per world is **vocabulary, tiers, currency and place
descriptions**: a bundle declares `terms: { level: "身手", gold: "银两" }` and the panel never shows
"境界 / 灵石" again. `scripts/verify_settings.py` asserts this for every bundle.

| | |
|---|---|
| ![World pulse](docs/screenshots/drawer-world.png) | ![Character card](docs/screenshots/character-card.png) |
| **World pulse** — Panarchy phase, faction stock, connectedness, intensity, rumor heat, advanced by `tick` | **Character card** — click anyone on stage to read their card text |
| ![Command palette](docs/screenshots/command-palette.png) | ![Action queue](docs/screenshots/action-queue.png) |
| **Command palette** (`Ctrl/⌘+K`), fully keyboard reachable | **Action queue** — queue in the browser, the host drains it via `pending_actions` |

| Codex | Market | Milestones |
|---|---|---|
| ![Codex](docs/screenshots/drawer-codex.png) | ![Market](docs/screenshots/drawer-market.png) | ![Milestones](docs/screenshots/drawer-milestones.png) |

| 768px | 320px | Help |
|---|---|---|
| ![Tablet](docs/screenshots/stage-768.png) | ![Narrow](docs/screenshots/stage-320.png) | ![Help](docs/screenshots/help.png) |

| Share mode (hides paths and controls) | First-visit guide |
|---|---|
| ![Share mode](docs/screenshots/share-mode.png) | ![First visit](docs/screenshots/first-visit.png) |

---

## The 64 tools

| Group | Tools |
|---|---|
| Setup and saves (9) | `session_new` `session_list` `session_switch` `session_snapshot` `session_manage` `session_import` `load_setting` `world_init` `world_open` |
| Per-turn core (5) | `pending_actions` `context_pack` `narration_context` `publish_prose` `tick` |
| Checks and numbers (11) | `roll` `combat` `trade` `social` `karma` `advance` `use_item` `game_profile` `game_adjust` `game_tag` `game_sheet` |
| World and place (9) | `travel` `world_state` `narrative` `status` `playbook_info` `quest_status` `quest_advance` `lore_lookup` `failure_tick` |
| Memory and recall (7) | `context_remember` `context_search` `context_forget` `recall` `write_summary` `recap` `read_state` |
| Systems and templates (9) | `templates_list` `template_info` `template_apply` `template_start` `system_define` `system_remove` `system_run` `system_status` `system_schema` |
| Ecosystem and tooling (13) | `character_card_read` `add_character` `import_lorebook` `spawn_npc` `model` `model_list` `merit` `narrative_weight` `snapshot` `restore` `configure` `open_panel` `close_panel` `world_schema` |

Full parameters and calling conventions: [GAME_MASTER_PROTOCOL.md](GAME_MASTER_PROTOCOL.md).

---

## One turn, end to end

Real return values from the Fogport investigation bundle.

**Player:** I go to the docks and ask the gatekeeper whether the lighthouse has been lit.

```
1. context_pack(scene_text="码头 灯塔 门房")
   → playbook (choice · clues 0/24), open clues, recent events

2. roll(attribute="per", difficulty=9, dice="2d6", reason="ask about the lighthouse")
   → {"rolls":[1,1], "total":2, "difficulty":9, "margin":-7, "level":"failure"}

3. context_remember("The gatekeeper says the lighthouse burned for three minutes last night",
                     kind="clue", keys=["lighthouse","gatekeeper"], source="gatekeeper")
   → {"fact":{"id":"f0001", ...}, "created":true}

4. game_adjust("clue", delta=1)    → {"after":1, "at_max":false}
   game_adjust("sanity", delta=-1) → {"after":7, "at_min":false}

5. publish_prose("The rain did not stop. The gatekeeper crushed his cigarette on the sill
                  and said the lighthouse burned for three minutes.")
6. tick()  → one turn of world evolution
```

Everything lands in one state file: checks under `checks`, facts under `context.facts`,
resources under `game`, prose under `prose`, world under `panarchy/factions/...`.
The panel reads those fields and nothing else.

---

## Systems and templates

### Seven pluggable subsystems

Gameplay mechanics are **data**, not code. Add or remove them at runtime.

| Kind | Manages | Actions |
|---|---|---|
| `time` | day/hour/minute, season, weather | `advance(minutes)`, `status` |
| `loot` | weighted drop tables, quantity ranges, empty rolls | `roll(table, times, grant)`, `list` |
| `craft` | recipes, material checks, skill roll, partial refund | `craft(recipe)`, `list` |
| `reputation` | faction standing −100..100 with tiers | `adjust(faction, delta)`, `status` |
| `achievement` | conditions (questline predicate language) + rewards | `check`, `list` |
| `progression` | XP curve, levels, per-level attribute growth | `grant(amount)`, `status` |
| `custom` | restricted effect list (resource/attribute/meter/flag/fact/reputation/xp/time/loot) | `<action>`, `list` |

All deterministic: subsystem randomness derives from `sha256(seed|tick|...)` and never consumes
`rng_counter`. Runtime lives in `state["systems"]["rt"]`, so a snapshot rollback rolls subsystems back too.

### Eight playable templates

| Template | Genre | Loop | Systems |
|---|---|---|---|
| `jrpg` | fantasy adventure | freeform | 7 |
| `mystery` | investigation | choice | 5 |
| `management` | shop management | mud | 4 |
| `survival` | post-apocalypse | mud | 4 |
| `narrative` | emotional story | freeform | 4 |
| `cozy` | rural life | freeform | 4 |
| `tabletop` | tabletop RPG | ttrpg | 5 |
| `immersive` | immersive sim | ttrpg | 4 |

Templates are starting points, not lock-in: `overrides` deep-merges dicts and replaces lists;
`template_apply` returns the bundle without writing state.

---

## Four play loops, one rule set

`playbook` describes how a game is played and gives the host narration guidance.

| Field | Values | Effect |
|---|---|---|
| `loop` | `freeform` / `choice` / `mud` / `ttrpg` | free input / options / location commands / declare → resolve → consequence |
| `input` | `natural` / `choice` / `command` | player input form |
| `progress` | `{axis, label, max}` | `level` / `gold` / `reputation` / `knowledge` / `clock` |
| `failure` | `{mode, label, max}` | `hp` / `sanity` / `clock` / `deadline` / `none` |
| `beat` | `{pattern, every}` | beat sequence, e.g. daily · friction · escalation · cost · payoff |
| `context` | `{inject, max_lore, scan_depth}` | per-turn context injection policy |

The loops guide the host; the engine does not enforce them. Failure does not require hit points —
a creditor at the door, a tail, or a drained sanity meter are all valid, advanced by `failure_tick`.

The four bundles demonstrate the four loops: Xuanshu `freeform`, Zhejian `ttrpg`, Neon Abyss `mud`, Fogport `choice`.

### Questlines

A questline is a stage DAG whose predicates read world state only:

```json
{
  "id": "fog_lighthouse",
  "title": "Keep the lighthouse dark",
  "visibility": {"flag": "unsigned_letter"},
  "stages": [
    {"id": "letter", "title": "The letter", "objectives": ["find out who wrote it"],
     "exit_if": {"visited": "fog_harbor"}, "next": ["keeper"]},
    {"id": "keeper", "title": "The keeper", "objectives": ["find old Shen"], "next": []}
  ],
  "reward": {"flags": ["lighthouse_truth"]}
}
```

- **Predicates:** `flag` / `visited` / `gold_gte` / `karma_gte` / `tier_gte` / `relation_gte` / `item_gte` / `counter_gte` / `stage_done`, composable with `all` / `any` / `not`.
- **Dormant is hidden** — unmet `visibility` keeps a quest out of the panel, so it never becomes a chore list.
- **Only `exit_if` advances** — a stage without one never moves on its own; the host calls `quest_advance`.
- **Failure wins** — `fail_if` or `deadline_tick` short-circuits progress.
- **Rewards pay once** — repeated ticks after completion pay nothing.
- Loading validates the DAG: cycles and dangling `next` are rejected.

### Lorebook

SillyTavern semantics, but deterministic per tick:

| Semantics | Status |
|---|---|
| `keys` / `secondary_keys` / `selective` | supported |
| `selectiveLogic` (AND_ANY / NOT_ALL / NOT_ANY / AND_ALL) | supported |
| `constant` / `insertion_order` / `enabled` | supported |
| `probability` / `use_probability` | supported, derived from `sha256(seed|tick|entry)` |
| `sticky` / `cooldown` / `delay` | supported, tick-based, persisted |
| `group` / `group_weight` / `group_override` | supported, one entry per group |
| `scan_depth` / `match_whole_words` / `exclude_recursion` | supported |
| Recursive scanning | supported, **off by default** |
| `position` / `depth` / `role` / `outlet` | not supported — prompt layout belongs to the host |
| `vectorized` / `automationId` / `characters` filters | not supported — needs embeddings or front-end scripts |

The panel's lorebook drawer shows trigger counts and remaining sticky/cooldown, so you can answer
"why was this paragraph injected". `lore_lookup` previews a trigger for arbitrary text without
writing state or consuming cooldown.

### Setting bundles

One JSON file is one world. Format: [settings/README.md](settings/README.md).

| Bundle | Genre | Highlights |
|---|---|---|
| [`玄枢界`](settings/玄枢界.setting.json) | Eastern fantasy | ten cultivation tiers, crystal economy, eight factions, 21 lorebook entries |
| [`折剑行`](settings/折剑行.setting.json) | Wuxia | seven martial tiers, broken-sword main line, pawnshop economy |
| [`霓虹深渊`](settings/霓虹深渊.setting.json) | Cyberpunk | F–S ratings, credits, cyberware and memory, endless rain |
| [`雾港`](settings/雾港.setting.json) | Investigation | six investigator tiers, sanity/stamina, lighthouse mystery |

`scripts/verify_settings.py` asserts each bundle loads completely, that term coverage leaves no
foreign vocabulary, that currency and brand persist, and that factions and phase still move after 15 turns.

---

## Scope

**In scope:** rule resolution, setting bundles, saves, context ledger, host narration guidance,
SillyTavern character cards (PNG/JSON, V1–V3) and world info.

**Out of scope, deliberately:** image generation, multiplayer, cloud accounts, plugin marketplace.
These are trade-offs with reasons in [ROADMAP.md](ROADMAP.md), not oversights.

---

## Quality

No pytest suite, by design. Verification is `scripts/verify_*.py` plus behavior regressions plus
mutation testing: **an assertion must be killable, not merely covered.**

| Suite | Assertions | What it locks |
|---|---|---|
| `verify_formulas.py` | 122 | recompute 77 functions from their docstring math |
| `verify_branches.py` | 192 | exception paths and state branches of low-coverage modules |
| `verify_cli.py` | 21 | read-only invariants, write effects, cross-channel determinism, CLI tick drives the world |
| `verify_panel.py` | 89 | view-model contract, legacy saves, static whitelist, inbox guards |
| `verify_mcp_stdio.py` | 64 | real stdio e2e, tavern ecosystem, read-only zero side effects |
| `verify_world.py` | 48 | self-evolution, phase, flow, morality, terms, prose, ledger |
| `verify_settings.py` | 17 | all four bundles load and evolve (zero-dependency path) |
| `verify_docs.py` | — | version single source, tool count, assertion counts, asset references |
| `verify_i18n.py` | 12 | panel dictionary: unique keys, unambiguous templates, no CJK in output, bilingual wiring |
| `verify_gameplay.py` | 60 | playbook loops, questline DAG, lorebook semantics |
| `verify_generic.py` | 87 | generic checks, game profile, context ledger, save library, brand |
| `verify_systems.py` | 161 | seven subsystem kinds, eight templates, counters, panel contract |
| `verify_injection.py` | 23 | injection signatures and `untrusted` marking |
| `verify_near_death.py` | 7 | near-death protection |
| `verify_audit_fix.py` | 22 | snapshot restore, concurrent RMW, finite JSON, input boundaries, read-only side effects |
| `verify_memory.py` | 7 | leak check and three bounded structures |
| `user_playtest.py` | 47 | player-perspective abuse cases and error readability |
| `smoke_ui.py` | 20 | real Edge render, cards and drawers, responsive, zero JS errors |
| `verify_tests.py` | — | AST-level rejection of tautological assertions |
| `verify_mutation.py` | 44 mutants | **break the code, require tests to go red**; survival must be 0% |

```bash
bash scripts/pre_push_gate.sh     # 28 steps; missing required dependencies fail the gate
```

Two end-to-end stress runs exist: `stress_freeplay.py 500` (CI) and `stress_freeplay.py 2000` (local),
both over real MCP stdio. Last 500-turn run: 0 unexpected errors, 0 invariant violations.

Coverage gate: core domain ≥70% (measured 86%, including the generic layer); `pyflakes` 0.
`bandit` is clean on the engine core; the repository-wide scan still reports findings confined to test scripts.

---

## Project layout

```
world-walker/                  # repo root IS the game_engine package
├── engine.py                  # CLI, 14 commands
├── mcp_server.py              # MCP server, 64 tools
├── state_schema.py            # state model / atomic write / transaction lock / generational archive / seed
├── panel.py                   # read-only view model + HTTP/SSE + action inbox
├── panel.html / .css / .js    # the stage: native trio, no build chain
├── viz_series.py              # long-run telemetry sidecar (<state>.viz.jsonl)
├── sessions.py                # save library: multi-run / snapshot / trash
├── rules/                     # 188 public rule functions
│   ├── checks.py              # d20/2d6/d100/4dF/dice pool, opposed rolls, success bands
│   ├── gamesystem.py          # game profile: custom attributes, resources, tracks, tags, sheet
│   ├── context.py             # context ledger: clues, promises, facts + budgeted packing
│   ├── combat.py economy.py social.py karma.py
│   ├── cognition.py narrative_engine.py progression.py
│   ├── world_dynamics.py world_evolution.py
│   ├── models.py              # 16 named closed-form models
│   └── social_extended.py cultural_evolution.py systems_feedback.py
├── settings/                  # 4 ready-to-play bundles
├── scripts/                   # 18 self-checks + mutation testing + screenshot/video/demo pipeline
├── docs/demo/                 # real demo saves (the data behind the screenshots)
├── docs/screenshots/          # asserted renders
└── assets/echarts.min.js      # offline chart library (Apache-2.0, shipped with the package)
```

---

## FAQ

**Does it need network access?**
No. Core and panel have zero third-party dependencies and the chart library ships locally.
Only MCP mode installs the `mcp` SDK.

**Does it need an OpenAI / Claude API key?**
No. It never calls a model. Your agent supplies the model; the engine only decides how the world changes.

**Can I use it commercially?**
MIT. Every name, faction and place in the demo bundles is original and free to replace.

**Why no pytest?**
Assertions must survive "break the code, watch the test go red". `verify_tests.py` statically rejects
tautological assertions and `verify_mutation.py` injects 44 real defects, requiring every one to be killed.
Both run in the gate.

**Why can't the panel submit actions directly?**
It can queue them, but not settle them. The panel writes to `<state>.inbox.jsonl`; the agent drains it
with `pending_actions` and settles through the engine. That keeps a single writer, which is what makes
determinism and snapshot rollback trustworthy.

**Is power-loss safety guaranteed?**
No, and we do not claim it. Saves use atomic replacement with `.bak` fallback and a re-entrant
Windows/POSIX lock, and crash tests cover several interruption windows. If `<state>.archive-pending`
or `.ww-session-transaction-pending` exists, protected reads and writes are refused and there is
no automatic recovery — stop writing, preserve the evidence, and review it manually. Restoring the
caller's in-memory state after a failed save is not an archive rollback.
See [the archive recovery guide](docs/ARCHIVE_RECOVERY.md).

---

## Regenerate the demo assets

```bash
python scripts/make_demo.py          # 4 real demo saves → docs/demo/
python scripts/shots.py              # assert, screenshot, record → docs/screenshots/
python scripts/verify_settings.py    # validate all four bundles
```

---

## License

MIT. Charts by [ECharts](https://echarts.apache.org/) 5.5.1 (Apache-2.0).
Tavern-ecosystem compatibility follows the publicly documented character-card and world-info
conventions; no names or settings from existing works are reused.
