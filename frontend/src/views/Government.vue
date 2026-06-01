<template>
  <div class="government-page" v-loading="store.loading" element-loading-text="正在分析中...">
    <div class="top-filter">
      <div class="filter-item">
        <label>城市：</label>
        <el-select v-model="store.currentRegion" placeholder="请选择城市" @change="onCityChange">
          <el-option
            v-for="city in store.cities"
            :key="city"
            :label="city"
            :value="city"
          />
          <el-option v-if="store.cities.length === 0" label="深圳" value="深圳" />
          <el-option v-if="store.cities.length === 0" label="上海" value="上海" />
          <el-option v-if="store.cities.length === 0" label="成都" value="成都" />
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

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      closable
      @close="store.error = null"
      style="margin-bottom: 20px"
    />

    <template v-if="store.governmentResult">
      <div class="kpi-grid">
        <KpiCard
          :value="govData.fiscal_leverage?.score?.toFixed(1) || '0'"
          label="财政杠杆评分"
          unit="分"
          icon-type="wallet"
          color="#764ba2"
          bgColor="#764ba2"
        />
        <KpiCard
          :value="govData.fiscal_leverage?.revenue_efficiency?.toFixed(1) || '0'"
          label="收入效率"
          unit="分"
          icon-type="trend"
          color="#667eea"
          bgColor="#667eea"
        />
        <KpiCard
          :value="govData.industry_drive?.score?.toFixed(1) || '0'"
          label="产业带动评分"
          unit="分"
          icon-type="data"
          color="#e6a23c"
          bgColor="#e6a23c"
        />
        <KpiCard
          :value="govData.industry_drive?.employment_contribution?.toFixed(1) || '0'"
          label="就业贡献"
          unit="分"
          icon-type="user"
          color="#67c23a"
          bgColor="#67c23a"
        />
      </div>

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

      <div class="city-data-section" v-if="store.governmentResult.note">
        <el-alert
          :title="store.governmentResult.note"
          type="info"
          show-icon
          :closable="false"
        />
      </div>
    </template>

    <el-empty
      v-else-if="!store.loading"
      description="请选择城市后点击'开始分析'按钮获取分析结果"
      :image-size="200"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import KpiCard from '@/components/widgets/KpiCard.vue'
import EChart from '@/components/charts/EChart.vue'
import type { EChartsOption } from 'echarts'

const store = useAnalysisStore()

const govData = computed(() => {
  return store.governmentResult?.data || store.governmentResult || {}
})

const fiscalChartOption = computed(() => {
  const fiscal = govData.value.fiscal_leverage
  if (!fiscal) return {}
  const categories = ['综合评分', '收入效率', '支出效率']
  const values = [
    fiscal.score || 0,
    fiscal.revenue_efficiency || 0,
    fiscal.expenditure_efficiency || 0,
  ]
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value', name: '评分', max: 100 },
    series: [
      {
        name: '评分',
        type: 'bar',
        data: values,
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const colors = ['#764ba2', '#667eea', '#a855f7']
            return colors[params.dataIndex % colors.length]
          },
        },
        label: { show: true, position: 'top', formatter: '{c}' },
      },
    ],
  } as EChartsOption
})

const industryChartOption = computed(() => {
  const industry = govData.value.industry_drive
  if (!industry) return {}
  return {
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        name: '产业带动',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 20, fontWeight: 'bold' },
        },
        labelLine: { show: false },
        data: [
          { name: '就业贡献', value: industry.employment_contribution || 0 },
          { name: '税收贡献', value: industry.tax_contribution || 0 },
        ],
      },
    ],
  } as EChartsOption
})

const onCityChange = () => {
  store.governmentResult = null
}

const handleAnalysis = async () => {
  if (!store.currentRegion) return
  await store.runGovernmentAnalysis()
}

onMounted(() => {
  if (store.cities.length === 0) {
    store.fetchCities()
  }
})
</script>

<style scoped>
.government-page {
  width: 100%;
  min-height: 200px;
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
  border-bottom: 2px solid #764ba2;
  padding-bottom: 8px;
}

.city-data-section {
  margin-top: 20px;
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
