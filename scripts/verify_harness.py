#!/usr/bin/env python3
"""Harness-layer regressions: prompt, skills, rulebook events, local hooks."""

import json
import os
import shutil
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

from game_engine import dialog_runtime, harness_config, harness_hooks  # noqa: E402
from game_engine.rules import rulebook  # noqa: E402
from game_engine.state_schema import load_state, transact_state  # noqa: E402

RESULTS = []


def check(name, ok, note=''):
    RESULTS.append(bool(ok))
    print('%s  %-58s %s' % ('PASS' if ok else 'FAIL', name, str(note)[:100]))


def _demo_state(tmp):
    # CI checkouts have no `saves/` directory (it is gitignored); the demo
    # fixture under docs/demo is the portable source of truth.  Keep the old
    # local save as a fallback for developer machines that still have it.
    candidates = [
        os.path.join(ROOT, 'docs', 'demo', '折剑行.save.json'),
        os.path.join(ROOT, 'saves', '万岛海域_救生筏_重开.save.json'),
    ]
    src = next((path for path in candidates if os.path.isfile(path)), '')
    if not src:
        raise FileNotFoundError('没有可用的演示存档：docs/demo/折剑行.save.json 或 saves/万岛海域_救生筏_重开.save.json')
    dst = os.path.join(tmp, 'game.save.json')
    shutil.copy(src, dst)
    return dst


def g1_config():
    catalog = harness_config.skill_map()
    check('叙事技能目录至少 4 个包', len(catalog) >= 4, ', '.join(sorted(catalog)))
    check('技能包带 name/summary/body',
          all(item.get('name') and item.get('summary') and item.get('body')
              for item in catalog.values()), str(len(catalog)))

    cfg = harness_config.normalize({
        'director_note': '  短句。  ',
        'table_rules': ['不出现枪械', '', ' 不出现枪械 ', '不替玩家决定'],
        'skills': ['survival-pressure', 'missing', 'survival-pressure'],
        'runtime': {'audit': False, 'history_turns': 2, 'tool_rounds': 99},
        'rule_events': {'turn': True, 'tool': False},
        'hooks': {'enabled': True, 'timeout': 0, 'events': ['before_turn', 'nope']},
    })
    check('导演备注 trim', cfg['director_note'] == '短句。', cfg['director_note'])
    check('桌面规则去空去重', cfg['table_rules'] == ['不出现枪械', '不替玩家决定'],
          str(cfg['table_rules']))
    check('未知技能被丢弃、重复只留一个', cfg['skills'] == ['survival-pressure'],
          str(cfg['skills']))
    check('运行时参数夹紧（history 4 / tool_rounds 6）',
          cfg['runtime']['history_turns'] == 4 and cfg['runtime']['tool_rounds'] == 6,
          str(cfg['runtime']))
    check('规则事件开关保留', cfg['rule_events']['turn'] is True
          and cfg['rule_events']['tool'] is False, str(cfg['rule_events']))
    check('hook 超时夹到 1 秒、未知事件丢弃',
          cfg['hooks']['timeout'] == 1 and cfg['hooks']['events'] == ['before_turn'],
          str(cfg['hooks']))


def g2_prompt_and_file(tmp):
    path = os.path.join(tmp, 'harness.json')
    cfg = harness_config.normalize({
        'director_note': '先写代价。',
        'table_rules': ['每场最多一条线索'],
        'skills': ['clue-discipline'],
    })
    saved = harness_config.save(cfg, path=path)
    check('配置写入后可读回',
          harness_config.load(path)['director_note'] == '先写代价。',
          saved.get('director_note'))
    mode = oct(os.stat(path).st_mode & 0o777)
    check('配置文件权限 0600', mode == '0o600', mode)
    public = harness_config.public_config(path=path)
    check('public_config 标记 file 来源且技能 enabled',
          public['source'] == 'file'
          and any(row['id'] == 'clue-discipline' and row['enabled'] for row in public['skills']),
          public['source'])
    prompt = harness_config.prompt_sections(cfg)
    check('提示词段落含导演备注/桌面规则/技能正文',
          '先写代价。' in prompt and '每场最多一条线索' in prompt
          and '一场戏只给一条能推进的线索' in prompt, prompt[:80])


