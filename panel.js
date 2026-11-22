/*
 * World Walker · player shell
 *
 * One story, one composer, four rail tabs, one world overlay.  No command
 * palette, no card dashboard, no developer diagnostics.
 */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const app = {
    bootstrap: null,
    view: null,
    selectedWorld: null,
    rail: "character",
    worldTab: "codex",
    busy: false,
    sse: null,
    toastTimer: null,
    feedFirst: true,
    session: null,
  };

  const esc = (value) => String(value == null ? "" : value)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  const num = (value) => {
    const n = Number(value);
    return Number.isFinite(n) ? n.toLocaleString("zh-CN") : "—";
  };

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  async function api(path, options = {}) {
    const opts = { headers: {}, ...options };
    if (opts.body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const response = await fetch(path, opts);
    let payload = null;
    try { payload = await response.json(); } catch (err) { payload = null; }
    if (!response.ok || (payload && payload.ok === false)) {
      const message = (payload && payload.error) || `请求失败（${response.status}）`;
      throw new Error(message);
    }
    return payload;
  }

  function toast(message, ms = 3000) {
    const el = $("toast");
    el.textContent = message;
    el.hidden = false;
    clearTimeout(app.toastTimer);
    app.toastTimer = setTimeout(() => { el.hidden = true; }, ms);
  }

  function showScreen(name) {
    const lobby = $("lobby");
    const play = $("play");
    if (name === "play") { lobby.hidden = true; play.hidden = false; }
    else { play.hidden = true; lobby.hidden = false; }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openOverlay(id) {
    const el = $(id);
    if (!el) return;
    el.hidden = false;
    const first = el.querySelector("input, button");
    if (first && id === "model-overlay") setTimeout(() => first.focus(), 30);
  }

  function closeOverlay(id) {
    const el = $(id);
    if (el) el.hidden = true;
  }

  function closeAllOverlays() {
    document.querySelectorAll(".overlay").forEach((el) => { el.hidden = true; });
  }

  /* ------------------------------------------------------------------ */
  /* Lobby                                                              */
  /* ------------------------------------------------------------------ */

  function renderLobby() {
    const data = app.bootstrap || {};
    renderContinue(data.current);
    renderSaves(data.saves || []);
    const model = data.model || {};
    if (!model.configured) {
      $("lobby-model-btn").textContent = "模型未连接 · 去设置";
    } else {
      $("lobby-model-btn").textContent = `模型 · ${model.model || "已连接"}`;
    }
  }

  function renderContinue(current) {
    const body = $("continue-body");
    if (!current) {
      body.innerHTML = `<p class="muted">还没有正在进行的局。开一局，先说你想玩什么。</p>`;
      return;
    }
    const broken = current.broken ? "（存档需要修复）" : "";
    body.innerHTML = `
      <h3>${esc(current.world || current.name || "未命名世界")}</h3>
      <p>第 ${num(current.tick)} 回合 · ${esc(current.name)} ${broken}</p>
      <div class="continue-actions">
        <button class="primary-btn" id="continue-btn" type="button">继续这一局</button>
        <button class="ghost-btn" id="continue-open-btn" type="button">查看存档</button>
      </div>`;
    $("continue-btn").addEventListener("click", () => openGame(current.path));
    $("continue-open-btn").addEventListener("click", () => $("saves-list").scrollIntoView({ behavior: "smooth" }));
  }

  const FALLBACK_SESSION_OPTIONS = {
    genres: ["悬疑", "奇幻", "武侠仙侠", "科幻", "都市", "历史", "恋爱", "恐怖", "生存", "日常"],
    plays: ["探索解谜", "生存压力", "权谋经营", "关系情感", "战斗成长", "调查恐怖", "轻松日常"],
    tones: ["明亮", "阴郁", "热血", "克制", "荒诞"],
    difficulties: ["轻松", "标准", "硬核", "铁人"],
    roles: [
      { id: "random", label: "随机生成", desc: "让引擎给你一个能直接玩的人" },
      { id: "custom", label: "我自己写一句", desc: "名字和身份由你定" },
      { id: "preset", label: "用预设角色", desc: "用模板里的主角" },
    ],
    boundaries: ["不写玩家内心决定", "不出现现代科技", "不写血腥细节", "不写恋爱线", "不无故杀死 NPC"],
  };

  function sessionOptions() {
    const data = (app.bootstrap && app.bootstrap.session_zero) || {};
    if (Array.isArray(data.genres) && data.genres.length) return data;
    return FALLBACK_SESSION_OPTIONS;
  }

  function newSession() {
    app.session = {
      step: 0, genre: "", play: "", role: "random", name: "",
      tone: [], difficulty: "标准", boundaries: [], world: null, showWorlds: false,
    };
    app.sessionPreviewToken = 0;
  }

  function openSession() {
    if (!app.bootstrap) { toast("大厅还没加载好"); return; }
    newSession();
    renderSession();
    openOverlay("session-overlay");
  }

  function sessionChip(label, value, selected, group, extra = "") {
    return `<button class="choice-chip ${selected ? "selected" : ""}" type="button"
      data-session-group="${esc(group)}" data-session-value="${esc(value)}">
      ${esc(label)}${extra ? `<small>${esc(extra)}</small>` : ""}
    </button>`;
  }

  function renderSession() {
    const s = app.session;
    if (!s) { newSession(); return; }
    const opts = sessionOptions();
    const stepNames = ["类型", "玩法", "角色", "开局卡"];
    $("session-steps").innerHTML = stepNames.map((name, index) =>
      `<span class="${index <= s.step ? "on" : ""}" title="${esc(name)}"></span>`).join("");
    $("session-step-label").textContent = `第 ${s.step + 1} / 4 步 · ${stepNames[s.step]}`;
    $("session-back").disabled = s.step === 0;
    $("session-next").textContent = s.step === 3 ? "开始这一局" : "下一步";

    const body = $("session-body");
    if (s.step === 0) {
      body.innerHTML = `
        <h3 class="session-question">你想玩什么类型？</h3>
        <p class="session-sub">这一步决定世界的气味。选一个，或者直接告诉我你脑子里的那个词。</p>
        <div class="choice-grid">${opts.genres.map((x) => sessionChip(x, x, s.genre === x, "genre")).join("")}</div>`;
    } else if (s.step === 1) {
      body.innerHTML = `
        <h3 class="session-question">你想怎么玩？</h3>
        <p class="session-sub">同一个世界，可以调查、可以生存、也可以只谈关系。玩法决定每一回合在推进什么。</p>
        <div class="choice-grid">${opts.plays.map((x) => sessionChip(x, x, s.play === x, "play")).join("")}</div>`;
    } else if (s.step === 2) {
      body.innerHTML = `
        <h3 class="session-question">你以谁的身份进去？</h3>
        <p class="session-sub">随机是让引擎给你一个人；自己写一句，是你已经知道自己想当谁。</p>
        <div class="choice-grid">${(opts.roles || []).map((r) =>
          sessionChip(r.label || r.id, r.id, s.role === r.id, "role", r.desc || "")).join("")}</div>
        <div class="session-field">
          <label for="session-name">名字 / 身份一句话</label>
          <input id="session-name" type="text" maxlength="24" autocomplete="off"
                 value="${esc(s.name)}" placeholder="留空就让引擎决定" />
        </div>`;
    } else {
      const worlds = (app.bootstrap && app.bootstrap.worlds) || [];
      body.innerHTML = `
        <h3 class="session-question">最后，定一下体验</h3>
        <p class="session-sub">难度不是“敌人更强”，是“失败会不会留下后果”。世界起点可以自动配，也可以指定。</p>
        <div class="session-field"><label>基调（可多选）</label>
          <div class="choice-grid">${opts.tones.map((x) => sessionChip(x, x, s.tone.includes(x), "tone")).join("")}</div>
        </div>
        <div class="session-field"><label>难度</label>
          <div class="choice-grid">${opts.difficulties.map((x) => sessionChip(x, x, s.difficulty === x, "difficulty")).join("")}</div>
        </div>
        <div class="session-field"><label>内容边界（可多选）</label>
          <div class="choice-grid">${opts.boundaries.map((x) => sessionChip(x, x, s.boundaries.includes(x), "boundaries")).join("")}</div>
        </div>
        <div class="session-field"><label>开局卡</label>
          <div id="session-preview" class="session-preview"><p class="muted">选完上面的项，这里会出现开局卡。</p></div>
        </div>
        <div class="session-field"><label>世界起点（可选）</label>
          <button class="world-option ${s.world ? "" : "selected"}" type="button" data-world-auto="1">
            <span><b>自动配一个</b><small>按类型和玩法选最合适的规则骨架</small></span>
            <span>→</span>
          </button>
          <button class="ghost-btn session-world-toggle" id="session-world-toggle" type="button">
            ${s.showWorlds || s.world ? "收起世界列表" : "我想指定一个世界"}
          </button>
          <div class="world-picker" id="session-world-list" ${s.showWorlds || s.world ? "" : "hidden"}>
            ${worlds.map((w) => `<button class="world-option ${s.world && s.world.id === w.id ? "selected" : ""}" type="button"
              data-world-kind="${esc(w.kind)}" data-world-id="${esc(w.id)}" data-world-name="${esc(w.name)}">
              <span><b>${esc(w.name)}</b><small>${esc(w.notes || w.genre || "")}</small></span>
              <span class="muted">${w.kind === "template" ? "模板" : "设定包"}</span>
            </button>`).join("")}
          </div>
        </div>`;
      refreshSessionPreview();
    }
    bindSessionBody();
  }

  function bindSessionBody() {
    const s = app.session;
    document.querySelectorAll("#session-body [data-session-group]").forEach((chip) => {
      chip.addEventListener("click", () => {
        const group = chip.dataset.sessionGroup;
        const value = chip.dataset.sessionValue;
        if (group === "tone" || group === "boundaries") {
          const list = Array.isArray(s[group]) ? s[group] : [];
          s[group] = list.includes(value) ? list.filter((x) => x !== value) : list.concat(value);
        } else {
          s[group] = value;
        }
        renderSession();
      });
    });
    document.querySelectorAll("#session-body .world-option").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.worldAuto) {
          s.world = null;
        } else {
          s.world = { kind: button.dataset.worldKind, id: button.dataset.worldId,
            name: button.dataset.worldName };
          s.showWorlds = false;
        }
        renderSession();
      });
    });
    const toggle = $("session-world-toggle");
    if (toggle) {
      toggle.addEventListener("click", () => {
        s.showWorlds = !s.showWorlds;
        renderSession();
      });
    }
    const input = $("session-name");
    if (input) {
      input.addEventListener("input", (event) => { s.name = event.target.value; });
    }
  }

  function sessionNarrative() {
    const s = app.session || {};
    return {
      genre: s.genre, play: s.play, role: s.role, player_name: s.name,
      tone: s.tone, difficulty: s.difficulty, boundaries: s.boundaries,
      world_kind: s.world ? s.world.kind : "", world_id: s.world ? s.world.id : "",
      world_name: s.world ? s.world.name : "",
    };
  }

  async function refreshSessionPreview() {
    const s = app.session;
    if (!s || s.step !== 3) return;
    if (!s.genre || !s.play) { renderSessionPreview(null); return; }
    const token = (app.sessionPreviewToken || 0) + 1;
    app.sessionPreviewToken = token;
    try {
      const card = await api("/api/v1/session-zero/preview", {
        method: "POST",
        body: { narrative: sessionNarrative(), world_name: s.world ? s.world.name : "" },
      });
      if (app.session !== s || app.sessionPreviewToken !== token || s.step !== 3) return;
      s.preview = card;
      renderSessionPreview(card);
    } catch (err) {
      if (app.session === s && s.step === 3) renderSessionPreview(null, err.message);
    }
  }

  function renderSessionPreview(card, error = "") {
    const el = $("session-preview");
    if (!el) return;
    if (!card) {
      el.innerHTML = `<p class="muted">${esc(error || "选完类型和玩法，这里会出现开局卡。")}</p>`;
      return;
    }
    el.innerHTML = `
      <h3>${esc(card.headline)}</h3>
      <p>${esc(card.world_line)}</p>
      <p>${esc(card.player_line)}</p>
      <p>${esc(card.pressure_line)}</p>
      <p class="rules">${esc(card.rules_line)}</p>
      <p class="rules">核心问题：${esc(card.central_question || "由你的选择决定")}</p>
      <ul class="hints">${(card.hints || []).map((hint) => `<li>${esc(hint)}</li>`).join("")}</ul>`;
    el.dataset.ready = "1";
  }

  function sessionNext() {
    const s = app.session;
    if (!s) return;
    if (s.step === 0 && !s.genre) { toast("先选一个类型"); return; }
    if (s.step === 1 && !s.play) { toast("先选一种玩法"); return; }
    if (s.step === 2 && s.role === "custom" && !String(s.name || "").trim()) {
      toast("自己写一句，至少给个名字"); return;
    }
    if (s.step < 3) {
      s.step += 1;
      renderSession();
      return;
    }
    createGame();
  }

  function sessionBack() {
    const s = app.session;
    if (!s || s.step === 0) return;
    s.step -= 1;
    renderSession();
  }

  function renderSaves(saves) {
    const list = $("saves-list");
    $("saves-count").textContent = saves.length ? `${saves.length} 局` : "";
    if (!saves.length) {
      list.innerHTML = `<p class="empty">还没有存档。开一局，它会自动存。</p>`;
      return;
    }
    list.innerHTML = saves.map((save) => `
      <button class="save-item ${save.current ? "current" : ""}" type="button" data-path="${esc(save.path)}">
        <b>${esc(save.world || save.name)}</b>
        <small>${esc(save.name)} · 第 ${num(save.tick)} 回合 · ${esc(save.protagonist || "主角")}</small>
      </button>`).join("");
    list.querySelectorAll(".save-item").forEach((item) => {
      item.addEventListener("click", () => openGame(item.dataset.path));
    });
  }

  async function refreshLobby() {
    try {
      app.bootstrap = await api("/api/v1/bootstrap");
      renderLobby();
    } catch (err) {
      toast(err.message);
    }
  }

  async function openGame(path) {
    try {
      const payload = await api("/api/v1/open", { method: "POST", body: { path } });
      app.view = payload.state;
      app.feedFirst = true;
      showScreen("play");
      renderPlay();
      connectSSE();
    } catch (err) {
      toast(err.message);
    }
  }

  async function createGame() {
    const s = app.session;
    if (!s) return;
    const button = $("session-next");
    const narrative = sessionNarrative();
    const name = String(s.name || "").trim();
    button.disabled = true;
    button.textContent = "正在开局…";
    try {
      const payload = await api("/api/v1/new", {
        method: "POST",
        body: {
          kind: s.world ? s.world.kind : "",
          id: s.world ? s.world.id : "",
          name,
          narrative,
        },
      });
      app.view = payload.state;
      app.feedFirst = true;
      app.session = null;
      closeOverlay("session-overlay");
      showScreen("play");
      renderPlay();
      connectSSE();
      toast("新的一局开始了");
    } catch (err) {
      toast(err.message);
    } finally {
      button.disabled = false;
      button.textContent = "开始这一局";
    }
  }

  /* ------------------------------------------------------------------ */
  /* Play                                                               */
  /* ------------------------------------------------------------------ */

  function renderPlay() {
    if (!app.view) return;
    const view = app.view;
    const world = view.world || {};
    $("world-name").textContent = world.name || "未命名世界";
    $("world-meta").textContent = [
      world.era, `第 ${num(world.tick)} 回合`,
      view.player && view.player.location ? view.player.location : "",
    ].filter(Boolean).join(" · ");
    renderModelBadge(view.model || {});
    renderFeed(view.feed || []);
    renderRail();
    if (!$("world-overlay").hidden) renderWorld();
  }

  function renderModelBadge(model) {
    const el = $("model-badge");
    el.classList.remove("ok", "bad");
    if (model.configured) {
      el.classList.add("ok");
      el.textContent = `模型 · ${model.model || "已连接"}`;
    } else {
      el.classList.add("bad");
      el.textContent = "模型未连接";
    }
  }

  function renderFeed(items) {
    const feed = $("feed");
    const wasNearBottom = feed.scrollHeight - feed.scrollTop - feed.clientHeight < 120;
    const shouldPin = wasNearBottom || app.feedFirst;
    app.feedFirst = false;
    if (!items.length) {
      const scene = (app.view && app.view.scene) || {};
      const narrative = (app.view && app.view.narrative) || {};
      const brief = narrative.brief || {};
      if (brief.headline) {
        const hints = (brief.hints || narrative.hints || []);
        feed.innerHTML = `
          <div class="session-zero-card">
            <p class="eyebrow">开局卡</p>
            <h2>${esc(brief.headline)}</h2>
            <div class="brief">
              ${brief.world_line ? `<p>${esc(brief.world_line)}</p>` : ""}
              ${brief.player_line ? `<p>${esc(brief.player_line)}</p>` : ""}
              ${brief.pressure_line ? `<p>${esc(brief.pressure_line)}</p>` : ""}
              ${brief.rules_line ? `<p class="muted">${esc(brief.rules_line)}</p>` : ""}
            </div>
            ${hints.length ? `<ul class="hints">${hints.map((hint) => `<li>${esc(hint)}</li>`).join("")}</ul>` : ""}
            <p class="cta">说第一句话，或者先问一句。你不需要选“正确”的开头。</p>
          </div>`;
        return;
      }
      feed.innerHTML = `
        <div class="empty-feed">
          <h2>${esc(scene.title || "故事还没有开始")}</h2>
          <p>${esc(scene.text || (app.view && app.view.world && app.view.world.location_desc) ||
            "说一句话，让世界回应你。")}</p>
          <p class="muted">比如：我先看看四周；我走向柜台；我问掌柜最近有什么消息。</p>
        </div>`;
      return;
    }
    feed.innerHTML = items.map((item) => {
      if (item.role === "player") {
        return `<div class="bubble player" data-id="${esc(item.id)}">
          ${esc(item.text)}
          ${item.status === "error" ? `<span class="turn-error">发送失败</span>` : ""}
        </div>`;
      }
      if (item.role === "check") {
        return `<div class="bubble check">判定 · ${esc(item.text)}</div>`;
      }
      const paragraphs = String(item.text || "").split(/\n{2,}/)
        .map((part) => `<p>${esc(part).replace(/\n/g, "<br>")}</p>`).join("");
      const tools = (item.tools || []).length
        ? `<span class="turn-tools">结算 ${item.tools.length} 次</span>` : "";
      return `<div class="bubble narrator" data-id="${esc(item.id)}">${paragraphs}${tools}</div>`;
    }).join("");
    if (shouldPin) {
      feed.scrollTop = feed.scrollHeight;
      requestAnimationFrame(() => { feed.scrollTop = feed.scrollHeight; });
    }
  }

  function renderRail() {
    if (!app.view) return;
    document.querySelectorAll("#rail-tabs button").forEach((button) => {
      button.classList.toggle("active", button.dataset.rail === app.rail);
    });
    const body = $("rail-body");
    const rail = (app.view.rail || {});
    if (app.rail === "character") body.innerHTML = characterRail(rail.character || {});
    else if (app.rail === "quests") body.innerHTML = questsRail(rail.quests || {});
    else if (app.rail === "relations") body.innerHTML = relationsRail(rail.relations || {});
    else body.innerHTML = worldRail(rail.world || {});
    body.querySelectorAll("[data-open-world]").forEach((button) => {
      button.addEventListener("click", () => openWorld(button.dataset.openWorld));
    });
  }

  function section(title, html) {
    return `<section class="rail-section"><h3>${esc(title)}</h3>${html}</section>`;
  }

  const ATTR_LABELS = {
    str: "力量", dex: "敏捷", int: "智力", con: "体质", cha: "魅力",
    wis: "感知", luck: "幸运", per: "感知",
  };

  function attrLabel(key) {
    return ATTR_LABELS[String(key || "").toLowerCase()] || key;
  }

  function characterRail(character) {
    const p = character.player || {};
    const hp = Number(p.hp || 0), hpMax = Math.max(1, Number(p.hp_max || 1));
    const mp = Number(p.mp || 0), mpMax = Number(p.mp_max || 0);
    const items = p.inventory || [];
    const checks = character.checks || [];
    const attrs = Object.entries(p.attrs || {});
    const parts = [];

    parts.push(section("此人", `
      <div class="stat-grid">
        <div class="stat"><span class="k">${esc(p.name || "玩家")}</span><span class="v">${esc(p.level || "凡人")}</span></div>
        <div class="stat"><span class="k">所在</span><span class="v" style="font-size:14px">${esc(p.location || "未知")}</span></div>
        <div class="stat"><span class="k">气血</span><span class="v">${num(hp)} / ${num(hpMax)}</span>
          <div class="bar hp"><i style="width:${clamp(hp / hpMax * 100, 0, 100)}%"></i></div></div>
        ${mpMax > 0 ? `<div class="stat"><span class="k">内力</span><span class="v">${num(mp)} / ${num(mpMax)}</span>
          <div class="bar mp"><i style="width:${clamp(mp / mpMax * 100, 0, 100)}%"></i></div></div>` : ""}
      </div>
      <div class="row"><span>${esc(p.currency || "钱财")}</span><b>${num(p.gold)}</b></div>
      ${p.karma ? `<div class="row"><span>未清因果</span><b>${esc(typeof p.karma === "object" ? JSON.stringify(p.karma) : p.karma)}</b></div>` : ""}`));

    if (attrs.length) {
      parts.push(section("属性", `<div class="pill-row">${attrs.map(([k, v]) =>
        `<span class="pill">${esc(attrLabel(k))} ${num(v)}</span>`).join("")}</div>`));
    }
    parts.push(section("随身", items.length
      ? items.map((it) => `<div class="row"><span>${esc(it.name || it.key)}</span><b>×${num(it.quantity)}</b></div>`).join("")
      : `<p class="empty-small">空空如也。</p>`));

    if (checks.length) {
      parts.push(section("最近判定", checks.slice(0, 3).map((check) =>
        `<div class="row"><span>${esc(check.attribute || "判定")} ${esc(check.dice || "")}</span>
         <b>${esc(check.level_label || check.level || "")}</b></div>`).join("")));
    }

    const insights = character.insights || {};
    const flowState = insights.flow && (insights.flow.label || insights.flow.state || insights.flow.value);
    const flowMap = { flow: "心流", stuck: "滞涩", low: "低沉", high: "亢奋" };
    const flow = flowState ? (flowMap[flowState] || flowState) : "";
    const phase = insights.phase && (insights.phase.desc || insights.phase.label || insights.phase.phase || insights.phase.current);
    if (flow || phase) {
      parts.push(section("引擎推导", `
        ${flow ? `<div class="row"><span>心流</span><b>${esc(flow)}</b></div>` : ""}
        ${phase ? `<div class="row"><span>世界相位</span><b>${esc(phase)}</b></div>` : ""}`));
    }
    return parts.join("");
  }

  function summaryObject(value) {
    if (!value || typeof value !== "object") return esc(value || "");
    const keys = ["label", "title", "name", "value", "current", "state", "mode", "text"];
    const found = keys.map((key) => value[key]).filter((x) => x !== undefined && x !== null && x !== "");
    if (found.length) return found.map(esc).join(" · ");
    return esc(JSON.stringify(value));
  }

  function fractionText(value, fallback) {
    const label = value && (value.label || value.title || value.name) || fallback;
    if (!value || value.value === undefined || value.value === null) return esc(label);
    const max = value.max;
    return esc(max === undefined || max === null || Number(max) <= 0
      ? `${label} ${value.value}`
      : `${label} ${value.value}/${max}`);
  }

  function questsRail(quests) {
    const playbook = quests.playbook || {};
    const rows = quests.rows || [];
    const moves = quests.next_moves || [];
    const milestones = quests.milestones || [];
    const active = rows.find((q) => q.status === "active") || rows[0];
    const parts = [];

    // 同一件事只留一个入口：当前节拍 + 当前委托 + 一个非任务提示。
    // 完整任务链与玩法说明都折叠到“全部委托 / 这一局怎么玩”，不占据视线。
    let front = "";
    if (playbook.beat || playbook.progress || playbook.failure) {
      front += `<div class="quest-facts">
        ${playbook.beat ? `<div class="row"><span>当前节拍</span><b>${esc(summaryObject(playbook.beat))}</b></div>` : ""}
        ${playbook.progress ? `<div class="row"><span>进度</span><b>${fractionText(playbook.progress, "进度")}</b></div>` : ""}
        ${playbook.failure ? `<div class="row"><span>压力</span><b>${fractionText(playbook.failure, "失败")}</b></div>` : ""}
      </div>`;
    }
    if (active) {
      front += `<div class="quest-card">
        <b>${esc(active.title || active.id)}</b><span class="q-state">${esc(active.status || "")}</span>
        <small>${esc(active.stage_title || active.stage || "尚未开始")}</small>
        ${(active.objectives || []).length ? `<p>${esc(active.objectives.join("；"))}</p>` : ""}
      </div>`;
    } else {
      front += `<p class="empty-small">眼下还没有谁把事托到你手上。先四处走走，或开口问人。</p>`;
    }
    if (moves.length) {
      front += `<div class="row"><span>${esc(typeof moves[0] === "string" ? moves[0] : moves[0].text || moves[0].hint || "")}</span><b>风声</b></div>`;
    }
    if (rows.length > 1) {
      front += `<details class="rail-fold"><summary>全部委托 · ${rows.length}</summary>
        ${rows.map((q) => `<div class="row"><span>${esc(q.title || q.id)}</span><b>${esc(q.stage_title || q.status || "")}</b></div>`).join("")}
      </details>`;
    }
    if (playbook.loop_guide) {
      front += `<details class="rail-fold"><summary>这一局怎么玩</summary><p class="empty-small">${esc(playbook.loop_guide)}</p></details>`;
    }
    parts.push(section("眼前", front));

    if (milestones.length) {
      parts.push(section("记录", milestoneRows(milestones.slice(-3))));
    }
    return parts.join("");
  }

  function relationsRail(relations) {
    const present = relations.present || [];
    const others = relations.others || [];
    const rels = relations.relations || [];
    const parts = [];
    parts.push(section("在场", present.length ? present.map((person) => `
      <div class="person-card" title="${esc(person.desc || "")}">
        <span class="avatar">${esc((person.name || "?").slice(0, 1))}</span>
        <div><b>${esc(person.name || person.id)}</b>
          <small>${esc(person.level || "")}${person.faction ? ` · ${esc(person.faction)}` : ""}
          ${person.hp_pct != null ? ` · 气血 ${person.hp_pct}%` : ""}</small>
          ${person.personality ? `<p>${esc(person.personality)}</p>` : ""}
        </div>
      </div>`).join("") : `<p class="empty-small">这里只有你。</p>`));

    if (relations.relations && relations.relations.length) {
      parts.push(section("人情", rels.map((rel) =>
        `<div class="row"><span>${esc(rel.name || rel.id)}</span><b>亲 ${num(rel.affinity)} · 敬 ${num(rel.respect)}</b></div>`).join("")));
    }
    if (others.length) {
      parts.push(section("别处", others.slice(0, 8).map((person) =>
        `<div class="row"><span>${esc(person.name || person.id)}</span><b>${esc(person.location || "")}</b></div>`).join("")));
    }
    return parts.join("");
  }

  function worldParts(world) {
    const summary = world.summary || world.world_state || {};
    return {
      summary,
      flags: world.flags || [],
      places: world.places || [],
      market: world.market || [],
      milestones: world.milestones || [],
      factions: summary.factions || [],
    };
  }

  function factionRows(factions) {
    return factions.length
      ? factions.slice(0, 3).map((f) =>
        `<div class="row"><span>${esc(f.name)}</span><b>${num(f.power)}</b></div>`).join("")
      : `<p class="empty-small">还没有势力数据。</p>`;
  }

  const FLAG_LABELS = {
    "__start__": "投放开始",
    "raft_start": "救生筏开局",
    "vessel_base": "载具基地",
    "no_initial_island": "无初始岛屿",
    "tide_cycle": "潮汐周期",
    "safe_windows": "安全窗口",
    "system_guide": "系统引导",
    "vessel_ladder": "载具阶梯",
    "facility_ladder": "设施阶梯",
    "world_channel_on": "世界频道",
    "region_channel_on": "区域频道",
    "nearby_channel_on": "附近频道",
    "trade_channel_on": "交易频道",
    "newbie_protection": "新手保护",
    "system_decomp": "系统分解",
    "space_slots_6": "六格空间",
  };

  function flagLabel(flag) {
    const key = String(flag || "");
    return FLAG_LABELS[key] || key.replace(/^__|__$/g, "").replace(/_/g, " ");
  }

  function flagPills(flags) {
    return flags.length
      ? `<div class="pill-row">${flags.map((flag) => `<span class="pill">${esc(flagLabel(flag))}</span>`).join("")}</div>`
      : `<p class="empty-small">没有世界标记。</p>`;
  }

  function milestoneRows(milestones) {
    return milestones.length
      ? milestones.map((m) => `<div class="row"><span>${esc(m.title || m.desc || "")}</span><b>${m.tick == null ? "" : `第 ${m.tick} 回合`}</b></div>`).join("")
      : `<p class="empty-small">还没有大事记。</p>`;
  }

  function worldRail(world) {
    const { summary, flags, places, market, factions } = worldParts(world);
    const parts = [];
    parts.push(section("世界", `
      ${summary.phase ? `<div class="row"><span>相位</span><b>${esc(summaryObject(summary.phase))}</b></div>` : ""}
      ${summary.market_index != null ? `<div class="row"><span>物价指数</span><b>${num(summary.market_index)}</b></div>` : ""}
      ${factionRows(factions)}`));
    parts.push(section("标记", flagPills(flags)));
    parts.push(section("地点", places.length ? places.slice(0, 5).map((place) =>
      `<div class="row"><span>${esc(place.name)}</span><b>${place.last_tick ? `第 ${place.last_tick} 回合` : ""}</b></div>`).join("")
      : `<p class="empty-small">还没走过什么地方。</p>`));
    parts.push(section("市场", market.length
      ? `<p class="empty-small">${market.length} 个地点有行情。</p>`
      : `<p class="empty-small">没有市场数据。</p>`));
    parts.push(`<div class="world-actions">
      <button class="ghost-btn" type="button" data-open-world="codex">打开世界</button>
      <button class="ghost-btn" type="button" data-open-world="log">看日志</button>
    </div>`);
    return parts.join("");
  }

  /* ------------------------------------------------------------------ */
  /* World overlay                                                      */
  /* ------------------------------------------------------------------ */

  function openWorld(tab) {
    app.worldTab = tab || "codex";
    renderWorld();
    openOverlay("world-overlay");
  }

  function renderWorld() {
    document.querySelectorAll("#world-tabs button").forEach((button) => {
      button.classList.toggle("active", button.dataset.world === app.worldTab);
    });
    const view = app.view || {};
    const world = view.world_overlay || {};
    const body = $("world-body");
    $("world-overlay-title").textContent = (view.world && view.world.name) || "世界";
    if (app.worldTab === "codex") body.innerHTML = codexView(world.codex || {});
    else if (app.worldTab === "log") body.innerHTML = logView(world.events || []);
    else if (app.worldTab === "map") body.innerHTML = mapView(world);
    else if (app.worldTab === "market") body.innerHTML = marketView(world.market || []);
    else body.innerHTML = archiveView(world);
  }

  function codexView(codex) {
    const blocks = [
      ["地点", codex.locations || []],
      ["人物", codex.people || []],
      ["物品", codex.items || []],
      ["词条", codex.lore || []],
    ];
    const html = blocks.map(([title, rows]) => `
      <div class="codex-block"><h3>${esc(title)}</h3>
        ${rows.length ? rows.slice(0, 30).map((row) => `<p>${esc(row)}</p>`).join("") : `<p class="muted">还没有记录。</p>`}
      </div>`).join("");
    return `<div class="codex-grid">${html}</div>`;
  }

  function logView(events) {
    if (!events.length) return `<p class="empty">还没有值得记下的事。</p>`;
    return `<div class="log-list">${events.slice().reverse().map((event) => `
      <div class="log-item">
        <span class="tick">${event.tick == null ? "" : `#${event.tick}`}</span>
        <div><b>${esc(event.title || event.type || "事件")}</b><p>${esc(event.desc || "")}</p></div>
      </div>`).join("")}</div>`;
  }

  function mapView(world) {
    const { places, factions } = worldParts(world);
    return `
      <div class="map-list">
        ${places.length ? places.map((place) => `
          <div class="map-card"><h3>${esc(place.name)}</h3>
            <p>${esc(place.desc || place.last_prose || "还没有描写。")}</p></div>`).join("")
          : `<p class="empty">地图还是空的。走一走，它会慢慢长出来。</p>`}
      </div>
      <div class="rail-section" style="margin-top:16px"><h3>势力</h3>
        ${factionRows(factions)}
      </div>`;
  }

  function marketView(markets) {
    if (!markets.length) return `<p class="empty">这一局还没有市场。</p>`;
    return markets.map((market) => `
      <div class="rail-section"><h3>${esc(market.location)}</h3>
        <table class="market-table"><thead><tr><th>商品</th><th>类别</th><th class="num">价格</th><th class="num">库存</th></tr></thead>
        <tbody>${(market.items || []).map((item) => `
          <tr><td>${esc(item.name || item.key)}</td><td>${esc(item.type || "")}</td>
            <td class="num">${num(item.price)}${item.delta ? ` (${item.delta > 0 ? "+" : ""}${num(item.delta)})` : ""}</td>
            <td class="num">${num(item.supply)}</td></tr>`).join("")}</tbody></table>
      </div>`).join("");
  }

  function archiveView(world) {
    const { summary, flags, places, milestones } = worldParts(world);
    return `
      <div class="archive-grid">
        <div class="archive-card"><div class="v">${num(summary.collapses)}</div><div class="k">崩溃次数</div></div>
        <div class="archive-card"><div class="v">${num(world.summaries)}</div><div class="k">章节摘要</div></div>
        <div class="archive-card"><div class="v">${num(places.length)}</div><div class="k">地点</div></div>
        <div class="archive-card"><div class="v">${num(world.archived_events)}</div><div class="k">归档事件</div></div>
      </div>
      <div class="rail-section" style="margin-top:16px"><h3>大事记</h3>
        ${milestoneRows(milestones.slice().reverse())}
      </div>
      <div class="rail-section"><h3>世界标记</h3>
        ${flagPills(flags)}
      </div>`;
  }

  /* ------------------------------------------------------------------ */
  /* Chat                                                               */
  /* ------------------------------------------------------------------ */

  function autoGrow() {
    const el = $("action-text");
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  async function send() {
    if (app.busy) return;
    const input = $("action-text");
    const text = input.value.trim();
    if (!text) return;
    const model = (app.view && app.view.model) || {};
    if (!model.configured) {
      toast("先连接一个模型，再来对话");
      openModel();
      return;
    }
    app.busy = true;
    $("send-btn").disabled = true;
    $("typing").hidden = false;
    input.value = "";
    autoGrow();
    // Optimistic player bubble: the persisted turn will replace it on response.
    const optimistic = { id: "local-" + Date.now(), role: "player", tick: (app.view.world || {}).tick || 0, text, tools: [], status: "ok" };
    app.view.feed = (app.view.feed || []).concat(optimistic);
    renderFeed(app.view.feed);
    try {
      const payload = await api("/api/v1/chat", { method: "POST", body: { text } });
      app.view = payload.state;
      renderPlay();
      if (payload.tools && payload.tools.length) toast(`本回合结算 ${payload.tools.length} 次`, 1600);
    } catch (err) {
      toast(err.message, 5000);
      try {
        const refreshed = await api("/api/v1/state");
        app.view = refreshed;
        renderPlay();
      } catch (ignored) { /* keep the optimistic feed */ }
    } finally {
      app.busy = false;
      $("send-btn").disabled = false;
      $("typing").hidden = true;
      input.focus();
    }
  }

  /* ------------------------------------------------------------------ */
  /* Model dialog                                                       */
  /* ------------------------------------------------------------------ */

  const MODEL_PRESETS = [
    { label: "DeepSeek", base: "https://api.deepseek.com/v1", model: "deepseek-chat" },
    { label: "通义千问", base: "https://dashscope.aliyuncs.com/compatible-mode/v1", model: "qwen-plus" },
    { label: "本地 Ollama", base: "http://127.0.0.1:11434/v1", model: "qwen3:8b" },
    { label: "自定义", base: "", model: "" },
  ];

  function setConnectTab(tab) {
    document.querySelectorAll("#connect-tabs button").forEach((button) => {
      button.classList.toggle("active", button.dataset.connect === tab);
    });
    $("connect-model").hidden = tab !== "model";
    $("connect-agent").hidden = tab !== "agent";
  }

  function renderModelSummary(model) {
    const el = $("model-summary");
    el.className = "model-summary" + (model.configured ? "" : " bad");
    if (!model.configured) {
      el.textContent = model.has_api_key
        ? "还没填完整：接口地址和模型名都要有。"
        : "还没连上。填接口地址、模型名；云端网关还要 API Key，本地 Ollama 可以留空。";
      return;
    }
    if (model.source === "environment") {
      el.textContent = `当前由环境变量接管（${(model.env_keys || []).join("、")}）。面板里保存的地址和 Key 不会覆盖它。`;
      return;
    }
    el.textContent = `当前生效：${model.base_url} · ${model.model}${model.has_api_key ? "" : " · 未设 Key（本地端点可留空）"}`;
  }

  function renderModelPresets() {
    const row = $("model-presets");
    row.innerHTML = MODEL_PRESETS.map((item, index) =>
      `<button class="preset-chip" type="button" data-preset="${index}">${esc(item.label)}</button>`).join("");
    row.querySelectorAll("[data-preset]").forEach((button) => {
      button.addEventListener("click", () => {
        const preset = MODEL_PRESETS[Number(button.dataset.preset)];
        if (!preset) return;
        $("model-base").value = preset.base;
        $("model-name").value = preset.model;
        $("model-status").className = "model-status";
        $("model-status").textContent = preset.base
          ? "已填入参考值；模型名以你的账号控制台为准，改完再测试。"
          : "清空后填你自己的网关地址。";
        if (!preset.base) $("model-base").focus();
      });
    });
  }

  function modelPayload() {
    const number = (id, fallback) => {
      const value = Number($(id).value);
      return Number.isFinite(value) && value > 0 ? value : fallback;
    };
    return {
      base_url: $("model-base").value.trim(),
      model: $("model-name").value.trim(),
      api_key: $("model-key").value.trim(),
      timeout: number("model-timeout", 60),
      temperature: $("model-temperature").value === "" ? 0.7 : Number($("model-temperature").value),
      max_tokens: number("model-max-tokens", 1200),
    };
  }

  async function openModel() {
    try {
      const payload = await api("/api/v1/model/config");
      const model = payload.model || {};
      $("model-base").value = model.base_url || "";
      $("model-name").value = model.model || "";
      $("model-key").value = "";
      $("model-key").placeholder = model.api_key_masked
        ? `已保存（${model.api_key_masked}），留空则不改`
        : "sk-…（本地保存，0600）";
      $("model-timeout").value = model.timeout == null ? 60 : model.timeout;
      $("model-temperature").value = model.temperature == null ? 0.7 : model.temperature;
      $("model-max-tokens").value = model.max_tokens == null ? 1200 : model.max_tokens;
      renderModelSummary(model);
      $("model-status").className = "model-status";
      $("model-status").textContent = model.configured
        ? "保存后才会改变当前局使用的连接。"
        : "填完先测试，再保存；测试用当前输入，不必先存。";
    } catch (err) {
      toast(err.message);
    }
    setConnectTab("model");
    openOverlay("model-overlay");
  }

  async function saveModel() {
    const payload = modelPayload();
    if (!payload.base_url || !payload.model) {
      $("model-status").className = "model-status bad";
      $("model-status").textContent = "接口地址和模型名都要填。";
      return;
    }
    try {
      const result = await api("/api/v1/model/config", { method: "POST", body: payload });
      $("model-status").className = "model-status ok";
      $("model-status").textContent = result.model.source === "environment"
        ? "已保存，但环境变量仍在接管，实际请求不会用这份文件。"
        : "已保存。";
      if (app.bootstrap) app.bootstrap.model = result.model;
      if (app.view) { app.view.model = result.model; renderModelBadge(result.model); }
      renderModelSummary(result.model);
      toast("模型已保存");
    } catch (err) {
      $("model-status").className = "model-status bad";
      $("model-status").textContent = err.message;
    }
  }

  async function testModel() {
    const status = $("model-status");
    const payload = modelPayload();
    if (!payload.base_url || !payload.model) {
      status.className = "model-status bad";
      status.textContent = "先填接口地址和模型名，再测试。";
      return;
    }
    status.className = "model-status";
    status.textContent = "正在用当前输入测试…";
    try {
      const result = await api("/api/v1/model/test", { method: "POST", body: payload });
      status.className = "model-status ok";
      status.textContent = `连接正常 · ${result.model || payload.model} · ${result.latency_ms || 0}ms`;
    } catch (err) {
      status.className = "model-status bad";
      status.textContent = err.message;
    }
  }

  async function copyCode(button) {
    const target = document.querySelector(button.dataset.copy);
    if (!target) return;
    const text = target.textContent;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const area = document.createElement("textarea");
        area.value = text;
        area.style.position = "fixed";
        area.style.left = "-9999px";
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        area.remove();
      }
      const old = button.textContent;
      button.textContent = "已复制";
      setTimeout(() => { button.textContent = old; }, 1200);
    } catch (err) {
      toast("复制失败，请手动选中命令");
    }
  }

  /* ------------------------------------------------------------------ */
  /* SSE                                                                */
  /* ------------------------------------------------------------------ */

  function connectSSE() {
    if (app.sse) { app.sse.close(); app.sse = null; }
    if (!$("play").hidden && window.EventSource) {
      app.sse = new EventSource("/api/v1/events");
      app.sse.addEventListener("state", (event) => {
        if (app.busy || $("play").hidden) return;
        try {
          const next = JSON.parse(event.data);
          if (next && next.ok !== false) {
            app.view = next;
            renderPlay();
          }
        } catch (err) { /* ignore malformed frame */ }
      });
    }
  }

  /* ------------------------------------------------------------------ */
  /* Events                                                             */
  /* ------------------------------------------------------------------ */

  function bind() {
    $("send-btn").addEventListener("click", send);
    $("action-text").addEventListener("input", autoGrow);
    $("action-text").addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        send();
      }
    });

    $("new-btn").addEventListener("click", openSession);
    $("session-next").addEventListener("click", sessionNext);
    $("session-back").addEventListener("click", sessionBack);
    $("lobby-model-btn").addEventListener("click", openModel);
    $("model-badge").addEventListener("click", openModel);

    $("back-btn").addEventListener("click", () => {
      if (app.sse) { app.sse.close(); app.sse = null; }
      showScreen("lobby");
      refreshLobby();
    });

    $("menu-btn").addEventListener("click", () => openOverlay("menu-overlay"));
    $("menu-saves").addEventListener("click", () => { closeAllOverlays(); showScreen("lobby"); refreshLobby(); });
    $("menu-model").addEventListener("click", () => { closeOverlay("menu-overlay"); openModel(); });
    $("menu-world").addEventListener("click", () => { closeOverlay("menu-overlay"); openWorld("codex"); });
    $("menu-export").addEventListener("click", () => { window.location.href = "/api/v1/export"; });
    $("menu-about").addEventListener("click", () => toast("World Walker · 对话游戏引擎：AI 演，引擎判，存档记。", 5000));
    $("menu-back").addEventListener("click", () => {
      closeAllOverlays();
      if (app.sse) { app.sse.close(); app.sse = null; }
      showScreen("lobby");
      refreshLobby();
    });

    $("model-save").addEventListener("click", saveModel);
    $("model-test").addEventListener("click", testModel);
    renderModelPresets();
    document.querySelectorAll("#connect-tabs button").forEach((button) => {
      button.addEventListener("click", () => setConnectTab(button.dataset.connect));
    });
    document.querySelectorAll("[data-copy]").forEach((button) => {
      button.addEventListener("click", () => copyCode(button));
    });

    document.querySelectorAll("#rail-tabs button").forEach((button) => {
      button.addEventListener("click", () => { app.rail = button.dataset.rail; renderRail(); });
    });
    document.querySelectorAll("#world-tabs button").forEach((button) => {
      button.addEventListener("click", () => { app.worldTab = button.dataset.world; renderWorld(); });
    });
    document.querySelectorAll("[data-close]").forEach((button) => {
      button.addEventListener("click", () => closeOverlay(button.dataset.close));
    });
    document.querySelectorAll(".overlay").forEach((overlay) => {
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) overlay.hidden = true;
      });
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeAllOverlays();
    });

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && !$("play").hidden) {
        api("/api/v1/state").then((view) => { if (!app.busy) { app.view = view; renderPlay(); } }).catch(() => {});
      }
    });
  }

  async function boot() {
    bind();
    try {
      app.bootstrap = await api("/api/v1/bootstrap");
      renderLobby();
    } catch (err) {
      toast(err.message);
    }
  }

  boot();
})();
