# 区域产业经济分析平台 - 可视化开发完整计划

## 一、技术栈选型

### 1.1 前端技术栈

| 技术 | 选型 | 版本要求 | 用途 |
|------|------|----------|------|
| **前端框架** | Vue 3 | ^3.4.0 | 核心框架 |
| **构建工具** | Vite | ^5.0.0 | 快速构建 |
| **状态管理** | Pinia | ^2.1.7 | 全局状态管理 |
| **路由** | Vue Router | ^4.2.5 | 单页路由 |
| **UI 框架** | Element Plus | ^2.5.0 | 组件库 |
| **图表库** | Apache ECharts | ^5.4.3 | 核心可视化 |
| **地图** | Apache ECharts + GeoJSON | - | 地图可视化 |
| **HTTP 客户端** | Axios | ^1.6.0 | API 请求 |
| **工具库** | Lodash | ^4.17.21 | 数据处理 |
| **日期处理** | Day.js | ^1.11.10 | 日期操作 |
| **工具链** | TypeScript | ^5.3.0 | 类型安全 |

### 1.2 后端技术栈（已有）

| 技术 | 版本要求 | 用途 |
|------|----------|------|
| **Web 框架** | FastAPI | ^0.104.0 | REST API |
| **可视化** | Plotly | ^5.18.0 | 后端图表支持 |
| **数据处理** | Pandas, NumPy | - | 数据处理 |

---

## 二、界面布局设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            顶部导航栏 (64px)                             │
│  Logo        主页  │  分析  │  企业端  │  政府端  │  数据管理  │  关于  │
├─────────────────────────────────────────────────────────────────────────┤
│                              主内容区                                   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  左侧边栏   │              主展示区 (可拖拽)                  │ │
│  │             │                                                   │ │
│  │  1. 概览    │  ┌─────────────────────────────────────────┐    │ │
│  │  2. 企业端  │  │      KPI 卡片区域 (自适应网格)          │    │ │
│  │  3. 政府端  │  ├─────────────────────────────────────────┤    │ │
│  │  4. 产业地图│  │      主要图表区域                       │    │ │
│  │  5. 对比分析│  ├─────────────────────────────────────────┤    │ │
│  │  6. 报告导出│  │      详细数据区域                       │    │ │
│  │             │  └─────────────────────────────────────────┘    │ │
│  └─────────────┘                                                   │ │
└─────────────────────────────────────────────────────────────────────┘
│                              页脚 (48px)                                │
│  Copyright © 2026 区域产业经济分析平台                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 页面设计

#### 2.2.1 主页 / 概览页 (`/`)
```
布局：
  ┌─────────────────────────────────────────────────────────────┐
  │  KPI 卡片 (4 个一行，自适应)                               │
  │  [GDP] [增速] [就业] [财政收入]                             │
  ├─────────────────────────────────────────────────────────────┤
  │  双栏布局 (50% - 50%)                                       │
  │  ┌──────────────────┐  ┌──────────────────┐               │
  │  │  主要指标趋势图  │  │  产业结构饼图    │               │
  │  └──────────────────┘  └──────────────────┘               │
  ├─────────────────────────────────────────────────────────────┤
  │  单栏布局 (100%)                                            │
  │  ┌───────────────────────────────────────────────────────┐ │
  │  │  快速操作区 - 一键开始分析                            │ │
  │  │  [企业端分析]  [政府端分析]  [产业对比]                 │ │
  │  └───────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────┘
```

#### 2.2.2 企业端分析页 (`/enterprise`)
```
布局：
  ┌─────────────────────────────────────────────────────────────┐
  │  顶部：区域 & 产业 & 年份选择器                             │
  ├─────────────────────────────────────────────────────────────┤
  │  KPI 卡片 (6 个，2 行)                                      │
  │  [用地成本] [人力成本] [能源成本] [营商指数] [融资便利度]   │
  ├─────────────────────────────────────────────────────────────┤
  │  三栏布局 (33% - 34% - 33%)                                │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
  │  │ 成本对比图表 │  │ 供应链分析图 │  │ 政策红利图  │    │
  │  └──────────────┘  └──────────────┘  └──────────────┘    │
  ├─────────────────────────────────────────────────────────────┤
  │  双栏布局 (60% - 40%)                                       │
  │  ┌─────────────────────┐  ┌────────────────┐              │
  │  │ 综合成本趋势 (面积图)│  │  企业友好度排名 │              │
  │  └─────────────────────┘  └────────────────┘              │
  ├─────────────────────────────────────────────────────────────┤
  │  详细数据分析表                                            │
  └─────────────────────────────────────────────────────────────┘
```