def g3_hooks(tmp):
    hook_dir = os.path.join(tmp, 'hooks')
    os.makedirs(hook_dir)
    harness_hooks.LOG_PATH = os.path.join(tmp, 'hooks.log')
    open(os.path.join(hook_dir, 'before_turn.py'), 'w', encoding='utf-8').write(
        'def before_turn(ctx):\n'
        '    return {"prompt": "潮水正在退", "block": ""}\n')
    open(os.path.join(hook_dir, 'after_tool.py'), 'w', encoding='utf-8').write(
        'def after_tool(ctx):\n'
        '    return {"notes": ["工具后记一笔"]}\n')
    open(os.path.join(hook_dir, 'after_turn.py'), 'w', encoding='utf-8').write(
        'def after_turn(ctx):\n'
        '    return {"note": "回合后记一笔"}\n')
    cfg = harness_config.normalize({'hooks': {'enabled': True, 'dir': hook_dir, 'timeout': 3}})
    before = harness_hooks.run('before_turn', {'text': '看看'}, cfg)
    check('before_turn 返回 prompt', before.get('ok') and before.get('prompt') == '潮水正在退',
          str(before)[:100])
    tool = harness_hooks.run('after_tool', {'tool': 'inspect'}, cfg)
    check('after_tool 返回 notes', tool.get('ok') and tool.get('notes') == ['工具后记一笔'],
          str(tool)[:100])
    after = harness_hooks.run('after_turn', {'reply': '你看见光'}, cfg)
    check('after_turn 返回 note', after.get('ok') and after.get('notes') == ['回合后记一笔'],
          str(after)[:100])
    status = harness_hooks.status(cfg)
    check('hook 状态列出三个脚本', status.get('ready') is True
          and sum(1 for row in status['scripts'] if row['exists']) == 3,
          str(status['scripts']))
    disabled = harness_config.normalize({'hooks': {'enabled': False, 'dir': hook_dir}})
    skipped = harness_hooks.run('before_turn', {}, disabled)
    check('默认关闭时 hook 不执行', skipped.get('ran') is False, str(skipped))

    open(os.path.join(hook_dir, 'before_turn.py'), 'w', encoding='utf-8').write(
        'import socket\n'
        'def before_turn(ctx):\n'
        '    socket.socket()\n'
        '    return {}\n')
    net = harness_hooks.run('before_turn', {}, cfg)
    check('hook 网络调用被审计钩子拦下', net.get('ok') is False
          and 'hook 退出码' in str(net.get('error')), str(net.get('error'))[:100])

    open(os.path.join(hook_dir, 'after_turn.py'), 'w', encoding='utf-8').write(
        'import time\n'
        'def after_turn(ctx):\n'
        '    time.sleep(2)\n'
        '    return {"note": "太慢"}\n')
    slow_cfg = harness_config.normalize(
        {'hooks': {'enabled': True, 'dir': hook_dir, 'timeout': 1}})
    slow = harness_hooks.run('after_turn', {}, slow_cfg)
    check('hook 超时被捕获且不拖垮进程', slow.get('ok') is False
          and '超时' in str(slow.get('error')), str(slow.get('error'))[:100])
    open(os.path.join(hook_dir, 'after_turn.py'), 'w', encoding='utf-8').write(
        'def after_turn(ctx):\n    return {"notes": ["HOOK-NOTE"]}\n')


