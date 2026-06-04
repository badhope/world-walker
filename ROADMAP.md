# Roadmap / 路线图

This document outlines the high-level direction of the **Regional Industrial Economic Analysis Platform**.

We follow a quarterly release cadence. Dates below are indicative and may shift.

---

## v6.1.0 (Released 2026-06) ✅ Current — Docker investment-grade engine stack

### Headline features
- 🐳 **Docker 投资级引擎栈**:`statsforecast` / `arch` / `pmdarima` 预装
- ⚙️ **`backend/core/engine_stack.py`** — 运行时库探测模块,自动 fallback
- 🚀 `auto_arima_native()` — AutoARIMA 路径(statsforecast > pmdarima > statsmodels)
- 📈 `garch_volatility()` — GARCH(1,1) 条件波动率 + 持续性 + 半衰期
- 📊 所有 investment / risk API 输出加 `"backend"` 字段
- 📚 `docs/METHODOLOGY.md` §10 — Docker 部署与引擎探测
- 🧪 273 后端测试通过(263 + 10 新 engine_stack)

---

## v6.0.0 (Released 2026-06) ✅ Investment-grade forecasting platform

### Headline features
- 📊 **10 城 × 12 指标 × 16 年** 真实公开数据(1920 数据点)
- 🌍 4 宏观协变量(NBSC / PBOC / MOFCOM,2010-2025)
- 🎯 **3 模型集成**(ARIMA + ETS + LR, AIC-weighted)
- 🩺 **5 项残差诊断**(ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan)
- 🧪 **5 项 walk-forward CV**(MAPE / RMSE / MASE / sMAPE / Coverage)
- 📉 **风险分析**:VaR / CVaR / 4 档情景 / 1000-iter Monte Carlo
- 🧬 **结构突变检测**(Chow test)
- 🕵️ **数据血缘**:每条数据带 source URL + confidence + estimated flag
- 🌐 **7 个新投资端点**(`/api/v1/investment/*`)+ **5 个血缘端点**(`/api/v1/lineage/*`)
- 📊 `frontend/investment_grade.html` — 投资决策级 dashboard
- 📚 `docs/METHODOLOGY.md` — 9 章节完整方法学
- 🏆 深圳 GDP 16 年实测:MAPE 0.40% / MASE 0.07 / Coverage 100%

---

## v4.0.0 (Released 2026-06)

### Headline features
- 🏙️ 10-city economic dataset
- 📊 4 analysis scenarios (enterprise / retail / sales / government)
- 🚀 70+ REST API endpoints
- 🎨 Zero-build web UI (HTML + Tailwind CDN + ECharts CDN)
- 🐳 Production-ready Docker deployment
- 🧪 159 backend tests passing
- 📚 Comprehensive documentation (README, ARCHITECTURE, DEPLOYMENT, API, FAQ)
- 🛡️ Security hardening (CORS, XSS, ARIA, secrets)
- 🤖 GitHub Actions CI (lint + test)
- 🐙 Dependabot auto-updates
- 📝 Full open-source compliance (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, etc.)

---

## v4.1.0 (Target: 2026-08) 🔨 In progress

### 🎯 Theme: Data accuracy & data-source integrations

- [ ] **Real-data connectors**: Wind / 同花顺 / NBS / CEIC plug-in interface
- [ ] **Automated data refresh**: cron + GitHub Actions scheduled jobs
- [x] **Data lineage tracking**: track every data point back to its source
      (已交付: `backend/api/routes/data_lineage.py` + `provenance` 字段)
- [ ] **Anomaly detection**: flag outlier values during ingestion
- [ ] **Bilingual data labels**: zh-CN / en-US toggle for all metrics
- [ ] **Per-city data-quality dashboard**
- [ ] **5 new cities**: 苏州工业园 / 重庆 / 长沙 / 青岛 / 宁波

### Performance
- [ ] Response-time SLA dashboards
- [ ] Query-result cache (Redis adapter)

### Documentation
- [ ] Tutorials in `docs/tutorials/`
- [ ] English translation of all `.md` files (currently bilingual)

---

## v4.2.0 (Target: 2026-10) 📋 Planned

### 🎯 Theme: Advanced analytics & ML

