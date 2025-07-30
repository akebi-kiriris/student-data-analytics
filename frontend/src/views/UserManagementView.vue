<template>
  <div class="user-management-container">
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
      <!-- 主內容區域 -->
      <main class="main-content">
        <div class="page-header">
          <h2>用戶管理</h2>
          <button @click="showAddUserModal = true" class="add-user-btn">
            ➕ 新增用戶
          </button>
        </div>

        <!-- 搜尋和篩選 -->
        <div class="search-filter-section">
          <div class="search-bar">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="🔍 搜尋用戶名稱、電子郵件或角色..."
              class="search-input"
            />
          </div>
          <div class="filter-group">
            <select v-model="selectedRole" class="filter-select">
              <option value="">全部角色</option>
              <option value="admin">管理員</option>
              <option value="teacher">教師</option>
              <option value="student">學生</option>
            </select>
            <select v-model="selectedStatus" class="filter-select">
              <option value="">全部狀態</option>
              <option value="active">啟用</option>
              <option value="inactive">停用</option>
            </select>
          </div>
        </div>

        <!-- 用戶統計卡片 -->
        <div class="stats-grid">
          <div class="stat-card total">
            <div class="stat-icon">👥</div>
            <div class="stat-content">
              <div class="stat-number">{{ totalUsers }}</div>
              <div class="stat-label">總用戶數</div>
            </div>
          </div>
          <div class="stat-card admin">
            <div class="stat-icon">🔧</div>
            <div class="stat-content">
              <div class="stat-number">{{ adminUsers }}</div>
              <div class="stat-label">管理員</div>
            </div>
          </div>
          <div class="stat-card teacher">
            <div class="stat-icon">👨‍🏫</div>
            <div class="stat-content">
              <div class="stat-number">{{ teacherUsers }}</div>
              <div class="stat-label">教師</div>
            </div>
          </div>
          <div class="stat-card student">
            <div class="stat-icon">🎓</div>
            <div class="stat-content">
              <div class="stat-number">{{ studentUsers }}</div>
              <div class="stat-label">學生</div>
            </div>
          </div>
        </div>

        <!-- 用戶列表 -->
        <div class="user-table-section">
          <div class="table-header">
            <h3>用戶列表</h3>
            <div class="table-actions">
              <button @click="exportUsers" class="action-btn export-btn">
                📄 匯出列表
              </button>
              <button @click="refreshUsers" class="action-btn refresh-btn">
                🔄 重新整理
              </button>
            </div>
          </div>

          <div class="table-container">
            <table class="user-table">
              <thead>
                <tr>
                  <th>
                    <input type="checkbox" @change="toggleSelectAll" :checked="isAllSelected" />
                  </th>
                  <th @click="sortBy('name')" class="sortable">
                    姓名 
                    <span class="sort-icon">{{ getSortIcon('name') }}</span>
                  </th>
                  <th @click="sortBy('email')" class="sortable">
                    電子郵件
                    <span class="sort-icon">{{ getSortIcon('email') }}</span>
                  </th>
                  <th @click="sortBy('role')" class="sortable">
                    角色
                    <span class="sort-icon">{{ getSortIcon('role') }}</span>
                  </th>
                  <th @click="sortBy('status')" class="sortable">
                    狀態
                    <span class="sort-icon">{{ getSortIcon('status') }}</span>
                  </th>
                  <th @click="sortBy('lastLogin')" class="sortable">
                    最後登入
                    <span class="sort-icon">{{ getSortIcon('lastLogin') }}</span>
                  </th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedUsers" :key="user.id" :class="{ selected: selectedUsers.includes(user.id) }">
                  <td>
                    <input type="checkbox" :value="user.id" v-model="selectedUsers" />
                  </td>
                  <td>
                    <div class="user-info">
                      <div class="user-avatar">{{ user.name.charAt(0) }}</div>
                      <div class="user-details">
                        <div class="user-name">{{ user.name }}</div>
                        <div class="user-id">ID: {{ user.id }}</div>
                      </div>
                    </div>
                  </td>
                  <td>{{ user.email }}</td>
                  <td>
                    <span :class="['role-badge', user.role]">
                      {{ getRoleLabel(user.role) }}
                    </span>
                  </td>
                  <td>
                    <span :class="['status-badge', user.status]">
                      {{ getStatusLabel(user.status) }}
                    </span>
                  </td>
                  <td>{{ formatDate(user.lastLogin) }}</td>
                  <td>
                    <div class="action-buttons">
                      <button @click="editUser(user)" class="btn-edit" title="編輯">
                        ✏️
                      </button>
                      <button 
                        @click="toggleUserStatus(user)" 
                        :class="['btn-toggle', user.status]" 
                        :title="user.status === 'active' ? '停用' : '啟用'"
                      >
                        {{ user.status === 'active' ? '🔒' : '🔓' }}
                      </button>
                      <button @click="resetPassword(user)" class="btn-reset" title="重設密碼">
                        🔑
                      </button>
                      <button @click="deleteUser(user)" class="btn-delete" title="刪除">
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分頁控制 -->
          <div class="pagination-container">
            <div class="pagination-info">
              顯示 {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, filteredUsers.length) }} 
              項，共 {{ filteredUsers.length }} 項
            </div>
            <div class="pagination-controls">
              <button 
                @click="currentPage = 1" 
                :disabled="currentPage === 1"
                class="pagination-btn"
              >
                ⏮️
              </button>
              <button 
                @click="currentPage--" 
                :disabled="currentPage === 1"
                class="pagination-btn"
              >
                ⬅️
              </button>
              <span class="page-numbers">
                <button 
                  v-for="page in visiblePages" 
                  :key="page"
                  @click="currentPage = page"
                  :class="['page-btn', { active: currentPage === page }]"
                >
                  {{ page }}
                </button>
              </span>
              <button 
                @click="currentPage++" 
                :disabled="currentPage === totalPages"
                class="pagination-btn"
              >
                ➡️
              </button>
              <button 
                @click="currentPage = totalPages" 
                :disabled="currentPage === totalPages"
                class="pagination-btn"
              >
                ⏭️
              </button>
            </div>
            <div class="page-size-selector">
              <label>每頁顯示:</label>
              <select v-model="pageSize" class="page-size-select">
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 批量操作 -->
        <div v-if="selectedUsers.length > 0" class="bulk-actions">
          <div class="bulk-info">
            已選擇 {{ selectedUsers.length }} 個用戶
          </div>
          <div class="bulk-buttons">
            <button @click="bulkActivate" class="bulk-btn activate">
              ✅ 批量啟用
            </button>
            <button @click="bulkDeactivate" class="bulk-btn deactivate">
              ❌ 批量停用
            </button>
            <button @click="bulkDelete" class="bulk-btn delete">
              🗑️ 批量刪除
            </button>
          </div>
        </div>
      </main>
    </div>

    <!-- 新增/編輯用戶 Modal -->
    <div v-if="showAddUserModal || showEditUserModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ showAddUserModal ? '新增用戶' : '編輯用戶' }}</h3>
          <button @click="closeModal" class="modal-close">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveUser">
            <div class="form-group">
              <label>姓名 *</label>
              <input 
                type="text" 
                v-model="userForm.name" 
                required 
                class="form-input"
                placeholder="請輸入姓名"
              />
            </div>
            <div class="form-group">
              <label>電子郵件 *</label>
              <input 
                type="email" 
                v-model="userForm.email" 
                required 
                class="form-input"
                placeholder="請輸入電子郵件"
              />
            </div>
            <div class="form-group">
              <label>角色 *</label>
              <select v-model="userForm.role" required class="form-select">
                <option value="">請選擇角色</option>
                <option value="admin">管理員</option>
                <option value="teacher">教師</option>
                <option value="student">學生</option>
              </select>
            </div>
            <div v-if="showAddUserModal" class="form-group">
              <label>密碼 *</label>
              <input 
                type="password" 
                v-model="userForm.password" 
                required 
                class="form-input"
                placeholder="請輸入密碼"
                minlength="6"
              />
            </div>
            <div class="form-group">
              <label>狀態</label>
              <select v-model="userForm.status" class="form-select">
                <option value="active">啟用</option>
                <option value="inactive">停用</option>
              </select>
            </div>
            <div class="modal-actions">
              <button type="button" @click="closeModal" class="btn-cancel">
                取消
              </button>
              <button type="submit" class="btn-save">
                {{ showAddUserModal ? '新增' : '儲存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 響應式數據
const currentUser = ref('管理者')
const currentTime = ref('')
const searchQuery = ref('')
const selectedRole = ref('')
const selectedStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(25)
const sortColumn = ref('name')
const sortDirection = ref('asc')
const selectedUsers = ref([])
const showAddUserModal = ref(false)
const showEditUserModal = ref(false)
const userForm = ref({
  id: null,
  name: '',
  email: '',
  role: '',
  password: '',
  status: 'active'
})

const users = ref([])

// 計算屬性
const totalUsers = computed(() => users.value.length)

const adminUsers = computed(() => users.value.filter(user => user.role === 'admin').length)

const teacherUsers = computed(() => users.value.filter(user => user.role === 'teacher').length)

const studentUsers = computed(() => users.value.filter(user => user.role === 'student').length)

const filteredUsers = computed(() => {
  let filtered = users.value

  // 搜尋過濾
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(user => 
      user.name.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query) ||
      getRoleLabel(user.role).toLowerCase().includes(query)
    )
  }

  // 角色過濾
  if (selectedRole.value) {
    filtered = filtered.filter(user => user.role === selectedRole.value)
  }

  // 狀態過濾
  if (selectedStatus.value) {
    filtered = filtered.filter(user => user.status === selectedStatus.value)
  }

  // 排序
  filtered.sort((a, b) => {
    let aValue = a[sortColumn.value]
    let bValue = b[sortColumn.value]

    if (sortColumn.value === 'lastLogin') {
      aValue = new Date(aValue)
      bValue = new Date(bValue)
    }

    if (aValue < bValue) return sortDirection.value === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })

  return filtered
})

