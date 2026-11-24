"""Android host for the local World Walker panel.

The APK carries the engine as a zip under assets/runtime.zip.  Java extracts it
into app-private storage, then calls :func:`start_server` from a background
thread.  Everything below stays inside the app process and binds to loopback,
so the WebView talks to a real local HTTP server, not a remote one.
"""

from __future__ import annotations

import glob
import os
import shutil
import sys
import threading

_SERVER = None
_PORT = 0
_LOCK = threading.Lock()


def _env_paths(data_dir: str, home_dir: str, cache_dir: str) -> None:
    home_dir = os.path.abspath(home_dir)
    data_dir = os.path.abspath(data_dir)
    cache_dir = os.path.abspath(cache_dir)
    os.makedirs(home_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["HOME"] = home_dir
    os.environ["TMPDIR"] = cache_dir
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["WW_MODEL_CONFIG"] = os.path.join(home_dir, ".world-walker", "model.json")
    os.environ["WW_HARNESS_CONFIG"] = os.path.join(home_dir, ".world-walker", "harness.json")
    os.environ["WW_HOOKS_DIR"] = os.path.join(home_dir, ".world-walker", "hooks")
    os.environ["WG_PANEL_PORT_VERBOSE"] = "0"


def _cert_bundle() -> None:
    """Point OpenSSL at a CA bundle that ships inside the APK.

    Android keeps its CA store outside OpenSSL's usual search path, and a
    missing bundle makes every HTTPS model endpoint fail with a generic
    certificate error.  certifi is a pure-Python wheel so this stays cheap.
    """
    try:
        import certifi  # type: ignore
        where = certifi.where()
    except Exception:
        return
    if where and os.path.isfile(where):
        os.environ["SSL_CERT_FILE"] = where
        os.environ["REQUESTS_CA_BUNDLE"] = where


def _seed_saves(runtime_dir: str, data_dir: str) -> list[str]:
    saves = os.path.join(data_dir, "saves")
    os.makedirs(saves, exist_ok=True)
    files = sorted(glob.glob(os.path.join(saves, "*.json")), key=os.path.getmtime, reverse=True)
    if files:
        return files
    demo = os.path.join(runtime_dir, "game_engine", "docs", "demo", "折剑行.save.json")
    if not os.path.isfile(demo):
        demo = os.path.join(runtime_dir, "game_engine", "docs", "demo", "雾港.save.json")
    if os.path.isfile(demo):
        target = os.path.join(saves, "折剑行.save.json")
        shutil.copyfile(demo, target)
        return [target]
    return []


def start_server(runtime_dir: str, data_dir: str, home_dir: str, cache_dir: str) -> int:
    """Start the panel and return its loopback port.

    Call once per process.  A second call returns the existing port, which makes
    the Android retry button harmless instead of leaking a second HTTP server.
    """
    global _SERVER, _PORT
    with _LOCK:
        if _SERVER is not None and _PORT:
            return _PORT
        runtime_dir = os.path.abspath(runtime_dir)
        if runtime_dir not in sys.path:
            sys.path.insert(0, runtime_dir)
        _env_paths(data_dir, home_dir, cache_dir)
        _cert_bundle()
        os.chdir(os.path.abspath(data_dir))

        from game_engine import panel
        files = _seed_saves(runtime_dir, data_dir)
        if not files:
            raise RuntimeError("没有可用的初始存档，runtime.zip 可能缺 docs/demo")
        state_path = files[0]
        srv, port = panel.start(
            state_path, 0, "127.0.0.1",
            host_allow=("127.0.0.1", "localhost"))
        _SERVER, _PORT = srv, int(port)
        return _PORT


def stop_server() -> None:
    global _SERVER, _PORT
    with _LOCK:
        srv, _SERVER, _PORT = _SERVER, None, 0
    if srv is not None:
        try:
            from game_engine import panel
            panel.stop(srv)
        except Exception:
            pass
