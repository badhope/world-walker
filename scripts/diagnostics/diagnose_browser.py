"""
诊断模式 - 捕获所有网络请求找出404
"""

from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:8080/index.html"

requests_log = []


def on_request(req):
    requests_log.append({"type": "request", "url": req.url, "method": req.method})


def on_response(resp):
    requests_log.append({"type": "response", "url": resp.url, "status": resp.status})


def on_failed(req):
    requests_log.append({"type": "failed", "url": req.url, "failure": str(req.failure)})


def on_console(msg):
    print(f"  [CONSOLE {msg.type}] {msg.text[:300]}")


def on_pageerror(err):
    print(f"  [PAGEERROR] {err}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    page.on("request", on_request)
    page.on("response", on_response)
    page.on("requestfailed", on_failed)
    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    print("Loading page...")
    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(3000)

    print("\n--- All network requests ---")
    for r in requests_log:
        if r["type"] == "response":
            status = r["status"]
            mark = "❌" if status >= 400 else "✅"
            print(f"  {mark} {status} {r['url']}")
        elif r["type"] == "failed":
            print(f"  ❌ FAILED {r['url']} - {r['failure']}")

    print("\n--- Console errors ---")
    print("--- done ---")
    browser.close()
