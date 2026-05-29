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
    
    <!-- 错误提示 -->
    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      closable
      @close="store.error = null"
      style="margin-bottom: 20px"
    />
    
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
    <template v-else-if="store.enterpriseResult">
      <!-- KPI 卡片 -->
      <div class="kpi-grid">
        <KpiCard
          :value="store.enterpriseResult.land_cost_analysis?.city_average || 0"
          label="平均用地成本"
          unit="元/㎡·年"
          icon-type="box"
        />
        <KpiCard
          :value="store.enterpriseResult.labor_cost_analysis?.average_salary || 0"
          label="平均工资"
          unit="元/月"
          icon-type="user"
        />
        <KpiCard
          :value="store.enterpriseResult.supply_chain_analysis?.localization_rate || 0"
          label="本地化率"
          unit="%"
          icon-type="goods"
        />
        <KpiCard
          :value="store.enterpriseResult.comprehensive_cost_index?.shenzhen_index || 0"
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
      <div class="suggestions-section" v-if="store.enterpriseResult.overall_recommendations?.length">
        <h3 class="section-title">优化建议</h3>
        <div class="suggestions-grid">
          <div
            v-for="(rec, index) in store.enterpriseResult.overall_recommendations"
            :key="index"
            class="suggestion-card"
          >
            <div class="suggestion-header">
              <el-tag :type="getTagType(rec.type)">{{ rec.type }}</el-tag>
            </div>
            <div class="suggestion-text">{{ rec.suggestion }}</div>
          </div>
        </div>
      </div>
    </template>
    
    <!-- 空状态 -->
    <el-empty 
      v-else 
      description="请选择参数后点击'开始分析'按钮获取分析结果"
      :image-size="200"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import KpiCard from '@/components/widgets/KpiCard.vue'
import EChart from '@/components/charts/EChart.vue'
import { createBarChart, createRadarChart, createLineChart } from '@/utils/charts'

const store = useAnalysisStore()

const costChartData = ref({
  categories: ['用地成本', '人力成本', '能源成本', '融资成本'],
  series: [
    {
      name: '深圳',
      data: [812, 18500, 0.68, 4.85],
    },
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
  if (!store.currentRegion || !store.currentIndustry || !store.currentYear) {
    return
  }
  await store.fetchEnterpriseAnalysis()
}

const getTagType = (type: string) => {
  if (type.includes('人力')) return 'warning'
  if (type.includes('融资')) return 'success'
  if (type.includes('用地')) return 'primary'
  return 'info'
}
</script>

<style scoped>
.enterprise-page {
  width: 100%;
  padding: 0;
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
  font-weight: 600;
  white-space: nowrap;
  font-size: 14px;
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

.suggestion-header {
  margin-bottom: 12px;
}

.suggestion-text {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

@media (max-width: 768px) {
  .top-filter {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-item {
    width: 100%;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
