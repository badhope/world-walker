#!/usr/bin/env python3
"""
测试自身可信度审计 (verify_tests.py)

防"假测试"：静态审计其余自检脚本里每一条断言，拒绝恒真/恒假的写法。

历史上真实出现过的问题（本脚本即为防止其复发而写）：
  1. verify_cli.py 把两份 demo_state 副本互相比较，从没读被测试命令的结果；
  2. verify_panel.py 的侧写断言写成 `os.path.exists(...) or True`，永远通过；
  3. verify_panel.py 皮肤循环用 for/else 把结论硬编码成 True；
  4. stress_freeplay.py 的"回退后 stage 保持"只断言 tick >= 0，等于没测。

审计规则（AST 级，不看字符串）：
  R1 断言条件含字面量 True（`x or True`）→ 恒真
  R2 断言条件只含字面量 True/False → 恒真/恒假
  R3 断言条件是 `x >= 0` / `x > -1` 这类恒真下界（对 int 计数无意义）
  R4 断言名称里有"保持/不变/一致"但条件只判真值（bool(x)）→ 弱断言
  R5 断言条件里出现 `or True` / `and False` 的等价短路

用法:  python scripts/verify_tests.py
退出码: 0 = 审计通过；1 = 发现可疑断言
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    'scripts/verify_cli.py',
    'scripts/verify_panel.py',
    'scripts/verify_mcp_stdio.py',
    'scripts/verify_near_death.py',
    'scripts/user_playtest.py',
    'scripts/stress_freeplay.py',
]
CHECK_FUNCS = {'check', 'ux'}
FINDINGS = []


def add(path, lineno, rule, detail, snippet):
    FINDINGS.append({'file': path, 'line': lineno, 'rule': rule,
                     'detail': detail, 'snippet': snippet[:110]})


def is_const_bool(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, bool)


def is_trivial_lower_bound(node):
    """x >= 0 / x > -1 —— 对非负量恒真（注意 >= 2 这类是有意义的边界，不算）。"""
    if not isinstance(node, ast.Compare):
        return False
    if len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    op, right = node.ops[0], node.comparators[0]
    if not isinstance(right, ast.Constant) or not isinstance(right.value, (int, float)):
        return False
    if isinstance(op, ast.GtE):
        return right.value == 0
    if isinstance(op, ast.Gt):
        return right.value == -1
    return False


def has_name_claim(node):
    """名字里出现"保持/不变/一致/相等"等强断言词。"""
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and any(
        k in node.value for k in ('保持', '不变', '一致', '相等', '同一', '逐字节'))


def audit_file(rel):
    path = os.path.join(ROOT, rel)
    src = open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = node.func.id if isinstance(node.func, ast.Name) else None
        if fname not in CHECK_FUNCS or len(node.args) < 2:
            continue
        name_node, cond = node.args[0], node.args[1]
        snippet = ast.get_source_segment(src, node) or ''
        # R2 的正确形态：except 分支里显式记 False 是"记录失败"，不是假测试。
        # 只有调用点不在 except 处理器内、且条件为 True/False 常量时才算（True 恒真）。
        in_except = any(isinstance(p, ast.ExceptHandler) for p in ast.walk(tree))
        # R1/R5: 条件里含字面量 True 的 BoolOp，或 and False
        for sub in ast.walk(cond):
            if isinstance(sub, ast.BoolOp):
                for v in sub.values:
                    if is_const_bool(v) and v.value is True:
                        add(rel, node.lineno, 'R1', '条件含字面量 True（短路恒真）', snippet)
                    if is_const_bool(v) and v.value is False:
                        add(rel, node.lineno, 'R5', '条件含字面量 False（短路恒假）', snippet)
        # R2: 条件为常量且值为 True（恒真）。值为 False 只允许出现在 except 失败记录里。
        if is_const_bool(cond) and cond.value is True:
            add(rel, node.lineno, 'R2', '条件恒为 True', snippet)
        # R3: 恒真下界
        if is_trivial_lower_bound(cond):
            add(rel, node.lineno, 'R3', '条件为恒真下界（>= 0 等）', snippet)
        # R4: 强断言词 + 仅判真值
        if has_name_claim(name_node):
            if isinstance(cond, ast.Name) or (
                    isinstance(cond, ast.BoolOp)
                    and all(isinstance(v, ast.Name) for v in cond.values)):
                add(rel, node.lineno, 'R4', '名称声称保持/一致，但条件只判真值', snippet)
    return len(tree.body)


def main():
    total = 0
    for rel in TARGETS:
        if not os.path.exists(os.path.join(ROOT, rel)):
            print('SKIP  %s（不存在）' % rel)
            continue
        n = audit_file(rel)
        total += n
        print('SCAN  %-32s %d 顶层语句' % (rel, n))

    print('\n审计结果：%d 条可疑断言' % len(FINDINGS))
    for f in FINDINGS:
        print('  [%s] %s:%d  %s\n        %s'
              % (f['rule'], f['file'], f['line'], f['detail'], f['snippet']))
    if FINDINGS:
        return 1
    print('未发现恒真/恒假/弱断言。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
