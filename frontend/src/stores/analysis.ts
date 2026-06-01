import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { citiesApi, analysisApi, forecastApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { EnterpriseResult, GovernmentResult, CityRankingsResponse, AggregationResponse, TimeSeriesResponse } from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  const currentRegion = ref('深圳')
  const currentIndustry = ref('半导体')
  const currentYear = ref(2025)

  const cities = ref<string[]>([])
  const cityData = ref<Record<string, unknown> | null>(null)
  const cityHistorical = ref<Record<string, unknown>[]>([])
  const enterpriseResult = ref<EnterpriseResult | null>(null)
  const governmentResult = ref<GovernmentResult | null>(null)
  const comparisonResult = ref<unknown>(null)
  const forecastResult = ref<unknown>(null)
  const benchmarks = ref<unknown>(null)
  const mapData = ref<unknown>(null)

  const loading = ref(false)
  const error = ref<string | null>(null)

  const isReady = computed(() => {
    return enterpriseResult.value !== null || governmentResult.value !== null
  })

  async function fetchCities() {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.getCities() as { cities?: string[] }
      cities.value = response.cities || []
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取城市列表失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function fetchCityData(cityName: string) {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.getCityDetail(cityName) as Record<string, unknown>
      cityData.value = response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取城市数据失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function fetchCityHistorical(cityName: string) {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.getCityHistorical(cityName) as { historical_data?: Record<string, unknown>[] }
      cityHistorical.value = response.historical_data || []
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取历史数据失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function runEnterpriseAnalysis(cityName?: string) {
    loading.value = true
    error.value = null
    const target = cityName || currentRegion.value
    try {
      const response = await analysisApi.enterpriseV3(target) as EnterpriseResult
      enterpriseResult.value = response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取企业端分析失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function runGovernmentAnalysis(cityName?: string) {
    loading.value = true
    error.value = null
    const target = cityName || currentRegion.value
    try {
      const response = await analysisApi.government({
        region: target,
        industry: currentIndustry.value,
        year: currentYear.value,
      }) as GovernmentResult
      governmentResult.value = response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取政府端分析失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function compareCities(cityNames: string[]) {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.compareCities(cityNames) as unknown
      comparisonResult.value = response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '城市对比失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function fetchForecast(cityName: string, forecastYears: number = 5) {
    loading.value = true
    error.value = null
    try {
      const response = await forecastApi.forecastGdp(cityName, forecastYears) as unknown
      forecastResult.value = response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取预测数据失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function fetchBenchmarks() {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.getBenchmarks() as unknown
      benchmarks.value = response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取评分基准失败'
      error.value = message
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  }

  async function fetchCityRankings(params: { indicator?: string; year?: number; limit?: number }): Promise<CityRankingsResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.getCityRankings(params) as CityRankingsResponse
      return response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取排名数据失败'
      error.value = message
      ElMessage.error(message)
      return null
    } finally {
      loading.value = false
    }
  }

  async function aggregateData(data: {
    group_by: string[]
    metrics: string[]
    filters?: Record<string, unknown>
    sort_by?: string
    sort_order?: string
    limit?: number
  }): Promise<AggregationResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.aggregateData(data) as AggregationResponse
      return response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '聚合分析失败'
      error.value = message
      ElMessage.error(message)
      return null
    } finally {
      loading.value = false
    }
  }

  async function timeSeriesAnalysis(data: {
    city_codes: string[]
    indicator: string
    year_start: number
    year_end: number
    group_by?: string[]
  }): Promise<TimeSeriesResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await citiesApi.timeSeriesAnalysis(data) as TimeSeriesResponse
      return response
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '时间序列分析失败'
      error.value = message
      ElMessage.error(message)
      return null
    } finally {
      loading.value = false
    }
  }

  function setRegion(region: string) {
    currentRegion.value = region
  }

  function setIndustry(industry: string) {
    currentIndustry.value = industry
  }

  function setYear(year: number) {
    currentYear.value = year
  }

  function reset() {
    enterpriseResult.value = null
    governmentResult.value = null
    comparisonResult.value = null
    forecastResult.value = null
    cityData.value = null
    cityHistorical.value = []
    mapData.value = null
    error.value = null
  }

  return {
    currentRegion,
    currentIndustry,
    currentYear,
    cities,
    cityData,
    cityHistorical,
    enterpriseResult,
    governmentResult,
    comparisonResult,
    forecastResult,
    benchmarks,
    mapData,
    loading,
    error,
    isReady,
    fetchCities,
    fetchCityData,
    fetchCityHistorical,
    runEnterpriseAnalysis,
    runGovernmentAnalysis,
    compareCities,
    fetchForecast,
    fetchBenchmarks,
    fetchCityRankings,
    aggregateData,
    timeSeriesAnalysis,
    setRegion,
    setIndustry,
    setYear,
    reset,
  }
})