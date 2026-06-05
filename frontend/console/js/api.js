// frontend/console/js/api.js — fetch 封装 + 错误处理 + JSON 解析
// API base 来自 <meta name="data-api-base"> (跟 frontend/index.html 一致)
// 默认同源空字符串(use 当前 host)

(function () {
  "use strict";

  const meta = document.querySelector('meta[name="data-api-base"]');
  const base = (meta && meta.content) ? meta.content.replace(/\/$/, "") : "";

  /**
   * fetch 封装:
   * - 自动加 /api/v1 前缀
   * - 返 {ok, status, data, error} 而不是抛
   * - SSE stream 用 streamSSE() 单独
   */
  async function rcaFetch(path, opts = {}) {
    const url = base + path;
    const init = Object.assign(
      {
        headers: Object.assign(
          { "Content-Type": "application/json", "Accept": "application/json" },
          opts.headers || {},
        ),
        credentials: "same-origin",
      },
      opts,
    );
    if (init.body && typeof init.body !== "string") {
      init.body = JSON.stringify(init.body);
    }
    let response;
    try {
      response = await fetch(url, init);
    } catch (networkErr) {
      return {
        ok: false,
        status: 0,
        data: null,
        error: "无法连接后端,请确认 :8000 端口在跑(原始错:" + (networkErr.message || networkErr) + ")",
      };
    }
    let body = null;
    const text = await response.text();
    if (text) {
      try { body = JSON.parse(text); }
      catch (e) {
        // 非 JSON(比如 nginx 错误页)— 包成 error
        return {
          ok: false,
          status: response.status,
          data: null,
          error: "后端返非 JSON 响应(status=" + response.status + "): " + text.slice(0, 200),
        };
      }
    }
    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        data: body,
        error: (body && body.detail) || ("HTTP " + response.status),
      };
    }
    return { ok: true, status: response.status, data: body, error: null };
  }

  /**
   * 调一个 tool — POST /api/v1/admin/tools/{name}/run
   */
  async function runTool(name, params) {
    return rcaFetch("/api/v1/admin/tools/" + encodeURIComponent(name) + "/run", {
      method: "POST",
      body: params,
    });
  }

  /**
   * 列出 9 tool metadata — GET /api/v1/admin/tools
   */
  async function listTools() {
    return rcaFetch("/api/v1/admin/tools");
  }

  /**
   * 列出可用的 city / province / indicator(从 list_cities 端点拉)
   */
  async function listCities() {
    return runTool("get_list_cities", {});
  }

  /**
   * LLM config GET / PUT
   */
  async function getConfig() {
    return rcaFetch("/api/v1/admin/config");
  }
  async function updateConfig(patch) {
    return rcaFetch("/api/v1/admin/config", { method: "PUT", body: patch });
  }

  /**
   * History GET / DELETE
   */
  async function listHistory(opts) {
    const q = new URLSearchParams();
    if (opts && opts.tool) q.set("tool", opts.tool);
    if (opts && opts.limit) q.set("limit", String(opts.limit));
    const qs = q.toString();
    return rcaFetch("/api/v1/admin/history" + (qs ? "?" + qs : ""));
  }
  async function clearHistory() {
    return rcaFetch("/api/v1/admin/history", { method: "DELETE" });
  }

  /**
   * Chat non-stream
   */
  async function chat(sessionId, message) {
    return rcaFetch("/api/v1/admin/chat", {
      method: "POST",
      body: { session_id: sessionId, message: message },
    });
  }

  /**
   * SSE chat stream — 用 fetch + reader 解析 text/event-stream
   * 不用 EventSource(EventSource 不支持 POST / headers)
   *
   * @param {string} sessionId
   * @param {string} message
   * @param {(ev: object) => void} onEvent
   * @returns {Promise<void>}
   */
  async function streamChat(sessionId, message, onEvent) {
    const url = base + "/api/v1/admin/chat/stream"
      + "?session_id=" + encodeURIComponent(sessionId)
      + "&message=" + encodeURIComponent(message);
    let response;
    try {
      response = await fetch(url, { method: "GET", credentials: "same-origin" });
    } catch (e) {
      onEvent({ type: "error", message: "无法连接后端: " + (e.message || e) });
      return;
    }
    if (!response.ok) {
      onEvent({ type: "error", message: "HTTP " + response.status });
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const chunk = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        // SSE: "data: ..." 行
        for (const line of chunk.split("\n")) {
          if (line.startsWith("data:")) {
            const data = line.slice(5).trim();
            if (!data || data === "[DONE]") continue;
            try {
              const ev = JSON.parse(data);
              onEvent(ev);
            } catch (e) {
              console.warn("SSE parse error:", data, e);
            }
          }
        }
      }
    }
  }

  // 暴露
  window.RCA = window.RCA || {};
  window.RCA.api = {
    rcaFetch, runTool, listTools, listCities,
    getConfig, updateConfig,
    listHistory, clearHistory,
    chat, streamChat,
  };
})();
