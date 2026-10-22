#!/usr/bin/env python3
"""
真变异测试 (verify_mutation.py)

为什么需要：`scripts/verify_tests.py` 是**静态 AST 审计**，只能识别已知的
9 类假写法。审查报告 F-002 指出：理论上总能找到新绕过。真正的信任来源
只有一个——**把实现改坏，看测试会不会红**。本脚本就是这件事的自动化。

做法：
  1. 从 `MUTATIONS` 表里逐条取一个"已知正确的单点改动"（如 `>` 改 `>=`、
     常数 ×2、删掉一条赋值），在临时副本上应用
  2. 跑指定的验证脚本；**期望它失败**
  3. 若脚本仍全绿 → 该变异"存活" → 说明测试漏掉了这个错误 → 记为 FAIL
  4. 全部复原（用 git checkout，绝不留下改动）

存活率 = 存活数 / 总数；红线：存活率必须为 0。

用法:  python scripts/verify_mutation.py [--quick]
退出码: 0 = 所有变异都被杀死；1 = 有存活变异
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 每条：(编号, 说明, 目标文件, 原文片段, 替换片段, 应该失败的验证脚本)
# 片段必须是**唯一出现**的，且改动语义明确（不是格式化）。
MUTATIONS = [
    # ── 战斗 ──
    ('M01', '濒死保底 1 → 0', 'rules/combat.py',
     '    player["hp"] = 1\n', '    player["hp"] = 0\n',
     'scripts/verify_near_death.py'),
    ('M02', '濒死不掉钱（gold_lost 置 0）', 'rules/combat.py',
     '    gold_lost = int(gold * 0.30)', '    gold_lost = 0',
     'scripts/verify_near_death.py'),
    ('M03', 'NPC 死亡不判定', 'rules/combat.py',
     '            result["defender_dead"] = True', '            result["defender_dead"] = False',
     'scripts/verify_near_death.py'),

    # ── 经济 ──
    ('M04', '买入不扣钱', 'rules/economy.py',
     '        ent["gold"] -= total', '        ent["gold"] -= 0',
     'scripts/verify_cli.py'),
    ('M05', '买入不入库', 'rules/economy.py',
     '        _add_items(ent, item, quantity)', '        pass',
     'scripts/verify_mcp_stdio.py'),
    ('M06', '买入不减库存', 'rules/economy.py',
     '        item_data["supply"] -= quantity', '        pass',
     'scripts/verify_cli.py'),

    # ── 社交 / 因果 ──
    ('M07', '社交增益翻倍', 'rules/social.py',
     '        "help":       (5, 3),', '        "help":       (10, 3),',
     'scripts/verify_cli.py'),
    ('M08', '因果 theft 记错金额', 'rules/karma.py',
     '        "theft": 15,', '        "theft": 0,',
     'scripts/verify_cli.py'),

    # ── 模型层公式 ──
    ('M09', 'Lerner 分母 ε-1 → ε+1', 'rules/models.py',
     '    return cogs * elasticity / (elasticity - 1.0)',
     '    return cogs * elasticity / (elasticity + 1.0)',
     'scripts/verify_formulas.py'),
    ('M10', 'Cobb-Douglas 指数对调', 'rules/models.py',
     '    return A * (L ** alpha) * (K ** beta)', '    return A * (L ** beta) * (K ** alpha)',
     'scripts/verify_formulas.py'),
    ('M11', 'SIR 恢复项符号反向', 'rules/models.py',
     '    i2 = max(0.0, i + flow - recov)', '    i2 = max(0.0, i + flow + recov)',
     'scripts/verify_formulas.py'),

    # ── 认知 ──
    ('M12', '前景理论损失放大系数失效', 'rules/cognition.py',
     '        return -lam * ((-change) ** beta)', '        return -1.0 * ((-change) ** beta)',
     'scripts/verify_formulas.py'),
    ('M13', '认知预算"正常"档系数 1.0 → 1.1', 'rules/cognition.py',
     '"正常": 1.0,', '"正常": 1.1,',
     'scripts/verify_formulas.py'),

    # ── 世界动力学 ──
    ('M14', 'Shannon 熵漏掉负号', 'rules/world_dynamics.py',
     '            H -= p * math.log(p, base)', '            H += p * math.log(p, base)',
     'scripts/verify_formulas.py'),

    # ── 归档/回退（数据完整性）──
    ('M15', '回退后 archived_events 不校正（历史计数退步）', 'mcp_server.py',
     '    state["archived_events"] = max(int(state.get("archived_events", 0) or 0), total)',
     '    state["archived_events"] = int(state.get("archived_events", 0) or 0)',
     'scripts/verify_mcp_stdio.py'),

    # ── 注入防护 ──
    ('M16', '注入扫描永不放行（全返回空）', 'mcp_server.py',
     '    for pat in _INJECTION_PATTERNS:', '    for pat in []:',
     'scripts/verify_injection.py'),
    ('M17', '外部内容不再标记 untrusted', 'mcp_server.py',
     '                            "untrusted": True,', '                            "untrusted": False,',
     'scripts/verify_injection.py'),

    # ── 面板视图模型 ──
    ('M18', '时间线不再合并重复事件', 'panel.py',
     'for e in _merge_adjacent(raw)[-EVENTS_CAP:]]', 'for e in raw[-EVENTS_CAP:]]',
     'scripts/verify_panel.py'),
    ('M19', '价格指数不再取均值', 'viz_series.py',
     '        "price_index": round(sum(ratios) / len(ratios), 4) if ratios else 1.0,',
     '        "price_index": 1.0,',
     'scripts/verify_panel.py'),
]


def run_script(rel):
    """跑一个验证脚本，返回是否通过（exit 0）。"""
    r = subprocess.run([sys.executable, os.path.join(ROOT, rel)],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode == 0, (r.stdout or '')[-300:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='只跑某个编号，如 M01')
    args = ap.parse_args()

    if shutil.which('git') is None:
        print('需要 git 来安全回滚改动')
        return 2

    total = killed = 0
    survivors = []

    for mid, desc, target, old, new, script in MUTATIONS:
        if args.only and args.only != mid:
            continue
        path = os.path.join(ROOT, target)
        # newline='' 保留原行尾：否则 Python 默认会做 universal newlines，
        # 写回时把整个文件的行尾改掉（LF→CRLF），在 git 里显示为整文件重写。
        with open(path, encoding='utf-8', newline='') as f:
            src = f.read()
        if src.count(old) != 1:
            print('SKIP  %s %-44s 片段不唯一（出现 %d 次）' % (mid, desc, src.count(old)))
            continue

        total += 1
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(src.replace(old, new, 1))
            passed, tail = run_script(script)
            if passed:
                survivors.append((mid, desc, script))
                print('SURVIVED  %s  %-46s → %s 仍全绿' % (mid, desc, script))
            else:
                killed += 1
                print('KILLED    %s  %-46s → %s 变红 ✓' % (mid, desc, script))
        finally:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(src)

    print('\n变异：%d 个 · 杀死 %d · 存活 %d' % (total, killed, len(survivors)))
    if total and survivors:
        print('存活率 %.0f%%（红线 0%%）' % (100.0 * len(survivors) / total))
        print('存活变异说明测试漏掉了这些错误：')
        for mid, desc, script in survivors:
            print('  - %s %s（%s 未发现）' % (mid, desc, script))
        return 1
    print('所有变异都被测试杀死（存活率 0%）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
