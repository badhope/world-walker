# National Stats — 国家经济数据分析平台

多场景产业经济智能分析与预测系统。覆盖 **8个中国主要城市**，支持 **4个分析场景**，提供 **REST API + 单页 Web 前端（零构建依赖）**。

---

## 🔥 快速了解：这个项目能干什么？

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

## 📚 更多文档

| 文件 | 内容 |
|------|------|
| [QUICK_START.md](QUICK_START.md) | 5分钟极速入门指南 |
| [pyproject.toml](pyproject.toml) | 项目元数据、测试配置 |
| 后端 `/docs` | Swagger API 交互式文档 |

---

## 🧪 测试

```bash
# API 端到端测试
python full_diagnose.py

# 浏览器自动化测试（生成截图）
python screenshots/browser_test.py
# 截图输出: screenshots/browser_test/*.png
```

---

## 🔒 安全配置

```bash
# 复制并修改环境变量配置
cp .env.example .env
# 编辑 .env 文件，修改 SECRET_KEY 和 CORS_ORIGINS
```

---

MIT License