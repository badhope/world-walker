// 浮动 chat widget — 调 /api/v1/ai/chat
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
  css.href = "/chat_widget.css";
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
    const bubble = document.createElement("div");
    bubble.className = "rca-msg-bubble";
    bubble.textContent = content;
    msg.appendChild(bubble);
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
    return bubble;
  }

  function appendToolChip(name, args) {
    const chip = document.createElement("span");
    chip.className = "rca-tool-chip";
    chip.textContent = "🔧 " + name + "(" + JSON.stringify(args).slice(0, 60) + ")";
    body.appendChild(chip);
  }

  async function send() {
    const text = input.value.trim();
    if (!text) return;
    appendMessage("user", text);
    input.value = "";
    btn.disabled = true;

    // 占位 assistant 气泡
    const placeholder = appendMessage("assistant", "");

    try {
      const resp = await fetch("/api/v1/ai/chat", {
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
        btn.disabled = false;
        return;
      }
      const data = await resp.json();
      placeholder.textContent = data.content || "(无内容)";
    } catch (e) {
      placeholder.textContent = "(网络错误): " + e.message;
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
