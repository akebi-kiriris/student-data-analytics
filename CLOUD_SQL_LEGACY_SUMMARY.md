# Cloud SQL 架構與設定整合紀錄（已棄用）

> 本文件整合原 `CLOUD_SQL_IMPLEMENTATION.md` 與 `Cloud_SQL_Setup_Guide.md`，僅供歷史參考，現階段專案已不再使用 Cloud SQL。

---

## 一、Cloud SQL 架構與多租戶設計

### 1. 資料庫動態切換
- 透過 `get_database_url()` 函數，根據環境變數自動選擇 PostgreSQL（Cloud SQL）或 SQLite（本地開發）。
- 主要環境變數：
  - `CLOUD_SQL_CONNECTION_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_NAME`

### 2. 多租戶表格結構
- 所有資料表皆新增 `user_id` 欄位，資料隔離。
- 插入資料時自動記錄上傳者 ID。

### 3. 查詢與 API 權限
- 查詢 API 需加上 `WHERE user_id = :user_id` 過濾。
- 表格列表 API 只顯示當前管理員上傳的表格。

### 4. 依賴與安裝
- 需安裝 `pg8000` 驅動（`requirements-cloudsql.txt`）。
- 本地開發不需安裝，雲端部署時安裝。

---

## 二、Cloud SQL 設定與部署流程

### 1. 建立 Cloud SQL 實例
- 使用 GCP Console 或 gcloud CLI 建立 PostgreSQL 實例。
- 取得連接名稱（格式：`project-id:region:instance-name`）。

### 2. 建立資料庫與使用者
- 建立資料庫（如 `student_analytics`）。
- 建議建立專用 DB 使用者。

### 3. 設定環境變數
- 建立 `.env` 檔案或於部署時設定。
- 本地測試可用 Cloud SQL Proxy 連接。

### 4. Dockerfile 與部署
- Dockerfile 需安裝 Cloud SQL 驅動。
- Cloud Run 部署時加上 `--add-cloudsql-instances` 與環境變數。

### 5. 故障排除
- 連接失敗、認證失敗、找不到資料庫等常見問題與解法。

### 6. 成本與切換
- Cloud SQL 有免費額度，開發/測試可用低規格。
- 移除環境變數即可切回 SQLite。

---

## 三、測試與驗證清單

- [ ] Cloud SQL 實例與資料庫建立
- [ ] 環境變數設定
- [ ] requirements 安裝
- [ ] 本地/雲端連線測試
- [ ] 上傳/查詢/分析功能測試
- [ ] CRUD 功能正常

---

## 四、設計原則與最佳實踐

1. 本地優先，無環境變數自動用 SQLite
2. 零侵入，開發體驗不變
3. 自動切換資料庫
4. 多租戶資料隔離（user_id）
5. 查詢語法同時支援 SQLite/PostgreSQL
6. 敏感資訊用 Secret Manager 管理
7. 建議啟用自動備份與監控

---

> 本文件僅供歷史備查，現階段專案已改用 SQLite + 雲端儲存備份，Cloud SQL 相關設定與程式碼已移除。
