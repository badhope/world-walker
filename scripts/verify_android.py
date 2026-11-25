#!/usr/bin/env python3
"""Verify the Android package without needing a phone attached.

Checks the staged runtime zip, the signed APK's manifest/native payload, and
boots the exact same Python host used by the APK against the extracted runtime.
That covers the two failure classes which static APK inspection misses:
missing resources and a panel that cannot start from app-private paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID = ROOT / "android"
ASSETS = ANDROID / "app" / "src" / "main" / "assets"
RUNTIME = ASSETS / "runtime.zip"
DIST = ROOT / "dist" / "android"
VERSION = re.search(r'__version__\s*=\s*["\']([^"\']+)',
                    (ROOT / "__init__.py").read_text(encoding="utf-8")).group(1)
PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, okay: bool, detail: str = "") -> None:
    (PASS if okay else FAIL).append(name + (("  " + detail) if detail else ""))
    print(("PASS  " if okay else "FAIL  ") + name + (("  " + detail) if detail else ""))


def runtime_check() -> None:
    check("runtime.zip 已生成", RUNTIME.is_file(), "%.1f KB" % (RUNTIME.stat().st_size / 1024) if RUNTIME.is_file() else "")
    if not RUNTIME.is_file():
        return
    with zipfile.ZipFile(RUNTIME) as zf:
        names = set(zf.namelist())
        required = [
            "game_engine/__init__.py", "game_engine/panel.py", "game_engine/panel.html",
            "game_engine/panel.css", "game_engine/panel.js", "game_engine/panel.compat.js", "game_engine/settings",
            "game_engine/library/playbooks/folded-sword.json",
            "game_engine/library/playbooks/neon-abyss.json",
            "game_engine/narrative_skills/survival-pressure.md",
            "game_engine/docs/demo/折剑行.save.json",
            "game_engine/android_manifest.json",
        ]
        for item in required:
            check("runtime 含 %s" % item, any(n == item or n.startswith(item + "/") for n in names))
        check("runtime 不含测试脚本", not any("tests_" in n for n in names))
        manifest = json.loads(zf.read("game_engine/android_manifest.json").decode("utf-8"))
        check("runtime 版本一致", manifest.get("version") == VERSION, "%s vs %s" % (manifest.get("version"), VERSION))
        check("runtime 文件数 > 60", manifest.get("files", 0) > 60, str(manifest.get("files")))


def apk_check() -> None:
    apk = DIST / ("world-walker-%s-arm64-v8a.apk" % VERSION)
    check("arm64 APK 已生成", apk.is_file(), "%.1f MB" % (apk.stat().st_size / 1024 / 1024) if apk.is_file() else "")
    if not apk.is_file():
        return
    aapt = Path(os.environ.get("ANDROID_HOME", "/home/user/android-sdk")) / "build-tools" / "35.0.0" / "aapt"
    apksigner = aapt.parent / "apksigner"
    if not aapt.is_file():
        check("aapt 可用", False, str(aapt))
        return
    out = subprocess.run([str(aapt), "dump", "badging", str(apk)], capture_output=True, text=True, check=True).stdout
    check("包名 com.worldwalker.app", "package: name='com.worldwalker.app'" in out)
    check("versionName %s" % VERSION, ("versionName='%s'" % VERSION) in out)
    check("minSdk 24", "sdkVersion:'24'" in out)
    check("targetSdk 35", "targetSdkVersion:'35'" in out)
    check("arm64 native", "native-code:" in out and "arm64-v8a" in out)
    with zipfile.ZipFile(apk) as zf:
        names = zf.namelist()
        check("APK 含 runtime.zip", "assets/runtime.zip" in names)
        check("APK 含 libpython3.12", "lib/arm64-v8a/libpython3.12.so" in names)
        check("APK 含 Chaquopy app.imy", "assets/chaquopy/app.imy" in names)
        check("APK 含 CA bundle", "assets/chaquopy/cacert.pem" in names)
        app_imy = zipfile.ZipFile(__import__("io").BytesIO(zf.read("assets/chaquopy/app.imy")))
        check("app.imy 含安卓宿主", "world_walker_android.pyc" in app_imy.namelist())
    if apksigner.is_file():
        proc = subprocess.run([str(apksigner), "verify", str(apk)], capture_output=True, text=True)
        check("APK 签名可验证", proc.returncode == 0, (proc.stderr or proc.stdout)[:80])


def boot_check() -> None:
    if not RUNTIME.is_file():
        return
    tmp = Path(tempfile.mkdtemp(prefix="ww-android-"))
    try:
        runtime = tmp / "runtime"
        game = tmp / "game"
        home = tmp / "home"
        cache = tmp / "cache"
        for p in (runtime, game, home, cache):
            p.mkdir(parents=True)
        with zipfile.ZipFile(RUNTIME) as zf:
            zf.extractall(runtime)
        sys.path.insert(0, str(ANDROID / "app" / "src" / "main" / "python"))
        import world_walker_android
        port = world_walker_android.start_server(str(runtime), str(game), str(home), str(cache))
        check("Python 宿主返回端口", 1 <= port <= 65535, str(port))
        health = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/api/v1/health" % port, timeout=8).read())
        check("面板健康检查", health.get("ok") is True and health.get("version") == VERSION, str(health)[:120])
        saves = list((game / "saves").glob("*.json"))
        check("首次启动铺演示档", len(saves) == 1, saves[0].name if saves else "none")
        world = json.loads(saves[0].read_text(encoding="utf-8")).get("world_info", {}).get("name", "")
        check("演示档世界可读", bool(world), world)
        world_walker_android.stop_server()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def source_check() -> None:
    main_java = (ANDROID / "app/src/main/java/com/worldwalker/app/MainActivity.java").read_text(encoding="utf-8")
    check("MainActivity 使用本地回环", "127.0.0.1" in main_java)
    check("Android 用 canonical 路径避开 /data/user/0 软链", "getCanonicalPath()" in main_java and "getFilesDir().getCanonicalPath()" in main_java)
    check("手机 CSS 断点存在", "@media (max-width: 760px)" in (ROOT / "panel.css").read_text(encoding="utf-8"))
    check("手机返回桥存在", "window.wwAndroidBack" in (ROOT / "panel.js").read_text(encoding="utf-8"))
    compat = (ROOT / "panel.compat.js").read_text(encoding="utf-8")
    digest = hashlib.sha256((ROOT / "panel.js").read_bytes()).hexdigest()
    check("panel.compat.js 与 panel.js 同步", digest in compat[:240], digest[:12])
    manifest = (ANDROID / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    check("Manifest 声明联网权限", 'android.permission.INTERNET' in manifest)
    check("Manifest 允许本地明文回环", 'android:usesCleartextTraffic="true"' in manifest)


def main() -> int:
    runtime_check()
    apk_check()
    boot_check()
    source_check()
    print("\n%d/%d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: " + "; ".join(FAIL))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
