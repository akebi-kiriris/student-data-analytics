// 認證服務
export const authService = {
  // 登入
  login(username, password) {
    return new Promise((resolve, reject) => {
      // 模擬 API 調用
      setTimeout(() => {
        // 簡單的用戶驗證邏輯
        const users = {
          'admin': { password: '123456', role: 'admin', name: '管理員' },
          'teacher': { password: '123456', role: 'teacher', name: '教師' },
          'student': { password: '123456', role: 'student', name: '學生' }
        }

        if (users[username] && users[username].password === password) {
          const user = users[username]
          // 儲存認證資訊
          localStorage.setItem('isAuthenticated', 'true')
          localStorage.setItem('userRole', user.role)
          localStorage.setItem('userName', user.name)
          localStorage.setItem('userId', username)
          
          resolve({
            success: true,
            user: {
              id: username,
              name: user.name,
              role: user.role
            }
          })
        } else {
          reject({
            success: false,
            message: '用戶名或密碼錯誤'
          })
        }
      }, 1000) // 模擬網路延遲
    })
  },

  // 登出
  logout() {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userName')
    localStorage.removeItem('userId')
  },

  // 檢查是否已登入
  isAuthenticated() {
    return localStorage.getItem('isAuthenticated') === 'true'
  },

  // 獲取當前用戶資訊
  getCurrentUser() {
    if (!this.isAuthenticated()) {
      return null
    }

    return {
      id: localStorage.getItem('userId'),
      name: localStorage.getItem('userName'),
      role: localStorage.getItem('userRole')
    }
  },

  // 檢查用戶角色
  hasRole(role) {
    const userRole = localStorage.getItem('userRole')
    return userRole === role
  },

  // 檢查是否為管理員
  isAdmin() {
    return this.hasRole('admin')
  }
}
