"""Detailed trace - log every 4xx request with the page state at the time."""
from playwright.sync_api import sync_playwright

console_msgs = []
responses = []
request_attempts = []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()

        page.on("console", lambda msg: console_msgs.append((msg.type, msg.text)))
        page.on("response", lambda r: responses.append((r.status, r.url, r.request.resource_type, r.request.method)))

        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)

        for sel in ["#tab-btn-enterprise", "#tab-btn-government", "#tab-btn-cities", "#tab-btn-dashboard"]:
            page.click(sel)
            page.wait_for_timeout(2500)

        browser.close()

    print("\n--- All 4xx responses:")
    for status, url, rtype, method in responses:
        if status >= 400:
            print(f"  {method} {status}  [{rtype}]  {url}")

    print("\n--- Total requests:", len(responses))
    for s, u, t, m in responses:
        if "cities/" in u or "enterprise/v3" in u or "/health" in u:
            print(f"  {m} {s}  {u}")

if __name__ == "__main__":
    main()
