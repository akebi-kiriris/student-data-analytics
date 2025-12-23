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
                    👁️ 管理資料
                  </button>
                  <button @click="deleteTable(table)" class="delete-table-btn">
                    🗑️ 刪除
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 數據 CRUD 管理區域 -->
        <div v-if="showDataManager" class="data-crud-section">
          <div class="crud-header">
            <h3>{{ currentTable.display_name }} - 數據管理</h3>
            <div class="crud-actions">
              <button @click="showCreateDialog" class="create-btn">
                ➕ 新增資料
              </button>
              <button @click="refreshTableData" class="refresh-btn">
                🔄 重新整理
              </button>
              <button @click="showDataManager = false" class="close-btn">
                ✖️ 關閉
              </button>
            </div>
          </div>

          <!-- 搜尋區域 -->
          <div class="search-section">
            <input 
              v-model="searchQuery" 
              @keyup.enter="performSearch"
              placeholder="搜尋資料..." 
              class="search-input"
            >
            <button @click="performSearch" class="search-btn">🔍 搜尋</button>
            <button @click="clearSearch" class="clear-btn">🗑️ 清除</button>
          </div>

          <!-- 數據表格 -->
          <div class="data-table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th v-for="col in tableColumns" :key="col">{{ col }}</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in tableData" :key="row.id">
                  <td>{{ row.id }}</td>
                  <td v-for="col in tableColumns" :key="col">
                    <div v-if="editingRow === row.id" class="edit-cell">
                      <input 
                        v-model="editData[col]" 
                        :placeholder="col"
                        class="edit-input"
                      >
                    </div>
                    <div v-else class="view-cell">{{ row[col] || '-' }}</div>
                  </td>
                  <td class="action-cell">
                    <div v-if="editingRow === row.id" class="edit-actions">
                      <button @click="saveEdit(row.id)" class="save-btn">💾</button>
                      <button @click="cancelEdit" class="cancel-btn">✖️</button>
                    </div>
                    <div v-else class="view-actions">
                      <button @click="startEdit(row)" class="edit-btn">✏️</button>
                      <button @click="deleteRow(row.id)" class="delete-btn">🗑️</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分頁 -->
          <div class="pagination" v-if="pagination.total_pages > 1">
            <button 
              @click="changePage(pagination.current_page - 1)"
              :disabled="!pagination.has_prev"
              class="page-btn"
            >
              ◀️ 上一頁
            </button>
            <span class="page-info">
              第 {{ pagination.current_page }} / {{ pagination.total_pages }} 頁 
              (共 {{ pagination.total_count }} 筆)
            </span>
            <button 
              @click="changePage(pagination.current_page + 1)"
              :disabled="!pagination.has_next"
              class="page-btn"
            >
              下一頁 ▶️
            </button>
          </div>
        </div>

        <!-- 新增資料對話框 -->
        <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
          <div class="modal-content">
            <div class="modal-header">
              <h3>新增資料</h3>
              <button @click="showCreateModal = false" class="modal-close">✖️</button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="createNewRow">
                <div v-for="col in tableColumns" :key="col" class="form-group">
                  <label>{{ col }}:</label>
                  <input 
                    v-model="newRowData[col]" 
                    :placeholder="col"
                    class="form-input"
                  >
                </div>
                <div class="form-actions">
                  <button type="submit" class="submit-btn">💾 儲存</button>
                  <button type="button" @click="showCreateModal = false" class="cancel-btn">取消</button>
                </div>
              </form>
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
import { simpleApiService, SIMPLE_API_ENDPOINTS } from '../services/api-simple.js'
import { apiService } from '../services/api.js'

const router = useRouter()

// 響應式數據
const currentUser = ref('')
const currentTime = ref('')
const selectedFile = ref(null)
const availableSheets = ref([])
const selectedSheet = ref('')
const isUploading = ref(false)
const databaseTables = ref([])

