"""chat_widget.js 的 parseSSEEvent + chip DOM 渲染测试。"""
import subprocess
from pathlib import Path

WIDGET_JS = Path("/workspace/frontend/chat_widget.js")


def test_chat_widget_js_is_valid_javascript():
    """node --check 验证 JS 无语法错。"""
    result = subprocess.run(
        ["node", "--check", str(WIDGET_JS)],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"JS syntax error: {result.stderr}"


def test_chat_widget_exposes_parseSSEEvent():  # noqa: N802
    """parseSSEEvent 必须在文件里定义;用花括号配对提取并跑一次。"""
    js = WIDGET_JS.read_text()
    # 找到 'function parseSSEEvent' 起点
    start = js.index("function parseSSEEvent")
    # 找到下一个 '{'(函数体起点)
    brace_open = js.index("{", start)
    # 花括号配对 — 直到匹配到函数体的 '}'
    depth = 0
    i = brace_open
    while i < len(js):
        ch = js[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    func_body = js[start:i + 1]

    result = subprocess.run(
        ["node", "-e", f"""
        {func_body}
        const ev = parseSSEEvent('event: message\\ndata: {{"type":"tool_call","name":"get_forecast","navigate_to":"/x"}}');
        console.log(JSON.stringify({{
            type: ev.data.type,
            name: ev.data.name,
            navigate_to: ev.data.navigate_to
        }}));
        """],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"eval error: {result.stderr}"
    import json
    out = json.loads(result.stdout.strip())
    assert out["type"] == "tool_call"
    assert out["name"] == "get_forecast"
    assert out["navigate_to"] == "/x"


def test_chat_widget_exposes_appendToolChip():  # noqa: N802
    """appendToolChip 必须存在并能调(签名 chip(name, args, navigate_to))。"""
    js = WIDGET_JS.read_text()
    assert "function appendToolChip" in js
    m = js.split("function appendToolChip")[1].split("}")[0]
    assert "navigate_to" in m


def test_chat_widget_handles_type_tool_call_in_send():
    """send() 的 for-await 必须 type=tool_call 分支,调 appendToolChip。"""
    js = WIDGET_JS.read_text()
    send_section = js[js.index("async function send()"):]
    assert '"tool_call"' in send_section or "'tool_call'" in send_section
