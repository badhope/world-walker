<template>
  <div class="app-wrapper">
    <header class="app-header">
      <div class="header-left">
        <h1 class="logo">🌐 产业经济分析平台</h1>
      </div>
      <nav class="header-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          {{ item.name }}
        </router-link>
      </nav>
    </header>
    
    <main class="app-main">
      <router-view />
    </main>
    
    <footer class="app-footer">
      <p>© 2025 区域产业经济分析平台 | All Rights Reserved.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { name: '🏠 首页', path: '/' },
  { name: '🏢 企业端', path: '/enterprise' },
  { name: '🏛️ 政府端', path: '/government' },
  { name: '🗺️ 产业地图', path: '/map' },
  { name: '📁 数据管理', path: '/data' },
  { name: '🏙️ 城市对比', path: '/cities' },
  { name: '🔧 测试', path: '/test' },
]

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f0f2f5;
  width: 100%;
  overflow-x: hidden;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  padding: 0 32px;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
  overflow: hidden;
}

.header-left .logo {
  font-size: 20px;
  margin: 0;
  font-weight: 700;
  white-space: nowrap;
}

.header-nav {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.nav-item {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.3s;
  white-space: nowrap;
}

.nav-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.15);
}

.nav-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.25);
}

.app-main {
  flex: 1;
  padding: 0;
  overflow-x: hidden;
  width: 100%;
}

.app-footer {
  height: 48px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid #e0e0e0;
  color: #909399;
  flex-shrink: 0;
}

.app-footer p {
  margin: 0;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .app-header {
    padding: 0 16px;
  }
  
  .header-nav {
    gap: 4px;
  }
  
  .nav-item {
    padding: 6px 10px;
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    height: auto;
    padding: 12px 16px;
    gap: 12px;
  }
  
  .header-left .logo {
    font-size: 16px;
    text-align: center;
  }
  
  .header-nav {
    width: 100%;
    justify-content: center;
  }
  
  .nav-item {
    font-size: 12px;
    padding: 6px 8px;
  }
}
</style>
