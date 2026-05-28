# 区域产业经济分析平台 - 前端可视化系统

## 项目简介

这是一个基于 Vue 3 + TypeScript + ECharts 的区域产业经济分析可视化平台。提供企业端分析、政府端分析、产业地图、数据管理等功能。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **图表库**: ECharts
- **HTTP 客户端**: Axios

## 目录结构

```
frontend/
├── public/
├── src/
│   ├── api/
│   │   └── index.ts              # API 接口封装
│   ├── components/
│   │   ├── charts/               # 图表组件
│   │   │   └── EChart.vue        # ECharts 通用组件
│   │   ├── layout/               # 布局组件
│   │   │   └── AppLayout.vue     # 应用主布局
│   │   └── widgets/              # 小部件
│   │       └── KpiCard.vue       # KPI 卡片组件
│   ├── router/
│   │   └── index.ts              # 路由配置
│   ├── stores/
│   │   ├── analysis.ts           # 分析数据状态管理
│   │   └── ui.ts                 # UI 状态管理
│   ├── types/
│   │   └── index.ts              # TypeScript 类型定义
│   ├── utils/
│   │   ├── charts.ts             # 图表预设配置
│   │   └── request.ts            # Axios 封装
│   ├── views/
│   │   ├── Home.vue              # 概览页面
│   │   ├── Enterprise.vue        # 企业端分析页面
│   │   ├── Government.vue        # 政府端分析页面
│   │   ├── Map.vue               # 产业地图页面
│   │   └── DataManager.vue       # 数据管理页面
│   ├── App.vue
│   └── main.ts
├── .env.development
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发环境运行

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

## 页面功能说明

### 1. 概览页面 (Home)
- 显示关键指标 KPI 卡片
- 经济指标趋势图
- 产业结构分布图
- 快速操作入口

### 2. 企业端分析 (Enterprise)
- 营商成本分析（土地、人力、能源等）
- 供应链配套分析
- 政策红利分析
- 综合成本指数
- 优化建议

### 3. 政府端分析 (Government)
- 财政杠杆分析
- 产业带动效应
- 产业链完整度分析
- 政策效果评估
- 政策建议

### 4. 产业地图 (Map)
- 区域热力图
- 指标筛选
- 区域对比
- 趋势分析

### 5. 数据管理 (DataManager)
- 数据查询与筛选
- 数据上传
- 数据导出
- 数据编辑

## 环境变量

在 `.env.development` 中配置：

```env
VITE_API_BASE_URL=http://localhost:8001
```

## 后端 API 要求

后端需要提供以下 API：

```
GET    /api/v1/data/basic
GET    /api/v1/data/trend
GET    /api/v1/data/map
POST   /api/v1/analysis/enterprise
POST   /api/v1/analysis/government
POST   /api/v1/analysis/compare
POST   /api/v1/inference/model
```

## 开发建议

1. **组件设计**: 尽可能复用组件，遵循单一职责原则
2. **状态管理**: 使用 Pinia 集中管理状态
3. **类型安全**: 充分利用 TypeScript 类型系统
4. **图表性能**: 大数据量时使用虚拟滚动、懒加载
5. **响应式**: 确保在各种设备上正常显示

## 启动后端

在项目根目录下：

```bash
# 启动 FastAPI 后端
python -m uvicorn backend.api.main:app --reload --port 8001
```

## License

MIT
