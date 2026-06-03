"""
安全回归测试:SQL 标识符验证 (L-01)

防御 backend/core/data_manager.py::load_database 中
f"SELECT * FROM {table_name}" 的字符串拼接。

即便当前不通过 API 直接接收 table_name,提前做白名单校验
可以避免日后添加路由时遗留漏洞。
"""

import pytest


@pytest.mark.unit
class TestValidateSqlIdentifier:
    """validate_sql_identifier 必须严格白名单化 SQL 表名/列名。"""

    def test_accepts_simple_alphanumeric(self):
        from backend.core.data_manager import validate_sql_identifier

        assert validate_sql_identifier("gdp_data") == "gdp_data"
        assert validate_sql_identifier("users") == "users"
        assert validate_sql_identifier("table_2024") == "table_2024"

    def test_rejects_empty(self):
        from backend.core.data_manager import validate_sql_identifier

        with pytest.raises(ValueError):
            validate_sql_identifier("")

    def test_rejects_sql_injection_attempt(self):
        from backend.core.data_manager import validate_sql_identifier

        with pytest.raises(ValueError):
            validate_sql_identifier("users; DROP TABLE users--")

    def test_rejects_union_attack(self):
        from backend.core.data_manager import validate_sql_identifier

        with pytest.raises(ValueError):
            validate_sql_identifier("users UNION SELECT password FROM users")

    def test_rejects_whitespace(self):
        from backend.core.data_manager import validate_sql_identifier

        with pytest.raises(ValueError):
            validate_sql_identifier("users ")

    def test_rejects_quote_injection(self):
        from backend.core.data_manager import validate_sql_identifier

        with pytest.raises(ValueError):
            validate_sql_identifier("users'")

    def test_rejects_dot_path(self):
        from backend.core.data_manager import validate_sql_identifier

        # 不允许 users.password 这种点路径
        with pytest.raises(ValueError):
            validate_sql_identifier("users.password")

    def test_rejects_kwarg_style(self):
        from backend.core.data_manager import validate_sql_identifier

        with pytest.raises(ValueError):
            validate_sql_identifier("users--")

    def test_max_length_enforced(self):
        from backend.core.data_manager import validate_sql_identifier

        # SQLite 标识符最大 128 字符
        too_long = "a" * 200
        with pytest.raises(ValueError):
            validate_sql_identifier(too_long)
