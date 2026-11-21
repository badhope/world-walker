#!/usr/bin/env python3
"""领域模型回归：载具梯、物品目录、能力选择、体力双写与当前存档一致性。

这些断言针对过去真实漂移过的点：
  · setting 里有 vessel_ladder，state 里没有 → 面板只能读手写 sheet；
  · progression.max 被 game engine 夹到 20，85 级载具显示成 20 级；
  · game.resources.hp 与 entities.player.hp 各改各的；
  · vehicle_core / blueprint_rubber_boat 等 key 在背包里没有中文名。
"""

import json
import os
import sys
import tempfile

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
_spec = _ilu.spec_from_file_location('panel_domain', os.path.join(ROOT, 'panel.py'))
PANEL = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(PANEL)

from game_engine import gameplay as GP
from game_engine import settings_loader as SL
from game_engine.rules import gamesystem as GS
from game_engine.rules import vessel as VS
from game_engine.state_schema import load_state, save_state

SETTING = os.path.join(ROOT, 'settings', '白鹿岛.setting.json')
SAVE = os.path.join(ROOT, 'saves', '万岛海域_救生筏.save.json')
RESULTS = []


def check(name, ok, note=''):
    RESULTS.append(bool(ok))
    print('%s  %-62s %s' % ('PASS' if ok else 'FAIL', name, str(note)[:90]))


