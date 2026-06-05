// frontend/console/js/sidebar.js — 渲染侧栏 nav
// 用法: <aside class="console-sidebar" id="sidebar"></aside> + <script src="js/sidebar.js"></script>
// 自动用 fetch 把 index.html 的 nav 内容拉过来,避免在 12 个页面重复粘贴 25 行 HTML

(function () {
  "use strict";

  const NAV_HTML = `
    <div class="console-sidebar__brand">
      <h1>
        <span class="console-sidebar__brand-mark">R</span>
        RCA Console
      </h1>
      <div class="console-sidebar__brand-sub">v9.1 · Regional Economic Analysis</div>
    </div>

    <ul class="console-nav">
      <li class="console-nav__item">
        <a href="../index.html"><span class="console-nav__icon">⌂</span> Dashboard</a>
      </li>

      <li class="console-nav__section-title">Tools · 9 项分析工具</li>
      <li class="console-nav__item"><a href="forecast.html"><span class="console-nav__icon">↗</span> Forecast <span style="opacity:.6;font-size:11px;margin-left:auto">预测</span></a></li>
      <li class="console-nav__item"><a href="diagnostics.html"><span class="console-nav__icon">⚙</span> Diagnostics <span style="opacity:.6;font-size:11px;margin-left:auto">诊断</span></a></li>
      <li class="console-nav__item"><a href="backtest.html"><span class="console-nav__icon">⟲</span> Backtest <span style="opacity:.6;font-size:11px;margin-left:auto">回测</span></a></li>
      <li class="console-nav__item"><a href="risk.html"><span class="console-nav__icon">△</span> Risk <span style="opacity:.6;font-size:11px;margin-left:auto">风险</span></a></li>
      <li class="console-nav__item"><a href="scenarios.html"><span class="console-nav__icon">◫</span> Scenarios <span style="opacity:.6;font-size:11px;margin-left:auto">情景</span></a></li>
      <li class="console-nav__item"><a href="monte-carlo.html"><span class="console-nav__icon">✦</span> Monte Carlo <span style="opacity:.6;font-size:11px;margin-left:auto">蒙特卡洛</span></a></li>
      <li class="console-nav__item"><a href="data-provenance.html"><span class="console-nav__icon">⇋</span> Data Provenance <span style="opacity:.6;font-size:11px;margin-left:auto">数据来源</span></a></li>
      <li class="console-nav__item"><a href="macro-data.html"><span class="console-nav__icon">≋</span> Macro Data <span style="opacity:.6;font-size:11px;margin-left:auto">宏观</span></a></li>
      <li class="console-nav__item"><a href="list-cities.html"><span class="console-nav__icon">⋮⋮</span> List Cities <span style="opacity:.6;font-size:11px;margin-left:auto">城市列表</span></a></li>

      <li class="console-nav__section-title">LLM</li>
      <li class="console-nav__item"><a href="../chat.html"><span class="console-nav__icon">✎</span> Chat <span style="opacity:.6;font-size:11px;margin-left:auto">对话</span></a></li>
      <li class="console-nav__item"><a href="../settings.html"><span class="console-nav__icon">✱</span> Settings <span style="opacity:.6;font-size:11px;margin-left:auto">设置</span></a></li>

      <li class="console-nav__section-title">操作</li>
      <li class="console-nav__item"><a href="../history.html"><span class="console-nav__icon">⏱</span> History <span style="opacity:.6;font-size:11px;margin-left:auto">历史</span></a></li>
      <li class="console-nav__item"><a href="/docs" target="_blank"><span class="console-nav__icon">⌘</span> API Docs <span style="opacity:.6;font-size:11px;margin-left:auto">接口</span></a></li>
    </ul>
  `;

  function init() {
    const sb = document.getElementById("sidebar");
    if (!sb) return;
    sb.innerHTML = NAV_HTML;
    // 高亮当前页
    const currentPath = location.pathname.split("/").pop() || "index.html";
    sb.querySelectorAll("a").forEach((a) => {
      const href = a.getAttribute("href");
      if (href && href.endsWith(currentPath)) {
        a.parentElement.classList.add("console-nav__item--active");
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
