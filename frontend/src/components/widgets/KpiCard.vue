<template>
  <div class="kpi-card">
    <div class="kpi-content">
      <div class="kpi-value" :style="{ color: color }">{{ value }}{{ unit }}</div>
      <div class="kpi-label">{{ label }}</div>
    </div>
    <div class="kpi-icon" :style="{ backgroundColor: bgColor }">
      <component :is="icon" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { h, computed } from 'vue'
import { TrendCharts, DataLine, Wallet, User, Box, Goods } from '@element-plus/icons-vue'

interface Props {
  value: string | number
  label: string
  unit?: string
  color?: string
  bgColor?: string
  iconType?: 'trend' | 'data' | 'wallet' | 'user' | 'box' | 'goods'
}

const props = withDefaults(defineProps<Props>(), {
  unit: '',
  color: '#303133',
  bgColor: '#667eea',
  iconType: 'trend',
})

const iconMap = {
  trend: h(TrendCharts),
  data: h(DataLine),
  wallet: h(Wallet),
  user: h(User),
  box: h(Box),
  goods: h(Goods),
}

const icon = computed(() => iconMap[props.iconType])
</script>

<style scoped>
.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-content {
  flex: 1;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.kpi-label {
  font-size: 14px;
  color: #909399;
}

.kpi-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}
</style>
