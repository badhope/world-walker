#!/usr/bin/env python3
"""
玩家壳契约自检 (verify_player_shell.py)

验证 A 玩家版的三条硬约束：
  1. 新壳能被服务：/、panel.css、panel.js 200；旧控制台/翻译/主题入口 404。
  2. 玩家 API 有完整数据：bootstrap / state / saves，且当前局不会从大厅消失。
  3. 新局与模型配置可用：模板开局写进存档库；Key 只以掩码出现；存档仍只读。

用法: python scripts/verify_player_shell.py
退出码: 0 = 全绿；1 = 有失败项
"""

import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []


def check(name, ok, note=""):
    RESULTS.append(bool(ok))
    print("%s  %-56s %s" % ("PASS" if ok else "FAIL", name, note))


def http(method, url, payload=None, timeout=10):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", "") if exc.headers else "", exc.read()
    except Exception as exc:  # noqa: BLE001 - probe failures must become assertions
        return 0, "", str(exc).encode("utf-8")


def get_json(url):
    status, _ctype, body = http("GET", url)
    try:
        return status, json.loads(body.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return status, None


def post_json(url, payload):
    status, _ctype, body = http("POST", url, payload)
    try:
        return status, json.loads(body.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return status, None


def main():
    temp = tempfile.mkdtemp(prefix="ww-player-shell-")
    original_env = {key: os.environ.get(key) for key in
                    ("WORLD_GAMES_SAVES", "WW_MODEL_CONFIG")}
    srv = None
    try:
        shutil.copyfile(os.path.join(ROOT, "docs", "demo", "折剑行.save.json"),
                        os.path.join(temp, "折剑行.save.json"))
        os.environ["WORLD_GAMES_SAVES"] = os.path.join(temp, "saves")
        os.environ["WW_MODEL_CONFIG"] = os.path.join(temp, "model.json")

        spec = importlib.util.spec_from_file_location("panel", os.path.join(ROOT, "panel.py"))
        panel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(panel)
        srv, port = panel.start(os.path.join(temp, "折剑行.save.json"), port=0)
        base = "http://127.0.0.1:%d" % port

        for path in ("/", "/panel.html", "/panel.css", "/panel.js"):
            status, ctype, body = http("GET", base + path)
            check("静态资源 %s 可访问" % path,
                  status == 200 and len(body) > 0 and ("html" in ctype or "css" in ctype or "javascript" in ctype),
                  "%s %s bytes" % (status, len(body)))
        for path in ("/state", "/admin", "/panel.i18n.js", "/panel.theme.js", "/assets/echarts.min.js"):
            status, _ctype, _body = http("GET", base + path)
            check("旧入口 %s 已下线" % path, status == 404, str(status))

        status, health = get_json(base + "/api/v1/health")
        check("health 返回 v1", status == 200 and health and health.get("api") == "v1")
        status, boot = get_json(base + "/api/v1/bootstrap")
        check("bootstrap 返回世界目录与当前局",
              status == 200 and boot and boot.get("worlds") and boot.get("current"),
              "%d worlds" % len((boot or {}).get("worlds") or []))
        check("当前局出现在大厅存档列表",
              any(row.get("current") for row in ((boot or {}).get("saves") or [])))
        featured = (boot or {}).get("featured") or []
        check("大厅有三张旗舰开局卡",
              len(featured) == 3 and all(row.get("id") and row.get("title") and row.get("pitch")
                                         for row in featured),
              str([row.get("id") for row in featured]))

        status, view = get_json(base + "/api/v1/state")
        check("state 是玩家视图",
              status == 200 and view and view.get("feed") and view.get("rail")
              and view.get("player", {}).get("name") == "顾青",
              "%d feed rows" % len((view or {}).get("feed") or []))
        check("feed 不再包含旧仪表盘尾巴",
              all("刚才发生的事还压在心上" not in (row.get("text") or "")
                  for row in ((view or {}).get("feed") or [])))
        moves = (((view or {}).get("rail") or {}).get("quests") or {}).get("next_moves") or []
        check("下一步提示不重复任务目标",
              all((row or {}).get("kind") != "quest" for row in moves),
              str([row.get("text") for row in moves]))
        check("模型默认未配置", not (view or {}).get("model", {}).get("configured"))

        state_path = os.path.join(temp, "折剑行.save.json")
        status, replay = get_json(base + "/api/v1/replay")
        check("战报回放返回时间线",
              status == 200 and replay and replay.get("format") == "world-walker.replay.v1"
              and isinstance(replay.get("timeline"), list) and replay.get("counts", {}).get("total") >= 1,
              str((replay or {}).get("counts")))

        status, ctype, story = http("GET", base + "/api/v1/export?kind=story")
        check("战报导出是 Markdown，不是 JSON",
              status == 200 and "markdown" in ctype and story.startswith(b"# ")
              and b"World Walker" in story,
              "%s %d bytes" % (ctype, len(story)))

        status, _ctype, world_body = http("GET", base + "/api/v1/export?kind=world")
        try:
            pack = json.loads(world_body.decode("utf-8"))
        except Exception:  # noqa: BLE001
            pack = None
        check("世界包导出格式正确且含快照",
              status == 200 and pack and pack.get("format") == "world-walker.worldpack.v1"
              and isinstance(pack.get("snapshot"), dict) and pack.get("contains_spoilers") is True,
              (pack or {}).get("format", ""))

        status, _ctype, card_body = http("GET", base + "/api/v1/export?kind=character")
        try:
            card = json.loads(card_body.decode("utf-8"))
        except Exception:  # noqa: BLE001
            card = None
        check("角色卡导出为 chara_card_v2",
              status == 200 and card and card.get("spec") == "chara_card_v2"
              and (card.get("data") or {}).get("name") == "顾青",
              (card or {}).get("spec", ""))

        status, imported = post_json(base + "/api/v1/import/world",
                                     {"pack": pack, "name": "世界包导入验收"})
        imported_path = ((imported or {}).get("created") or {}).get("state_path") or ""
        check("世界包可导入成新存档",
              status == 200 and imported and imported.get("ok")
              and os.path.isfile(imported_path),
              imported_path or str((imported or {}).get("error", "")))
        status, imported_view = get_json(base + "/api/v1/state")
        check("导入后当前局切到副本",
              status == 200 and imported_view
              and imported_view.get("world", {}).get("name") == "折剑行",
              str((imported_view or {}).get("world", {}).get("name")))

        before = hashlib.sha256(open(state_path, "rb").read()).hexdigest()

        status, card_import = post_json(base + "/api/v1/import/character", {
            "card": {"spec": "chara_card_v2", "spec_version": "2.0",
                     "data": {"name": "测试旅人", "description": "雨里走进来的人，鞋底沾着白灰。",
                              "personality": "少话，先看门后看人。"}},
            "entity_id": "test_traveler",
        })
        check("角色卡 JSON 可导入当前对局",
              status == 200 and card_import and card_import.get("ok")
              and (card_import.get("result") or {}).get("name") == "测试旅人"
              and (card_import.get("result") or {}).get("entity_id") == "test_traveler",
              str((card_import or {}).get("error", "")))

        status, created = post_json(base + "/api/v1/new",
                                    {"kind": "template", "id": "tabletop", "name": "门禁新局"})
        new_path = ((created or {}).get("created") or {}).get("state_path") or ""
        check("模板新局成功", status == 200 and created and created.get("ok") and os.path.isfile(new_path),
              new_path)
        check("新局写进当前存档库", os.path.abspath(new_path).startswith(os.path.abspath(temp)))

        status, saved = post_json(base + "/api/v1/model/config",
                                  {"base_url": "https://gateway.example/v1",
                                   "model": "any-model", "api_key": "sk-test-secret-12345678"})
        model = (saved or {}).get("model") or {}
        check("模型配置保存成功", status == 200 and model.get("configured"))
        check("Key 只返回掩码", "sk-test-secret-12345678" not in json.dumps(saved)
              and model.get("api_key_masked"))
        config_path = os.path.join(temp, "model.json")
        mode = os.stat(config_path).st_mode & 0o777 if os.path.exists(config_path) else None
        check("模型配置文件权限 0600", mode == 0o600, oct(mode) if mode is not None else "missing")
        status, boot2 = get_json(base + "/api/v1/bootstrap")
        check("大厅模型状态已更新", (boot2 or {}).get("model", {}).get("configured") is True)

        after = hashlib.sha256(open(state_path, "rb").read()).hexdigest()
        check("读取接口不修改当前存档", before == after)
        check("旧存档仍可打开", get_json(base + "/api/v1/state")[0] == 200)

        # 三张旗舰卡不是只有标题：每张开局都必须带序章、三枚动作和随身物品。
        for row in featured:
            status, flagship = post_json(base + "/api/v1/new", {
                "kind": (row.get("world") or {}).get("kind") or "setting",
                "id": (row.get("world") or {}).get("id") or "",
                "name": "旗舰-" + str(row.get("id")),
                "narrative": {"genre": row.get("genre"), "play": row.get("play"),
                              "mode": row.get("mode_default"), "role": row.get("role") or "preset"},
            })
            fstate = (flagship or {}).get("state") or {}
            brief = ((fstate.get("narrative") or {}).get("brief") or {})
            inventory = (fstate.get("player") or {}).get("inventory") or []
            check("旗舰 %s 开局有序章、三动作和随身物品" % row.get("id"),
                  status == 200 and flagship and flagship.get("ok")
                  and len(brief.get("prologue") or []) >= 3
                  and len(brief.get("opening_actions") or []) == 3
                  and len(inventory) >= 1,
                  "prologue=%d actions=%d items=%d" % (
                      len(brief.get("prologue") or []),
                      len(brief.get("opening_actions") or []), len(inventory)))
    finally:
        if srv is not None:
            panel.stop(srv)
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(temp, ignore_errors=True)

    failed = RESULTS.count(False)
    print("\n%d/%d 通过" % (len(RESULTS) - failed, len(RESULTS)))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
