// 浮动 chat widget — 调 /api/v1/ai/chat/stream(SSE 真流式 + 打字机渲染)
(function () {
  if (window.RCAChatLoaded) return;
  window.RCAChatLoaded = true;

  // 加载 session_id(同会话复用)
  let sessionId = sessionStorage.getItem("rca_chat_session");
  if (!sessionId) {
    sessionId = "sess-" + Math.random().toString(36).slice(2, 10) + Date.now();
    sessionStorage.setItem("rca_chat_session", sessionId);
  }

  // 注入 CSS
  const css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = "/chat_widget/chat_widget.css";
  document.head.appendChild(css);

  // 注入 HTML
  const bubble = document.createElement("button");
  bubble.className = "rca-chat-bubble";
  bubble.textContent = "💬";
  bubble.setAttribute("aria-label", "Open AI chat");

  const win = document.createElement("div");
  win.className = "rca-chat-window";
  win.innerHTML = `
    <div class="rca-chat-header">
      <h3>🤖 AI 经济助手</h3>
      <select class="rca-backend-select"><option value="default">default</option></select>
    </div>
    <div class="rca-chat-body"></div>
    <div class="rca-status">输入问题开始对话(可问:深圳 GDP 2026 预测/风险/情景/数据来源)</div>
    <div class="rca-chat-input-area">
      <input type="text" placeholder="例如:深圳 GDP 2026 预测多少?" maxlength="4000">
      <button>发送</button>
    </div>
  `;

  document.body.appendChild(bubble);
  document.body.appendChild(win);

  const body = win.querySelector(".rca-chat-body");
  const input = win.querySelector("input");
  const btn = win.querySelector("button");
  const backendSelect = win.querySelector(".rca-backend-select");

  bubble.addEventListener("click", () => win.classList.toggle("open"));

  // 加载 backend 选项
  fetch("/api/v1/ai/config").then((r) => r.json()).then((cfg) => {
    const backends = cfg.available_backends || [];
    backendSelect.innerHTML = '<option value="default">default (' + cfg.active_backend + ")</option>";
    backends.forEach((b) => {
      if (b !== cfg.active_backend) {
        const opt = document.createElement("option");
        opt.value = b;
        opt.textContent = b;
        backendSelect.appendChild(opt);
      }
    });
  }).catch(() => {});

  function appendMessage(role, content) {
    const msg = document.createElement("div");
    msg.className = "rca-msg " + role;
    const bubbleEl = document.createElement("div");
    bubbleEl.className = "rca-msg-bubble";
    bubbleEl.textContent = content;
    msg.appendChild(bubbleEl);
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
    return bubbleEl;
  }

  function appendToolChip(name, args, navigate_to) {
    const chip = document.createElement("a");
    chip.className = "rca-tool-chip";
    chip.href = navigate_to || "#";
    chip.target = "_blank";  // 新窗口打开,保留 chat
    chip.rel = "noopener noreferrer";
    // 显示:🔧 get_forecast(name=shenzhen, indicator=gdp) → 📊 在图表中查看
    const argsStr = Object.entries(args || {}).map(([k, v]) => k + "=" + v).join(", ").slice(0, 60);
    chip.innerHTML = "🔧 " + name + "(" + argsStr + ") → 📊 在图表中查看";
    body.appendChild(chip);
    return chip;
  }

  // SSE 解析器 — 把 ReadableStream 拆成 {event, data} 对象
  // SSE 格式: "event: message\ndata: {...}\n\n"
  async function* consumeSSE(resp) {
    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // 按 \n\n 拆 event
      let idx;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const raw = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const event = parseSSEEvent(raw);
        if (event) yield event;
      }
    }
  }

  function parseSSEEvent(raw) {
    let event = "message";
    let data = "";
    for (const line of raw.split("\n")) {
      if (line.startsWith("event: ")) event = line.slice(7).trim();
      else if (line.startsWith("data: ")) data += line.slice(6);
    }
    if (!data) return null;
    try {
      return { event, data: JSON.parse(data) };
    } catch {
      return { event, data: { type: "raw", content: data } };
    }
  }

  async function send() {
    const text = input.value.trim();
    if (!text) return;
    appendMessage("user", text);
    input.value = "";
    btn.disabled = true;

    // 占位 assistant 气泡(打字机渲染,逐字追加)
    const placeholder = appendMessage("assistant", "");
    let accumulated = "";
    const status = win.querySelector(".rca-status");
    const originalStatus = status ? status.textContent : "";

    try {
      const resp = await fetch("/api/v1/ai/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          messages: [{ role: "user", content: text }],
        }),
      });
      if (!resp.ok) {
        const err = await resp.text();
        placeholder.textContent = "(错误 " + resp.status + "): " + err;
        return;
      }
      if (!resp.body || !resp.body.getReader) {
        // 老浏览器:降级为一次性
        const data = await resp.json();
        placeholder.textContent = data.content || "(无内容)";
        return;
      }
      // 真流式消费 SSE
      for await (const ev of consumeSSE(resp)) {
        const d = ev.data || {};
        if (d.type === "thinking") {
          if (status) status.textContent = "🤔 思考中…";
        } else if (d.type === "tool_call") {
          // v7.1: 渲染可点击 chip,跳转到对应图表页
          appendToolChip(d.name, d.args, d.navigate_to);
        } else if (d.type === "token" && d.content) {
          accumulated += d.content;
          placeholder.textContent = accumulated;  // 打字机:逐字覆盖
          body.scrollTop = body.scrollHeight;
        } else if (d.type === "done") {
          if (status) status.textContent = originalStatus;
          break;
        } else if (d.type === "error") {
          placeholder.textContent = "(LLM 错误): " + (d.message || "未知");
          if (status) status.textContent = originalStatus;
          break;
        }
      }
      if (!accumulated) placeholder.textContent = "(无内容)";
    } catch (e) {
      placeholder.textContent = "(网络错误): " + e.message;
      if (status) status.textContent = originalStatus;
    } finally {
      btn.disabled = false;
      input.focus();
    }
  }

  btn.addEventListener("click", send);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
})();
