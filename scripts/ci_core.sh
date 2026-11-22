#!/usr/bin/env bash
# Canonical zero-dependency core suite.
#
# GitHub, Gitee and GitCode used to spell this list out three times; every new
# regression had to be added in three YAML dialects and the lists drifted.
# Keep the order here, let each runner only supply its own Python executable.
set -euo pipefail
PYTHON="${PYTHON:-python}"

run() {
  echo "── $* ──"
  "$PYTHON" "$@"
}

for suite in \
  compile_all \
  verify_tests \
  run_behavior_regressions \
  verify_cli \
  verify_panel \
  verify_harness \
  verify_player_shell \
  verify_near_death \
  verify_formulas \
  verify_branches \
  verify_world \
  verify_settings \
  verify_surface \
  verify_mechanics \
  verify_replay \
  verify_docs \
  verify_domain_model \
  verify_gameplay \
  verify_generic \
  verify_systems
do
  run "scripts/${suite}.py"
done

run scripts/metrics.py --check
echo "core suite passed"