#### 2.2.3 政府端分析页 (`/government`)
```
布局：
  ┌─────────────────────────────────────────────────────────────┐
  │  顶部：区域 & 产业 & 年份选择器                             │
  ├─────────────────────────────────────────────────────────────┤
  │  KPI 卡片 (6 个，2 行)                                      │
  │  [财政投入] [带动效应] [杠杆倍数] [投入产出] [产业链完整度] │
  ├─────────────────────────────────────────────────────────────┤
  │  双栏布局 (50% - 50%)                                       │
  │  ┌──────────────────┐  ┌──────────────────┐               │
  │  │ 财政杠杆分析图  │  │ 产业带动效应图    │               │
  │  └──────────────────┘  └──────────────────┘               │
  ├─────────────────────────────────────────────────────────────┤
  │  三栏布局 (33% - 34% - 33%)                                │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
  │  │ 产业链地图   │  │ 政策效果评分  │  │ 政策建议     │    │
  │  └──────────────┘  └──────────────┘  └──────────────┘    │
  └─────────────────────────────────────────────────────────────┘
```

#### 2.2.4 产业地图页 (`/map`)
```
布局：
  ┌─────────────────────────────────────────────────────────────┐
  │  顶部：指标 & 年份选择器                                    │
  ├─────────────────────────────────────────────────────────────┤
  │  左侧：地图控制面板                                         │
  │  ┌─────────────────┐                                        │
  │  │  指标选择      │                                        │
  │  │  区域选择      │                                        │
  │  │  图例          │                                        │
  │  │  统计数据      │                                        │
  │  └─────────────────┘                                        │
  │                                                             │
  │  右侧：中国地图（可下钻）                                   │
  │  ┌───────────────────────────────────────────────────────┐ │
  │  │                 区域热力图                              │ │
  │  │              (省份点击下钻到城市)                       │ │
  │  └───────────────────────────────────────────────────────┘ │
  │                                                             │
  │  底部：趋势线图                                              │
  └─────────────────────────────────────────────────────────────┘
```

#### 2.2.5 数据管理页 (`/data`)
```
布局：
  ┌─────────────────────────────────────────────────────────────┐
  │  顶部：数据上传、批量导入按钮                               │
  ├─────────────────────────────────────────────────────────────┤
  │  左侧：数据类型筛选、条件过滤                               │
  │  ┌──────────────┐                                          │
  │  │  数据类型    │                                          │
  │  │  区域筛选    │                                          │
  │  │  时间范围    │                                          │
  │  │  指标选择    │                                          │
  │  └──────────────┘                                          │
  │                                                             │
  │  右侧：数据表格                                             │
  │  ┌───────────────────────────────────────────────────────┐ │
  │  │                可编辑的数据表格                          │ │
  │  └───────────────────────────────────────────────────────┘ │
  │                                                             │
  │  底部：分页、导出按钮                                        │
  └─────────────────────────────────────────────────────────────┘
```

---

## 三、响应式设计方案

### 3.1 断点定义

| 断点类型 | 屏幕宽度 | 适配设备 | 布局调整 |
|----------|----------|----------|----------|
| **超大屏 (xl)** | ≥ 1920px | 大屏显示器 | 4 列布局，面板最大宽度 1600px |
| **桌面屏 (lg)** | 1200px - 1919px | 常规桌面 | 3 列布局，面板最大宽度 1200px |
| **平板 (md)** | 768px - 1199px | 平板、小型桌面 | 2 列布局，侧边栏折叠 |
| **手机 (sm)** | 576px - 767px | 大屏手机 | 1 列布局，导航切换到抽屉 |
| **小屏手机 (xs)** | < 576px | 小屏手机 | 1 列布局，简化 UI 元素 |

### 3.2 响应式策略

