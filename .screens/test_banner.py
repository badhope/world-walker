"""Simulate backend down — block /api/v1/* and /health, then take screenshot of banner."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()

        # Block all API calls to simulate backend down
        def block_route(route):
            url = route.request.url
            if "localhost:8000" in url:
                route.abort("connectionrefused")
            else:
                route.continue_()
        page.route("**/*", block_route)

        page.goto("http://localhost:8080/index.html", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(4000)  # let error handlers run

        # Verify banner is visible
        info = page.evaluate("""() => {
            const b = document.getElementById('backendBanner');
            return {
                hidden: b.hidden,
                visible: !b.hidden && b.offsetHeight > 0,
                title: document.getElementById('backendBannerTitle')?.textContent,
                count: document.getElementById('backendBannerCount')?.textContent,
                detail: document.getElementById('backendBannerDetail')?.textContent?.slice(0, 200)
            };
        }""")
        print("Banner state when backend down:", info)

        page.screenshot(path="/workspace/.screens/06_banner_offline.png", full_page=False)
        print("[ok] banner screenshot saved")
        browser.close()

if __name__ == "__main__":
    main()
