# National Stats — 5分钟极速上手指南

## 前提条件

- Python 3.11+
- pip
- 现代浏览器（Chrome / Edge / Firefox / Safari）

> ⚠️ **本项目前端无 npm 依赖**，不需要 Node.js。直接用 `python3 -m http.server` 启动即可。

---

## 方案 A：命令行体验（2 分钟）

只用命令行跑完一个完整的分析流程，适合不想配置前端的人：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行演示 — 将自动生成数据、训练模型、输出报告
python demo_complete.py

# 3. 查看结果
ls data/retail_complete/
# 你会看到：analysis_report.pdf, analysis_report.xlsx,
#           analysis_report.json, analysis_summary.txt,
#           以及多张可视化 PNG 图片
```

---

## 方案 B：Web 体验（5 分钟）

启动完整的 Web 界面，适合想通过浏览器交互式操作的人：

### 第一步：启动后端

```bash
# 终端 1
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

打开 <http://localhost:8000/docs> 验证后端已经启动（你会看到 Swagger API 文档页面）。

### 第二步：启动前端

```bash
# 终端 2（新开一个终端窗口）
cd frontend
python3 -m http.server 8080
```

> 💡 前端是 **纯 HTML + Tailwind CDN + ECharts CDN**，**零 npm / 零 webpack**。

### 第三步：开始使用

打开浏览器访问 **<http://localhost:8080/index.html>**

1. 你会看到系统首页 → 点击导航栏中的「企业选址分析」或「政府产业分析」或「城市数据对比」
2. 选择一个城市（如「深圳」）→ 点击「开始企业选址分析」或「运行产业分析」
3. 系统返回评分和图表 → 尝试切换不同城市或对比 8 个城市

---

## 常见问题

**Q: 端口被占用？**
A: 后端修改 `--port` 参数；前端修改 `python3 -m http.server 8080` 的 8080。

**Q: 前端页面空白？**
A: 确保后端先启动，前端等待几秒再刷新。检查浏览器控制台是否有 CORS 或网络错误。

**Q: CORS 错误？**
A: 在 `.env` 中把前端地址加入 `CORS_ORIGINS`（默认已包含 `localhost:8080, 8000, 5173`）。

**Q: `jose` 相关错误？**
A: 运行 `pip install python-jose[cryptography]`。

**Q: 想了解 API 详情？**
A: 后端启动后访问 <http://localhost:8000/docs> 查看 Swagger 交互式文档。

**Q: 没有 Node.js / npm 怎么办？**
A: 不需要！本项目前端是纯 HTML，直接用 Python 静态服务器即可。

---

## 接下来可以做什么？

- 体验完企业选址/政府分析后，修改 `config/settings.py` 调整评分权重
- 前端页面中切换到「城市数据对比」页面，对比 8 个城市的经济指标
- 运行 `python full_diagnose.py` 检查所有 API 端点是否正常
- 运行 `python screenshots/browser_test.py` 自动截图验证页面
