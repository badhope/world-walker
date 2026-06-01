<template>
  <div class="city-comparison-page">
    <div class="page-header">
      <h2>城市对比分析</h2>
      <div class="header-actions">
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="filter-section">
      <el-card>
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="选择指标">
            <el-select v-model="filterForm.indicator" placeholder="选择指标" style="width: 200px">
              <el-option label="GDP" value="gdp" />
              <el-option label="CPI" value="cpi" />
              <el-option label="PMI" value="pmi" />
              <el-option label="财政收入" value="fiscal_revenue" />
              <el-option label="工业产值" value="industrial_output" />
            </el-select>
          </el-form-item>

          <el-form-item label="年份">
            <el-date-picker
              v-model="filterForm.year"
              type="year"
              placeholder="选择年份"
              format="YYYY"
              value-format="YYYY"
              style="width: 150px"
            />
          </el-form-item>

          <el-form-item label="排名数量">
            <el-input-number
              v-model="filterForm.limit"
              :min="5"
              :max="20"
              style="width: 120px"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="loadRankings">
              查询
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="main-content">
      <div class="rankings-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>城市排名</span>
              <el-tag type="info">{{ filterForm.indicator }}</el-tag>
            </div>
          </template>

          <div v-loading="loading">
            <el-table :data="rankings" stripe border>
              <el-table-column type="index" label="排名" width="80" align="center">
                <template #default="{ $index }">
                  <el-tag :type="getRankType($index + 1)">
                    {{ $index + 1 }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="city" label="城市" min-width="120" />

              <el-table-column prop="value" label="数值" width="150" sortable>
                <template #default="{ row }">
                  <span class="value-text">{{ formatNumber(row.value) }}</span>
                </template>
              </el-table-column>

              <el-table-column label="趋势" width="100" align="center">
                <template #default="{ $index }">
                  <el-icon :color="getTrendColor($index)">
                    <Top v-if="$index < 3" />
                    <Bottom v-else />
                  </el-icon>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </div>

      <div class="charts-section">
        <el-card>
          <template #header>
            <span>城市对比柱状图</span>
          </template>
          <div ref="barChartRef" class="chart-container"></div>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>时间趋势图</span>
          </template>
          <div ref="lineChartRef" class="chart-container"></div>
        </el-card>
      </div>
    </div>

    <div class="aggregation-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>聚合分析</span>
            <el-button-group>
              <el-button size="small" @click="showAggregationDialog = true">
                配置聚合
              </el-button>
            </el-button-group>
          </div>
        </template>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="按城市聚合" name="city">
            <el-table :data="aggregationByCity" stripe border>
              <el-table-column prop="city" label="城市" width="150" />
              <el-table-column prop="sum" label="总和" width="150">
                <template #default="{ row }">
                  {{ formatNumber(row.sum) }}
                </template>
              </el-table-column>
              <el-table-column prop="avg" label="平均值" width="150">
                <template #default="{ row }">
                  {{ formatNumber(row.avg) }}
                </template>
              </el-table-column>
              <el-table-column prop="min" label="最小值" width="150">
                <template #default="{ row }">
                  {{ formatNumber(row.min) }}
                </template>
              </el-table-column>
              <el-table-column prop="max" label="最大值" width="150">
                <template #default="{ row }">
                  {{ formatNumber(row.max) }}
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数据量" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="按区域聚合" name="region">
            <el-table :data="aggregationByRegion" stripe border>
              <el-table-column prop="region" label="区域" width="150" />
              <el-table-column prop="city_count" label="城市数量" width="120" />
              <el-table-column prop="avg" label="平均值" width="150">
                <template #default="{ row }">
                  {{ formatNumber(row.avg) }}
                </template>
              </el-table-column>
              <el-table-column prop="total" label="总计" width="150">
                <template #default="{ row }">
                  {{ formatNumber(row.total) }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <el-dialog
      v-model="showAggregationDialog"
      title="聚合分析配置"
      width="600px"
    >
      <el-form :model="aggregationForm" label-width="100px">
        <el-form-item label="分组字段">
          <el-checkbox-group v-model="aggregationForm.groupBy">
            <el-checkbox label="city">城市</el-checkbox>
            <el-checkbox label="region">区域</el-checkbox>
            <el-checkbox label="year">年份</el-checkbox>
            <el-checkbox label="indicator">指标</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="聚合指标">
          <el-checkbox-group v-model="aggregationForm.metrics">
            <el-checkbox label="count">计数</el-checkbox>
            <el-checkbox label="sum">求和</el-checkbox>
            <el-checkbox label="avg">平均值</el-checkbox>
            <el-checkbox label="min">最小值</el-checkbox>
            <el-checkbox label="max">最大值</el-checkbox>
            <el-checkbox label="median">中位数</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="排序字段">
          <el-select v-model="aggregationForm.sortBy" style="width: 100%">
            <el-option label="无" :value="null" />
            <el-option label="求和" value="sum" />
            <el-option label="平均值" value="avg" />
            <el-option label="计数" value="count" />
          </el-select>
        </el-form-item>

        <el-form-item label="排序方式">
          <el-radio-group v-model="aggregationForm.sortOrder">
            <el-radio label="desc">降序</el-radio>
            <el-radio label="asc">升序</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="限制数量">
          <el-input-number
            v-model="aggregationForm.limit"
            :min="1"
            :max="100"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAggregationDialog = false">取消</el-button>
        <el-button type="primary" @click="runAggregation">执行聚合</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Top, Bottom } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAnalysisStore } from '@/stores/analysis'
