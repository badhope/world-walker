<template>
  <div class="test-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>API 测试页面</span>
        </div>
      </template>
      
      <div class="test-content">
        <h3>测试说明</h3>
        <p>这个页面用于测试前后端API连接是否正常。</p>
        
        <el-divider />
        
        <div class="test-section">
          <h4>1. 测试后端连接</h4>
          <el-button @click="testBackendHealth" :loading="testing">
            测试健康检查
          </el-button>
          <div v-if="healthResult" class="result-box">
            <pre>{{ healthResult }}</pre>
          </div>
        </div>
        
        <el-divider />
        
        <div class="test-section">
          <h4>2. 测试企业端分析API</h4>
          <el-button @click="testEnterpriseAPI" :loading="testing">
            调用企业端分析
          </el-button>
          <div v-if="enterpriseResult" class="result-box">
            <pre>{{ enterpriseResult }}</pre>
          </div>
        </div>
        
        <el-divider />
        
        <div class="test-section">
          <h4>3. 错误状态</h4>
          <p>如果以上测试都失败，请检查：</p>
          <ul>
            <li>后端服务器是否正在运行（端口8000）</li>
            <li>前端代理配置是否正确</li>
            <li>网络连接是否正常</li>
          </ul>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const testing = ref(false)
const healthResult = ref('')
const enterpriseResult = ref('')

const testBackendHealth = async () => {
  testing.value = true
  healthResult.value = ''
  
  try {
    const response = await fetch('/api/v1/health')
    const data = await response.json()
    healthResult.value = JSON.stringify(data, null, 2)
    ElMessage.success('健康检查成功！')
  } catch (error) {
    healthResult.value = `错误: ${error}`
    ElMessage.error('健康检查失败')
  } finally {
    testing.value = false
  }
}

const testEnterpriseAPI = async () => {
  testing.value = true
  enterpriseResult.value = ''
  
  try {
    const response = await fetch('/api/v1/analysis/enterprise', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        region: '深圳',
        industry: '半导体',
        year: 2025,
      }),
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    enterpriseResult.value = JSON.stringify(data, null, 2)
    ElMessage.success('企业端分析API测试成功！')
  } catch (error) {
    enterpriseResult.value = `错误: ${error}`
    ElMessage.error('企业端分析API测试失败')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.test-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.test-content h3 {
  color: #303133;
  margin-bottom: 12px;
}

.test-content h4 {
  color: #606266;
  margin-bottom: 12px;
}

.test-content p {
  color: #909399;
  line-height: 1.6;
}

.test-section {
  margin: 20px 0;
}

.result-box {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  max-height: 300px;
  overflow: auto;
}

.result-box pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