def g4_rules(tmp):
    path = _demo_state(tmp)
    with open(path, encoding='utf-8') as fh:
        state = json.load(fh)
    before_hp = state['entities']['player']['hp']
    rules = rulebook.normalize([
        {'id': 'turn_hp', 'order': 10, 'when': True,
         'then': [{'op': 'resource', 'key': 'hp', 'delta': -1}], 'note': '每回合掉 1'},
    ])

    def edit(current):
        rulebook.load(current, rules)

    transact_state(edit, path, allow_create=False)
    cfg = harness_config.normalize({'rule_events': {'turn': True, 'tool': False}})
    runtime = dialog_runtime.DialogRuntime(path, adapter=SimpleNamespace(), harness=cfg)
    result = runtime._apply_rules('turn', 'turn')
    after = load_state(path)
    check('回合事件执行规则并扣血',
          result.get('applied') == ['turn_hp'] and after['entities']['player']['hp'] == before_hp - 1,
          str(result.get('applied')) + ' hp=%s' % after['entities']['player']['hp'])
    check('规则触发计数落盘', after['rulebook']['fired'].get('turn_hp') == 1,
          str(after['rulebook']['fired']))
    skipped = runtime._apply_rules('inspect', 'tool')
    check('工具事件开关关闭时不执行', skipped.get('skipped') is True, str(skipped))

    bad = False
    try:
        rulebook.normalize([{'id': 'bad', 'then': [{'op': 'teleport'}]}])
    except ValueError:
        bad = True
    check('规则白名单拒绝未知效果', bad, '')


def g5_runtime(tmp):
    path = _demo_state(tmp)
    rules = rulebook.normalize([
        {'id': 'turn_hp', 'when': True,
         'then': [{'op': 'resource', 'key': 'hp', 'delta': -1}]},
    ])

    def edit(state):
        rulebook.load(state, rules)

    transact_state(edit, path, allow_create=False)
    with open(path, encoding='utf-8') as fh:
        before_hp = json.load(fh)['entities']['player']['hp']
    hook_dir = os.path.join(tmp, 'runtime-hooks')
    os.makedirs(hook_dir)
    harness_hooks.LOG_PATH = os.path.join(tmp, 'runtime-hooks.log')
    open(os.path.join(hook_dir, 'before_turn.py'), 'w', encoding='utf-8').write(
        'def before_turn(ctx):\n    return {"prompt": "HOOK-PROMPT"}\n')
    open(os.path.join(hook_dir, 'after_turn.py'), 'w', encoding='utf-8').write(
        'def after_turn(ctx):\n    return {"notes": ["HOOK-NOTE"]}\n')
    cfg = harness_config.normalize({
        'director_note': '短句。',
        'skills': ['clue-discipline'],
        'runtime': {'audit': False},
        'rule_events': {'turn': True, 'tool': False},
        'hooks': {'enabled': True, 'dir': hook_dir, 'timeout': 3,
                  'events': ['before_turn', 'after_turn']},
    })

    class FakeAdapter:
        def __init__(self):
            self.messages = None

        def chat(self, messages, tools=None, tool_choice='auto', stream=False):
            self.messages = messages
            return {'message': {'content': '门缝里透出一点光。'}, 'usage': {'total_tokens': 4}}

    adapter = FakeAdapter()
    runtime = dialog_runtime.DialogRuntime(path, adapter=adapter, harness=cfg)
    result = runtime.respond('我看看门')
    check('对话回合成功返回', result.get('ok') is True and result.get('reply'), str(result)[:90])
    check('before_turn 的 prompt 进入系统提示',
          adapter.messages and 'HOOK-PROMPT' in adapter.messages[0]['content'], '')
    check('导演备注与技能进入系统提示',
          adapter.messages and '短句。' in adapter.messages[0]['content']
          and '一场戏只给一条能推进的线索' in adapter.messages[0]['content'], '')
    check('after_turn 的 note 写入回合', result.get('hook_notes') == ['HOOK-NOTE'],
          str(result.get('hook_notes')))
    check('audit 开关关闭后 audit 为空', result.get('audit') == [], str(result.get('audit')))
    after = load_state(path)
    check('回合规则在模型调用前生效', after['entities']['player']['hp'] == before_hp - 1,
          'hp=%s -> %s' % (before_hp, after['entities']['player']['hp']))

    open(os.path.join(hook_dir, 'before_turn.py'), 'w', encoding='utf-8').write(
        'def before_turn(ctx):\n    return {"block": "这一行动不符合桌上的约定"}\n')
    blocked = dialog_runtime.DialogRuntime(path, adapter=FakeAdapter(), harness=cfg)
    try:
        blocked.respond('我推开门')
        raised = False
        error = ''
    except dialog_runtime.DialogRuntimeError as exc:
        raised = True
        error = str(exc)
    check('before_turn 的 block 会中止回合', raised and '不符合桌上的约定' in error,
          error[:100])
    with open(path, encoding='utf-8') as fh:
        turns = json.load(fh).get('turns') or []
    check('被 block 时不写入玩家回合', not any(
        row.get('role') == 'player' and row.get('text') == '我推开门' for row in turns), '')


