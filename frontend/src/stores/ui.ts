import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // 侧边栏状态
  const sidebarCollapsed = ref(false)
  
  // 当前路由
  const activeRoute = ref('/')
  
  // 主题设置
  const theme = ref<'light' | 'dark'>('light')
  
  // 计算属性
  const isMobile = computed(() => {
    return window.innerWidth < 768
  })

  // 动作
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed: boolean) {
    sidebarCollapsed.value = collapsed
  }

  function setActiveRoute(route: string) {
    activeRoute.value = route
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return {
    sidebarCollapsed,
    activeRoute,
    theme,
    isMobile,
    toggleSidebar,
    setSidebarCollapsed,
    setActiveRoute,
    toggleTheme,
  }
})
