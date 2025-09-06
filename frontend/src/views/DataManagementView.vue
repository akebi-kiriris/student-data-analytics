<template>
  <div class="data-management-container">
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
        <div class="page-header">
          <h2>數據管理</h2>
        </div>

        <!-- 檔案上傳區域 -->
        <div class="upload-section">
          <div class="upload-card">
            <h3>檔案上傳到資料庫</h3>
            <div class="upload-controls">
              <button @click="triggerFileInput" class="upload-btn">
                📁 選擇檔案
              </button>
              <button 
                @click="previewData" 
                class="preview-btn"
                :disabled="!selectedFile"
              >
                📋 預覽資料
              </button>
              <button 
                @click="uploadFile" 
                class="confirm-btn"
                :disabled="!selectedFile || isUploading"
              >
                {{ isUploading ? '上傳中...' : '✅ 確認上傳' }}
              </button>
            </div>

            <!-- 工作表選擇區域 -->
            <div v-if="availableSheets.length > 0" class="sheet-selection">
              <h4>選擇要上傳的工作表：</h4>
              <div class="sheet-list">
                <div 
                  v-for="sheet in availableSheets" 
                  :key="sheet"
                  class="sheet-item"
                  :class="{ selected: selectedSheet === sheet }"
                  @click="selectSheet(sheet)"
                >
                  📄 {{ sheet }}
                </div>
              </div>
              <button 
                @click="uploadToDatabase" 
                class="confirm-btn"
                :disabled="!selectedSheet || isUploading"
                style="margin-top: 10px;"
              >
                {{ isUploading ? '存入資料庫中...' : '💾 存入資料庫' }}
              </button>
            </div>

            <div class="upload-info">
              <span>支援格式：.xlsx, .xls | 最大檔案：10MB</span>
              <span v-if="selectedFile" class="file-info">
                已選擇：{{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})
              </span>
            </div>
            <input 
              ref="fileInput" 
              type="file" 
              accept=".xlsx,.xls" 
              @change="handleFileSelect"
              style="display: none"
            />
          </div>
        </div>

        <!-- 已上傳的資料表列表 -->
        <div class="database-tables-section">
          <div class="section-card">
            <h3>已存入資料庫的表格</h3>
            <div v-if="databaseTables.length === 0" class="empty-state">
              <p>📭 目前沒有已上傳的資料表</p>
              <p>請使用上方的檔案上傳功能來新增資料</p>
            </div>
            <div v-else class="tables-grid">
              <div 
                v-for="table in databaseTables" 
                :key="table.table_name"
                class="table-card"
              >
                <div class="table-header">
                  <h4>{{ table.display_name }}</h4>
                  <span class="table-info">{{ table.row_count || '載入中...' }} 筆資料</span>
                </div>
                <div class="table-actions">
                  <button @click="analyzeTable(table)" class="analyze-btn">
                    📊 分析資料
                  </button>
                  <button @click="viewTableData(table)" class="view-btn">
                    👁️ 預覽資料
                  </button>
                  <button @click="deleteTable(table)" class="delete-table-btn">
                    🗑️ 刪除
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/auth.js'
import { apiService, API_ENDPOINTS } from '../services/api.js'

const router = useRouter()

// 響應式數據
const currentUser = ref('')
const currentTime = ref('')
const selectedFile = ref(null)
const availableSheets = ref([])
const selectedSheet = ref('')
const isUploading = ref(false)
const databaseTables = ref([])

// 模板引用
const fileInput = ref(null)

