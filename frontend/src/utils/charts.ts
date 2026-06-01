import type { EChartsOption } from 'echarts'

// 图表预设 - 折线图
export function createLineChart(data: {
  categories: string[]
  series: { name: string; data: number[] }[]
}): EChartsOption {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      top: 0,
      data: data.series.map((s) => s.name),
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.categories,
    },
    yAxis: {
      type: 'value',
    },
    series: data.series.map((s) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data,
      areaStyle: {
        opacity: 0.3,
      },
    })),
  }
}

// 图表预设 - 柱状图
export function createBarChart(data: {
  categories: string[]
  series: { name: string; data: number[] }[]
}): EChartsOption {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      top: 0,
      data: data.series.map((s) => s.name),
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.categories,
    },
    yAxis: {
      type: 'value',
    },
    series: data.series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
    })),
  }
}

// 图表预设 - 饼图
export function createPieChart(data: {
  name: string
  value: number
}[]): EChartsOption {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data,
      },
    ],
  }
}

// 图表预设 - 雷达图
export function createRadarChart(data: {
  indicator: { name: string; max: number }[]
  data: { name: string; value: number[] }[]
}): EChartsOption {
  return {
    tooltip: {},
    legend: {
      data: data.data.map((d) => d.name),
    },
    radar: {
      indicator: data.indicator,
    },
    series: [
      {
        name: '综合评分',
        type: 'radar',
        data: data.data,
      },
    ],
  }
}

// 图表预设 - KPI 卡片图
export function createKpiChart(value: number, name: string, unit?: string): EChartsOption {
  return {
    series: [
      {
        type: 'gauge',
        startAngle: 90,
        endAngle: -270,
        pointer: {
          show: false,
        },
        progress: {
          show: true,
          overlap: false,
          roundCap: true,
          clip: false,
          itemStyle: {
            color: '#667eea',
          },
        },
        axisLine: {
          lineStyle: {
            width: 40,
            color: [[1, '#e0e0e0']],
          },
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        data: [{ value: Math.min(value, 100) }],
        title: {
          fontSize: 14,
          offsetCenter: [0, 40],
          formatter: name,
        },
        detail: {
          fontSize: 36,
          offsetCenter: [0, 0],
          formatter: '{value}' + (unit || ''),
          color: '#667eea',
        },
      },
    ],
  }
}
