<template>
  <div class="map-page">
    <!-- 顶部选择器 -->
    <div class="top-filter">
      <div class="filter-item">
        <label>指标：</label>
        <el-select v-model="currentIndicator" placeholder="请选择指标">
          <el-option label="产业产值" value="output" />
          <el-option label="就业人口" value="employment" />
          <el-option label="研发投入" value="rd" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>年份：</label>
        <el-select v-model="store.currentYear" placeholder="请选择年份">
          <el-option :label="2025" :value="2025" />
          <el-option :label="2024" :value="2024" />
        </el-select>
      </div>
    </div>
    
    <div class="map-container">
      <!-- 左侧地图 -->
      <div class="map-main">
        <EChart :option="mapChartOption" height="100%" />
      </div>
      
      <!-- 右侧统计 -->
      <div class="map-sidebar">
        <div class="sidebar-card">
          <h3 class="sidebar-title">区域分布</h3>
          <div class="region-list">
            <div v-for="region in regionData" :key="region.name" class="region-item">
              <span class="region-name">{{ region.name }}</span>
              <span class="region-value">{{ region.value }}{{ region.unit }}</span>
            </div>
          </div>
        </div>
        
        <div class="sidebar-card">
          <h3 class="sidebar-title">趋势分析</h3>
          <EChart :option="trendChartOption" height="200px" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import EChart from '@/components/charts/EChart.vue'

const store = useAnalysisStore()
const currentIndicator = ref('output')

// 地图数据
const regionData = ref([
  { name: '深圳', value: 12000, unit: '亿元' },
  { name: '上海', value: 13500, unit: '亿元' },
  { name: '北京', value: 11800, unit: '亿元' },
  { name: '广州', value: 8900, unit: '亿元' },
  { name: '苏州', value: 7200, unit: '亿元' },
])

// 地图图表配置
const mapChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} 亿元',
  },
  visualMap: {
    min: 0,
    max: 15000,
    left: 'left',
    top: 'bottom',
    text: ['高', '低'],
    inRange: {
      color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695'],
    },
  },
  geo: {
    map: 'china',
    roam: true,
    emphasis: {
      itemStyle: {
        areaColor: '#2a333d',
      },
    },
  },
  series: [
    {
      name: '产业产值',
      type: 'map',
      map: 'china',
      geoIndex: 0,
      data: regionData.value.map(r => ({ name: r.name, value: r.value })),
    },
  ],
}))

// 趋势图表配置
const trendChartData = ref({
  categories: ['2020', '2021', '2022', '2023', '2024', '2025'],
  series: [
    { name: '深圳', data: [6800, 8200, 9600, 11000, 12000, 12800] },
    { name: '上海', data: [7200, 8600, 9900, 11500, 13000, 13500] },
  ],
})

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, data: ['深圳', '上海'] },
  grid: { left: '10%', right: '5%', bottom: '15%', top: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendChartData.value.categories,
  },
  yAxis: { type: 'value' },
  series: trendChartData.value.series.map(s => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.data,
  })),
}))
</script>

<style scoped>
.map-page {
  width: 100%;
  height: 100%;
}

.top-filter {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  color: #606266;
  font-weight: 500;
}

.map-container {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  height: calc(100vh - 260px);
  min-height: 500px;
}

.map-main {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.map-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sidebar-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.region-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.region-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.region-name {
  color: #606266;
  font-weight: 500;
}

.region-value {
  color: #303133;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 1199px) {
  .map-container {
    grid-template-columns: 1fr;
  }
}
</style>
