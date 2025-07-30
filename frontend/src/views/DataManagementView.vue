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
            <h3>檔案上傳</h3>
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

        <!-- 搜尋與篩選工具列 -->
        <div class="filter-section">
          <div class="filter-controls">
            <div class="search-group">
              <input 
                v-model="searchKeyword"
                type="text" 
                placeholder="🔍 關鍵字搜尋"
                class="search-input"
                @input="handleSearch"
              />
            </div>
            <div class="filter-group">
              <select v-model="dateFilter" class="filter-select">
                <option value="">📅 日期範圍</option>
                <option value="today">今天</option>
                <option value="week">本週</option>
                <option value="month">本月</option>
                <option value="year">本年</option>
              </select>
            </div>
            <div class="filter-group">
              <select v-model="categoryFilter" class="filter-select">
                <option value="">🏷️ 分類篩選</option>
                <option value="資管系">資管系</option>
                <option value="企管系">企管系</option>
                <option value="會計系">會計系</option>
              </select>
            </div>
            <button @click="clearFilters" class="clear-btn">
              🧹 清除篩選
            </button>
          </div>
        </div>

        <!-- 資料表格 -->
        <div class="table-section">
          <div class="table-controls">
            <button @click="showAddModal = true" class="add-btn">
              ➕ 新增資料
            </button>
            <button @click="batchSave" class="save-btn" :disabled="!hasChanges">
              💾 批次儲存
            </button>
            <span class="data-count">總共 {{ totalRecords }} 筆資料</span>
          </div>

          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>
                    <input 
                      type="checkbox" 
                      v-model="selectAll"
                      @change="toggleSelectAll"
                    />
                  </th>
                  <th @click="sortBy('studentId')">
                    學號 
                    <span class="sort-icon">{{ getSortIcon('studentId') }}</span>
                  </th>
                  <th @click="sortBy('name')">
                    姓名
                    <span class="sort-icon">{{ getSortIcon('name') }}</span>
                  </th>
                  <th @click="sortBy('department')">
                    科系
                    <span class="sort-icon">{{ getSortIcon('department') }}</span>
                  </th>
                  <th @click="sortBy('score')">
                    成績
                    <span class="sort-icon">{{ getSortIcon('score') }}</span>
                  </th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(record, index) in paginatedData" :key="record.id">
                  <td>
                    <input 
                      type="checkbox" 
                      v-model="record.selected"
                      @change="updateSelectAll"
                    />
                  </td>
                  <td>
                    <input 
                      v-if="record.editing"
                      v-model="record.studentId"
                      type="text"
                      class="edit-input"
                    />
                    <span v-else>{{ record.studentId }}</span>
                  </td>
                  <td>
                    <input 
                      v-if="record.editing"
                      v-model="record.name"
                      type="text"
                      class="edit-input"
                    />
                    <span v-else>{{ record.name }}</span>
                  </td>
                  <td>
                    <select 
                      v-if="record.editing"
                      v-model="record.department"
                      class="edit-select"
                    >
                      <option value="資管系">資管系</option>
                      <option value="企管系">企管系</option>
                      <option value="會計系">會計系</option>
                    </select>
                    <span v-else>{{ record.department }}</span>
                  </td>
                  <td>
                    <input 
                      v-if="record.editing"
                      v-model="record.score"
                      type="number"
                      min="0"
                      max="100"
                      class="edit-input"
                    />
                    <span v-else>{{ record.score }}</span>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <template v-if="record.editing">
                        <button @click="saveRecord(record)" class="save-record-btn">
                          💾
                        </button>
                        <button @click="cancelEdit(record)" class="cancel-btn">
                          ❌
                        </button>
                      </template>
                      <template v-else>
                        <button @click="editRecord(record)" class="edit-btn">
                          ✏️
                        </button>
                        <button @click="deleteRecord(record)" class="delete-btn">
                          🗑️
                        </button>
                      </template>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分頁控制 -->
          <div class="pagination-section">
            <div class="pagination-info">
              <span>每頁顯示：</span>
              <select v-model="pageSize" @change="updatePagination" class="page-size-select">
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
              <span>共 {{ totalPages }} 頁</span>
            </div>
            <div class="pagination-controls">
              <button 
                @click="goToPage(1)" 
                :disabled="currentPage === 1"
                class="page-btn"
              >
                ⏮️
              </button>
              <button 
                @click="goToPage(currentPage - 1)" 
                :disabled="currentPage === 1"
                class="page-btn"
              >
                ⬅️
              </button>
              <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
              <button 
                @click="goToPage(currentPage + 1)" 
                :disabled="currentPage === totalPages"
                class="page-btn"
              >
                ➡️
              </button>
              <button 
                @click="goToPage(totalPages)" 
                :disabled="currentPage === totalPages"
                class="page-btn"
              >
                ⏭️
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 新增資料模態框 -->
    <div v-if="showAddModal" class="modal-overlay" @click="showAddModal = false">
      <div class="modal-content" @click.stop>
        <h3>新增學生資料</h3>
        <form @submit.prevent="addNewRecord">
          <div class="form-group">
            <label>學號：</label>
            <input v-model="newRecord.studentId" type="text" required />
          </div>
          <div class="form-group">
            <label>姓名：</label>
            <input v-model="newRecord.name" type="text" required />
          </div>
          <div class="form-group">
            <label>科系：</label>
            <select v-model="newRecord.department" required>
              <option value="">請選擇科系</option>
              <option value="資管系">資管系</option>
              <option value="企管系">企管系</option>
              <option value="會計系">會計系</option>
            </select>
          </div>
          <div class="form-group">
            <label>成績：</label>
            <input v-model="newRecord.score" type="number" min="0" max="100" required />
          </div>
          <div class="modal-actions">
            <button type="submit" class="confirm-btn">確認新增</button>
            <button type="button" @click="showAddModal = false" class="cancel-btn">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 響應式數據
