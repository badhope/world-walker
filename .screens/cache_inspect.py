"""Inspect what's in the LRU cache."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        result = page.evaluate("""() => {
            const api = window.__citylens_api;
            const cache = api.cache;
            const keys = [];
            for (const [k, v] of cache.map.entries()) {
                keys.push({ key: k, valuePreview: JSON.stringify(v).slice(0, 100), exp: v.exp, now: Date.now() });
            }
            return keys;
        }""")
        print("Cache contents:", result)

        browser.close()

if __name__ == "__main__":
    main()
