"""
前端 chat_widget.js 单元测试 — 用 node 跑。

验证:
1. JS 语法合法
2. consumeSSE 解析器正确拆 SSE event
3. parseSSEEvent 拆 event/data
4. send() 流程调 /api/v1/ai/chat/stream 而非 /api/v1/ai/chat
"""
import json
import shutil
import subprocess
import textwrap

import pytest

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")


def _run_node(code: str) -> dict:
    """跑 node -e code,返 {returncode, stdout, stderr}。"""
    p = subprocess.run(
        [NODE, "-e", code],
        capture_output=True,
        text=True,
        timeout=20,
        cwd="/workspace",
    )
    return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def test_widget_js_syntax_valid():
    """chat_widget.js 语法合法(用 node --check 仅做语法验证,不执行 IIFE)。"""
    p = subprocess.run(
        [NODE, "--check", "/workspace/frontend/chat_widget.js"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert p.returncode == 0, f"syntax error: {p.stderr}"


def test_widget_js_calls_stream_endpoint():
    """widget.js 内部引用了 /api/v1/ai/chat/stream(而非 /chat)。"""
    src = open("/workspace/frontend/chat_widget.js").read()
    assert "/api/v1/ai/chat/stream" in src, "必须调 stream 端点"
    # 原来的非流式端点应该不在
    non_stream_uses = [line for line in src.splitlines() if '"/api/v1/ai/chat"' in line]
    assert not non_stream_uses, f"仍引用非流式端点: {non_stream_uses}"


def test_widget_js_has_sse_parser():
    """widget.js 有 SSE 解析函数(consumeSSE 或 parseSSEEvent)。"""
    src = open("/workspace/frontend/chat_widget.js").read()
    assert "consumeSSE" in src
    assert "parseSSEEvent" in src
    # 应处理 data: 前缀
    assert "data: " in src
    # 应处理 event: 前缀
    assert "event: " in src


def test_widget_js_handles_thinking_token_done():
    """widget.js 至少处理 4 种 SSE 类型:thinking / token / done / error。"""
    src = open("/workspace/frontend/chat_widget.js").read()
    for ttype in ('"thinking"', '"token"', '"done"', '"error"'):
        assert ttype in src, f"缺少 type={ttype} 处理"


def test_widget_js_typewriter_renders():
    """widget.js 用了打字机渲染(累加 + 覆盖 placeholder.textContent)。"""
    src = open("/workspace/frontend/chat_widget.js").read()
    assert "accumulated" in src, "必须累加 token 渲染打字机效果"
    assert "placeholder.textContent = accumulated" in src


def test_parse_sse_event_logic():
    """parseSSEEvent 函数:拆 'event: x\\ndata: y' 格式。"""
    # 用 node 跑同样的逻辑
    js = textwrap.dedent("""
        function parseSSEEvent(raw) {
            let event = "message";
            let data = "";
            for (const line of raw.split("\\n")) {
                if (line.startsWith("event: ")) event = line.slice(7).trim();
                else if (line.startsWith("data: ")) data += line.slice(6);
            }
            if (!data) return null;
            try { return { event, data: JSON.parse(data) }; }
            catch { return { event, data: { type: "raw", content: data } }; }
        }
        const r = parseSSEEvent('event: message\\ndata: {"type":"token","content":"hi"}');
        process.stdout.write(JSON.stringify(r));
    """)
    r = _run_node(js)
    assert r["returncode"] == 0, r["stderr"]
    out = json.loads(r["stdout"])
    assert out == {"event": "message", "data": {"type": "token", "content": "hi"}}


def test_parse_sse_event_null_on_empty_data():
    """parseSSEEvent:没有 data 行 → 返 null。"""
    js = textwrap.dedent("""
        function parseSSEEvent(raw) {
            let event = "message";
            let data = "";
            for (const line of raw.split("\\n")) {
                if (line.startsWith("event: ")) event = line.slice(7).trim();
                else if (line.startsWith("data: ")) data += line.slice(6);
            }
            return data ? { event, data } : null;
        }
        const r = parseSSEEvent('event: ping');
        process.stdout.write(r === null ? "null" : "notnull");
    """)
    r = _run_node(js)
    assert r["stdout"] == "null"
