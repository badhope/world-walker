# World Walker

[中文](README.md) | **English**

---

*World Walker* is an AI-driven text interaction game engine. World evolution is driven by 15 academic disciplines and 85+ formulas — every player decision is processed through mathematical models, and the world emerges its own story naturally, without pre-written branches.

Keywords: `AI text adventure` `interactive fiction engine` `emergent narrative` `cognitive architecture` `game AI` `world simulation` `behavioral economics` `evolutionary dynamics` `systems thinking`

---

## Screenshots

The live stage (opened by `open_panel`) — read-only, offline-capable; world skins, long-run curves and
event feedback all live on this one page. All shots below are **real renders** (2000-turn demo save, not mockups):

| Xuanshu (default skin) | Ink skin | Neon skin |
|---|---|---|
| ![Xuanshu](docs/screenshots/stage-xuanshu.png) | ![Ink](docs/screenshots/stage-ink.png) | ![Neon](docs/screenshots/stage-neon.png) |

| 320px narrow | Help & glossary | First-visit guide |
|---|---|---|
| ![Narrow](docs/screenshots/stage-320.png) | ![Help](docs/screenshots/help.png) | ![First visit](docs/screenshots/first-visit.png) |

> Captured from the `scripts/stress_freeplay.py 2000` free-player save (600 telemetry samples); every shot is
> taken only after asserting brand / skin / chart rendering / timeline. Provenance: [`docs/screenshots/README.md`](docs/screenshots/README.md).

---

## Quick Start

### Option A: MCP (recommended — for any AI agent)

```bash
pip install -e ".[mcp]"
```

Add to your MCP client (Claude Code / Codex / Cursor / any MCP-capable agent):

```json
{ "mcpServers": { "world-walker": { "command": "world-walker-mcp" } } }
```

Hand your setting bible to the agent and play. Clients with MCP prompt support can start in one step:
call `new_game` (pass the setting) and it produces the full opening brief. The loop is:
`world_init` (build the world from the setting; typed args with field docs; takes a seed) →
each player action is settled by `combat` / `trade` / `social` / `karma` →
`narration_context` returns the triggered lore, the on-scene cast's card prose and a chronicle →
prose → `tick` closes the turn → every 3-5 turns call `narrative` + `status`. The agent only turns
the engine's JSON into prose — it must never invent numbers.

- Ecosystem compatible (no reinventing): reads SillyTavern-style **character cards** (`.png`-embedded
  or `.json`, V1/V2/V3) and **world info** lorebooks (world-info / card `character_book`, with
  selective/constant/disable semantics); `character_card_read` → `add_character` → `import_lorebook`
- **Long-game support (built for a million turns)**: three memory layers — `write_summary` chapter
  summaries (host writes one every 20-50 turns), milestones (breakthroughs / kills / first arrivals,
  auto-recorded), and automatic event archiving (state keeps the last N events, default 200; older ones
  spill to `<state>.log.jsonl`, searchable via `recall`). `recap(budget_chars)` assembles summary +
  milestones + recent events under a character budget.
- **Growth loop**: `advance` — the engine rolls breakthroughs from insight / mind / karma / HP and applies
  the numeric consequences (success raises caps and attrs, failure backlashes HP and leaves a mind scar).
- **Model layer**: `model_list` / `model(name, params)` evaluate 16 named closed-form models directly
  (Lerner pricing / OU price reversion, Cobb-Douglas, logistic & Lotka-Volterra populations, SIR + R0,
  Poisson survival, thermal relaxation, bounded-confidence opinion dynamics, …). Market prices mean-revert
  via the OU model every tick — hosts derive effects from formulas instead of ad-hoc reasoning.
- Live stage: `open_panel` serves a **read-only stage** (narrative panel + HP/MP/flow/world phase + event
  timeline + graded dialogs/toasts + drawers for codex / market / milestones + inventory & relations;
  auto-refreshes via SSE with polling fallback, and shows a readable banner + retry when the save is
  missing). Standalone: `python panel.py --state ww_state.json`
