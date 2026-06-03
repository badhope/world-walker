"""Simulate 404 on a city — verify banner shows the right message."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()

        # /cities/{city} returns 404 for "苏州" (real backend behavior)
        def route_handler(route):
            url = route.request.url
            if "苏州" in url or "苏州" in route.request.post_data or True:
                if "%E8%8B%8F%E5%B7%9E" in url:
                    route.fulfill(status=404, body='{"detail":"城市 苏州 数据未找到"}', headers={"content-type":"application/json"})
                else:
                    route.continue_()
            else:
                route.continue_()
        page.route("**/api/v1/cities/*", route_handler)

        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3500)

        info = page.evaluate("""() => {
            const b = document.getElementById('backendBanner');
            return {
                hidden: b.hidden,
                title: document.getElementById('backendBannerTitle')?.textContent,
                count: document.getElementById('backendBannerCount')?.textContent,
                detailHas404: document.getElementById('backendBannerDetail')?.textContent?.includes('404')
            };
        }""")
        print("404 case banner state:", info)
        browser.close()

if __name__ == "__main__":
    main()
