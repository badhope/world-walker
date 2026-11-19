"""OpenAI-compatible HTTP adapter for the player runtime.

The project deliberately knows no vendor: a config is just base_url + api_key +
model.  The adapter speaks the standard /chat/completions request/response and
passes tool calls through unchanged.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from game_engine import model_config


class HostAdapterError(RuntimeError):
    def __init__(self, message: str, status: int = 0):
        super().__init__(model_config.redact(message))
        self.status = int(status or 0)


class ToolsUnsupported(HostAdapterError):
    """The endpoint rejected the `tools` field (some gateways only proxy text)."""


def _endpoint(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if not base:
        raise HostAdapterError("还没有配置模型地址（base_url）")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    # A bare gateway root (e.g. https://api.example.com) usually exposes
    # /chat/completions; a full OpenAI base should end in /v1.  Users can
    # always paste the complete endpoint and it will be used as-is.
    return base + "/chat/completions"


def _headers(cfg: dict) -> dict:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = "Bearer " + str(cfg["api_key"])
    headers.update({str(k): str(v) for k, v in (cfg.get("extra_headers") or {}).items()})
    return headers


class OpenAICompatAdapter:
    def __init__(self, cfg: dict | None = None):
        self.cfg = model_config.load_config() if cfg is None else model_config._clean(cfg)
        self.endpoint = _endpoint(self.cfg.get("base_url", ""))

    def _post(self, payload: dict, timeout: float | None = None) -> dict:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=body, headers=_headers(self.cfg), method="POST")
        timeout = float(timeout or self.cfg.get("timeout") or 60)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - user-configured endpoint
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")
            except Exception:
                detail = ""
            message = detail
            try:
                parsed = json.loads(detail)
                message = (parsed.get("error") or {}).get("message") or parsed.get("message") or detail
            except (ValueError, TypeError, AttributeError):
                pass
            text = model_config.redact("模型接口返回 %s：%s" % (exc.code, message or exc.reason))
            if exc.code == 400 and payload.get("tools") and "tool" in (message or "").lower():
                raise ToolsUnsupported(text, exc.code) from exc
            raise HostAdapterError(text, exc.code) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HostAdapterError("连接模型接口失败：%s" % exc) from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise HostAdapterError("模型接口返回的不是 JSON：%s" % str(exc)[:120]) from exc

    def chat(self, messages: list, tools: list | None = None,
             tool_choice: str = "auto", stream: bool = False) -> dict:
        """Return {message, usage, raw}. `message` is the OpenAI assistant message."""
        if stream:
            # The player shell uses the non-streaming path today; keeping this
            # explicit avoids silently pretending we implemented SSE.
            raise HostAdapterError("当前适配器只支持非流式响应")
        if not self.cfg.get("model"):
            raise HostAdapterError("还没有配置模型名（model）")
        payload = {
            "model": self.cfg["model"],
            "messages": messages,
            "temperature": float(self.cfg.get("temperature") or 0.7),
            "max_tokens": int(self.cfg.get("max_tokens") or 1200),
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        if self.cfg.get("extra_body"):
            payload.update(self.cfg["extra_body"])
        data = self._post(payload)
        choices = data.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            raise HostAdapterError("模型接口没有返回 choices")
        message = choices[0].get("message") or {}
        if not isinstance(message, dict):
            raise HostAdapterError("模型接口返回的 message 不是对象")
        return {
            "message": message,
            "finish_reason": choices[0].get("finish_reason", ""),
            "usage": data.get("usage") or {},
            "raw": data,
        }

    def test(self) -> dict:
        started = time.time()
        result = self.chat(
            [{"role": "user", "content": "只回复 ok"}],
            tools=None,
        )
        text = str((result.get("message") or {}).get("content") or "").strip()
        return {
            "ok": True,
            "model": self.cfg.get("model", ""),
            "base_url": self.cfg.get("base_url", ""),
            "latency_ms": int((time.time() - started) * 1000),
            "reply": text[:80],
        }


def adapter_from_env() -> OpenAICompatAdapter:
    return OpenAICompatAdapter(model_config.load_config())
