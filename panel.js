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
    renderWorlds(data.worlds || []);
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
      body.innerHTML = `<p class="muted">还没有正在进行的局。选一个世界，说第一句话。</p>`;
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

  function renderWorlds(worlds) {
    const list = $("world-list");
    if (!worlds.length) {
      list.innerHTML = `<p class="empty">没有找到设定包或模板。</p>`;
      return;
    }
    const first = app.selectedWorld || worlds[0];
    app.selectedWorld = first;
    list.innerHTML = worlds.map((world) => `
      <button class="world-item ${world.kind === first.kind && world.id === first.id ? "active" : ""}"
              type="button" role="option" data-kind="${esc(world.kind)}" data-id="${esc(world.id)}">
        <span class="w-main"><b>${esc(world.name)}</b><small>${esc(world.notes || world.genre || "")}</small></span>
        <span class="w-kind">${world.kind === "template" ? "模板" : "设定包"}</span>
      </button>`).join("");
    list.querySelectorAll(".world-item").forEach((item) => {
      item.addEventListener("click", () => {
        app.selectedWorld = { kind: item.dataset.kind, id: item.dataset.id,
          name: item.querySelector("b").textContent };
        list.querySelectorAll(".world-item").forEach((x) => x.classList.remove("active"));
        item.classList.add("active");
      });
    });
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
    if (!app.selectedWorld) { toast("先选一个世界"); return; }
    const name = $("new-name").value.trim();
    const button = $("new-btn");
    button.disabled = true;
    button.textContent = "正在开局…";
    try {
      const payload = await api("/api/v1/new", {
        method: "POST",
        body: { kind: app.selectedWorld.kind, id: app.selectedWorld.id, name },
      });
      app.view = payload.state;
      app.feedFirst = true;
      $("new-name").value = "";
      showScreen("play");
      renderPlay();
      connectSSE();
      toast("新的一局开始了");
    } catch (err) {
      toast(err.message);
    } finally {
      button.disabled = false;
      button.textContent = "开始";
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
    const mp = Number(p.mp || 0), mpMax = Math.max(1, Number(p.mp_max || 1));
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
        <div class="stat"><span class="k">内力</span><span class="v">${num(mp)} / ${num(mpMax)}</span>
          <div class="bar mp"><i style="width:${clamp(mp / mpMax * 100, 0, 100)}%"></i></div></div>
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

  function questsRail(quests) {
    const playbook = quests.playbook || {};
    const rows = quests.rows || [];
    const moves = quests.next_moves || [];
    const milestones = quests.milestones || [];
    const parts = [];

    if (playbook.loop_guide || playbook.beat || playbook.progress || playbook.failure) {
      parts.push(section("这一局怎么玩", `
        ${playbook.loop_guide ? `<p class="empty-small">${esc(playbook.loop_guide)}</p>` : ""}
        ${playbook.beat ? `<div class="row"><span>当前节拍</span><b>${esc(summaryObject(playbook.beat))}</b></div>` : ""}
        ${playbook.progress ? `<div class="row"><span>进度</span><b>${esc(summaryObject(playbook.progress))}</b></div>` : ""}
        ${playbook.failure ? `<div class="row"><span>失败</span><b>${esc(summaryObject(playbook.failure))}</b></div>` : ""}`));
    }

    parts.push(section("当前目标", rows.length ? rows.map((q) => `
      <div class="quest-card">
        <b>${esc(q.title || q.id)}</b><span class="q-state">${esc(q.status || "")}</span>
        <small>${esc(q.stage_title || q.stage || "尚未开始")}</small>
        ${(q.objectives || []).length ? `<p>${esc(q.objectives.join("；"))}</p>` : ""}
      </div>`).join("") : `<p class="empty-small">还没有浮现的目标。先四处走走。</p>`));

    if (moves.length) {
      parts.push(section("可以试试", moves.slice(0, 4).map((move) =>
        `<div class="row"><span>${esc(typeof move === "string" ? move : move.text || move.hint || "")}</span></div>`).join("")));
    }
    if (milestones.length) {
      parts.push(section("大事记", milestones.slice(-3).map((m) =>
        `<div class="row"><span>${esc(m.title || m.desc || "")}</span><b>${esc(m.tick == null ? "" : `第 ${m.tick} 回合`)}</b></div>`).join("")));
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

  function worldRail(world) {
    const summary = world.summary || {};
    const flags = world.flags || [];
    const places = world.places || [];
    const market = world.market || [];
    const parts = [];
    parts.push(section("世界", `
      ${summary.phase ? `<div class="row"><span>相位</span><b>${esc(summaryObject(summary.phase))}</b></div>` : ""}
      ${summary.market_index != null ? `<div class="row"><span>物价指数</span><b>${num(summary.market_index)}</b></div>` : ""}
      ${(summary.factions || []).slice(0, 3).map((f) =>
        `<div class="row"><span>${esc(f.name)}</span><b>${num(f.power)}</b></div>`).join("")}`));
    parts.push(section("标记", flags.length
      ? `<div class="pill-row">${flags.map((flag) => `<span class="pill">${esc(flag)}</span>`).join("")}</div>`
      : `<p class="empty-small">没有世界标记。</p>`));
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
    const places = world.places || [];
    const summary = world.world_state || {};
    const factions = summary.factions || [];
    return `
      <div class="map-list">
        ${places.length ? places.map((place) => `
          <div class="map-card"><h3>${esc(place.name)}</h3>
            <p>${esc(place.desc || place.last_prose || "还没有描写。")}</p></div>`).join("")
          : `<p class="empty">地图还是空的。走一走，它会慢慢长出来。</p>`}
      </div>
      <div class="rail-section" style="margin-top:16px"><h3>势力</h3>
        ${factions.length ? factions.map((f) => `<div class="faction-row"><span>${esc(f.name)}</span><b>${num(f.power)}</b></div>`).join("")
          : `<p class="empty-small">还没有势力数据。</p>`}
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
    const summary = world.world_state || {};
    const milestones = world.milestones || [];
    return `
      <div class="archive-grid">
        <div class="archive-card"><div class="v">${num(summary.collapses)}</div><div class="k">崩溃次数</div></div>
        <div class="archive-card"><div class="v">${num(world.summaries)}</div><div class="k">章节摘要</div></div>
        <div class="archive-card"><div class="v">${num((world.places || []).length)}</div><div class="k">地点</div></div>
        <div class="archive-card"><div class="v">${num(world.archived_events)}</div><div class="k">归档事件</div></div>
      </div>
      <div class="rail-section" style="margin-top:16px"><h3>大事记</h3>
        ${milestones.length ? milestones.slice().reverse().map((m) => `
          <div class="row"><span>${esc(m.title || m.desc || "")}</span><b>${m.tick == null ? "" : `第 ${m.tick} 回合`}</b></div>`).join("")
          : `<p class="empty-small">还没有大事记。</p>`}
      </div>
      <div class="rail-section"><h3>世界标记</h3>
        ${(world.flags || []).length ? `<div class="pill-row">${world.flags.map((f) => `<span class="pill">${esc(f)}</span>`).join("")}</div>`
          : `<p class="empty-small">没有。</p>`}
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
      $("model-status").className = "model-status";
      $("model-status").textContent = model.configured
        ? "已连接；测试一次确认网关可用。"
        : "还没有连接模型。填完保存即可开始对话。";
    } catch (err) {
      toast(err.message);
    }
    openOverlay("model-overlay");
  }

  async function saveModel() {
    const payload = {
      base_url: $("model-base").value.trim(),
      model: $("model-name").value.trim(),
      api_key: $("model-key").value.trim(),
    };
    if (!payload.base_url || !payload.model) {
      $("model-status").className = "model-status bad";
      $("model-status").textContent = "接口地址和模型名都要填。";
      return;
    }
    try {
      const result = await api("/api/v1/model/config", { method: "POST", body: payload });
      $("model-status").className = "model-status ok";
      $("model-status").textContent = "已保存。";
      if (app.bootstrap) app.bootstrap.model = result.model;
      if (app.view) { app.view.model = result.model; renderModelBadge(result.model); }
      toast("模型已保存");
    } catch (err) {
      $("model-status").className = "model-status bad";
      $("model-status").textContent = err.message;
    }
  }

  async function testModel() {
    const status = $("model-status");
    status.className = "model-status";
    status.textContent = "正在测试…";
    try {
      const result = await api("/api/v1/model/test", { method: "POST", body: {} });
      status.className = "model-status ok";
      status.textContent = `连接正常 · ${result.model || "模型"} · ${result.latency_ms || 0}ms`;
    } catch (err) {
      status.className = "model-status bad";
      status.textContent = err.message;
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

    $("new-btn").addEventListener("click", createGame);
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
