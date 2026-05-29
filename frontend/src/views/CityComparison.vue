<template>
  <div class="city-comparison-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <h2>城市对比分析</h2>
      <div class="header-actions">
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 筛选条件 -->
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
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：城市排名 -->
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
      
      <!-- 右侧：图表区域 -->
      <div class="charts-section">
        <!-- 柱状图 -->
        <el-card>
          <template #header>
            <span>城市对比柱状图</span>
          </template>
          <div ref="barChartRef" class="chart-container"></div>
        </el-card>
        
        <!-- 趋势图 -->
        <el-card style="margin-top: 20px">
          <template #header>
            <span>时间趋势图</span>
          </template>
          <div ref="lineChartRef" class="chart-container"></div>
        </el-card>
      </div>
    </div>
    
    <!-- 聚合分析区域 -->
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
    
    <!-- 聚合配置对话框 -->
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
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Top, Bottom } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 状态
const loading = ref(false)
const showAggregationDialog = ref(false)
const activeTab = ref('city')

// 筛选表单
const filterForm = ref({
  indicator: 'gdp',
  year: '2024',
  limit: 10,
})

// 聚合配置表单
const aggregationForm = ref({
  groupBy: ['city'],
  metrics: ['sum', 'avg'],
  sortBy: 'sum',
  sortOrder: 'desc',
  limit: 20,
})

// 数据
const rankings = ref<any[]>([])
const aggregationByCity = ref<any[]>([])
const aggregationByRegion = ref<any[]>([])
const timeSeriesData = ref<any[]>([])

// 图表引用
const barChartRef = ref()
const lineChartRef = ref()

// 方法
const loadRankings = async () => {
  loading.value = true
  try {
    // 模拟加载排名数据
    const mockRankings = [
      { city: '上海', value: 47218.66 },
      { city: '北京', value: 43430.1 },
      { city: '深圳', value: 36801.87 },
      { city: '广州', value: 30355.73 },
      { city: '重庆', value: 27894.02 },
      { city: '苏州', value: 23458.36 },
      { city: '成都', value: 22074.7 },
      { city: '杭州', value: 20059.0 },
      { city: '武汉', value: 18866.43 },
      { city: '南京', value: 16908.0 },
    ]
    
    rankings.value = mockRankings.slice(0, filterForm.value.limit)
    
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
    // 模拟聚合数据
    aggregationByCity.value = [
      { city: '上海', sum: 47218.66, avg: 9443.73, min: 3400.0, max: 12000.0, count: 5 },
      { city: '北京', sum: 43430.1, avg: 8686.02, min: 3200.0, max: 11500.0, count: 5 },
      { city: '深圳', sum: 36801.87, avg: 7360.37, min: 2800.0, max: 10000.0, count: 5 },
      { city: '广州', sum: 30355.73, avg: 6071.15, min: 2400.0, max: 8500.0, count: 5 },
    ]
    
    aggregationByRegion.value = [
      { region: '广东', city_count: 2, avg: 6711.76, total: 67117.6 },
      { region: '上海', city_count: 1, avg: 8686.02, total: 43430.1 },
      { region: '北京', city_count: 1, avg: 8686.02, total: 43430.1 },
      { region: '浙江', city_count: 1, avg: 6071.15, total: 30355.73 },
    ]
    
    // 模拟时间序列数据
    timeSeriesData.value = [
      { year: 2020, gdp: 28000, cpi: 100, pmi: 48 },
      { year: 2021, gdp: 30500, cpi: 101, pmi: 50 },
      { year: 2022, gdp: 32500, cpi: 102, pmi: 49 },
      { year: 2023, gdp: 34600, cpi: 101, pmi: 51 },
      { year: 2024, gdp: 36801, cpi: 102, pmi: 52 },
    ]
    
    await nextTick()
    renderLineChart()
    
  } catch (error) {
    console.error('聚合数据加载失败', error)
  }
}

const runAggregation = () => {
  showAggregationDialog.value = false
  loadAggregation()
  ElMessage.success('聚合分析完成')
}

const renderBarChart = () => {
  if (!barChartRef.value) return
  
  const chart = echarts.init(barChartRef.value)
  
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
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

const renderLineChart = () => {
  if (!lineChartRef.value) return
  
  const chart = echarts.init(lineChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['GDP', 'CPI', 'PMI'],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: timeSeriesData.value.map(d => d.year),
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: 'GDP',
        type: 'line',
        data: timeSeriesData.value.map(d => d.gdp),
        smooth: true,
        itemStyle: { color: '#409eff' },
      },
      {
        name: 'CPI',
        type: 'line',
        data: timeSeriesData.value.map(d => d.cpi),
        smooth: true,
        yAxisIndex: 0,
        itemStyle: { color: '#67c23a' },
      },
      {
        name: 'PMI',
        type: 'line',
        data: timeSeriesData.value.map(d => d.pmi),
        smooth: true,
        itemStyle: { color: '#e6a23c' },
      },
    ],
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart.resize()
  })
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

// 生命周期
onMounted(() => {
  loadRankings()
  loadAggregation()
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

/* 响应式 */
@media (max-width: 1199px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    order: -1;
  }
}
</style>
