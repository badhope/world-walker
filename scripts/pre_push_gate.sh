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

# MCP 相关：只有装了 mcp SDK 才跑（与 CI 的 mcp 作业对应）
if "$PY" -c "import mcp" >/dev/null 2>&1; then
  step "MCP 端到端自检" "$PY" scripts/verify_mcp_stdio.py
  step "玩家视角试玩" "$PY" scripts/user_playtest.py
  step "长局压力测试（500 轮，对齐 CI 的 mcp 作业）" "$PY" scripts/stress_freeplay.py 500
else
  say $'\n=== MCP 作业 ===\n  SKIP（未安装 mcp SDK）'
  say '  注意：MCP 端到端 / 试玩 / 压测本次未执行，绿灯不代表这三项通过。'
  say '  安装后重跑：python -m pip install -e ".[mcp]"'
  FAILED=1
fi

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
