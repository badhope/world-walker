"""
安全回归测试:数据导入字段大小限制 (L-04)

防御 backend/api/routes/interactive.py::import_data 接受超大
file_content (Base64) 或过多数据项导致 DoS。
"""

import base64

import pytest


@pytest.mark.unit
class TestDataImportRequestLimits:
    """DataImportRequest 必须限制字段大小。"""

    def test_default_accepts_normal_payload(self):
        from backend.api.routes.interactive import DataImportRequest

        req = DataImportRequest(
            file_name="data.csv",
            file_content=base64.b64encode(b"a,b\n1,2").decode(),
            format_type="csv",
        )
        assert req.file_name == "data.csv"
        assert req.format_type == "csv"

    def test_file_content_must_be_within_max_length(self):
        from pydantic import ValidationError

        from backend.api.routes.interactive import DataImportRequest

        # 50MB Base64 字符串
        huge = "A" * (51 * 1024 * 1024)
        with pytest.raises(ValidationError):
            DataImportRequest(
                file_name="data.csv",
                file_content=huge,
                format_type="csv",
            )

    def test_file_name_length_capped(self):
        from pydantic import ValidationError

        from backend.api.routes.interactive import DataImportRequest

        with pytest.raises(ValidationError):
            DataImportRequest(
                file_name="x" * 300,  # 超过 255 字符
                file_content="AAA=",
                format_type="csv",
            )

    def test_format_type_must_be_known(self):
        from pydantic import ValidationError

        from backend.api.routes.interactive import DataImportRequest

        with pytest.raises(ValidationError):
            DataImportRequest(
                file_name="data.csv",
                file_content="AAA=",
                format_type="exe",  # 非法格式
            )

    def test_accepts_known_formats(self):
        from backend.api.routes.interactive import DataImportRequest

        for fmt in ("json", "csv", "xlsx"):
            req = DataImportRequest(
                file_name=f"data.{fmt}",
                file_content=base64.b64encode(b"x").decode(),
                format_type=fmt,
            )
            assert req.format_type == fmt


@pytest.mark.unit
class TestDataExportRequestLimits:
    """DataExportRequest 也应有合理上限(防 DoS)。"""

    def test_default_data_length_within_limit(self):
        from backend.api.routes.interactive import DataExportRequest

        req = DataExportRequest(
            data=[{"a": 1}] * 100,
            format_type="json",
        )
        assert len(req.data) == 100

    def test_data_list_size_capped(self):
        from pydantic import ValidationError

        from backend.api.routes.interactive import DataExportRequest

        with pytest.raises(ValidationError):
            DataExportRequest(
                data=[{"a": 1}] * 200_000,  # 超过上限
                format_type="json",
            )
