<template>
  <div class="map-page">
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
      <div class="map-main">
        <el-card>
          <template #header>
            <span>城市产业分布</span>
          </template>
          <EChart :option="barChartOption" height="400px" />
        </el-card>
      </div>

      <div class="map-sidebar">
        <el-card>
          <template #header>
            <span>区域分布</span>
          </template>
          <div class="region-list">
            <div v-for="region in regionData" :key="region.name" class="region-item">
              <span class="region-name">{{ region.name }}</span>
              <span class="region-value">{{ region.value }}{{ region.unit }}</span>
            </div>
          </div>
        </el-card>

        <el-card>
          <template #header>
            <span>趋势分析</span>
          </template>
          <EChart :option="trendChartOption" height="200px" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import EChart from '@/components/charts/EChart.vue'
import type { EChartsOption } from 'echarts'
import { citiesApi } from '@/api'

const store = useAnalysisStore()
const currentIndicator = ref('output')

const regionData = ref([
  { name: '深圳', value: 12000, unit: '亿元' },
  { name: '上海', value: 13500, unit: '亿元' },
  { name: '北京', value: 11800, unit: '亿元' },
  { name: '广州', value: 8900, unit: '亿元' },
  { name: '苏州', value: 7200, unit: '亿元' },
])

const barChartOption = computed(() => {
  const data = [...regionData.value].sort((a, b) => b.value - a.value)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c} 亿元',
    },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '亿元' },
    yAxis: {
      type: 'category',
      data: data.map(r => r.name),
      inverse: true,
    },
    series: [
      {
        name: '产业产值',
        type: 'bar',
        data: data.map(r => r.value),
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const colors = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8']
            return colors[params.dataIndex % colors.length]
          },
          borderRadius: [0, 4, 4, 0],
        },
        label: { show: true, position: 'right', formatter: '{c} 亿元' },
      },
    ],
  } as EChartsOption
})

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
  xAxis: { type: 'category', data: trendChartData.value.categories },
  yAxis: { type: 'value' },
  series: trendChartData.value.series.map(s => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.data,
  })),
} as EChartsOption))

onMounted(async () => {
  try {
    await citiesApi.getCities()
  } catch {
    // fallback to hardcoded data
  }
})
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
}

.map-main {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.map-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

@media (max-width: 1199px) {
  .map-container {
    grid-template-columns: 1fr;
  }
}
</style>