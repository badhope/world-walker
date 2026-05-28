<template>
  <div class="app-wrapper">
    <header class="app-header">
      <div class="header-left">
        <h1 class="logo">区域产业经济分析平台</h1>
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
      <aside
        :class="{ 'sidebar-collapsed': uiStore.sidebarCollapsed }"
        class="app-sidebar"
        v-if="!uiStore.isMobile"
      >
        <div class="sidebar-content">
          <div class="sidebar-header">
            <h3 v-if="!uiStore.sidebarCollapsed">分析菜单</h3>
            <el-button
              text
              @click="uiStore.toggleSidebar"
            >
              <el-icon>
                <Fold v-if="!uiStore.sidebarCollapsed" />
                <Expand v-else />
              </el-icon>
            </el-button>
          </div>
          <el-menu
            :default-active="activeMenu"
            router
            class="sidebar-menu"
          >
            <el-menu-item index="/">
              <el-icon><DataAnalysis /></el-icon>
              <template #title>概览</template>
            </el-menu-item>
            <el-menu-item index="/enterprise">
              <el-icon><OfficeBuilding /></el-icon>
              <template #title>企业端</template>
            </el-menu-item>
            <el-menu-item index="/government">
        <el-icon><Reading /></el-icon>
        <template #title>政府端</template>
      </el-menu-item>
            <el-menu-item index="/map">
              <el-icon><MapLocation /></el-icon>
              <template #title>产业地图</template>
            </el-menu-item>
            <el-menu-item index="/data">
              <el-icon><FolderOpened /></el-icon>
              <template #title>数据管理</template>
            </el-menu-item>
          </el-menu>
        </div>
      </aside>
      
      <div class="app-content">
        <router-view />
      </div>
    </main>
    
    <footer class="app-footer">
      <p>© 2025 区域产业经济分析平台 | All Rights Reserved.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUIStore } from '@/stores/ui'
import {
  Fold,
  Expand,
  DataAnalysis,
  OfficeBuilding,
  Reading,
  MapLocation,
  FolderOpened,
} from '@element-plus/icons-vue'

const route = useRoute()
const uiStore = useUIStore()

const navItems = [
  { name: '概览', path: '/' },
  { name: '企业端', path: '/enterprise' },
  { name: '政府端', path: '/government' },
  { name: '产业地图', path: '/map' },
  { name: '数据管理', path: '/data' },
]

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 32px;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left .logo {
  font-size: 24px;
  margin: 0;
}

.header-nav {
  display: flex;
  gap: 32px;
}

.nav-item {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s;
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
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 256px;
  background: white;
  border-right: 1px solid #e0e0e0;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
}

.sidebar-collapsed {
  width: 64px;
}

.sidebar-content {
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.sidebar-menu {
  border: none;
}

.app-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.app-footer {
  height: 48px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid #e0e0e0;
  color: #909399;
}

.app-footer p {
  margin: 0;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1199px) {
  .app-sidebar {
    width: 64px;
  }
}

@media (max-width: 767px) {
  .app-header {
    padding: 0 16px;
  }
  .header-left .logo {
    font-size: 18px;
  }
  .header-nav {
    display: none;
  }
}
</style>
