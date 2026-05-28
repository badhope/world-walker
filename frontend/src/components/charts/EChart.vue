<template>
  <div 
    ref="chartContainer"
    :style="{ width: '100%', height: height }"
  />
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import type { EChartsOption, ECharts } from 'echarts'

interface Props {
  option: EChartsOption
  height?: string
  theme?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  theme: 'light',
})

const chartContainer = ref<HTMLElement>()
let chartInstance: ECharts | null = null

const initChart = () => {
  if (!chartContainer.value) return
  
  chartInstance = echarts.init(chartContainer.value, props.theme)
  chartInstance.setOption(props.option)
  
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  chartInstance?.resize()
}

const updateOption = (newOption: EChartsOption) => {
  chartInstance?.setOption(newOption, { notMerge: false })
}

watch(() => props.option, updateOption, { deep: true })

onMounted(initChart)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

defineExpose({
  getInstance: () => chartInstance,
  updateOption,
})
</script>

<style scoped></style>
