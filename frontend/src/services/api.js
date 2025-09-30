// API服務 - 統一處理HTTP請求
import { authService } from './auth.js'

const API_BASE_URL = 'http://localhost:5000/api'

// 創建一個通用的fetch包裝器
async function apiRequest(url, options = {}) {
  const token = authService.getToken()
  console.log('API請求URL:', `${API_BASE_URL}${url}`)
  console.log('Token:', token ? `${token.substring(0, 20)}...` : 'null')
  
  // 設置默認headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  // 如果有token，加入Authorization header
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
    console.log('Authorization header已設置')
  } else {
    console.warn('沒有找到Token!')
  }

  const config = {
    ...options,
    headers
  }

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, config)
    
    // 如果是401未授權，清除token並跳轉到登入頁面
    if (response.status === 401) {
      authService.logout()
      window.location.href = '/login'
      throw new Error('未授權，請重新登入')
    }

    // 如果響應不是JSON格式，直接返回response
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      return response
    }

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || `HTTP錯誤: ${response.status}`)
    }

    return data
  } catch (error) {
    console.error('API請求錯誤:', error)
    throw error
  }
}

// API服務對象
export const apiService = {
  // GET請求
  get(url) {
    return apiRequest(url, { method: 'GET' })
  },

  // POST請求
  post(url, data) {
    return apiRequest(url, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  },

  // PUT請求
  put(url, data) {
    return apiRequest(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  },

  // DELETE請求
  delete(url) {
    return apiRequest(url, { method: 'DELETE' })
  },

  // 檔案上傳請求
  upload(url, formData) {
    const token = authService.getToken()
    const headers = {}
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return fetch(`${API_BASE_URL}${url}`, {
      method: 'POST',
      headers,
      body: formData
    }).then(response => {
      if (response.status === 401) {
        authService.logout()
        window.location.href = '/login'
        throw new Error('未授權，請重新登入')
      }
      return response.json()
    })
  },

  // CRUD 操作輔助函數
  crud: {
    // 獲取表格數據（分頁）
    getTableData(tableName, params = {}) {
      const { page = 1, limit = 50, search = '' } = params
      const queryParams = new URLSearchParams({ page, limit, search })
      return apiService.get(`/database/tables/${tableName}/data?${queryParams}`)
    },

    // 新增資料
    createRow(tableName, data) {
      return apiService.post(`/database/tables/${tableName}/data`, data)
    },

    // 更新資料
    updateRow(tableName, rowId, data) {
      return apiService.put(`/database/tables/${tableName}/data/${rowId}`, data)
    },

    // 刪除資料
    deleteRow(tableName, rowId) {
      return apiService.delete(`/database/tables/${tableName}/data/${rowId}`)
    }
  }
}

// 常用的API端點
export const API_ENDPOINTS = {
  // 認證相關
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    PROFILE: '/auth/profile',
    LOGOUT: '/auth/logout'
  },
  
  // 檔案管理
  FILES: '/files',
  FILE: {
    UPLOAD: '/upload',
    SHEETS: '/sheets',
    READ_COLUMNS: '/read_columns',
    DATA: '/data'
  },
  SHEETS: '/sheets',
  READ_COLUMNS: '/read_columns',
  RAW_DATA: '/raw_data',

  // 資料庫相關
  DATABASE: {
    TABLES: '/database_tables',
    TABLE_COLUMNS: '/table_columns',
    NEW_TABLES: '/database/tables',
    TABLE_COUNT: '/database/tables',
    TABLE_DATA: '/database/tables', // 用於 CRUD 操作
    CREATE_ROW: '/database/tables',
    UPDATE_ROW: '/database/tables',
    DELETE_ROW: '/database/tables'
  },

  // 統計分析
  COLUMN_STATS: '/column_stats',
  MULTI_SUBJECT_STATS: '/multi_subject_stats',
  YEARLY_ADMISSION_STATS: '/yearly_admission_stats',
  SCHOOL_SOURCE_STATS: '/school_source_stats',
  ADMISSION_METHOD_STATS: '/admission_method_stats',
  GEOGRAPHIC_STATS: '/geographic_stats',
  
  STATS: {
    COLUMN: '/column_stats',
    MULTI_SUBJECT: '/multi_subject_stats',
    YEARLY_ADMISSION: '/yearly_admission_stats',
    SCHOOL_SOURCE: '/school_source_stats',
    ADMISSION_METHOD: '/admission_method_stats',
    GEOGRAPHIC: '/geographic_stats',
    TOP_SCHOOLS: '/top_schools_stats'
  },
  
  // 前20大入學高中
  TOP_SCHOOLS_STATS: '/top_schools_stats',
  
  // 大一各科平均成績
  SUBJECT_AVERAGE_STATS: '/subject_average_stats',
  
  // 性別科目成績分析
  GENDER_SUBJECT_STATS: '/analysis/gender-subject',
  
  // 入學管道科目成績分析
  ADMISSION_SUBJECT_STATS: '/analysis/admission-subject'
}
