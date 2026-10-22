/*
 万界·行者 · 实况主舞台 前端

 三层结构（见 ARCHITECTURE.md ADR-001/003）：
   panelData  —— 取数：fetch('/state') + SSE('/events')，SSE 断了退回轮询
   panelState —— 上次视图模型、已提示过的事件 id、当前弹窗、动效开关
   render*    —— 纯渲染：把视图模型写进 DOM（状态文字一律 textContent）

 规则：事件分类（kind/severity/title/icon）由 panel.py 决定，本文件不做任何关键词判断。
*/

(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const pct = (a, b) => Math.max(0, Math.min(100, b > 0 ? a * 100 / b : 0));
  const SEV_RANK = { info: 0, warning: 1, success: 1, danger: 2 };
  const MOOD_LABEL = {
    neutral: "寻常", danger: "危急", trade: "市易",
    social: "人情", growth: "精进", discovery: "初探",
  };

  /* ── panelState ───────────────────────────────────── */
  const panelState = {
    vm: null,              // 上次视图模型
    shownEvents: new Set(),// 已弹过提示的事件 id（本轮页面生命周期内）
    primed: false,         // 首次渲染前不弹历史事件的提示
    dialogFor: null,       // 弹窗正在展示的事件
    focusReturn: null,     // 关闭弹窗后焦点归还的控件
    motion: true,          // 动效开关
  };

  /* ── 小工具 ───────────────────────────────────────── */
  function setText(el, text) { if (el) el.textContent = text; }

  function chip(el, arr, cls) {
    if (!el) return;
    el.textContent = "";
    const list = Array.isArray(arr) ? arr : [];
    if (!list.length) {
      const s = document.createElement("span");
      s.className = "empty";
      s.textContent = "（还没有）";
      el.appendChild(s);
      return;
    }
    list.forEach((x) => {
      const s = document.createElement("span");
      s.className = "chip" + (cls ? " " + cls : "");
      s.textContent = String(x);
      el.appendChild(s);
    });
  }

  function fmtFlow(f) {
    if (!f || f.state === undefined) return "—";
    const m = { anxiety: "焦虑", flow: "心流", boredom: "无聊", unknown: "—" };
    return (m[f.state] || f.state) +
      (f.adjustment !== undefined ? "（" + (f.adjustment > 0 ? "+" : "") + f.adjustment + "）" : "");
  }

  function fmtPhase(p) {
    if (!p) return "—";
    if (typeof p === "string") return p;
    // panarchy 返回 {phase:"r", desc:"开发/增长", trigger:"…"}：给人看的应是描述，字母只是代号
    const zh = p.desc || p.phase || p.current || p.name;
    if (!zh) return JSON.stringify(p).slice(0, 40);
    return p.phase && p.desc ? String(p.desc) : String(zh);
  }

  function phaseTitle(p) {
    if (!p || typeof p !== "object") return "";
    const bits = [];
    if (p.phase) bits.push("相位 " + p.phase);
    if (p.trigger) bits.push(p.trigger);
    return bits.join(" · ");
  }

  function fmtIdentity(i) {
    if (!i || typeof i !== "object") return "";
    return Object.entries(i)
      .filter(([, v]) => typeof v === "number")
      .sort((a, b) => b[1] - a[1]).slice(0, 2)
      .map(([k, v]) => k + " " + v.toFixed(2)).join(" · ");
  }

  function relChipClass(v) {
    if (v >= 30) return "good";
    if (v <= -30) return "bad";
    return "dim";
  }

  /* 大数可读：千分位只在展示层用，接口与状态里仍是数值（图表解析不受影响） */
  function fmtNum(n) {
    if (typeof n !== "number" || !isFinite(n)) return n == null ? "—" : String(n);
    return n.toLocaleString("zh-CN");
  }

  /* ── 错误/空态横幅：状态读不到时不清屏、不装死，给出原因与重试 ── */
  function showNotice(msg, hint) {
    const box = $("notice");
    if (!box) return;
    setText($("notice-text"), msg + (hint ? "　" + hint : ""));
    box.hidden = false;
  }

  function hideNotice() {
    const box = $("notice");
    if (box) box.hidden = true;
  }

  /* ── render：主舞台 ───────────────────────────────── */
  function renderScene(v) {
    const sc = v.scene || {};
    setText($("scene-title"), sc.title || "未命名之地");
    const desc = $("scene-desc");
    if (sc.description) {
      desc.textContent = sc.description;
      desc.classList.remove("empty");
    } else {
      desc.textContent = "（尚无场景描写——开局后由状态与摘要填充）";
      desc.classList.add("empty");
    }
    const mood = $("scene-mood");
    mood.hidden = !sc.mood;
    mood.dataset.mood = sc.mood || "neutral";
    setText(mood, MOOD_LABEL[sc.mood] || sc.mood || "");
    const focus = $("scene-focus");
    if (sc.focus_event) {
      focus.hidden = false;
      focus.textContent = "";
      const b = document.createElement("b");
      b.textContent = "当前焦点：";
      focus.appendChild(b);
      focus.appendChild(document.createTextNode(sc.focus_event));
    } else {
      focus.hidden = true;
    }
  }

  /* ── render：HUD ──────────────────────────────────── */
  function renderHud(v) {
    const p = v.player || {};
    const worldName = (v.world && v.world.name) || "未命名世界";
    const skin = v.skin || {};
    const brand = skin.brand || "万界·行者";
    setText($("world"), worldName);
    const mark = document.querySelector(".wordmark");
    if (mark) mark.textContent = brand;
    const seal = document.querySelector(".seal");
    if (seal) seal.textContent = brand.slice(0, 1);
    const tag = document.querySelector(".tagline");
    if (tag) tag.textContent = skin.tagline || "";
    document.title = (worldName === brand || !worldName) ? brand : (worldName + " · " + brand);
    setText($("era"), (v.world && v.world.era) || "");
    setText($("tick"), "回合 " + fmtNum(v.tick));
    setText($("clock"), "更新于 " + (v.updated_at || "—"));

    setText($("pname"), p.name || "—");
    setText($("pname-sub"), (p.stage ? "第 " + p.stage + " 阶段" : "") || "");
    setText($("plevel"), p.level || "—");
    setText($("ploc"), p.location || "—");
    setText($("phpn"), fmtNum(p.hp) + "/" + fmtNum(p.hp_max));
    setText($("pmpn"), fmtNum(p.mp) + "/" + fmtNum(p.mp_max));
    setText($("pgold"), "钱财 " + fmtNum(p.gold) + " " + (p.currency || ""));

    const hpBar = $("phpbar");
    const hpLow = p.hp_max > 0 && p.hp / p.hp_max < 0.3;
    hpBar.style.width = pct(p.hp, p.hp_max) + "%";
    hpBar.classList.toggle("low", hpLow);
    $("pmpbar").style.width = pct(p.mp, p.mp_max || 1) + "%";
    const warn = $("hpwarn");
    if (warn) warn.hidden = !hpLow;

    const attrs = $("pattrs");
    attrs.textContent = "";
    Object.entries(p.attrs || {}).forEach(([k, x]) => {
      const s = document.createElement("span");
      s.className = "chip dim";
      s.textContent = k + " " + x;
      attrs.appendChild(s);
    });

    const ins = v.insights || {};
    setText($("flow"), fmtFlow(ins.flow));
    const phaseEl = $("phase");
    setText(phaseEl, fmtPhase(ins.phase));
    phaseEl.title = phaseTitle(ins.phase) || fmtIdentity(ins.identity);

    const karmaEl = $("karma");
    karmaEl.textContent = "";
    const kv = (v.player || {}).karma != null ? v.player.karma : (v.karma || 0);
    if (kv > 0) {
      const b = document.createElement("b");
      b.style.color = "var(--danger)";
      b.textContent = String(kv);
      karmaEl.appendChild(b);
    } else {
      karmaEl.textContent = "0";
    }

    const moral = $("moral");
    moral.textContent = "";
    ((v.moral || {}).dims || []).forEach((d, i) => {
      const val = ((v.moral || {}).values || [])[i] || 0;
      const wrap = document.createElement("span");
      wrap.style.marginRight = "8px";
      const b = document.createElement("b");
      b.textContent = d;
      const s = document.createElement("span");
      s.style.color = val > 0 ? "var(--success)" : (val < 0 ? "var(--danger)" : "var(--text-dim)");
      s.textContent = (val > 0 ? "+" : "") + val;
      wrap.appendChild(b);
      wrap.appendChild(document.createTextNode(" "));
      wrap.appendChild(s);
      moral.appendChild(wrap);
    });

    const inv = (p.inventory || []);
    setText($("inv-count"), inv.length ? inv.length + " 种" : "");
    const invEl = $("inventory");
    invEl.textContent = "";
    if (!inv.length) {
      const s = document.createElement("span");
      s.className = "empty";
      s.textContent = "（空手）";
      invEl.appendChild(s);
    } else {
      inv.forEach((it) => {
        const s = document.createElement("span");
        s.className = "chip" + (it.type === "丹药" || it.type === "药品" ? " good" : "");
        s.textContent = it.name + " ×" + it.quantity;
        invEl.appendChild(s);
      });
    }
  }

  /* ── render：在场 / 关系 ──────────────────────────── */
  /* 长局收敛：人会越攒越多（2000 轮实测 96 段关系、20+ 在场），
     首屏只列最相关的若干条，其余折叠——信息不丢，但不再糊成一整面墙。 */
  const PRESENT_TOP = 6;
  const REL_TOP = 8;

  function expander(host, total, shown, onExpand, noun) {
    if (total <= shown) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tbtn more-btn";
    btn.textContent = "展开其余 " + (total - shown) + " " + noun + "（共 " + total + "）";
    btn.addEventListener("click", () => {
      btn.remove();
      onExpand();
    });
    host.appendChild(btn);
  }

  function renderCast(v) {
    const relMap = {};
    (v.relations || []).forEach((r) => { relMap[r.id] = r; });

    const present = $("present");
    present.textContent = "";
    const list = v.present || [];
    setText($("present-count"), list.length ? list.length + " 人" : "");
    if (!list.length) {
      const s = document.createElement("span");
      s.className = "empty";
      s.textContent = "此刻无人";
      present.appendChild(s);
    } else {
      const drawCast = (c) => {
        const div = document.createElement("div");
        div.className = "castcard";
        if (c.hp != null && c.hp <= 0) div.classList.add("down");
        else if (relMap[c.id] && relMap[c.id].affinity <= -30) div.classList.add("hostile");
        const b = document.createElement("b");
        b.textContent = c.name;
        div.appendChild(b);
        const meta = document.createElement("span");
        meta.className = "d";
        meta.textContent = " " + (c.level || "") + (c.hp_max ? " · 气血 " + c.hp + "/" + c.hp_max : "");
        div.appendChild(meta);
        if (c.desc) {
          const d = document.createElement("div");
          d.className = "d";
          d.textContent = c.desc;
          div.appendChild(d);
        }
        const rel = relMap[c.id];
        if (rel) {
          const r = document.createElement("div");
          r.className = "rel";
          const chipEl = document.createElement("span");
          chipEl.className = "chip " + relChipClass(rel.affinity);
          chipEl.textContent = "亲密 " + rel.affinity + " · 敬重 " + rel.respect;
          r.appendChild(chipEl);
          div.appendChild(r);
        }
        present.appendChild(div);
      };
      const ranked = list.slice().sort((a, b) => {
        const ra = relMap[a.id] ? Math.abs(relMap[a.id].affinity) : -1;
        const rb = relMap[b.id] ? Math.abs(relMap[b.id].affinity) : -1;
        return rb - ra;
      });
      ranked.slice(0, PRESENT_TOP).forEach(drawCast);
      expander(present, ranked.length, PRESENT_TOP,
               () => ranked.slice(PRESENT_TOP).forEach(drawCast), "人");
    }

    const others = $("others");
    const olist = v.others || [];
    setText(others, olist.length
      ? "别处 " + olist.length + " 人：" + olist.slice(0, 6).map((o) => o.name).join("、")
        + (olist.length > 6 ? "…" : "")
      : "");

    const rels = $("relations");
    rels.textContent = "";
    const rlist = (v.relations || []).slice().sort((a, b) => Math.abs(b.affinity) - Math.abs(a.affinity));
    setText($("rel-count"), rlist.length ? rlist.length + " 人" : "");
    if (!rlist.length) {
      const s = document.createElement("span");
      s.className = "empty";
      s.textContent = "（尚未结缘）";
      rels.appendChild(s);
    } else {
      const drawRel = (r) => {
        const s = document.createElement("span");
        s.className = "chip " + relChipClass(r.affinity);
        s.textContent = r.name + " 亲密" + r.affinity + " / 敬重" + r.respect;
        s.title = r.id;
        rels.appendChild(s);
      };
      rlist.slice(0, REL_TOP).forEach(drawRel);
      expander(rels, rlist.length, REL_TOP,
               () => rlist.slice(REL_TOP).forEach(drawRel), "段关系");
    }
  }

  /* ── render：时间线 ───────────────────────────────── */
  function timelineItem(e) {
    const li = document.createElement("li");
    li.dataset.severity = e.severity;
    li.dataset.eventId = e.id;
    if (e.milestone) {
      li.classList.add("is-milestone");
      li.title = "大事记：会被 recap 与回捞记住的事件";
    }
    const t = document.createElement("span");
    t.className = "t";
    t.textContent = e.tick != null ? e.tick : "";
    const y = document.createElement("span");
    y.className = "y";
    const sev = document.createElement("span");
    sev.className = "sev";
    sev.textContent = e.icon + " " + e.kind;
    y.appendChild(sev);
    if (e.milestone) {
      const tag = document.createElement("span");
      tag.className = "chip accent";
      tag.style.cssText = "margin:2px 0 0;padding:0 7px;font-size:11px";
      tag.textContent = "记";
      y.appendChild(tag);
    }
    const d = document.createElement("span");
    d.className = "d";
    // 合并过的重复事件标出次数，玩家才知道"连打 4 回合都被闪"而不是只发生一次
    d.textContent = e.desc + (e.repeat > 1 ? "（×" + e.repeat + "）" : "");
    li.appendChild(t);
    li.appendChild(y);
    li.appendChild(d);
    // 条目可点开详情：时间线只给一行摘要，玩家常需要看完整事件
    // （时间/类型/是否大事记/重复次数）。复用事件弹窗，不新造一层 UI。
    li.tabIndex = 0;
    li.setAttribute("role", "button");
    li.style.cursor = "pointer";
    li.title = "点击查看事件详情";
    const openIt = (ev) => { ev.preventDefault(); openDialog(e, li); };
    li.addEventListener("click", openIt);
    li.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") openIt(ev);
    });
    return li;
  }

  function renderTimeline(v) {
    const ul = $("timeline");
    ul.textContent = "";
    const events = (v.events || []).slice().reverse();
    setText($("timeline-hint"),
      "大事记 " + ((v.milestones || []).length) + " · 归档 " + (v.archived_events || 0));
    if (!events.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "暂无事件";
      ul.appendChild(li);
      return;
    }
    events.forEach((e) => ul.appendChild(timelineItem(e)));
  }

  function renderDrawers(v) {
    const cx = v.codex || {};
    chip($("cx-loc"), cx.locations, "accent");
    chip($("cx-people"), cx.people, "");
    chip($("cx-items"), cx.items, "");
    chip($("cx-lore"), cx.lore, "dim");
    setText($("lorecnt"), "设定词条 " + (v.lore_total || 0) + " 条");

    const market = $("market");
    market.textContent = "";
    const mlist = v.market || [];
    if (!mlist.length) {
      const s = document.createElement("span");
      s.className = "empty";
      s.textContent = "此界无市";
      market.appendChild(s);
    } else {
      const here = (v.player || {}).location;
      mlist.forEach((m) => {
        const head = document.createElement("div");
        head.className = "row";
        const k = document.createElement("span");
        k.className = "k";
        k.textContent = m.location + (m.location === here ? "（本地）" : "");
        head.appendChild(k);
        market.appendChild(head);
        const table = document.createElement("table");
        const thead = document.createElement("tr");
        ["物品", "价", "基准", "库存"].forEach((h) => {
          const th = document.createElement("th");
          th.textContent = h;
          thead.appendChild(th);
        });
        table.appendChild(thead);
        (m.items || []).forEach((it) => {
          const tr = document.createElement("tr");
          const td1 = document.createElement("td");
          td1.textContent = it.name;
          const td2 = document.createElement("td");
          td2.className = it.delta > 0 ? "up" : (it.delta < 0 ? "down" : "flat");
          td2.textContent = it.price + (it.delta > 0 ? " ▲" : (it.delta < 0 ? " ▼" : " ＝"));
          const td3 = document.createElement("td");
          td3.textContent = it.base_price;
          const td4 = document.createElement("td");
          td4.textContent = it.supply;
          [td1, td2, td3, td4].forEach((td) => tr.appendChild(td));
          table.appendChild(tr);
        });
        market.appendChild(table);
      });
    }

    const ms = $("milestones");
    ms.textContent = "";
    const mlist2 = v.milestones || [];
    setText($("memhint"), "摘要 " + (v.summaries || 0) + " 条 · 归档 " + (v.archived_events || 0) + " 条");
    if (!mlist2.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "暂无";
      ms.appendChild(li);
    } else {
      mlist2.forEach((m) => {
        const li = document.createElement("li");
        li.className = "is-milestone";
        const d = document.createElement("span");
        d.className = "d";
        d.textContent = m;
        li.appendChild(d);
        ms.appendChild(li);
      });
    }

    chip($("flags"), v.flags, "dim");
  }

  /* ── 长局态势：三张离线图表（ECharts 缺失时降级为文案）── */
  const charts = { c1: null, c2: null, c3: null };
  let lastSeriesKey = "";
  let seriesCache = null;

  function chartReady() { return typeof window.echarts !== "undefined"; }

  function chartPalette(vm) {
    const p = (vm && vm.skin && vm.skin.palette) || {};
    return {
      line: p.line || "#e8b04b",
      area: p.area || "rgba(232,176,75,.18)",
      bar: p.bar || "#c07a3a",
      hp: p.hp || "#d9534f",
      mp: p.mp || "#4a90d9",
      grid: p.grid || "#2b3341",
      text: p.text || "#a3abb9",
    };
  }

  function chartBase(pal, rightPad) {
    return {
      animation: panelState.motion,
      backgroundColor: "transparent",
      grid: { left: 46, right: rightPad || 18, top: 30, bottom: 26 },
      textStyle: { color: pal.text, fontSize: 11 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#151920",
        borderColor: pal.grid,
        textStyle: { color: "#ecebe6", fontSize: 12 },
      },
      legend: { top: 0, textStyle: { color: pal.text, fontSize: 11 }, icon: "roundRect" },
      xAxis: {
        type: "category",
        boundaryGap: false,
        axisLine: { lineStyle: { color: pal.grid } },
        axisLabel: { color: pal.text },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: pal.grid, opacity: .5 } },
        axisLabel: { color: pal.text },
      },
    };
  }

  function ensureChart(key, elId, emptyId) {
    const el = $(elId);
    const emptyEl = $(emptyId);
    if (!el) return null;
    if (!chartReady()) {
      if (emptyEl) {
        emptyEl.hidden = false;
        emptyEl.textContent = "图表库未加载（离线资产 assets/echarts.min.js 缺失或被拦截）——数据仍在上方时间线与 HUD 中。";
      }
      el.hidden = true;
      return null;
    }
    if (!charts[key]) charts[key] = window.echarts.init(el, null, { renderer: "canvas" });
    return charts[key];
  }

  function renderCharts(vm, series) {
    const samples = (series && series.samples) || [];
    const ticks = samples.map((s) => s.tick);
    const pal = chartPalette(vm);
    const enough = samples.length >= 2;

    // 图一：行藏曲线（气血% / 内力% / 钱财）
    let c1 = ensureChart("c1", "chart1", "chart1-empty");
    if (c1) {
      $(("chart1-empty")).hidden = enough;
      c1.getDom && (c1.getDom().style.display = enough ? "" : "none");
      if (enough) {
        const hpPct = samples.map((s) => Math.round(s.hp * 100 / Math.max(1, s.hp_max)));
        const mpPct = samples.map((s) => Math.round(s.mp * 100 / Math.max(1, s.mp_max || 1)));
        const gold = samples.map((s) => s.gold);
        // 图鉴累计（地点/人物/物品/词条）：长局里唯一"只增不减"的成长指标，
        // 气血常因突破回满而看不出变化，用它才能看出"这局到底走了多远"。
        const codex = samples.map((s) => s.codex_total || 0);
        const codexGrows = codex.length && (codex[codex.length - 1] - codex[0]) > 0;
        // 自适应纵轴：长局里气血常年在 76–100% 之间，固定 0–100 会把它压成一条
        // 贴着顶边的直线，玩家看不出任何起伏。这里按实际范围外扩一点，
        // 但如果跨度本身就很大（>60），仍回到 0–100 以免夸大小波动。
        const spanOf = (arr) => {
          const lo = Math.min.apply(null, arr), hi = Math.max.apply(null, arr);
          return { lo, hi, span: hi - lo };
        };
        const hpSpan = spanOf(hpPct), mpSpan = spanOf(mpPct);
        // 全程无波动的序列在图上就是一条贴边的直线，读者会以为是渲染故障。
        // 在系列名里标注"恒定 N%"，让"没变化"本身成为可读信息。
        // "看起来是平线"的两种情形：跨度极小（<5 点），或绝大多数点挤在同一值
        // （长局里玩家靠突破回满，600 回合里可能只有 1 次受伤）。
        const dominantShare = (arr) => {
          const c = {}; arr.forEach(v => { c[v] = (c[v] || 0) + 1; });
          const top = Object.keys(c).reduce((a, b) => (c[a] >= c[b] ? a : b));
          return c[top] / Math.max(1, arr.length);
        };
        const flatLabel = (name, sp, arr, unit) => {
          if (sp.span === 0) return name + "（恒定 " + sp.hi + unit + "）";
          if (sp.span < 5) return name + "（几乎恒定 " + sp.hi + unit + "）";
          const share = dominantShare(arr);
          if (share >= 0.9) {
            return name + "（" + Math.round(share * 100) + "% 回合为 " + sp.hi + unit + "）";
          }
          return name;
        };
        const pctAxis = () => {
          const lo = Math.min(hpSpan.lo, mpSpan.lo);
          const hi = Math.max(hpSpan.hi, mpSpan.hi);
          if (hi - lo > 60) return { min: 0, max: 100 };
          const pad = Math.max(4, Math.round((hi - lo) * 0.25));
          return { min: Math.max(0, lo - pad), max: Math.min(100, hi + pad) };
        };
        const opt = Object.assign(chartBase(pal, 58), {
          xAxis: Object.assign(chartBase(pal).xAxis, { data: ticks }),
          yAxis: [
            Object.assign(chartBase(pal).yAxis, Object.assign(
              { name: "%", nameTextStyle: { color: pal.text } }, pctAxis())),
            { type: "value", splitLine: { show: false }, axisLabel: { color: pal.text },
              name: "钱财", nameTextStyle: { color: pal.text, fontSize: 10 } },
          ].concat(codexGrows ? [
            { type: "value", splitLine: { show: false }, show: false, name: "图鉴" },
          ] : []),
          series: [
            { name: flatLabel("气血%", hpSpan, hpPct, "%"), type: "line", smooth: true, showSymbol: false, data: hpPct,
              lineStyle: { color: pal.hp, width: 2 }, itemStyle: { color: pal.hp },
              areaStyle: { color: pal.hp, opacity: .10 } },
            { name: flatLabel("内力%", mpSpan, mpPct, "%"), type: "line", smooth: true, showSymbol: false, data: mpPct,
              lineStyle: { color: pal.mp, width: 2 }, itemStyle: { color: pal.mp } },
            { name: "钱财", type: "line", smooth: true, showSymbol: false, yAxisIndex: 1, data: gold,
              lineStyle: { color: pal.line, width: 2, type: "dashed" }, itemStyle: { color: pal.line } },
          ].concat(codexGrows ? [
            { name: "图鉴累计", type: "line", smooth: true, showSymbol: false, yAxisIndex: 2, data: codex,
              lineStyle: { color: pal.bar, width: 1.8, type: "dotted" }, itemStyle: { color: pal.bar } },
          ] : []),
        });
        c1.setOption(opt, { notMerge: true });
      }
    }

    // 图二：业债与心境
    let c2 = ensureChart("c2", "chart2", "chart2-empty");
    if (c2) {
      $("chart2-empty").hidden = enough;
      c2.getDom && (c2.getDom().style.display = enough ? "" : "none");
      if (enough) {
        const karma = samples.map((s) => s.karma);
        const aff = samples.map((s) => s.affinity_avg);
        const opt = Object.assign(chartBase(pal), {
          xAxis: Object.assign(chartBase(pal).xAxis, { data: ticks }),
          series: [
            { name: "未清业债", type: "bar", data: karma, itemStyle: { color: pal.bar, opacity: .8 },
              barMaxWidth: 10 },
            { name: "人情均值", type: "line", smooth: true, showSymbol: false, data: aff,
              lineStyle: { color: pal.line, width: 2 }, itemStyle: { color: pal.line } },
          ],
        });
        c2.setOption(opt, { notMerge: true });
      }
    }

    // 图三：市价偏离（1.0 基准参考线）
    let c3 = ensureChart("c3", "chart3", "chart3-empty");
    if (c3) {
      $("chart3-empty").hidden = enough;
      c3.getDom && (c3.getDom().style.display = enough ? "" : "none");
      if (enough) {
        const idx = samples.map((s) => s.price_index);
        const opt = Object.assign(chartBase(pal, 34), {
          xAxis: Object.assign(chartBase(pal).xAxis, { data: ticks }),
          series: [
            { name: "物价指数", type: "line", smooth: true, showSymbol: false, data: idx,
              lineStyle: { color: pal.line, width: 2 },
              areaStyle: { color: pal.area },
              markLine: { silent: true, symbol: "none",
                lineStyle: { color: pal.text, type: "dashed", opacity: .7 },
                data: [{ yAxis: 1.0, label: { formatter: "基准 1.0", color: pal.text, fontSize: 10,
                                              position: "insideStartTop" } }] } },
          ],
        });
        c3.setOption(opt, { notMerge: true });
      }
    }
  }

  function refreshSeries(vm) {
    const key = vm.tick + ":" + ((vm.events || []).length) + ":" + (vm.player || {}).gold;
    if (key === lastSeriesKey && seriesCache) { renderCharts(vm, seriesCache); return; }
    fetch("/series")
      .then((r) => r.json())
      .then((s) => { seriesCache = s; lastSeriesKey = key; renderCharts(vm, s); })
      .catch(() => { renderCharts(vm, seriesCache || { samples: [] }); });
  }

  /* ── 事件谱：按严重度与类型计数（维度信号 + 文本标签）── */
  function renderSpectrum(vm) {
    const box = $("spectrum");
    if (!box) return;
    const events = vm.events || [];
    const bySev = { danger: 0, warning: 0, success: 0, info: 0 };
    const byType = {};
    events.forEach((e) => {
      if (bySev[e.severity] !== undefined) bySev[e.severity] += 1;
      byType[e.type] = (byType[e.type] || 0) + 1;
    });
    const total = Math.max(1, events.length);
    setText($("spectrum-hint"), "最近 " + events.length + " 条 · " + Object.keys(byType).length + " 类");
    box.textContent = "";
    const sevLabels = { danger: "危急", warning: "警示", success: "顺遂", info: "寻常" };
    Object.keys(bySev).forEach((sev) => {
      const n = bySev[sev];
      const cell = document.createElement("div");
      cell.className = "spec-cell";
      cell.dataset.sev = sev;
      const num = document.createElement("div");
      num.className = "n";
      num.textContent = String(n);
      const lab = document.createElement("div");
      lab.className = "l";
      lab.textContent = sevLabels[sev] + " · " + (n / total * 100).toFixed(0) + "%";
      const bar = document.createElement("div");
      bar.className = "spec-bar";
      const fill = document.createElement("i");
      fill.style.width = (n / total * 100).toFixed(1) + "%";
      bar.appendChild(fill);
      cell.appendChild(num);
      cell.appendChild(lab);
      cell.appendChild(bar);
      box.appendChild(cell);
    });
  }

  /* ── 人物关系网：纯 SVG，中心玩家 + 结缘者环绕 ── */
  function renderRelNet(vm) {
    const box = $("relnet");
    if (!box) return;
    const rels = (vm.relations || []).filter((r) => r.affinity !== 0 || r.respect !== 0);
    box.textContent = "";
    if (!rels.length) {
      const s = document.createElement("div");
      s.className = "relnet-empty";
      s.textContent = "（还没有值得画的关系——去认识几个人）";
      box.appendChild(s);
      return;
    }
    const W = 300, H = 190, cx = W / 2, cy = H / 2, R = 66;
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    rels.slice(0, 8).forEach((r, i) => {
      const ang = (-90 + i * (360 / Math.min(8, rels.length))) * Math.PI / 180;
      const x = cx + R * Math.cos(ang), y = cy + R * Math.sin(ang) * 0.82;
      const line = document.createElementNS(NS, "line");
      line.setAttribute("x1", cx); line.setAttribute("y1", cy);
      line.setAttribute("x2", x); line.setAttribute("y2", y);
      line.setAttribute("class", "edge");
      const good = r.affinity > 0;
      line.setAttribute("stroke", good ? "var(--success)" : "var(--danger)");
      svg.appendChild(line);
      const g = document.createElementNS(NS, "g");
      g.setAttribute("class", "node");
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", x); c.setAttribute("cy", y);
      c.setAttribute("r", String(8 + Math.min(10, Math.abs(r.affinity) / 10)));
      g.appendChild(c);
      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", x); t.setAttribute("y", y + 20);
      t.setAttribute("text-anchor", "middle");
      t.textContent = r.name + " " + (r.affinity > 0 ? "+" : "") + r.affinity;
      g.appendChild(t);
      svg.appendChild(g);
    });
    const meG = document.createElementNS(NS, "g");
    meG.setAttribute("class", "node me");
    const meC = document.createElementNS(NS, "circle");
    meC.setAttribute("cx", cx); meC.setAttribute("cy", cy); meC.setAttribute("r", "15");
    meG.appendChild(meC);
    const meT = document.createElementNS(NS, "text");
    meT.setAttribute("x", cx); meT.setAttribute("y", cy + 4);
    meT.setAttribute("text-anchor", "middle");
    meT.textContent = (vm.player || {}).name || "我";
    meG.appendChild(meT);
    svg.appendChild(meG);
    box.appendChild(svg);
  }

  /* ── 地点图：已探索地点环布，当前所在地高亮 ── */
  function renderMapNet(vm) {
    const box = $("mapnet");
    if (!box) return;
    const locs = ((vm.codex || {}).locations || []).slice(0, 10);
    const here = (vm.player || {}).location || "";
    box.textContent = "";
    setText($("map-hint"), locs.length ? locs.length + " 处" : "");
    setText($("map-legend"), here ? "当前：" + here : "");
    if (!locs.length) {
      const s = document.createElement("div");
      s.className = "relnet-empty";
      s.textContent = "（还没记录任何地点——用 travel 走动会记进图鉴）";
      box.appendChild(s);
      return;
    }
    const W = 300, H = 170, cx = W / 2, cy = H / 2, R = 60;
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    if (locs.length > 1) {
      const ring = document.createElementNS(NS, "polygon");
      ring.setAttribute("class", "link");
      const pts = locs.map((_, i) => {
        const ang = (-90 + i * (360 / locs.length)) * Math.PI / 180;
        return (cx + R * Math.cos(ang)) + "," + (cy + R * Math.sin(ang) * 0.78);
      }).join(" ");
      ring.setAttribute("points", pts);
      svg.appendChild(ring);
    }
    locs.forEach((name, i) => {
      const ang = (-90 + i * (360 / locs.length)) * Math.PI / 180;
      const x = cx + R * Math.cos(ang), y = cy + R * Math.sin(ang) * 0.78;
      const g = document.createElementNS(NS, "g");
      g.setAttribute("class", "loc" + (name === here ? " here" : ""));
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", x); c.setAttribute("cy", y);
      c.setAttribute("r", name === here ? "9" : "6.5");
      g.appendChild(c);
      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", x); t.setAttribute("y", y + (y < cy ? -12 : 18));
      t.setAttribute("text-anchor", "middle");
      t.textContent = name;
      g.appendChild(t);
      svg.appendChild(g);
    });
    box.appendChild(svg);
  }

  /* ── 修行轨：stage / stage_max 进度 ── */
  function renderStageTrack(vm) {
    const box = $("stage-track");
    if (!box) return;
    const p = vm.player || {};
    const stage = p.stage || 0;
    const cap = p.stage_max || 20;
    const shown = Math.min(cap, 20);
    setText($("stage-hint"), stage + " / " + cap + (stage >= cap ? "（已到上限）" : ""));
    box.textContent = "";
    for (let i = 0; i < shown; i++) {
      const d = document.createElement("span");
      d.className = "step" + (i < stage ? " on" : "") + (i === shown - 1 ? " cap" : "");
      d.title = "第 " + (i + 1) + " 阶";
      box.appendChild(d);
    }
    const lbl = document.createElement("span");
    lbl.className = "lbl";
    lbl.textContent = (p.level || "—")
      + (p.mind_scars ? " · 心伤 " + p.mind_scars : "")
      + (p.near_death_count ? " · 濒死 " + p.near_death_count : "");
    box.appendChild(lbl);
  }

  /* ── 危险/机会徽章 ── */
  function renderBadges(vm) {
    const host = $("badges");
    if (!host) return;
    const p = vm.player || {};
    host.textContent = "";
    const add = (cls, text) => {
      const b = document.createElement("span");
      b.className = "badge " + cls;
      b.textContent = text;
      host.appendChild(b);
    };
    const hpRatio = (p.hp_max || 0) > 0 ? p.hp / p.hp_max : 1;
    if (hpRatio < 0.3) add("danger", "气血吃紧");
    else if (hpRatio < 0.55) add("warn", "气血偏低");
    if ((p.karma || 0) >= 150) add("danger", "业债深重 " + p.karma);
    else if ((p.karma || 0) >= 60) add("warn", "业债缠身 " + p.karma);
    const mkt = (vm.market || []).find((m) => m.location === p.location);
    if (mkt && (mkt.items || []).some((it) => it.delta < 0)) add("chance", "本地有折价货");
    if ((vm.player || {}).stage >= ((vm.player || {}).stage_max || 20)) add("warn", "已到修行上限");
  }

  /* 抽屉位于页面底部；展开时把它滚进视口，否则用户点了"图鉴"却看不到内容。
     键盘/读屏用户同理：焦点跟随滚动，不然展开等于没展开。 */
  function wireDrawers() {
    document.querySelectorAll('details.drawer').forEach((d) => {
      d.addEventListener('toggle', () => {
        if (!d.open) return;
        requestAnimationFrame(() => {
          d.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        });
      });
    });
  }

  function render(v) {
    if (!v || typeof v !== "object") return;
    document.body.dataset.skin = (v.skin && v.skin.id) || "neutral";
    if (v.skin && v.skin.accent) {
      document.documentElement.style.setProperty("--accent", v.skin.accent);
      document.documentElement.style.setProperty("--accent-dim", v.skin.accent + "88");
    }
    renderHud(v);
    renderScene(v);
    renderCast(v);
    renderTimeline(v);
    renderDrawers(v);
    renderSpectrum(v);
    renderRelNet(v);
    renderMapNet(v);
    renderStageTrack(v);
    renderBadges(v);
    refreshSeries(v);
  }

  /* ── 反馈层：toast / dialog ───────────────────────── */
  function toast(e) {
    const box = $("toasts");
    if (!box) return;
    const div = document.createElement("div");
    div.className = "toast";
    div.dataset.severity = e.severity;
    div.setAttribute("role", e.severity === "danger" ? "alert" : "status");
    const tt = document.createElement("div");
    tt.className = "tt";
    tt.textContent = "第 " + (e.tick != null ? e.tick : "?") + " 回合 · " + e.icon + " " + e.kind;
    const dd = document.createElement("div");
    dd.textContent = e.desc;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "关闭";
    btn.setAttribute("aria-label", "关闭这条提示");
    const remove = () => div.remove();
    btn.addEventListener("click", remove);
    div.appendChild(tt);
    div.appendChild(dd);
    div.appendChild(btn);
    box.appendChild(div);
    if (e.severity !== "danger") setTimeout(remove, 6200);
  }

  function openDialog(e, trigger) {
    const dlg = $("eventdlg");
    if (!dlg || typeof dlg.showModal !== "function") { toast(e); return; }
    panelState.dialogFor = e;
    panelState.focusReturn = trigger || document.activeElement;
    setText($("dlg-icon"), e.icon || "");
    setText($("dlg-title-text"), e.title || "事件");
    setText($("dlg-meta"), "第 " + (e.tick != null ? e.tick : "?") + " 回合 · " + (e.type || "") + (e.milestone ? " · 大事记" : ""));
    setText($("dlg-desc"), e.desc || "");
    if (dlg.open) return;
    dlg.showModal();
  }

  function closeDialog() {
    const dlg = $("eventdlg");
    if (!dlg || !dlg.open) return;
    dlg.close();
    const back = panelState.focusReturn;
    panelState.focusReturn = null;
    panelState.dialogFor = null;
    if (back && typeof back.focus === "function" && document.contains(back)) {
      back.focus();
    }
  }

  /* 事件 → 反馈等级（severity 由 panel.py 决定，这里只做呈现分派） */
  function dispatchFeedback(newEvents) {
    if (!panelState.primed) return;   // 首屏不弹历史提示
    const highest = newEvents.reduce(
      (acc, e) => (SEV_RANK[e.severity] > SEV_RANK[acc.severity] ? e : acc),
      newEvents[0] || { severity: "info" });
    if (!newEvents.length) return;
    newEvents.forEach((e) => {
      if (e.severity === "info") return;          // info 只进时间线
      if (e.severity === "danger") return;        // danger 合并进弹窗
      toast(e);
    });
    if (SEV_RANK[highest.severity] >= 2) {
      openDialog(highest, null);
    }
    const ul = $("timeline");
    newEvents.forEach((e) => {
      const li = ul && ul.querySelector('[data-event-id="' + CSS.escape(e.id) + '"]');
      if (li) li.classList.add("flash");
    });
  }

  function diffEvents(prev, next) {
    const out = [];
    (next.events || []).forEach((e) => {
      if (!panelState.shownEvents.has(e.id)) out.push(e);
    });
    return out;
  }

  function apply(vm) {
    if (!vm || typeof vm !== "object") return;
    if (vm.error) {                    // 状态不可读：保留上一屏，横幅说明原因
      showNotice(vm.error, vm.hint || "");
      return;
    }
    hideNotice();
    const fresh = diffEvents(panelState.vm, vm);
    panelState.vm = vm;
    render(vm);
    (vm.events || []).forEach((e) => panelState.shownEvents.add(e.id));
    if (panelState.primed) dispatchFeedback(fresh);
    panelState.primed = true;
  }

  /* ── panelData：取数 + SSE + 轮询降级 ─────────────── */
  function setConn(state, text) {
    const el = $("conn");
    if (!el) return;
    el.dataset.state = state;
    setText($("conn-text"), text);
  }

  let lastData = 0;

  function fetchState() {
    return fetch("/state")
      .then((r) => r.json())
      .then((v) => {
        lastData = Date.now();
        if (v && v.error) {
          setConn("stale", "状态不可读");
        } else {
          setConn("live", "实况 · " + (v.updated_at || ""));
        }
        apply(v);
      })
      .catch(() => { setConn("down", "连接失败，重试中…"); });
  }

  function boot() {
    wireDrawers();
    fetchState();

    if (window.EventSource) {
      const es = new EventSource("/events");
      es.addEventListener("state", (ev) => {
        try {
          const v = JSON.parse(ev.data);
          lastData = Date.now();
          if (v && v.error) {
            setConn("stale", "状态不可读");
          } else {
            setConn("live", "实况 · " + (v.updated_at || ""));
          }
          apply(v);
        } catch (err) { /* 单帧解析失败不打断流 */ }
      });
      es.onerror = () => { setConn("stale", "信号不稳，轮询兜底…"); };
    }

    // 轮询兜底：SSE 静默超过 4 秒就自己拉
    setInterval(() => {
      if (Date.now() - lastData > 4000) fetchState();
    }, 2500);
    setInterval(() => {
      if (Date.now() - lastData > 8000) setConn("down", "连接中断，重试中…");
    }, 4000);

    $("jump-latest").addEventListener("click", () => {
      const ul = $("timeline");
      if (ul) ul.scrollTop = 0;
    });

    $("notice-retry").addEventListener("click", () => fetchState());

    const motionBtn = $("motion");
    motionBtn.addEventListener("click", () => {
      panelState.motion = !panelState.motion;
      document.documentElement.style.setProperty("--speed", panelState.motion ? ".22s" : "0s");
      motionBtn.setAttribute("aria-pressed", String(!panelState.motion));
      setText(motionBtn, panelState.motion ? "动效：开" : "动效：关");
      Object.keys(charts).forEach((k) => {
        if (charts[k]) charts[k].setOption({ animation: panelState.motion });
      });
    });

    // 图表随窗口尺寸重排（rAF 节流）
    let resizeQueued = false;
    window.addEventListener("resize", () => {
      if (resizeQueued) return;
      resizeQueued = true;
      window.requestAnimationFrame(() => {
        resizeQueued = false;
        Object.keys(charts).forEach((k) => { if (charts[k]) charts[k].resize(); });
      });
    });

    $("dlg-close").addEventListener("click", closeDialog);
    $("dlg-ok").addEventListener("click", closeDialog);
    $("eventdlg").addEventListener("close", () => {
      // 原生 Esc / cancel 也要归还焦点
      if (panelState.focusReturn && document.contains(panelState.focusReturn)) {
        panelState.focusReturn.focus();
      }
      panelState.focusReturn = null;
      panelState.dialogFor = null;
    });

    /* ── 帮助：入口按钮 + `?` 快捷键（不打扰正在输入的场景，本页无输入框）── */
    const helpBtn = $("help-btn");
    if (helpBtn) {
      helpBtn.addEventListener("click", () => openHelp(helpBtn));
    }
    const helpClose = $("help-close");
    if (helpClose) helpClose.addEventListener("click", () => closeHelp());
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "?" || (ev.key === "/" && ev.shiftKey)) {
        const tag = (ev.target && ev.target.tagName) || "";
        if (tag === "INPUT" || tag === "TEXTAREA") return;
        ev.preventDefault();
        const dlg = $("helpdlg");
        if (dlg && dlg.open) closeHelp(); else openHelp(helpBtn);
      }
    });

    /* ── 首访一次引导：localStorage 记忆；隐私模式下降级为本次会话内记忆 ── */
    const seen = storageGet("ww_guide_seen");
    if (!seen) {
      const g = $("guide");
      if (g) g.hidden = false;
    }
    const gc = $("guide-close");
    if (gc) {
      gc.addEventListener("click", () => {
        const g = $("guide");
        if (g) g.hidden = true;
        storageSet("ww_guide_seen", "1");
      });
    }
  }

  /* ── 帮助弹窗 ─────────────────────────────────────── */
  let helpReturn = null;

  function storageGet(k) {
    try { return window.localStorage.getItem(k); } catch (e) { return panelState["_" + k] || null; }
  }

  function storageSet(k, v) {
    try { window.localStorage.setItem(k, v); } catch (e) { panelState["_" + k] = v; }
  }

  function fillHelp() {
    const v = panelState.vm || {};
    const meta = v.meta || {};
    const skin = v.skin || {};
    setText($("help-state-path"), meta.state_path || "（尚未开局）");
    setText($("help-sidecar-path"), meta.sidecar || "—");
    setText($("help-skin"), (skin.id || "—") + (skin.motif ? "（" + skin.motif + "）" : ""));
  }

  function openHelp(trigger) {
    const dlg = $("helpdlg");
    if (!dlg || typeof dlg.showModal !== "function") return;
    fillHelp();
    helpReturn = trigger || document.activeElement;
    if (!dlg.open) dlg.showModal();
  }

  function closeHelp() {
    const dlg = $("helpdlg");
    if (!dlg || !dlg.open) return;
    dlg.close();
    if (helpReturn && document.contains(helpReturn)) helpReturn.focus();
    helpReturn = null;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
