<template>
  <div class="data-page">
    <!-- 顶部操作栏 -->
    <div class="top-actions">
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传数据
      </el-button>
      <el-button @click="showExportDialog = true">
        <el-icon><Download /></el-icon>
        导出数据
      </el-button>
      <el-button @click="loadData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button @click="showCitiesDialog = true">
        <el-icon><Location /></el-icon>
        城市对比
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
              <el-option label="广州" value="广州" />
              <el-option label="杭州" value="杭州" />
              <el-option label="武汉" value="武汉" />
              <el-option label="成都" value="成都" />
              <el-option label="南京" value="南京" />
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
          
          <div class="filter-group">
            <label>搜索关键词</label>
            <el-input
              v-model="filters.keyword"
              placeholder="搜索指标名称"
              clearable
            />
          </div>
          
          <el-button type="primary" @click="handleFilter" style="width: 100%">
            应用筛选
          </el-button>
          <el-button @click="resetFilters" style="width: 100%; margin-top: 10px">
            重置筛选
          </el-button>
        </div>
        
        <!-- 数据统计 -->
        <div class="sidebar-card" style="margin-top: 20px">
          <h3 class="sidebar-title">数据统计</h3>
          <div class="stat-item">
            <span class="stat-label">总记录数</span>
            <span class="stat-value">{{ total }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">当前页</span>
            <span class="stat-value">{{ currentPage }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">每页条数</span>
            <span class="stat-value">{{ pageSize }}</span>
          </div>
        </div>
      </div>
      
      <!-- 右侧表格 -->
      <div class="data-main">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据列表</span>
              <el-tag type="info">{{ filteredData.length }} 条记录</el-tag>
            </div>
          </template>
          
          <el-table
            :data="paginatedData"
            style="width: 100%"
            stripe
            border
            v-loading="loading"
          >
            <el-table-column
              prop="year"
              label="年份"
              width="100"
              sortable
            />
            <el-table-column
              prop="quarter"
              label="季度"
              width="80"
              v-if="showQuarter"
            />
            <el-table-column
              prop="region"
              label="区域"
              width="120"
            />
            <el-table-column
              prop="indicator"
              label="指标"
              min-width="180"
              show-overflow-tooltip
            />
            <el-table-column
              prop="value"
              label="数值"
              width="150"
              sortable
            >
              <template #default="{ row }">
                <span class="value-cell">
                  {{ formatNumber(row.value) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column
              prop="unit"
              label="单位"
              width="100"
            />
            <el-table-column
              prop="source"
              label="来源"
              width="120"
              show-overflow-tooltip
            />
            <el-table-column
              label="操作"
              width="180"
              fixed="right"
            >
              <template #default="{ row, $index }">
                <el-button link type="primary" size="small" @click="viewDetail(row)">
                  详情
                </el-button>
                <el-button link type="primary" size="small" @click="editRow(row)">
                  编辑
                </el-button>
                <el-button link type="danger" size="small" @click="deleteRow(row, $index)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="filteredData.length"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传数据"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="文件格式">
          <el-select v-model="uploadForm.format" placeholder="选择格式">
            <el-option label="JSON" value="json" />
            <el-option label="CSV" value="csv" />
            <el-option label="Excel" value="xlsx" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".json,.csv,.xlsx,.xls"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 JSON、CSV、Excel 格式
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="验证数据">
          <el-switch v-model="uploadForm.validate" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出数据"
      width="500px"
    >
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式">
          <el-select v-model="exportForm.format" placeholder="选择格式">
            <el-option label="JSON" value="json" />
            <el-option label="CSV" value="csv" />
            <el-option label="Excel" value="xlsx" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="文件名">
          <el-input v-model="exportForm.filename" placeholder="输入文件名" />
        </el-form-item>
        
        <el-form-item label="导出范围">
          <el-radio-group v-model="exportForm.range">
            <el-radio label="current">当前页</el-radio>
            <el-radio label="filtered">筛选结果</el-radio>
            <el-radio label="all">全部数据</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="exporting">
          导出
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 城市对比对话框 -->
    <el-dialog
      v-model="showCitiesDialog"
      title="城市对比分析"
      width="800px"
    >
      <el-form :model="cityForm" label-width="120px">
        <el-form-item label="选择城市">
          <el-select
            v-model="cityForm.cities"
            multiple
            placeholder="选择城市"
            style="width: 100%"
          >
            <el-option
              v-for="city in availableCities"
              :key="city.code"
              :label="city.name"
              :value="city.code"
            >
              <span>{{ city.name }}</span>
              <span style="float: right; color: #999; font-size: 12px">
                {{ city.province }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择年份">
          <el-date-picker
            v-model="cityForm.year"
            type="year"
            placeholder="选择年份"
            format="YYYY"
            value-format="YYYY"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="选择指标">
          <el-select
            v-model="cityForm.indicators"
            multiple
            placeholder="选择指标"
            style="width: 100%"
          >
            <el-option label="GDP" value="gdp" />
            <el-option label="CPI" value="cpi" />
            <el-option label="PMI" value="pmi" />
            <el-option label="财政收入" value="fiscal_revenue" />
            <el-option label="工业产值" value="industrial_output" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCitiesDialog = false">取消</el-button>
        <el-button type="primary" @click="compareCities" :loading="comparing">
          开始对比
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 数据详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="数据详情"
      width="600px"
    >
      <el-descriptions :column="2" border v-if="selectedRow">
        <el-descriptions-item label="年份">{{ selectedRow.year }}</el-descriptions-item>
        <el-descriptions-item label="季度">{{ selectedRow.quarter || '-' }}</el-descriptions-item>
        <el-descriptions-item label="区域">{{ selectedRow.region }}</el-descriptions-item>
        <el-descriptions-item label="指标">{{ selectedRow.indicator }}</el-descriptions-item>
        <el-descriptions-item label="数值" :span="2">
          {{ formatNumber(selectedRow.value) }} {{ selectedRow.unit }}
        </el-descriptions-item>
        <el-descriptions-item label="来源" :span="2">{{ selectedRow.source }}</el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">
          {{ selectedRow.updateTime || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="editRow(selectedRow)">编辑</el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑数据"
      width="600px"
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="年份">
          <el-input v-model.number="editForm.year" type="number" />
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="editForm.region" />
        </el-form-item>
        <el-form-item label="指标">
          <el-input v-model="editForm.indicator" />
        </el-form-item>
        <el-form-item label="数值">
          <el-input v-model.number="editForm.value" type="number" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="editForm.unit" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Refresh, Location } from '@element-plus/icons-vue'
import { interactiveApi } from '@/api'

// 状态
const loading = ref(false)
const uploading = ref(false)
const exporting = ref(false)
const comparing = ref(false)
const showQuarter = ref(false)

// 筛选
const filters = ref({
  type: '',
  region: '',
  years: [],
  keyword: '',
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = computed(() => filteredData.value.length)

// 数据
const tableData = ref<any[]>([])
const filteredData = computed(() => {
  let data = [...tableData.value]
  
  if (filters.value.type) {
    data = data.filter(item => item.type === filters.value.type)
  }
  
  if (filters.value.region) {
    data = data.filter(item => item.region === filters.value.region)
  }
  
  if (filters.value.years && filters.value.years.length === 2) {
    const [start, end] = filters.value.years
    data = data.filter(item => {
      const year = String(item.year)
      return year >= start && year <= end
    })
  }
  
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    data = data.filter(item => 
      item.indicator?.toLowerCase().includes(keyword) ||
      item.region?.toLowerCase().includes(keyword)
    )
  }
  
  return data
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

// 上传相关
const showUploadDialog = ref(false)
const uploadForm = ref({
  format: 'json',
  validate: true,
})
const fileList = ref<any[]>([])
const uploadRef = ref()

// 导出相关
const showExportDialog = ref(false)
const exportForm = ref({
  format: 'json',
  filename: '',
  range: 'filtered',
})

// 城市对比
const showCitiesDialog = ref(false)
const cityForm = ref({
  cities: [],
  year: '2024',
  indicators: ['gdp'],
})
const availableCities = ref<any[]>([])

// 详情和编辑
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const selectedRow = ref<any>(null)
const editForm = ref<any>({})

// 方法
const loadData = async () => {
  loading.value = true
  try {
    // 模拟加载数据
    tableData.value = [
      {
        year: '2025',
        quarter: 'Q1',
        region: '深圳',
        indicator: 'GDP',
        value: 36801.87,
        unit: '亿元',
        source: '国家统计局',
        updateTime: '2025-03-15',
      },
      {
        year: '2025',
        region: '深圳',
        indicator: '半导体产业产值',
        value: 12000,
        unit: '亿元',
        source: '深圳统计局',
        updateTime: '2025-03-15',
      },
      {
        year: '2024',
        region: '深圳',
        indicator: 'GDP',
        value: 32800,
        unit: '亿元',
        source: '国家统计局',
        updateTime: '2024-12-31',
      },
    ]
    ElMessage.success('数据加载成功')
  } catch (error) {
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  currentPage.value = 1
  ElMessage.success('筛选已应用')
}

const resetFilters = () => {
  filters.value = {
    type: '',
    region: '',
    years: [],
    keyword: '',
  }
  currentPage.value = 1
  ElMessage.success('筛选已重置')
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

const formatNumber = (value: number) => {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

const viewDetail = (row: any) => {
  selectedRow.value = row
  showDetailDialog.value = true
}

const editRow = (row: any) => {
  editForm.value = { ...row }
  showEditDialog.value = true
  showDetailDialog.value = false
}

const saveEdit = () => {
  // 模拟保存
  const index = tableData.value.findIndex(item => item === selectedRow.value)
  if (index !== -1) {
    tableData.value[index] = { ...editForm.value }
    ElMessage.success('保存成功')
    showEditDialog.value = false
  }
}

const deleteRow = async (row: any, index: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    tableData.value.splice(index, 1)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

const handleFileChange = (file: any) => {
  fileList.value = [file]
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    const file = fileList.value[0].raw
    const reader = new FileReader()
    
    reader.onload = async (e) => {
      const content = btoa(e.target?.result as string)
      
      await interactiveApi.importData({
        file_name: file.name,
        file_content: content,
        format_type: uploadForm.value.format,
        validate: uploadForm.value.validate,
      })
      
      ElMessage.success('数据上传成功')
      showUploadDialog.value = false
      loadData()
    }
    
    reader.readAsText(file)
  } catch (error) {
    ElMessage.error('数据上传失败')
  } finally {
    uploading.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    let dataToExport: any[] = []
    
    switch (exportForm.value.range) {
      case 'current':
        dataToExport = paginatedData.value
        break
      case 'filtered':
        dataToExport = filteredData.value
        break
      case 'all':
        dataToExport = tableData.value
        break
    }
    
    const result = await interactiveApi.exportData({
      data: dataToExport,
      format_type: exportForm.value.format,
      file_name: exportForm.value.filename || undefined,
    })
    
    // 下载文件
    const link = document.createElement('a')
    link.href = `data:application/octet-stream;base64,${result.file_content}`
    link.download = result.file_name
    link.click()
    
    ElMessage.success('数据导出成功')
    showExportDialog.value = false
  } catch (error) {
    ElMessage.error('数据导出失败')
  } finally {
    exporting.value = false
  }
}

const loadCities = async () => {
  try {
    const result = await interactiveApi.getCities()
    availableCities.value = result.cities
  } catch (error) {
    console.error('加载城市列表失败', error)
  }
}

const compareCities = async () => {
  if (cityForm.value.cities.length < 2) {
    ElMessage.warning('请至少选择两个城市进行对比')
    return
  }
  
  comparing.value = true
  try {
    await interactiveApi.compareCities({
      city_codes: cityForm.value.cities,
      year: parseInt(cityForm.value.year),
      indicators: cityForm.value.indicators,
    })
    
    ElMessage.success('城市对比分析完成')
    showCitiesDialog.value = false
  } catch (error) {
    ElMessage.error('城市对比分析失败')
  } finally {
    comparing.value = false
  }
}

// 生命周期
onMounted(() => {
  loadData()
  loadCities()
})
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

.filter-group .el-select,
.filter-group .el-input {
  width: 100%;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #606266;
}

.stat-value {
  color: #303133;
  font-weight: 600;
}

.data-main {
  background: white;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.value-cell {
  font-weight: 600;
  color: #409eff;
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
