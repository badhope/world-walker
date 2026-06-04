import os
import pytest


def test_load_config_defaults_openai(monkeypatch):
    monkeypatch.delenv("LLM_DEFAULT_BACKEND", raising=False)
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test")
    from backend.ai.config import load_config
    cfg = load_config()
    assert cfg.default_backend == "openai"
    assert cfg.active_backend in {"openai", "anthropic", "ollama"}
    assert cfg.model == "gpt-4o-mini"


def test_load_config_ollama(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "ollama")
    monkeypatch.setenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_OLLAMA_MODEL", "qwen2.5:7b")
    from backend.ai.config import load_config
    cfg = load_config()
    assert cfg.default_backend == "ollama"
    assert cfg.active_backend == "ollama"
    assert cfg.model == "qwen2.5:7b"


def test_load_config_fallback_when_no_key(monkeypatch):
    """openai 无 key → 尝试 anthropic → 尝试 ollama"""
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "openai")
    monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")
    from backend.ai.config import load_config
    cfg = load_config()
    # 应降级到 ollama
    assert cfg.active_backend == "ollama"


def test_load_config_all_unavailable(monkeypatch):
    """全无可用 backend → 抛 ConfigError"""
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "openai")
    monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_OLLAMA_BASE_URL", raising=False)
    from backend.ai.config import load_config, ConfigError
    with pytest.raises(ConfigError):
        load_config()


def test_config_exposes_constants(monkeypatch):
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test")
    from backend.ai.config import load_config
    cfg = load_config()
    assert cfg.max_tokens == 2000
    assert cfg.temperature == 0.3
    assert cfg.max_tool_rounds == 5
    assert cfg.timeout_sec == 60