#### 3.2.1 弹性网格系统
```css
/* 使用 CSS Grid 实现自适应布局 */
.dashboard-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(4, 1fr); /* 默认 4 列 */
}

/* 响应式断点 */
@media (max-width: 1919px) {
  .dashboard-grid {
    grid-template-columns: repeat(3, 1fr); /* 桌面 3 列 */
  }
}

@media (max-width: 1199px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr); /* 平板 2 列 */
  }
}

@media (max-width: 767px) {
  .dashboard-grid {
    grid-template-columns: 1fr; /* 手机 1 列 */
  }
}
```

#### 3.2.2 图表自适应
```typescript
// 监听窗口大小变化，自动调整图表
class ResponsiveChart {
  private chart: echarts.ECharts;
  private debounceTimer: number = 0;
  
  constructor(container: HTMLElement, options: echarts.EChartsOption) {
    this.chart = echarts.init(container);
    this.chart.setOption(options);
    
    // 监听窗口 resize
    window.addEventListener('resize', this.handleResize.bind(this));
    
    // 监听容器尺寸变化 (MutationObserver)
    this.watchContainerResize(container);
  }
  
  private handleResize(): void {
    // 防抖处理，避免频繁重绘
    clearTimeout(this.debounceTimer);
    this.debounceTimer = window.setTimeout(() => {
      this.chart.resize();
      this.updateLayout();
    }, 200);
  }
  
  private updateLayout(): void {
    const width = this.chart.getWidth();
    let newOption: echarts.EChartsOption = {};
    
    if (width < 768) {
      // 小屏幕：减少图例，简化展示
      newOption = {
        legend: { show: false },
        grid: { left: 40, right: 20, top: 40, bottom: 40 }
      };
    } else {
      newOption = {
        legend: { show: true },
        grid: { left: 60, right: 40, top: 50, bottom: 50 }
      };
    }
    
    this.chart.setOption(newOption);
  }
}
```

#### 3.2.3 侧边栏自适应
```vue
<template>
  <aside 
    :class="{ 'sidebar-collapsed': isCollapsed }"
    class="sidebar"
  >
    <div class="sidebar-header">
      <h3 v-if="!isCollapsed">分析菜单</h3>
      <el-button 
        text 
        @click="isCollapsed = !isCollapsed"
      >
        <el-icon>
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useWindowSize } from '@vueuse/core';

const { width } = useWindowSize();
const isCollapsed = ref(false);

// 自动折叠侧边栏
watch(width, (newWidth) => {
  if (newWidth < 1200) {
    isCollapsed.value = true;
  }
}, { immediate: true });
</script>

<style scoped>
.sidebar {
  width: 256px;
  transition: width 0.3s ease;
}

.sidebar-collapsed {
  width: 64px;
}

/* 超小屏幕隐藏侧边栏 */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    z-index: 1000;
    transform: translateX(-100%);
  }
}
</style>
```

---

## 四、前后端连接与数据流

### 4.1 技术架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + TypeScript)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐                 │
│  │  路由 (Router)   │──►│  页面组件        │                 │
│  └──────────────────┘   └──────────────────┘                 │
│                                    │                            │
│  ┌──────────────────┐   ┌──────────────────┐                 │
│  │  状态管理 (Pinia)│◄──┤  图表组件 (ECharts)│                 │
│  └──────────────────┘   └──────────────────┘                 │
│           │                                                      │
│  ┌───────────────────────────────────────────────────┐        │
│  │             API 层 (Axios)                      │        │
│  │  GET /api/v1/data                    POST /api/v1/analysis │
│  └───────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API + CORS
                              │
┌─────────────────────────────────────────────────────────────────┐
│                 后端 (FastAPI + Python 3.12)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────┐        │
│  │              路由层 (Routers)                  │        │
│  │  /api/v1/data  /api/v1/analysis  /api/v1/inference │        │
│  └───────────────────────────────────────────────────┘        │
│                                    │                            │
│  ┌──────────────────┐   ┌──────────────────┐                 │
│  │  数据处理 (Pandas) │──►│  分析引擎         │                 │
│  └──────────────────┘   └──────────────────┘                 │
│                                    │                            │
│  ┌──────────────────┐   ┌──────────────────┐                 │
│  │  可视化 (Plotly)│◄──│  数据源管理        │                 │
│  └──────────────────┘   └──────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 API 接口设计

#### 4.2.1 数据接口 (`/api/v1/data`)

