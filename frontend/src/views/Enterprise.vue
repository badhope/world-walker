<template>
  <div class="enterprise-page" v-loading="store.loading" element-loading-text="正在分析中...">
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

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      closable
      @close="store.error = null"
      style="margin-bottom: 20px"
    />

    <template v-if="store.enterpriseResult">
      <div class="kpi-grid">
        <KpiCard
          :value="store.enterpriseResult.business_cost_score?.toFixed(1) || '0'"
          label="营商成本评分"
          unit="分"
          icon-type="box"
          color="#e6a23c"
          bgColor="#e6a23c"
        />
        <KpiCard
          :value="store.enterpriseResult.supply_chain_score?.toFixed(1) || '0'"
          label="供应链配套评分"
          unit="分"
          icon-type="goods"
          color="#67c23a"
          bgColor="#67c23a"
        />
        <KpiCard
          :value="store.enterpriseResult.policy_benefit_score?.toFixed(1) || '0'"
          label="政策红利评分"
          unit="分"
          icon-type="wallet"
          color="#409eff"
          bgColor="#409eff"
        />
        <KpiCard
          :value="store.enterpriseResult.total_score?.toFixed(1) || '0'"
          label="综合评分"
          unit="分"
          icon-type="trend"
          color="#667eea"
          bgColor="#667eea"
        />
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <h3 class="chart-title">营商成本详情</h3>
          <EChart :option="costChartOption" height="300px" />
        </div>
        <div class="chart-card">
          <h3 class="chart-title">供应链配套雷达图</h3>
          <EChart :option="supplyChainChartOption" height="300px" />
        </div>
        <div class="chart-card">
          <h3 class="chart-title">政策红利详情</h3>
          <EChart :option="policyChartOption" height="300px" />
        </div>
      </div>

      <div class="suggestions-section" v-if="store.enterpriseResult.suggestions?.length">
        <h3 class="section-title">分析建议</h3>
        <div class="suggestions-grid">
          <div
            v-for="(suggestion, index) in store.enterpriseResult.suggestions"
            :key="index"
            class="suggestion-card"
          >
            <div class="suggestion-text">{{ suggestion }}</div>
          </div>
        </div>
      </div>

      <div class="methodology-section" v-if="store.enterpriseResult.methodology">
        <h3 class="section-title">方法论说明</h3>
        <div class="methodology-content">
          <p v-if="store.enterpriseResult.methodology.scoring_basis">
            {{ store.enterpriseResult.methodology.scoring_basis }}
          </p>
          <p v-if="store.enterpriseResult.methodology.weight_source">
            {{ store.enterpriseResult.methodology.weight_source }}
          </p>
        </div>
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

const store = useAnalysisStore()

const costChartOption = computed(() => {
  const details = store.enterpriseResult?.details?.cost_details
  if (!details) return {}
  const categories = ['土地价格', '平均工资', '能源成本', '融资成本']
  const rawValues = [details['土地价格'], details['平均工资'], details['能源成本'], details['融资成本']]
  const scoreValues = [details['土地价格得分'], details['平均工资得分'], details['能源成本得分'], details['融资成本得分']]
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['原始值', '得分'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: categories },
    yAxis: [
      { type: 'value', name: '原始值' },
      { type: 'value', name: '得分', max: 100 },
    ],
    series: [
      {
        name: '原始值',
        type: 'bar',
        data: rawValues,
        itemStyle: { color: '#409eff' },
      },
      {
        name: '得分',
        type: 'line',
        yAxisIndex: 1,
        data: scoreValues,
        itemStyle: { color: '#e6a23c' },
        lineStyle: { width: 3 },
      },
    ],
  }
})

const supplyChainChartOption = computed(() => {
  const details = store.enterpriseResult?.details?.supply_details
  if (!details) return {}
  return {
    tooltip: {},
    radar: {
      indicator: [
        { name: '本地配套率', max: 100 },
        { name: '交付周期', max: 100 },
        { name: '产业集聚度', max: 100 },
      ],
    },
    series: [
      {
        name: '供应链评分',
        type: 'radar',
        data: [
          {
            value: [
              details['本地配套率得分'] || 0,
              details['交付周期得分'] || 0,
              details['产业集聚度得分'] || 0,
            ],
            name: store.enterpriseResult?.city || '当前城市',
            areaStyle: { opacity: 0.3 },
          },
        ],
      },
    ],
  }
})

const policyChartOption = computed(() => {
  const details = store.enterpriseResult?.details?.policy_details
  if (!details) return {}
  const categories = ['减税降费', '政策覆盖率', '研发补贴', '审批效率']
  const rawValues = [details['减税降费'], details['政策覆盖率'], details['研发补贴'], details['平均审批时间']]
  const scoreValues = [details['减税降费得分'], details['政策覆盖率得分'], details['研发补贴得分'], details['审批效率得分']]
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['原始值', '得分'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: categories },
    yAxis: [
      { type: 'value', name: '原始值' },
      { type: 'value', name: '得分', max: 100 },
    ],
    series: [
      {
        name: '原始值',
        type: 'bar',
        data: rawValues,
        itemStyle: {
          color: (params: any) => {
            const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c']
            return colors[params.dataIndex % colors.length]
          },
        },
      },
      {
        name: '得分',
        type: 'line',
        yAxisIndex: 1,
        data: scoreValues,
        itemStyle: { color: '#667eea' },
        lineStyle: { width: 3 },
      },
    ],
  }
})

const onCityChange = () => {
  store.enterpriseResult = null
}

const handleAnalysis = async () => {
  if (!store.currentRegion) return
  await store.runEnterpriseAnalysis()
}

onMounted(() => {
  if (store.cities.length === 0) {
    store.fetchCities()
  }
})
</script>

<style scoped>
.enterprise-page {
  width: 100%;
  padding: 0;
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
  border-bottom: 2px solid #667eea;
  padding-bottom: 8px;
}

.suggestions-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
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
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.methodology-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.methodology-content p {
  color: #909399;
  font-size: 13px;
  line-height: 1.8;
  margin: 4px 0;
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
