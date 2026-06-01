# National Stats - 前端开发指南

## 技术栈
Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts

## 快速开始
```bash
npm install
npm run dev
```

## 如何与后端交互
- 后端运行在 http://localhost:8001
- API基础路径在 `src/utils/request.ts` 中配置
- 所有API定义集中在 `src/api/index.ts`
- 状态管理在 `src/stores/analysis.ts`

## 页面路由
| 路径 | 页面 | 说明 |
|------|------|------|
| / | Home | 系统概览 |
| /enterprise | Enterprise | 企业端分析 |
| /government | Government | 政府端分析 |
| /map | Map | 产业地图 |
| /data | DataManager | 数据管理 |
| /comparison | CityComparison | 城市对比 |

## 构建
```bash
npm run build    # 输出到 dist/
npx vue-tsc --noEmit  # 类型检查
```