"""
API验证 + 静态代码审查
不依赖浏览器，直接验证后端 + 分析前端代码潜在问题
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "http://localhost:8000"
results = {
    "api_pass": [],
    "api_fail": [],
    "code_issues": [],
    "perf_issues": [],
    "a11y_issues": [],
    "security_issues": [],
}


def ok(msg):
    results["api_pass"].append(msg)
    print(f"  [ok] {msg}")


def fail(msg):
    results["api_fail"].append(msg)
    print(f"  [FAIL] {msg}")


def http_get(path, timeout=15):
    """GET 请求"""
    url = f"{API}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def http_post(path, data, timeout=15):
    """POST 请求"""
    url = f"{API}{path}"
    try:
        req = urllib.request.Request(
            url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


# =======================================
#  第1部分: API 端点验证
# =======================================
print("\n" + "-" * 70)
print(" [1/5] 全部 API 端点验证")
print("-" * 70)

endpoints = [
    ("GET", "/health", None),
    ("GET", "/", None),
    ("GET", "/app", None),
    ("GET", "/dashboard", None),
    ("GET", "/api/v1/cities/list", None),
    ("GET", "/api/v1/cities/%E6%B7%B1%E5%9C%B3", None),
    ("GET", "/api/v1/cities/%E6%B7%B1%E5%9C%B3/historical", None),
    ("GET", "/api/v1/analysis/enterprise/v3/%E6%B7%B1%E5%9C%B3", None),
    ("GET", "/api/v1/forecast/gdp/%E6%B7%B1%E5%9C%B3?forecast_years=3", None),
]

for method, path, body in endpoints:
    if method == "GET":
        status, text = http_get(path)
    else:
        status, text = http_post(path, body or {})
    if status == 200:
        ok(f"{method} {path} → 200")
    elif status in [0]:
        fail(f"{method} {path} → 连接失败: {text[:80]}")
    else:
        fail(f"{method} {path} → {status}: {text[:100]}")

# POST endpoints
post_endpoints = [
    (
        "/api/v1/cities/time-series",
        {
            "city_codes": ["深圳", "上海"],
            "indicator": "gdp",
            "year_start": 2020,
            "year_end": 2025,
            "group_by": ["city"],
        },
    ),
    ("/api/v1/cities/compare", ["深圳", "北京", "广州"]),
]
for path, body in post_endpoints:
    status, text = http_post(path, body)
    if status == 200:
        ok(f"POST {path} → 200")
    else:
        fail(f"POST {path} → {status}: {text[:100]}")

# 检查关键数据完整性
print("\n  [i] 关键数据完整性检查")
status, text = http_get("/api/v1/cities/list")
if status == 200:
    data = json.loads(text)
    cities = data.get("cities", [])
    print(f"    城市列表: {len(cities)} 个")
    for city in cities:
        print(f"      - {city}")
    if len(cities) >= 8:
        ok("8个城市数据完整")
    else:
        fail(f"城市数量不足: {len(cities)}")

# 检查企业分析关键字段
status, text = http_get("/api/v1/analysis/enterprise/v3/%E6%B7%B1%E5%9C%B3")
if status == 200:
    data = json.loads(text)
    score = data.get("total_score")
    cost_d = data.get("details", {}).get("cost_details", {})
    sup_d = data.get("details", {}).get("supply_details", {})
    pol_d = data.get("details", {}).get("policy_details", {})

    print("\n  企业分析字段 (深圳):")
    print(f"    总分: {score}")
    print(f"    成本字段: {list(cost_d.keys())}")
    print(f"    供应字段: {list(sup_d.keys())}")
    print(f"    政策字段: {list(pol_d.keys())}")

    if score and score > 0:
        ok(f"企业分析总分: {score}")
    else:
        fail("企业分析总分为空")

    if "减税降费" in pol_d:
        ok(f"政策字段 '减税降费' 存在: {pol_d['减税降费']}")
    else:
        fail("政策字段 '减税降费' 缺失")

# 检查热力图数据 - 重要！前端使用 tax_reduction 字段
status, text = http_get("/api/v1/cities/%E6%B7%B1%E5%9C%B3")
if status == 200:
    data = json.loads(text).get("data", {})
    if "tax_reduction" in data:
        ok(f"tax_reduction 字段存在: {data['tax_reduction']}")
    else:
        fail("tax_reduction 字段缺失")

# =======================================
#  第2部分: 前端代码静态分析
# =======================================
print("\n" + "-" * 70)
print("[scan] [2/5] 前端 HTML/JS 静态代码审查")
print("-" * 70)

html_path = Path("/workspace/frontend/index.html")
html = html_path.read_text(encoding="utf-8")
print(f"  文件大小: {len(html):,} 字节")

# 2.1 检查空状态/错误处理
checks = [
    (r"loc\.origin|window\.location\.origin|resolveApiBase|api-base", "动态 API 基础 URL (无硬编码)"),
    (r"AbortController", "API 超时控制 (AbortController)"),
    (r"\.toast-error|toast\.error|toast-success", "Toast 通知系统"),
    (r"\.skeleton|skeleton-", "骨架屏加载状态"),
    (r"echarts\.getInstanceByDom.*dispose", "ECharts 实例正确清理"),
    (r"btnEntAnalyze.*disabled|loading", "按钮 loading 状态"),
    (r"addEventListener.*error", "错误事件监听"),
    (r"@media.*max-width.*768", "响应式断点"),
    (r"@media.*max-width.*480", "移动端断点"),
    (r"viewport.*device-width", "viewport meta"),
    (r"lang=.zh-CN.", "中文 lang 声明"),
    (r"aria-label|aria-hidden|role=", "ARIA 无障碍属性"),
]
for pattern, desc in checks:
    if re.search(pattern, html):
        ok(f"已实现: {desc}")
    else:
        results["code_issues"].append(desc)
        print(f"  [!]  缺失: {desc}")

# 2.2 检查潜在问题
issues_to_check = [
    (r"alert\(", "使用了 alert()（应改用 Toast）", "code_issues"),
    (r"localhost:8001", "硬编码了 localhost:8001（应该用 window.location.origin）", "code_issues"),
    (r"href=.[\"']javascript:[\"']", "javascript: 协议（XSS风险）", "security_issues"),
    (r"innerHTML\s*=\s*[\"']\s*\+", "字符串拼接的 innerHTML（XSS风险）", "security_issues"),
    (r"innerHTML\s*=\s*.*\+.*[a-zA-Z]", "innerHTML 拼接变量（XSS风险）", "security_issues"),
    (r"eval\(", "使用 eval()", "security_issues"),
    (r"setTimeout\([^,]+,\s*[0-9]{6,}\)", "长时间 setTimeout（性能问题）", "perf_issues"),
    (r"document\.write", "document.write", "code_issues"),
    (r"console\.log", "生产环境 console.log", "code_issues"),
]
for pattern, desc, category in issues_to_check:
    matches = re.findall(pattern, html)
    if matches:
        results[category].append(f"{desc} ({len(matches)} 处)")
        print(f"  [scan] {desc}: {len(matches)} 处")

# 2.3 检查图表配置 - 是否启用动画和交互
chart_check = [
    (r"animation:\s*true", "ECharts 动画开启"),
    (r"tooltip:", "Tooltip 提示"),
    (r"legend:", "Legend 图例"),
    (r"grid:", "Grid 网格"),
    (r"xAxis:|yAxis:", "坐标轴"),
]
for p, d in chart_check:
    if re.search(p, html):
        ok(f"图表配置: {d}")
    else:
        results["code_issues"].append(f"图表配置缺失: {d}")
        print(f"  [!]  图表配置: {d}")

# 2.4 检查无障碍（a11y）
a11y = [
    (r"<html[^>]*lang=", "html lang 属性"),
    (r"<button[^>]*type=.button.", "按钮 type 属性"),
    (r":focus-visible|:focus", "焦点可见状态"),
    (r"tabindex", "tabindex 键盘导航"),
]
for p, d in a11y:
    if re.search(p, html):
        ok(f"无障碍: {d}")
    else:
        results["a11y_issues"].append(d)
        print(f"  [a11y] 无障碍缺失: {d}")

# 2.4b 图片 alt 文本（仅在存在 <img> 标签时校验）
img_tags = re.findall(r"<img\b[^>]*>", html, re.IGNORECASE)
if img_tags:
    imgs_without_alt = [tag for tag in img_tags if "alt=" not in tag.lower()]
    if imgs_without_alt:
        results["a11y_issues"].append(f"{len(imgs_without_alt)} 张 <img> 缺少 alt 文本")
        print(f"  [a11y] 无障碍缺失: {len(imgs_without_alt)} 张 <img> 缺少 alt 文本")
    else:
        ok(f"无障碍: 所有 {len(img_tags)} 张 <img> 均有 alt 文本")
else:
    ok("无障碍: 页面未使用 <img>（CSS/SVG-only，无需 alt 校验）")

# 2.5 检查 SEO/元数据
seo = [
    (r"<title>.*</title>", "页面标题"),
    (r"<meta\s+name=.description.", "meta description"),
    (r"<meta\s+property=.og:", "Open Graph 元数据"),
    (r"<link\s+rel=.icon.", "favicon"),
]
for p, d in seo:
    if re.search(p, html):
        ok(f"SEO: {d}")
    else:
        results["code_issues"].append(f"SEO缺失: {d}")
        print(f"  [+] SEO缺失: {d}")

# 2.6 关键 UI 模式检查
ui_patterns = [
    (r"aria-busy|aria-live", "ARIA 实时状态"),
    (r"loading=|isLoading", "加载状态管理"),
    (r"errorMessage|errorDetail", "错误信息展示"),
    (r"emptyState|noData|暂无", "空状态组件"),
    (r"retry|重试|重连接", "重试机制"),
    (r"skeleton", "骨架屏"),
    (r"debounce|throttle", "防抖/节流"),
]
for p, d in ui_patterns:
    if re.search(p, html):
        ok(f"UI模式: {d}")
    else:
        print(f"  [i] UI建议: {d}")

# =======================================
#  第3部分: 性能分析
# =======================================
print("\n" + "-" * 70)
print("[perf] [3/5] 性能分析")
print("-" * 70)

import time

# API 响应时间
api_times = []
for ep in ["/health", "/api/v1/cities/list", "/api/v1/cities/%E6%B7%B1%E5%9C%B3/historical"]:
    start = time.time()
    status, _ = http_get(ep)
    elapsed = (time.time() - start) * 1000
    api_times.append((ep, status, elapsed))

for ep, status, t in api_times:
    if status == 200:
        if t < 200:
            ok(f"{ep}: {t:.0f}ms (优秀)")
        elif t < 500:
            ok(f"{ep}: {t:.0f}ms (良好)")
        elif t < 1500:
            print(f"  🟡 {ep}: {t:.0f}ms (偏慢)")
            results["perf_issues"].append(f"{ep} 偏慢: {t:.0f}ms")
        else:
            print(f"  [FAIL] {ep}: {t:.0f}ms (慢)")
            results["perf_issues"].append(f"{ep} 慢: {t:.0f}ms")

# 前端体积
fe_size = len(html)
if fe_size < 50_000:
    ok(f"前端体积合理: {fe_size / 1024:.1f}KB")
elif fe_size < 100_000:
    print(f"  🟡 前端体积: {fe_size / 1024:.1f}KB")
else:
    print(f"  [FAIL] 前端过大: {fe_size / 1024:.1f}KB")
    results["perf_issues"].append(f"前端过大: {fe_size / 1024:.1f}KB")

# 同步分析大文件
eod = re.findall(r"echarts", html, re.IGNORECASE)
print(f"  ECharts 引用数: {len(eod)}")

# =======================================
#  第4部分: 业务逻辑验证
# =======================================
print("\n" + "-" * 70)
print("💼 [4/5] 业务逻辑验证")
print("-" * 70)

# 4.1 评分合理性
print("\n  城市评分对比:")
all_scores = []
for city_code in ["%E6%B7%B1%E5%9C%B3", "%E4%B8%8A%E6%B5%B7", "%E5%8C%97%E4%BA%AC", "%E5%B9%BF%E5%B7%9E"]:
    status, text = http_get(f"/api/v1/analysis/enterprise/v3/{city_code}")
    if status == 200:
        d = json.loads(text)
        score = d.get("total_score", 0)
        cost = d.get("business_cost_score", 0)
        sup = d.get("supply_chain_score", 0)
        pol = d.get("policy_benefit_score", 0)
        city_name = urllib.parse.unquote(city_code)
        print(f"    {city_name}: 总={score} 成本={cost} 供应={sup} 政策={pol}")
        all_scores.append(score)

if all_scores:
    if max(all_scores) - min(all_scores) > 5:
        ok(f"评分有差异 (差 {max(all_scores) - min(all_scores):.1f} 分)")
    else:
        print(f"  🟡 评分差异小: 范围 {min(all_scores):.1f}-{max(all_scores):.1f}")

# 4.2 GDP 预测合理性
print("\n  GDP 预测验证:")
for city in ["%E6%B7%B1%E5%9C%B3", "%E4%B8%8A%E6%B5%B7", "%E5%8C%97%E4%BA%AC"]:
    status, text = http_get(f"/api/v1/forecast/gdp/{city}?forecast_years=3")
    if status == 200:
        d = json.loads(text)
        forecasts = d.get("forecast_data", [])
        method = d.get("forecast_method", "unknown")
        print(f"    {urllib.parse.unquote(city)}: 方法={method}, 预测点={len(forecasts)}")
        if forecasts:
            last = forecasts[-1]
            year = last.get("year")
            val = last.get("forecast")
            print(f"      {year}: {val:.0f} 亿元")

# 4.3 时间序列对比 - 中文名验证
print("\n  时间序列对比:")
status, text = http_post(
    "/api/v1/cities/time-series",
    {
        "city_codes": ["深圳", "上海", "北京"],
        "indicator": "gdp",
        "year_start": 2020,
        "year_end": 2025,
        "group_by": ["city"],
    },
)
if status == 200:
    d = json.loads(text)
    ts = d.get("time_series", {})
    groups = ts.get("groups", [])
    if groups:
        for g in groups:
            if isinstance(g.get("groups"), list) and g.get("groups"):
                group_name = str(g.get("groups")[0])
            elif g.get("city"):
                group_name = str(g.get("city"))
            else:
                group_name = "未知"
            points = g.get("time_points", [])
            print(f"    {group_name}: {len(points)} 数据点")
            if group_name in ["深圳", "上海", "北京", "广州"]:
                ok(f"分组名是中文: '{group_name}'")
            else:
                print(f"  [FAIL] 分组名是代码: '{group_name}'")
                fail(f"分组名应中文实际 '{group_name}'")

# =======================================
#  第5部分: 文件结构 & 文档
# =======================================
print("\n" + "-" * 70)
print(" [5/5] 项目结构完整性")
print("-" * 70)

required_files = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    "frontend/index.html",
    "backend/api/main.py",
    "backend/data/city_data.py",
    "tests/backend/test_analysis.py",
]
for f in required_files:
    p = Path(f"/workspace/{f}")
    if p.exists():
        ok(f"{f}: {p.stat().st_size:,} 字节")
    else:
        fail(f"{f}: 不存在")

print("\n" + "=" * 70)
print("[report] 诊断报告")
print("=" * 70)
print(f"  [ok] API 通过: {len(results['api_pass'])}")
print(f"  [FAIL] API 失败: {len(results['api_fail'])}")
print(f"  [scan] 代码问题: {len(results['code_issues'])}")
print(f"  [perf] 性能问题: {len(results['perf_issues'])}")
print(f"  [a11y] 无障碍问题: {len(results['a11y_issues'])}")
print(f"  [sec] 安全问题: {len(results['security_issues'])}")

if results["api_fail"]:
    print("\n  [FAIL] API 失败:")
    for x in results["api_fail"]:
        print(f"     {x}")
if results["code_issues"]:
    print("\n  [scan] 代码问题:")
    for x in results["code_issues"]:
        print(f"     {x}")
if results["perf_issues"]:
    print("\n  [perf] 性能问题:")
    for x in results["perf_issues"]:
        print(f"     {x}")
if results["a11y_issues"]:
    print("\n  [a11y] 无障碍问题:")
    for x in results["a11y_issues"]:
        print(f"     {x}")
if results["security_issues"]:
    print("\n  [sec] 安全问题:")
    for x in results["security_issues"]:
        print(f"     {x}")

print("=" * 70)
