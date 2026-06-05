// frontend/console/js/chart.js — 6 ECharts chart helper
// 主题继承 console.css 的 design tokens(深墨蓝 + 暖铜)
// 用法: <div id="chart1" class="console-chart"></div>
//       RCA.chart.renderForecastChart("chart1", data)

(function () {
  "use strict";

  // ------------------------------------------------------------------------- //
  // 主题 — 抽自 console.css 的 :root tokens
  // ------------------------------------------------------------------------- //
  const THEME = {
    ink: "#0E1F3F",
    ink_700: "#1E3A5F",
    copper: "#D08560",
    copper_300: "#E8BFA6",
    copper_600: "#B8714A",
    stone_700: "#5C5A52",
    sand_200: "#E6DFD2",
    paper_50: "#FAF8F3",
    success: "#2D7A4F",
    warning: "#B8941F",
    danger:  "#B73E3E",
  };

  // 共享 axis / tooltip / grid 配置
  const AXIS = {
    axisLine: { lineStyle: { color: THEME.stone_700 } },
    axisLabel: { color: THEME.stone_700, fontFamily: "JetBrains Mono" },
    splitLine: { lineStyle: { color: THEME.sand_200, type: "dashed" } },
  };

  const TOOLTIP = {
    trigger: "axis",
    backgroundColor: THEME.ink,
    borderColor: THEME.ink,
    textStyle: { color: THEME.paper_50, fontFamily: "JetBrains Mono", fontSize: 12 },
  };

  /**
   * 通用 init / dispose
   */
  function _init(divOrId) {
    const dom = typeof divOrId === "string" ? document.getElementById(divOrId) : divOrId;
    if (!dom) throw new Error("chart div not found: " + divOrId);
    if (dom._echart) dom._echart.dispose();
    const echart = echarts.init(dom, null, { renderer: "canvas" });
    dom._echart = echart;
    window.addEventListener("resize", () => echart.resize());
    return echart;
  }

  // ------------------------------------------------------------------------- //
  // 1. Forecast chart — 折线 + CI 区间带
  // ------------------------------------------------------------------------- //
  function renderForecastChart(divOrId, ensemble) {
    const echart = _init(divOrId);
    const years = (ensemble.predictions || []).map((_, i) => 2024 + i);
    const ci_lower = ensemble.ci_lower || [];
    const ci_upper = ensemble.ci_upper || [];
    echart.setOption({
      tooltip: { ...TOOLTIP, formatter: function (params) {
        let s = params[0].name + "<br/>";
        for (const p of params) {
          s += p.marker + " " + p.seriesName + ": <b>" + (p.value?.[1] ?? p.value).toLocaleString() + "</b><br/>";
        }
        return s;
      }},
      legend: { data: ["预测", "95% CI 上", "95% CI 下"], textStyle: { color: THEME.ink } },
      grid: { left: 60, right: 20, top: 40, bottom: 50 },
      xAxis: { type: "category", data: years, ...AXIS },
      yAxis: { type: "value", ...AXIS },
      series: [
        {
          name: "95% CI 上", type: "line", data: ci_upper,
          lineStyle: { opacity: 0 }, stack: "ci", symbol: "none",
          areaStyle: { color: THEME.copper_300, opacity: 0.4 },
        },
        {
          name: "95% CI 下", type: "line", data: ci_lower,
          lineStyle: { opacity: 0 }, stack: "ci", symbol: "none",
        },
        {
          name: "预测", type: "line", data: ensemble.predictions,
          lineStyle: { color: THEME.ink, width: 2.5 },
          itemStyle: { color: THEME.ink },
          symbol: "circle", symbolSize: 8,
          areaStyle: { color: THEME.copper, opacity: 0.15, origin: "start" },
          z: 10,
        },
      ],
    });
  }

  // ------------------------------------------------------------------------- //
  // 2. Backtest chart — 实际 vs 预测双线
  // ------------------------------------------------------------------------- //
  function renderBacktestChart(divOrId, actual, predicted) {
    const echart = _init(divOrId);
    const labels = (actual || []).map((_, i) => "t" + i);
    echart.setOption({
      tooltip: TOOLTIP,
      legend: { data: ["实际", "预测"], textStyle: { color: THEME.ink } },
      grid: { left: 60, right: 20, top: 40, bottom: 50 },
      xAxis: { type: "category", data: labels, ...AXIS },
      yAxis: { type: "value", ...AXIS },
      series: [
        { name: "实际", type: "line", data: actual, lineStyle: { color: THEME.ink, width: 2 }, itemStyle: { color: THEME.ink } },
        { name: "预测", type: "line", data: predicted, lineStyle: { color: THEME.copper, width: 2, type: "dashed" }, itemStyle: { color: THEME.copper } },
      ],
    });
  }

  // ------------------------------------------------------------------------- //
  // 3. Risk chart — VaR / CVaR bar + GARCH 条件波动率 line
  // ------------------------------------------------------------------------- //
  function renderRiskChart(divOrId, data) {
    const echart = _init(divOrId);
    const var95 = data.var_95 || {};
    const var99 = data.var_99 || {};
    const cvar95 = data.cvar_95 || {};
    const cvar99 = data.cvar_99 || {};
    echart.setOption({
      tooltip: TOOLTIP,
      legend: { data: ["百分比损失"], textStyle: { color: THEME.ink } },
      grid: { left: 60, right: 20, top: 40, bottom: 50 },
      xAxis: { type: "category", data: ["VaR 95%", "VaR 99%", "CVaR 95%", "CVaR 99%"], ...AXIS },
      yAxis: { type: "value", name: "%", ...AXIS },
      series: [{
        name: "百分比损失", type: "bar", data: [
          var95.var_pct ?? 0, var99.var_pct ?? 0,
          cvar95.cvar_pct ?? 0, cvar99.cvar_pct ?? 0,
        ],
        itemStyle: { color: function (p) {
          return [THEME.copper_300, THEME.copper, THEME.copper_600, THEME.ink][p.dataIndex];
        }},
        label: { show: true, position: "top", formatter: "{c}%" },
      }],
    });
  }

  // ------------------------------------------------------------------------- //
  // 4. Scenarios chart — 4 档情景折线对比
  // ------------------------------------------------------------------------- //
  function renderScenariosChart(divOrId, scenarios) {
    const echart = _init(divOrId);
    const series = [];
    const palette = [THEME.ink, THEME.copper, THEME.copper_600, THEME.stone_700];
    let n_years = 0;
    let i = 0;
    for (const [name, payload] of Object.entries(scenarios || {})) {
      const series_data = payload.series || payload.predictions || [];
      n_years = Math.max(n_years, series_data.length);
      series.push({
        name: name,
        type: "line",
        data: series_data,
        lineStyle: { color: palette[i % palette.length], width: 2 },
        itemStyle: { color: palette[i % palette.length] },
      });
      i++;
    }
    const years = Array.from({ length: n_years }, (_, j) => 2024 + j);
    echart.setOption({
      tooltip: TOOLTIP,
      legend: { data: series.map(s => s.name), textStyle: { color: THEME.ink } },
      grid: { left: 60, right: 20, top: 40, bottom: 50 },
      xAxis: { type: "category", data: years, ...AXIS },
      yAxis: { type: "value", ...AXIS },
      series,
    });
  }

  // ------------------------------------------------------------------------- //
  // 5. Monte Carlo chart — P5/P50/P95 扇形带
  // ------------------------------------------------------------------------- //
  function renderMonteCarloChart(divOrId, data) {
    const echart = _init(divOrId);
    const p5 = data.percentiles?.p5 || [];
    const p50 = data.percentiles?.p50 || [];
    const p95 = data.percentiles?.p95 || [];
    const n_years = p5.length;
    const years = Array.from({ length: n_years }, (_, j) => 2024 + j);
    echart.setOption({
      tooltip: TOOLTIP,
      legend: { data: ["P5", "P50 (中位)", "P95"], textStyle: { color: THEME.ink } },
      grid: { left: 60, right: 20, top: 40, bottom: 50 },
      xAxis: { type: "category", data: years, ...AXIS },
      yAxis: { type: "value", ...AXIS },
      series: [
        { name: "P95", type: "line", data: p95, lineStyle: { color: THEME.copper_600, width: 1, type: "dashed" }, itemStyle: { color: THEME.copper_600 }, symbol: "none" },
        { name: "P5",  type: "line", data: p5,  lineStyle: { color: THEME.copper_600, width: 1, type: "dashed" }, itemStyle: { color: THEME.copper_600 }, symbol: "none",
          areaStyle: { color: THEME.copper_300, opacity: 0.4 } },
        { name: "P50 (中位)", type: "line", data: p50, lineStyle: { color: THEME.ink, width: 2.5 }, itemStyle: { color: THEME.ink }, symbol: "circle", symbolSize: 7 },
      ],
    });
  }

  // ------------------------------------------------------------------------- //
  // 6. Diagnostics chart — 5 指标 bar
  // ------------------------------------------------------------------------- //
  function renderDiagnosticsChart(divOrId, diag) {
    const echart = _init(divOrId);
    const tests = diag.tests || [];
    const labels = tests.map(t => t.name);
    const pvalues = tests.map(t => t.pvalue ?? t.statistic ?? 0);
    echart.setOption({
      tooltip: TOOLTIP,
      grid: { left: 100, right: 30, top: 30, bottom: 30 },
      xAxis: { type: "value", name: "p-value / statistic", ...AXIS },
      yAxis: { type: "category", data: labels, ...AXIS },
      series: [{
        type: "bar",
        data: pvalues,
        itemStyle: { color: function (p) {
          // 红色表示有问题
          return p.value < 0.05 ? THEME.copper : THEME.ink_700;
        }},
        label: { show: true, position: "right", formatter: "{c}" },
      }],
    });
  }

  // ------------------------------------------------------------------------- //
  // 7. Sparkline(macro data 用)— 小巧折线
  // ------------------------------------------------------------------------- //
  function renderSparkline(divOrId, data) {
    const echart = _init(divOrId);
    echart.setOption({
      tooltip: { show: false },
      grid: { left: 0, right: 0, top: 5, bottom: 5 },
      xAxis: { type: "category", show: false, data: data.map((_, i) => i) },
      yAxis: { type: "value", show: false, scale: true },
      series: [{
        type: "line", data: data, smooth: true,
        lineStyle: { color: THEME.copper, width: 2 },
        itemStyle: { color: THEME.copper },
        symbol: "none", areaStyle: { color: THEME.copper_300, opacity: 0.5 },
      }],
    });
  }

  window.RCA = window.RCA || {};
  window.RCA.chart = {
    renderForecastChart,
    renderBacktestChart,
    renderRiskChart,
    renderScenariosChart,
    renderMonteCarloChart,
    renderDiagnosticsChart,
    renderSparkline,
  };
})();
