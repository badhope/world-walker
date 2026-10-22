#!/usr/bin/env bash
#
# 推送前门禁（pre-push gate）
#
# 为什么需要：GitHub Actions 已在三个账号上跑（8 作业 / 85 步全绿），
# 但 GitCode 与 Gitee 不提供可编程 CI（API 全部 404，无 Actions / Pipelines 服务）。
# 为保证三平台代码质量一致，所有推送前在本机跑同一套判据——推上去的代码
# 必然已经通过 GitHub Actions 会跑的那些检查。
#
# 安装： bash scripts/install_git_hooks.sh
# 跳过： git push --no-verify（不推荐）

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

PY="${PYTHON:-python}"
FAILED=0

say() { printf '%s\n' "$*"; }
step() {
  printf '\n=== %s ===\n' "$1"
  shift
  if "$@" > /tmp/ww-gate.log 2>&1; then
    say "  PASS"
  else
    say "  FAIL（输出尾 20 行）"
    tail -20 /tmp/ww-gate.log | sed 's/^/    /'
    FAILED=1
  fi
}

say "推送前门禁：判据与 GitHub Actions 一致（含 500 轮压测 + 打包校验）"
say "仓库：$ROOT"

step "编译全部 Python 源" "$PY" scripts/compile_all.py
step "断言审计（拒绝恒真/恒假/弱断言）" "$PY" scripts/verify_tests.py
step "CLI 通道自检" "$PY" scripts/verify_cli.py
step "面板契约自检" "$PY" scripts/verify_panel.py
step "濒死保护自检" "$PY" scripts/verify_near_death.py
step "规则内核公式对拍（77 个函数的闭式复算）" "$PY" scripts/verify_formulas.py
step "模块分支补测（systems/narrative/cognition/economy）" "$PY" scripts/verify_branches.py
step "长局内存稳定性（三段对照，查泄漏）" "$PY" scripts/verify_memory.py 300

# 覆盖率门禁：核心域 ≥70%（当前 81%）。装了 coverage 才跑。
if "$PY" -c "import coverage" >/dev/null 2>&1; then
  say $'
=== 覆盖率门禁（核心域 ≥70%）==='
  rm -rf "$ROOT/.cov-gate"
  COV_OK=1
  for suite in verify_formulas verify_branches verify_cli verify_panel verify_near_death; do
    "$PY" -m coverage run --data-file="$ROOT/.cov-gate" --append       --source=rules,panel,state_schema "$ROOT/scripts/$suite.py" >/dev/null 2>&1 || COV_OK=0
  done
  PCT=$("$PY" -m coverage report --data-file="$ROOT/.cov-gate" 2>/dev/null         | awk '/^TOTAL/ {gsub("%","",$NF); print $NF}')
  rm -rf "$ROOT/.cov-gate"
  # 用 Python 比较（bc 在 Git Bash 里通常不存在）
  if [ -n "$PCT" ] && "$PY" -c "import sys; sys.exit(0 if float('$PCT') >= 70 else 1)"; then
    say "  PASS（${PCT}%）"
  else
    say "  FAIL（覆盖率 ${PCT:-未知}% < 70%）"
    FAILED=1
  fi
else
  say $'
=== 覆盖率门禁 ===
  SKIP（未安装 coverage）'
fi

# MCP 相关：只有装了 mcp SDK 才跑（与 CI 的 mcp 作业对应）
if "$PY" -c "import mcp" >/dev/null 2>&1; then
  step "MCP 端到端自检" "$PY" scripts/verify_mcp_stdio.py
  step "提示词注入防护（角色卡/世界书 untrusted 标记）" "$PY" scripts/verify_injection.py
  step "玩家视角试玩" "$PY" scripts/user_playtest.py
  step "长局压力测试（500 轮，对齐 CI 的 mcp 作业）" "$PY" scripts/stress_freeplay.py 500
else
  say $'\n=== MCP 作业 ===\n  SKIP（未安装 mcp SDK）'
  say '  注意：MCP 端到端 / 试玩 / 压测本次未执行，绿灯不代表这三项通过。'
  say '  安装后重跑：python -m pip install -e ".[mcp]"'
  FAILED=1
fi

# 界面巡检：需要 Playwright + 浏览器；装了才跑（未装时跳过但明确提示，不算绿）
if "$PY" -c "import playwright" >/dev/null 2>&1; then
  say $'
=== 界面巡检 ==='
  STEP_RC=0
  "$PY" scripts/smoke_ui.py > /tmp/ww-ui.log 2>&1 || STEP_RC=$?
  if [ "$STEP_RC" -eq 0 ]; then say "  PASS"; else
    say "  FAIL（输出尾 20 行）"; tail -20 /tmp/ww-ui.log | sed 's/^/    /'; FAILED=1
  fi
else
  say $'
=== 界面巡检 ===
  SKIP（未安装 playwright）'
fi

# 真变异测试：把实现改坏，确认测试会红（静态审计之外的唯一硬证据）
step "变异测试（已知错误必须被测试杀死）" "$PY" scripts/verify_mutation.py

# 打包完整性：对齐 CI 的 package 作业（构建 + wheel 资源校验）
# 本机可能无外网 PyPI，构建时不做隔离环境（CI 上有网，用默认隔离即可）
step "构建 sdist + wheel" "$PY" -m build --no-isolation --outdir "$ROOT/.gate-dist"
step "校验 wheel 运行时资源齐全" "$PY" scripts/check_wheel.py "$ROOT/.gate-dist"
rm -rf "$ROOT/.gate-dist"

if [ "$FAILED" -ne 0 ]; then
  say $'\n推送被门禁拦下：请先修复上面的失败项。'
  exit 1
fi
say $'\n门禁全绿，允许推送。'
exit 0
