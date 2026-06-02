# Roadmap / 路线图

This document outlines the high-level direction of the **Regional Industrial Economic Analysis Platform**.

We follow a quarterly release cadence. Dates below are indicative and may shift.

---

## v4.0.0 (Released 2026-06) ✅ Current

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
- [ ] **Data lineage tracking**: track every data point back to its source
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

**Last updated**: 2026-06-02
**Current version**: v4.0.0
**Next review**: 2026-08 (v4.1.0 planning)
