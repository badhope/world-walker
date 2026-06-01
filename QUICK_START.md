# National Stats — 5分钟极速上手指南

## 前提条件

- Python 3.11+
- pip
- Node.js 18+（仅网页模式需要）

---

## 方案A：命令行体验（2分钟）

只用命令行跑完一个完整的零售分析流程，适合不想配置前端的人：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行演示 — 将自动生成数据、训练模型、输出报告
python demo_complete.py

# 3. 查看结果
ls data/retail_complete/
# 你会看到：analysis_report.pdf, analysis_report.xlsx, 
#           analysis_report.json, analysis_summary.txt,
#           以及多张可视化PNG图片
```

## 方案B：网页体验（5分钟）

启动完整的Web界面，适合想通过浏览器交互式操作的人：

### 第一步：启动后端

```bash
# 终端1
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8001 --host 0.0.0.0
```

打开 http://localhost:8001/docs 验证后端已经启动（你会看到Swagger API文档页面）。

### 第二步：启动前端

```bash
# 终端2（新开一个终端窗口）
cd frontend
npm install
npm run dev
```

### 第三步：开始使用

打开浏览器访问 **http://localhost:5173**

1. 你会看到系统首页 → 点击导航栏中的"企业端"或"政府端"
2. 选择一个城市（如"深圳"）→ 点击"开始分析"
3. 系统返回评分和图表 → 尝试切换不同城市对比结果

---

## 常见问题

**Q: 端口被占用？**
A: 后端修改 `--port` 参数，前端修改 `vite.config.ts` 中的端口配置。

**Q: 前端页面空白？**
A: 确保后端先启动，前端等待几秒再刷新。检查浏览器控制台是否有网络请求错误。

**Q: `jose` 相关错误？**
A: 运行 `pip install python-jose[cryptography]`。

**Q: 想了解API详情？**
A: 后端启动后访问 http://localhost:8001/docs 查看Swagger交互式文档。

---

## 接下来可以做什么？

- 体验完零售选址后，修改 `demo_complete.py` 尝试不同的超参数配置
- 前端页面中切换到"城市对比"页面，对比8个城市的经济指标
- 查看 `config/settings.py` 了解所有可配置的环境变量