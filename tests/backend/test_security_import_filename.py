"""
安全回归测试:数据导入路径穿越防护 (H-02)

防御 /interactive/import 接口利用 file_name 字段覆盖工作区外的文件。
"""

import pytest


@pytest.mark.unit
class TestSafeImportFilename:
    """interactive.py 的导入文件名安全函数。"""

    def test_rejects_dotdot_segment(self):
        from backend.api.routes.interactive import safe_import_filename

        with pytest.raises(ValueError):
            safe_import_filename("../etc/passwd")

    def test_rejects_absolute_path(self):
        from backend.api.routes.interactive import safe_import_filename

        with pytest.raises(ValueError):
            safe_import_filename("/etc/passwd")

    def test_rejects_backslash(self):
        from backend.api.routes.interactive import safe_import_filename

        with pytest.raises(ValueError):
            safe_import_filename("..\\..\\..\\etc\\passwd")

    def test_rejects_empty(self):
        from backend.api.routes.interactive import safe_import_filename

        with pytest.raises(ValueError):
            safe_import_filename("")

    def test_rejects_hidden_filename(self):
        from backend.api.routes.interactive import safe_import_filename

        with pytest.raises(ValueError):
            safe_import_filename(".bashrc")

    def test_accepts_simple_filename(self):
        from backend.api.routes.interactive import safe_import_filename

        name = safe_import_filename("data.csv")
        assert name.endswith("data.csv")
        # 必须包含随机前缀,防止猜到
        assert "_data.csv" in name or name.endswith("/data.csv")
        # 长度大于等于 12 (8 字节 hex + "_" + basename)
        assert len(name.split("/")[-1]) >= 12

    def test_accepts_extension_with_dots(self):
        from backend.api.routes.interactive import safe_import_filename

        name = safe_import_filename("report.2025.csv")
        assert "report.2025.csv" in name

    def test_rejects_nested_path(self):
        """含 '/' 必须直接拒绝(不静默剥离)。"""
        from backend.api.routes.interactive import safe_import_filename

        with pytest.raises(ValueError):
            safe_import_filename("a/b/data.csv")
