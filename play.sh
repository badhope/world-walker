#!/bin/bash
# 万界 · 行者 — 快速启动脚本
# ./play.sh           运行所有命令演示
# ./play.sh --state F  指定状态文件 (默认 game_state.json)

# 参数解析：支持 `./play.sh combat`、`./play.sh combat --state F`、
# `./play.sh --state F combat` 三种写法（旧实现固定取 $2，会把 `--state` 当文件名）。
STATE="game_state.json"
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --state)
      STATE="${2:-game_state.json}"
      shift 2 || shift
      ;;
    --state=*)
      STATE="${1#--state=}"
      shift
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done
set -- "${ARGS[@]}"
CMD="${1:-}"
shift || true

if [ ! -f "$STATE" ]; then
  echo "状态文件不存在: $STATE（先跑 ./play.sh init 生成）" >&2
  exit 1
fi

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
export PYTHONPATH=.

echo "=== 万界 · 行者 | 第 $("$PY" -c "import json;print(json.load(open('$STATE')).get('tick',0))") 回合 ==="
echo ""

case "$CMD" in
  combat)
    "$PY" engine.py combat --state "$STATE" --attacker player --defender "${3:-goblin}"
    ;;
  trade)
    "$PY" engine.py trade --state "$STATE" --location "${3:-bamboo_tea_booth}" --item "${4:-an_zhen_san}" --quantity "${5:-1}" --direction "${6:-buy}" --entity player
    ;;
  social)
    "$PY" engine.py social --state "$STATE" --actor player --target "${3:-old_chen}" --event "${4:-help}"
    ;;
  karma)
    "$PY" engine.py karma --state "$STATE" --actor player --karma_type "${3:-help_innocent}"
    ;;
  tick)
    "$PY" engine.py tick --state "$STATE"
    ;;
  world)
    "$PY" engine.py world_state --state "$STATE"
    ;;
  narrative)
    "$PY" engine.py narrative --state "$STATE"
    ;;
  flow)
    "$PY" engine.py flow --state "$STATE"
    ;;
  panarchy)
    "$PY" engine.py panarchy --state "$STATE"
    ;;
  identity)
    "$PY" engine.py identity --state "$STATE"
    ;;
  moral)
    "$PY" engine.py moral_update --state "$STATE"
    ;;
  cognition)
    "$PY" engine.py cognition --state "$STATE" --entity player
    ;;
  merit)
    "$PY" engine.py merit --state "$STATE" --aid "${3:-1.0}" --sincerity "${4:-1.0}"
    ;;
  info)
    "$PY" engine.py info_weight --state "$STATE" --probability "${3:-0.1}"
    ;;
  init)
    "$PY" init_game.py
    ;;
  *)
    echo "用法: ./play.sh <command> [--state FILE] [args]"
    echo ""
    echo "可用命令:"
    echo "  combat    trade    social    karma     tick"
    echo "  world     narrative  flow    panarchy  identity"
    echo "  moral     cognition  merit   info      init"
    ;;
esac
