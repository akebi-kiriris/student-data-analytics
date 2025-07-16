# 學生數據分析系統

這是一個用於分析學生數據的網頁應用系統。

## 專案結構

```
project/
├── frontend/         # Vue.js 前端應用
│   ├── src/         # 源代碼
│   ├── public/      # 靜態資源
│   └── ...
│
└── backend/         # Python Flask 後端應用
    ├── app.py      # 主應用程式
    └── ...
```

## 功能特點

- 檔案上傳和管理
- 數據視覺化分析
- 動態圖表展示
- 多維度數據分析
  - 每年入學生數量分析
  - 多科目分年平均分析
  - 地理區域分布分析
  - 入學管道分析

## 技術棧

### 前端
- Vue.js
- Element Plus
- ECharts
- Chart.js

### 後端
- Python
- Flask
- Pandas
- NumPy

## 安裝與運行

### 前端設置
```bash
cd frontend
npm install
npm run dev
```

### 後端設置
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 使用說明

1. 啟動前後端服務
2. 訪問 http://localhost:5173
3. 上傳 Excel 檔案
4. 選擇分析類型
5. 查看分析結果

## 開發團隊

[您的資訊]

## License

[選擇適當的授權]
