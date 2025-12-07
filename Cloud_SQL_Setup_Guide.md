# Cloud SQL 設定指南

## 📋 前置準備

### 1. 確認已安裝的套件
```bash
# 檢查是否需要安裝 Cloud SQL 驅動
pip list | Select-String "pg8000"
```

如果沒有，安裝：
```bash
pip install -r requirements-cloudsql.txt
```

---

## 🔧 步驟一：建立 Cloud SQL 實例

### 1. 在 GCP Console 建立 PostgreSQL 實例

```bash
# 使用 gcloud CLI 建立（或在 Console 操作）
gcloud sql instances create student-analytics-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-east1 \
  --root-password=YOUR_SECURE_PASSWORD
```

**重要參數**：
- `student-analytics-db`: 實例名稱（可自訂）
- `POSTGRES_15`: PostgreSQL 版本
- `db-f1-micro`: 最小規格（測試用，免費額度）
- `asia-east1`: 區域（台灣）

### 2. 取得連接名稱

建立完成後，記下「連接名稱」：
```
格式：project-id:region:instance-name
範例：my-project-123456:asia-east1:student-analytics-db
```

---

## 🗄️ 步驟二：建立資料庫

```bash
# 建立資料庫
gcloud sql databases create student_analytics \
  --instance=student-analytics-db
```

或在 Cloud SQL Console 手動建立。

---

## 👤 步驟三：建立資料庫使用者（可選）

```bash
# 建立專用使用者（建議）
gcloud sql users create app_user \
  --instance=student-analytics-db \
  --password=APP_USER_PASSWORD
```

或使用預設的 `postgres` 使用者。

---

## 🔐 步驟四：設定環境變數

### 本地測試 Cloud SQL

建立 `backend/.env` 檔案：

```bash
# backend/.env
CLOUD_SQL_CONNECTION_NAME=your-project:asia-east1:student-analytics-db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_NAME=student_analytics
```

**注意**：`.env` 檔案不要提交到 Git！

### 載入環境變數（PowerShell）

```powershell
# 方法一：手動設定
$env:CLOUD_SQL_CONNECTION_NAME="your-project:asia-east1:student-analytics-db"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your-secure-password"
$env:DB_NAME="student_analytics"

# 方法二：從 .env 檔案載入（需要 python-dotenv）
pip install python-dotenv
```

---

## 🔌 步驟五：本地連接 Cloud SQL

### 方法 A：使用 Cloud SQL Proxy（推薦）

```bash
# 1. 下載 Cloud SQL Proxy
# Windows: https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe

# 2. 啟動 Proxy
cloud_sql_proxy.exe -instances=YOUR_CONNECTION_NAME=tcp:5432

# 3. 在另一個終端啟動應用
python app.py
```

### 方法 B：允許本地 IP（不安全，不推薦）

在 Cloud SQL Console → 連線 → 授權網路，新增你的公開 IP。

---

## ✅ 步驟六：測試連接

### 1. 修改 `app.py` 檢查資料庫連接

你的 `get_database_url()` 函數已經準備好了：

```python
def get_database_url():
    cloud_sql_connection = os.getenv('CLOUD_SQL_CONNECTION_NAME')
    
    if cloud_sql_connection:
        # 使用 Cloud SQL
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME', 'student_analytics')
        db_socket_dir = os.getenv('DB_SOCKET_DIR', '/cloudsql')
        
        return f'postgresql+pg8000://{db_user}:{db_password}@/{db_name}?unix_sock={db_socket_dir}/{cloud_sql_connection}/.s.PGSQL.5432'
    else:
        # 使用 SQLite（本地開發）
        return f'sqlite:///{DATABASE_PATH}'
```

### 2. 啟動應用

```bash
python app.py
```

**檢查輸出**：
```
[INFO] 使用 Cloud SQL: your-project:asia-east1:student-analytics-db
```

如果顯示：
```
[INFO] 使用本地 SQLite 資料庫
```
表示環境變數沒設定成功。

### 3. 測試上傳 Excel

- 登入系統
- 上傳一個 Excel 檔案
- 檢查是否成功存入 Cloud SQL

---

## 🚀 步驟七：部署到 Cloud Run

### 1. 修改 Dockerfile（如果有）

確保包含 Cloud SQL 驅動：

```dockerfile
COPY requirements.txt requirements-cloudsql.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-cloudsql.txt
```

### 2. 部署時設定環境變數

```bash
gcloud run deploy student-analytics-backend \
  --source . \
  --region asia-east1 \
  --set-env-vars CLOUD_SQL_CONNECTION_NAME=your-project:asia-east1:student-analytics-db \
  --set-env-vars DB_USER=postgres \
  --set-env-vars DB_NAME=student_analytics \
  --set-secrets DB_PASSWORD=db-password-secret:latest \
  --add-cloudsql-instances your-project:asia-east1:student-analytics-db
```

**重要**：
- `--add-cloudsql-instances`: 授權 Cloud Run 連接 Cloud SQL
- `--set-secrets`: 使用 Secret Manager 存儲密碼（更安全）

---

## 🔍 故障排除

### 問題 1：連接失敗

**錯誤**：`could not connect to server`

**解決**：
1. 檢查 Cloud SQL 實例是否啟動
2. 確認 Cloud SQL Proxy 是否執行
3. 驗證環境變數是否正確

### 問題 2：認證失敗

**錯誤**：`password authentication failed`

**解決**：
1. 確認 `DB_USER` 和 `DB_PASSWORD` 正確
2. 檢查使用者是否有權限存取該資料庫

### 問題 3：找不到資料庫

**錯誤**：`database "student_analytics" does not exist`

**解決**：
```bash
gcloud sql databases create student_analytics --instance=student-analytics-db
```

---

## 📊 驗證資料

### 連接到 Cloud SQL 檢視資料

```bash
# 使用 gcloud
gcloud sql connect student-analytics-db --user=postgres

# 進入後執行 SQL
\c student_analytics
\dt  -- 列出所有表格
SELECT * FROM "1_整理後總表_251207091530" LIMIT 10;
```

---

## 💰 成本考量

**Cloud SQL 免費額度**（每月）：
- db-f1-micro: 720 小時（1 個實例 24/7）
- 儲存空間: 30 GB
- 出站流量: 1 GB

**建議**：
- 開發/測試：使用 `db-f1-micro`
- 生產環境：根據需求升級

---

## 🔄 切換回 SQLite

只要移除環境變數即可：

```powershell
Remove-Item Env:CLOUD_SQL_CONNECTION_NAME
Remove-Item Env:DB_USER
Remove-Item Env:DB_PASSWORD
Remove-Item Env:DB_NAME
```

重啟應用，會自動切回 SQLite。

---

## ✅ 檢查清單

- [ ] Cloud SQL 實例已建立
- [ ] 資料庫 `student_analytics` 已建立
- [ ] 環境變數已設定
- [ ] Cloud SQL Proxy 已啟動（本地測試）
- [ ] `requirements-cloudsql.txt` 已安裝
- [ ] 應用顯示「使用 Cloud SQL」訊息
- [ ] 成功上傳 Excel 並存入 Cloud SQL
- [ ] 可以查詢和分析資料
- [ ] CRUD 功能正常運作

---

## 📝 下一步

1. **設定自動備份**：在 Cloud SQL Console 啟用自動備份
2. **監控**：設定 Cloud Monitoring 追蹤效能
3. **安全性**：使用 Secret Manager 管理敏感資訊
4. **讀寫分離**：如有需要，可建立讀取副本

有任何問題，請參考 [Cloud SQL 文件](https://cloud.google.com/sql/docs)
