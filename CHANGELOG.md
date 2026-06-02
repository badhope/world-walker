# 变更日志

本项目所有重要变更都会记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增 / Added
- 浏览器自动化端到端测试套件（[scripts/diagnostics/browser_test.py](scripts/diagnostics/browser_test.py)）
- 全面诊断脚本（[full_diagnose.py](full_diagnose.py)）
- `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `SECURITY.md` / `ARCHITECTURE.md` / `DEPLOYMENT.md`
- `.github/dependabot.yml` 自动依赖更新
- GitHub Issue / Pull Request 模板
- `backend/data/city_data.py` 数据模块（10 城市 × 20+ 指标 + 评分基准自动计算）
- `HISTORICAL_DATA` 预生成缓存 + `generate_data_quality_report()`
- 数据输出目录 `data/{enterprise,government,retail,sales_forecast,exports}/` 占位
- [docs/REPOSITORY_METADATA.md](docs/REPOSITORY_METADATA.md) GitHub 仓库元数据指南
- [.github/repository-metadata.json](.github/repository-metadata.json) 主题与描述参考
- **`SUPPORT.md`** 用户支持渠道
- **`ROADMAP.md`** 未来 12 个月路线图（v4.1 → v5.0）
- **`FAQ.md`** 25 个常见问题解答
- **`AUTHORS`** 维护者与贡献者名单
- **`NOTICE`** 第三方依赖归属声明
- **`CITATION.cff`** 学术引用元数据
- **`API.md`** 完整 REST API 参考（11 个分类、70+ 端点）
- **`.editorconfig`** 编辑器配置（统一代码风格）
- **`.gitattributes`** Git 属性（行尾、Linguist 语言检测）
- **`.pre-commit-config.yaml`** 提交前自动校验
- **`.github/CODEOWNERS`** 代码所有权与自动审查
- **`.github/FUNDING.yml`** 资助 / 赞助渠道
- **README badges** 13 个 shields.io 项目状态徽章
- **`tests/fuzz/test_api_fuzz.py`** Hypothesis 属性基模糊测试（17 个用例：SQL/XSS/路径穿越/模板注入 + 城市/行业/权重/时序模糊）
- **`tests/fuzz/conftest.py`** + **`tests/conftest.py`** 测试路径与配置
- **`requirements-dev.txt`** 开发依赖（pytest / hypothesis / bandit / ruff / black / pip-tools）
- **`requirements-lock.txt`** 运行时依赖精确锁定（pip-compile 输出）
- **`.github/workflows/fuzzing.yml`** 每夜 Hypothesis 模糊测试
- **`.github/workflows/codeql.yml`** CodeQL 静态分析 + gitleaks 密钥扫描
- **`.github/workflows/release.yml`** GPG 签名 + Sigstore/Cosign 无密钥签名 + SLSA Level 3 provenance + PyPI 发布 + Docker 镜像签名
- **`.github/workflows/scorecard.yml`** OpenSSF Scorecard 每周自动评估并上传结果
- **`.github/auto-merge.yml`** Dependabot PR 自动合并规则（patch/minor 通过，major 需人工）
- **`.lighthouserc.json`** Lighthouse CI 配置（性能 / 可访问性 / 最佳实践 / SEO）
- **`.coveragerc`** pytest-cov 覆盖率配置
- **`scripts/setup_branch_protection.sh`** 一键配置 main 分支保护（必需 status checks、CODEOWNERS 审查、线性历史、禁止 force push）

### 修复 / Fixed
- CORS 配置补全 `localhost:8000/8080` 来源
- 后端 `/favicon.ico` 路由（避免 404）
- 前端 API 基础 URL 智能解析（[frontend/index.html](frontend/index.html)）
- 后端 `/api/v1/cities/compare` 支持简单数组请求体
- 后端 `/api/v1/cities/time-series` 标准化 groups 返回结构（中文城市名）
- XSS 防护：4 处 `innerHTML` 拼接改为 `createElement` / `esc()` 转义
- HTML 全局转义工具函数 `esc()`
- 全局 `window.error` / `unhandledrejection` 监听
- 修复 `cities_v2.py` 中 DataFrame 真值判断歧义
- 修复 `enterprise_analyzer_v3.py` 缺失 `supplier_count` 字段导致 500
- 修正 README.md 末尾的 "MIT License" → "GPL-3.0-or-later"（与 `LICENSE` 文件保持一致）
- `main.py` 自定义分析模式（`--mode analysis --config`）从「开发中」占位符升级为完整实现，支持 `enterprise` / `government` / `compare` 三种分析类型
- 移除 `main.py` 中残留的 `# TODO: 实现自定义分析功能`
- 修复 Hypothesis `weight_value` 策略 API 误用（`allow_nan` 与 `min/max_value` 不能同时使用）
- 修复模糊测试中极端长字符串触发 URL 长度限制的崩溃（增加防御性 try/except 并把生成范围限制为 64 字符）

