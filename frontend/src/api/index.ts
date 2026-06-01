import { request } from '@/utils/request'

export const citiesApi = {
  getCities() {
    return request.get('/api/v1/cities/list')
  },

  getCityDetail(cityName: string) {
    return request.get(`/api/v1/cities/${cityName}`)
  },

  getCityHistorical(cityName: string) {
    return request.get(`/api/v1/cities/${cityName}/historical`)
  },

  compareCities(cityNames: string[]) {
    return request.post('/api/v1/cities/compare', cityNames)
  },

  getBenchmarks() {
    return request.get('/api/v1/cities/benchmarks/scores')
  },

  getCityRankings(params: { indicator?: string; year?: number; limit?: number }) {
    return request.get('/api/v1/cities/rankings', { params })
  },

  aggregateData(data: {
    group_by: string[]
    metrics: string[]
    filters?: Record<string, unknown>
    sort_by?: string
    sort_order?: string
    limit?: number
  }) {
    return request.post('/api/v1/cities/aggregate', data)
  },

  timeSeriesAnalysis(data: {
    city_codes: string[]
    indicator: string
    year_start: number
    year_end: number
    group_by?: string[]
  }) {
    return request.post('/api/v1/cities/time-series', data)
  },

  regionalAnalysis(data: {
    region_field?: string
    indicators?: string[]
  }) {
    return request.post('/api/v1/cities/regional', data)
  },
}

export const analysisApi = {
  enterpriseV3(cityName: string) {
    return request.get(`/api/v1/analysis/enterprise/v3/${cityName}`)
  },

  enterpriseV3Compare(cityNames: string[]) {
    return request.post('/api/v1/analysis/enterprise/v3/compare', cityNames)
  },

  enterpriseV2(data: {
    region: string
    industry: string
    year: number
    data?: Record<string, unknown>
  }) {
    return request.post('/api/v1/analysis/enterprise/v2', data)
  },

  government(data: {
    region: string
    industry: string
    year: number
  }) {
    return request.post('/api/v1/analysis/government', data)
  },

  getAnalysisConfig() {
    return request.get('/api/v1/analysis/config')
  },
}

export const forecastApi = {
  forecastGdp(cityName: string, forecastYears: number = 5) {
    return request.get(`/api/v1/forecast/gdp/${cityName}`, { params: { forecast_years: forecastYears } })
  },

  compareForecasts(cityNames: string[], forecastYears: number = 5) {
    return request.post('/api/v1/forecast/compare', cityNames, { params: { forecast_years: forecastYears } })
  },

  getFullReport() {
    return request.get('/api/v1/forecast/report/full')
  },
}

export const interactiveApi = {
  importData(data: {
    file_name: string
    file_content: string
    format_type: string
    validate?: boolean
  }) {
    return request.post('/api/v1/interactive/import', data)
  },

  exportData(data: {
    data: Record<string, unknown>[]
    format_type: string
    file_name?: string
  }) {
    return request.post('/api/v1/interactive/export', data)
  },

  getFormats() {
    return request.get('/api/v1/interactive/formats')
  },

  getCities(params?: {
    province?: string
    tags?: string
    gdp_rank_le?: number
  }) {
    return request.get('/api/v1/interactive/cities', { params })
  },

  getCityDetail(cityCode: string) {
    return request.get(`/api/v1/interactive/cities/${cityCode}`)
  },

  compareCities(data: {
    city_codes: string[]
    year: number
    indicators: string[]
  }) {
    return request.post('/api/v1/interactive/cities/compare', data)
  },

  analyzeIndicators(data: {
    indicator_code: string
    city_codes: string[]
    start_year: number
    end_year: number
    dimensions?: string[]
  }) {
    return request.post('/api/v1/interactive/indicators/analyze', data)
  },

  calculate(data: {
    formula: string
    variables: Record<string, number>
    description?: string
  }) {
    return request.post('/api/v1/interactive/indicators/calculate', data)
  },

  createScenario(data: {
    name: string
    description?: string
    config: Record<string, unknown>
    tags?: string[]
  }) {
    return request.post('/api/v1/interactive/scenarios', data)
  },

  getScenarios() {
    return request.get('/api/v1/interactive/scenarios')
  },

  getScenarioDetail(scenarioId: string) {
    return request.get(`/api/v1/interactive/scenarios/${scenarioId}`)
  },

  clearCache(pattern?: string) {
    return request.post('/api/v1/interactive/cache/clear', null, {
      params: { pattern: pattern || '*' }
    })
  },

  getCacheStats() {
    return request.get('/api/v1/interactive/cache/stats')
  },
}

export const healthApi = {
  check() {
    return request.get('/health')
  },
}

export default {
  ...citiesApi,
  ...analysisApi,
  ...forecastApi,
  ...interactiveApi,
  ...healthApi,
}
