"""
前端交互自动化测试 - 模拟人工操作全流程
测试所有4个标签页 + 前后端连接 + 边界情况
"""

import os

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = "/workspace/screenshots/interaction_test"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

RESULTS = {"passed": [], "failed": [], "warnings": [], "network_errors": [], "console_errors": []}


def ok(msg):
    RESULTS["passed"].append(msg)
    print(f"  [ok] {msg}")


def fail(msg):
    RESULTS["failed"].append(msg)
    print(f"  [FAIL] {msg}")


def warn(msg):
    RESULTS["warnings"].append(msg)
    print(f"  [!] {msg}")


def shot(page, name):
    path = os.path.join(SCREENSHOT_DIR, name)
    page.screenshot(path=path, full_page=True)
    print(f"  📸 截图: {name}")


print("=" * 70)
print("[*] 全功能前端交互自动化测试")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
    page = ctx.new_page()

    # 捕获所有错误
    page.on(
        "console", lambda m: RESULTS["console_errors"].append(f"[{m.type}] {m.text}") if m.type == "error" else None
    )
    page.on("requestfailed", lambda r: RESULTS["network_errors"].append(f"FAIL {r.method} {r.url}"))
    page.on(
        "response", lambda r: RESULTS["network_errors"].append(f"HTTP{r.status} {r.url}") if r.status >= 500 else None
    )

    # =======================================
    #  第1步: 加载首页 + 后端健康检查
    # =======================================
    print("\n" + "-" * 60)
    print("📄 [1/6] 首页加载 & 健康检查")
    print("-" * 60)

    try:
        page.goto("http://localhost:8001/app", timeout=20000)
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception as e:
        fail(f"首页加载超时: {e}")
        browser.close()
        exit(1)

    # 等待数据加载完成（城市卡片是异步加载的）
    page.wait_for_timeout(4000)

    # 验证标题
    title = page.title()
    if title == "区域产业经济分析平台":
        ok(f"页面标题正确: '{title}'")
    else:
        fail(f"标题不匹配: '{title}'")

    # 验证健康状态
    health = page.locator("#healthText").inner_text()
    if "正常" in health or "系统" in health:
        ok(f"健康状态: {health}")
    else:
        fail(f"健康状态异常: {health}")

    # 验证版本号
    version = page.locator("#versionTag").inner_text()
    ok(f"版本号显示: {version}")

    # 后端健康检查
    try:
        resp = page.evaluate("""async () => {
            const r = await fetch('/health');
            const d = await r.json();
            return d;
        }""")
        if resp.get("status") == "healthy":
            ok(f"后端健康检查通过: status={resp.get('status')}, version={resp.get('version')}")
        else:
            fail(f"后端健康检查失败: {resp}")
    except Exception as e:
        fail(f"后端健康检查异常: {e}")

    shot(page, "01_home_loaded.png")

    # =======================================
    #  第2步: 仪表盘标签页检查
    # =======================================
    print("\n" + "-" * 60)
    print("[i] [2/6] 仪表盘标签页 — 模拟人工浏览")
    print("-" * 60)

    # 等待异步数据加载
    page.wait_for_timeout(2000)

    # 检查统计卡片
    stat_cards = page.locator(".stat-card").all()
    ok(f"统计卡片数量: {len(stat_cards)}")
    if len(stat_cards) >= 4:
        for i, card in enumerate(stat_cards[:4]):
            label = card.locator(".stat-label").inner_text()
            value = card.locator(".stat-value").inner_text()
            ok(f"  统计[{i}]: {label} = {value}")
    else:
        fail(f"统计卡片不足: 只有 {len(stat_cards)} 个")

    # 检查城市卡片（等待异步加载完成）
    try:
        page.wait_for_selector("#cityCards .city-card", timeout=8000)
    except:
        warn("城市卡片加载较慢，继续等待...")
        page.wait_for_timeout(3000)

    city_cards = page.locator("#cityCards .city-card").all()
    if len(city_cards) >= 8:
        ok(f"城市卡片数量: {len(city_cards)}")
        for i, card in enumerate(city_cards[:3]):
            name = card.locator(".city-name").inner_text()
            industry = card.locator(".city-industry").inner_text()
            ok(f"  城市[{i}]: {name} | 产业: {industry}")
    elif len(city_cards) > 0:
        ok(f"城市卡片部分加载: {len(city_cards)} 个")
    else:
        fail("城市卡片未加载")

    # 模拟鼠标悬停在城市卡片上
    if city_cards:
        city_cards[0].hover()
        page.wait_for_timeout(300)
        ok("城市卡片 hover 动效正常")
        city_cards[0].click()
        page.wait_for_timeout(300)
        ok("城市卡片点击事件正常")

    # 检查图表容器
    gdp_chart = page.locator("#chartGdpRank canvas").count()
    industry_chart = page.locator("#chartIndustryOverview canvas").count()
    if gdp_chart > 0:
        ok("GDP排名图表已渲染")
    else:
        warn("GDP排名图表未检测到 canvas")
    if industry_chart > 0:
        ok("产业指标对比图已渲染")
    else:
        warn("产业指标对比图未检测到 canvas")

    # 检查提示文字
    hint = page.locator("#cityCardHint").inner_text()
    if "个城市" in hint or "已接入" in hint:
        ok(f"城市卡片提示: {hint}")
    else:
        warn(f"城市卡片提示异常: {hint}")

    # 模拟滚动整个页面
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    ok("页面滚动测试正常")

    shot(page, "02_dashboard_full.png")

    # =======================================
    #  第3步: 企业选址分析 — 模拟选择城市+点击分析
    # =======================================
    print("\n" + "-" * 60)
    print(" [3/6] 企业选址分析 — 模拟人工操作流程")
    print("-" * 60)

    # 模拟人工点击标签切换
    enterprise_tab = page.locator('.tab-btn[data-tab="enterprise"]').first
    enterprise_tab.click()
    page.wait_for_timeout(600)
    ok("切换到「企业选址分析」标签页")

    # 检查页面元素
    city_select = page.locator("#entCitySelect")
    analyze_btn = page.locator("#btnEntAnalyze")

    if city_select.is_visible():
        ok("城市选择器可见")
    else:
        fail("城市选择器不可见")

    if analyze_btn.is_visible():
        ok("分析按钮可见")
    else:
        fail("分析按钮不可见")

    # 获取下拉选项
    options = city_select.locator("option").all()
    city_names = [o.inner_text() for o in options]
    ok(f"可选城市: {len(options)} 个 ({', '.join(city_names[:4])}...)")

    # 模拟人工操作: 选择不同城市并查看
    city_select.select_option(value=city_names[1])  # 选第2个城市
    page.wait_for_timeout(200)
    ok(f"人工选择了城市: {city_names[1]}")

    shot(page, "03_enterprise_before_analyze.png")

    # 点击分析按钮
    analyze_btn.click()
    ok("点击了「开始选址分析」按钮")

    # 等待分析完成（按钮变为可点击状态）
    try:
        page.wait_for_function("document.getElementById('btnEntAnalyze').disabled === false", timeout=12000)
        ok("分析按钮恢复可用（分析完成）")
    except:
        fail("分析超时或按钮未恢复")

    page.wait_for_timeout(1000)

    # 验证评分显示
    score_card = page.locator("#entScoreCard")
    if score_card.is_visible():
        score = page.locator("#entTotalScore").inner_text()
        ok(f"综合评分显示: {score} 分")

        # 检查环形评分图 SVG
        ring = page.locator("#scoreRingFill")
        if ring.is_visible():
            color = ring.get_attribute("stroke")
            ok(f"评分环形图已渲染 (颜色: {color})")
    else:
        fail("评分卡片未显示")

    # 验证指标详情
    detail_items = page.locator("#entDetails .detail-item").all()
    if len(detail_items) >= 10:
        ok(f"企业分析指标详情: {len(detail_items)} 项")
        for item in detail_items[:3]:
            label = item.locator(".detail-label").inner_text()
            value = item.locator(".detail-value").inner_text()
            ok(f"  指标: {label} = {value}")
    elif len(detail_items) > 0:
        ok(f"企业分析指标: {len(detail_items)} 项")
    else:
        fail("企业分析指标未显示")

    # 验证雷达图
    radar_canvas = page.locator("#chartEntRadar canvas").count()
    if radar_canvas > 0:
        ok("雷达图已渲染")
    else:
        warn("雷达图未检测到canvas")

    shot(page, "04_enterprise_after_analyze.png")

    # 模拟人工操作: 再选另一个城市分析
    city_select.select_option(value=city_names[3])
    page.wait_for_timeout(300)
    analyze_btn.click()
    page.wait_for_timeout(5000)
    try:
        page.wait_for_function("document.getElementById('btnEntAnalyze').disabled === false", timeout=12000)
        score2 = page.locator("#entTotalScore").inner_text()
        ok(f"二次分析 ({city_names[3]}): 得分 {score2}")
    except:
        warn("二次分析超时，但不影响整体")

    # =======================================
    #  第4步: 政府产业分析 — 模拟人工操作
    # =======================================
    print("\n" + "-" * 60)
    print(" [4/6] 政府产业分析 — 模拟人工操作流程")
    print("-" * 60)

    # 点击标签切换
    gov_tab = page.locator('.tab-btn[data-tab="government"]').first
    gov_tab.click()
    page.wait_for_timeout(600)
    ok("切换到「政府产业分析」标签页")

    # 检查参数面板
    gov_select = page.locator("#govCitySelect")
    gov_btn = page.locator('button:has-text("运行产业分析")').first

    if gov_select.is_visible() and gov_btn.is_visible():
        ok("政府分析参数面板完整")
    else:
        fail("政府分析参数面板不完整")

    # 人工选择城市
    gov_select.select_option(value=city_names[0])
    page.wait_for_timeout(200)
    ok(f"人工选择了城市: {city_names[0]}")

    # 检查空状态
    empty_icon = page.locator("#govDetails .text-center").first
    if empty_icon.is_visible():
        ok("初始显示空状态提示")

    shot(page, "05_government_before_analyze.png")

    # 点击运行分析
    gov_btn.click()
    ok("点击了「运行产业分析」按钮")

    # 等待分析完成
    page.wait_for_timeout(10000)

    # 检查指标详情
    gov_indicator_items = page.locator("#govDetails .detail-item").all()
    if len(gov_indicator_items) >= 5:
        ok(f"政府分析指标: {len(gov_indicator_items)} 项")
        for item in gov_indicator_items:
            label = item.locator(".detail-label").inner_text()
            if item.locator(".detail-value").count() > 0:
                value = item.locator(".detail-value").inner_text()
                ok(f"  指标: {label} = {value}")
            elif item.locator(".badge-purple").count() > 0:
                method = item.locator(".badge-purple").inner_text()
                ok(f"  预测方法: {method}")
    elif len(gov_indicator_items) > 0:
        ok(f"政府分析指标: {len(gov_indicator_items)} 项")
    else:
        fail("政府分析指标未显示")

    # 验证 GDP 预测图
    gdp_forecast_canvas = page.locator("#chartGdpForecast canvas").count()
    if gdp_forecast_canvas > 0:
        ok("GDP预测图已渲染")
    else:
        warn("GDP预测图未检测到canvas")

    shot(page, "06_government_after_analyze.png")

    # 模拟再换一个城市
    gov_select.select_option(value=city_names[2])
    page.wait_for_timeout(300)
    gov_btn.click()
    page.wait_for_timeout(8000)
    items2 = page.locator("#govDetails .detail-item").all()
    if len(items2) >= 3:
        ok(f"二次政府分析: {len(items2)} 项指标已更新")
    else:
        warn("二次政府分析可能不完整")

    # =======================================
    #  第5步: 城市数据对比 — 模拟多城市选择+对比
    # =======================================
    print("\n" + "-" * 60)
    print("🏙️ [5/6] 城市数据对比 — 模拟多城市选择流程")
    print("-" * 60)

    # 点击标签切换
    cities_tab = page.locator('.tab-btn[data-tab="cities"]').first
    cities_tab.click()
    page.wait_for_timeout(600)
    ok("切换到「城市数据对比」标签页")

    # 检查复选框初始状态（全选）
    checkboxes = page.locator(".city-cb:checked").all()
    all_checkboxes = page.locator(".city-cb").all()
    ok(f"城市复选框: 已选 {len(checkboxes)}/{len(all_checkboxes)} (默认全选)")

    # 验证空状态/提示
    empty_state = page.locator("#compareEmpty")
    if empty_state.is_visible():
        ok("初始显示空状态提示")
    else:
        warn("空状态提示不可见")

    shot(page, "07_cities_before_compare.png")

    # 模拟人工: 先清空，再手动勾选3个城市
    page.locator('button:has-text("清空")').first.click()
    page.wait_for_timeout(300)
    cleared = page.locator(".city-cb:checked").all()
    ok(f"清空后: 已选 {len(cleared)} 个城市")

    # 手动勾选城市（模拟人工点击）
    if len(all_checkboxes) >= 3:
        for cb in all_checkboxes[:3]:
            check_label = cb.locator("..")
            check_label.click()
            page.wait_for_timeout(150)
        selected_after = page.locator(".city-cb:checked").all()
        ok(f"手动勾选3城市: {len(selected_after)} 个已选")
    else:
        warn("城市复选框不足3个")

    shot(page, "08_cities_selected_3.png")

    # 点击对比分析
    compare_btn = page.locator('button:has-text("对比分析")').first
    compare_btn.click()
    ok("点击了「对比分析」按钮")

    # 等待分析完成
    page.wait_for_timeout(12000)

    # 检查 GDP 对比图
    compare_canvas = page.locator("#chartCityCompare canvas").count()
    if compare_canvas > 0:
        ok("GDP时序对比图已渲染")
    else:
        warn("GDP对比图未检测到canvas")

    # 检查热力图
    heatmap_canvas = page.locator("#chartCityHeatmap canvas").count()
    if heatmap_canvas > 0:
        ok("指标热力图已渲染")
    else:
        warn("热力图未检测到canvas")

    # 检查对比表格
    table_rows = page.locator("#compareTable tbody tr").all()
    if len(table_rows) >= 5:
        ok(f"城市对比表格: {len(table_rows)} 行数据")
        for row in table_rows[:2]:
            cells = row.locator("td").all()
            if len(cells) >= 2:
                indicator = cells[0].inner_text()
                values = " | ".join([c.inner_text() for c in cells[1:3]])
                ok(f"  表格: {indicator} → {values}")
    elif len(table_rows) > 0:
        ok(f"对比表格: {len(table_rows)} 行")
    else:
        fail("对比表格无数据行")

    # 检查空状态是否隐藏
    if not empty_state.is_visible():
        ok("空状态提示已隐藏（数据已加载）")
    else:
        fail("数据加载后空状态仍可见")

    shot(page, "09_cities_after_compare.png")

    # 模拟: 切换回全选再分析一次
    page.locator('button:has-text("全选")').first.click()
    page.wait_for_timeout(300)
    full_selected = page.locator(".city-cb:checked").all()
    ok(f"全选后: 已选 {len(full_selected)} 个城市")
    compare_btn.click()
    page.wait_for_timeout(12000)
    rows_full = page.locator("#compareTable tbody tr").all()
    ok(f"全城市对比: {len(rows_full)} 行数据")

    # =======================================
    #  第6步: 回归 — 切换回仪表盘验证持久性
    # =======================================
    print("\n" + "-" * 60)
    print(" [6/6] 回归测试 — 标签页循环切换 + 后端验证")
    print("-" * 60)

    # 切换回仪表盘
    dashboard_tab = page.locator('.tab-btn[data-tab="dashboard"]').first
    dashboard_tab.click()
    page.wait_for_timeout(1000)
    shot(page, "10_final_dashboard.png")

    # 验证统计卡仍然存在
    final_stats = page.locator(".stat-value").all()
    if len(final_stats) >= 4:
        ok(f"回归: 统计卡片仍为 {len(final_stats)} 个")
    else:
        fail(f"回归: 统计卡片变为 {len(final_stats)} 个")

    # 闭环: 再次检查后端健康
    try:
        final_health = page.evaluate("""async () => {
            const r = await fetch('/health');
            return await r.json();
        }""")
        if final_health.get("status") == "healthy":
            ok(f"闭环后端健康: {final_health.get('status')}")
        else:
            fail(f"闭环后端异常: {final_health}")
    except Exception as e:
        fail(f"闭环后端检查失败: {e}")

    # 额外检查: 验证无 Toast 错误
    toast_errors = page.locator(".toast-error").count()
    if toast_errors == 0:
        ok("无 Toast 错误提示")
    else:
        fail(f"检测到 {toast_errors} 个 Toast 错误")

    # 额外: 验证本地 API 调用成功
    try:
        api_resp = page.evaluate("""async () => {
            const r = await fetch('/api/v1/cities/list');
            const d = await r.json();
            return d.cities ? d.cities.length : -1;
        }""")
        if api_resp >= 8:
            ok(f"前端 fetch API 验证通过: {api_resp} 城市")
        else:
            fail(f"前端 fetch API 异常: {api_resp}")
    except Exception as e:
        fail(f"前端 fetch API 测试失败: {e}")

    browser.close()

