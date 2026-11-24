#!/usr/bin/env python3
"""Build the Android APK from the same Python engine the desktop uses.

The APK is a thin WebView host plus a Chaquopy Python runtime.  Engine source
and data are staged into ``android/app/src/main/assets/runtime.zip``; nothing
under ``android/`` duplicates the Python tree.  Release APKs are signed with a
local keystore under ``.android-signing/`` (gitignored), so the same package
name can be upgraded later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID = ROOT / "android"
ASSETS = ANDROID / "app" / "src" / "main" / "assets"
RUNTIME = ASSETS / "runtime.zip"
DIST = ROOT / "dist" / "android"
SIGN_DIR = ROOT / ".android-signing"
KEYSTORE = SIGN_DIR / "world-walker-release.jks"
PASSFILE = SIGN_DIR / "password.txt"


def version() -> str:
    text = (ROOT / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)', text)
    if not match:
        raise SystemExit("cannot read __version__")
    return match.group(1)


def runtime_files() -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.py", "rules/*.py"):
        for path in sorted(ROOT.glob(pattern)):
            if path.name.startswith("test_") or path.name.startswith("tests_"):
                continue
            if path.name == "mcp_server.py":
                # MCP is optional on desktop and impossible on Android; leaving it
                # out keeps the APK smaller and avoids an import-time mcp SDK probe.
                continue
            files.append(path)
    for pattern in (
        "panel.html", "panel.css", "panel.js",
        "settings/*.json", "settings/*.md",
        "library/playbooks/*.json", "library/archives/*.md",
        "narrative_skills/*.md",
        "docs/demo/*.json",
        "LICENSE", "BRAND.md",
    ):
        files.extend(sorted(ROOT.glob(pattern)))
    seen: dict[str, Path] = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if rel not in seen:
            seen[rel] = path
    return [seen[k] for k in sorted(seen)]


def stage_runtime() -> dict:
    ASSETS.mkdir(parents=True, exist_ok=True)
    files = runtime_files()
    manifest = {
        "version": version(),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": len(files),
    }
    with zipfile.ZipFile(RUNTIME, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            arc = "game_engine/" + path.relative_to(ROOT).as_posix()
            zf.write(path, arc)
        zf.writestr(
            "game_engine/android_manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
    digest = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
    manifest["zip_bytes"] = RUNTIME.stat().st_size
    manifest["zip_sha256"] = digest
    print("runtime.zip: %d files, %.1f KB, sha256=%s" % (
        len(files), RUNTIME.stat().st_size / 1024, digest[:16]))
    return manifest


def java_home() -> str:
    if os.environ.get("JAVA_HOME"):
        return os.environ["JAVA_HOME"]
    candidate = "/usr/lib/jvm/java-17-openjdk-amd64"
    return candidate if os.path.isdir(candidate) else ""


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit("missing build tool: " + name)
    return path


def ensure_keystore() -> tuple[str, str, str]:
    """Return (keystore, alias, password), creating a local dev key if absent."""
    env_ks = os.environ.get("WW_ANDROID_KEYSTORE")
    if env_ks:
        return (env_ks,
                os.environ.get("WW_ANDROID_KEY_ALIAS", "worldwalker"),
                os.environ.get("WW_ANDROID_KEYSTORE_PASS", ""))
    SIGN_DIR.mkdir(parents=True, exist_ok=True)
    if not KEYSTORE.is_file():
        password = secrets.token_urlsafe(24)
        keytool = os.path.join(java_home(), "bin", "keytool") if java_home() else tool("keytool")
        subprocess.run([
            keytool, "-genkeypair", "-v",
            "-keystore", str(KEYSTORE),
            "-alias", "worldwalker",
            "-keyalg", "RSA", "-keysize", "4096", "-validity", "10000",
            "-storepass", password, "-keypass", password,
            "-dname", "CN=World Walker, OU=Android, O=World Walker, L=Chaozhou, ST=Guangdong, C=CN",
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PASSFILE.write_text(password + "\n", encoding="utf-8")
        os.chmod(PASSFILE, 0o600)
        os.chmod(KEYSTORE, 0o600)
        print("created local release keystore: %s" % KEYSTORE)
    password = PASSFILE.read_text(encoding="utf-8").strip()
    return str(KEYSTORE), "worldwalker", password


def run_gradle(task: str) -> None:
    env = os.environ.copy()
    jh = java_home()
    if jh:
        env["JAVA_HOME"] = jh
    sdk = env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT") or "/home/user/android-sdk"
    if not os.path.isdir(sdk):
        raise SystemExit("ANDROID_HOME not found: " + sdk)
    env["ANDROID_HOME"] = sdk
    env["ANDROID_SDK_ROOT"] = sdk
    env.setdefault("GRADLE_USER_HOME", "/home/user/.gradle-android")
    cmd = [str(ANDROID / "gradlew"), "--no-daemon", task]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(ANDROID), env=env, check=True)


def sign_apk(unsigned: Path, out: Path, keystore: str, alias: str, password: str) -> None:
    build_tools = Path(os.environ.get("ANDROID_HOME", "/home/user/android-sdk")) / "build-tools" / "35.0.0"
    zipalign = build_tools / "zipalign"
    apksigner = build_tools / "apksigner"
    if not zipalign.is_file() or not apksigner.is_file():
        raise SystemExit("build-tools 35.0.0 missing")
    aligned = out.with_suffix(".aligned.apk")
    subprocess.run([str(zipalign), "-f", "-p", "4", str(unsigned), str(aligned)], check=True)
    subprocess.run([
        str(apksigner), "sign",
        "--ks", keystore, "--ks-key-alias", alias,
        "--ks-pass", "pass:" + password, "--key-pass", "pass:" + password,
        "--out", str(out), str(aligned),
    ], check=True)
    aligned.unlink(missing_ok=True)
    subprocess.run([str(apksigner), "verify", "--print-certs", str(out)],
                   check=True, stdout=subprocess.DEVNULL)


def collect_release(debug: bool) -> list[Path]:
    outputs = sorted((ANDROID / "app" / "build" / "outputs" / "apk").rglob("*.apk"))
    # Split builds produce app-<abi>-release-unsigned.apk plus app-universal-release-unsigned.apk.
    candidates = [p for p in outputs if "release" in p.name and "unsigned" in p.name]
    if debug:
        candidates = [p for p in outputs if "debug" in p.name]
    if not candidates:
        raise SystemExit("no APK outputs found under " + str(ANDROID / "app" / "build" / "outputs" / "apk"))
    DIST.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    if debug:
        for src in candidates:
            dst = DIST / ("world-walker-%s-debug.apk" % version())
            shutil.copy2(src, dst)
            copied.append(dst)
        return copied
    keystore, alias, password = ensure_keystore()
    for src in candidates:
        if "arm64" in src.name:
            abi = "arm64-v8a"
        elif "x86_64" in src.name:
            abi = "x86_64"
        elif "universal" in src.name:
            abi = "universal"
        else:
            abi = src.stem.replace("app-", "").replace("-release-unsigned", "")
        dst = DIST / ("world-walker-%s-%s.apk" % (version(), abi))
        sign_apk(src, dst, keystore, alias, password)
        copied.append(dst)
    return copied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true", help="only stage runtime.zip")
    ap.add_argument("--debug", action="store_true", help="build a debug APK instead of signed release")
    args = ap.parse_args()
    manifest = stage_runtime()
    if args.no_build:
        return 0
    run_gradle(":app:assembleDebug" if args.debug else ":app:assembleRelease")
    copied = collect_release(args.debug)
    sums = []
    for path in copied:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sums.append("%s  %s" % (digest, path.name))
        print("APK %-48s %7.1f MB  %s" % (path.name, path.stat().st_size / 1024 / 1024, digest[:16]))
    (DIST / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    (DIST / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
