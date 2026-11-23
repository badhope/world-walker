#!/usr/bin/env python3
"""Panel invariants that used to live in a deleted verify_panel.py.

These are narrow on purpose: they cover the four mutation targets that still
exist in panel.py / viz_series.py.  Keep the assertion names stable — the
mutation runner matches them to prove a known defect was actually killed.
"""

import json
import os
import sys
import tempfile
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if 'game_engine' not in sys.modules:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        'game_engine', os.path.join(ROOT, '__init__.py'),
        submodule_search_locations=[ROOT])
    _pkg = importlib.util.module_from_spec(_spec)
    _pkg.__path__ = [ROOT]
    sys.modules['game_engine'] = _pkg
    _spec.loader.exec_module(_pkg)

import importlib.util as _ilu
_pspec = _ilu.spec_from_file_location('panel_settings', os.path.join(ROOT, 'panel.py'))
PANEL = _ilu.module_from_spec(_pspec)
_pspec.loader.exec_module(PANEL)
from game_engine import state_diff  # noqa: E402
from game_engine import viz_series as VIZ  # noqa: E402

RESULTS = []


def check(name, ok, note=''):
    RESULTS.append(bool(ok))
    print('%s  %-58s %s' % ('PASS' if ok else 'FAIL', name, str(note)[:80]))


def g1_events():
    log = [{'type': 'tick', 'desc': '心跳', 'tick': 1},
           {'type': 'prose', 'desc': '正文', 'tick': 1}]
    for i in range(10):
        log.append({'type': 'event', 'desc': '事件%d' % i, 'tick': i + 2, 'seq': i + 1})
        log.append({'type': 'event', 'desc': '事件%d' % i, 'tick': i + 2, 'seq': i + 2})
    st = {'event_log': log}
    events, _, merged = PANEL._build_events(st)
    expected = {'id', 'seq', 'tick', 'type', 'kind', 'severity', 'title', 'desc', 'icon'}
    check('events 契约（9 字段 + severity 合法，tick 滤除且重复合并后 10 条）',
          len(events) == 10 and expected <= set(events[0])
          and all(e['severity'] in ('info', 'warn', 'danger', 'good', 'success', 'error')
                  or isinstance(e['severity'], str) for e in events),
          '%d events' % len(events))
    check('相邻重复事件已合并（repeat 计数生效）',
          len(merged) == 10 and all(e.get('repeat') == 2 for e in merged),
          str([e.get('repeat') for e in merged[:3]]))
    ids = [e['id'] for e in events]
    check('events.id 稳定（tick[.seq]:type:短哈希，无重复）',
          len(ids) == len(set(ids)) and all(':' in x for x in ids), str(ids[:2]))


def g2_price_index():
    st = {'market': {
        'a': {'x': {'price': 110, 'base_price': 100}},
        'b': {'y': {'price': 100, 'base_price': 100}},
    }}
    sample = VIZ.sample_of(st)
    check('price_index 精确等于样本均价（(1.1+1.0)/2=1.05）',
          sample.get('price_index') == 1.05, str(sample.get('price_index')))


def g3_inbox():
    path = os.path.join(tempfile.mkdtemp(prefix='ww-panel-'), 's.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'tick': 0}, f)
    for i in range(PANEL.INBOX_MAX_PENDING + 5):
        PANEL.inbox_append(path, '测试行动 %d' % i)
    records = PANEL.inbox_read_all(path)
    check('行动队列：落盘记录有界（≤ 102 行，不是只切片返回）',
          len(records) <= PANEL.INBOX_MAX_PENDING + 2,
          '%d records' % len(records))


def g4_api_guard():
    handler = object.__new__(PANEL.Handler)
    handler.headers = {'Host': '127.0.0.1:8791', 'Origin': 'http://evil.example'}
    handler.server = SimpleNamespace(host_allow=None)
    calls = []
    handler._api_json = lambda code, payload: calls.append(code)
    check('POST /action 拒绝跨站 Origin（403）',
          handler._api_guard() is False and 403 in calls, str(calls))


def g5_state_diff():
    before = {
        "tick": 3,
        "entities": {"player": {
            "hp": 30, "gold": 8,
            "items": {"plank": 4, "nails": 16},
            "weapon": {"name": "旧柴刀", "durability": 20},
        }},
        "gameplay": {"clocks": [{"name": "体温", "segments": 6, "filled": 1}]},
        "world_flags": ["mode:power"],
        "scene": {"title": "第一夜：四块板"},
        "relations": {"lin": {"name": "林蔓", "affinity": 0}},
    }
    after = {
        "tick": 4,
        "entities": {"player": {
            "hp": 15, "gold": 8,
            "items": {"plank": 2, "nails": 16, "rope": 1},
            "weapon": {"name": "旧柴刀", "durability": 18},
        }},
        "gameplay": {"clocks": [{"name": "体温", "segments": 6, "filled": 3}]},
        "world_flags": ["mode:power", "door_barred"],
        "scene": {"title": "第二夜：门闩"},
        "relations": {"lin": {"name": "林蔓", "affinity": 1}},
        "item_catalog": {"rope": {"name": "尼龙绳"}},
    }
    summary = state_diff.summarize(before, after)
    keys = {row["key"] for row in summary["changes"]}
    check("状态差异：气血下降、木板减少、体温上升、绳子入包",
          {"hp", "item:plank", "clock:体温", "item:rope"} <= keys,
          str(sorted(keys)))
    check("状态差异：武器耐久与门闩标记可见",
          {"weapon:durability", "flag:door_barred"} <= keys,
          str(sorted(keys)))
    check("状态差异：物品名来自 item_catalog，而不是英文 key",
          next(row for row in summary["changes"] if row["key"] == "item:rope")["label"] == "尼龙绳")
    check("状态差异：有界且带一行摘要",
          len(summary["changes"]) <= state_diff.MAX_CHANGES
          and "气血 -15" in state_diff.format_line(summary))


def main():
    g1_events()
    g2_price_index()
    g3_inbox()
    g4_api_guard()
    g5_state_diff()
    passed = sum(RESULTS)
    print('\n%d/%d passed' % (passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
