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

export default {
  ...dataApi,
  ...analysisApi,
  ...inferenceApi,
}
