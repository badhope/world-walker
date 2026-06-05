// frontend/console/js/form-helpers.js — 城市 / 指标 / 后端 autocomplete
// 依赖 RCA.api 暴露的 listCities()

(function () {
  "use strict";

  /**
   * 拉取并缓存 list_cities 数据(全 session 调一次)
   */
  let _citiesCache = null;
  async function _getCities() {
    if (_citiesCache) return _citiesCache;
    const r = await window.RCA.api.listCities();
    if (!r.ok) {
      console.warn("listCities failed:", r.error);
      return { cities: [], provinces: [], indicators: [] };
    }
    _citiesCache = r.data.data;
    return _citiesCache;
  }

  /**
   * 填充 <input list="cities"> 的 <datalist>
   * 用法: <input list="cities" name="city"> + <datalist id="cities"></datalist>
   *       populateCityDatalist("cities")
   */
  async function populateCityDatalist(datalistId) {
    const data = await _getCities();
    const dl = document.getElementById(datalistId);
    if (!dl) return;
    dl.innerHTML = "";
    const cities = data.cities_pinyin || data.cities || [];
    const provinces = data.provinces || [];
    cities.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      dl.appendChild(opt);
    });
    provinces.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p;
      dl.appendChild(opt);
    });
  }

  /**
   * 填充 <select id="indicator"> 的 options
   * 优先从 list_cities 的 data.indicators 拿,fallback 一个常用列表
   */
  async function populateIndicatorSelect(selectId) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    const data = await _getCities();
    const indicators = data.indicators || ["gdp", "population", "fdi", "cpi", "fixed_asset_investment"];
    sel.innerHTML = "";
    indicators.forEach((i) => {
      const opt = document.createElement("option");
      opt.value = i;
      opt.textContent = i;
      if (i === "gdp") opt.selected = true;
      sel.appendChild(opt);
    });
  }

  /**
   * 填充 <select id="backend"> 的可用后端
   */
  function populateBackendSelect(selectId, available) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = "";
    (available || ["openai", "anthropic", "kimi", "qwen"]).forEach((b) => {
      const opt = document.createElement("option");
      opt.value = b;
      opt.textContent = b;
      sel.appendChild(opt);
    });
  }

  /**
   * 通用:把 <form> 的 FormData 转成普通 dict(去掉空字符串)
   */
  function formToDict(form) {
    const fd = new FormData(form);
    const obj = {};
    for (const [k, v] of fd.entries()) {
      if (v === "" || v === null || v === undefined) continue;
      if (k === "years") obj[k] = Number(v);
      else obj[k] = v;
    }
    return obj;
  }

  /**
   * 渲染 toast
   */
  function toast(msg, kind) {
    const t = document.createElement("div");
    t.className = "console-toast console-toast--" + (kind || "ok");
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
  }

  /**
   * 渲染 error 区块
   */
  function showError(intoEl, msg) {
    if (typeof intoEl === "string") intoEl = document.getElementById(intoEl);
    if (!intoEl) return;
    intoEl.innerHTML = '<div class="console-error">' + escapeHtml(msg) + "</div>";
  }
  function clearError(intoEl) {
    if (typeof intoEl === "string") intoEl = document.getElementById(intoEl);
    if (intoEl) intoEl.innerHTML = "";
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /**
   * 判定 verdict / status → 渲染 console-badge class
   */
  function verdictClass(v) {
    if (typeof v !== "string") return "info";
    const vl = v.toUpperCase();
    if (vl.includes("OK") || vl.includes("PASS") || vl.includes("HEALTHY")) return "ok";
    if (vl.includes("WARN") || vl.includes("DEGRAD")) return "warn";
    if (vl.includes("FAIL") || vl.includes("ERROR") || vl.includes("BAD")) return "err";
    return "info";
  }

  window.RCA = window.RCA || {};
  window.RCA.form = {
    populateCityDatalist, populateIndicatorSelect, populateBackendSelect,
    formToDict, toast, showError, clearError, escapeHtml, verdictClass,
  };
})();
