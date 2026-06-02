# GitHub Repository Metadata / GitHub 仓库元数据

> GitHub's "About" section (description + topics + website + social preview) can only be edited through the GitHub web UI, not from files in the repository. Copy-paste the values below into the **Settings → General → "About"** panel of your GitHub repository.
>
> GitHub 的"About"区域（描述、主题、网站、社交预览）只能通过 GitHub Web UI 编辑，无法由仓库内的文件直接控制。请把下面的值复制到 **Settings → General → "About"** 面板中。

---

## Repository name (建议)

**`regional-economic-analysis`**

(原 `national-stats` 太泛，与实际场景不一致。)

---

## Description / 描述

> _A production-grade analytics platform for regional economic comparison, retail site selection, sales forecasting and government industry-policy evaluation — covering 10 Chinese cities with 4 analysis scenarios, REST API and zero-build web UI._

长度: **180 字符以内** (GitHub 限制 ≤ 350，最佳 ≤ 180)

### 备选 (更短的版本)

> _Production-grade FastAPI platform for multi-city economic analysis: enterprise site selection, retail location, sales forecasting and government policy evaluation. 10 cities · 70+ API endpoints · zero-build UI._

### 备选 (中文版)

> _生产级多场景产业经济分析平台：城市对比 / 企业选址 / 销售预测 / 政府产业政策评估。FastAPI + ECharts，零构建前端，10 个中国主要城市，70+ REST API。_

---

## Topics / 主题 (推荐 15 个以内)

在 GitHub 仓库主页点击 "⚙️" 旁的齿轮，添加以下标签（按重要性排序）：

| # | Topic | 含义 |
|---|-------|------|
| 1 | `regional-economy` | 区域经济（核心定位） |
| 2 | `economic-analysis` | 经济分析 |
| 3 | `city-comparison` | 城市对比 |
| 4 | `industry-analysis` | 产业分析 |
| 5 | `retail-location` | 零售选址（核心场景） |
| 6 | `sales-forecast` | 销售预测（核心场景） |
| 7 | `site-selection` | 选址分析 |
| 8 | `policy-evaluation` | 政策评估（政府端） |
| 9 | `time-series-forecasting` | 时序预测 |
| 10 | `data-visualization` | 数据可视化 |
| 11 | `fastapi` | 技术栈 |
| 12 | `echarts` | 前端图表 |
| 13 | `data-science` | 学科领域 |
| 14 | `machine-learning` | 学科领域 |
| 15 | `python` | 编程语言 |

---

## Website URL / 网站

设置为：<https://github.com/your-org/regional-economic-analysis>

（如果没有自定义域名，可以指向仓库主页本身，或留空。）

---

## Releases / Releases 标签

发布 v4.0.0 时建议附带:

```markdown
## What's New in v4.0.0

### Highlights
- 🏙️ 10-city economic dataset (Beijing, Shanghai, Shenzhen, Guangzhou, Hangzhou, Suzhou, Nanjing, Wuhan, Chengdu, Xi'an)
- 📊 4 analysis scenarios: enterprise site selection, retail location, sales forecast, government policy
- 🚀 70+ REST API endpoints with auto-generated OpenAPI docs
- 🎨 Zero-build web UI (HTML + Tailwind CDN + ECharts CDN)
- 🐳 Production-ready Docker / Docker Compose deployment
- 🧪 159 backend tests passing, full-stack E2E diagnostic suite

### Stack
FastAPI · Pydantic v2 · pandas · scikit-learn · statsmodels · ECharts · Tailwind CSS · pytest · Playwright
```

---

## Social Preview Image / 社交预览图

GitHub 仓库 → **Settings → General → Social preview**：

- 推荐尺寸: **1280 × 640 px**
- 格式: PNG 或 JPG，< 1 MB
- 内容建议: 项目 Logo + 一句话定位 + 关键特性图标

参考开源项目示例:
- <https://github.com/tiangolo/fastapi> (FastAPI 官方)
- <https://github.com/streamlit/streamlit>

---

## Pinned Issues / 置顶 Issue

发布后建议置顶 2-3 个 Issue 来引导社区：

1. **Welcome / 欢迎** - 项目介绍 + 如何贡献
2. **Roadmap / 路线图** - 未来 3-6 个月计划
3. **Help Wanted / 寻求帮助** - 列出 good first issue

模板可在 GitHub 上创建后置顶。

---

## GitHub Pages / 项目主页 (可选)

如果启用 GitHub Pages，可以把 `frontend/index.html` 作为静态页面发布：

- **Source**: `Deploy from a branch`
- **Branch**: `main` / `docs` 或 `frontend/`
- **Path**: `/frontend`

---

## PyPI 发布 (可选)

如需发布到 PyPI：

1. 注册账号: <https://pypi.org/account/register/>
2. 配置 `~/.pypirc`
3. 构建包：
   ```bash
   python -m pip install --upgrade build twine
   python -m build
   ```
4. 上传：
   ```bash
   python -m twine upload dist/*
   ```
5. 安装验证：
   ```bash
   pip install regional-economic-analysis
   rea-api
   ```

发布到 PyPI 后，描述和标签会从 [pyproject.toml](../pyproject.toml) 和 [setup.py](../setup.py) 自动同步。

---

## 快速复制清单

- [ ] 仓库名: `regional-economic-analysis`
- [ ] 描述: `Production-grade analytics platform for regional economic comparison, retail site selection, sales forecasting and government industry-policy evaluation — 10 cities, 70+ APIs, zero-build UI.`
- [ ] 主题: `regional-economy` `economic-analysis` `city-comparison` `industry-analysis` `retail-location` `sales-forecast` `site-selection` `policy-evaluation` `time-series-forecasting` `data-visualization` `fastapi` `echarts` `data-science` `machine-learning` `python`
- [ ] Website: `https://github.com/your-org/regional-economic-analysis`
- [ ] Releases: v4.0.0
- [ ] Social preview 图: 1280×640 PNG
- [ ] PyPI 发布 (可选)

---

**最后更新**: 2026-06-02
**适用版本**: v4.0.0+
