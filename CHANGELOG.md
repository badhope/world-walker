# Changelog

All notable changes to this project will be documented in this file.

## [3.0.0] - 2026-04-04

### 重构 (Refactored)

**架构优化**
- 统一配置系统，消除 `core/` 和 `backend/core/` 的混乱
- 建立正确的 Python 包结构
- 精简项目结构，从 50+ 文件精简到 24 个核心文件

**数据采集**
- 删除所有假爬虫代码
- 集成 AKShare 获取真实经济数据
- 支持 GDP、CPI、PPI、M2、PMI 等指标采集

**推演引擎**
- 重写推演引擎，实现 14 个真正的经济学指标推演
- 支持线性推演和蒙特卡洛模拟
- 添加置信区间计算

**经济模型**
- 菲利普斯曲线 (失业率-通胀率关系)
- 奥肯定律 (GDP-失业率关系)
- 柯布-道格拉斯生产函数
- 索洛增长模型

**前端优化**
- 重写 Streamlit 应用
- 修复页面路由问题
- 优化 UI 样式

**部署优化**
- 创建一键启动脚本 `启动.bat`
- 自动管理双进程启动
- 自动打开浏览器

### 修复 (Fixed)

- 修复 `pyyaml` 依赖缺失问题
- 修复 `start.py` 引用不存在的 `web_app_enhanced.py`
- 修复 Streamlit 页面路由错误
- 修复数据库初始化问题
- 修复数据采集保存逻辑

### 移除 (Removed)

- 删除假爬虫代码 (`backend/services/scraper/`)
- 删除重复的 `core/` 目录
- 删除旧的 `config.py`
- 删除无用的测试文件
- 删除 Docker 相关文件
- 删除空的 services 子目录

## [2.1.0] - 2026-03-23

### Added
- 国际化支持 (中英文切换)
- 批量计算 API
- UI/UX 增强

## [2.0.0] - 2026-03-22

### Added
- FastAPI 后端
- Streamlit 前端
- 数据采集基础设施
- 教学模型

## [1.0.0] - 2026-03-20

### Added
- 初始项目结构