```typescript
// 获取基础数据
GET /api/v1/data/basic
Response: {
  region: string;
  industry: string;
  year: number;
  data: {
    macro_economy: {
      gdp: number;
      gdp_growth: number;
      cpi: number;
    };
    semiconductor_industry: {
      output_value: number;
      market_share: { domestic: number; global: number };
    };
  };
}

// 获取趋势数据
GET /api/v1/data/trend?region=xxx&industry=yyy&startYear=2020&endYear=2025
Response: {
  years: number[];
  series: {
    name: string;
    data: number[];
  }[];
}

// 获取地图数据
GET /api/v1/data/map?indicator=xxx&year=2025
Response: {
  geoJson: any;
  values: {
    [regionCode: string]: {
      name: string;
      value: number;
    };
  };
}
```

#### 4.2.2 分析接口 (`/api/v1/analysis`)

```typescript
// 企业端分析
POST /api/v1/analysis/enterprise
Body: {
  region: string;
  industry: string;
  year: number;
}
Response: {
  land_cost: { ... };
  labor_cost: { ... };
  supply_chain: { ... };
  comprehensive: { ... };
  recommendations: { ... }[];
}

// 政府端分析
POST /api/v1/analysis/government
Body: {
  region: string;
  industry: string;
  year: number;
}
Response: {
  fiscal_leverage: { ... };
  industry_drive: { ... };
  chain_completeness: { ... };
  policy_suggestions: { ... }[];
}

// 对比分析
POST /api/v1/analysis/compare
Body: {
  regions: string[];
  industry: string;
  year: number;
}
Response: {
  regions: string[];
  metrics: {
    name: string;
    unit: string;
    data: number[];
  }[];
}
```

#### 4.2.3 模型接口 (`/api/v1/inference`)

```typescript
// 运行经济模型
POST /api/v1/inference/model
Body: {
  model_type: "phillips" | "okun" | "cobb_douglas";
  input_data: any;
}
Response: {
  model_type: string;
  result: any;
  plot_data?: any;
}
```

### 4.3 状态管理 (Pinia)

```typescript
// stores/analysis.ts
import { defineStore } from 'pinia';

export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    // 当前选择
    currentRegion: '深圳',
    currentIndustry: '半导体',
    currentYear: 2025,
    
    // 分析结果
    enterpriseResult: null,
    governmentResult: null,
    mapData: null,
    
    // UI 状态
    loading: false,
    error: null as string | null,
  }),
  
  actions: {
    async fetchEnterpriseAnalysis() {
      this.loading = true;
      try {
        const response = await api.post('/analysis/enterprise', {
          region: this.currentRegion,
          industry: this.currentIndustry,
          year: this.currentYear,
        });
        this.enterpriseResult = response.data;
      } catch (error) {
        this.error = String(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchGovernmentAnalysis() {
      // 类似...
    },
  },
  
  getters: {
    isReady: (state) => state.enterpriseResult !== null,
  },
});
```

---

## 五、图表组件库设计

### 5.1 封装 ECharts 组件

```vue
<!-- components/charts/EChart.vue -->
<template>
  <div 
    ref="chartContainer"
    :style="{ width: '100%', height: height }"
  />
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';

interface Props {
  option: echarts.EChartsOption;
  height?: string;
  theme?: string;
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  theme: 'light',
});

const chartContainer = ref<HTMLElement>();
let chartInstance: echarts.ECharts;

const initChart = () => {
  if (!chartContainer.value) return;
  
  chartInstance = echarts.init(chartContainer.value, props.theme);
  chartInstance.setOption(props.option);
  
  window.addEventListener('resize', handleResize);
};

const handleResize = () => {
  chartInstance?.resize();
};

const updateOption = (newOption: echarts.EChartsOption) => {
  chartInstance?.setOption(newOption, { notMerge: false });
};

watch(() => props.option, updateOption, { deep: true });

onMounted(initChart);

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
});

defineExpose({
  getInstance: () => chartInstance,
  updateOption,
});
</script>
```

### 5.2 预设图表类型

