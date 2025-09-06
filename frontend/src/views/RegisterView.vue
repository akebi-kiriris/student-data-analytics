<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h1 class="system-title">🎓 用戶註冊</h1>
        <p class="subtitle">學生資料分析系統</p>
      </div>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">用戶名</label>
          <input
            id="username"
            v-model="registerForm.username"
            type="text"
            class="form-input"
            placeholder="請輸入用戶名"
            required
            minlength="3"
          />
        </div>
        
        <div class="form-group">
          <label for="email">電子郵件</label>
          <input
            id="email"
            v-model="registerForm.email"
            type="email"
            class="form-input"
            placeholder="請輸入電子郵件"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="password">密碼</label>
          <input
            id="password"
            v-model="registerForm.password"
            type="password"
            class="form-input"
            placeholder="請輸入密碼"
            required
            minlength="6"
          />
        </div>
        
        <div class="form-group">
          <label for="confirmPassword">確認密碼</label>
          <input
            id="confirmPassword"
            v-model="registerForm.confirmPassword"
            type="password"
            class="form-input"
            placeholder="請再次輸入密碼"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="role">用戶角色</label>
          <select
            id="role"
            v-model="registerForm.role"
            class="form-select"
            required
          >
            <option value="viewer">觀察者 - 僅查看數據</option>
            <option value="user">一般用戶 - 上傳和分析數據</option>
            <option value="admin">管理員 - 完整權限</option>
          </select>
        </div>
        
        <button type="submit" class="register-btn" :disabled="isLoading">
          {{ isLoading ? '註冊中...' : '註冊' }}
        </button>
      </form>
      
      <div class="login-link">
        <p>已有帳號？ <router-link to="/login">立即登入</router-link></p>
      </div>
      
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/auth.js'

const router = useRouter()

// 響應式數據
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'user'
})
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// 方法
const handleRegister = async () => {
  // 驗證表單
  if (!registerForm.value.username || !registerForm.value.email || 
      !registerForm.value.password || !registerForm.value.confirmPassword) {
    errorMessage.value = '請填寫所有必填欄位'
    return
  }

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    errorMessage.value = '密碼與確認密碼不一致'
    return
  }

  if (registerForm.value.password.length < 6) {
    errorMessage.value = '密碼長度至少需要6個字符'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    const result = await authService.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password,
      registerForm.value.role
    )
    
    if (result.success) {
      successMessage.value = '註冊成功！請使用新帳號登入。'
      // 清除表單
      registerForm.value = {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'user'
      }
      // 3秒後跳轉到登入頁面
      setTimeout(() => {
        router.push('/login')
      }, 3000)
    }
  } catch (error) {
    errorMessage.value = error.message
    console.error('註冊錯誤:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  padding: 20px;
}

.register-card {
  width: 450px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 40px;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.system-title {
  color: #1976d2;
  font-size: 24px;
  font-weight: bold;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.register-form {
  width: 100%;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #212121;
  font-weight: 500;
}

.form-input, .form-select {
  width: 100%;
  height: 40px;
  padding: 0 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #1976d2;
}

.register-btn {
  width: 100%;
  height: 40px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.register-btn:hover:not(:disabled) {
  background-color: #1565c0;
}

.register-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 20px;
}

.login-link p {
  color: #666;
  font-size: 14px;
}

.login-link a {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background-color: #ffebee;
  color: #f44336;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
}

.success-message {
  margin-top: 16px;
  padding: 12px;
  background-color: #e8f5e8;
  color: #4caf50;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
}
</style>
