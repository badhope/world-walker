"""
安全回归测试:生产环境 SECRET_KEY 必须显式设置 (M-01)
"""

import pytest


@pytest.mark.unit
class TestSecretKeyEnforcement:
    """Settings.SECRET_KEY 在生产环境不允许使用默认值。"""

    def test_default_secret_key_raises_in_production(self, monkeypatch):
        """未设 SECRET_KEY 且 APP_ENV=production 时构造 Settings 必须抛 ValueError。"""
        from config.settings import Settings

        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setenv("APP_ENV", "production")

        with pytest.raises((ValueError, RuntimeError)) as exc_info:
            Settings()
        assert "SECRET_KEY" in str(exc_info.value)

    def test_explicit_secret_key_passes_in_production(self, monkeypatch):
        """设了 SECRET_KEY 时不应抛错。"""
        from config.settings import Settings

        monkeypatch.setenv("SECRET_KEY", "this-is-a-real-prod-secret")
        monkeypatch.setenv("APP_ENV", "production")

        s = Settings()
        assert s.SECRET_KEY == "this-is-a-real-prod-secret"
        assert s.APP_ENV == "production"

    def test_dev_env_allows_default_key(self, monkeypatch):
        """APP_ENV=dev 时默认值仍然可用(便于开发体验)。"""
        from config.settings import Settings

        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setenv("APP_ENV", "dev")

        s = Settings()
        # 任何非空 SECRET_KEY 都接受
        assert s.SECRET_KEY

    def test_default_app_env_treated_as_dev(self, monkeypatch):
        """不设 APP_ENV 时默认 dev,不抛错。"""
        from config.settings import Settings

        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("APP_ENV", raising=False)

        # 默认值即可
        s = Settings()
        assert s.SECRET_KEY
