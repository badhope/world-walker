"""Try to invoke the API and select population directly."""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Click Enterprise tab
        page.click("#tab-btn-enterprise")
        page.wait_for_timeout(3000)

        # Inspect the api object and try the same call
        result = page.evaluate("""async () => {
            const api = window.__citylens_api;
            const sel = document.getElementById('entCitySelect');
            const beforeVal = sel.value;
            const beforeCount = sel.options.length;

            // Try the call manually
            let apiResult, apiErr;
            try {
                apiResult = await api.get('/cities/list', { cacheTTL: 60000 });
            } catch (e) {
                apiErr = e.message;
            }

            return {
                beforeVal,
                beforeCount,
                apiResultType: typeof apiResult,
                apiResultCities: apiResult?.cities,
                apiErr
            };
        }""")
        print("Result:", result)

        browser.close()

if __name__ == "__main__":
    main()