```typescript
// chartPresets.ts
export const createLineChart = (data: any) => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0 },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: data.categories },
  yAxis: { type: 'value' },
  series: data.series.map((s: any) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.data,
  })),
});

export const createBarChart = (data: any) => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { top: 0 },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: data.categories },
  yAxis: { type: 'value' },
  series: data.series.map((s: any) => ({
    name: s.name,
    type: 'bar',
    data: s.data,
  })),
});

export const createMapChart = (data: any) => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c}',
  },
  visualMap: {
    min: data.min,
    max: data.max,
    left: 'left',
    top: 'bottom',
    text: ['高', '低'],
    inRange: { color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695'] },
  },
  geo: {
    map: 'china',
    roam: true,
    emphasis: {
      itemStyle: { areaColor: '#2a333d' },
    },
  },
  series: [
    {
      name: data.metric,
      type: 'map',
      map: 'china',
      geoIndex: 0,
      data: data.values,
    },
  ],
});
```

---

## 六、开发阶段规划

### 阶段一：项目初始化 (1 天)

1. **前端项目初始化**
   - 使用 Vite + Vue 3 + TypeScript 搭建项目
   - 配置 ESLint、Prettier、Husky
   - 安装依赖包：Element Plus、Pinia、Vue Router、Axios、ECharts
   - 设置开发环境 (dev server 代理)

2. **后端 API 完善**
   - 补充可视化相关 API 端点
   - 添加 CORS 配置 (已完成)
   - 添加数据验证 (Pydantic)

3. **目录结构**
```
frontend/
├── src/
│   ├── api/
│   │   ├── index.ts           # API 实例
│   │   ├── data.ts            # 数据接口
│   │   └── analysis.ts        # 分析接口
│   ├── components/
│   │   ├── charts/            # 图表组件
│   │   ├── layout/            # 布局组件
│   │   └── widgets/           # 小部件
│   ├── views/
│   │   ├── Home.vue           # 主页
│   │   ├── Enterprise.vue     # 企业端
│   │   ├── Government.vue     # 政府端
│   │   ├── Map.vue            # 产业地图
│   │   └── DataManager.vue    # 数据管理
│   ├── stores/
│   │   ├── analysis.ts        # 分析状态
│   │   └── ui.ts              # UI 状态
│   ├── router/
│   │   └── index.ts           # 路由配置
│   ├── types/
│   │   └── index.ts           # TypeScript 类型
│   ├── utils/
│   │   ├── charts.ts          # 图表工具
│   │   └── request.ts         # 请求工具
│   ├── App.vue
│   └── main.ts
├── public/
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### 阶段二：基础布局与导航 (1 天)

1. **布局组件**
   - 顶部导航栏 (Navbar)
   - 侧边栏 (Sidebar)
   - 内容容器 (MainContent)
   - 页脚 (Footer)

2. **路由系统**
   - 配置路由
   - 实现页面切换
   - 路由守卫

3. **响应式基础**
   - 实现断点系统
   - 侧边栏折叠逻辑

### 阶段三：API 层与状态管理 (1 天)

1. **API 层**
   - 封装 Axios 实例
   - 拦截器 (请求/响应)
   - 类型定义

2. **状态管理**
   - 分析数据 store
   - UI 状态 store
   - 持久化 (localStorage)

3. **数据 Mock**
   - 开发阶段 Mock 数据
   - 真实数据切换

### 阶段四：图表组件开发 (3 天)

1. **基础图表组件**
   - 折线图组件
   - 柱状图组件
   - 饼图/环形图组件
   - 雷达图组件
   - 散点图组件

2. **复合图表组件**
   - 双轴图
   - 堆叠图
   - KPI 卡片图
   - 仪表盘

3. **地图组件**
   - 中国地图 (GeoJSON)
   - 下钻交互
   - 热力图

4. **响应式优化**
   - 图表自适应
   - 移动端适配

### 阶段五：页面开发 (4 天)

1. **主页**
   - KPI 卡片
   - 概览图表
   - 快速操作

2. **企业端分析页**
   - 成本分析
   - 供应链分析
   - 政策红利
   - 综合报告

3. **政府端分析页**
   - 财政杠杆
   - 产业带动
   - 产业链分析
   - 政策建议

4. **产业地图页**
   - 区域选择
   - 指标筛选
   - 地图交互
   - 趋势对比

5. **数据管理页**
   - 数据表格
   - 数据筛选
   - 数据导出

### 阶段六：导出与报告功能 (1 天)

1. **图表导出**
   - 导出为图片
   - 导出为 PDF
   - 批量导出

2. **报告生成**
   - HTML 报告
   - Markdown 报告
   - Word 报告 (可选)

### 阶段七：测试与优化 (2 天)

1. **功能测试**
   - 单元测试
   - 集成测试
   - E2E 测试

2. **性能优化**
   - 图表懒加载
   - 数据缓存
   - 虚拟滚动
   - 代码分割

3. **多浏览器测试**
   - Chrome
   - Firefox
   - Safari
   - Edge

### 阶段八：部署与文档 (1 天)

1. **部署配置**
   - Docker 化
   - 反向代理 (Nginx)
   - CI/CD 配置

2. **用户文档**
   - 使用手册
   - 开发文档
   - API 文档

---

## 七、性能优化策略

### 7.1 前端优化

1. **图表懒加载**
```typescript
// 使用 IntersectionObserver 实现图表懒加载
const useLazyLoad = () => {
  const isVisible = ref(false);
  
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          isVisible.value = true;
          observer.disconnect();
        }
      });
    },
    { threshold: 0.1 }
  );
  
  const observe = (el: HTMLElement) => {
    observer.observe(el);
  };
  
  return { isVisible, observe };
};
```

2. **数据缓存**
```typescript
// 使用 TanStack Query 进行数据缓存
import { useQuery } from '@tanstack/vue-query';

