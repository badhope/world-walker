import { request } from '@/utils/request'
import type { 
  BasicData, 
  TrendData, 
  EnterpriseAnalysisResult, 
  GovernmentAnalysisResult,
  AnalysisRequest 
} from '@/types'

// 数据接口
export const dataApi = {
  // 获取基础数据
  getBasicData(): Promise<BasicData> {
    return request.get('/api/v1/data/basic')
  },
  
  // 获取趋势数据
  getTrendData(params: {
    region: string
    industry: string
    startYear: number
    endYear: number
  }): Promise<TrendData> {
    return request.get('/api/v1/data/trend', { params })
  },
  
  // 获取地图数据
  getMapData(params: {
    indicator: string
    year: number
  }) {
    return request.get('/api/v1/data/map', { params })
  },
}

// 分析接口
export const analysisApi = {
  // 企业端分析
  enterprise(data: AnalysisRequest): Promise<EnterpriseAnalysisResult> {
    return request.post('/api/v1/analysis/enterprise', data)
  },
  
  // 政府端分析
  government(data: AnalysisRequest): Promise<GovernmentAnalysisResult> {
    return request.post('/api/v1/analysis/government', data)
  },
  
  // 对比分析
  compare(data: {
    regions: string[]
    industry: string
    year: number
  }) {
    return request.post('/api/v1/analysis/compare', data)
  },
}

// 模型接口
export const inferenceApi = {
  // 运行模型
  runModel(data: {
    model_type: string
    input_data: any
  }) {
    return request.post('/api/v1/inference/model', data)
  },
}

// 交互操作接口
export const interactiveApi = {
  // 导入数据
  importData(data: {
    file_name: string
    file_content: string  // Base64
    format_type: string
    validate?: boolean
  }) {
    return request.post('/api/v1/interactive/import', data)
  },
  
  // 导出数据
  exportData(data: {
    data: any[]
    format_type: string
    file_name?: string
  }) {
    return request.post('/api/v1/interactive/export', data)
  },
  
  // 获取支持格式
  getFormats() {
    return request.get('/api/v1/interactive/formats')
  },
  
  // 获取城市列表
  getCities(params?: {
    province?: string
    tags?: string
    gdp_rank_le?: number
  }) {
    return request.get('/api/v1/interactive/cities', { params })
  },
  
  // 获取城市详情
  getCityDetail(cityCode: string) {
    return request.get(`/api/v1/interactive/cities/${cityCode}`)
  },
  
  // 城市对比分析
  compareCities(data: {
    city_codes: string[]
    year: number
    indicators: string[]
  }) {
    return request.post('/api/v1/interactive/cities/compare', data)
  },
  
  // 指标分析
  analyzeIndicators(data: {
    indicator_code: string
    city_codes: string[]
    start_year: number
    end_year: number
    dimensions?: string[]
  }) {
    return request.post('/api/v1/interactive/indicators/analyze', data)
  },
  
  // 自定义计算
  calculate(data: {
    formula: string
    variables: Record<string, number>
    description?: string
  }) {
    return request.post('/api/v1/interactive/indicators/calculate', data)
  },
  
  // 创建场景
  createScenario(data: {
    name: string
    description?: string
    config: any
    tags?: string[]
  }) {
    return request.post('/api/v1/interactive/scenarios', data)
  },
  
  // 获取场景列表
  getScenarios() {
    return request.get('/api/v1/interactive/scenarios')
  },
  
  // 获取场景详情
  getScenarioDetail(scenarioId: string) {
    return request.get(`/api/v1/interactive/scenarios/${scenarioId}`)
  },
  
  // 清除缓存
  clearCache(pattern?: string) {
    return request.post('/api/v1/interactive/cache/clear', null, {
      params: { pattern: pattern || '*' }
    })
  },
  
  // 获取缓存统计
  getCacheStats() {
    return request.get('/api/v1/interactive/cache/stats')
  },
}

export default {
  ...dataApi,
  ...analysisApi,
  ...inferenceApi,
  ...interactiveApi,
}
