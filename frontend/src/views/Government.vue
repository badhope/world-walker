<template>
  <div class="government-page">
    <!-- 顶部选择器 -->
    <div class="top-filter">
      <div class="filter-item">
        <label>区域：</label>
        <el-select v-model="store.currentRegion" placeholder="请选择区域">
          <el-option label="深圳" value="深圳" />
          <el-option label="上海" value="上海" />
          <el-option label="北京" value="北京" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>产业：</label>
        <el-select v-model="store.currentIndustry" placeholder="请选择产业">
          <el-option label="半导体" value="半导体" />
          <el-option label="新能源汽车" value="新能源汽车" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>年份：</label>
        <el-select v-model="store.currentYear" placeholder="请选择年份">
          <el-option :label="2025" :value="2025" />
          <el-option :label="2024" :value="2024" />
        </el-select>
      </div>
      <el-button type="primary" @click="handleAnalysis" :loading="store.loading">
        开始分析
      </el-button>
    </div>
    
    <!-- KPI 卡片 -->
    <div class="kpi-grid" v-if="store.governmentResult">
      <KpiCard
        :value="store.governmentResult.fiscal_leverage.fiscal_revenue"
        label="财政收入 (亿元)"
        icon-type="wallet"
      />
      <KpiCard
        :value="store.governmentResult.fiscal_leverage.leverage_ratio"
        label="杠杆倍数"
        unit="倍"
        icon-type="trend"
      />
      <KpiCard
        :value="store.governmentResult.industry_drive.employment_effect.total"
        label="带动就业 (万人)"
        icon-type="user"
      />
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-grid">
      <div class="chart-card">
        <h3 class="chart-title">财政杠杆分析</h3>
        <EChart :option="fiscalChartOption" height="320px" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">产业带动效应</h3>
        <EChart :option="industryChartOption" height="320px" />
      </div>
    </div>
    
    <!-- 政策建议 -->
    <div class="suggestions-section" v-if="store.governmentResult?.policy_suggestions">
      <h3 class="section-title">政策建议</h3>
      <div class="suggestions-list">
        <div
          v-for="(suggestion, index) in store.governmentResult.policy_suggestions"
          :key="index"
          class="suggestion-card"
        >
          <div class="suggestion-header">
            <span class="suggestion-priority">{{ suggestion.priority }}</span>
            <h4 class="suggestion-title">{{ suggestion.title }}</h4>
          </div>
          <p class="suggestion-content">{{ suggestion.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import KpiCard from '@/components/widgets/KpiCard.vue'
import EChart from '@/components/charts/EChart.vue'
import { createBarChart, createPieChart } from '@/utils/charts'

const store = useAnalysisStore()

// 图表数据
const fiscalChartData = ref({
  categories: ['财政收入', '财政支出', '产业支持'],
  series: [
    { name: '2025', data: [4512, 5057, 158] },
  ],
})

const industryChartData = ref([
  { name: '直接就业', value: 45 },
  { name: '间接就业', value: 28.5 },
  { name: '带动GDP', value: 320 },
])

const fiscalChartOption = computed(() => createBarChart(fiscalChartData.value))
const industryChartOption = computed(() => createPieChart(industryChartData.value))

const handleAnalysis = async () => {
  await store.fetchGovernmentAnalysis()
}
</script>

<style scoped>
.government-page {
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
  border-bottom: 2px solid #764ba2;
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

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-card {
  border-left: 4px solid #667eea;
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 0 8px 8px 0;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.suggestion-priority {
  padding: 2px 8px;
  background: #667eea;
  color: white;
  font-size: 12px;
  border-radius: 4px;
}

.suggestion-title {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.suggestion-content {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}
</style>
