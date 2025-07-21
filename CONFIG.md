# 🎓 學生資料分析系統 - 配置說明

## 📋 項目概述
這是一個基於 Vue.js 3 和 Element Plus 的學生資料分析系統，提供數據管理、分析和用戶管理功能。

## 🚀 快速開始

### 1. 安裝依賴
```bash
cd frontend
npm install
```

### 2. 啟動開發服務器
```bash
npm run dev
```

### 3. 打包生產版本
```bash
npm run build
```

## 🏗️ 項目結構
```
frontend/
├── public/                 # 靜態資源
├── src/
│   ├── components/         # 可重用組件
│   ├── views/             # 頁面組件
│   │   ├── LoginView.vue           # 登入頁面
│   │   ├── DashboardView.vue       # 主控台
│   │   ├── DataManagementView.vue  # 數據管理
│   │   ├── AnalysisView.vue        # 數據分析
│   │   └── UserManagementView.vue  # 用戶管理
│   ├── router/            # 路由配置
│   │   └── index.js       # 主路由文件
│   ├── services/          # 服務層
│   │   └── auth.js        # 認證服務
│   ├── styles/            # 樣式文件
│   │   └── global.css     # 全局樣式
│   ├── App.vue            # 根組件
│   ├── main.js            # 入口文件
│   └── style.css          # 基礎樣式
├── package.json           # 項目配置
└── vite.config.js        # Vite 配置
```

## 🔐 認證系統

### 預設帳號
| 用戶名 | 密碼 | 角色 | 權限 |
|--------|------|------|------|
| admin  | 123456 | 管理員 | 所有功能 |
| teacher | 123456 | 教師 | 數據查看和分析 |
| student | 123456 | 學生 | 基本查看權限 |

### 權限控制
- **管理員**: 可訪問所有頁面，包括用戶管理
- **教師**: 可訪問主控台、數據管理、數據分析
- **學生**: 僅可訪問主控台和基本數據查看

## 🛠️ 主要功能

### 1. 登入系統
- 用戶身份驗證
- 角色權限控制
- 自動跳轉功能

### 2. 主控台 (Dashboard)
- 系統概覽
- 統計數據顯示
- 最近活動記錄
- 快速操作按鈕

### 3. 數據管理
- Excel 檔案上傳
- 數據表格展示
- 內聯編輯功能
- 搜尋、篩選、排序
- 分頁控制

### 4. 數據分析
- 快速分析模板
- 自定義分析建構器
- 圖表展示
- 報告匯出

### 5. 用戶管理 (管理員專用)
- 用戶列表管理
- 新增/編輯用戶
- 批量操作
- 角色權限設定

## 🎨 設計系統

### 主色調
- 主色: #1976d2 (藍色)
- 成功: #4caf50 (綠色)
- 警告: #ff9800 (橘色)
- 錯誤: #f44336 (紅色)

### 響應式設計
- 桌面: 1200px+
- 平板: 768px - 1199px
- 手機: < 768px

## 🔧 開發配置

### 路由配置
路由採用 Vue Router 4，包含：
- 路由守衛 (認證檢查)
- 權限控制
- 頁面標題設定

### 狀態管理
使用 localStorage 進行簡單狀態管理：
- `isAuthenticated`: 登入狀態
- `userRole`: 用戶角色
- `userName`: 用戶名稱
- `userId`: 用戶ID

### API 服務
認證服務 (`services/auth.js`) 提供：
- `login()`: 用戶登入
- `logout()`: 用戶登出
- `isAuthenticated()`: 檢查登入狀態
- `getCurrentUser()`: 獲取當前用戶
- `hasRole()`: 角色檢查

## 📱 頁面功能說明

### LoginView.vue
- 用戶登入表單
- 表單驗證
- 錯誤訊息顯示
- 自動跳轉

### DashboardView.vue
- 統計卡片展示
- 活動時間軸
- 快速操作區域
- 實時時間顯示

### DataManagementView.vue
- 檔案上傳功能
- 數據表格 (可編輯)
- 搜尋篩選功能
- 新增/編輯 Modal

### AnalysisView.vue
- 快速分析選項
- 自定義分析建構器
- 圖表預覽區域
- 結果匯出功能

### UserManagementView.vue
- 用戶列表表格
- 批量操作功能
- 用戶編輯 Modal
- 角色權限管理

## 🎯 部署說明

### 開發環境
```bash
npm run dev
```
訪問 http://localhost:5173

### 生產環境
```bash
npm run build
npm run preview
```

## 📊 數據格式

### 學生資料 Excel 格式
建議的 Excel 檔案格式：
- 學號 (studentId)
- 姓名 (name) 
- 科系 (department)
- 成績 (score)
- 入學年度 (admissionYear)
- 入學管道 (admissionType)
- 地區 (region)

## 🔍 測試帳號說明

系統預設了三種角色的測試帳號：

1. **管理員帳號**
   - 帳號: admin
   - 密碼: 123456
   - 可訪問所有功能

2. **教師帳號**
   - 帳號: teacher  
   - 密碼: 123456
   - 可訪問數據分析功能

3. **學生帳號**
   - 帳號: student
   - 密碼: 123456
   - 僅能查看基本數據

## 🚨 注意事項

1. 這是演示版本，實際部署時請：
   - 更換真實的 API 端點
   - 實作真實的數據庫連接
   - 加強安全性驗證
   - 使用環境變數管理敏感資訊

2. 目前使用 localStorage 存儲認證資訊，生產環境建議使用：
   - JWT Token
   - Refresh Token 機制
   - Session 管理

3. 檔案上傳功能需要後端 API 支援

## 📝 後續開發建議

1. **後端整合**
   - 實作 REST API
   - 數據庫設計
   - 檔案上傳處理

2. **功能增強**
   - 更多圖表類型
   - 報告模板
   - 數據匯出格式

3. **效能優化**
   - 組件懶載入
   - 數據虛擬化
   - 圖片優化

4. **安全加強**
   - HTTPS 配置
   - CSRF 防護
   - XSS 防護
