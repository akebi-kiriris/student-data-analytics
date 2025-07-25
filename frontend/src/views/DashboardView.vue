<template>
  <div class="dashboard-container">
    <!-- 頂部導航欄 -->
    <header class="top-navbar">
      <div class="navbar-left">
        <h1 class="system-title">🎓 學生資料分析系統</h1>
      </div>
      <div class="navbar-right">
        <span class="current-time">{{ currentTime }}</span>
        <span class="user-info">👤 {{ currentUser }}</span>
        <button @click="handleLogout" class="logout-btn">🚪 登出</button>
      </div>
    </header>

    <div class="main-layout">
      <!-- 側邊欄 -->
      <aside class="sidebar">
        <nav class="sidebar-nav">
          <ul class="nav-menu">
            <li class="nav-item active">
              <a href="#" class="nav-link">
                <span class="nav-icon">🏠</span>
                <span class="nav-text">主控台</span>
              </a>
            </li>
            <li class="nav-item">
              <a href="#" @click="$router.push('/analysis')" class="nav-link">
                <span class="nav-icon">📊</span>
                <span class="nav-text">數據分析</span>
              </a>
            </li>
            <li class="nav-item">
              <a href="#" @click="$router.push('/data-management')" class="nav-link">
                <span class="nav-icon">📋</span>
                <span class="nav-text">數據管理</span>
              </a>
            </li>
            <li class="nav-item">
              <a href="#" @click="$router.push('/user-management')" class="nav-link">
                <span class="nav-icon">👥</span>
                <span class="nav-text">用戶管理</span>
              </a>
            </li>
            <li class="nav-item">
              <a href="#" class="nav-link">
                <span class="nav-icon">⚙️</span>
                <span class="nav-text">設定</span>
              </a>
            </li>
          </ul>
        </nav>
        <div class="sidebar-footer">
          <span class="version">版本 v1.0</span>
        </div>
      </aside>

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
            <div class="stat-card">
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

        <!-- 最近活動 -->
        <div class="activity-section">
          <div class="section-header">
            <h3>最近活動</h3>
            <a href="#" class="more-link">更多 →</a>
          </div>
          <div class="activity-list">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <span class="activity-icon">{{ activity.icon }}</span>
              <span class="activity-time">{{ activity.time }}</span>
              <span class="activity-description">{{ activity.description }}</span>
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
            <button class="action-btn">
              <span class="action-icon">📋</span>
              <span>新建報告</span>
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

const router = useRouter()

// 響應式數據
const currentUser = ref('管理者')
const currentTime = ref('')
const currentDate = ref('')
const stats = ref({
  totalData: '1,250',
  totalUsers: '15',
  totalReports: '89',
  totalFiles: '42'
})
const recentActivities = ref([
  {
    id: 1,
    icon: '📋',
    time: '2025/07/21 10:30',
    description: '管理者上傳了新的學生資料 (120筆)'
  },
  {
    id: 2,
    icon: '📊',
    time: '2025/07/20 15:45',
    description: '完成了入學管道分析報告'
  },
  {
    id: 3,
    icon: '👥',
    time: '2025/07/20 09:15',
    description: '新增用戶：張教授'
  }
])

let timeInterval = null

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
    currentUser.value = user.name
  }
}

const handleLogout = () => {
  if (confirm('確定要登出嗎？')) {
    authService.logout()
    router.push('/login')
  }
}

// 生命週期掛鉤
onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  loadUserInfo()
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

/* 側邊欄 */
.sidebar {
  width: 250px;
  background-color: #263238;
  color: white;
  display: flex;
  flex-direction: column;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin-bottom: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: #b0bec5;
  text-decoration: none;
  transition: all 0.3s;
}

.nav-item.active .nav-link,
.nav-link:hover {
  background-color: #1976d2;
  color: white;
}

.nav-icon {
  margin-right: 12px;
  font-size: 16px;
}

.nav-text {
  font-size: 14px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #37474f;
  text-align: center;
}

.version {
  color: #78909c;
  font-size: 12px;
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
  grid-template-columns: repeat(4, 1fr);
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

/* 最近活動 */
.activity-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  color: #212121;
  font-size: 18px;
}

.more-link {
  color: #1976d2;
  text-decoration: none;
  font-size: 14px;
}

.activity-list {
  space-y: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  margin-right: 12px;
  font-size: 16px;
}

.activity-time {
  margin-right: 16px;
  color: #666;
  font-size: 14px;
  min-width: 140px;
}

.activity-description {
  color: #212121;
  font-size: 14px;
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