- **Long-run telemetry visuals**: three offline charts (vitals/gold over turns; karma & affinity;
  price index vs baseline) + an event spectrum + a relationship network + a locations map +
  a cultivation stage track + danger/opportunity badges. Samples accumulate per turn into a sidecar
  (`<state>.viz.jsonl`, never touching the save file) so hundreds of turns stay readable at a glance.
- **World skins & branding**: the stage adapts to the setting — xuanshu (ink & gold) / ink / neon / neutral,
  including chart palettes; a setting bundle or `world_init` can pass
  `ui: {skin, accent, motif, brand, tagline}` so a new world ships its own look **and its own name**
  (unknown ids fall back to neutral; spec in `BRAND.md`).
- **Onboarding help**: a top-bar Help (`?`) dialog with a plain-language glossary (flow, panarchy phase,
  karma, price index, …), how to read each chart, keyboard controls, data & privacy (real state/sidecar
  paths) and skin notes; first-time visitors get a one-shot guidance strip.
- Convenience: thousands separators for large numbers, low-HP / karma badges, and automatic
  collapsing of long-run cast & relation lists.
- Travel & codex: `travel` is the only tool that moves the player; first arrival enters the codex
- Deterministic undo: `snapshot` / `restore`
- Near-death protection: the player never truly dies — hitting zero HP becomes "severe injury retreat" with 1 HP floor, costing 30% of gold and +1 mind scar (panel shows the count); NPC deaths are unaffected
- End-to-end self-check: `python scripts/verify_mcp_stdio.py` (53 assertions, including ecosystem / codex / panel / settings / long game / model layer / determinism)
- Panel contract self-check: `python scripts/verify_panel.py` (53 assertions: view-model contract / legacy saves / static whitelist / missing-save banner / brand / help / series sampling)
- CLI channel self-check: `python scripts/verify_cli.py` (19 assertions: read-only commands never rewrite the save / all five write paths persist with bounded fields / same seed + same action reproduces)
- Near-death self-check: `python scripts/verify_near_death.py` (7 assertions: 1-HP floor / costs persisted / NPC death semantics unchanged)
- Test-integrity audit: `python scripts/verify_tests.py` (statically audits every self-check assertion and rejects tautologies / always-false / weak checks — no more "all green but nothing tested")
- User-perspective playtest: `python scripts/user_playtest.py` (44 checks a real player would raise — money-minting exploits, boundary inputs, readable refusals)
- Field-tested: opencode (GLM-5.2) builds a world from the setting and settles three actions in a row;
  its narration matches the engine's state file item by item
- Reproducible: pass `seed` at world_init; every settlement seeds its RNG from the state's
  `rng_seed` + `rng_counter`, both persisted with the state.

### Option B: CLI (manual settlement)

```bash
python init_game.py                                      # writes the sample world game_state.json
python engine.py world_state --state game_state.json      # `python` on Windows, `python3` on macOS/Linux
```

14 commands at a glance (using `game_state.json`; note `--item` takes the market item_key, not the display name):

```bash
python engine.py combat    --state game_state.json --attacker player --defender goblin --action_type heavy
python engine.py trade     --state game_state.json --location bamboo_tea_booth --item an_zhen_san --quantity 3 --direction buy --entity player
python engine.py social    --state game_state.json --actor player --target old_chen --event help
python engine.py karma     --state game_state.json --actor player --karma_type murder_innocent
python engine.py tick      --state game_state.json
python engine.py flow      --state game_state.json
python engine.py identity  --state game_state.json
python engine.py narrative --state game_state.json
python engine.py world_state  --state game_state.json
python engine.py panarchy  --state game_state.json
python engine.py moral_update   --state game_state.json
python engine.py cognition   --state game_state.json --entity player
python engine.py merit     --state game_state.json --aid 0.8 --sincerity 0.9
python engine.py info_weight --state game_state.json --probability 0.05
```

---

## Project Structure