import type {
  CityRanking,
  AggregationGroupItem,
  AggregationCityItem,
  AggregationRegionItem,
  TimeSeriesValue,
  TimeSeriesGroup,
  TimeSeriesDisplayItem,
  FilterFormData,
  AggregationFormData,
} from '@/types'

const store = useAnalysisStore()

const loading = ref(false)
const showAggregationDialog = ref(false)
const activeTab = ref('city')

const filterForm = ref<FilterFormData>({
  indicator: 'gdp',
  year: '2024',
  limit: 10,
})

const aggregationForm = ref<AggregationFormData>({
  groupBy: ['city'],
  metrics: ['sum', 'avg'],
  sortBy: 'sum',
  sortOrder: 'desc',
  limit: 20,
})

const rankings = ref<CityRanking[]>([])
const aggregationByCity = ref<AggregationCityItem[]>([])
const aggregationByRegion = ref<AggregationRegionItem[]>([])
const timeSeriesData = ref<TimeSeriesDisplayItem[]>([])

const barChartRef = ref()
const lineChartRef = ref()

let barChartInstance: echarts.ECharts | null = null
let lineChartInstance: echarts.ECharts | null = null

const loadRankings = async () => {
  loading.value = true
  try {
    const yearNum = filterForm.value.year ? parseInt(filterForm.value.year) : undefined
    const result = await store.fetchCityRankings({
      indicator: filterForm.value.indicator,
      year: yearNum,
      limit: filterForm.value.limit,
    })

    if (result && result.rankings) {
      rankings.value = result.rankings
    } else if (result) {
      rankings.value = Array.isArray(result) ? result : []
    }

    await nextTick()
    renderBarChart()

    ElMessage.success('排名加载成功')
  } catch (error) {
    ElMessage.error('排名加载失败')
  } finally {
    loading.value = false
  }
}

const loadAggregation = async () => {
  try {
    const result = await store.aggregateData({
      group_by: aggregationForm.value.groupBy,
      metrics: aggregationForm.value.metrics,
      sort_by: aggregationForm.value.sortBy || undefined,
      sort_order: aggregationForm.value.sortOrder,
      limit: aggregationForm.value.limit,
    })

    if (result && result.result) {
      const groups = result.result.groups || []
      if (aggregationForm.value.groupBy.includes('city')) {
        aggregationByCity.value = groups.map((g: AggregationGroupItem) => ({
          city: g.city || g.group_key || '',
          sum: g.sum ?? g.metrics?.sum ?? 0,
          avg: g.avg ?? g.metrics?.avg ?? 0,
          min: g.min ?? g.metrics?.min ?? 0,
          max: g.max ?? g.metrics?.max ?? 0,
          count: g.count ?? g.metrics?.count ?? 0,
        }))
      }
      if (aggregationForm.value.groupBy.includes('region')) {
        aggregationByRegion.value = groups.map((g: AggregationGroupItem) => ({
          region: g.region || g.group_key || '',
          city_count: g.city_count ?? g.metrics?.count ?? 0,
          avg: g.avg ?? g.metrics?.avg ?? 0,
          total: g.sum ?? g.metrics?.sum ?? 0,
        }))
      }
    }

    await loadTimeSeries()
  } catch (error) {
    ElMessage.error('聚合数据加载失败')
  }
}

