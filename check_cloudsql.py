"""
檢查 Cloud SQL 資料庫內容的腳本
"""
import pg8000
import os

# Cloud SQL 連接資訊
DB_HOST = "35.221.173.49"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "asd138012"
DB_NAME = "student_analytics"

try:
    # 建立連接
    print(f"正在連接到 Cloud SQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    conn = pg8000.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    
    # 1. 列出所有資料表
    print("\n" + "="*60)
    print("📊 資料庫中的所有資料表:")
    print("="*60)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    if not tables:
        print("⚠️  資料庫中沒有任何資料表！")
    else:
        for i, (table_name,) in enumerate(tables, 1):
            print(f"{i}. {table_name}")
        
        print(f"\n共 {len(tables)} 個資料表")
        
        # 2. 檢查每個資料表的記錄數
        print("\n" + "="*60)
        print("📈 各資料表的記錄數:")
        print("="*60)
        for (table_name,) in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]
                print(f"{table_name}: {count} 筆記錄")
            except Exception as e:
                print(f"{table_name}: 查詢失敗 - {e}")
        
        # 3. 檢查 uploaded_files 表（如果存在）
        if any('uploaded_files' in str(t) for t in tables):
            print("\n" + "="*60)
            print("📁 已上傳的檔案記錄:")
            print("="*60)
            cursor.execute("""
                SELECT file_id, user_id, original_filename, upload_time, table_name
                FROM uploaded_files
                ORDER BY upload_time DESC
                LIMIT 10
            """)
            files = cursor.fetchall()
            for file_id, user_id, filename, upload_time, table_name in files:
                print(f"  • {filename}")
                print(f"    User: {user_id} | Time: {upload_time}")
                print(f"    Table: {table_name}")
                print()
    
    cursor.close()
    conn.close()
    print("\n✅ 檢查完成！")
    
except Exception as e:
    print(f"\n❌ 連接失敗: {e}")
    print("\n可能的原因:")
    print("1. IP 地址未授權（需要在 Cloud SQL Console 添加你的 IP）")
    print("2. Cloud SQL 實例未啟動")
    print("3. 密碼錯誤")
