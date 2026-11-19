"""Loop detection: notice when the game is going in circles.

Why this exists
--------------
A long AI-run game can stall without failing: the player walks between the same
two rooms, the same market prices regenerate, the same events re-log. Nothing is
"broken", so no error surfaces, but nothing progresses either. ZorkGPT solved
this with a state hash; we take the detector and leave the LLM-driven generation
behind, because our state is already deterministic and therefore comparable.

Design notes
------------
* The hash covers **play-relevant state only**: location, HP/MP, inventory,
  world flags, quest stages, market prices, unsettled karma. It deliberately
  excludes `tick`, timestamps and the action sequence — including them would make
  every hash unique and the detector useless.
* Detection is advisory, never restrictive. `tick` reports `loop_suspected` and
  suggests a change of scene; it never blocks a tool, because a legitimately
  repetitive stretch (grinding, resting) is a valid way to play.
* Bounded: the ring buffer of recent hashes is capped, so a 10 000-turn save does
  not grow a 10 000-entry list in every state file.
* Edge pruning applies to **suggestions only**: a route that failed three times
  stops being recommended, but `travel` still allows it.
"""

from __future__ import annotations

import hashlib
import json

HASH_WINDOW = 20      # how many recent hashes to remember
LOOP_THRESHOLD = 3    # same hash this many times triggers suspicion
EDGE_FAIL_LIMIT = 3   # failed traversals before an edge is hidden from suggestions


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), default=str)


def state_signature(state: dict) -> str:
    """Hash of the parts of the state a player can perceive and act on."""
    player = (state.get('entities') or {}).get('player') or {}
    summary = {
        'location': player.get('location', ''),
        'hp': player.get('hp'),
        'mp': player.get('mp'),
        'gold': player.get('gold'),
        'level': player.get('level', ''),
        # 数量也要进哈希：用了 1 颗丹药但仍在原地，是"有进展"而不是循环。
        'items': sorted([str(k), int(v or 0)]
                        for k, v in (player.get('items') or {}).items()),
        'flags': sorted(str(f) for f in (state.get('world_flags') or [])),
        'quests': _quest_progress(state),
        'prices': _market_prices(state),
        'karma': round(_unsettled_karma(state), 3),
    }
    return hashlib.sha256(_canonical(summary).encode('utf-8')).hexdigest()[:16]


def _quest_progress(state: dict) -> list:
    """事业线的**运行时**进度（state["quests"]），不是设定里的 questlines 定义。

    旧实现读 `questlines` 并取 `q["stage"]["id"]`：定义里没有 stage，于是任务
    推进永远不会改变签名——玩家明明推进了一幕，循环检测仍判"同一状态"。
    旧存档/夹具可能把 stage 直接放在 questlines 上，作为回退保留。
    """
    runtime = state.get('quests')
    if isinstance(runtime, dict) and runtime:
        return [[str(qid), str((row or {}).get('status') or ''),
                 str((row or {}).get('stage') or '')]
                for qid, row in sorted(runtime.items()) if isinstance(row, dict)]
    rows = []
    for quest in (state.get('questlines') or []):
        if not isinstance(quest, dict):
            continue
        stage = quest.get('stage')
        stage_id = (stage.get('id') if isinstance(stage, dict) else stage) or ''
        rows.append([str(quest.get('id') or ''), '', str(stage_id)])
    return rows


def _market_prices(state: dict) -> list:
    """各地行情按「相对基准价的档位」计入签名（0.1 = 10% 一档）。

    两个结构都要认：引擎现行 `{地点: {商品键: {price, base_price}}}`，以及
    旧存档/夹具的 `{地点: {"items": {...}}}` 包裹层。
    为什么用档位而不是精确价格：`tick_market` 每回合都有 ±4% 的确定性抖动，
    精确价格会让每个回合的哈希都不同，循环检测永远不会触发（与"不得把 tick
    放进哈希"是同一条理由）。
    """
    rows = []
    market = state.get('market') or {}
    if not isinstance(market, dict):
        return rows
    for location in sorted(market.keys()):
        bucket = market.get(location) or {}
        if not isinstance(bucket, dict):
            continue
        items = bucket.get('items') if isinstance(bucket.get('items'), dict) else bucket
        for key in sorted(items.keys()):
            entry = items.get(key)
            if not isinstance(entry, dict):
                continue
            price = entry.get('price')
            base = entry.get('base_price') or price
            if not isinstance(price, (int, float)):
                continue
            if isinstance(base, (int, float)) and base:
                band = round(float(price) / float(base), 1)
            else:
                band = round(float(price), 1)
            rows.append([str(location), str(key), band])
    return rows


def _unsettled_karma(state: dict) -> float:
    ledger = state.get('karma_ledger')
    if not isinstance(ledger, list):
        ledger = state.get('karma') or []   # 旧存档回退
    total = 0.0
    for entry in ledger:
        if isinstance(entry, dict) and not entry.get('settled'):
            try:
                total += float(entry.get('amount') or 0)
            except (TypeError, ValueError):
                continue
    return total


def observe(state: dict) -> dict:
    """Record the current signature and report whether a loop is suspected."""
    signature = state_signature(state)
    trail = state.get('_state_hashes')
    if not isinstance(trail, list):
        trail = []
    trail.append(signature)
    if len(trail) > HASH_WINDOW:
        trail = trail[-HASH_WINDOW:]
    state['_state_hashes'] = trail

    seen = trail.count(signature)
    suspected = seen >= LOOP_THRESHOLD
    result = {
        'signature': signature,
        'seen': seen,
        'window': len(trail),
        'loop_suspected': suspected,
    }
    if suspected:
        result['hint'] = ('同一状态已出现 %d 次：位置、资源与市场都没变。'
                          '建议换场景、推进时间或触发一个未尝试的交互。' % seen)
    return result


def record_edge(state: dict, origin: str, destination: str, ok: bool) -> None:
    """Track travel outcomes so suggestions can avoid dead ends."""
    if not origin or not destination:
        return
    edges = state.get('_travel_edges')
    if not isinstance(edges, dict):
        edges = {}
    key = '%s->%s' % (origin, destination)
    entry = edges.get(key)
    if not isinstance(entry, dict):
        entry = {'ok': 0, 'fail': 0}
    if ok:
        entry['ok'] = int(entry.get('ok') or 0) + 1
    else:
        entry['fail'] = int(entry.get('fail') or 0) + 1
    edges[key] = entry
    # Keep the map bounded: on a long game a player can visit hundreds of pairs.
    if len(edges) > 200:
        ordered = sorted(edges.items(), key=lambda kv: -(kv[1].get('ok', 0) + kv[1].get('fail', 0)))
        edges = dict(ordered[:200])
    state['_travel_edges'] = edges


def pruned_edges(state: dict) -> list:
    """Edges hidden from suggestions (never forbidden)."""
    edges = state.get('_travel_edges')
    if not isinstance(edges, dict):
        return []
    return sorted(key for key, value in edges.items()
                  if isinstance(value, dict) and int(value.get('fail') or 0) >= EDGE_FAIL_LIMIT
                  and int(value.get('ok') or 0) == 0)


def summary(state: dict) -> dict:
    """Read-only view for `status` and the panel."""
    trail = state.get('_state_hashes')
    trail = trail if isinstance(trail, list) else []
    latest = trail[-1] if trail else None
    return {
        'window': len(trail),
        'repeats': trail.count(latest) if latest else 0,
        'loop_suspected': bool(latest) and trail.count(latest) >= LOOP_THRESHOLD,
        'pruned_edges': pruned_edges(state),
    }
