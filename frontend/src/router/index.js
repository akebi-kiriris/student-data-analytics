import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import DataManagementView from '../views/DataManagementView.vue'
import AnalysisView from '../views/AnalysisView.vue'
// 延遲導入 authService 避免循環依賴
// import { authService } from '../services/auth.js'
// 暫時隱藏用戶管理頁面導入
// import UserManagementView from '../views/UserManagementView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../App.vue'),
    meta: {
      title: '數據分析 - 學生資料分析系統'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: {
      title: '登入 - 學生資料分析系統'
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: {
      title: '註冊 - 學生資料分析系統'
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: {
      title: '主控台 - 學生資料分析系統',
      requiresAuth: true
    }
  },
  {
    path: '/data-management',
    name: 'DataManagement',
    component: DataManagementView,
    meta: {
      title: '數據管理 - 學生資料分析系統',
      requiresAuth: true
    }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: AnalysisView,
    meta: {
      title: '數據分析 - 學生資料分析系統',
      requiresAuth: true
    }
  },
  // 暫時隱藏用戶管理路由
  /*
  {
    path: '/user-management',
    name: 'UserManagement',
    component: UserManagementView,
    meta: {
      title: '用戶管理 - 學生資料分析系統',
      requiresAuth: true,
      requiresAdmin: true
    }
  }
  */
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守衛
router.beforeEach(async (to, from, next) => {
  // 動態導入 authService 避免循環依賴
  const { authService } = await import('../services/auth.js')
  
  // 設置頁面標題
  if (to.meta.title) {
    document.title = to.meta.title
  }

  // 檢查是否需要登入
  if (to.meta.requiresAuth) {
    if (!authService.isAuthenticated()) {
      next('/login')
      return
    }
  }

  // 檢查是否需要管理員權限
  if (to.meta.requiresAdmin) {
    if (!authService.isAdmin()) {
      alert('您沒有權限訪問此頁面')
      next('/dashboard')
      return
    }
  }

  next()
})

export default router
