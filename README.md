# Regional Economic Analysis — 区域产业经济分析平台

> A production-grade, multi-scenario analytics platform for **city comparison, retail site selection, sales forecasting and government industry-policy evaluation**.
>
> 生产级多场景产业经济分析平台：覆盖 **10 个中国主要城市**，支持 **4 个分析场景**，提供 **REST API + 单页 Web 前端（零构建依赖）**。
>
> **Tagline**: _"Where should the next factory be built? Which city will grow fastest next year? Is this retail location worth the rent?"_

---

## 🔥 What can this platform do? / 这个项目能干什么？

| Scenario | Business Question | Audience |
|----------|------------------|----------|
| 🏪 **Retail Site Selection** | Where should the next store open? Predict revenue from foot-traffic, competitors and rent. | Retail chains, expansion teams |
| 📈 **Sales Forecasting** | How much will we sell next quarter? Multi-model forecasting from historical data. | Operations, sales planning |
| 🏢 **Enterprise Business Environment** | Which city has the lowest operating cost and best supply-chain support? | Corporate strategy, site-selection |
| 🏛️ **Government Industry Policy** | How complete is the local industrial chain? How effective is fiscal leverage? | Government planning & development |

| 场景 | 解决什么问题 | 适合谁用 |
|------|-------------|---------|
| 🏪 零售门店选址 | 新店开在哪？基于流量/竞品/租金预测营收 | 连锁零售企业 |
| 📈 销售预测 | 下季度卖多少？基于历史数据+多模型预测 | 运营/销售团队 |
| 🏢 企业营商环境评估 | 哪个城市营商成本低？供应链配套好？ | 企业战略/选址部门 |
| 🏛️ 政府产业政策分析 | 产业链完整度？财政杠杆效率？ | 政府产业/发改部门 |

---

## 🚀 5分钟快速上手

### 方式一：纯Python运行（最简单，不需要前端）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行完整演示（生成数据→训练模型→预测→报告输出）
python demo_complete.py
```

演示完成后，在 `data/retail_complete/` 目录下查看生成的分析报告（PDF/Excel/JSON/TXT）和可视化图表。

### 方式二：启动 Web 界面（前后端完整运行）

**终端 1 — 启动后端 API 服务（端口 8000）**
```bash
# 首次需安装依赖
pip install -r requirements.txt

# 启动 API 服务
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
# API 文档: http://localhost:8000/docs
```

**终端 2 — 启动前端静态服务器（端口 8080）**
```bash
cd frontend
python3 -m http.server 8080
# 访问 http://localhost:8080/index.html
```

> 💡 前端是 **纯 HTML + Tailwind CDN + ECharts CDN**，**零 npm / 零 node_modules**，开箱即用。

### 方式三：Docker 一键启动

```bash
docker-compose up --build
# 访问 http://localhost:8000  (API)
# 访问 http://localhost:8080  (Web UI, 通过 nginx)
```

---

## 🧭 Web 界面使用流程

打开 http://localhost:8080/index.html 后，按以下流程使用：

### 步骤 1：首页概览
页面顶部显示系统概览：4 个统计卡片（覆盖城市/8、API 端点/40+、系统状态/在线、版本号）。
导航栏可切换 4 个 Tab：**总览仪表盘 / 企业选址分析 / 政府产业分析 / 城市数据对比**。

### 步骤 2：企业选址分析
点击「企业选址分析」Tab
1. **选择城市**：从下拉框选择（深圳/上海/北京/广州/武汉/成都/杭州/南京）
2. **点击「开始企业选址分析」**：系统计算 12 个指标 / 3 维度（经营成本 / 供应链 / 政策福利）
3. **查看结果**：
   - 顶部 KPI 圆环：综合得分（如深圳 84.3）
   - 评分维度雷达图
   - 细分指标详情网格

### 步骤 3：政府产业分析
点击「政府产业分析」Tab
1. 选择城市
2. 点击「运行产业分析」
3. 查看 **GDP 历史趋势 + 5 年预测**（含 95% 置信区间）+ 核心经济指标网格

### 步骤 4：城市数据对比
点击「城市数据对比」Tab
1. 多选城市（点击 pill 按钮切换）
2. 点击「对比分析」
3. 查看 **GDP 时序对比图 + 多指标热力图 + 城市对比详情表**

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────┐
│       单页 Web 前端 (8080)                │
│   HTML + Tailwind CSS + ECharts          │
│   零构建依赖，CDN 即开即用                │
└──────────┬───────────────────────────────┘
           │ HTTP/JSON (CORS 已配置)
┌──────────┴───────────────────────────────┐
│       FastAPI 后端 (8000)                │
│  /api/v1/cities/*      城市数据           │
│  /api/v1/analysis/*    分析引擎           │
│  /api/v1/forecast/*    时间序列预测       │
│  /health               健康检查           │
│  /favicon.ico          站点图标           │
│  /docs                 Swagger API 文档  │
└──────────┬───────────────────────────────┘
           │
┌──────────┴───────────────────────────────┐
│          分析引擎层                       │
│  EnterpriseAnalyzer / GovernmentAnalyzer │
│  RetailLocationAnalyzer / SalesAnalyzer  │
│  CityAggregator / Forecaster             │
│  继承 BaseAnalyzer 统一接口              │
└──────────┬───────────────────────────────┘
           │
┌──────────┴───────────────────────────────┐
│          数据层                           │
│  8 城市真实经济数据 / ML 模型 / 报告生成器│
└──────────────────────────────────────────┘
```

