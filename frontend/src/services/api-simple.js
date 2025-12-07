// 超級簡化版 API 服務 - 完全避免模組依賴問題

// 硬編碼配置，完全避免導入任何其他模組
const CONFIG = {
  development: 'http://localhost:5000/api',
  production: 'https://student-analytics-backend-470050740360.asia-east1.run.app/api'
}

// 最簡單的環境檢測
let API_BASE_URL = CONFIG.development
try {
  if (typeof window !== 'undefined' && window.location) {
    const hostname = window.location.hostname
    if (hostname.includes('web.app') || hostname.includes('firebaseapp.com') || 
        hostname.includes('vercel.app') || hostname.includes('netlify.app') ||
        (hostname !== 'localhost' && !hostname.includes('127.0.0.1'))) {
      API_BASE_URL = CONFIG.production
    }
  }
} catch (e) {
  // 如果出錯，使用生產環境
  API_BASE_URL = CONFIG.production
}

const TOKEN_KEY = 'access_token'

const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY) || localStorage.getItem('token')
  } catch (e) {
    return null
  }
}

const clearToken = () => {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_email')
  } catch (e) {
    // 忽略錯誤
  }
}

// 最基本的 fetch 包裝器
async function apiRequest(url, options = {}) {
  const token = getToken()
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const config = {
    ...options,
    headers
  }

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, config)
    
    if (response.status === 401) {
      clearToken()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      throw new Error('未授權，請重新登入')
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('API請求失敗:', error)
    throw error
  }
}

// API 服務對象 - 最簡化
export const simpleApiService = {
  get: (url) => apiRequest(url, { method: 'GET' }),
  post: (url, data) => apiRequest(url, { method: 'POST', body: JSON.stringify(data) }),
  put: (url, data) => apiRequest(url, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (url) => apiRequest(url, { method: 'DELETE' }),
  
  // 上傳檔案
  upload: async (url, formData) => {
    const token = getToken()
    const headers = {}
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        method: 'POST',
        headers,
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return response.json()
    } catch (error) {
      console.error('上傳失敗:', error)
      throw error
    }
  },

  // 檔案下載
  downloadFile: async (url) => {
    const token = getToken()
    const headers = {}
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        method: 'GET',
        headers
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // 取得下載 URL
      const data = await response.json()
      if (data.download_url) {
        // 開啟下載連結
        window.open(data.download_url, '_blank')
        return data
      } else {
        throw new Error('無法取得下載連結')
      }
    } catch (error) {
      console.error('下載失敗:', error)
      throw error
    }
  }
}

// API 端點常數 - 完全靜態
export const SIMPLE_API_ENDPOINTS = {
  DATABASE_TABLES: '/database/tables',
  TABLE_COUNT: '/database/tables',
  UPLOAD: '/upload',
  FILES: '/files'
}

export default simpleApiService