// 方法
const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-TW')
}

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const previewData = () => {
  if (!selectedFile.value) return
  alert('預覽功能：顯示檔案前 10 行資料預覽')
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  
  isUploading.value = true
  availableSheets.value = []
  selectedSheet.value = ''
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const result = await apiService.upload(API_ENDPOINTS.FILE.UPLOAD, formData)
    
    if (result.need_sheet_selection) {
      // 需要選擇工作表
      availableSheets.value = result.sheets
      alert(`檔案上傳成功！檔案包含 ${result.sheets.length} 個工作表，請選擇要存入資料庫的工作表。`)
    } else if (result.success) {
      // 直接上傳成功
      alert(`檔案已成功存入資料庫！表格名稱：${result.table_name}，共 ${result.rows_inserted} 筆資料。`)
      selectedFile.value = null
      fileInput.value.value = ''
      availableSheets.value = []
    } else {
      throw new Error(result.error || '上傳失敗')
    }
  } catch (error) {
    alert('上傳失敗：' + error.message)
  } finally {
    isUploading.value = false
  }
}

const selectSheet = (sheet) => {
  selectedSheet.value = sheet
}

const uploadToDatabase = async () => {
  if (!selectedFile.value || !selectedSheet.value) return
  
  isUploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('sheet_name', selectedSheet.value)
    
    const result = await apiService.upload(API_ENDPOINTS.FILE.UPLOAD, formData)
    
    if (result.success) {
      alert(`工作表「${selectedSheet.value}」已成功存入資料庫！\n表格名稱：${result.table_name}\n共 ${result.rows_inserted} 筆資料`)
      
      // 清理狀態
      selectedFile.value = null
      fileInput.value.value = ''
      availableSheets.value = []
      selectedSheet.value = ''
      
      // 重新載入資料庫表格列表
      loadDatabaseTables()
    } else {
      throw new Error(result.error || '存入資料庫失敗')
    }
  } catch (error) {
    alert('存入資料庫失敗：' + error.message)
  } finally {
    isUploading.value = false
  }
}

// 載入資料庫表格列表
const loadDatabaseTables = async () => {
  try {
    const response = await apiService.get(API_ENDPOINTS.DATABASE.NEW_TABLES)
    
    if (response.success) {
      databaseTables.value = response.tables
      
      // 為每個表格載入行數
      for (const table of databaseTables.value) {
        try {
          const countResponse = await apiService.get(`${API_ENDPOINTS.DATABASE.TABLE_COUNT}/${table.table_name}/count`)
          if (countResponse.success) {
            table.row_count = countResponse.count.toLocaleString()
          }
        } catch (error) {
          console.warn(`無法獲取表格 ${table.table_name} 的筆數:`, error)
          table.row_count = '未知'
        }
      }
    } else {
      console.error('API回應表示失敗:', response)
    }
  } catch (error) {
    console.error('載入資料庫表格失敗:', error)
    // 不要在這裡跳轉，只是記錄錯誤
  }
}

const analyzeTable = (table) => {
  // 跳轉到分析頁面並選擇該表格
  router.push({
    path: '/analysis',
    query: { table: table.table_name }
  })
}

const viewTableData = async (table) => {
  try {
    // 這裡可以實現資料預覽功能
    alert(`預覽功能：顯示表格 ${table.display_name} 的前20筆資料`)
  } catch (error) {
    alert('預覽失敗：' + error.message)
  }
}