### 前后端如何协调？

| 交互方式 | 说明 |
|---------|------|
| **开发模式** | 后端 `uvicorn` (8000) + 前端 `python3 -m http.server` (8080) |
| **生产模式** | Nginx 反向代理 8000（API）+ 8080（静态文件） |
| **CORS** | 后端默认允许 `localhost:8000, 8080, 5173, 127.0.0.1:8000/8080` |
| **数据流** | 前端 → fetch → API 路由 → 分析引擎 → 返回 JSON → ECharts 渲染 |

---

## 📚 More Documentation / 更多文档

| File | Content |
|------|---------|
| [QUICK_START.md](QUICK_START.md) | 5-minute quick start (English & 中文) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flow, key decisions |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment (Systemd / Docker / K8s / Nginx) |
| [API.md](API.md) | Complete REST API reference (auto-generated from OpenAPI) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines & development setup |
| [CHANGELOG.md](CHANGELOG.md) | Release notes & version history |
| [SECURITY.md](SECURITY.md) | Security policy & vulnerability reporting |
| Backend `/docs` | Interactive Swagger API documentation |

| 文件 | 内容 |
|------|------|
| [QUICK_START.md](QUICK_START.md) | 5分钟极速入门指南 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构、数据流、关键决策 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 生产环境部署（Systemd/Docker/K8s/Nginx） |
| [pyproject.toml](pyproject.toml) | 项目元数据、测试配置 |
| 后端 `/docs` | Swagger API 交互式文档 |

---

## 🏷️ Topics / 主题

`regional-economy` · `economic-analysis` · `city-comparison` · `industry-analysis` · `retail-location` · `sales-forecast` · `site-selection` · `policy-evaluation` · `time-series-forecasting` · `data-visualization` · `fastapi` · `echarts` · `data-science` · `machine-learning` · `python`

---

## 🧪 Testing / 测试

```bash
# Backend unit & integration tests
python -m pytest tests/backend/ -v

# Full-stack E2E diagnostics
python full_diagnose.py

# Browser-automation tests (produces screenshots)
python screenshots/browser_test.py
```

---

## 🔒 Security / 安全

```bash
# Copy and customise environment configuration
cp .env.example .env
# Edit .env: change SECRET_KEY and CORS_ORIGINS for production
```

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.
See [LICENSE](LICENSE) for the full text.

本项目基于 **GNU 通用公共许可证 v3.0 或更高版本** 发布，详见 [LICENSE](LICENSE)。