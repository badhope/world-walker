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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 每条：(编号, 说明, 目标文件, 原文片段, 替换片段, 应该失败的验证脚本)
# 片段必须是**唯一出现**的，且改动语义明确（不是格式化）。
MUTATIONS = [
    # ── 战斗 ──
    ('M01', '濒死保底 1 → 0', 'rules/combat.py',
     '    player["hp"] = 1\n    gold = int(player.get("gold", 0) or 0)',
     '    player["hp"] = 0\n    gold = int(player.get("gold", 0) or 0)',
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
     '    "theft": 15,', '    "theft": 0,',
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

    # ── 世界演化（本轮新增；每条对应一个曾经的"展示但不生效"缺陷）──
    ('M20', 'tick 不再驱动世界演化', 'mcp_server.py',
     '    world = evolve_world(state)', '    world = {}',
     'scripts/verify_world.py'),
    # 注意：M20 曾经**存活**——verify_world 的 W11 走了 in-process 调用，而变异点
    # 在 stdio 之外的同名文件里，两处都能命中；真正让它变红的是同一条断言在本文件
    # （MCP tick 工具）里跑，因此 M20 的目标脚本必须是 verify_world（含 W11 in-process）。
    ('M26', '只读工具偷偷落盘（status 顺手 save_state）', 'mcp_server.py',
     '    result["_tick"] = int((_load().get("tick", 0)) or 0)\n    return result',
     '    result["_tick"] = int((_load().get("tick", 0)) or 0)\n    save_state(_load(), _state_path())\n    return result',
     'scripts/verify_mcp_stdio.py'),
    ('M27', 'CLI tick 退回只推市价（不驱动世界）', 'engine.py',
     '    world = evolve_world(state)\n    for desc in world.get("events", []):',
     '    world = {}\n    for desc in world.get("events", []):',
     'scripts/verify_cli.py'),
    ('M28', '死目标继续进编年史（噪声复现）', 'mcp_server.py',
     '    if not result.get("target_already_dead"):\n        for e in result.get("events", []):',
     '    if True:\n        for e in result.get("events", []):',
     'scripts/verify_mcp_stdio.py'),
    ('M29', '行动队列不设上限（侧写无限增长）', 'panel.py',
     '    if len(pending) > INBOX_MAX_PENDING:',
     '    if False:',
     'scripts/verify_panel.py'),
    ('M30', '行动队列接受跨站请求（去掉 Origin 校验）', 'panel.py',
     "        if origin and origin.split('//')[-1] != host:",
     '        if False:',
     'scripts/verify_panel.py'),
    ('M31', '文档版本号与 pyproject 漂移', 'pyproject.toml',
     'version = "1.0.0"', 'version = "0.9.9"',
     'scripts/verify_docs.py'),
    ('M32', 'README 宣称的工具数与源码不符', 'README.md',
     '## MCP 工具一览（34 个）', '## MCP 工具一览（99 个）',
     'scripts/verify_docs.py'),
    ('M21', '相位不再影响事件概率', 'rules/narrative_engine.py',
     '    return PHASE_EVENT_MULT.get(_phase_key(state), 1.0)',
     '    return 1.0',
     'scripts/verify_world.py'),
    ('M22', '心流不再影响命中（修正失效）', 'rules/combat.py',
     '        hit_mult *= max(0.75, min(1.25, 1.0 - adj * 0.5))',
     '        hit_mult *= 1.0',
     'scripts/verify_world.py'),
    ('M23', '暴击重新被算成失败', 'rules/narrative_engine.py',
     '    if "命中" in desc or "暴击" in desc or "击败" in desc or "逃跑成功" in desc:',
     '    if "命中" in desc or "击败" in desc or "逃跑成功" in desc:',
     'scripts/verify_world.py'),
    ('M24', '道德画像改用中文名查英文键（永远全 0）', 'panel.py',
     '        return [int(vec.get(k, 0)) for k in ENGINE_DIMS]',
     '        return [int(vec.get(d, 0)) for d in MORAL_DIMS]',
     'scripts/verify_world.py'),
    ('M25', '台账重新只裁已结算（未结算无上限）', 'state_schema.py',
     '    over = len(ledger) - cap + 1', '    over = 0',
     'scripts/verify_world.py'),
]


def purge_pycache(target_path):
    """删掉目标文件所在的 __pycache__。

    为什么必须做：变异→跑测试→还原通常在同一个 mtime 秒内完成，
    Python 的 pyc 失效判断基于 (mtime, size)。还原后 size 与 mtime 都可能
    与变异前一致，导致后续运行**继续使用变异版的字节码**——
    表现为"源码正确但函数返回错误值"（本轮就因此让 CI 挂掉）。
    """
    import shutil as _sh
    d = os.path.join(os.path.dirname(target_path), '__pycache__')
    if os.path.isdir(d):
        _sh.rmtree(d, ignore_errors=True)


def run_script(rel):
    """跑一个验证脚本，返回是否通过（exit 0）。"""
    r = subprocess.run([sys.executable, os.path.join(ROOT, rel)],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode == 0, (r.stdout or '')[-300:]


def _match_eol(fragment, src):
    """把片段里的 \\n 换成目标文件实际用的行尾（Windows 上源码是 CRLF）。

    不做这一步的话，任何**跨行**的变异片段在 CRLF 文件里都匹配不到，
    脚本只会打一行 SKIP 就跳过——变异测试看起来仍然"全绿"，
    实际上那条规则从没被验证过（本轮实测 M01 就是这样被静默跳过的）。
    """
    if '\r\n' in src and '\r\n' not in fragment:
        return fragment.replace('\n', '\r\n')
    return fragment


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
        old = _match_eol(old, src)
        new = _match_eol(new, src)
        if src.count(old) != 1:
            # 片段对不上 = 这条"已知错误"从未被真正验证过。静默跳过会让变异测试
            # 看起来全绿而实际漏测（本项目历史上真发生过），所以按失败处理。
            print('SKIP  %s %-44s 片段不唯一（出现 %d 次）' % (mid, desc, src.count(old)))
            total += 1
            survivors.append((mid, desc + '（片段已失效，需更新）', script))
            continue

        total += 1
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(src.replace(old, new, 1))
            purge_pycache(path)          # 变异前清缓存，确保跑到变异版
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
            purge_pycache(path)          # 还原后清缓存，避免残留变异字节码

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
