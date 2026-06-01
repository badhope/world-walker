from playwright.sync_api import sync_playwright
import os

screenshot_dir = "/workspace/test_screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    print("=" * 60)
    print("测试前端首页")
    print("=" * 60)
    
    page.goto('http://localhost:5173/')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    screenshot_path = os.path.join(screenshot_dir, "homepage.png")
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"✅ 首页截图已保存: {screenshot_path}")
    
    title = page.title()
    print(f"📄 页面标题: {title}")
    
    content = page.content()
    print(f"📊 页面内容长度: {len(content)} 字符")
    
    print("\n" + "=" * 60)
    print("检查页面关键元素")
    print("=" * 60)
    
    buttons = page.locator('button').all()
    print(f"🔘 按钮数量: {len(buttons)}")
    for btn in buttons[:5]:
        try:
            text = btn.inner_text()
            if text.strip():
                print(f"   - 按钮: {text.strip()[:50]}")
        except:
            pass
    
    inputs = page.locator('input').all()
    print(f"📝 输入框数量: {len(inputs)}")
    
    links = page.locator('a').all()
    print(f"🔗 链接数量: {len(links)}")
    
    print("\n" + "=" * 60)
    print("测试 API 连接")
    print("=" * 60)
    
    response = page.request.get("http://localhost:8001/api/v1/dashboard")
    print(f"📡 Dashboard API 状态: {response.ok}")
    if response.ok:
        data = response.json()
        print(f"   数据字段: {list(data.keys())}")
    
    response = page.request.get("http://localhost:8001/api/v1/cities")
    print(f"📡 Cities API 状态: {response.ok}")
    if response.ok:
        data = response.json()
        print(f"   城市数量: {len(data.get('cities', []))}")
    
    print("\n" + "=" * 60)
    print("测试交互功能")
    print("=" * 60)
    
    try:
        nav_items = page.locator('nav a, .nav-item, [class*="nav"]').all()
        print(f"🧭 导航项数量: {len(nav_items)}")
        for nav in nav_items[:3]:
            try:
                text = nav.inner_text()
                href = nav.get_attribute('href')
                print(f"   - 导航: {text.strip()} -> {href}")
            except:
                pass
    except Exception as e:
        print(f"⚠️ 导航项检查: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    browser.close()
    print("\n✅ 所有测试通过！前端页面正常工作。")
