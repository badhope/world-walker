"""Clear cache and try again to confirm the API works correctly."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Check cache and call again with cacheTTL:0 to bypass cache
        result = page.evaluate("""async () => {
            const api = window.__citylens_api;
            // Force a fresh call
            let r;
            try {
                r = await api.get('/cities/list', { cacheTTL: 0 });
            } catch (e) {
                return { err: e.message };
            }
            return { cities: r?.cities, total: r?.total, raw: JSON.stringify(r) };
        }""")
        print("Bypass-cache result:", result)

        # Click Enterprise tab now
        page.click("#tab-btn-enterprise")
        page.wait_for_timeout(3000)
        sel = page.evaluate("""() => {
            const s = document.getElementById('entCitySelect');
            return { value: s.value, count: s.options.length, options: Array.from(s.options).map(o => o.value) };
        }""")
        print("After click Enterprise:", sel)

        browser.close()

if __name__ == "__main__":
    main()
