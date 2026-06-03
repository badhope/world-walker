"""
安全回归测试:前端 CSP 与 SRI (M-03)

防御:CDN 资源(Tailwind / ECharts)被劫持后被恶意替换;以及
任意脚本在浏览器执行导致 XSS 持久化。

修复:在 index.html 头部添加 Content-Security-Policy meta 标签,
并为所有外部脚本添加 SRI integrity 属性。
"""

import re
from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).resolve().parents[2] / "frontend" / "index.html"


@pytest.mark.unit
class TestFrontendCSP:
    """index.html 必须包含限制性的 Content-Security-Policy。"""

    @pytest.fixture
    def html_text(self):
        return FRONTEND_HTML.read_text(encoding="utf-8")

    def test_csp_meta_tag_present(self, html_text):
        assert 'http-equiv="Content-Security-Policy"' in html_text, "CSP meta tag must be present in <head>"

    def test_csp_eval_restricted_to_script_src(self, html_text):
        """'unsafe-eval' 如必须存在,只能出现在 script-src 中(不能扩散到其他指令)。

        实际: Tailwind CDN 在浏览器端 JIT 编译会调用 eval/Function,
        因此 script-src 需要 'unsafe-eval'。但 default-src / style-src
        / connect-src 等绝不能放行 eval。
        """
        m = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"', html_text)
        assert m
        csp = m.group(1)
        # 拆分每条指令
        directives = [d.strip() for d in csp.split(";") if d.strip()]
        for d in directives:
            name, _, _ = d.partition(" ")
            if "'unsafe-eval'" in d and name != "script-src":
                pytest.fail(f"'unsafe-eval' leaked into non-script directive: {d!r}")

    def test_csp_has_default_src_self(self, html_text):
        m = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"', html_text)
        assert m
        csp = m.group(1)
        assert "default-src 'self'" in csp, f"CSP must include default-src 'self': {csp}"

    def test_csp_whitelists_tailwind_cdn(self, html_text):
        m = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"', html_text)
        assert m
        csp = m.group(1)
        # Tailwind CDN 在当前 build 中已被移除(见 index.html 注释),但若
        # 重新引入,Tailwind CDN 必须出现在 CSP 白名单中(不能是 *)
        if "cdn.tailwindcss.com" in html_text:
            assert "cdn.tailwindcss.com" in csp, f"Tailwind CDN must be explicitly whitelisted in CSP: {csp}"
        # 不应有通配的 * 作为 script-src
        script_src = re.search(r"script-src\s+([^;]+)", csp)
        if script_src:
            assert "*" not in script_src.group(1).split(), f"script-src must not be wildcard: {script_src.group(1)}"


@pytest.mark.unit
class TestFrontendSRI:
    """所有外部 <script> 必须带 integrity 和 crossorigin 属性。"""

    @pytest.fixture
    def html_text(self):
        return FRONTEND_HTML.read_text(encoding="utf-8")

    def test_all_external_scripts_have_integrity(self, html_text):
        """所有 src 指向 https:// 的 <script> 必须带 integrity。"""
        external_scripts = re.findall(
            r'<script\s+[^>]*src="https?://[^"]+"[^>]*>',
            html_text,
        )
        assert external_scripts, "no external <script> tags found"
        for tag in external_scripts:
            assert "integrity=" in tag, f"external script missing integrity: {tag}"
            assert "crossorigin=" in tag, f"external script missing crossorigin: {tag}"

    def test_echarts_has_sri(self, html_text):
        """ECharts CDN 脚本必须有 SRI。"""
        m = re.search(r'<script\s+[^>]*src="https?://cdn\.jsdelivr\.net/npm/echarts[^"]+"[^>]*>', html_text)
        assert m, "ECharts script not found"
        tag = m.group(0)
        assert "integrity=" in tag
        # integrity 必须是 sha384
        m2 = re.search(r'integrity="(sha384-[A-Za-z0-9+/=]+)"', tag)
        assert m2, f"integrity must be sha384 hash, got: {tag}"

    def test_tailwind_has_sri(self, html_text):
        """Tailwind CDN 脚本必须有 SRI(若仍存在)。"""
        m = re.search(r'<script\s+[^>]*src="https?://cdn\.tailwindcss\.com[^"]*"[^>]*>', html_text)
        if not m:
            pytest.skip("Tailwind CDN is intentionally not loaded in this build")
        tag = m.group(0)
        assert "integrity=" in tag
