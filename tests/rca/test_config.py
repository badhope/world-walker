"""Tests for rca._config — 从 env 读 LLM 配置构造 AIConfig,带 fallback chain 默认值。"""
import pytest

from backend.ai.config import AIConfig
from backend.ai.fallback import DEFAULT_FALLBACK_CHAIN
from rca._config import load_config
from rca.errors import ConfigError


def test_load_config_reads_env(monkeypatch):
    """env 设齐 → 返 AIConfig 含 fallback_chain + parallel + tool_timeout。"""
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "openai")
    monkeypatch.setenv("LLM_OPENAI_MODEL", "qwen-max")

    cfg = load_config()
    assert isinstance(cfg, AIConfig)
    assert cfg.model == "qwen-max"
    assert cfg.active_backend == "openai"
    assert cfg.temperature == 0.3  # default
    assert cfg.fallback_chain == tuple(DEFAULT_FALLBACK_CHAIN)
    assert cfg.tool_timeout_sec == 30  # default
    assert cfg.parallel_max_workers == 5  # default


def test_load_config_no_api_key_raises(monkeypatch):
    """env 全空 → 抛 ConfigError(不是 RCAError 别的子类)。"""
    for k in ("LLM_OPENAI_API_KEY", "LLM_ANTHROPIC_API_KEY", "LLM_OLLAMA_BASE_URL"):
        monkeypatch.delenv(k, raising=False)

    with pytest.raises(ConfigError) as exc:
        load_config()
    assert "LLM_OPENAI_API_KEY" in str(exc.value) or "OPENAI" in str(exc.value)


def test_load_config_uses_default_fallback_chain(monkeypatch):
    """未传 chain 时,fallback_chain = DEFAULT_FALLBACK_CHAIN。"""
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test")
    cfg = load_config()
    assert len(cfg.fallback_chain) == 5
    assert cfg.fallback_chain[0].model == "qwen-max"
