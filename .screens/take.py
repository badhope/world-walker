"""Take screenshots of all 4 tabs of the citylens SPA."""
from playwright.sync_api import sync_playwright
import os, sys, time

OUT = "/workspace/.screens"
os.makedirs(OUT, exist_ok=True)

console_msgs = []
errors = []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()

        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. Navigate
        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)  # let ECharts render

        # 2. Dashboard tab
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{OUT}/01_dashboard.png", full_page=True)
        print("[ok] dashboard")

        # 3. Enterprise tab
        page.click("#tab-btn-enterprise")
        page.wait_for_timeout(2500)
        page.screenshot(path=f"{OUT}/02_enterprise.png", full_page=True)
        print("[ok] enterprise")

        # 4. Government tab
        page.click("#tab-btn-government")
        page.wait_for_timeout(2500)
        page.screenshot(path=f"{OUT}/03_government.png", full_page=True)
        print("[ok] government")

        # 5. Cities (Compare) tab
        page.click("#tab-btn-cities")
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{OUT}/04_compare.png", full_page=True)
        print("[ok] compare")

        # 6. Dark mode
        page.click("#tab-btn-dashboard")
        page.wait_for_timeout(800)
        page.click("#themeToggle")
        page.wait_for_timeout(800)
        page.screenshot(path=f"{OUT}/05_dashboard_dark.png", full_page=True)
        print("[ok] dashboard dark")

        browser.close()

    print("\n--- Console messages ({}):".format(len(console_msgs)))
    for m in console_msgs[:30]:
        print(" ", m)
    print("\n--- Page errors ({}):".format(len(errors)))
    for e in errors:
        print(" ", e)

if __name__ == "__main__":
    main()
