"""Capture the actual response body and error when Enterprise mounts."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # Capture all API calls with their response
        api_calls = []
        page.on("response", lambda r: api_calls.append((r.request.method, r.url, r.status)))

        page.on("console", lambda msg: print(f"[{msg.type}]", msg.text[:200]))

        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        print("\n--- Before clicking Enterprise ---")
        print("API calls so far:")
        for m, u, s in api_calls:
            print(f"  {m} {s}  {u}")
        api_calls.clear()

        # Click Enterprise tab
        page.click("#tab-btn-enterprise")
        page.wait_for_timeout(3500)

        print("\n--- After clicking Enterprise ---")
        print("API calls:")
        for m, u, s in api_calls:
            print(f"  {m} {s}  {u}")

        # Get the actual state and try to fetch manually
        result = page.evaluate("""async () => {
            const sel = document.getElementById('entCitySelect');
            const before = {
                value: sel.value,
                optionsCount: sel.options.length
            };
            // Try the same fetch
            const r = await fetch('http://localhost:8000/api/v1/cities/list');
            const txt = await r.text();
            return {before, status: r.status, body: txt.slice(0, 200)};
        }""")
        print("\n--- Diagnostic result ---")
        print(result)

        browser.close()

if __name__ == "__main__":
    main()