const useEnterpriseAnalysis = () => {
  const store = useAnalysisStore();
  return useQuery({
    queryKey: ['enterprise', store.currentRegion, store.currentIndustry, store.currentYear],
    queryFn: () => fetchEnterpriseAnalysis(),
    staleTime: 5 * 60 * 1000, // 5 分钟内认为是新鲜的
  });
};
```

3. **虚拟滚动**
```vue
<!-- 大数据表格使用虚拟滚动 -->
<el-table-v2
  :columns="columns"
  :data="data"
  :width="700"
  :height="400"
/>
```

### 7.2 后端优化

1. **响应缓存**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.post("/analysis/enterprise")
@cache(expire=300)  # 缓存 5 分钟
async def enterprise_analysis(request: AnalysisRequest):
    return await do_analysis(request)
```

2. **流式响应** (大数据)
```python
from fastapi.responses import StreamingResponse

async def generate_large_data():
    for chunk in large_data_generator():
        yield chunk

@router.get("/data/large")
async def get_large_data():
    return StreamingResponse(generate_large_data(), media_type="application/json")
```

---

## 八、开发工具与最佳实践

### 8.1 开发工具

| 工具 | 用途 |
|------|------|
| **Vite DevTools** | 调试状态管理 |
| **Vue DevTools** | 组件调试 |
| **ECharts Inspector** | 图表调试 |
| **VS Code** | 代码编辑 |
| **Postman/Insomnia** | API 调试 |

### 8.2 Git 工作流

```
main (生产环境)
  ↓
develop (开发主线)
  ├── feature/dashboard (功能分支)
  ├── feature/charts (图表功能)
  └── ... (其他功能)
```

### 8.3 代码规范

1. **TypeScript 严格模式**
2. **ESLint + Prettier 自动格式化**
3. **Vue 3 Composition API**
4. **命名规范** (PascalCase 组件, camelCase 变量, UPPER_SNAKE_CASE 常量)

---

## 九、总开发时间估算

| 阶段 | 工作内容 | 时间估算 |
|------|----------|----------|
| **阶段一** | 项目初始化 | 1 天 |
| **阶段二** | 基础布局与导航 | 1 天 |
| **阶段三** | API 层与状态管理 | 1 天 |
| **阶段四** | 图表组件开发 | 3 天 |
| **阶段五** | 页面开发 | 4 天 |
| **阶段六** | 导出与报告功能 | 1 天 |
| **阶段七** | 测试与优化 | 2 天 |
| **阶段八** | 部署与文档 | 1 天 |
| **总计** | - | **14 天 (2 周)** |

---

## 十、下一步行动

1. **准备环境**：检查 Node.js (v18+) 和 Python (3.12+) 版本
2. **开始开发**：按照阶段一步步执行
3. **持续测试**：每个阶段完成后进行测试
4. **及时调整**：根据实际开发进度调整计划
