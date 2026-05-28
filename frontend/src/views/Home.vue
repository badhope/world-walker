<template>
  <div class="home-page">
    <!-- KPI 卡片区域 -->
    <div class="kpi-grid">
      <KpiCard
        :value="36801.87"
        label="GDP (亿元)"
        icon-type="data"
        color="#667eea"
        bg-color="#667eea"
      />
      <KpiCard
        :value="5.8"
        label="GDP 增速 (%)"
        unit="%"
        icon-type="trend"
        color="#10b981"
        bg-color="#10b981"
      />
      <KpiCard
        :value="1222.56"
        label="就业人口 (万人)"
        icon-type="user"
        color="#f59e0b"
        bg-color="#f59e0b"
      />
      <KpiCard
        :value="4512"
        label="财政收入 (亿元)"
        icon-type="wallet"
        color="#ef4444"
        bg-color="#ef4444"
      />
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-grid">
      <div class="chart-card">
        <h3 class="chart-title">经济指标趋势</h3>
        <EChart :option="lineChartOption" height="320px" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">产业结构分布</h3>
        <EChart :option="pieChartOption" height="320px" />
      </div>
    </div>
    
    <!-- 快速操作区域 -->
    <div class="quick-actions">
      <h3 class="section-title">快速操作</h3>
      <div class="actions-grid">
        <router-link to="/enterprise" class="action-card">
          <div class="action-icon">
            <el-icon size="36"><OfficeBuilding /></el-icon>
          </div>
          <div class="action-title">企业端分析</div>
          <div class="action-desc">分析营商成本、供应链、政策红利</div>
        </router-link>
        <router-link to="/government" class="action-card">
          <div class="action-icon">
            <el-icon size="36"><Reading /></el-icon>
          </div>
          <div class="action-title">政府端分析</div>
          <div class="action-desc">分析财政杠杆、产业带动效应</div>
        </router-link>
        <router-link to="/map" class="action-card">
          <div class="action-icon">
            <el-icon size="36"><MapLocation /></el-icon>
          </div>
          <div class="action-title">产业地图</div>
          <div class="action-desc">查看各区域产业发展情况</div>
        </router-link>
        <router-link to="/data" class="action-card">
          <div class="action-icon">
            <el-icon size="36"><FolderOpened /></el-icon>
          </div>
          <div class="action-title">数据管理</div>
          <div class="action-desc">管理和导出分析数据</div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { OfficeBuilding, Reading, MapLocation, FolderOpened } from '@element-plus/icons-vue'
import KpiCard from '@/components/widgets/KpiCard.vue'
import EChart from '@/components/charts/EChart.vue'
import { createLineChart, createPieChart } from '@/utils/charts'

const router = useRouter()

// 图表数据
const lineChartData = ref({
  categories: ['2020', '2021', '2022', '2023', '2024', '2025'],
  series: [
    { name: 'GDP增速', data: [6.5, 8.1, 3.0, 5.6, 5.8, 6.0] },
    { name: 'CPI增速', data: [2.5, 0.9, 2.0, 2.5, 2.3, 2.1] },
  ],
})

const pieChartData = ref([
  { name: '第一产业', value: 1150 },
  { name: '第二产业', value: 12250 },
  { name: '第三产业', value: 23400 },
])

const lineChartOption = ref(createLineChart(lineChartData.value))
const pieChartOption = ref(createPieChart(pieChartData.value))

onMounted(() => {
  // 初始化加载
})
</script>

<style scoped>
.home-page {
  width: 100%;
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

.quick-actions {
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

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.action-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}

.action-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.action-icon {
  color: #667eea;
  margin-bottom: 12px;
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.action-desc {
  font-size: 14px;
  color: #909399;
}

/* 响应式 */
@media (max-width: 767px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