const totalPages = computed(() => Math.ceil(filteredUsers.value.length / pageSize.value))

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredUsers.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) pages.push(i)
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    }
  }
  
  return pages
})

const isAllSelected = computed(() => {
  return paginatedUsers.value.length > 0 && 
         paginatedUsers.value.every(user => selectedUsers.value.includes(user.id))
})

// 監聽器
watch(searchQuery, () => {
  currentPage.value = 1
})

watch(selectedRole, () => {
  currentPage.value = 1
})

watch(selectedStatus, () => {
  currentPage.value = 1
})

watch(pageSize, () => {
  currentPage.value = 1
})

// 方法
const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-TW')
}

const handleLogout = () => {
  if (confirm('確定要登出嗎？')) {
    router.push('/login')
  }
}

const sortBy = (column) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}

const getSortIcon = (column) => {
  if (sortColumn.value !== column) return '↕️'
  return sortDirection.value === 'asc' ? '⬆️' : '⬇️'
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedUsers.value = selectedUsers.value.filter(id => 
      !paginatedUsers.value.find(user => user.id === id)
    )
  } else {
    const newSelections = paginatedUsers.value
      .filter(user => !selectedUsers.value.includes(user.id))
      .map(user => user.id)
    selectedUsers.value.push(...newSelections)
  }
}