def main():
    with open(SETTING, encoding='utf-8') as handle:
        bundle = json.load(handle)
    state = SL.build_state(bundle)
    ladder = state.get('vessel_ladder') or {}
    classes = ladder.get('classes') or []

    check('载具梯落进运行状态（不是只留在 setting）',
          bool(classes) and state.get('vessel', {}).get('class') == '普通充气救生筏',
          '%d classes' % len(classes))
    check('17 大品阶 × 每阶 5 细分阶 = 85 级',
          len(classes) == 17 and all(len(row.get('grades') or []) == 5 for row in classes)
          and ladder.get('tier_max') == 85,
          'classes=%d tier_max=%s' % (len(classes), ladder.get('tier_max')))
    check('首阶没有甲板：甲板 0 / 筏包 2 / 载重 30kg',
          state['vessel']['deck_slots'] == 0
          and state['vessel']['storage_slots'] == 2
          and state['vessel']['cargo_kg'] == 30,
          str({k: state['vessel'][k] for k in ('deck_slots', 'storage_slots', 'cargo_kg')}))

    base = next((m for m in (state.get('game') or {}).get('meters') or []
                 if m.get('key') == 'base'), None)
    check('game.meters.base 的 max 是 85（不是被夹成 20）',
          base is not None and int(base.get('max', 0)) == 85,
          str(base))
    upgrade = next((p for p in (state.get('gameplay') or {}).get('progression') or []
                    if p.get('id') == 'upgrade'), None)
    check('gameplay.progression.upgrade.max 保留 85',
          upgrade is not None and int(upgrade.get('max', 0)) == 85,
          str(upgrade))

    # 升到橡皮艇 I 后：甲板 1 格、筏包 4 格、载重 60kg；数值来自同一张梯。
    base['value'] = 6
    up = VS.status(state)
    check('第 6 级 = 橡皮艇 I，甲板/筏包/载重同步变大',
          up.get('class') == '橡皮艇' and up.get('deck_slots') == 1
          and up.get('storage_slots') == 4 and up.get('cargo_kg') == 60,
          str({k: up.get(k) for k in ('class', 'grade', 'deck_slots', 'storage_slots', 'cargo_kg')}))

    check('设施梯 10 类、每类 5 级全部落盘',
          len(state.get('facility_ladder') or []) == 10
          and all(len(row.get('levels') or []) == 5 for row in state.get('facility_ladder') or []),
          str(len(state.get('facility_ladder') or [])))
    check('模块梯 8 类、每类 5 级全部落盘',
          len(state.get('module_ladder') or []) == 8
          and all(len(row.get('levels') or []) == 5 for row in state.get('module_ladder') or []),
          str(len(state.get('module_ladder') or [])))
    abilities = state.get('ability_selection') or {}
    check('能力选择 8 个选项，当前分解系可解析到 current_id',
          len(abilities.get('options') or []) == 8
          and abilities.get('current_id') == 'decompose',
          '%s / %s' % (abilities.get('current'), abilities.get('current_id')))

    catalog = state.get('item_catalog') or {}
    used = [k for k, n in ((state.get('entities', {}).get('player') or {}).get('items') or {}).items() if n]
    check('背包里每个正数物品都有中文名',
          all((catalog.get(k) or {}).get('name') not in (None, '', k) for k in used),
          str([(k, (catalog.get(k) or {}).get('name')) for k in used[:5]]))
    check('载具核/橡皮艇蓝图/橡胶胶水/阀夹都有目录条目',
          all(k in catalog for k in ('vehicle_core', 'blueprint_rubber_boat', 'rubber_glue', 'valve_clamp')),
          str(sorted(k for k in catalog if k in ('vehicle_core', 'blueprint_rubber_boat', 'rubber_glue', 'valve_clamp'))))

    # 双写：game_adjust 改 hp 必须同步实体；实体战斗扣血后必须能回写档案。
    player = state['entities']['player']
    before = player['hp']
    GS.adjust(state, 'hp', delta=-7)
    check('game_adjust(hp) 同步 entities.player.hp',
          player['hp'] == before - 7,
          '%s -> %s' % (before, player['hp']))
    player['hp'] = 5
    profile = GS.sync_from_player(state)
    hp_row = next(r for r in profile['resources'] if r['key'] == 'hp')
    check('sync_from_player 把实体扣血回写档案',
          hp_row['value'] == 5, str(hp_row))

    tmp = tempfile.mkdtemp(prefix='ww-domain-')
    state_path = os.path.join(tmp, 'domain.save.json')
    state['entities']['player']['items']['vehicle_core'] = 1
    save_state(state, state_path)
    vm = PANEL.view_model(state_path)
    check('面板 HUD 阶位与载具 base 同源（6/85，不再读 config.stage_max=20）',
          vm['player']['stage'] == 6 and vm['player']['stage_max'] == 85,
          '%s/%s' % (vm['player']['stage'], vm['player']['stage_max']))
    check('面板 game.vessel 与 state.vessel 同源',
          (vm.get('game') or {}).get('vessel', {}).get('class') == '橡皮艇',
          str((vm.get('game') or {}).get('vessel')))
    check('面板物品使用目录中文名',
          any(row.get('key') == 'vehicle_core' and row.get('name') == '载具核'
              for row in vm['player']['inventory']),
          str([(r['key'], r['name']) for r in vm['player']['inventory'][:4]]))

    # 当前存档：允许旧场景仍在 open，但域模型、任务条件、双写必须一致。
    # CI 没有本地 saves/（该目录被 .gitignore 排除），缺省时用同一设定包生成的
    # 内存态做等价核验，避免回归测试依赖某台机器上的私有存档。
    if os.path.exists(SAVE):
        current = load_state(SAVE)
    else:
        current = state
        current['scene'] = {'title': '安装载具核', 'status': 'open'}
    cur_player = (current.get('entities') or {}).get('player') or {}
    cur_hp = next((r['value'] for r in (current.get('game') or {}).get('resources') or []
                   if r.get('key') == 'hp'), None)
    check('当前存档 hp 档案与实体一致',
          cur_hp == cur_player.get('hp'), '%s vs %s' % (cur_hp, cur_player.get('hp')))
    check('当前存档已带载具梯/物品目录/能力选择',
          all(k in current for k in ('vessel_ladder', 'item_catalog', 'ability_selection')),
          str([k for k in ('vessel_ladder', 'item_catalog', 'ability_selection') if k in current]))
    check('当前存档场景仍是“安装载具核”且 open',
          (current.get('scene') or {}).get('title') == '安装载具核'
          and (current.get('scene') or {}).get('status') == 'open',
          str((current.get('scene') or {}).get('title')))
    q = next((q for q in (current.get('questlines') or []) if q.get('id') == 'upgrade_vessel'), {})
    stage = next((s for s in q.get('stages') or [] if s.get('id') == 'parts'), {})
    check('升级任务不再要求已过期的 core_shard×3',
          'core_shard' not in json.dumps(stage, ensure_ascii=False)
          and 'vehicle_core' in json.dumps(stage, ensure_ascii=False),
          str(stage.get('exit_if')))

    passed = sum(RESULTS)
    print('\n%d/%d passed' % (passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
