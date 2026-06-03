"""
端到端浏览器自动化测试
"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:8080/index.html"
SHOT_DIR = Path("/workspace/screenshots/browser_test")
SHOT_DIR.mkdir(parents=True, exist_ok=True)

for f in SHOT_DIR.glob("*.png"):
    f.unlink()

results = {
    "console_logs": [],
    "page_errors": [],
    "request_failures": [],
    "screenshots": [],
    "actions": [],
}


def on_console(msg):
    try:
        results["console_logs"].append({"type": msg.type, "text": msg.text[:200]})
    except Exception:
        pass


def on_pageerror(err):
    try:
        results["page_errors"].append(str(err))
    except Exception:
        pass


def on_requestfailed(req):
    try:
        results["request_failures"].append({"url": req.url, "failure": str(req.failure)[:100]})
    except Exception:
        pass


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        page.on("console", on_console)
        page.on("pageerror", on_pageerror)
        page.on("requestfailed", on_requestfailed)

        # 1) Open homepage
        print("=" * 60)
        print("1 Open homepage")
        print("=" * 60)
        page.goto(FRONTEND_URL, wait_until="networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        try:
            page.wait_for_function(
                "document.getElementById('healthPill') && document.getElementById('healthPill').className.includes('online')",
                timeout=10000,
            )
            print("  OK health check")
        except Exception as e:
            print(f"  WARN health check timeout: {e}")
        shot1 = SHOT_DIR / "01_home_dashboard.png"
        page.screenshot(path=str(shot1), full_page=True)
        results["screenshots"].append(str(shot1))
        print(f"  Shot: {shot1}")
        print(f"  Title: {page.title()}")

        # 2) Enterprise tab
        print("\n" + "=" * 60)
        print("2 Click Enterprise tab")
        print("=" * 60)
        page.click('button[data-tab="enterprise"]')
        page.wait_for_timeout(800)
        results["actions"].append("click:enterprise-tab")
        shot2 = SHOT_DIR / "02_enterprise_tab.png"
        page.screenshot(path=str(shot2), full_page=True)
        results["screenshots"].append(str(shot2))
        print(f"  Shot: {shot2}")

        # 3) Run enterprise analysis
        print("\n" + "=" * 60)
        print("3 Run enterprise analysis")
        print("=" * 60)
        try:
            page.select_option("#entCitySelect", "深圳")
            page.wait_for_timeout(300)
            page.click("#btnEntAnalyze")
            page.wait_for_timeout(3500)
            results["actions"].append("analyze:enterprise:深圳")
            shot3 = SHOT_DIR / "03_enterprise_analyzed.png"
            page.screenshot(path=str(shot3), full_page=True)
            results["screenshots"].append(str(shot3))
            details_html = page.locator("#entDetails").inner_html()
            print(f"  Shot: {shot3}")
            print(f"  Details length: {len(details_html)}")
            if "detail-item" in details_html:
                print("  OK enterprise details rendered")
            else:
                print("  WARN enterprise details not rendered")
        except Exception as e:
            print(f"  FAIL enterprise analysis: {e}")

        # 4) Government tab
        print("\n" + "=" * 60)
        print("4 Click Government tab")
        print("=" * 60)
        page.click('button[data-tab="government"]')
        page.wait_for_timeout(800)
        shot4 = SHOT_DIR / "04_government_tab.png"
        page.screenshot(path=str(shot4), full_page=True)
        results["screenshots"].append(str(shot4))
        print(f"  Shot: {shot4}")

        # 5) Run gov analysis
        print("\n" + "=" * 60)
        print("5 Run government analysis")
        print("=" * 60)
        try:
            page.select_option("#govCitySelect", "上海")
            page.wait_for_timeout(300)
            page.click('button:has-text("运行产业分析")')
            page.wait_for_timeout(4000)
            results["actions"].append("analyze:government:上海")
            shot5 = SHOT_DIR / "05_government_analyzed.png"
            page.screenshot(path=str(shot5), full_page=True)
            results["screenshots"].append(str(shot5))
            details_html = page.locator("#govDetails").inner_html()
            print(f"  Shot: {shot5}")
            print(f"  Details length: {len(details_html)}")
        except Exception as e:
            print(f"  FAIL gov analysis: {e}")

        # 6) Cities tab
        print("\n" + "=" * 60)
        print("6 Click Cities tab")
        print("=" * 60)
        page.click('button[data-tab="cities"]')
        page.wait_for_timeout(800)
        shot6 = SHOT_DIR / "06_cities_tab.png"
        page.screenshot(path=str(shot6), full_page=True)
        results["screenshots"].append(str(shot6))
        print(f"  Shot: {shot6}")

        # 7) Compare
        print("\n" + "=" * 60)
        print("7 Run city comparison")
        print("=" * 60)
        try:
            page.click('button:has-text("对比分析")')
            page.wait_for_timeout(5000)
            results["actions"].append("compare:深圳/上海/北京")
            shot7 = SHOT_DIR / "07_cities_compared.png"
            page.screenshot(path=str(shot7), full_page=True)
            results["screenshots"].append(str(shot7))
            table_html = page.locator("#compareTable").inner_html()
            print(f"  Shot: {shot7}")
            print(f"  Table length: {len(table_html)}")
        except Exception as e:
            print(f"  FAIL city compare: {e}")

        # 8) Back to dashboard
        print("\n" + "=" * 60)
        print("8 Back to dashboard")
        print("=" * 60)
        page.click('button[data-tab="dashboard"]')
        page.wait_for_timeout(1000)
        shot8 = SHOT_DIR / "08_dashboard_final.png"
        page.screenshot(path=str(shot8), full_page=True)
        results["screenshots"].append(str(shot8))
        print(f"  Shot: {shot8}")

        # 9) Test error handling
        print("\n" + "=" * 60)
        print("9 Test error handling")
        print("=" * 60)
        page.click('button[data-tab="enterprise"]')
        page.wait_for_timeout(500)
        page.evaluate("""
            var sel = document.getElementById('entCitySelect');
            var opt = document.createElement('option');
            opt.value = '不存在的城市XXX';
            opt.text = '不存在的城市XXX';
            sel.appendChild(opt);
            sel.value = '不存在的城市XXX';
        """)
        page.click("#btnEntAnalyze")
        page.wait_for_timeout(3000)
        shot9 = SHOT_DIR / "09_error_handling.png"
        page.screenshot(path=str(shot9), full_page=True)
        results["screenshots"].append(str(shot9))
        print(f"  Shot: {shot9}")
        toasts = page.locator(".toast").all()
        print(f"  Toasts: {len(toasts)}")

        browser.close()

    report = {
        "console_logs_count": len(results["console_logs"]),
        "console_errors": [entry for entry in results["console_logs"] if entry["type"] == "error"],
        "console_warnings": [entry for entry in results["console_logs"] if entry["type"] == "warning"],
        "page_errors_count": len(results["page_errors"]),
        "page_errors": results["page_errors"][:5],
        "request_failures_count": len(results["request_failures"]),
        "request_failures": results["request_failures"][:5],
        "screenshots": results["screenshots"],
        "actions_performed": results["actions"],
    }
    with open("/tmp/browser_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "=" * 60)
    print("BROWSER TEST REPORT")
    print("=" * 60)
    print(f"  Console logs: {len(results['console_logs'])}")
    print(f"  Console errors: {len(report['console_errors'])}")
    print(f"  Console warnings: {len(report['console_warnings'])}")
    print(f"  Page errors: {len(results['page_errors'])}")
    print(f"  Request failures: {len(results['request_failures'])}")
    print(f"  Screenshots: {len(results['screenshots'])}")
    print("=" * 60)
    if report["console_errors"]:
        print("\nCONSOLE ERRORS:")
        for e in report["console_errors"][:10]:
            print(f"  - {e['text'][:150]}")
    if report["page_errors"]:
        print("\nPAGE ERRORS:")
        for e in report["page_errors"][:5]:
            print(f"  - {e[:200]}")
    if report["request_failures"]:
        print("\nREQUEST FAILURES:")
        for r in report["request_failures"][:5]:
            print(f"  - {r['url']}")
            print(f"    {r['failure']}")
    return report


if __name__ == "__main__":
    main()
