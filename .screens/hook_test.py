"""Hook into the api.get to see what's happening with /cities/list."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}]", msg.text))
        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Hook into the request method to log
        page.evaluate("""() => {
            const api = window.__citylens_api;
            const orig = api.request.bind(api);
            api.request = async function(method, path, opts = {}) {
                const url = api._join(path);
                const key = api._key(method, url);
                const cached = api.cache.has(key);
                console.log(`[HOOK] ${method} ${path} cached=${cached}`);
                const r = await orig(method, path, opts);
                console.log(`[HOOK RESULT] ${method} ${path} -> cities=${r?.cities ? r.cities.length : 'null'}, total=${r?.total}`);
                return r;
            };
        }""")

        # Now click Enterprise
        print("\n--- Clicking Enterprise tab ---")
        page.click("#tab-btn-enterprise")
        page.wait_for_timeout(4000)

        print("\n--- After Enterprise mount ---")
        # Check select state
        sel = page.evaluate("""() => {
            const s = document.getElementById('entCitySelect');
            return { value: s.value, count: s.options.length };
        }""")
        print("Select state:", sel)

        browser.close()

if __name__ == "__main__":
    main()
