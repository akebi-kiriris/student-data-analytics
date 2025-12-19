<template>
  <div class="dashboard-container">
    <!-- 頂部導航欄 -->
    <header class="top-navbar">
      <div class="navbar-left">
        <h1 class="system-title">🎓 學生資料分析系統</h1>
        <nav class="nav-links">
          <router-link to="/dashboard" class="nav-link">主控台</router-link>
          <router-link to="/data-management" class="nav-link">數據管理</router-link>
          <router-link to="/analysis" class="nav-link">數據分析</router-link>
        </nav>
      </div>
      <div class="navbar-right">
        <span class="current-time">{{ currentTime }}</span>
        <span class="user-info">👤 {{ currentUser }}</span>
        <button @click="handleLogout" class="logout-btn">🚪 登出</button>
      </div>
    </header>

    <div class="main-layout">
      <!-- 主內容區域 -->
      <main class="main-content">
        <!-- 歡迎區域 -->
        <div class="welcome-section">
          <div class="welcome-text">
            <h2>歡迎回來，{{ currentUser }}！</h2>
            <p>{{ currentDate }}</p>
          </div>
        </div>

        <!-- 統計卡片 -->
        <div class="stats-section">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">📊</div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.totalData }}</div>
                <div class="stat-label">筆資料</div>
              </div>
            </div>
            <!-- 暫時隱藏用戶管理統計 -->
            <div v-if="showUserManagement" class="stat-card" style="display: none;">
              <div class="stat-icon">👥</div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.totalUsers }}</div>
                <div class="stat-label">位用戶</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📋</div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.totalReports }}</div>
                <div class="stat-label">個報告</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📁</div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.totalFiles }}</div>
                <div class="stat-label">個檔案</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 快速操作 -->
        <div class="quick-actions-section">
          <h3>快速操作</h3>
          <div class="action-buttons">
            <button @click="$router.push('/data-management')" class="action-btn">
              <span class="action-icon">📁</span>
              <span>上傳資料</span>
            </button>
            <button @click="$router.push('/analysis')" class="action-btn">
              <span class="action-icon">📊</span>
              <span>快速分析</span>
            </button>
            <button class="action-btn" disabled style="opacity: 0.6;">
              <span class="action-icon">📋</span>
              <span>新建報告 (開發中)</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/auth.js'
import { simpleApiService, SIMPLE_API_ENDPOINTS } from '../services/api-simple.js'

const router = useRouter()

// 響應式數據
const currentUser = ref('')
const currentTime = ref('')
const currentDate = ref('')

// 功能開關
const showUserManagement = ref(false) // 暫時隱藏用戶管理功能

const stats = ref({
  totalData: '載入中...',
  totalReports: '0',
  totalFiles: '載入中...'
})

let timeInterval = null

// 載入統計數據
const loadStats = async () => {
  try {
    // 獲取資料庫表格數量
    const tablesResponse = await simpleApiService.get(SIMPLE_API_ENDPOINTS.DATABASE_TABLES)
    
    if (tablesResponse.success) {
      stats.value.totalFiles = tablesResponse.tables.length.toString()
      
      // 計算總數據筆數
      let totalRows = 0
      for (const table of tablesResponse.tables) {
        try {
          const countResponse = await simpleApiService.get(`${SIMPLE_API_ENDPOINTS.TABLE_COUNT}/${table.table_name}/count`)
          if (countResponse.success) {
            totalRows += countResponse.count
          }
        } catch (error) {
          console.warn(`無法獲取表格 ${table.table_name} 的筆數:`, error)
        }
      }
      stats.value.totalData = totalRows.toLocaleString()
    } else {
      console.error('獲取表格列表失敗:', tablesResponse)
    }
  } catch (error) {
    console.error('載入統計數據失敗:', error)
    stats.value.totalData = '無法載入'
    stats.value.totalFiles = '無法載入'
  }
}

// 方法
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-TW')
  currentDate.value = now.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const loadUserInfo = () => {
  const user = authService.getCurrentUser()
  if (user) {
    currentUser.value = user.username
  }
}

const handleLogout = async () => {
  if (confirm('確定要登出嗎？')) {
    try {
      await authService.logout()
      router.push('/login')
    } catch (error) {
      console.error('登出錯誤:', error)
      // 即使API調用失敗，也要清除本地存儲並跳轉
      authService.logout()
      router.push('/login')
    }
  }
}

// 生命週期掛鉤
onMounted(() => {
  // 獲取當前用戶信息
  const user = authService.getCurrentUser()
  if (user) {
    currentUser.value = user.username || '用戶'
  }
  
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  loadUserInfo()
  loadStats() // 載入統計數據
})

onBeforeUnmount(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 頂部導航欄 */
.top-navbar {
  height: 60px;
  background-color: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.navbar-left .system-title {
  color: #1976d2;
  font-size: 18px;
  margin: 0;
  margin-right: 30px;
}

.navbar-left {
  display: flex;
  align-items: center;
}



.nav-links {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: #666;
  text-decoration: none;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-link:hover {
  background-color: #f5f5f5;
  color: #1976d2;
}

.nav-link.router-link-active {
  background-color: #1976d2;
  color: white;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.current-time, .user-info {
  color: #666;
  font-size: 14px;
}

.logout-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.logout-btn:hover {
  background-color: #f5f5f5;
}

/* 主要布局 */
.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 主內容區域 */
.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f5f5f5;
  overflow-y: auto;
}

/* 歡迎區域 */
.welcome-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.welcome-text h2 {
  margin: 0 0 8px 0;
  color: #212121;
  font-size: 24px;
}

.welcome-text p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* 統計卡片 */
.stats-section {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #1976d2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 快速操作 */
.quick-actions-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.quick-actions-section h3 {
  margin: 0 0 16px 0;
  color: #212121;
  font-size: 18px;
}

.action-buttons {
  display: flex;
  gap: 16px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 120px;
}

.action-btn:hover {
  background: #e3f2fd;
  border-color: #1976d2;
}

.action-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.action-btn span:last-child {
  font-size: 14px;
  color: #212121;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>
