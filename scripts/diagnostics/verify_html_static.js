// 静态 DOM 校验:用 jsdom 加载 HTML,只检查元素 ID 都在
// 不跑 JS、不依赖 fetch,只验证 HTML 结构正确
// 用 global jsdom
const { JSDOM } = require('/root/.nvm/versions/node/v24.15.0/lib/node_modules/jsdom');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '../../frontend/province_forecast.html'), 'utf-8');
const dom = new JSDOM(html, { runScripts: 'outside-only' });
const doc = dom.window.document;

const requiredIds = [
  'province', 'indicator', 'years', 'runBtn',
  's_latest', 's_latest_year',
  's_forecast', 's_forecast_year',
  's_hist_cagr', 's_fc_cagr',
  's_r2', 's_mape',
  'chart', 'chartMeta',
  'tableHost', 'tableMeta',
  'metaBox', 'result',
];
const missing = requiredIds.filter((id) => !doc.getElementById(id));
console.log('Element IDs present:', requiredIds.length - missing.length, '/', requiredIds.length);
if (missing.length) {
  console.log('MISSING:', missing);
  process.exit(1);
}

// Check 关键视觉元素
const hasEcharts = html.includes('echarts@5.6.0');
const hasApiBase = html.includes('API_BASE') && html.includes('forecast/province/');
const hasFallbackMsg = html.includes('初始化失败');
const hasLegend = html.includes('上界') && html.includes('下界(填充)');
const hasCsp = html.includes("connect-src 'self' http://localhost:8000");
console.log('ECharts 5.6 loaded:', hasEcharts ? 'YES ✓' : 'NO ✗');
console.log('API_BASE wired to /forecast/province/:', hasApiBase ? 'YES ✓' : 'NO ✗');
console.log('Error fallback message:', hasFallbackMsg ? 'YES ✓' : 'NO ✗');
console.log('Legend 4 series (上界/下界/历史/预测):', hasLegend ? 'YES ✓' : 'NO ✗');
console.log('CSP allows localhost:8000:', hasCsp ? 'YES ✓' : 'NO ✗');

// Count <select> options hint (province/indicator selects)
const selects = doc.querySelectorAll('select');
console.log('Select elements:', selects.length, '(expect 2)');
const cards = doc.querySelectorAll('.stat');
console.log('Stat cards (in HTML):', cards.length, '(expect 6)');

console.log('\nSTATIC DOM CHECK PASSED ✓');
console.log('Open in browser: http://localhost:8080/province_forecast.html');