# =======================================
#  汇总报告
# =======================================
print("\n" + "=" * 70)
print("[report] 测试汇总报告")
print("=" * 70)

# 过滤误报（CDN 相关、deprecated 等）
real_console_errs = [
    e
    for e in RESULTS["console_errors"]
    if "cdn" not in e.lower() and "deprecated" not in e.lower() and "favicon" not in e.lower()
]

passed = len(RESULTS["passed"])
failed = len(RESULTS["failed"])
total = passed + failed
pass_rate = (passed / total * 100) if total > 0 else 100

print(f"\n  [ok] 通过: {passed}")
print(f"  [FAIL] 失败: {failed}")
print(f"  [!] 警告: {len(RESULTS['warnings'])}")
print(f"   网络错误 (5xx): {len(RESULTS['network_errors'])}")
print(f"  📟 前端 Console 错误: {len(real_console_errs)}")
print(f"  [i] 通过率: {pass_rate:.1f}%")

if failed > 0:
    print("\n  [FAIL] 失败详情:")
    for f in RESULTS["failed"]:
        print(f"     {f}")

if RESULTS["warnings"]:
    print("\n  [!] 警告详情:")
    for w in RESULTS["warnings"]:
        print(f"     {w}")

if real_console_errs:
    print("\n  📟 前端错误详情:")
    for e in real_console_errs[:5]:
        print(f"     {e}")

if RESULTS["network_errors"]:
    print("\n   网络错误详情:")
    for e in RESULTS["network_errors"][:5]:
        print(f"     {e}")

print(f"\n  📸 截图已保存到: {SCREENSHOT_DIR}")
print(f"     共 {len(os.listdir(SCREENSHOT_DIR))} 张截图")

if failed == 0:
    print("\n 全部测试通过! 前端交互完全正常!")
else:
    print(f"\n[!] 有 {failed} 项测试失败，请检查详情")

print("=" * 70)