// CRUD 相關數據
const showDataManager = ref(false)
const currentTable = ref(null)
const tableData = ref([])
const tableColumns = ref([])
const pagination = ref({
  current_page: 1,
  total_pages: 1,
  total_count: 0,
  limit: 50,
  has_next: false,
  has_prev: false
})
const searchQuery = ref('')
const editingRow = ref(null)
const editData = ref({})
const showCreateModal = ref(false)
const newRowData = ref({})

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
    
    const result = await simpleApiService.upload(SIMPLE_API_ENDPOINTS.UPLOAD, formData)
    
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
    
    const result = await simpleApiService.upload(SIMPLE_API_ENDPOINTS.UPLOAD, formData)
    
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
    const response = await simpleApiService.get(SIMPLE_API_ENDPOINTS.DATABASE_TABLES)
    
    if (response.success) {
      databaseTables.value = response.tables
      
      // 為每個表格載入行數
      for (const table of databaseTables.value) {
        try {
          const countResponse = await simpleApiService.get(`${SIMPLE_API_ENDPOINTS.TABLE_COUNT}/${table.table_name}/count`)
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
    currentTable.value = table
    showDataManager.value = true
    searchQuery.value = ''
    await loadTableData()
  } catch (error) {
    alert('載入資料失敗：' + error.message)
  }
}

// CRUD 相關方法
const loadTableData = async (page = 1) => {
  try {
    const params = {
      page,
      limit: 50,
      search: searchQuery.value
    }
    
    const result = await apiService.crud.getTableData(currentTable.value.table_name, params)
    
    if (result.success) {
      tableData.value = result.data
      tableColumns.value = result.columns.filter(col => col !== 'id')
      pagination.value = result.pagination
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    alert('載入資料失敗：' + error.message)
  }
}

const refreshTableData = () => {
  loadTableData(pagination.value.current_page)
}

const performSearch = () => {
  loadTableData(1) // 搜尋時回到第一頁
}

const clearSearch = () => {
  searchQuery.value = ''
  loadTableData(1)
}

const changePage = (page) => {
  if (page >= 1 && page <= pagination.value.total_pages) {
    loadTableData(page)
  }
}

// 編輯相關
const startEdit = (row) => {
  editingRow.value = row.id
  editData.value = { ...row }
}

const cancelEdit = () => {
  editingRow.value = null
  editData.value = {}
}

const saveEdit = async (rowId) => {
  try {
    const updateData = {}
    tableColumns.value.forEach(col => {
      updateData[col] = editData.value[col]
    })
    
    const result = await apiService.crud.updateRow(currentTable.value.table_name, rowId, updateData)
    
    if (result.success) {
      alert('資料更新成功！')
      editingRow.value = null
      editData.value = {}
      await loadTableData(pagination.value.current_page)
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    alert('更新失敗：' + error.message)
  }
}

const deleteRow = async (rowId) => {
  if (!confirm('確定要刪除這筆資料嗎？此操作無法復原。')) {
    return
  }
  
  try {
    const result = await apiService.crud.deleteRow(currentTable.value.table_name, rowId)
    
    if (result.success) {
      alert('資料刪除成功！')
      await loadTableData(pagination.value.current_page)
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    alert('刪除失敗：' + error.message)
  }
}

// 新增資料相關
const showCreateDialog = () => {
  newRowData.value = {}
  tableColumns.value.forEach(col => {
    newRowData.value[col] = ''
  })
  showCreateModal.value = true
}

const createNewRow = async () => {
  try {
    const result = await apiService.crud.createRow(currentTable.value.table_name, newRowData.value)
    
    if (result.success) {
      alert('資料新增成功！')
      showCreateModal.value = false
      newRowData.value = {}
      await loadTableData(pagination.value.current_page)
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    alert('新增失敗：' + error.message)
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

const cancelRecordEdit = (record) => {
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

/* CRUD 管理界面樣式 */
.data-crud-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
  overflow: hidden;
}

.crud-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.crud-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.crud-actions {
  display: flex;
  gap: 8px;
}

.create-btn, .refresh-btn, .close-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.create-btn {
  background: #28a745;
  color: white;
}

.refresh-btn {
  background: #17a2b8;
  color: white;
}

.close-btn {
  background: #6c757d;
  color: white;
}

.create-btn:hover {
  background: #218838;
}

.refresh-btn:hover {
  background: #138496;
}

.close-btn:hover {
  background: #5a6268;
}

.search-section {
  padding: 16px 20px;
  display: flex;
  gap: 8px;
  align-items: center;
  border-bottom: 1px solid #dee2e6;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.search-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.search-btn:hover {
  background: #0056b3;
}

.data-table-container {
  overflow-x: auto;
  max-height: 600px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table tr:hover {
  background: #f8f9fa;
}

.edit-cell {
  padding: 2px;
}

.edit-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #ced4da;
  border-radius: 3px;
  font-size: 13px;
}

.view-cell {
  min-height: 20px;
  word-break: break-word;
}

.action-cell {
  width: 100px;
}

.edit-actions, .view-actions {
  display: flex;
  gap: 4px;
}

.edit-btn, .delete-btn, .save-btn, .cancel-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  min-width: 30px;
  transition: all 0.3s;
}

.edit-btn {
  background: #ffc107;
  color: #212529;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.save-btn {
  background: #28a745;
  color: white;
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.edit-btn:hover {
  background: #e0a800;
}

.delete-btn:hover {
  background: #c82333;
}

.save-btn:hover {
  background: #218838;
}

.cancel-btn:hover {
  background: #5a6268;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-top: 1px solid #dee2e6;
}

.page-btn {
  padding: 8px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.page-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.page-btn:not(:disabled):hover {
  background: #0056b3;
}

.page-info {
  font-size: 14px;
  color: #6c757d;
}

/* 模態框樣式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #dee2e6;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #6c757d;
  padding: 4px;
}

.modal-close:hover {
  color: #343a40;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #dee2e6;
}

.submit-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.submit-btn:hover {
  background: #218838;
}

.form-actions .cancel-btn {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.form-actions .cancel-btn:hover {
  background: #5a6268;
}
</style>
