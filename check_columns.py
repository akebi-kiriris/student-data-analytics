import sqlite3

# 連接資料庫
conn = sqlite3.connect('backend/database/excel_data.db')
cursor = conn.cursor()

# 獲取所有表格
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', [table[0] for table in tables])

# 獲取特定表格的欄位信息
table_name = 'excel_107_113大一新生來源管道與成績分析_20250525_整理後總表'
cursor.execute(f"PRAGMA table_info('{table_name}');")
columns = cursor.fetchall()
print(f'\nColumns in {table_name}:')
for col in columns:
    print(f'{col[1]} - {col[2]}')

# 檢查哪些欄位可能是成績相關
print('\n可能的成績欄位:')
for col in columns:
    col_name = col[1]
    if any(keyword in col_name for keyword in ['成績', '分數', '分', '總分', '會計', '計算機', '微積分', '程式', '統計', '經濟', '管理']):
        print(f'- {col_name}')

conn.close()