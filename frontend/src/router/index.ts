import { createRouter, createWebHistory, type RouteRecordRaw, type RouteLocationNormalized, type NavigationGuardNext } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/enterprise',
    name: 'Enterprise',
    component: () => import('@/views/Enterprise.vue'),
    meta: { title: '企业端分析' },
  },
  {
    path: '/government',
    name: 'Government',
    component: () => import('@/views/Government.vue'),
    meta: { title: '政府端分析' },
  },
  {
    path: '/map',
    name: 'Map',
    component: () => import('@/views/Map.vue'),
    meta: { title: '产业地图' },
  },
  {
    path: '/data',
    name: 'Data',
    component: () => import('@/views/DataManager.vue'),
    meta: { title: '数据管理' },
  },
  {
    path: '/cities',
    name: 'Cities',
    component: () => import('@/views/CityComparison.vue'),
    meta: { title: '城市对比' },
  },
  {
    path: '/test',
    name: 'Test',
    component: () => import('@/views/Test.vue'),
    meta: { title: 'API测试' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to: RouteLocationNormalized, _from: RouteLocationNormalized, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

router.beforeEach((to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
  document.title = to.meta.title ? `${to.meta.title} - 区域产业经济分析平台` : '区域产业经济分析平台'
  next()
})

export default router