const getRoleLabel = (role) => {
  const labels = {
    admin: '管理員',
    teacher: '教師',
    student: '學生'
  }
  return labels[role] || role
}

const getStatusLabel = (status) => {
  const labels = {
    active: '啟用',
    inactive: '停用'
  }
  return labels[status] || status
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-TW')
}

const editUser = (user) => {
  userForm.value = { ...user }
  showEditUserModal.value = true
}

const resetPassword = (user) => {
  if (confirm(`確定要重設 ${user.name} 的密碼嗎？`)) {
    alert('密碼重設成功，新密碼已發送至用戶郵箱')
  }
}

const toggleUserStatus = (user) => {
  const action = user.status === 'active' ? '停用' : '啟用'
  if (confirm(`確定要${action} ${user.name} 嗎？`)) {
    user.status = user.status === 'active' ? 'inactive' : 'active'
    alert(`用戶已${action}`)
  }
}

const deleteUser = (user) => {
  if (confirm(`確定要刪除用戶 ${user.name} 嗎？此操作無法復原。`)) {
    const index = users.value.findIndex(u => u.id === user.id)
    if (index > -1) {
      users.value.splice(index, 1)
      selectedUsers.value = selectedUsers.value.filter(id => id !== user.id)
      alert('用戶已刪除')
    }
  }
}

const closeModal = () => {
  showAddUserModal.value = false
  showEditUserModal.value = false
  userForm.value = {
    id: null,
    name: '',
    email: '',
    role: '',
    password: '',
    status: 'active'
  }
}

const saveUser = () => {
  if (showAddUserModal.value) {
    // 新增用戶
    const newUser = {
      ...userForm.value,
      id: 'U' + String(users.value.length + 1).padStart(3, '0'),
      lastLogin: null,
      createdAt: new Date().toISOString()
    }
    users.value.push(newUser)
    alert('用戶新增成功')
  } else {
    // 編輯用戶
    const index = users.value.findIndex(u => u.id === userForm.value.id)
    if (index > -1) {
      users.value[index] = { ...userForm.value }
      alert('用戶資料已更新')
    }
  }
  closeModal()
}

const bulkActivate = () => {
  if (confirm(`確定要啟用選擇的 ${selectedUsers.value.length} 個用戶嗎？`)) {
    users.value.forEach(user => {
      if (selectedUsers.value.includes(user.id)) {
        user.status = 'active'
      }
    })
    selectedUsers.value = []
    alert('批量啟用完成')
  }
}