def g6_library():
    from game_engine import library, narrative_rules
    data = library.payload()
    check('知识库至少 1 个预制玩法', len(data['playbooks']) >= 1,
          ', '.join(row['id'] for row in data['playbooks']))
    check('知识库至少 2 份档案', len(data['archives']) >= 2,
          ', '.join(row['id'] for row in data['archives']))
    island = library.get_playbook('island-raft')
    check('海岛预制包锁定白鹿岛设定',
          island['world']['kind'] == 'setting'
          and island['world']['id'] == 'settings/白鹿岛.setting.json',
          str(island['world']))
    payload = library.playbook_narrative(island)
    cfg = narrative_rules.normalize(payload)
    check('预制包叙事字段被归一化',
          cfg['genre'] == '生存' and cfg['difficulty'] == '硬核'
          and cfg['skill_ids'] == ['survival-pressure', 'ledger-economy']
          and cfg['prefab'] == 'island-raft', str(cfg)[:140])
    check('预制包带真实技能与风格',
          'survival-pressure' in cfg['skill_ids'] and '短句' in cfg['style'], cfg['style'][:50])
    bad = False
    try:
        library.normalize_playbook({'id': '../bad', 'title': 'x',
                                    'world': {'kind': 'template', 'id': 'survival'}})
    except ValueError:
        bad = True
    check('预制包拒绝路径式 id', bad, '')


def g7_ui():
    html = open(os.path.join(ROOT, 'panel.html'), encoding='utf-8').read()
    js = open(os.path.join(ROOT, 'panel.js'), encoding='utf-8').read()
    for ident in ('connect-harness', 'harness-note', 'harness-table-rules',
                  'harness-skills', 'rule-json', 'rule-save', 'hook-enabled',
                  'hook-status'):
        check('调校页包含 #%s' % ident, ('id="%s"' % ident) in html, '')
    check('脚本包含调校接口与技能渲染',
          '/api/v1/harness/config' in js and 'renderHarnessSkills' in js
          and '/api/v1/rules' in js and 'refreshHooks' in js, '')
    check('调校页已加入缓存破坏版本 ui5', '?v=ui5' in html, '')
    check('大厅包含知识库入口', 'id="library-btn"' in html and 'id="library-overlay"' in html, '')
    check('知识库脚本包含预制玩法渲染',
          'renderLibrary' in js and '/api/v1/library' in js
          and 'usePlaybook' in js and 'libraryTab' in js, '')


def main():
    tmp = tempfile.mkdtemp(prefix='ww-harness-')
    g1_config()
    g2_prompt_and_file(tmp)
    g3_hooks(tmp)
    g4_rules(tmp)
    g5_runtime(tmp)
    g6_library()
    g7_ui()
    print('\n%d/%d passed' % (sum(RESULTS), len(RESULTS)))
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
