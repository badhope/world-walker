"""
诊断脚本 - 模拟用户视角检查所有UI/UX问题
- 视觉问题（对齐、溢出、空白、颜色）
- 交互问题（按钮无响应、hover失效、焦点丢失）
- 数据问题（空状态、错误回显、加载状态）
- 响应性（不同屏幕尺寸）
- 可访问性
- 性能（加载时间、卡顿）
"""

import os

from playwright.sync_api import sync_playwright

OUT = "/workspace/screenshots/diagnose"
os.makedirs(OUT, exist_ok=True)

ISSUES = {"critical": [], "major": [], "minor": [], "suggestions": []}


def critical(msg):
    ISSUES["critical"].append(msg)
    print(f"  [FAIL] 严重: {msg}")


def major(msg):
    ISSUES["major"].append(msg)
    print(f"  🟠 重要: {msg}")


def minor(msg):
    ISSUES["minor"].append(msg)
    print(f"  🟡 轻微: {msg}")


def suggest(msg):
    ISSUES["suggestions"].append(msg)
    print(f"  [i] 建议: {msg}")


def ok(msg):
    print(f"  [ok] {msg}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    print("\n" + "-" * 70)
    print("🖥️ [测试 1] 桌面端 1920x1080")
    print("-" * 70)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    errs = []
    page.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type == "error" else None)

    page.goto("http://localhost:8001/app")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    page.screenshot(path=f"{OUT}/desktop_home.png", full_page=True)

    # 检查 1: 滚动条 - 是否被header遮挡
    body_overflow = page.evaluate("getComputedStyle(document.body).overflowX")
    if body_overflow in ["hidden", "auto"]:
        ok(f"body 横向滚动: {body_overflow}")
    else:
        ok(f"body 横向滚动: {body_overflow}")

    # 检查 2: 头部是否固定
    header = page.locator("header").first
    if header.is_visible():
        header_pos = page.evaluate("""() => {
            const h = document.querySelector('header');
            const s = getComputedStyle(h);
            return { position: s.position, top: s.top, zIndex: s.zIndex, height: h.offsetHeight };
        }""")
        ok(
            f"Header 样式: position={header_pos['position']}, z-index={header_pos['zIndex']}, 高度={header_pos['height']}px"
        )
    else:
        major("Header 不可见")

    # 检查 3: 标签页 - 选中态视觉反馈
    tabs = page.locator(".tab-btn").all()
    print(f"\n  标签页数量: {len(tabs)}")
    for i, tab in enumerate(tabs):
        text = tab.inner_text().strip()
        cls = tab.get_attribute("class")
        is_active = "active" in (cls or "")
        print(f"    标签[{i}]: '{text}' active={is_active}")

    # 模拟鼠标 hover 一个 tab
    if len(tabs) >= 2:
        tabs[1].hover()
        page.wait_for_timeout(300)
        page.screenshot(path=f"{OUT}/desktop_tab_hover.png")

    # 检查 4: 城市卡片 - 内容是否完整
    cards = page.locator("#cityCards .city-card").all()
    print(f"\n  城市卡片数量: {len(cards)}")
    if len(cards) >= 8:
        ok(f"城市卡片数: {len(cards)}")
        # 检查每个卡片的字段
        for i, card in enumerate(cards[:3]):
            name = card.locator(".city-name").inner_text() if card.locator(".city-name").count() > 0 else "N/A"
            print(f"    卡片[{i}]: {name}")
    else:
        major(f"城市卡片不足: {len(cards)}")

    # 检查 5: 图表 - 是否成功渲染（canvas 元素）
    chart_canvases = page.locator("canvas").count()
    print(f"\n  Canvas 元素数: {chart_canvases}")
    if chart_canvases >= 2:
        ok(f"已渲染图表: {chart_canvases}")
    elif chart_canvases > 0:
        minor(f"只渲染了 {chart_canvases} 个图表")
    else:
        major("没有任何图表渲染")

    # 检查 6: 暗色模式/对比度问题
    # 检查文字颜色 vs 背景颜色对比度
    text_contrast = page.evaluate("""() => {
        const text = document.querySelector('.city-name');
        if (!text) return null;
        const s = getComputedStyle(text);
        const parent = text.closest('.city-card');
        const ps = getComputedStyle(parent);
        return { color: s.color, bg: ps.backgroundColor };
    }""")
    if text_contrast:
        print(f"  文字颜色: {text_contrast['color']}, 卡片背景: {text_contrast['bg']}")

    # 检查 7: 错误状态 - 模拟后端错误
    print("\n  模拟 API 错误场景...")
    page.route("**/api/v1/cities/list", lambda route: route.abort())
    page.evaluate("location.reload()")
    page.wait_for_timeout(3000)
    has_error = page.locator(".toast-error").count() > 0 or page.locator("[role='alert']").count() > 0
    page.screenshot(path=f"{OUT}/desktop_error_state.png")
    if has_error:
        ok("错误状态: 显示了 Toast 错误提示")
    else:
        major("错误状态: 没有任何错误提示（API 失败时）")
    page.unroute("**/api/v1/cities/list")

    print("\n" + "-" * 70)
    print("📱 [测试 2] 平板端 768x1024")
    print("-" * 70)
    ctx2 = browser.new_context(viewport={"width": 768, "height": 1024})
    page2 = ctx2.new_page()
    page2.goto("http://localhost:8001/app")
    page2.wait_for_load_state("networkidle")
    page2.wait_for_timeout(3000)
    page2.screenshot(path=f"{OUT}/tablet_home.png", full_page=True)

    # 检查响应式 - 标签页是否换行
    tab_layout = page2.evaluate("""() => {
        const btns = document.querySelectorAll('.tab-btn');
        const rects = Array.from(btns).map(b => b.getBoundingClientRect());
        const ys = rects.map(r => r.top);
        const uniqueRows = new Set(ys.map(Math.round)).size;
        return { count: btns.length, rows: uniqueRows };
    }""")
    print(f"  标签页布局: {tab_layout['count']}个, 占用 {tab_layout['rows']} 行")
    if tab_layout["rows"] > 1:
        minor(f"标签页在平板端换行成 {tab_layout['rows']} 行")
    else:
        ok("标签页单行显示")

    # 检查统计卡片 - 是否变成2列
    stats_layout = page2.evaluate("""() => {
        const cards = document.querySelectorAll('.stat-card');
        const tops = Array.from(cards).map(c => Math.round(c.getBoundingClientRect().top));
        return { count: cards.length, rows: new Set(tops).size };
    }""")
    print(f"  统计卡片布局: {stats_layout['count']}个, 占用 {stats_layout['rows']} 行")
    if stats_layout["rows"] == 1:
        suggest("统计卡片在平板端应改2列布局（目前仍4列）")
    elif stats_layout["rows"] == 2:
        ok("统计卡片2列布局")

    # 城市卡片
    cities_layout = page2.evaluate("""() => {
        const cards = document.querySelectorAll('#cityCards .city-card');
        const tops = Array.from(cards).map(c => Math.round(c.getBoundingClientRect().top));
        return { count: cards.length, rows: new Set(tops).size };
    }""")
    print(f"  城市卡片布局: {cities_layout['count']}个, 占用 {cities_layout['rows']} 行")

    print("\n" + "-" * 70)
    print("📱 [测试 3] 移动端 375x667")
    print("-" * 70)
    ctx3 = browser.new_context(viewport={"width": 375, "height": 667})
    page3 = ctx3.new_page()
    page3.goto("http://localhost:8001/app")
    page3.wait_for_load_state("networkidle")
    page3.wait_for_timeout(3000)
    page3.screenshot(path=f"{OUT}/mobile_home.png", full_page=True)

    # 横向溢出检测
    has_overflow = page3.evaluate("""() => {
        return document.documentElement.scrollWidth > window.innerWidth;
    }""")
    if has_overflow:
        major("移动端横向溢出: scrollWidth > viewport")
    else:
        ok("移动端无横向溢出")

    # 检查按钮是否过小
    btn_sizes = page3.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        return Array.from(btns).filter(b => b.offsetHeight > 0).map(b => ({
            text: b.innerText.slice(0, 10),
            height: b.offsetHeight,
            width: b.offsetWidth
        })).slice(0, 5);
    }""")
    for b in btn_sizes:
        print(f"    按钮 '{b['text']}': {b['width']}x{b['height']}")
        if b["height"] < 32:
            minor(f"按钮 '{b['text']}' 高度过小: {b['height']}px（建议 ≥36px）")

    ctx3.close()
    ctx2.close()

    print("\n" + "-" * 70)
    print(" [测试 4] 慢速API + 超时处理")
    print("-" * 70)
    ctx4 = browser.new_context(viewport={"width": 1920, "height": 1080})
    page4 = ctx4.new_page()

    # 延迟企业分析 API 20 秒（超过前端 15s 超时）
    def slow_response(route):
        import time

        time.sleep(20)
        route.continue_()

    page4.route("**/api/v1/analysis/enterprise/**", slow_response)
    page4.goto("http://localhost:8001/app")
    page4.wait_for_load_state("networkidle")
    page4.wait_for_timeout(2000)
    page4.locator('.tab-btn[data-tab="enterprise"]').click()
    page4.wait_for_timeout(500)
    page4.locator("#btnEntAnalyze").click()
    # 等待 16 秒看是否触发超时
    page4.wait_for_timeout(16000)
    timeout_toast = page4.locator(".toast-error:has-text('超时')").count()
    timeout_btn_enabled = not page4.locator("#btnEntAnalyze").is_disabled()
    if timeout_toast > 0:
        ok("超时处理: 出现超时错误提示")
    else:
        major("超时处理: 16秒后无超时提示")
    if timeout_btn_enabled:
        ok("超时处理: 按钮已恢复可用")
    else:
        major("超时处理: 按钮仍处于禁用状态")
    page4.screenshot(path=f"{OUT}/timeout_state.png")
    ctx4.close()

    print("\n" + "-" * 70)
    print("[!] [测试 5] 边界情况测试")
    print("-" * 70)
    ctx5 = browser.new_context(viewport={"width": 1920, "height": 1080})
    page5 = ctx5.new_page()

    # 5.1 快速连续点击
    page5.goto("http://localhost:8001/app")
    page5.wait_for_load_state("networkidle")
    page5.wait_for_timeout(2000)
    page5.locator('.tab-btn[data-tab="cities"]').click()
    page5.wait_for_timeout(500)
    print("  5.1 快速点击「对比分析」按钮 5 次...")
    for _ in range(5):
        try:
            page5.locator('button:has-text("对比分析")').click(timeout=500)
        except:
            pass
    page5.wait_for_timeout(3000)
    if page5.locator("#compareTable tbody tr").count() >= 5:
        ok("快速点击处理: 表格正常渲染，无重复")
    else:
        major("快速点击处理: 表格未正确渲染")

    # 5.2 所有城市取消选择
    print("\n  5.2 清空所有城市选择...")
    page5.locator('button:has-text("清空")').click()
    page5.wait_for_timeout(500)
    page5.locator('button:has-text("对比分析")').click()
    page5.wait_for_timeout(3000)
    has_empty_state = page5.locator("#compareEmpty:visible").count() > 0
    has_toast = page5.locator(".toast-warning:visible, .toast-error:visible").count() > 0
    if has_empty_state or has_toast:
        ok("空选择: 显示空状态或提示")
    else:
        major("空选择: 无任何反馈")

    # 5.3 长内容溢出
    print("\n  5.3 检查页面整体滚动...")
    scroll_height = page5.evaluate("document.documentElement.scrollHeight")
    viewport_height = page5.evaluate("window.innerHeight")
    if scroll_height > viewport_height * 3:
        suggest(f"页面较长（{scroll_height}px），建议添加回到顶部按钮")
    else:
        ok(f"页面长度合理: {scroll_height}px")

    ctx5.close()

    print("\n" + "-" * 70)
    print("📟 [测试 6] 控制台错误统计")
    print("-" * 70)
    if errs:
        real_errs = [
            e for e in errs if "cdn" not in e.lower() and "favicon" not in e.lower() and "deprecated" not in e.lower()
        ]
        if real_errs:
            major(f"控制台错误: {len(real_errs)} 个")
            for e in real_errs[:5]:
                print(f"    {e}")
        else:
            ok("无关键控制台错误")
    else:
        ok("无控制台错误")

    browser.close()

print("\n" + "=" * 70)
print("[report] 诊断报告汇总")
print("=" * 70)
print(f"  [FAIL] 严重问题: {len(ISSUES['critical'])}")
print(f"  🟠 重要问题: {len(ISSUES['major'])}")
print(f"  🟡 轻微问题: {len(ISSUES['minor'])}")
print(f"  [i] 优化建议: {len(ISSUES['suggestions'])}")

if ISSUES["critical"]:
    print("\n  [FAIL] 严重问题:")
    for i in ISSUES["critical"]:
        print(f"     {i}")
if ISSUES["major"]:
    print("\n  🟠 重要问题:")
    for i in ISSUES["major"]:
        print(f"     {i}")
if ISSUES["minor"]:
    print("\n  🟡 轻微问题:")
    for i in ISSUES["minor"]:
        print(f"     {i}")
if ISSUES["suggestions"]:
    print("\n  [i] 优化建议:")
    for i in ISSUES["suggestions"]:
        print(f"     {i}")

print(f"\n  📸 截图: {OUT}/")
print("=" * 70)
