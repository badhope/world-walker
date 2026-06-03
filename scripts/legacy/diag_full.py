from playwright.sync_api import sync_playwright

print("=" * 70)
print("[scan] E2E诊断 (新前端)")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})

    errors = []
    successes = []

    def ok(msg):
        successes.append(msg)
        print(f"[ok] {msg}")

    def err(msg):
        errors.append(msg)
        print(f"[FAIL] {msg}")

    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text[:150]}") if msg.type == "error" else None)
    page.on("requestfailed", lambda req: errors.append(f"NET {req.method} {req.url}"))
    page.on("response", lambda resp: errors.append(f"HTTP{resp.status} {resp.url}") if resp.status >= 500 else None)

    # 1. 加载页面
    print("\n📄 [1/4] 加载首页")
    try:
        page.goto("http://localhost:8001/app", timeout=15000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)
        title = page.title()
        health = page.locator("#healthText").inner_text()
        ok(f"标题: '{title}' | 健康: {health}")
    except Exception as e:
        err(f"加载失败: {e}")
        browser.close()
        exit(1)

    # 2. 检查仪表盘
    print("\n[i] [2/4] 仪表盘检查")
    try:
        stats = page.locator(".stat-value").all()
        cards = page.locator("#cityCards .city-card").all()
        ok(f"统计卡片: {len(stats)} | 城市卡片: {len(cards)}")
    except Exception as e:
        err(f"仪表盘检查失败: {e}")

    # 3. 企业选址分析
    print("\n [3/4] 企业选址分析")
    try:
        page.locator('.tab-btn[data-tab="enterprise"]').first.click()
        page.wait_for_timeout(500)
        page.locator("#btnEntAnalyze").first.click()
        page.wait_for_timeout(6000)
        score = page.locator("#entTotalScore").inner_text()
        dets = page.locator("#entDetails > div").count()
        ok(f"评分: {score} | 指标: {dets}")
    except Exception as e:
        err(f"企业分析失败: {e}")

    # 4. 政府分析 + 城市对比
    print("\n [4/4] 政府分析 + 城市对比")
    try:
        page.locator('.tab-btn[data-tab="government"]').first.click()
        page.wait_for_timeout(500)
        page.locator('button:has-text("运行产业分析")').first.click()
        page.wait_for_timeout(8000)
        gov = page.locator("#govDetails > div").count()
        ok(f"政府指标: {gov}")
    except Exception as e:
        err(f"政府分析失败: {e}")

    try:
        page.locator('.tab-btn[data-tab="cities"]').first.click()
        page.wait_for_timeout(500)
        page.locator('button:has-text("对比分析")').first.click()
        page.wait_for_timeout(10000)
        rows = page.locator("#compareTable tbody tr").count()
        ok(f"对比表格: {rows} 行")
    except Exception as e:
        err(f"城市对比失败: {e}")

    browser.close()

    print("\n" + "=" * 70)
    print("[report] 汇总")
    print("=" * 70)
    real_errs = [e for e in errors if "cdn.tailwindcss" not in e and "deprecated" not in e.lower()]
    print(f"[ok] 成功: {len(successes)}/{len(successes) + len(real_errs)}")
    print(f"[FAIL] 错误: {len(real_errs)}")
    for e in real_errs[:8]:
        print(f"   {e}")
    if not real_errs:
        print("    零错误!")

print("\n[ok] 诊断完成")