```
game_engine/                      # the repo root IS the game_engine package (any folder name works)
├── engine.py                     # CLI entry (14 commands)
├── mcp_server.py                 # MCP server (31 tools; only extra dep is mcp>=2)
├── state_schema.py               # State schema + helpers
├── init_game.py                  # Writes the sample world (青云界)
├── pyproject.toml                # pip install -e ".[mcp]"; commands world-walker / world-walker-mcp
├── panel.py / panel.html / panel.css / panel.js   # read-only live stage (view model + HTTP/SSE + web UI)
├── viz_series.py                 # long-run telemetry sidecar (<state>.viz.jsonl; chart data, never touches the save)
├── assets/echarts.min.js         # offline chart library (Apache-2.0, shipped with the package, no CDN)
├── BRAND.md                      # brand spec (name / tagline / palette / configurability; single source)
├── ARCHITECTURE.md               # architecture doc (single source of truth: view-model contract / invariants / ADRs)
├── scripts/verify_mcp_stdio.py   # MCP end-to-end self-check (53 assertions, including ecosystem compat / codex / panel / model layer / determinism)
├── scripts/verify_panel.py       # panel contract self-check (53 assertions: view model / legacy saves / static whitelist / missing-save banner / brand / help / series sampling)
├── scripts/verify_cli.py         # CLI channel self-check (19 assertions: read-only invariants / write persistence / determinism)
├── scripts/verify_tests.py       # test-integrity audit (AST-level: rejects tautologies / always-false / weak checks)
├── scripts/verify_near_death.py  # near-death self-check (HP floor / persisted costs / NPC death unchanged)
├── scripts/user_playtest.py      # user-perspective playtest (44 "would a player complain?" checks: exploits / edges / error readability)
├── scripts/stress_freeplay.py    # free-player stress test (default 2000 turns, real MCP stdio channel)
├── docs/screenshots/             # README preview shots (real renders + assertions; provenance in that folder's README)
├── demo_state.json               # Demo game state
├── GAME_MASTER_PROTOCOL.md       # AI Agent call protocol
└── rules/                        # 85+ academic formulas as Python
    ├── combat.py                 #    combat / hit / crit
    ├── economy.py                #    economy / supply / demand
    ├── social.py                 #    social 2D relations
    ├── karma.py                  #    causal debt (karma)
    ├── cognition.py              #    cognitive science
    ├── world_dynamics.py         #    world evolution (chaos/Panarchy/PID)
    ├── social_extended.py        #    extended social (Haidt/Milgram/Bandura)
    ├── cultural_evolution.py     #    cultural evolution (DIT/memes/ratchet)
    ├── systems_feedback.py       #    systems feedback (Meadows 12/NAT)
    └── narrative_engine.py       #    emergent narrative (Bartle/events)
```

---

## Academic Coverage

85+ formulas across 15 disciplines:

| Discipline | Core Theories | File | Lines |
|------------|--------------|------|-------|
| Cognitive Science | Kahneman dual-system, Prospect Theory, ACT-R memory, Flow | cognition.py | 235 |
| Chaos / Complex Systems | Lorenz attractor, Lyapunov exponent, Logistic map, Panarchy, PID | world_dynamics.py | 275 |
| Moral Psychology | Haidt 6-dim, Tajfel, Bandura, Milgram, Cialdini | social_extended.py | 202 |
| Evolutionary Dynamics | Price equation, Hamilton, ESS, Red Queen | world_dynamics.py | — |
| Cultural Evolution | DIT, memetics, cultural ratchet, fidelity decay | cultural_evolution.py | 92 |
| Systems Theory | Donella Meadows 12 leverage points, NAT, ANT | systems_feedback.py | 141 |
| Narrative Studies | Emergent narrative, Bartle, narrative transportation | narrative_engine.py | 141 |
| Information Theory | Shannon entropy, KL divergence, event information | world_dynamics.py | — |

---

## Design Principles

1. **Worldview-agnostic** — same math, different narrative vocabulary
2. **Emergence over branching** — the world produces its own story from mechanisms
3. **Agent → Engine → Prose** — engine returns JSON, AI Agent renders it as prose
4. **Fully responsive** — every player action gets a mathematically grounded result

---

## Collaboration

- **For players**: tell the Agent what you want → Agent calls engine → engine returns JSON → Agent narrates what happened
- **For AI Agents**: see [`GAME_MASTER_PROTOCOL.md`](GAME_MASTER_PROTOCOL.md) for the full call protocol, parameters, and response schemas

---

## License

MIT
