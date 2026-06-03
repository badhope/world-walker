"""Debug the select value at the time of the analyze call."""
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

        # Inspect the select state
        info = page.evaluate("""() => {
            const sel = document.getElementById('entCitySelect');
            return {
                value: sel.value,
                optionsCount: sel.options.length,
                optionsValues: Array.from(sel.options).map(o => o.value),
                optionsText: Array.from(sel.options).map(o => o.text)
            };
        }""")
        print("Enterprise select state:", info)

        # Click Government tab
        page.click("#tab-btn-government")
        page.wait_for_timeout(3000)

        info2 = page.evaluate("""() => {
            const sel = document.getElementById('govCitySelect');
            return {
                value: sel.value,
                optionsCount: sel.options.length,
                optionsValues: Array.from(sel.options).map(o => o.value),
                optionsText: Array.from(sel.options).map(o => o.text)
            };
        }""")
        print("Government select state:", info2)

        browser.close()

if __name__ == "__main__":
    main()
