# World Walker

**v1.20.1** · English · [简体中文](README.zh-CN.md) · [Android](docs/ANDROID.md) · [Architecture](ARCHITECTURE.md) · [MCP mode](docs/MCP_PLAY.md) · [Share formats](docs/SHARE_FORMATS.md) · [Changelog](CHANGELOG.md)

<p align="center">
  <a href="https://github.com/Morningstar202604/world-walker/releases/tag/v1.20.1">
    <img src="docs/assets/brand-hero-en.png" alt="World Walker — You speak. The world answers. A single-player AI tabletop RPG engine." width="100%">
  </a>
</p>

<p align="center">
  <strong>You speak. The world answers.</strong><br>
  <sub>A single-player AI tabletop RPG engine. The model writes the scene; the engine owns the truth.</sub>
</p>

`221 rule functions` · `74 MCP tools` · `28 player tools` · `7 worlds` · `9 templates` · `25 self-check suites` · `0 runtime dependencies`

Most AI RPGs are a chat window with dice bolted on. World Walker is a table that remembers: prices, wounds, debts, clocks, who saw what, and what your last choice cost. Any OpenAI-compatible `/chat/completions` endpoint can be the GM. The engine keeps the books.

No host app. No provider lock-in. No second save format. The model writes the scene; the engine owns the truth.

## Three things the engine refuses to fake

- **Your character is yours.** The GM describes the world and its people; it never decides what you do next.
- **NPCs only know what they saw.** A character cannot quote a fact that never entered their witnessed memory.
- **A turn leaves a mark.** Every reply carries a scene card and a bounded state diff; a turn with no visible consequence is a bug, not atmosphere.

A campaign is built at the table, not pre-written. Session Zero asks genre, play style, role, tone, mode (power / balanced / hardcore) and boundaries. Then each turn runs `scene card → your action → world reaction → state change → next hook`.

## One turn, five moves

![One turn, five moves](docs/assets/readme-loop-en.png)

A campaign is not a longer prompt. It is a causal chain you can inspect: the scene card fixes the pressure, the engine settles the numbers, the GM writes the world's answer, and the state file keeps the consequence.

## Three screens, one save

![World Walker on Android — lobby, table and character rail](docs/assets/readme-gallery-en.png)

The lobby continues an existing save or starts a new world. The table is one column of prose and one quiet rail. The rail holds character, clocks, ties and world facts; the sheet folds into a bottom drawer on a phone. There is no second state: the replay, the Markdown report and the Android APK all read the same file.

![Replay](docs/assets/replay.png)

The replay is the same save, read back: prologue, your lines, narrator prose, and the state chip for every settled turn. No parallel log format to keep in sync.

## Start in thirty seconds

```bash
pip install -e ".[mcp]"      # core uses only the standard library; mcp is optional
wg init my-game.json
wg play --state my-game.json
```

`wg play` opens the local page at `http://127.0.0.1:8899/`. Continue a save or start a new world. The player view is one screen: narrative in the centre, a narrow character and quest rail on the right, one input at the bottom.

`wg` is the entry point: `init`, `setup`, `play`, `serve`, `mcp`, `run`, `doctor`, `version`. `wg --help` lists the rest.

`wg setup` writes the five built-in narrative skill packs, a director note and two table rules to `~/.world-walker/harness.json` with `0600` permissions. An existing config is kept; use `--force` to rewrite it.

## Android: put the table in your pocket

