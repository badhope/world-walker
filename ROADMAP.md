# Roadmap

World Walker is maintained as a local-first engine, not a hosted platform. The work below is ordered by what makes a campaign easier to run and easier to audit.

## Now

- Keep the player page and MCP mode on one engine, one state file and one transactional writer.
- Tighten the turn contract: scene card, player agency, visible consequence, next hook.
- Keep the setting bundles playable without code changes; test each bundle after engine changes.
- Keep the save format recoverable, inspectable and replayable.

## Next

- More original setting bundles, each with its own economy, progression and quest structure.
- Better long-run context selection without adding a vector database or a hosted service.
- More browser and terminal playtests that exercise failure, death and recovery paths.
- Clearer diagnostics for save archives and interrupted writes.

## Not planned

Multiplayer, cloud accounts, a plugin marketplace, paid pre-written campaigns, image generation, or a second front-end that competes with the player page.

## How to propose work

Open an issue with the smallest reproducible case. For a setting bundle, include the JSON and the first three scenes. For an engine change, include the test that should fail before the fix.
