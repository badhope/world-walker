"""Deterministic map generation from a template blueprint.

The blueprint fixes what must not drift: the start node, the core nodes, which
core nodes are adjacent, and the danger tiers. It leaves names, descriptions,
which optional wild nodes appear, and exact travel time to the RNG. That is the
line the project needs: a new game may look different, but 青石村 -> 后山灵泉 ->
落霞山 always exists and always sits on the same side of the map.

No model call is made here. If a host wants an LLM to write richer prose, it can
call this function first and then use `canon_commit` / `state` edits to enrich
the generated places; the deterministic result is the fallback and the contract.
"""

from __future__ import annotations

import random


def _num_pair(value, rng):
    """Return one integer from an int, [min,max], or missing value."""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        lo, hi = int(value[0]), int(value[1])
        if hi < lo:
            lo, hi = hi, lo
        return rng.randint(lo, hi)
    return 0


def _pick_name(node, used, rng):
    fixed = str(node.get("name") or "").strip()
    if fixed:
        return fixed
    pool = [str(n).strip() for n in (node.get("names") or []) if str(n).strip()]
    if not pool:
        pool = [str(node.get("id") or "无名地")]
    available = [n for n in pool if n not in used]
    if not available:
        available = pool
    return rng.choice(available)


def generate(blueprint: dict, seed: int = 0) -> dict:
    """Build `places` + `map` for one game.

    Args:
        blueprint: template-level map contract.
        seed: deterministic seed (the game's rng_seed is passed in by settings_loader).

    Returns:
        {"places": {name: {"desc": str, "market": str}},
         "map": {"start": str, "nodes": [...], "edges": [...]},
         "start": str}
    """
    if not isinstance(blueprint, dict) or not blueprint.get("core_nodes"):
        return {"places": {}, "map": {"start": "", "nodes": [], "edges": []}, "start": ""}

    rng = random.Random(int(seed or 0))
    core = [n for n in blueprint.get("core_nodes") or [] if isinstance(n, dict)]
    optional = [n for n in blueprint.get("random_nodes") or [] if isinstance(n, dict)]
    random_count = int(blueprint.get("random_count", 2) or 0)
    random_count = max(0, min(random_count, len(optional)))
    selected = list(optional)
    if random_count < len(optional):
        # sample indexes, not dicts, keeps the selection deterministic and avoids
        # comparing unhashable dicts.
        indexes = sorted(rng.sample(range(len(optional)), random_count))
        selected = [optional[i] for i in indexes]

    chosen = []
    used_names = set()
    for node in core + selected:
        name = _pick_name(node, used_names, rng)
        # 固定节点如果重名，仍然保留第一个；随机节点的 name_pool 已去重。
        while name in used_names:
            name = "%s·%s" % (name, rng.randint(2, 9))
        used_names.add(name)
        desc = str(node.get("desc") or "").strip()
        if not desc:
            descs = [str(d).strip() for d in (node.get("descs") or []) if str(d).strip()]
            template = rng.choice(descs) if descs else "%s：雾气里看不清边界。" % name
            desc = template.format(name=name)
        chosen.append({
            "id": str(node.get("id") or name),
            "name": name,
            "role": str(node.get("role") or "wild"),
            "danger": int(node.get("danger", 0) or 0),
            "desc": desc,
            "market": str(node.get("market") or ""),
        })

    by_id = {n["id"]: n for n in chosen}
    start_id = str(blueprint.get("start") or "")
    start_name = by_id.get(start_id, {}).get("name") or chosen[0]["name"]

    places = {}
    for node in chosen:
        places[node["name"]] = {"desc": node["desc"], "market": node["market"]}

    edges = []
    seen_pairs = set()

    def add_edge(raw, default_label="路"):
        a = str(raw.get("a") or "")
        b = str(raw.get("b") or "")
        if a not in by_id or b not in by_id or a == b:
            return
        key = tuple(sorted((a, b)))
        if key in seen_pairs:
            return
        seen_pairs.add(key)
        edges.append({
            "a": by_id[a]["name"], "b": by_id[b]["name"],
            "label": str(raw.get("label") or default_label),
            "minutes": _num_pair(raw.get("minutes"), rng),
        })

    for edge in (blueprint.get("edges") or []):
        if isinstance(edge, dict):
            add_edge(edge)
    for link in (blueprint.get("random_links") or []):
        if not isinstance(link, dict):
            continue
        node_id = str(link.get("id") or "")
        if node_id not in by_id:
            continue
        for target in (link.get("links") or []):
            add_edge({"a": node_id, "b": str(target), "minutes": link.get("minutes", [10, 30]),
                      "label": link.get("label") or "野径"})

    # 任何被抽中的随机节点都必须至少有一条边，否则它只是地图上的孤岛。
    connected = {e["a"] for e in edges} | {e["b"] for e in edges}
    for node in chosen:
        if node["name"] not in connected:
            target = by_id.get(start_id) or chosen[0]
            add_edge({"a": node["id"], "b": target["id"], "minutes": [15, 40], "label": "野径"})

    return {
        "places": places,
        "map": {"start": start_name, "nodes": chosen, "edges": edges},
        "start": start_name,
    }
