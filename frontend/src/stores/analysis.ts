import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { citiesApi, analysisApi, forecastApi } from '@/api'
import { ElMessage } from 'element-plus'

export const useAnalysisStore = defineStore('analysis', () => {
  const currentRegion = ref('深圳')
  const currentIndustry = ref('半导体')
  const currentYear = ref(2025)

  const cities = ref<string[]>([])
  const cityData = ref<Record<string, any> | null>(null)
  const cityHistorical = ref<any[]>([])
  const enterpriseResult = ref<any>(null)
  const governmentResult = ref<any>(null)
  const comparisonResult = ref<any>(null)
  const forecastResult = ref<any>(null)
  const benchmarks = ref<any>(null)
  const mapData = ref<any>(null)

  const loading = ref(false)
  const error = ref<string | null>(null)

  const isReady = computed(() => {
    return enterpriseResult.value !== null || governmentResult.value !== null
  })

  async function fetchCities() {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.getCities()
      cities.value = response.cities || []
    } catch (err: any) {
      error.value = err?.message || '获取城市列表失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function fetchCityData(cityName: string) {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.getCityDetail(cityName)
      cityData.value = response
    } catch (err: any) {
      error.value = err?.message || '获取城市数据失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function fetchCityHistorical(cityName: string) {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.getCityHistorical(cityName)
      cityHistorical.value = response.historical_data || []
    } catch (err: any) {
      error.value = err?.message || '获取历史数据失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function runEnterpriseAnalysis(cityName?: string) {
    loading.value = true
    error.value = null
    const target = cityName || currentRegion.value
    try {
      const response: any = await analysisApi.enterpriseV3(target)
      enterpriseResult.value = response
    } catch (err: any) {
      error.value = err?.message || '获取企业端分析失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function runGovernmentAnalysis(cityName?: string) {
    loading.value = true
    error.value = null
    const target = cityName || currentRegion.value
    try {
      const response: any = await analysisApi.government({
        region: target,
        industry: currentIndustry.value,
        year: currentYear.value,
      })
      governmentResult.value = response
    } catch (err: any) {
      error.value = err?.message || '获取政府端分析失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function compareCities(cityNames: string[]) {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.compareCities(cityNames)
      comparisonResult.value = response
    } catch (err: any) {
      error.value = err?.message || '城市对比失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function fetchForecast(cityName: string, forecastYears: number = 5) {
    loading.value = true
    error.value = null
    try {
      const response: any = await forecastApi.forecastGdp(cityName, forecastYears)
      forecastResult.value = response
    } catch (err: any) {
      error.value = err?.message || '获取预测数据失败'
      ElMessage.error(error.value!)
    } finally {
      loading.value = false
    }
  }

  async function fetchBenchmarks() {
    try {
      const response: any = await citiesApi.getBenchmarks()
      benchmarks.value = response
    } catch (err: any) {
      ElMessage.error('获取评分基准失败')
    }
  }

  async function fetchCityRankings(params: { indicator?: string; year?: number; limit?: number }) {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.getCityRankings(params)
      return response
    } catch (err: any) {
      error.value = err?.message || '获取排名数据失败'
      ElMessage.error(error.value!)
      return null
    } finally {
      loading.value = false
    }
  }

  async function aggregateData(data: {
    group_by: string[]
    metrics: string[]
    filters?: Record<string, any>
    sort_by?: string
    sort_order?: string
    limit?: number
  }) {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.aggregateData(data)
      return response
    } catch (err: any) {
      error.value = err?.message || '聚合分析失败'
      ElMessage.error(error.value!)
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
  }) {
    loading.value = true
    error.value = null
    try {
      const response: any = await citiesApi.timeSeriesAnalysis(data)
      return response
    } catch (err: any) {
      error.value = err?.message || '时间序列分析失败'
      ElMessage.error(error.value!)
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
