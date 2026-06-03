"""
安全回归测试:静态文件路径穿越防护 (C-01)

通过单元测试静态文件解析函数,确保任何目录穿越都不可能构造出
CHARTS_DIR 之外的真实文件路径。
"""

import pytest


@pytest.mark.unit
class TestSafeChartPath:
    """static.py 的安全文件解析函数必须严格沙箱化。"""

    def test_rejects_dotdot_segment(self):
        """含 '..' 段必须拒绝。"""
        from backend.api.routes.static import safe_chart_path

        with pytest.raises(ValueError):
            safe_chart_path("../etc/passwd")

    def test_rejects_absolute_path(self):
        """绝对路径必须拒绝。"""
        from backend.api.routes.static import safe_chart_path

        with pytest.raises(ValueError):
            safe_chart_path("/etc/passwd")

    def test_rejects_backslash(self):
        """含反斜杠必须拒绝(Linux 上是合法字符,可能用来绕过检测)。"""
        from backend.api.routes.static import safe_chart_path

        with pytest.raises(ValueError):
            safe_chart_path("..\\..\\etc\\passwd")

    def test_rejects_hidden_filename(self):
        """以 '.' 开头的隐藏文件必须拒绝。"""
        from backend.api.routes.static import safe_chart_path

        with pytest.raises(ValueError):
            safe_chart_path(".htaccess")
        with pytest.raises(ValueError):
            safe_chart_path(".env")

    def test_rejects_empty_filename(self):
        """空字符串必须拒绝。"""
        from backend.api.routes.static import safe_chart_path

        with pytest.raises(ValueError):
            safe_chart_path("")

    def test_accepts_simple_png(self, tmp_path):
        """合法文件名应该能解析到 CHARTS_DIR 内的文件。"""
        from backend.api.routes import static as static_module

        # 临时把 CHARTS_DIR 指向 tmp_path
        original = static_module.CHARTS_DIR
        static_module.CHARTS_DIR = tmp_path
        try:
            real_file = tmp_path / "foo.png"
            real_file.write_bytes(b"\x89PNG\r\n\x1a\n")

            from backend.api.routes.static import safe_chart_path

            resolved = safe_chart_path("foo.png")
            assert resolved == real_file.resolve()
        finally:
            static_module.CHARTS_DIR = original

    def test_accepts_nested_subdir_filename(self, tmp_path):
        """合法子目录文件名应该可以解析。"""
        from backend.api.routes import static as static_module

        original = static_module.CHARTS_DIR
        static_module.CHARTS_DIR = tmp_path
        try:
            sub = tmp_path / "city" / "shenzhen.png"
            sub.parent.mkdir(parents=True)
            sub.write_bytes(b"\x89PNG")

            from backend.api.routes.static import safe_chart_path

            resolved = safe_chart_path("city/shenzhen.png")
            assert resolved == sub.resolve()
        finally:
            static_module.CHARTS_DIR = original

    def test_resolved_path_must_stay_within_charts_dir(self, tmp_path):
        """解析后路径必须在 CHARTS_DIR 内(防止 symlink 等绕过)。"""
        from backend.api.routes import static as static_module

        original = static_module.CHARTS_DIR
        static_module.CHARTS_DIR = tmp_path
        try:
            # 即便输入不直接包含 '..',解析后必须仍在 CHARTS_DIR 内
            outside = tmp_path.parent / "outside.txt"
            outside.write_text("pwned")
            try:
                from backend.api.routes.static import safe_chart_path

                # 试图用 ..\foo 形式
                with pytest.raises(ValueError):
                    safe_chart_path("..\\outside.txt")
            finally:
                outside.unlink(missing_ok=True)
        finally:
            static_module.CHARTS_DIR = original
