<template>
  <div class="data-page">
    <!-- 顶部操作栏 -->
    <div class="top-actions">
      <el-button type="primary" @click="handleUpload">
        <el-icon><Upload /></el-icon>
        上传数据
      </el-button>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon>
        导出数据
      </el-button>
    </div>
    
    <!-- 内容区域 -->
    <div class="data-content">
      <!-- 左侧筛选 -->
      <div class="data-sidebar">
        <div class="sidebar-card">
          <h3 class="sidebar-title">数据筛选</h3>
          
          <div class="filter-group">
            <label>数据类型</label>
            <el-select v-model="filters.type" placeholder="请选择" clearable>
              <el-option label="宏观经济" value="macro" />
              <el-option label="产业数据" value="industry" />
              <el-option label="财政数据" value="finance" />
            </el-select>
          </div>
          
          <div class="filter-group">
            <label>区域</label>
            <el-select v-model="filters.region" placeholder="请选择" clearable>
              <el-option label="深圳" value="深圳" />
              <el-option label="上海" value="上海" />
              <el-option label="北京" value="北京" />
            </el-select>
          </div>
          
          <div class="filter-group">
            <label>年份范围</label>
            <el-date-picker
              v-model="filters.years"
              type="yearrange"
              range-separator="至"
              start-placeholder="开始"
              end-placeholder="结束"
              format="YYYY"
              value-format="YYYY"
            />
          </div>
          
          <el-button type="primary" @click="handleFilter" style="width: 100%">
            筛选
          </el-button>
        </div>
      </div>
      
      <!-- 右侧表格 -->
      <div class="data-main">
        <el-card>
          <el-table
            :data="tableData"
            style="width: 100%"
            stripe
            border
          >
            <el-table-column
              prop="year"
              label="年份"
              width="120"
            />
            <el-table-column
              prop="region"
              label="区域"
              width="120"
            />
            <el-table-column
              prop="indicator"
              label="指标"
              width="150"
            />
            <el-table-column
              prop="value"
              label="数值"
              width="150"
            />
            <el-table-column
              prop="unit"
              label="单位"
              width="100"
            />
            <el-table-column
              prop="source"
              label="来源"
            />
            <el-table-column
              label="操作"
              width="180"
            >
              <template #default="{ row }">
                <el-button link type="primary" size="small">编辑</el-button>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
            />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Upload, Download } from '@element-plus/icons-vue'

const filters = ref({
  type: '',
  region: '',
  years: [],
})

const tableData = ref([
  {
    year: '2025',
    region: '深圳',
    indicator: 'GDP',
    value: '36801.87',
    unit: '亿元',
    source: '国家统计局',
  },
  {
    year: '2025',
    region: '深圳',
    indicator: '半导体产业产值',
    value: '12000',
    unit: '亿元',
    source: '深圳统计局',
  },
  {
    year: '2024',
    region: '深圳',
    indicator: 'GDP',
    value: '32800',
    unit: '亿元',
    source: '国家统计局',
  },
])

const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(3)

const handleUpload = () => {
  // 上传逻辑
}

const handleExport = () => {
  // 导出逻辑
}

const handleFilter = () => {
  // 筛选逻辑
}
</script>

<style scoped>
.data-page {
  width: 100%;
  height: 100%;
}

.top-actions {
  background: white;
  border-radius: 12px;
  padding: 16px 24px;
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.data-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.data-sidebar {
  display: flex;
  flex-direction: column;
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
  margin-bottom: 20px;
}

.filter-group {
  margin-bottom: 20px;
}

.filter-group label {
  display: block;
  color: #606266;
  font-weight: 500;
  margin-bottom: 8px;
}

.filter-group .el-select {
  width: 100%;
}

.data-main {
  background: white;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式 */
@media (max-width: 1199px) {
  .data-content {
    grid-template-columns: 1fr;
  }
  .data-sidebar {
    max-width: 100%;
  }
}
</style>
