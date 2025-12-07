# Cloud SQL 多租戶架構實作總結

## ✅ 已完成的改動

### 1. 資料庫動態切換功能

**檔案**: `backend/app.py`

添加了 `get_database_url()` 函數，根據環境變數自動選擇資料庫：

```python
def get_database_url():
    """
    - 有 Cloud SQL 環境變數 → 使用 PostgreSQL
    - 無環境變數 → 使用 SQLite（本地開發）
    """
```

**環境變數**：
- `CLOUD_SQL_CONNECTION_NAME`: Cloud SQL 實例名稱
- `DB_USER`: 資料庫使用者
- `DB_PASSWORD`: 資料庫密碼  
- `DB_NAME`: 資料庫名稱

**本地開發**: 不設定任何環境變數，自動使用 SQLite ✅

---

### 2. 多租戶表格結構

**修改**: `create_excel_table()` 函數

所有 Excel 資料表現在都包含 `user_id` 欄位：

```python
cols = [
    Column('id', Integer, primary_key=True),
    Column('user_id', String(50), nullable=False, index=True),  # 新增
    # ... 其他欄位
]
```

**效果**: 不同管理員的資料在同一張表中，但通過 `user_id` 隔離 ✅

---

### 3. 自動記錄上傳者

**修改**: `process_excel_data()` 函數

插入資料時自動添加當前管理員的 ID：

```python
current_user_id = get_jwt_identity()
for _, row in df.iterrows():
    row_dict = {'user_id': current_user_id}  # 自動添加
    # ... 處理其他欄位
```

**效果**: 每一行資料都知道是誰上傳的 ✅

---

### 4. 額外依賴文件

**新檔案**: `backend/requirements-cloudsql.txt`

```
pg8000==1.30.3  # PostgreSQL 驅動
```

**安裝方式**:
- 本地開發: 不需要安裝
- 雲端部署: `pip install -r requirements-cloudsql.txt`

---

## ⚠️ 需要繼續完成的改動

### 1. 查詢 API 添加 user_id 過濾

所有分析 API 都需要修改，只查詢當前管理員的資料：

```python
# ❌ 舊的查詢
query = f'SELECT * FROM {table_name}'

# ✅ 新的查詢
current_user_id = get_jwt_identity()
query = f'SELECT * FROM {table_name} WHERE user_id = :user_id'
params = {'user_id': current_user_id}
```

**需要修改的 API**:
- `/api/column_stats` ⚠️
- `/api/multi_subject_stats` ⚠️
- `/api/yearly_admission_stats` ⚠️
- `/api/school_source_stats` ⚠️
- `/api/admission_method_stats` ⚠️
- `/api/geographic_stats` ⚠️
- `/api/top_schools_stats` ⚠️
- `/api/subject_average_stats` ⚠️
- `/api/analysis/gender-subject` ⚠️
- `/api/analysis/admission-subject` ⚠️
- `/api/analysis/school-type-subject` ⚠️
- `/api/analysis/region-subject` ⚠️
- `/api/database/tables/<table_name>/data` (CRUD) ⚠️

---

### 2. 表格列表只顯示自己的

**修改**: `/api/database/tables` API

應該只列出當前管理員上傳的表格：

```python
current_user_id = get_jwt_identity()
# 從 uploaded_files 表查詢
SELECT DISTINCT table_name 
FROM uploaded_files 
WHERE user_id = :user_id
```

---

## 📋 測試清單

### 本地測試（SQLite）

- [ ] 啟動 backend: `python app.py`
- [ ] 確認顯示: `[INFO] 使用本地 SQLite 資料庫`
- [ ] 上傳 Excel 檔案成功
- [ ] 查看資料表列表
- [ ] 執行分析功能
- [ ] 確認資料有 `user_id` 欄位

### 雲端測試（Cloud SQL）

- [ ] 設定環境變數
- [ ] 啟動 backend
- [ ] 確認顯示: `[INFO] 使用 Cloud SQL: xxx`
- [ ] 測試所有功能

---

## 🎯 下一步

1. **批量修改查詢 API**：添加 `WHERE user_id = :user_id`
2. **修改表格列表 API**：只顯示自己的表格
3. **測試本地功能**：確保不影響現有功能
4. **準備 Cloud SQL**：建立實例、設定環境變數
5. **部署測試**：驗證雲端功能

---

## 💡 關鍵設計原則

1. **本地優先**: 不設環境變數就能用（SQLite）
2. **零侵入**: 本地開發體驗不變
3. **自動切換**: 根據環境變數自動選擇資料庫
4. **數據隔離**: 透過 user_id 實現多租戶
5. **向後相容**: 查詢語法同時支援 SQLite 和 PostgreSQL
