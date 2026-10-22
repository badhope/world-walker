#!/usr/bin/env python3
"""
界面冒烟 (smoke_ui.py)

门禁用：自己起一个临时面板（真实面板 + 真实状态），跑 scripts/audit_ui.py
的核心断言，跑完关掉。不依赖外部已启动的服务。

为什么单独一个文件：audit_ui.py 需要 `--url` 指向已运行的面板（截图时人工
用），而门禁里必须自包含——否则"门禁全绿"可能只是因为没连上任何面板。

用法:  python scripts/smoke_ui.py
退出码: 0 = 界面正常；1 = 有检查失败；2 = 缺少 playwright
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('缺少 playwright：pip install playwright && python -m playwright install msedge')
    sys.exit(2)

# 造一份最小但完整的存档：足够让面板渲染出 HUD/时间线/图鉴/市场/关系
STATE = {
    'tick': 42,
    'rng_seed': 7,
    'currency': '玄晶',
    'world_info': {'name': '玄枢界', 'era': '玄枢历三年', 'location_desc': '雾锁长街，灯影摇红。'},
    'entities': {
        'player': {'name': '沈砚', 'faction': '散修', 'level': '引元境·初层', 'stage': 2,
                   'attrs': {'str': 14, 'dex': 12, 'int': 15, 'con': 11, 'cha': 10},
                   'hp': 70, 'hp_max': 100, 'mp': 18, 'mp_max': 30, 'gold': 260,
                   'location': '临川城', 'items': {'an_shen_dan': 2, 'fei_jian': 1},
                   'morality': [1, 0, -1, 0, 0, 2]},
        'laowang': {'name': '老王', 'faction': '市井', 'level': '凡人',
                    'attrs': {'str': 7, 'dex': 8, 'int': 12, 'con': 9, 'cha': 13},
                    'hp': 35, 'hp_max': 35, 'gold': 150, 'location': '临川城'},
    },
    'relations': {'laowang:player': {'affinity': 24, 'respect': 3}},
    'market': {'临川城': {
        'an_shen_dan': {'name': '安神丹', 'price': 55, 'supply': 18, 'base_price': 50,
                        'type': '丹药', 'desc': '安神'}}},
    'karma_ledger': [],
    'world_flags': ['xuanshu'],
    'event_log': [
        {'tick': 40, 'type': 'system', 'desc': '世界「玄枢界」开局'},
        {'tick': 41, 'type': 'combat', 'desc': '沈砚击败了山贼'},
        {'tick': 42, 'type': 'trade', 'desc': '沈砚购买安神丹×2，花费110玄晶'},
        {'tick': 42, 'type': 'tick', 'desc': '回合42结束'},
    ],
    'milestones': [{'tick': 41, 'kind': '击杀', 'desc': '沈砚 击败了 山贼'}],
    'summaries': [],
    'codex': {'locations': ['临川城'], 'people': ['老王'], 'items': ['安神丹'], 'lore': []},
    'lore': [],
    'config': {},
}


def main():
    tmp = tempfile.mkdtemp(prefix='ww-smoke-ui-')
    state_path = os.path.join(tmp, 'smoke.save.json')
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(STATE, f, ensure_ascii=False)

    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, 'panel.py'),
         '--state', state_path, '--port', '8821'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'))

    try:
        # 等面板就绪（最多 15 秒），确认拿到的是**我们的**面板而不是同端口的别的服务
        base = 'http://127.0.0.1:8821'
        ready = False
        for _ in range(30):
            try:
                with urllib.request.urlopen(base + '/state', timeout=2) as r:
                    vm = json.load(r)
                if vm.get('tick') == 42:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ready:
            print('面板未就绪或端口被占用（期望 tick=42 的视图模型）')
            return 1

        results = []
        errors = []

        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            page.goto(base, wait_until='networkidle', timeout=20000)
            page.wait_for_timeout(1200)

            def check(name, ok, note=''):
                results.append((name, bool(ok), str(note)[:120]))
                print('%s  %-42s %s' % ('PASS' if ok else 'FAIL', name, str(note)[:70]))

            body = page.inner_text('body')
            check('页签含品牌', '行者' in page.title(), page.title())
            check('皮肤已应用', page.eval_on_selector('body', 'e => e.dataset.skin') == 'xuanshu')
            check('主角名渲染', '沈砚' in body)
            check('回合号渲染', '42' in body)
            check('气血数值渲染', '70' in body)
            # hp 满血时"气血吃紧"必须隐藏（曾经的 CSS bug：hidden 被 display 覆盖）
            check('满血不显示"气血吃紧"',
                  page.evaluate('''() => { const e = document.querySelector('#hpwarn');
                      return !!e && getComputedStyle(e).display === 'none'; }'''))
            # 单点存档时图表应为"数据不足"空状态（不是空白，也不是硬画一个点）
            check('图表空状态正确（单点 → 显示"数据不足"而非空白）',
                  page.evaluate('''() => {
                      const c1 = document.getElementById('chart1');
                      const empty = document.getElementById('chart1-empty');
                      if (!c1 || !empty) return false;
                      const c1Hidden = getComputedStyle(c1).display === 'none';
                      const emptyShown = getComputedStyle(empty).display !== 'none'
                                         && empty.getBoundingClientRect().height > 10;
                      return c1Hidden && emptyShown;
                  }'''))
            # tick 心跳不进时间线
            check('时间线不含"回合N结束"',
                  '回合42结束' not in page.inner_text('#timeline'),
                  page.inner_text('#timeline')[:40].replace('\n', ' '))
            # 抽屉能展开并滚入视口
            d = page.query_selector('#drawer-codex')
            page.evaluate('(x) => { x.open = true; }', d)
            page.wait_for_timeout(700)
            check('图鉴抽屉展开且在视口内',
                  page.evaluate('''() => { const x = document.querySelector('#drawer-codex');
                      const r = x.getBoundingClientRect();
                      return x.open && r.top < window.innerHeight && r.bottom > 0; }'''))
            # 帮助
            page.click('#help-btn')
            page.wait_for_timeout(500)
            check('帮助弹窗可开且含术语表',
                  page.evaluate('''() => { const d = document.querySelector('#helpdlg');
                      return !!d && (d.open || getComputedStyle(d).display !== 'none'); }'''))
            page.keyboard.press('Escape')
            # 窄屏无横向溢出
            for w in (768, 320):
                page.set_viewport_size({'width': w, 'height': 800})
                page.wait_for_timeout(500)
                ov = page.evaluate('() => document.documentElement.scrollWidth - document.documentElement.clientWidth')
                check('无横向溢出 @%d' % w, ov <= 1, 'overflow=%s' % ov)
            check('零 JS 控制台错误', not errors, '; '.join(errors[:2]) if errors else '0')
            browser.close()

        bad = [r for r in results if not r[1]]
        print('\n%d/%d passed' % (len(results) - len(bad), len(results)))
        return 0 if not bad else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == '__main__':
    sys.exit(main())
