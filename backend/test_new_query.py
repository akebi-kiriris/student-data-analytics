import sqlite3
import pandas as pd

# 連接資料庫
conn = sqlite3.connect('database/excel_data.db')

# 測試新的查詢
table_name = 'excel_107_113大一新生來源管道與成績分析_20250525_整理後總表'
subjects = [
    '會計學', '計算機概論', '微積分', '基礎程式設計', 
    '統計1', '經濟學', '程式設計', '管理學', '統計2'
]

query = f"""
SELECT 年度, 性別, 高中別, 入學管道, {', '.join([f'`{subject}`' for subject in subjects])}
FROM `{table_name}` 
WHERE 年度 IS NOT NULL
LIMIT 5
"""

df = pd.read_sql_query(query, conn)
print("查詢結果預覽:")
print(df.head())
print(f"\n總共 {len(df)} 筆資料")

# 檢查各欄位的唯一值
print(f"\n年度: {sorted(df['年度'].unique())}")
print(f"性別: {df['性別'].value_counts().to_dict()}")
print(f"高中別: {df['高中別'].value_counts().head(10).to_dict()}")
print(f"入學管道: {df['入學管道'].value_counts().to_dict()}")

conn.close()