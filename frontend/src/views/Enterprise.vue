<template>
  <div class="enterprise-page">
    <!-- 顶部选择器 -->
    <div class="top-filter">
      <div class="filter-item">
        <label>区域：</label>
        <el-select v-model="store.currentRegion" placeholder="请选择区域">
          <el-option label="深圳" value="深圳" />
          <el-option label="上海" value="上海" />
          <el-option label="北京" value="北京" />
          <el-option label="广州" value="广州" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>产业：</label>
        <el-select v-model="store.currentIndustry" placeholder="请选择产业">
          <el-option label="半导体" value="半导体" />
          <el-option label="新能源汽车" value="新能源汽车" />
          <el-option label="人工智能" value="人工智能" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>年份：</label>
        <el-select v-model="store.currentYear" placeholder="请选择年份">
          <el-option :label="2025" :value="2025" />
          <el-option :label="2024" :value="2024" />
          <el-option :label="2023" :value="2023" />
        </el-select>
      </div>
      <el-button type="primary" @click="handleAnalysis" :loading="store.loading">
        开始分析
      </el-button>
    </div>
    
    <!-- 加载状态 -->
    <el-skeleton :loading="store.loading" animated v-if="store.loading">
      <template #template>
        <div style="padding: 20px">
          <el-skeleton-item variant="h3" style="width: 40%" />
          <el-skeleton style="margin: 20px 0">
            <el-skeleton-item variant="text" />
            <el-skeleton-item variant="text" />
          </el-skeleton>
        </div>
      </template>
    </el-skeleton>
    
    <!-- 分析结果 -->
    <template v-else>
      <!-- KPI 卡片 -->
      <div class="kpi-grid" v-if="store.enterpriseResult">
        <KpiCard
          :value="store.enterpriseResult.land_cost.city_average"
          label="平均用地成本"
          unit="元/㎡·年"
          icon-type="box"
        />
        <KpiCard
          :value="store.enterpriseResult.labor_cost.average_salary"
          label="平均工资"
          unit="元/月"
          icon-type="user"
        />
        <KpiCard
          :value="store.enterpriseResult.supply_chain.localization_rate"
          label="本地化率"
          unit="%"
          icon-type="goods"
        />
        <KpiCard
          :value="store.enterpriseResult.comprehensive.shenzhen_index"
          label="综合成本指数"
          unit=""
          icon-type="trend"
        />
      </div>
      
      <!-- 图表区域 -->
      <div class="charts-grid">
        <div class="chart-card">
          <h3 class="chart-title">成本对比分析</h3>
          <EChart :option="costChartOption" height="300px" />
        </div>
        <div class="chart-card">
          <h3 class="chart-title">供应链覆盖度</h3>
          <EChart :option="supplyChainChartOption" height="300px" />
        </div>
        <div class="chart-card">
          <h3 class="chart-title">成本趋势</h3>
          <EChart :option="trendChartOption" height="300px" />
        </div>
      </div>
      
      <!-- 建议区域 -->
      <div class="suggestions-section" v-if="store.enterpriseResult?.recommendations">
        <h3 class="section-title">优化建议</h3>
        <div class="suggestions-grid">
          <div
            v-for="(rec, index) in store.enterpriseResult.recommendations"
            :key="index"
            class="suggestion-card"
          >
            <el-tag :type="rec.type === 'critical' ? 'danger' : 'info'">
              {{ rec.type }}
            </el-tag>
            <p class="suggestion-text">{{ rec.suggestion }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import KpiCard from '@/components/widgets/KpiCard.vue'
import EChart from '@/components/charts/EChart.vue'
import { createBarChart, createLineChart, createRadarChart } from '@/utils/charts'

const store = useAnalysisStore()

// 图表数据
const costChartData = ref({
  categories: ['用地成本', '人力成本', '能源成本'],
  series: [
    { name: '深圳', data: [812, 18500, 0.68] },
    { name: '上海', data: [920, 19200, 0.71] },
  ],
})

const supplyChainData = ref({
  indicator: [
    { name: '上游覆盖', max: 100 },
    { name: '中游覆盖', max: 100 },
    { name: '下游覆盖', max: 100 },
  ],
  data: [
    {
      name: '深圳',
      value: [65, 85, 95],
    },
  ],
})

const trendChartData = ref({
  categories: ['2020', '2021', '2022', '2023', '2024', '2025'],
  series: [
    { name: '综合成本指数', data: [100, 103, 105, 104, 106, 105] },
  ],
})

const costChartOption = computed(() => createBarChart(costChartData.value))
const supplyChainChartOption = computed(() => createRadarChart(supplyChainData.value))
const trendChartOption = computed(() => createLineChart(trendChartData.value))

const handleAnalysis = async () => {
  await store.fetchEnterpriseAnalysis()
}
</script>

<style scoped>
.enterprise-page {
  width: 100%;
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
  white-space: nowrap;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  border-bottom: 2px solid #667eea;
  padding-bottom: 8px;
}

.suggestions-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.suggestion-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
}

.suggestion-text {
  margin-top: 12px;
  color: #606266;
  line-height: 1.6;
}
</style>
