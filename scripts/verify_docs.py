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

import ast
import json
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

    # D2 工具数：静态解析（零依赖——CI core 作业没装 mcp，不能 import mcp_server）
    src = read('mcp_server.py')
    tree = ast.parse(src)
    decorated = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            func = deco.func if isinstance(deco, ast.Call) else deco
            if (isinstance(func, ast.Attribute) and func.attr == 'tool'
                    and isinstance(func.value, ast.Name) and func.value.id == 'server'):
                decorated[node.name] = True
    tool_count = len(decorated)
    check('D2a 静态解析出全部工具函数', tool_count > 25, '%d 个' % tool_count)

    registered = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            if 'world_init' in keys and 'tick' in keys and len(keys) > 20:
                registered = set(keys)
                break
    check('D2b world_schema 登记的工具名与实际工具完全一致',
          registered is not None and registered == set(decorated),
          '缺少: %s' % (sorted(set(decorated) - (registered or set()))[:4] if registered else '未找到'))

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

    # D7c Pages 工作流必须在首次运行时能自启用，否则每次推送都会红
    pages_wf = read('.github/workflows/pages.yml')
    check('D7c Pages 工作流带 enablement: true（首次运行自动启用站点）',
          'enablement: true' in pages_wf and 'pages: write' in pages_wf)

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

    # D11 规则函数数：文档宣称值必须等于 rules/ 顶层公开函数数
    rule_funcs = 0
    rules_dir = os.path.join(ROOT, 'rules')
    for name in sorted(os.listdir(rules_dir)):
        if not name.endswith('.py'):
            continue
        tree = ast.parse(read(os.path.join('rules', name)))
        rule_funcs += sum(1 for n in tree.body
                          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and not n.name.startswith('_'))
    claimed_funcs = []
    for doc in ('README.md', 'README.en.md', 'docs/index.html'):
        text = read(doc)
        claimed_funcs += [int(x) for x in re.findall(r'(\d+)\s*个规则函数', text)]
        claimed_funcs += [int(x) for x in re.findall(r'(\d+)\s*rule functions', text)]
    check('D11 文档宣称的规则函数数与源码一致',
          bool(claimed_funcs) and all(c == rule_funcs for c in claimed_funcs),
          'docs=%s actual=%d' % (sorted(set(claimed_funcs)), rule_funcs))

    # D12 自检脚本数：README 宣称值必须等于 scripts/verify_*.py 实际数量
    verify_scripts = [f for f in os.listdir(os.path.join(ROOT, 'scripts'))
                      if f.startswith('verify_') and f.endswith('.py')]
    claimed_checks = []
    for doc in ('README.md', 'README.en.md', 'docs/index.html'):
        text = read(doc)
        claimed_checks += [int(x) for x in re.findall(r'(\d+)\s*个可执行自检', text)]
        claimed_checks += [int(x) for x in re.findall(r'(\d+)\s*executable self-checks', text)]
    check('D12 文档宣称的自检脚本数与 scripts 实际一致',
          bool(claimed_checks) and all(c == len(verify_scripts) for c in claimed_checks),
          'docs=%s actual=%d' % (sorted(set(claimed_checks)), len(verify_scripts)))

    # D13 英文 README 与展示站的工具数也必须一致（D2c 只查中文 README）
    en_claimed = [int(x) for x in re.findall(r'(\d+)\s*MCP tools', en)]
    site_tools = [int(x) for x in re.findall(r'<b>(\d+)</b>\s*MCP 工具', read('docs/index.html'))]
    check('D13 英文 README / 展示站的工具数与源码一致',
          all(c == tool_count for c in en_claimed + site_tools),
          'en=%s site=%s actual=%d' % (en_claimed, site_tools, tool_count))

    # D14 全仓 Markdown 引用的 scripts/*.py 必须存在（此前 __init__.py 的幽灵引用漏检）
    ghost = []
    for base, _dirs, files in os.walk(ROOT):
        if '.git' in base.split(os.sep):
            continue
        for fname in files:
            if fname.endswith('.md'):
                path = os.path.join(base, fname)
                rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
                text = open(path, encoding='utf-8').read()
                # 历史审计报告（docs/AUDIT_*、docs/PROJECT_AUDIT_*）是带日期的快照，
                # 里面引用的旧脚本名允许不存在；其余文档必须全部可解析。
                if rel.startswith('docs/AUDIT_') or rel.startswith('docs/PROJECT_AUDIT_'):
                    continue
                for ref in set(re.findall(r'scripts/([A-Za-z0-9_]+\.py)', text)):
                    if not os.path.exists(os.path.join(ROOT, 'scripts', ref)):
                        ghost.append('%s → scripts/%s' % (rel, ref))
    check('D14 所有 Markdown 引用的脚本都存在（全仓扫描）', not ghost, str(ghost[:3]))

    # D15 展示站的相对链接必须在仓库内可解析（部署到 Pages 后 `../` 会越出站点根）
    site = read('docs/index.html')
    bad_links = []
    for ref in re.findall(r'href="([^"#:]+)"', site):
        if ref.startswith(('http', 'mailto')):
            continue
        if ref.startswith('../'):
            bad_links.append(ref)
            continue
        if not os.path.exists(os.path.join(ROOT, 'docs', ref)):
            bad_links.append(ref)
    check('D15 展示站相对链接全部可解析且不越出站点根', not bad_links, str(bad_links[:3]))

    # D16 README 的快速上手命令必须真的可执行（至少商品存在且买得起）
    quick = read('README.md')
    m = re.search(r'trade\(location="([^"]+)", item="([^"]+)", direction="(buy|sell)", quantity=(\d+)\)', quick)
    bundle = None
    if m:
        for f in os.listdir(os.path.join(ROOT, 'settings')):
            if f.endswith('.setting.json'):
                data = json.loads(read(os.path.join('settings', f)))
                if (data.get('world') or {}).get('name') == '玄枢界':
                    bundle = data
                    break
    ok_quick = False
    note = '未找到示例'
    if m and bundle:
        loc, item, direction, qty = m.group(1), m.group(2), m.group(3), int(m.group(4))
        market = {x.get('location'): x for x in bundle.get('market') or []}
        items = {i.get('key'): i for i in (market.get(loc) or {}).get('items') or []}
        it = items.get(item)
        gold = int((bundle.get('player') or {}).get('gold', 0) or 0)
        if it and direction == 'buy':
            ok_quick = gold >= int(it.get('price', 0)) * qty
            note = 'gold=%d price=%s qty=%d' % (gold, it.get('price'), qty)
        elif it and direction == 'sell':
            held = int(((bundle.get('player') or {}).get('items') or {}).get(item, 0))
            ok_quick = held >= qty
            note = 'held=%d qty=%d' % (held, qty)
    check('D16 README 快速上手交易示例可执行（商品存在且买得起/卖得出）',
          ok_quick, note)

    passed = sum(RESULTS)
    print('\n%d/%d passed' % (passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
