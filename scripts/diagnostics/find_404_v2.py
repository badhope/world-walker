"""
详细诊断：捕获所有4xx/5xx响应 + 所有console消息
"""

from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:8080/index.html"

all_responses = []
all_console = []


def on_response(resp):
    all_responses.append({"status": resp.status, "url": resp.url, "type": resp.request.resource_type})


def on_console(msg):
    all_console.append({"type": msg.type, "text": msg.text})


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.on("response", on_response)
    page.on("console", on_console)

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(3000)

    # do a full flow
    for tab in ["enterprise", "government", "cities", "dashboard"]:
        page.click(f'button[data-tab="{tab}"]')
        page.wait_for_timeout(800)
    page.click('button[data-tab="enterprise"]')
    page.wait_for_timeout(500)
    page.select_option("#entCitySelect", "深圳")
    page.wait_for_timeout(300)
    page.click("#btnEntAnalyze")
    page.wait_for_timeout(3500)
    page.click('button[data-tab="government"]')
    page.wait_for_timeout(500)
    page.select_option("#govCitySelect", "上海")
    page.click('button:has-text("运行产业分析")')
    page.wait_for_timeout(3500)
    page.click('button[data-tab="cities"]')
    page.wait_for_timeout(500)
    page.click('button:has-text("对比分析")')
    page.wait_for_timeout(5000)
    browser.close()

# Find 4xx/5xx
print("=== 4xx/5xx responses ===")
fails = [r for r in all_responses if r["status"] >= 400]
if fails:
    for f in fails:
        print(f"  {f['status']} {f['type']:10s} {f['url']}")
else:
    print("  (none)")

# Console errors
print("\n=== Console errors ===")
errs = [c for c in all_console if c["type"] == "error"]
if errs:
    for e in errs:
        print(f"  [{e['type']}] {e['text']}")
else:
    print("  (none)")

print(f"\nTotal responses: {len(all_responses)}")
print(f"  2xx: {sum(1 for r in all_responses if 200 <= r['status'] < 300)}")
print(f"  3xx: {sum(1 for r in all_responses if 300 <= r['status'] < 400)}")
print(f"  4xx: {sum(1 for r in all_responses if 400 <= r['status'] < 500)}")
print(f"  5xx: {sum(1 for r in all_responses if r['status'] >= 500)}")
