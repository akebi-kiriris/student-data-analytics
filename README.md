# 學生數據分析系統

這是一個用於分析學生數據的網頁應用系統，提供多維度的數據分析和視覺化功能。

## 📝 重要註記

**目前提供假資料(students)功能，但有以下限制：**
- ✅ 支援到大一各科平均成績前（不含大一各科平均成績分析）
- ❌ 管理資料功能無法使用

後端需要進一步調整以完全支援此功能。

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

- Windows 10 或更高版本
- Git
- Node.js 18.x 或更高版本
- Python 3.9 或更高版本

## 快速開始

### 🌐 使用雲端版本（推薦）

直接訪問 [https://student-analytics-prod.web.app](https://student-analytics-prod.web.app) 即可開始使用！

---

### 💻 本地開發設置

#### 1. 下載專案

```powershell
git clone https://github.com/akebi-kiriris/student-data-analytics.git
cd student-data-analytics
```

#### 2. 設置後端

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. 設置前端

```powershell
cd frontend
npm install
```

#### 4. 啟動系統

**後端** (終端 1):
```powershell
cd backend
venv\Scripts\activate
python app.py
```

**前端** (終端 2):
```powershell
cd frontend
npm run dev
```

#### 5. 訪問系統

- **雲端版本**：https://student-analytics-prod.web.app
- **本地前端**：http://localhost:5173
- **本地後端 API**：http://localhost:5000

## 使用說明

1. 🌐 **訪問系統**：線上版本或本地版本
2. 📝 **註冊登入**：建立帳號並登入
3. 📁 **上傳檔案**：選擇 Excel 數據檔案
4. 🔍 **選擇分析**：挑選分析類型和參數
5. 📈 **查看結果**：瀏覽分析結果和圖表
6. 💾 **匯出圖表**：可下載圖片格式

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