**[Download the v1.20.1 APK](https://github.com/Morningstar202604/world-walker/releases/tag/v1.20.1)** · **[Install, ABI and build notes](docs/ANDROID.md)**

A signed APK: about 25 MB for `arm64-v8a`, 26 MB for `x86_64`, 39 MB universal. This is not a remote web page. The APK carries the same Python engine; Chaquopy starts a loopback panel inside the app process, and the WebView only talks to `127.0.0.1`. Saves, model keys and world packs stay on the phone.

Android 7's stock WebView is supported as of v1.20.1 — the compatibility build removes the `async/await` cliff that left an older phone showing a static lobby with dead buttons. The phone shell folds the rail into a panel sheet; back closes the sheet, then overlays, then returns to the lobby. Downloads land in `Downloads/World Walker`, and JSON imports use the system file picker.

## Knowledge library

The lobby has three one-click flagship starts — fog-cabin survival, the ferry crossing in *Folded Sword*, and the White Whale clinic in *Neon Abyss* — plus island survival in the Ten Thousand Islands Sea. No rules reading first; the opening card and its first-reaction buttons are playable immediately. Every world can be started in one of three modes: **Power** (more starting supplies and room to recover; all gains are countable goods or stamina that can be used up or taken), **Balanced** (no favour, no sabotage), and **Hardcore** (scarce resources, faster clocks, permadeath). The fog-cabin Power kit is a second-hand hardware box: 4 boards, 16 nails, 1 hinge, a 10 m rope rated 40 kg, a mechanical thermometer/hygrometer, a windproof lighter rated for about 80 ignitions, a 500 g claw hammer and a 28 cm billhook. The character also has hauling strength from working in the family shop: STR 12 against a 10 baseline, enough to shoulder 60 kg for 20 m. Every piece can be consumed, broken or taken; the billhook dulls after 20 cuts; Hardcore has no kit and no respawn. The prefab fixes the world, play loop, base difficulty, tone and narrative style; name, role, boundaries and what happens next still belong to the player.

Every narrator turn now carries a bounded state diff under the prose: HP, items, clocks, weapon durability, location, flags and relationship movement. The menu also offers a chronological battle report, a Markdown export, a world-pack round trip (export and import), and a `chara_card_v2` character-card export/import path. These are reads over the same state file, not a second save format.

“Design archives” holds the raft, prefab-authoring and release-discipline notes. The data lives in `library/playbooks/*.json` and `library/archives/*.md` and ships with the package.

### Three modes, one rules core

`load_setting(path=..., mode="power")` accepts `power`, `balanced` or `hardcore`. The mode changes starting HP and supplies, market temperature, initial clock pressure and the GM's narrative rule; the world's own `modes` block names the edge. Power is extra countable stock, a modest physical edge where a world supplies one, and softer market/clock pressure; never a mystery sense. The same three presets work for every setting bundle and template.

## Use your own model

The model layer only assumes an OpenAI-compatible endpoint:

```json
{ "base_url": "https://your-gateway/v1", "api_key": "sk-...", "model": "any-model" }
```

Set it in the model settings page, or use `WW_MODEL_BASE_URL`, `WW_MODEL_API_KEY` and `WW_MODEL_NAME`. The config lives at `~/.world-walker/model.json` with `0600` permissions.

## Tune the GM

The “Connect & tune → Narrative tuning” panel keeps four layers separate instead of folding taste, prompt packs and hard rules into one switch:

- **Prompt:** director notes and table rules are appended to the GM system prompt. They change the telling, not POLICY, CANON or numeric outcomes.
- **Narrative skills:** prompt packs under `narrative_skills/*.md`, each with a title and summary, injected only when enabled. These are not character skills.
- **Engine rules:** the current save's `rulebook`, ordered by `order`, limited to whitelisted effects. Validate and save from the panel; trigger counts are persisted. Rules can run at turn start or after every tool result.
- **Turn hooks:** `before_turn.py`, `after_tool.py` and `after_turn.py` under `~/.world-walker/hooks`. Off by default. They run with your own permissions — treat them as Python you wrote yourself.

Tuning config lives at `~/.world-walker/harness.json` with `0600` permissions. Prompts, skills, hooks and rules for an external agent still belong to its host; World Walker only supplies MCP tools and starting prompts.

## Connect an agent over MCP

```json
{ "mcpServers": { "world-walker": { "command": "world-walker-mcp" } } }
```

Any MCP client works. For remote agents, use HTTP instead of stdio:

```bash
wg mcp --http --port 8620
```

Then point the client at `http://127.0.0.1:8620/mcp`. A complete game can start with one setting bundle and one trade:

```
load_setting(path="settings/玄枢界.setting.json")
trade(location="临川城", item="ningyuan_dan", direction="buy", quantity=1)
```

The host calls tools only when a number is needed. Prose stays in the conversation.

## What the engine owns

- **Checks and combat:** d20, 2d6, d100, 4dF, dice pools, opposed rolls, damage and death rules.
- **Economy and people:** prices, inventory, relationships, reputation, debts and faction shifts.
- **World movement:** clocks, rumors, roaming NPCs, clues, quest stages and long-run consequences.
- **Replay:** one transactional writer, a command log with state fingerprints, and a save you can inspect.
- **Context boundaries:** NPC knowledge, canon facts, world book triggers and a scene card before every reply.

The player surface exposes 28 tools. The 74-tool MCP surface remains for advanced hosts; `play(intent=..., arguments=...)` is a compact one-tool route over the same 28 player intents when a host does not want to load the full registry. Both routes share the same rules, state file and writer.

## Quality

Verification is executable, not decorative. `scripts/verify_*.py`, behaviour regressions and mutation tests must fail when the code is wrong. The main gate runs 25 self-check suites, with coverage for the core domain and a zero-survivor mutation pass.

```bash
python3 scripts/verify_docs.py
python3 scripts/verify_player_shell.py
python3 scripts/verify_mcp_stdio.py
```

## Saves and failure

Saves use atomic replacement with a `.bak` fallback and a re-entrant Windows/POSIX lock. Crash tests cover several interruption windows.

If `<state>.archive-pending` or `.ww-session-transaction-pending` exists, protected reads and writes are refused. There is **no automatic recovery**: stop writing, preserve the evidence and review it manually. Restoring the caller's in-memory state after a failed save is **not an archive rollback**. See [the archive recovery guide](docs/ARCHIVE_RECOVERY.md).

## Scope

Built for single-player AI GM play, setting bundles, local saves and MCP hosts. Deliberately not multiplayer, cloud accounts, a plugin marketplace or pre-written campaigns sold as content.

## Project layout

```
world-walker/                  # repo root is the game_engine package
├── panel.py                   # player HTTP/SSE server and game APIs
├── dialog_runtime.py          # GM prompt, tool loop, turn finish and audit
├── narrative_rules.py         # Session Zero, scene cards, turn audit
├── rules/                     # deterministic settlement
├── settings/                  # seven ready-to-play worlds
├── saves/                     # local save library
└── scripts/                   # verification and build tools
```

## A table worth keeping

If this is the kind of AI RPG you wanted to exist, [star the repo](https://github.com/Morningstar202604/world-walker). It helps the next player find a table that remembers.

## License

MIT. Demo names, factions and places are original; no setting material from existing works is reused.