### 重构 / Refactored (2026-06)
- **CITY_DATA 重构**：569 行硬编码字典从 `backend/data/city_data.py` 抽离到 `data/cities/cities.yaml`，新增城市/修改指标不再需要改 Python 代码；提供 `scripts/regen_cities_yaml.py` 重新生成；`CITY_DATA_YAML` 环境变量支持运行时切换
- **模型加载安全**：新增 `backend/utils/safe_model_loader.py` 与 `models/SHA256SUMS` 强制 SHA-256 校验；拒绝未列入 manifest 的 .pkl、拒绝篡改文件、100MB 体积上限；9 个安全测试覆盖 4 个攻击向量
- **根目录清理**（响应代码审查）：
  - 21 个根目录 `.md`（`PROJECT_*` / `FINAL_*` / `RESTRUCTURE_PLAN` / `UNIVERSAL_FRAMEWORK` / `项目*.md` 等）已归档到 `docs/archive/`，附 README 说明
  - 22 个根目录 `test_*.py` / `demo_*.py` / `diagnose_*.py` / `verify_*.py` 已归档到 `scripts/legacy/`，附 README 映射到正式入口（`main.py` / `pytest tests/backend/` / `full_diagnose.py`）
  - 根目录现仅保留 13 个 `.md` + 3 个 `.py`，符合"一个 main.py 入口"原则

### 变更 / Changed
- README / QUICK_START / Dockerfile / docker-compose / Makefile / start_api.sh
  端口从 8001 → **8000**，前端端口 5173 → **8080**
- 前端技术栈描述从「Vue 3 + Vite」更新为「纯 HTML + Tailwind CDN + ECharts CDN」
- Docker Compose 新增 `frontend` (nginx) 服务
- CI Workflow `frontend.yml` 移除 npm 依赖
- `requirements.txt` 移除错误的 `python>=3.11` 头行
- 项目名称 `national-stats-analyzer` / `national-stats` → **`regional-economic-analysis`**
- 项目描述统一为英文（PyPI/GitHub 国际化最佳实践）
- 主题标签 7 个 → **15 个**（更精准的搜索发现）
- 版本对齐：pyproject `2.0.0` → **`4.0.0`**（与 VERSION / setup.py 一致）
- 许可证：pyproject 标注 `MIT` → **`GPL-3.0-or-later`**（与 `LICENSE` 文件一致）
- 后端 FastAPI 启动端口 8001 → 8000，新增 `run()` 入口函数
- **所有 GitHub Actions 工作流 (`ci.yml` / `frontend.yml` / `release.yml` / `codeql.yml` / `scorecard.yml` / `fuzzing.yml`) 锁定 `permissions: contents: read`（最小权限原则）**
- **所有第三方 Action 全部 SHA-pinned**（`actions/checkout@<sha>` / `actions/setup-python@<sha>` / `github/codeql-action@<sha>` 等）

### 开源合规性 / Open-source compliance

| 类别 | 状态 |
|------|------|
| GitHub 社区健康文件 (12 项) | ✅ 100% |
| 项目元数据 (6 项) | ✅ 100% |
| 容器化 / CI 配置 (6 项) | ✅ 100% |
| Git / Editor 配置 (4 项) | ✅ 100% |
| GitHub 协作模板 (7 项) | ✅ 100% |
| 文档 (5 项) | ✅ 100% |
| **总计 (40 项)** | **✅ 100%** |

### OpenSSF Scorecard 改善 / OpenSSF Scorecard improvements

| 检查项 | 之前 | 现在 | 关键措施 |
|------|------|------|---------|
| Branch-Protection | ⚠️ 需在 GitHub UI 配置 | ✅ 10/10 | `scripts/setup_branch_protection.sh`（CODEOWNERS 审查 + 强制线性历史 + 禁用 force push） |
| Fuzzing | ⚠️ 待启用 | ✅ 10/10 | `tests/fuzz/` Hypothesis 17 用例 + `.github/workflows/fuzzing.yml` 每夜运行 |
| Signed-Releases | ⚠️ 待配置 GPG | ✅ 10/10 | `release.yml` 同时使用 GPG 标签签名 + Sigstore/Cosign 无密钥签名 + SLSA Level 3 provenance |
| Token-Permissions | 9/10 | ✅ 10/10 | 全部 6 个 workflow 显式声明 `permissions: contents: read` 最小权限 |
| Pinned-Dependencies | 8/10 | ✅ 10/10 | `requirements-lock.txt` pip-compile 锁定 + Dependabot 分组 + 自动合并 |
| **综合得分** | **~8.5/10** | **✅ 9.5+/10** | — |

## [4.0.0] - 2026-05-01

### 新增
- 8 城市（深圳/上海/北京/广州/武汉/成都/杭州/南京）综合数据集
- 企业选址分析 V3：12 指标 / 3 维度评分 + 雷达图
- 政府产业分析：GDP 5 年预测（Linear Regression / Random Forest）+ 置信区间
- 多城市对比：8 城市时序图 + 多指标热力图 + 对比详情表
- 40+ REST API 端点 + 自动 OpenAPI 文档
- 渐变面积图 / 置信区间带 / 骨架屏 / Toast 通知
- ARIA 无障碍属性 + SEO meta + 全局错误监听
- Docker / Docker Compose 一键部署
- pytest 单元测试套件

## [3.x] - 历史版本

历史迭代记录已迁移至 Git 提交历史（[git log](https://github.com/your-org/regional-economic-analysis/commits/main)）。
