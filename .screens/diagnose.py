"""Re-run with response logging to identify the 4 console 404 URLs."""
from playwright.sync_api import sync_playwright
import os

OUT = "/workspace/.screens"

console_msgs = []
responses = []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()

        page.on("console", lambda msg: console_msgs.append((msg.type, msg.text)))
        page.on("response", lambda r: responses.append((r.status, r.url)) if r.status >= 400 else None)

        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)

        # Click through tabs to surface all 4xx
        for sel in ["#tab-btn-enterprise", "#tab-btn-government", "#tab-btn-cities", "#tab-btn-dashboard"]:
            page.click(sel)
            page.wait_for_timeout(2500)

        page.click("#themeToggle")
        page.wait_for_timeout(800)
        page.click("#themeToggle")
        page.wait_for_timeout(800)

        browser.close()

    print("\n--- 4xx/5xx responses ({}):".format(sum(1 for s,_ in responses)))
    for status, url in responses:
        print(f"  {status}  {url}")

    print("\n--- Console errors/warnings:")
    for kind, text in console_msgs:
        if kind in ("error", "warning"):
            print(f"  [{kind}] {text[:240]}")

if __name__ == "__main__":
    main()