const deleteTable = async (table) => {
  if (!confirm(`確定要刪除表格「${table.display_name}」嗎？此操作無法復原。`)) {
    return
  }
  
  try {
    // 這裡需要實現刪除API
    alert('刪除功能開發中...')
    // 成功後重新載入列表
    // loadDatabaseTables()
  } catch (error) {
    alert('刪除失敗：' + error.message)
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const clearFilters = () => {
  searchKeyword.value = ''
  dateFilter.value = ''
  categoryFilter.value = ''
  currentPage.value = 1
}

const toggleSelectAll = () => {
  paginatedData.value.forEach(record => {
    record.selected = selectAll.value
  })
}

const updateSelectAll = () => {
  selectAll.value = paginatedData.value.every(record => record.selected)
}

const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

const getSortIcon = (field) => {
  if (sortField.value !== field) return '↕️'
  return sortDirection.value === 'asc' ? '⬆️' : '⬇️'
}

const editRecord = (record) => {
  record.originalData = { ...record }
  record.editing = true
}

const saveRecord = (record) => {
  record.editing = false
  record.originalData = null
  hasChanges.value = true
  alert('資料已修改，請點擊批次儲存以確認變更')
}

const cancelEdit = (record) => {
  if (record.originalData) {
    Object.assign(record, record.originalData)
    record.originalData = null
  }
  record.editing = false
}

const deleteRecord = (record) => {
  if (confirm('確定要刪除這筆資料嗎？')) {
    const index = studentData.value.findIndex(item => item.id === record.id)
    studentData.value.splice(index, 1)
    hasChanges.value = true
  }
}

const batchSave = () => {
  if (confirm('確定要儲存所有變更嗎？')) {
    hasChanges.value = false
    alert('資料已儲存')
  }
}

const addNewRecord = () => {
  const newId = Math.max(...studentData.value.map(r => r.id)) + 1
  studentData.value.push({
    id: newId,
    ...newRecord.value,
    selected: false,
    editing: false,
    originalData: null
  })
  newRecord.value = {
    studentId: '',
    name: '',
    department: '',
    score: ''
  }
  showAddModal.value = false
  hasChanges.value = true
}

const updatePagination = () => {
  currentPage.value = 1
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 登出功能
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
  setInterval(updateTime, 1000)
  loadDatabaseTables() // 載入已存入的資料庫表格
})
</script>

<style scoped>
.data-management-container {
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

.page-header h2 {
  margin: 0 0 20px 0;
  color: #212121;
  font-size: 24px;
}

/* 檔案上傳區域 */
.upload-section {
  margin-bottom: 20px;
}

.upload-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.upload-card h3 {
  margin: 0 0 16px 0;
  color: #212121;
  font-size: 18px;
}

.upload-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.upload-btn, .preview-btn, .confirm-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.upload-btn {
  background: #f8f9fa;
  color: #212121;
}

.preview-btn {
  background: #e3f2fd;
  color: #1976d2;
  border-color: #1976d2;
}

.confirm-btn {
  background: #4caf50;
  color: white;
  border-color: #4caf50;
}

.upload-btn:hover {
  background: #e9ecef;
}

.preview-btn:hover:not(:disabled) {
  background: #bbdefb;
}

.confirm-btn:hover:not(:disabled) {
  background: #45a049;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 工作表選擇區域 */
.sheet-selection {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px solid #e9ecef;
}

.sheet-selection h4 {
  margin: 0 0 12px 0;
  color: #212121;
  font-size: 16px;
}

.sheet-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.sheet-item {
  padding: 8px 12px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  user-select: none;
}

.sheet-item:hover {
  border-color: #2196f3;
  background: #f0f8ff;
}

.sheet-item.selected {
  background: #2196f3;
  color: white;
  border-color: #2196f3;
}

.upload-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.file-info {
  color: #1976d2;
  font-weight: 500;
}

/* 資料庫表格列表 */
.database-tables-section {
  margin-bottom: 20px;
}

.section-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-card h3 {
  margin: 0 0 16px 0;
  color: #212121;
  font-size: 18px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.empty-state p {
  margin: 8px 0;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.table-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  transition: all 0.3s;
}

.table-card:hover {
  border-color: #2196f3;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-header h4 {
  margin: 0 0 4px 0;
  color: #212121;
  font-size: 16px;
  font-weight: 600;
}

.table-info {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  display: block;
}

.table-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.analyze-btn, .view-btn, .delete-table-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.analyze-btn {
  background: #2196f3;
  color: white;
}

.view-btn {
  background: #4caf50;
  color: white;
}

.delete-table-btn {
  background: #f44336;
  color: white;
}

.analyze-btn:hover {
  background: #1976d2;
}

.view-btn:hover {
  background: #45a049;
}

.delete-table-btn:hover {
  background: #d32f2f;
}

/* 篩選區域 */
.filter-section {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input, .filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
}

.clear-btn {
  padding: 8px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.clear-btn:hover {
  background: #d32f2f;
}
</style>