- [ ] **Prophet** integration for time-series forecasting
- [ ] **XGBoost / LightGBM** for non-linear scoring
- [ ] **SHAP values** for model interpretability
- [ ] **Clustering analysis**: group cities by similarity
- [ ] **Sensitivity analysis**: how do score changes when weights change?
- [ ] **Scenario simulation**: "What if I open 5 stores in city X?"
- [ ] **Geo-spatial analysis**: Leaflet / Mapbox integration with city coordinates
- [ ] **Custom model upload**: users can upload their own ML model

### Frontend
- [ ] **Interactive map view** of all cities with metrics overlay
- [ ] **Scenario builder** UI (drag-and-drop weights)
- [ ] **Saved scenarios / share via URL**

### Quality
- [ ] Achieve 90 % test coverage
- [ ] Type checking with mypy strict mode
- [ ] OpenSSF Scorecard 8+ score

---

## v4.3.0 (Target: 2026-12) 📋 Planned

### 🎯 Theme: Multi-tenancy & permissions

- [ ] **User accounts**: registration / login / password reset
- [ ] **Roles**: admin / analyst / viewer
- [ ] **Organisations**: multi-tenant workspace
- [ ] **API key management** for external integrations
- [ ] **Audit log**: who did what, when
- [ ] **Per-organisation data isolation**

### Integrations
- [ ] Slack / DingTalk / WeCom notifications
- [ ] Webhook subscriptions
- [ ] Email reports (weekly digest)
- [ ] OpenAPI client SDKs (Python, TS, Java) published to package registries

---

## v5.0.0 (Target: 2027-03) 🔭 Vision

### 🎯 Theme: Real-time & streaming

- [ ] **Streaming analytics**: Apache Kafka / Pulsar input
- [ ] **WebSocket-based real-time dashboards**
- [ ] **Live forecast updates** as new data arrives
- [ ] **Edge deployment**: K3s / lightweight K8s for on-premise
- [ ] **GraphQL API** alongside REST
- [ ] **Mobile app** (iOS / Android via React Native)
- [ ] **Voice / chat interface** (LLM-powered natural-language queries)

### Architecture
- [ ] Migrate to **microservices** (data / analysis / presentation tiers)
- [ ] Event-driven architecture (CQRS + Event Sourcing)
- [ ] Service mesh (Istio / Linkerd)
- [ ] **Multi-region** active-active deployment

---

## Long-term vision (2027+)

- 🌐 **Open data marketplace** — share derived datasets back to the community
- 🏆 **Industry benchmarks** — community-contributed scoring rubrics
- 🤝 **Partner ecosystem** — third-party plugins / themes
- 🎓 **Education edition** — sandboxed environment for students
- 📱 **Mobile-first redesign** of the dashboard

---

## Won't do / 不做的事情

To stay focused, we will **not** add the following to the core product:

- ❌ **Real-time stock trading** (we do forecasting, not execution)
- ❌ **CRM / ERP** features (use a dedicated product for that)
- ❌ **Blockchain / Web3** (out of scope)
- ❌ **End-user marketing automation** (out of scope)

If you need any of these, please build on top of our public API.

---

## Contributing to the roadmap / 参与规划

We welcome community input on the roadmap!

- 💭 **Open a Discussion** in the `roadmap` category
- 🗳️ **Vote on existing proposals** with 👍 / 👎 reactions
- 📝 **Submit a Feature Request** issue (use the `feature_request` template)
- 🤝 **Maintainer nomination** for a topic area you specialise in

Major decisions are made by the **maintainer team** quarterly. Minor decisions
are continuously triaged in GitHub Issues.

---

## Release process / 发布流程

1. **Sprint planning** (week 0)
   - Triage all open issues
   - Pick 5–10 issues for the sprint
2. **Development** (week 1–10)
   - PRs against `main`
   - Daily CI runs
3. **Pre-release testing** (week 11)
   - Tag `vX.Y.Z-rc.1`
   - Community testing
4. **Release** (week 12)
   - Tag `vX.Y.Z`
   - Update CHANGELOG
   - Publish GitHub Release
   - Publish to PyPI (if applicable)
5. **Post-release** (week 13)
   - Hot-fix window for blockers
   - Begin next sprint planning

---

**Last updated**: 2026-06-04
**Current version**: v6.1.0
**Next review**: 2026-08 (v4.1.0 planning)
