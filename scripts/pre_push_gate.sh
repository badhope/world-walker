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

say "推送前门禁：与 GitHub Actions 同一套判据"
say "仓库：$ROOT"

step "编译全部 Python 源" "$PY" -m compileall -q . -x '/(\.git|__pycache__|dist|build)/'
step "断言审计（拒绝恒真/恒假/弱断言）" "$PY" scripts/verify_tests.py
step "CLI 通道自检" "$PY" scripts/verify_cli.py
step "面板契约自检" "$PY" scripts/verify_panel.py
step "濒死保护自检" "$PY" scripts/verify_near_death.py

# MCP 相关：只有装了 mcp SDK 才跑（与 CI 的 mcp 作业对应）
if "$PY" -c "import mcp" >/dev/null 2>&1; then
  step "MCP 端到端自检" "$PY" scripts/verify_mcp_stdio.py
  step "玩家视角试玩" "$PY" scripts/user_playtest.py
else
  say $'\n=== MCP 作业 ===\n  SKIP（未安装 mcp SDK，CI 里有独立作业覆盖）'
fi

if [ "$FAILED" -ne 0 ]; then
  say $'\n推送被门禁拦下：请先修复上面的失败项。'
  exit 1
fi
say $'\n门禁全绿，允许推送。'
exit 0