const loadTimeSeries = async () => {
  try {
    const cityCodes = store.cities.length > 0
      ? store.cities.slice(0, 8)
      : ['深圳', '上海', '北京', '广州', '杭州', '武汉', '成都', '南京']
    const result = await store.timeSeriesAnalysis({
      city_codes: cityCodes,
      indicator: filterForm.value.indicator,
      year_start: 2020,
      year_end: 2025,
      group_by: ['city_code'],
    })

    if (result && result.time_series) {
      const tsData = result.time_series
      if ('groups' in tsData && tsData.groups && Array.isArray(tsData.groups)) {
        timeSeriesData.value = tsData.groups.flatMap((g: TimeSeriesGroup) =>
          (g.values || []).map((v: TimeSeriesValue) => ({
            city: g.city || g.group_key || '',
            year: v.year || v.time || '',
            value: v.value ?? v.avg ?? 0,
          }))
        )
      } else if (Array.isArray(tsData)) {
        timeSeriesData.value = tsData as TimeSeriesDisplayItem[]
      }
    }

    await nextTick()
    renderLineChart()
  } catch (error) {
    ElMessage.error('时间序列数据加载失败')
  }
}

const runAggregation = () => {
  showAggregationDialog.value = false
  loadAggregation()
  ElMessage.success('聚合分析完成')
}

const renderBarChart = () => {
  if (!barChartRef.value) return

  if (barChartInstance) {
    barChartInstance.dispose()
  }
  barChartInstance = echarts.init(barChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: rankings.value.map(r => r.city),
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'value',
      name: '数值',
    },
    series: [
      {
        name: filterForm.value.indicator,
        type: 'bar',
        data: rankings.value.map(r => r.value),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409eff' },
            { offset: 1, color: '#66b1ff' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
        },
      },
    ],
  }

  barChartInstance.setOption(option)
}

const renderLineChart = () => {
  if (!lineChartRef.value) return

  if (lineChartInstance) {
    lineChartInstance.dispose()
  }
  lineChartInstance = echarts.init(lineChartRef.value)

  const years = [...new Set(timeSeriesData.value.map(d => d.year))].sort()
  const cities = [...new Set(timeSeriesData.value.map(d => d.city))]
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#667eea', '#764ba2', '#a855f7']

  const series = cities.map((city, idx) => ({
    name: city,
    type: 'line' as const,
    data: years.map(year => {
      const item = timeSeriesData.value.find(d => d.city === city && d.year === year)
      return item ? item.value : null
    }),
    smooth: true,
    itemStyle: { color: colors[idx % colors.length] },
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: cities,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: years.map(String),
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
    },
    series,
  }

  lineChartInstance.setOption(option)
}

const formatNumber = (value: number) => {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

const getRankType = (rank: number) => {
  if (rank === 1) return 'danger'
  if (rank === 2) return 'warning'
  if (rank === 3) return 'success'
  return 'info'
}

const getTrendColor = (index: number) => {
  if (index < 3) return '#67c23a'
  return '#909399'
}

const refreshData = () => {
  loadRankings()
  loadAggregation()
}

onMounted(() => {
  loadRankings()
  loadAggregation()
})

onUnmounted(() => {
  barChartInstance?.dispose()
  barChartInstance = null
  lineChartInstance?.dispose()
  lineChartInstance = null
})
</script>

<style scoped>
.city-comparison-page {
  width: 100%;
  height: 100%;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-section {
  margin-bottom: 20px;
}

.main-content {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.rankings-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.charts-section {
  display: flex;
  flex-direction: column;
}

.charts-section > .el-card {
  flex: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.value-text {
  font-weight: 600;
  color: #409eff;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.aggregation-section {
  margin-top: 20px;
}

@media (max-width: 1199px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .charts-section {
    order: -1;
  }
}
</style>
