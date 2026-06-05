"""rca 测试 env 设置:给 fake LLM key 让 SDK 内部 cfg loader 不抛 ConfigError。"""
import os

os.environ.setdefault("LLM_OPENAI_API_KEY", "sk-test-fake-key-for-rca-tests")
os.environ.setdefault("LLM_DEFAULT_BACKEND", "openai")
os.environ.setdefault("LLM_OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-rca-tests")
