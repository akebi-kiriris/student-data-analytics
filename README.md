# 學生數據分析系統

這是一個用於分析學生數據的網頁應用系統，提供多維度的數據分析和視覺化功能。

## 🌐 線上體驗

**系統已部署到雲端，可直接使用：**
- 🚀 **線上系統**：https://student-analytics-prod.web.app
- 📱 **響應式設計**：支援電腦、平板、手機使用
- ⚡ **全球 CDN**：快速載入，穩定運行

## 功能特點

- 📊 數據視覺化分析
- 📈 動態圖表展示
- 📁 Excel 檔案上傳和處理
- 🔍 多維度數據分析：
  - 入學管道科目成績分析
  - 高中類型科目成績分析
  - 地區科目成績分析
  - 學生來源分析
  - 成績統計分析

## 系統要求

### 本地開發版本
- Windows 10 或更高版本
- Git（通常已安裝）
- Node.js 18.x 或更高版本
- Python 3.9 或更高版本

## 快速開始

### 🌐 使用雲端版本（推薦）

直接訪問 [https://student-analytics-prod.web.app](https://student-analytics-prod.web.app) 即可開始使用！

---

### 💻 本地開發設置

### 1. 檢查並安裝必要軟體

#### 檢查 Git（通常已安裝）
```powershell
git --version
```

#### 安裝 Node.js（如果尚未安裝）
1. 前往 https://nodejs.org/
2. 下載並安裝 LTS 版本（建議 18.x 或 20.x）
3. 安裝完成後重新開啟 PowerShell，檢查：
```powershell
node --version
npm --version
```

#### 檢查 Python（通常已安裝）
```powershell
python --version
# 或
py --version
```

### 2. 下載專案

```powershell
# 克隆專案到桌面
cd C:\Users\[您的用戶名]\Desktop
git clone https://github.com/akebi-kiriris/student-data-analytics.git
cd student-data-analytics
git checkout feature/top-schools-analysis
```

### 3. 設置後端環境

```powershell
# 進入後端目錄
cd backend

# 建立 Python 虛擬環境
python -m venv venv
# 如果上述命令失效，嘗試：py -m venv venv

# 啟動虛擬環境
venv\Scripts\activate

# 安裝後端依賴
pip install -r requirements.txt
```

### 4. 設置前端環境

```powershell
# 開啟新的 PowerShell 視窗，進入前端目錄
cd C:\Users\[您的用戶名]\Desktop\student-data-analytics\frontend

# 安裝前端依賴
npm install
```

### 5. 啟動系統

#### 方法一：手動啟動（推薦）
```powershell
# 步驟1：啟動後端（在 backend 目錄）
cd backend
venv\Scripts\activate
python app.py
```
後端啟動成功會顯示：`Running on http://127.0.0.1:5000`

```powershell
# 步驟2：開啟新的 PowerShell 視窗，啟動前端
cd frontend
npm run dev
```
前端啟動成功會顯示：`Local: http://localhost:5173/`

#### 方法二：使用啟動腳本
```powershell
# 注意：使用此方法前，請確保已建立虛擬環境並安裝依賴
.\start_servers.bat
```
**重要提醒**：如果後端啟動失敗，請使用方法一手動啟動，確保虛擬環境正確啟動。

### 6. 訪問系統

- **雲端版本**：https://student-analytics-prod.web.app
- **本地前端**：http://localhost:5173
- **本地後端 API**：http://localhost:5000

## 使用說明

1. 🌐 **訪問系統**：線上版本或本地版本
2. 📝 **註冊登入**：建立帳號並登入（雲端版本需要）
3. 📁 **上傳檔案**：選擇 Excel 數據檔案
4. 🔍 **選擇分析**：挑選分析類型和參數
5. 📈 **查看結果**：瀏覽分析結果和圖表
6. 💾 **匯出圖表**：可下載圖片格式

## 常見問題

### Python 虛擬環境無法建立
```powershell
# 如果遇到權限問題
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然後重新嘗試
python -m venv venv
```

### 端口被佔用
```powershell
# 檢查端口使用情況
netstat -ano | findstr :5000
netstat -ano | findstr :5173
```

### Node.js 相關錯誤
確保 Node.js 版本為 18.x 或更高，並重新安裝依賴：
```powershell
cd frontend
npm cache clean --force
npm install
```

### Google Cloud 模組錯誤
如果本地開發時出現 `ModuleNotFoundError: No module named 'google.cloud'` 錯誤：
```powershell
# 方法1：安裝雲端依賴（可選）
pip install google-cloud-storage

# 方法2：忽略此錯誤（系統會自動使用本地儲存）
# 此錯誤不影響本地開發功能
```

## 技術棧

- **前端**：Vue.js 3, Element Plus, ECharts
- **後端**：Python Flask, Pandas, SQLAlchemy  
- **數據庫**：SQLite
- **雲端架構**：
  - 🔥 Firebase Hosting (前端)
  - ☁️ Google Cloud Run (後端)
  - 🌐 全球 CDN 加速
  - 🔒 HTTPS 安全傳輸

## 部署資訊

### 🌐 雲端架構
```
用戶瀏覽器 → Firebase Hosting → Cloud Run API → SQLite 資料庫
     ↑              ↑              ↑            ↑
   HTTPS 加密    全球 CDN 快取   容器自動擴展   高效能存取
```