const bulkDeactivate = () => {
  if (confirm(`確定要停用選擇的 ${selectedUsers.value.length} 個用戶嗎？`)) {
    users.value.forEach(user => {
      if (selectedUsers.value.includes(user.id)) {
        user.status = 'inactive'
      }
    })
    selectedUsers.value = []
    alert('批量停用完成')
  }
}

const bulkDelete = () => {
  if (confirm(`確定要刪除選擇的 ${selectedUsers.value.length} 個用戶嗎？此操作無法復原。`)) {
    users.value = users.value.filter(user => !selectedUsers.value.includes(user.id))
    selectedUsers.value = []
    alert('批量刪除完成')
  }
}

const exportUsers = () => {
  alert('用戶列表匯出功能')
}

const refreshUsers = () => {
  alert('用戶列表已重新整理')
}

// 生命週期掛鉤
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
})
</script>

<style scoped>
/* 複用基本布局樣式 */
.user-management-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

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

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

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

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f5f5f5;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #212121;
  font-size: 24px;
}

.add-user-btn {
  padding: 10px 20px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.3s;
}

.add-user-btn:hover {
  background: #45a049;
}

/* 搜尋和篩選 */
.search-filter-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 20px;
  align-items: center;
}

.search-bar {
  flex: 1;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.filter-group {
  display: flex;
  gap: 12px;
}

.filter-select {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  min-width: 120px;
}

/* 統計卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-left: 4px solid;
}

.stat-card.total {
  border-left-color: #2196f3;
}

.stat-card.admin {
  border-left-color: #ff9800;
}

.stat-card.teacher {
  border-left-color: #4caf50;
}

.stat-card.student {
  border-left-color: #9c27b0;
}

.stat-icon {
  font-size: 32px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #212121;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

/* 用戶表格 */
.user-table-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.table-header h3 {
  margin: 0;
  color: #212121;
  font-size: 18px;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.export-btn {
  background: #2196f3;
  color: white;
}

.refresh-btn {
  background: #4caf50;
  color: white;
}

.action-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.table-container {
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th,
.user-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.user-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #212121;
  position: sticky;
  top: 0;
  z-index: 1;
}

.sortable {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.3s;
}

.sortable:hover {
  background-color: #e9ecef;
}

.sort-icon {
  margin-left: 4px;
  font-size: 12px;
}

.user-table tr.selected {
  background-color: #e3f2fd;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #1976d2;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
}

.user-name {
  font-weight: 500;
  color: #212121;
}

.user-id {
  font-size: 12px;
  color: #666;
}

.role-badge, .status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: #fff3e0;
  color: #ef6c00;
}

.role-badge.teacher {
  background: #e8f5e8;
  color: #2e7d32;
}

.role-badge.student {
  background: #f3e5f5;
  color: #7b1fa2;
}

.status-badge.active {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-badge.inactive {
  background: #ffebee;
  color: #c62828;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-buttons button {
  padding: 6px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-edit {
  background: #2196f3;
  color: white;
}

.btn-toggle.active {
  background: #ff9800;
  color: white;
}

.btn-toggle.inactive {
  background: #4caf50;
  color: white;
}

.btn-reset {
  background: #9c27b0;
  color: white;
}

.btn-delete {
  background: #f44336;
  color: white;
}

.action-buttons button:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

/* 分頁控制 */
.pagination-container {
  display: flex;
  justify-content: between;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
}

.pagination-info {
  color: #666;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  padding: 6px 10px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
}

.pagination-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.pagination-btn:hover:not(:disabled) {
  background: #f0f0f0;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-btn {
  padding: 6px 10px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
}

.page-btn.active {
  background: #1976d2;
  color: white;
  border-color: #1976d2;
}

.page-btn:hover:not(.active) {
  background: #f0f0f0;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

/* 批量操作 */
.bulk-actions {
  background: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 8px;
  padding: 16px 20px;
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bulk-info {
  color: #1976d2;
  font-weight: 500;
}

.bulk-buttons {
  display: flex;
  gap: 8px;
}

.bulk-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.bulk-btn.activate {
  background: #4caf50;
  color: white;
}

.bulk-btn.deactivate {
  background: #ff9800;
  color: white;
}

.bulk-btn.delete {
  background: #f44336;
  color: white;
}

.bulk-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #212121;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.modal-close:hover {
  background-color: #f5f5f5;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  color: #212121;
  font-weight: 500;
  font-size: 14px;
}

.form-input, .form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-cancel, .btn-save {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.3s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-save {
  background: #1976d2;
  color: white;
}

.btn-save:hover {
  background: #1565c0;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .search-filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .pagination-container {
    flex-direction: column;
    gap: 12px;
  }
  
  .bulk-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .user-table {
    font-size: 12px;
  }
  
  .user-table th,
  .user-table td {
    padding: 8px 12px;
  }
}
</style>
