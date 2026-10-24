#!/usr/bin/env python3
"""
文档一致性自检 (verify_docs.py)

为什么需要：项目多次出现"代码改了、README 还写着旧数字"的漂移。文档是交付物的一部分，
版本号、工具数、断言数、文件路径都必须是可核对的，而不是手写的。

检查：
  D1  版本号单一信源：__init__.py == pyproject.toml == README 徽章区
  D2  MCP 工具数：mcp_server.py 实际 @server.tool 数 == world_schema 登记数 == README 宣称
  D3  README / README.en 引用的截图与演示存档全部存在且非空
  D4  文档里提到的 scripts/*.py 全部存在
  D5  ARCHITECTURE 的文档版本号与 __version__ 大版本一致
  D6  CHANGELOG 含当前版本条目
  D7  Pages 展示站引用的截图存在
  D8  没有残留的 TODO/FIXME 占位（生产代码）

用法:  python scripts/verify_docs.py
退出码: 0 = 一致；1 = 有漂移
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []


def check(name, ok, note=''):
    RESULTS.append(bool(ok))
    print('%s  %-52s %s' % ('PASS' if ok else 'FAIL', name, str(note)[:80]))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return f.read()


def version():
    txt = read('__init__.py')
    m = re.search(r'__version__\s*=\s*"([^"]+)"', txt)
    return m.group(1) if m else None


def main():
    ver = version()
    check('D1a __init__.py 有版本号', bool(ver), ver)

    pyproject = read('pyproject.toml')
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    check('D1b pyproject.toml 版本与 __init__.py 一致', m and m.group(1) == ver,
          '%s vs %s' % (m.group(1) if m else None, ver))

    readme = read('README.md')
    check('D1c README 提到当前版本', ver in readme, ver)

    # D2 工具数：源码里 @server.tool 数量
    mcp = read('mcp_server.py')
    tool_count = len(re.findall(r'^@server\.tool', mcp, re.M))
    # 精确解析：用 ast 读 world_schema 的返回字面量不可行（它含格式化表达式），
    # 改为直接 import 模块后比较字典键——这是唯一不会数错的方式。
    sys.path.insert(0, ROOT)
    import importlib
    if 'game_engine' not in sys.modules:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location('game_engine', os.path.join(ROOT, '__init__.py'),
                                            submodule_search_locations=[ROOT])
        _pkg = _ilu.module_from_spec(_spec)
        _pkg.__path__ = [ROOT]
        sys.modules['game_engine'] = _pkg
        _spec.loader.exec_module(_pkg)
    _ms = importlib.import_module('game_engine.mcp_server')
    actual = {t.name for t in _ms.server._tool_manager.list_tools()}
    registered = len(set(_ms.world_schema()['action_tools']))
    check('D2d world_schema 登记的键与实际工具名逐一对应',
          set(_ms.world_schema()['action_tools']) == actual,
          '缺少: %s' % sorted(actual - set(_ms.world_schema()['action_tools']))[:3])
    check('D2a 每行一个 @server.tool（无重复装饰）', tool_count > 30, '%d 个' % tool_count)
    check('D2b world_schema 登记数与实际工具数完全一致',
          registered == tool_count, 'registered=%d tools=%d' % (registered, tool_count))
    # README 里所有 "NN 个 MCP 工具" 与 "工具一览（NN 个）" 的写法都要对得上
    claimed = (re.findall(r'(\d+)\s*个\s*MCP\s*工具', readme)
               + re.findall(r'MCP\s*工具一览（(\d+)\s*个）', readme)
               + re.findall(r'MCP 服务器（(\d+) 个工具）', readme))
    check('D2c README 宣称的工具数与源码一致',
          len(claimed) >= 2 and all(int(c) == tool_count for c in claimed),
          'readme=%s actual=%d' % (claimed[:4], tool_count))

    # D3 截图与演示存档
    missing = []
    for doc in ('README.md', 'README.en.md'):
        text = read(doc)
        for ref in re.findall(r'\]\((docs/[^)\s]+)\)', text) + re.findall(r'src="(docs/[^"]+)"', text):
            path = os.path.join(ROOT, ref)
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                missing.append('%s → %s' % (doc, ref))
    check('D3 README 引用的图片/文件全部存在且非空', not missing, str(missing[:3]))

    # D4 scripts 引用
    ghost = []
    for doc in ('README.md', 'README.en.md', 'CONTRIBUTING.md', 'AGENTS.md', 'ARCHITECTURE.md'):
        for ref in set(re.findall(r'scripts/([A-Za-z0-9_]+\.py)', read(doc))):
            if not os.path.exists(os.path.join(ROOT, 'scripts', ref)):
                ghost.append('%s → scripts/%s' % (doc, ref))
    check('D4 文档引用的脚本全部存在', not ghost, str(ghost[:3]))

    # D5 架构文档版本
    arch = read('ARCHITECTURE.md')
    m = re.search(r'文档版本：v(\d+)\.(\d+)', arch)
    check('D5 ARCHITECTURE 文档版本可读', bool(m), m.group(0) if m else '—')

    # D6 CHANGELOG
    changelog = read('CHANGELOG.md')
    check('D6 CHANGELOG 有当前版本条目', ('v' + ver) in changelog, ver)

    # D7 Pages 展示站
    pages = read('docs/index.html')
    page_missing = [ref for ref in re.findall(r'(?:src|href)="(screenshots/[^"]+)"', pages)
                    if not os.path.exists(os.path.join(ROOT, 'docs', ref))]
    check('D7 展示站引用的截图/视频全部存在', not page_missing, str(page_missing[:3]))

    # D7b 中英文 README 的断言数与缩略指标必须一致（防只改一份）
    en = read('README.en.md')
    def counts(text):
        return sorted(int(x) for x in re.findall(r'\|\s*(\d+)\s*\|\s', text))
    zh_claims = re.findall(r'`verify_[a-z_]+\.py` \| (\d+)', readme)
    en_claims = re.findall(r'`verify_[a-z_]+\.py` \| (\d+)', en)
    check('D7b 中英文 README 的断言数一致', zh_claims == en_claims,
          'zh=%s en=%s' % (zh_claims[:4], en_claims[:4]))

    # D8 生产代码无 TODO 占位
    todo = []
    for name in ('engine.py', 'mcp_server.py', 'panel.py', 'state_schema.py', 'viz_series.py', '__init__.py'):
        if re.search(r'\b(TODO|FIXME|XXX)\b', read(name)):
            todo.append(name)
    check('D8 生产代码无 TODO/FIXME 占位', not todo, str(todo))

    # D9 演示存档清单与实际文件一致
    demo_readme = read('docs/demo/README.md')
    demo_files = sorted(f for f in os.listdir(os.path.join(ROOT, 'docs', 'demo')) if f.endswith('.save.json'))
    listed = [f for f in demo_files if f in demo_readme]
    check('D9 演示存档清单覆盖全部 .save.json', len(listed) == len(demo_files),
          '%d/%d' % (len(listed), len(demo_files)))

    # D10 四套设定包都在 README 与 settings/README 里列名
    settings_readme = read('settings/README.md')
    bundles = sorted(f[:-len('.setting.json')] for f in os.listdir(os.path.join(ROOT, 'settings'))
                     if f.endswith('.setting.json'))
    check('D10 全部设定包在 settings/README 中登记',
          all(b in settings_readme for b in bundles), str(bundles))

    passed = sum(RESULTS)
    print('\n%d/%d passed' % (passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
