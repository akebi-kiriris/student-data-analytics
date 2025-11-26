// JWT認證服務
import { API_BASE_URL } from './api-config.js'

export const authService = {
  // 登入
  async login(username, password) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (response.ok) {
        // 儲存JWT Token和用戶資訊
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('user_id', data.user.id.toString())
        localStorage.setItem('username', data.user.username)
        localStorage.setItem('user_role', data.user.role)
        localStorage.setItem('user_email', data.user.email || '')
        
        return {
          success: true,
          user: data.user
        }
      } else {
        throw new Error(data.message || '登入失敗')
      }
    } catch (error) {
      throw new Error(error.message || '網路連接失敗')
    }
  },

  // 註冊
  async register(username, email, password, role = 'user') {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password, role })
      })

      const data = await response.json()

      if (response.ok) {
        return {
          success: true,
          message: data.message
        }
      } else {
        throw new Error(data.message || '註冊失敗')
      }
    } catch (error) {
      throw new Error(error.message || '網路連接失敗')
    }
  },

  // 登出
  async logout() {
    try {
      const token = this.getToken()
      if (token) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        })
      }
    } catch (error) {
      console.error('登出API調用失敗:', error)
    } finally {
      // 清除本地儲存
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('username')
      localStorage.removeItem('user_role')
      localStorage.removeItem('user_email')
    }
  },

  // 取得用戶資料
  async getProfile() {
    try {
      const token = this.getToken()
      if (!token) {
        throw new Error('未找到認證Token')
      }

      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      })

      const data = await response.json()

      if (response.ok) {
        return data.user
      } else {
        throw new Error(data.message || '獲取用戶資料失敗')
      }
    } catch (error) {
      throw new Error(error.message || '網路連接失敗')
    }
  },

  // 取得Token
  getToken() {
    return localStorage.getItem('access_token')
  },

  // 檢查是否已登入
  isAuthenticated() {
    const token = this.getToken()
    return !!token
  },

  // 獲取當前用戶資訊
  getCurrentUser() {
    if (!this.isAuthenticated()) {
      return null
    }

    return {
      id: localStorage.getItem('user_id'),
      username: localStorage.getItem('username'),
      role: localStorage.getItem('user_role'),
      email: localStorage.getItem('user_email')
    }
  },

  // 檢查用戶角色
  hasRole(role) {
    const userRole = localStorage.getItem('user_role')
    return userRole === role
  },

  // 檢查是否為管理員
  isAdmin() {
    return this.hasRole('admin')
  },

  // 檢查是否為用戶
  isUser() {
    return this.hasRole('user')
  },

  // 檢查是否為觀察者
  isViewer() {
    return this.hasRole('viewer')
  }
}