const currentUser = ref('管理者')
const currentTime = ref('')
const selectedFile = ref(null)
const isUploading = ref(false)
const searchKeyword = ref('')
const dateFilter = ref('')
const categoryFilter = ref('')
const selectAll = ref(false)
const hasChanges = ref(false)
const sortField = ref('')
const sortDirection = ref('asc')
const currentPage = ref(1)
const pageSize = ref(25)
const showAddModal = ref(false)
const newRecord = ref({
  studentId: '',
  name: '',
  department: '',
  score: ''
})

const studentData = ref([])

// 模板引用
const fileInput = ref(null)

// 計算屬性
const filteredData = computed(() => {
  let data = [...studentData.value]
  
  if (searchKeyword.value) {
    data = data.filter(record => 
      record.studentId.includes(searchKeyword.value) ||
      record.name.includes(searchKeyword.value)
    )
  }
  
  if (categoryFilter.value) {
    data = data.filter(record => record.department === categoryFilter.value)
  }
  
  return data
})

const sortedData = computed(() => {
  if (!sortField.value) return filteredData.value
  
  return [...filteredData.value].sort((a, b) => {
    const aVal = a[sortField.value]
    const bVal = b[sortField.value]
    
    if (sortDirection.value === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return sortedData.value.slice(start, end)
})

const totalRecords = computed(() => filteredData.value.length)

const totalPages = computed(() => Math.ceil(totalRecords.value / pageSize.value))

// 方法
const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-TW')
}

const handleLogout = () => {
  if (confirm('確定要登出嗎？')) {
    router.push('/login')
  }
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
  try {
    // 模擬上傳
    await new Promise(resolve => setTimeout(resolve, 2000))
    alert('檔案上傳成功！')
    selectedFile.value = null
    fileInput.value.value = ''
  } catch (error) {
    alert('上傳失敗：' + error.message)
  } finally {
    isUploading.value = false
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

// 生命週期掛鉤
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
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

/* 表格區域 */
.table-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.add-btn, .save-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.add-btn {
  background: #4caf50;
  color: white;
}

.save-btn {
  background: #2196f3;
  color: white;
}

.add-btn:hover {
  background: #45a049;
}

.save-btn:hover:not(:disabled) {
  background: #1976d2;
}

.data-count {
  margin-left: auto;
  color: #666;
  font-size: 14px;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background-color: #f8f9fa;
  padding: 12px;
  text-align: left;
  border-bottom: 2px solid #e0e0e0;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
}

.data-table th:hover {
  background-color: #e9ecef;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.sort-icon {
  margin-left: 4px;
  font-size: 12px;
}

.edit-input, .edit-select {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.edit-btn, .delete-btn, .save-record-btn, .cancel-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.edit-btn:hover {
  background-color: #e3f2fd;
}

.delete-btn:hover {
  background-color: #ffebee;
}

.save-record-btn:hover {
  background-color: #e8f5e8;
}

.cancel-btn:hover {
  background-color: #ffebee;
}

/* 分頁控制 */
.pagination-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}

.pagination-info {
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
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f5f5f5;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
  margin: 0 8px;
}

/* 模態框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  min-width: 400px;
  max-width: 500px;
}

.modal-content h3 {
  margin: 0 0 20px 0;
  color: #212121;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  color: #212121;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.modal-actions .confirm-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.modal-actions .cancel-btn {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
</style>
