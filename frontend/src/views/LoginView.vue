<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="system-title">🎓 學生資料分析系統</h1>
      </div>
      <!-- @submit = v-on:submit 的縮寫，監聽表單提交事件
          .prevent = 事件修飾符，等同於呼叫 event.preventDefault()
          提交時避免重新載入畫面或跳轉-->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用戶名/帳號</label>
          <input
            id="username"
            v-model="loginForm.username"
            type="text"
            class="form-input"
            placeholder="請輸入用戶名"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="password">密碼</label>
          <input
            id="password"
            v-model="loginForm.password"
            type="password"
            class="form-input"
            placeholder="請輸入密碼"
            required
          />
        </div>
        
        <button type="submit" class="login-btn" :disabled="isLoading">
          {{ isLoading ? '登入中...' : '登入' }}
        </button>
      </form>
      
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/auth.js'

const router = useRouter()

// 響應式數據
const loginForm = ref({
  username: '',
  password: ''
})
const isLoading = ref(false)
const errorMessage = ref('')

// 生命週期掛鉤
onMounted(() => {
  // 如果已經登入，直接跳轉到主控台
  if (authService.isAuthenticated()) {
    router.push('/dashboard')
  }
})

// 方法
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    errorMessage.value = '請輸入用戶名和密碼'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  
  try {
    const result = await authService.login(loginForm.value.username, loginForm.value.password)
    if (result.success) {
      // 登入成功，跳轉到主控台
      router.push('/dashboard')
    }
  } catch (error) {
    errorMessage.value = error.message
    console.error('登入錯誤:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  padding: 20px;
}

.login-card {
  width: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.system-title {
  color: #1976d2;
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.login-form {
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

.form-input {
  width: 100%;
  height: 40px;
  padding: 0 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #1976d2;
}

.login-btn {
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

.login-btn:hover:not(:disabled) {
  background-color: #1565c0;
}

.login-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
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
</style>
