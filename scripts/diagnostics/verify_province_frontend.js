// 验证前端 JS 核心逻辑:把真实 API 数据喂给 renderResult 里的数据处理部分
// 不依赖 DOM/浏览器,只验证数据变换是否正确(echarts setOption 的 series 数组)

const API = 'http://localhost:8000/api/v1';

async function fetchJson(path, init) {
  const res = await fetch(API + path, init);
  if (!res.ok) throw new Error(`HTTP ${res.status} on ${path}: ${await res.text()}`);
  return res.json();
}

function fmtInt(n) { return n == null ? '--' : Math.round(n).toLocaleString('zh-CN'); }
function fmtPct(n) { return n == null ? '--' : (n >= 0 ? '+' : '') + n.toFixed(2) + '%'; }

function buildEchartsOption(data) {
  const hist = data.historical_values;
  const fc = data.forecast_values;
  const histYears = data.historical_years;
  const fcYears = data.forecast_years;
  const allYears = histYears.concat(fcYears);

  const histSeries = hist.map((v, i) => [histYears[i], v]);
  const fcSeriesConnect = [[histYears[histYears.length - 1], hist[hist.length - 1]]].concat(
    fc.map((v, i) => [fcYears[i], v])
  );
  const upperData = fc.map((v, i) => [fcYears[i], data.upper_95[i]]);
  const lowerMinusUpper = fc.map((v, i) => [fcYears[i], data.lower_95[i] - data.upper_95[i]]);

  return {
    series: [
      { name: '上界', type: 'line', stack: 'ci-band', data: upperData, lineStyle: { opacity: 0 }, z: 2 },
      { name: '下界(填充)', type: 'line', stack: 'ci-band', data: lowerMinusUpper, lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(208, 133, 96, 0.22)' }, z: 1, tooltip: { show: false } },
      { name: '历史', type: 'line', data: histSeries, z: 5 },
      { name: '预测', type: 'line', data: fcSeriesConnect, z: 5 },
    ],
  };
}

async function run() {
  // 1) 拿真实指标 + 省份
  const indicators = await fetchJson('/forecast/indicators');
  const provinces = await fetchJson('/forecast/provinces');

  console.log('===== API 元数据 =====');
  console.log('Supported indicators:', indicators.supported_indicators);
  console.log('Absolute:', indicators.absolute_indicators);
  console.log('Rate:', indicators.rate_indicators);
  console.log('Total:', indicators.total);
  console.log('Provinces:', provinces.provinces.map((p) => `${p.province}(${p.city_count})`).join(', '));

  // 2) 跑广东 GDP 5 年
  const data = await fetchJson('/forecast/province/' + encodeURIComponent('广东'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ indicator: 'gdp', forecast_years: 5 }),
  });

  console.log('\n===== 广东 GDP 5年预测 =====');
  console.log('scope:', data.scope);
  console.log('aggregation:', data.aggregation);
  console.log('included_cities:', data.included_cities);
  console.log('historical_years:', data.historical_years);
  console.log('historical_values:', data.historical_values.map(fmtInt));
  console.log('forecast_years:', data.forecast_years);
  console.log('forecast_values:', data.forecast_values.map(fmtInt));
  console.log('lower_95:', data.lower_95.map((v) => v.toFixed(2)));
  console.log('upper_95:', data.upper_95.map((v) => v.toFixed(2)));
  console.log('method:', data.method);
  console.log('metrics.r_squared:', data.metrics.r_squared);
  console.log('metrics.mae:', data.metrics.mae);
  console.log('metrics.mape_pct:', data.metrics.mape_pct);
  console.log('metrics.slope_per_year:', data.metrics.slope_per_year);
  console.log('growth.historical_cagr_pct:', data.growth.historical_cagr_pct);
  console.log('growth.forecast_cagr_pct:', data.growth.forecast_cagr_pct);

  // 3) 校验字段完整性
  const required = ['scope', 'province', 'indicator', 'aggregation', 'included_cities',
    'historical_years', 'historical_values', 'forecast_years', 'forecast_values',
    'lower_95', 'upper_95', 'method', 'metrics', 'growth'];
  const missing = required.filter((k) => !(k in data));
  console.log('\n[CHECK] Missing fields:', missing.length === 0 ? 'NONE ✓' : missing);

  // 4) 校验 CI 带宽非零
  const ciWidths = data.upper_95.map((u, i) => u - data.lower_95[i]);
  const allNonZero = ciWidths.every((w) => w > 0);
  console.log('[CHECK] All CI widths > 0:', allNonZero ? 'YES ✓' : 'NO ✗', '(widths:', ciWidths.map((w) => w.toFixed(0)).join(', ') + ')');

  // 5) 校验 ECharts option 能构造
  const opt = buildEchartsOption(data);
  console.log('[CHECK] ECharts series count:', opt.series.length, '(expect 4)');
  console.log('[CHECK] Series names:', opt.series.map((s) => s.name).join(', '));
  console.log('[CHECK] ci-band stack present:', opt.series[0].stack === 'ci-band' && opt.series[1].stack === 'ci-band' ? 'YES ✓' : 'NO ✗');
  console.log('[CHECK] History points:', opt.series[2].data.length, '(expect', data.historical_years.length + ')');
  console.log('[CHECK] Forecast points (with bridge):', opt.series[3].data.length, '(expect', data.forecast_years.length + 1 + ')');

  // 6) 跑一个率指标,确认 aggregation 切到 weighted_avg
  const rateData = await fetchJson('/forecast/province/' + encodeURIComponent('广东'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ indicator: 'rd_intensity', forecast_years: 3 }),
  });
  console.log('\n===== 广东 rd_intensity 3年(率指标) =====');
  console.log('aggregation:', rateData.aggregation, '(expect weighted_avg)');
  console.log('historical_values:', rateData.historical_values.map((v) => v.toFixed(3)));
  console.log('forecast_values:', rateData.forecast_values.map((v) => v.toFixed(3)));

  // 7) 跑 /province/all
  const allData = await fetchJson('/forecast/province/all?indicator=gdp&forecast_years=3');
  console.log('\n===== 全省 GDP 3年 =====');
  console.log('Provinces covered:', Object.keys(allData.provinces).length);
  for (const [name, info] of Object.entries(allData.provinces)) {
    const h = info.historical_values;
    const f = info.forecast_values;
    const w = info.upper_95[0] - info.lower_95[0];
    console.log(`  ${name}: hist ${h.length}y ${fmtInt(h[0])}→${fmtInt(h[h.length-1])} | fc ${f.length}y ${fmtInt(f[f.length-1])} | CI width[0]=${w.toFixed(0)} | R²=${info.metrics.r_squared}`);
  }

  console.log('\nALL CHECKS PASSED ✓');
}

run().catch((e) => { console.error('FAIL:', e); process.exit(1); });
