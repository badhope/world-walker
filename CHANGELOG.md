# 变更日志

本项目所有重要变更都会记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增
- 浏览器自动化端到端测试套件（[screenshots/browser_test.py](screenshots/browser_test.py)）
- 全面诊断脚本（[full_diagnose.py](full_diagnose.py)）
- `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `SECURITY.md` / `ARCHITECTURE.md` / `DEPLOYMENT.md`
- `.github/dependabot.yml` 自动依赖更新
- GitHub Issue / Pull Request 模板
- `backend/data/city_data.py` 数据模块（10 城市 × 20+ 指标 + 评分基准自动计算）
- `HISTORICAL_DATA` 预生成缓存 + `generate_data_quality_report()`
- 数据输出目录 `data/{enterprise,government,retail,sales_forecast,exports}/` 占位

### 修复
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

### 变更
- README / QUICK_START / Dockerfile / docker-compose / Makefile / start_api.sh
  端口从 8001 → **8000**，前端端口 5173 → **8080**
- 前端技术栈描述从「Vue 3 + Vite」更新为「纯 HTML + Tailwind CDN + ECharts CDN」
- Docker Compose 新增 `frontend` (nginx) 服务
- CI Workflow `frontend.yml` 移除 npm 依赖
- `requirements.txt` 移除错误的 `python>=3.11` 头行

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

历史迭代记录已迁移至 Git 提交历史（[git log](https://github.com/<owner>/national-stats/commits/main)）。
