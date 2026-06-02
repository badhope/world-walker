"""
找出最后的404错误是什么URL
"""
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:8080/index.html"

failed_404s = []

def on_response(resp):
    if resp.status >= 400:
        failed_404s.append({"status": resp.status, "url": resp.url})


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.on("response", on_response)

    page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    # 切换tab触发更多请求
    for tab in ['enterprise', 'government', 'cities', 'dashboard']:
        page.click(f'button[data-tab="{tab}"]')
        page.wait_for_timeout(500)
    page.wait_for_timeout(2000)
    browser.close()

print(f"Total 4xx/5xx responses: {len(failed_404s)}")
for r in failed_404s:
    print(f"  {r['status']} {r['url']}")
