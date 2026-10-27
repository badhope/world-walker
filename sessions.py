"""
存档会话 (Sessions) —— 多局管理、快照与可持续游玩

为什么需要：原内核一次只有一个"当前对局"，切换靠 `world_open` 记路径。玩家真正需要的是
一个**游戏库**：这局跑团、那局调查、第三局经营——各自的存档、快照、进度互不干扰。

设计：
  · 所有存档集中在一个目录（默认 `<状态文件所在目录>/saves/`，可用 `WORLD_GAMES_SAVES` 覆盖）；
  · 每个存档一个 `.save.json`，索引由目录实时扫描得出（不维护易漂移的索引文件）；
  · 快照 = `<name>.<tick>.snap.json`，与存档同目录；归档/回收站 = `.trash` 子目录；
  · 删除是"移入回收站"而不是物理删除（可回滚），清空回收站才是真删；
  · 本模块只碰文件系统，不写状态内容；状态写入仍由 MCP 的 save_state 单点负责。
"""

import json
import os
import re
import shutil
import time

SAFE_NAME = re.compile(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+")
MAX_NAME = 48
KEEP_SNAPSHOTS = 20
TRASH_DIR = ".trash"


def saves_root(base_dir: str = "") -> str:
    """存档库根目录：环境变量优先，其次 <base_dir>/saves，最后 ./saves。"""
    env = os.environ.get("WORLD_GAMES_SAVES", "").strip()
    if env:
        return os.path.abspath(env)
    base = os.path.abspath(base_dir or os.getcwd())
    return os.path.join(base, "saves")


def safe_name(name: str) -> str:
    """把用户给的局名变成安全文件名：保留中英文数字与 -_，其余折叠为 _。"""
    text = str(name or "").strip()
    if not text:
        raise ValueError("局名不能为空")
    text = SAFE_NAME.sub("_", text).strip("._-")
    if not text:
        raise ValueError("局名里至少要有字母、数字或中文")
    return text[:MAX_NAME]


def save_path(root: str, name: str, create_dir: bool = False) -> str:
    if create_dir:
        os.makedirs(root, exist_ok=True)
    return os.path.join(root, safe_name(name) + ".save.json")


def list_saves(root: str) -> list:
    """列出存档（只读扫描，不修改任何文件）。按最后写入时间倒序。"""
    if not os.path.isdir(root):
        return []
    rows = []
    for fname in os.listdir(root):
        if not fname.endswith(".save.json"):
            continue
        path = os.path.join(root, fname)
        try:
            st = os.stat(path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            rows.append({"name": fname[:-len(".save.json")], "path": path,
                         "broken": True, "bytes": 0, "mtime": 0})
            continue
        player = (data.get("entities") or {}).get("player") or {}
        rows.append({
            "name": fname[:-len(".save.json")],
            "path": path,
            "world": str((data.get("world_info") or {}).get("name") or ""),
            "tick": int(data.get("tick", 0) or 0),
            "player": str(player.get("name") or ""),
            "kind": str((data.get("game") or {}).get("kind") or ""),
            "bytes": st.st_size,
            "mtime": int(st.st_mtime),
            "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
            "broken": False,
        })
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return rows


def snapshot(state_path: str, label: str = "") -> dict:
    """给当前存档拍快照（同 tick 只保留一份；最多 KEEP_SNAPSHOTS 份）。"""
    if not os.path.exists(state_path):
        raise ValueError("存档不存在: %s" % state_path)
    with open(state_path, encoding="utf-8") as f:
        tick = int(json.load(f).get("tick", 0) or 0)
    base = state_path[:-len(".save.json")] if state_path.endswith(".save.json") else state_path
    tag = "".join(ch for ch in str(label or "") if ch.isalnum() or ch in "-_")[:24]
    stem = "%s.%06d%s" % (base, tick, ("-" + tag) if tag else "")
    dst = stem + ".snap.json"
    shutil.copyfile(state_path, dst)
    snaps = sorted(_glob_snapshots(base))
    for old in snaps[:-KEEP_SNAPSHOTS]:
        try:
            os.remove(old)
        except OSError:
            pass
    return {"snapshot": dst, "tick": tick, "kept": min(len(snaps), KEEP_SNAPSHOTS)}


def _glob_snapshots(base: str) -> list:
    folder = os.path.dirname(base) or "."
    prefix = os.path.basename(base) + "."
    if not os.path.isdir(folder):
        return []
    return [os.path.join(folder, f) for f in os.listdir(folder)
            if f.startswith(prefix) and f.endswith(".snap.json")]


def list_snapshots(state_path: str) -> list:
    base = state_path[:-len(".save.json")] if state_path.endswith(".save.json") else state_path
    rows = []
    for path in _glob_snapshots(base):
        try:
            st = os.stat(path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            tick = int(data.get("tick", 0) or 0)
        except (OSError, ValueError):
            continue
        rows.append({"path": path, "name": os.path.basename(path), "tick": tick,
                     "bytes": st.st_size, "updated": time.strftime("%Y-%m-%d %H:%M",
                                                                   time.localtime(st.st_mtime))})
    rows.sort(key=lambda r: (r["tick"], r["updated"]), reverse=True)
    return rows


def archive(root: str, state_path: str) -> dict:
    """把存档移入回收站（可还原，不物理删除）。"""
    if not os.path.exists(state_path):
        raise ValueError("存档不存在: %s" % state_path)
    trash = os.path.join(root, TRASH_DIR)
    os.makedirs(trash, exist_ok=True)
    dst = os.path.join(trash, os.path.basename(state_path))
    if os.path.exists(dst):
        dst = os.path.join(trash, "%s.%d" % (os.path.basename(state_path), int(time.time())))
    shutil.move(state_path, dst)
    return {"archived": dst, "name": os.path.basename(state_path)[:-len(".save.json")]}


def list_trash(root: str) -> list:
    trash = os.path.join(root, TRASH_DIR)
    if not os.path.isdir(trash):
        return []
    rows = []
    for fname in os.listdir(trash):
        if not fname.endswith(".save.json"):
            continue
        path = os.path.join(trash, fname)
        try:
            st = os.stat(path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        rows.append({"name": fname[:-len(".save.json")], "path": path,
                     "tick": int(data.get("tick", 0) or 0),
                     "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))})
    rows.sort(key=lambda r: r["updated"], reverse=True)
    return rows


def restore_from_trash(root: str, name: str) -> dict:
    trash = os.path.join(root, TRASH_DIR)
    src = os.path.join(trash, safe_name(name) + ".save.json")
    if not os.path.exists(src):
        raise ValueError("回收站里没有: %s" % name)
    os.makedirs(root, exist_ok=True)
    dst = os.path.join(root, safe_name(name) + ".save.json")
    if os.path.exists(dst):
        raise ValueError("同名存档已存在，不能覆盖: %s" % name)
    shutil.move(src, dst)
    return {"restored": dst, "name": safe_name(name)}


def purge_trash(root: str, name: str = "") -> dict:
    """清空回收站（危险：物理删除）。只删 .trash 目录内本程序管理的文件。"""
    trash = os.path.join(root, TRASH_DIR)
    if not os.path.isdir(trash):
        return {"removed": [], "count": 0}
    removed = []
    for fname in os.listdir(trash):
        if not fname.endswith(".save.json"):
            continue
        if name and fname != safe_name(name) + ".save.json":
            continue
        try:
            os.remove(os.path.join(trash, fname))
            removed.append(fname)
        except OSError:
            continue
    return {"removed": removed, "count": len(removed)}
