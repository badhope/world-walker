import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import type { EnterpriseAnalysisResult, GovernmentAnalysisResult } from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  // 状态
  const currentRegion = ref('深圳')
  const currentIndustry = ref('半导体')
  const currentYear = ref(2025)
  
  const enterpriseResult = ref<EnterpriseAnalysisResult | null>(null)
  const governmentResult = ref<GovernmentAnalysisResult | null>(null)
  const mapData = ref<any>(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const isReady = computed(() => {
    return enterpriseResult.value !== null || governmentResult.value !== null
  })

  // 动作
  async function fetchEnterpriseAnalysis() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.enterprise({
        region: currentRegion.value,
        industry: currentIndustry.value,
        year: currentYear.value,
      })
      enterpriseResult.value = response as EnterpriseAnalysisResult
    } catch (err: any) {
      error.value = err?.message || '获取企业端分析失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchGovernmentAnalysis() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.government({
        region: currentRegion.value,
        industry: currentIndustry.value,
        year: currentYear.value,
      })
      governmentResult.value = response as GovernmentAnalysisResult
    } catch (err: any) {
      error.value = err?.message || '获取政府端分析失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchMapData(indicator: string) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.getMapData({
        indicator,
        year: currentYear.value,
      })
      mapData.value = response
    } catch (err: any) {
      error.value = err?.message || '获取地图数据失败'
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
    mapData.value = null
    error.value = null
  }

  return {
    // 状态
    currentRegion,
    currentIndustry,
    currentYear,
    enterpriseResult,
    governmentResult,
    mapData,
    loading,
    error,
    
    // 计算属性
    isReady,
    
    // 动作
    fetchEnterpriseAnalysis,
    fetchGovernmentAnalysis,
    fetchMapData,
    setRegion,
    setIndustry,
    setYear,
    reset,
  }
})
