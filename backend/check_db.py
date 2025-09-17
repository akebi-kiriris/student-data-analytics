import sqlite3
import pandas as pd

# 連接資料庫
conn = sqlite3.connect('database/excel_data.db')
cursor = conn.cursor()

# 檢查所有表格
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('資料庫中的表格:')
for table in tables:
    print(f'  {table[0]}')

# 檢查第一個表格的欄位
if tables:
    table_name = tables[0][0]
    print(f'\n表格 "{table_name}" 的欄位:')
    df = pd.read_sql_query(f'SELECT * FROM {table_name} LIMIT 1', conn)
    for i, col in enumerate(df.columns):
        print(f'{i+1:2d}. {col}')
    
    # 尋找科目相關欄位
    subject_keywords = ['會計', '計算', '微積', '程式', '統計', '經濟', '管理']
    subject_columns = []
    for col in df.columns:
        for keyword in subject_keywords:
            if keyword in col:
                subject_columns.append(col)
                break
    
    print(f'\n找到的科目相關欄位 ({len(subject_columns)} 個):')
    for col in subject_columns:
        print(f'  {col}')

conn.close()