from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table, inspect, text
from sqlalchemy.orm import sessionmaker
import re


def filter_dataframe_until_empty_row(df):
    """
    過濾 DataFrame，在遇到第一個完全空白的行時停止
    """
    if df.empty:
        return df
    
    columns = df.columns.tolist()
    valid_rows = []
    
    for idx, row in df.iterrows():
        # 檢查這一行是否完全為空
        is_empty_row = True
        for col in columns:
            cell_value = row[col]
            if pd.notna(cell_value) and str(cell_value).strip() != '':
                is_empty_row = False
                break
        
        # 如果遇到完全空白的行，停止讀取
        if is_empty_row:
            print(f"[filter] 在第 {idx+1} 行遇到空白行，停止讀取")
            break
        
        valid_rows.append(idx)
    
    # 只保留有效的行
    if valid_rows:
        filtered_df = df.iloc[valid_rows].copy()
        print(f"[filter] 實際保留了 {len(valid_rows)} 行資料")
        return filtered_df
    else:
        print("[filter] 沒有找到有效資料")
        return pd.DataFrame()  # 返回空的 DataFrame


# 入學管道分類邏輯
def classify_admission_method(method_name):
    """
    根據入學管道名稱判斷入學管道類型
    """
    # 處理空值、空字串和純空白字串
    if pd.isna(method_name):
        return '其他'
    
    method_name = str(method_name).strip()
    if method_name == '':
        return '其他'
    
    # 檢查是否只包含換行或空白字元
    if all(c.isspace() for c in method_name):
        return '其他'
    
    # 定義各類型入學管道的關鍵字（按優先級排序）
    classification_rules = [
        # 自然組和社會組的處理（優先處理，因為可能包含在申請入學中）
        ('自然組', [r'\(自然組\)']),
        ('社會組', [r'\(社會組\)']),
        
        # 繁星推薦
        ('繁星推薦', [r'^繁星推薦$', r'^繁星$']),
        
        # 申請入學（完全匹配，不允許其他字元）
        ('申請入學', [r'^申請入學$']),
        
        # 僑生
        ('僑生', [r'^僑生$']),
        
        # 願景（包含【願景】格式）
        ('願景', [r'^【願景】$'])
    ]
    
    # 檢查每一個規則
    for category, patterns in classification_rules:
        for pattern in patterns:
            if re.search(pattern, method_name):
                return category
    
    # 如果都不符合，歸類為其他
    return '其他'
    


# 學校類型分類邏輯
def classify_school_type(school_name):
    """
    根據學校名稱或類型判斷學校類型
    將值分類為：國立、市立、縣立、私立、財團、國大轉、私大轉、科大轉、僑生、其他
    空白值、空字串或純空格都歸類為其他
    """
    # 處理空值、空字串或純空格的情況
    if pd.isna(school_name) or not str(school_name).strip():
        return '其他'

    school_name = str(school_name).strip()
    
    # 完全匹配的類型（優先）
    exact_matches = {
        '國立': '國立',
        '私立': '私立',
        '財團法人': '財團',
        '市立': '市立',
        '大陸台商': '其他',
        '私大轉': '私大轉',
        '科大轉': '科大轉',
        '國大轉': '國大轉',
        '僑生': '僑生'
    }
    
    # 檢查完全匹配
    for key, value in exact_matches.items():
        if school_name == key:
            return value
    
    # 關鍵字檢查（按優先順序）
    if '國立' in school_name:
        return '國立'
    elif '市立' in school_name:
        return '市立'
    elif '縣立' in school_name:
        return '縣立'
    elif '財團法人' in school_name:
        return '財團'
    elif '私立' in school_name:
        return '私立'
    elif '僑' in school_name or '海外' in school_name:
        return '僑生'
    elif '國立' in school_name and ('大學' in school_name or '學院' in school_name):
        return '國大轉'
    elif '私立' in school_name and ('大學' in school_name or '學院' in school_name):
        return '私大轉'
    elif '科技' in school_name or '技術學院' in school_name or '專科' in school_name:
        return '科大轉'
    
    # 地區檢查（這些通常也是國外/僑生）
    foreign_keywords = ['美國', '加拿大', '澳洲', '紐西蘭', '英國', '德國', 
                       '法國', '日本', '韓國', '馬來西亞', '印尼', '越南', 
                       '泰國', '緬甸', '柬埔寨', '新加坡', '汶萊', '菲律賓']
    for keyword in foreign_keywords:
        if keyword in school_name:
            return '其他'
    
    return '其他'


# 地理區域分類規則
def classify_region(region):
    """
    根據縣市名稱判斷所屬區域
    """
    if pd.isna(region):
        return '其他'
    
    region = str(region).strip()
    if region == '':
        return '其他'

    # 地理區域對應表
    region_mapping = {
        # 北台灣
        '台北市': '北台灣',
        '臺北市': '北台灣',
        '新北市': '北台灣',
        '基隆市': '北台灣',
        '宜蘭縣': '北台灣',
        '桃園市': '北台灣',
        '新竹市': '北台灣',
        '新竹縣': '北台灣',
        
        # 中台灣
        '苗栗縣': '中台灣',
        '台中市': '中台灣',
        '臺中市': '中台灣',
        '彰化縣': '中台灣',
        '南投縣': '中台灣',
        '雲林縣': '中台灣',
        
        # 南台灣
        '嘉義市': '南台灣',
        '嘉義縣': '南台灣',
        '台南市': '南台灣',
        '臺南市': '南台灣',
        '高雄市': '南台灣',
        '屏東縣': '南台灣',
        
        # 東台灣
        '花蓮縣': '東台灣',
        '台東縣': '東台灣',
        '臺東縣': '東台灣'
    }

    return region_mapping.get(region, '其他')


app = Flask(__name__)
CORS(app)  # 開放所有來源 CORS

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 限制 100MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE_FOLDER'] = 'database'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

# === SQLite 設定 ===
DATABASE_PATH = os.path.join(app.config['DATABASE_FOLDER'], 'excel_data.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
engine = create_engine(DATABASE_URL, echo=False)
metadata = MetaData()


# 動態建立表格（每個 Excel 檔案+工作表對應一個資料表）
def create_excel_table(table_name, columns):
    """
    為 Excel 檔案的特定工作表建立對應的資料表
    table_name: 表名（檔名_工作表名）
    columns: 欄位名稱列表
    """
    inspector = inspect(engine)
    
    # 若表格已存在則先刪除
    if inspector.has_table(table_name):
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.commit()
    
    # 建立新表
    cols = [Column('id', Integer, primary_key=True, autoincrement=True)]
    for col in columns:
        # SQLite 相容的欄位名稱處理
        safe_col_name = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        cols.append(Column(safe_col_name, String))
    
    table = Table(table_name, metadata, *cols)
    metadata.create_all(engine)
    return table

Session = sessionmaker(bind=engine)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    上傳 Excel 檔案並將指定工作表的資料存入 SQLite 資料庫
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    sheet_name = request.form.get('sheet_name', None)  # 工作表名稱
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # 儲存檔案
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 如果沒有指定工作表，先回傳所有工作表名稱讓前端選擇
        if not sheet_name:
            xl = pd.ExcelFile(filepath)
            return jsonify({
                "filename": file.filename,
                "sheets": xl.sheet_names,
                "need_sheet_selection": True
            }), 200

        # 讀取指定工作表
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # 過濾資料：在遇到空白行時停止讀取
        df = filter_dataframe_until_empty_row(df)
        
        if df.empty:
            return jsonify({"error": "工作表中沒有有效資料"}), 400
            
        columns = df.columns.tolist()

        # 建立資料表名稱：檔名_工作表名
        base_name = os.path.splitext(file.filename)[0]
        safe_base_name = base_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')
        safe_sheet_name = sheet_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')
        table_name = f"excel_{safe_base_name}_{safe_sheet_name}"

        # 建立資料表
        table = create_excel_table(table_name, columns)
        
        # 將資料寫入資料庫
        session = Session()
        try:
            # 轉換資料並插入
            data_dicts = []
            for _, row in df.iterrows():
                row_dict = {}
                for i, col in enumerate(columns):
                    safe_col_name = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                    row_dict[safe_col_name] = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ''
                data_dicts.append(row_dict)
            
            session.execute(table.insert(), data_dicts)
            session.commit()
            
            return jsonify({
                "success": True,
                "filename": file.filename,
                "sheet_name": sheet_name,
                "table_name": table_name,
                "columns": columns,
                "rows_inserted": len(data_dicts)
            }), 200
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/database_tables', methods=['GET'])
def list_database_tables():
    """
    取得資料庫中所有已存入的表格清單
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 只回傳以 excel_ 開頭的表格（排除系統表格）
        excel_tables = [table for table in tables if table.startswith('excel_')]
        
        # 解析表格名稱，提取檔名和工作表名
        table_info = []
        for table in excel_tables:
            try:
                # 格式：excel_檔名_工作表名
                parts = table.replace('excel_', '', 1).rsplit('_', 1)
                if len(parts) == 2:
                    filename = parts[0]
                    sheet_name = parts[1]
                    table_info.append({
                        'table_name': table,
                        'display_name': f"{filename} - {sheet_name}",
                        'filename': filename,
                        'sheet_name': sheet_name
                    })
            except Exception as e:
                # 如果解析失敗，就直接顯示表格名稱
                table_info.append({
                    'table_name': table,
                    'display_name': table,
                    'filename': '',
                    'sheet_name': ''
                })
        
        return jsonify({'tables': table_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/table_columns', methods=['POST'])
def get_table_columns():
    """
    取得指定資料表的欄位清單
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({'error': '缺少 table_name'}), 400
            
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404
            
        columns_info = inspector.get_columns(table_name)
        columns = [col['name'] for col in columns_info if col['name'] != 'id']  # 排除 id 欄位
        
        return jsonify({'columns': columns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/tables', methods=['GET'])
def list_database_tables_new():
    """
    取得資料庫中所有已存入的表格清單（新格式API）
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 只回傳以 excel_ 開頭的表格（排除系統表格）
        excel_tables = [table for table in tables if table.startswith('excel_')]
        
        # 解析表格名稱，提取檔名和工作表名
        table_info = []
        for table in excel_tables:
            try:
                # 格式：excel_檔名_工作表名
                parts = table.replace('excel_', '', 1).rsplit('_', 1)
                if len(parts) == 2:
                    filename = parts[0]
                    sheet_name = parts[1]
                    table_info.append({
                        'table_name': table,
                        'display_name': f"{filename} - {sheet_name}",
                        'filename': filename,
                        'sheet_name': sheet_name
                    })
            except Exception as e:
                # 如果解析失敗，就直接顯示表格名稱
                table_info.append({
                    'table_name': table,
                    'display_name': table,
                    'filename': '',
                    'sheet_name': ''
                })
        
        return jsonify({'success': True, 'tables': table_info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/tables/<table_name>/count', methods=['GET'])
def get_table_row_count(table_name):
    """
    取得指定資料表的行數統計
    """
    try:
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'success': False, 'error': '找不到指定的資料表'}), 404
        
        # 執行計數查詢
        with engine.connect() as connection:
            result = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
            count = result.scalar()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sheets', methods=['POST'])
def list_excel_sheets():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': '缺少 filename'}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '找不到檔案'}), 404
    try:
        xl = pd.ExcelFile(filepath)
        return jsonify({'sheets': xl.sheet_names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/read_columns', methods=['POST'])
def read_columns_from_file():
    data = request.get_json()
    filename = data.get('filename')
    sheet = data.get('sheet')
    if not filename:
        return jsonify({'error': '缺少 filename'}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '找不到檔案'}), 404
    try:
        if sheet:
            df = pd.read_excel(filepath, sheet_name=sheet)
        else:
            df = pd.read_excel(filepath)
        columns = df.columns.tolist()
        return jsonify({'columns': columns})
    except Exception as e:
        print(f"[read_columns_from_file] {e}")  # 印出詳細錯誤到後端終端機
        return jsonify({'error': str(e)}), 500





# 新增 API：查詢指定 Excel 檔案的內容（for 前端圖表）
@app.route('/api/data', methods=['POST'])
def get_excel_data_post():
    try:
        data = request.get_json()
        filename = data.get('filename') if data else None
        if not filename:
            return jsonify({'error': '缺少 filename'}), 400
        base_name = os.path.splitext(filename)[0]
        safe_table_name = f"excel_data_{base_name.replace('-', '_').replace(' ', '_')}"
        inspector = inspect(engine)
        if not inspector.has_table(safe_table_name):
            return jsonify({'error': '尚未上傳該檔案的資料'}), 400
        table = Table(safe_table_name, metadata, autoload_with=engine)
        session = Session()
        result = session.execute(table.select()).fetchall()
        session.close()
        columns = table.columns.keys()
        data = [dict(zip(columns, row)) for row in result]
        return jsonify({'columns': columns, 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# RESTful 風格 GET: /api/data/<filename>
@app.route('/api/data/<path:filename>', methods=['GET'])
def get_excel_data_get(filename):
    try:
        sheet = request.args.get('sheet')
        if not filename:
            return jsonify({'error': '缺少 filename'}), 400
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '找不到檔案'}), 404
        
        # 先嘗試從資料庫讀取（如果已上傳）
        base_name = os.path.splitext(filename)[0]
        safe_table_name = f"excel_data_{base_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')}"
        inspector = inspect(engine)
        
        if inspector.has_table(safe_table_name):
            # 從資料庫讀取
            table = Table(safe_table_name, metadata, autoload_with=engine)
            session = Session()
            result = session.execute(table.select()).fetchall()
            session.close()
            columns = [col.name for col in table.columns if col.name != 'id']
            data = [dict(zip(columns, row[1:])) for row in result]  # 跳過 id 欄位
            return jsonify({'columns': columns, 'data': data})
        else:
            # 直接從檔案讀取
            if sheet:
                df = pd.read_excel(filepath, sheet_name=sheet)
            else:
                df = pd.read_excel(filepath)
            
            # 過濾資料：在遇到空白行時停止讀取
            df = filter_dataframe_until_empty_row(df)
            
            columns = df.columns.tolist()
            data = df.to_dict(orient='records')
            return jsonify({'columns': columns, 'data': data})
    except Exception as e:
        print(f"[get_excel_data_get] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/column_stats', methods=['POST'])
def column_stats():
    """
    從資料庫讀取資料並計算指定欄位的統計數據
    前端傳入 { table_name: 資料表名稱, column: 欄位名稱 }
    回傳該欄位的平均數、變異數、最大、最小、筆數
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        column = data.get('column')
        
        if not table_name or not column:
            return jsonify({'error': '缺少 table_name 或 column'}), 400
            
        # 檢查資料表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404
            
        # 從資料庫讀取資料
        session = Session()
        try:
            # 安全的欄位名稱
            safe_column = column.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            
            # 檢查欄位是否存在
            columns_info = inspector.get_columns(table_name)
            available_columns = [col['name'] for col in columns_info]
            
            if safe_column not in available_columns:
                return jsonify({'error': f'找不到欄位 {column}，可用欄位：{available_columns}'}), 400
            
            # 使用原始 SQL 查詢
            query = text(f'SELECT "{safe_column}" FROM "{table_name}" WHERE "{safe_column}" IS NOT NULL AND "{safe_column}" != ""')
            result = session.execute(query).fetchall()
            
            # 處理數據
            raw_values = [row[0] for row in result]
            values = []
            skipped = 0
            
            for v in raw_values:
                if v == '' or v is None:
                    continue
                try:
                    v_str = str(v).strip().replace('，', '').replace(',', '')
                    if v_str == '' or v_str.lower() == 'nan':
                        skipped += 1
                        continue
                    values.append(float(v_str))
                except Exception:
                    skipped += 1
            
            if not values:
                return jsonify({'error': '該欄位無有效數值可統計'}), 400
            
            import numpy as np
            stats = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                'min': float(min(values)),
                'max': float(max(values)),
                'count': len(values),
                'skipped': skipped
            }
            
            return jsonify({
                'column': column, 
                'stats': stats,
                'raw_data': raw_values[:100]  # 限制回傳資料量
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multi_subject_stats', methods=['POST'])
def multi_subject_stats():
    """
    從資料庫讀取多科目分年平均分析
    前端傳入 { table_name, subjects: [科目1, 科目2, ...], year_col: '入學年度' }
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        subjects = data.get('subjects')
        year_col = data.get('year_col', '入學年度')
        
        if not table_name or not subjects or not year_col:
            return jsonify({'error': '缺少 table_name、subjects 或 year_col'}), 400
            
        # 檢查資料表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404
            
        # 取得欄位清單並轉換為安全名稱
        columns_info = inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_subjects = [s.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '') for s in subjects]
        
        # 檢查欄位是否存在
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
            
        for i, subj in enumerate(safe_subjects):
            if subj not in available_columns:
                return jsonify({'error': f'找不到科目欄位: {subjects[i]}'}), 400
        
        # 從資料庫讀取資料
        session = Session()
        try:
            # 構建查詢語句
            columns_str = f'"{safe_year_col}", ' + ', '.join([f'"{subj}"' for subj in safe_subjects])
            query = text(f'SELECT {columns_str} FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            # 轉換為 DataFrame 進行分析
            columns = [safe_year_col] + safe_subjects
            df = pd.DataFrame(result, columns=columns)
            
            # 轉換年度欄位
            try:
                df[safe_year_col] = pd.to_numeric(df[safe_year_col], errors='coerce')
                df = df.dropna(subset=[safe_year_col])
                df[safe_year_col] = df[safe_year_col].astype(int)
            except Exception as e:
                print(f"年度欄位轉換失敗: {e}")
                df[safe_year_col] = df[safe_year_col].astype(str)
            
            # 轉換科目欄位為數值
            for subj in safe_subjects:
                df[subj] = pd.to_numeric(df[subj], errors='coerce')
            
            # 按年度分組計算平均
            grouped = df.groupby(safe_year_col)
            years = sorted(grouped.groups.keys())
            result_data = {subjects[i]: [] for i in range(len(subjects))}  # 使用原始科目名稱
            
            for year in years:
                group = grouped.get_group(year)
                for i, safe_subj in enumerate(safe_subjects):
                    vals = group[safe_subj].dropna().tolist()
                    avg = sum(vals)/len(vals) if vals else None
                    result_data[subjects[i]].append(avg)  # 使用原始科目名稱
                    
            return jsonify({
                'years': years, 
                'subjects': subjects,  # 使用原始科目名稱
                'data': result_data
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 每年入學生數量分析（包含性別統計）- 從資料庫讀取
@app.route('/api/yearly_admission_stats', methods=['POST'])
def yearly_admission_stats():
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        gender_col = data.get('gender_col')  # 可選的性別欄位

        if not table_name or not year_col:
            return jsonify({'error': '缺少 table_name 或 year_col'}), 400

        # 檢查資料表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404

        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400

        has_gender = False
        safe_gender_col = None
        if gender_col:
            safe_gender_col = gender_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            if safe_gender_col in available_columns:
                has_gender = True

        # 從資料庫讀取資料
        session = Session()
        try:
            if has_gender:
                query = text(f'SELECT "{safe_year_col}", "{safe_gender_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
                result = session.execute(query).fetchall()
                df = pd.DataFrame(result, columns=[safe_year_col, safe_gender_col])
            else:
                query = text(f'SELECT "{safe_year_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
                result = session.execute(query).fetchall()
                df = pd.DataFrame(result, columns=[safe_year_col])
            
            # 轉換年度欄位
            try:
                df[safe_year_col] = pd.to_numeric(df[safe_year_col], errors='coerce')
                df = df.dropna(subset=[safe_year_col])
                df[safe_year_col] = df[safe_year_col].astype(int)
            except Exception as e:
                print(f"年度欄位轉換失敗: {e}")
                df[safe_year_col] = df[safe_year_col].astype(str)

            if has_gender:
                # 統一性別欄位的值
                df[safe_gender_col] = df[safe_gender_col].astype(str).str.strip().str.upper()
                
                # 將常見的性別表示法統一
                gender_mapping = {
                    'M': '男', 'MALE': '男', '男性': '男', '1': '男',
                    'F': '女', 'FEMALE': '女', '女性': '女', '2': '女'
                }
                df[safe_gender_col] = df[safe_gender_col].replace(gender_mapping)
                
                # 按年份和性別分組統計
                gender_year_counts = df.groupby([safe_year_col, safe_gender_col]).size().unstack(fill_value=0)
                years = sorted(gender_year_counts.index.tolist())
                
                # 確保有男女兩列
                if '男' not in gender_year_counts.columns:
                    gender_year_counts['男'] = 0
                if '女' not in gender_year_counts.columns:
                    gender_year_counts['女'] = 0
                
                gender_year_counts = gender_year_counts.reindex(years, fill_value=0)
                
                male_counts = gender_year_counts['男'].tolist()
                female_counts = gender_year_counts['女'].tolist()
                total_counts = [m + f for m, f in zip(male_counts, female_counts)]
                
                # 計算百分比
                male_percentages = [round(m/t*100, 1) if t > 0 else 0 for m, t in zip(male_counts, total_counts)]
                female_percentages = [round(f/t*100, 1) if t > 0 else 0 for f, t in zip(female_counts, total_counts)]
                
                return jsonify({
                    'years': years,
                    'male_counts': male_counts,
                    'female_counts': female_counts,
                    'total_counts': total_counts,
                    'male_percentages': male_percentages,
                    'female_percentages': female_percentages,
                    'total_students': sum(total_counts),
                    'year_range': f"{min(years)} - {max(years)}" if years else "無資料",
                    'has_gender': True
                })
            else:
                # 沒有性別欄位，只統計總數
                year_counts = df[safe_year_col].value_counts().sort_index()
                years = year_counts.index.tolist()
                counts = year_counts.values.tolist()
                
                return jsonify({
                    'years': years, 
                    'total_counts': counts,
                    'total_students': int(year_counts.sum()),
                    'year_range': f"{min(years)} - {max(years)}" if years else "無資料",
                    'has_gender': False
                })
                
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/school_source_stats', methods=['POST'])
def school_source_stats():
    """
    從資料庫統計每年入學生的學校來源類型分布
    """
    try:
        data = request.json
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        school_col = data.get('school_col')  # 學校名稱欄位
        
        if not table_name or not year_col or not school_col:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 檢查資料表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404
        
        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_school_col = school_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_school_col not in available_columns:
            return jsonify({'error': f'找不到學校欄位: {school_col}'}), 400
        
        # 從資料庫讀取資料
        session = Session()
        try:
            query = text(f'SELECT "{safe_year_col}", "{safe_school_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            if not result:
                return jsonify({'error': '沒有有效的年份資料'}), 400
            
            # 轉換為 DataFrame
            df = pd.DataFrame(result, columns=[safe_year_col, safe_school_col])
            
            # 將空的學校欄位填入空字串
            df[safe_school_col] = df[safe_school_col].fillna('')
            
            # 對每一筆資料進行學校類型分類
            df['school_type'] = df[safe_school_col].apply(classify_school_type)
            
            # 按年份和學校類型分組統計
            school_type_stats = df.groupby([safe_year_col, 'school_type']).size().unstack(fill_value=0)
            
            # 確保所有學校類型都存在
            all_types = ['國立', '市立', '縣立', '私立', '財團', '國大轉', '私大轉', '科大轉', '僑生', '其他']
            for school_type in all_types:
                if school_type not in school_type_stats.columns:
                    school_type_stats[school_type] = 0
            
            # 重新排序欄位
            school_type_stats = school_type_stats[all_types]
            
            years = sorted(school_type_stats.index.tolist())
            years = [str(year) for year in years]
            school_type_stats = school_type_stats.reindex(sorted(school_type_stats.index.tolist()), fill_value=0)
            
            # 準備返回資料
            result_data = {
                'years': years,
                'school_types': all_types,
                'data': {},
                'total_students': int(len(df)),
                'year_range': f"{min(years)} - {max(years)}" if years else "無資料"
            }
            
            # 計算每個年份的總人數和百分比
            year_totals = []
            original_years = sorted(school_type_stats.index.tolist())
            for i, year in enumerate(original_years):
                year_data = school_type_stats.loc[year]
                year_total = int(year_data.sum())
                year_totals.append(year_total)
                
                # 計算各類型的數量和百分比
                for school_type in all_types:
                    if school_type not in result_data['data']:
                        result_data['data'][school_type] = {
                            'counts': [],
                            'percentages': []
                        }
                    
                    count = int(year_data[school_type])
                    percentage = round(float(count / year_total * 100), 1) if year_total > 0 else 0.0
                    
                    result_data['data'][school_type]['counts'].append(count)
                    result_data['data'][school_type]['percentages'].append(percentage)
            
            result_data['year_totals'] = year_totals
            
            # 統計摘要
            result_data['summary'] = {
                'peak_year': str(years[year_totals.index(max(year_totals))]) if year_totals else None,
                'peak_count': int(max(year_totals)) if year_totals else 0,
                'low_year': str(years[year_totals.index(min(year_totals))]) if year_totals else None,
                'low_count': int(min(year_totals)) if year_totals else 0
            }
            
            return jsonify(result_data)
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admission_method_stats', methods=['POST'])
def admission_method_stats():
    """
    從資料庫統計入學管道分析
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        method_col = data.get('method_col')
        
        if not table_name or not year_col or not method_col:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 檢查資料表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404
        
        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_method_col = method_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_method_col not in available_columns:
            return jsonify({'error': f'找不到入學管道欄位: {method_col}'}), 400
        
        # 從資料庫讀取資料
        session = Session()
        try:
            query = text(f'SELECT "{safe_year_col}", "{safe_method_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            if not result:
                return jsonify({'error': '沒有有效的年份資料'}), 400
            
            # 轉換為 DataFrame
            df = pd.DataFrame(result, columns=[safe_year_col, safe_method_col])
            
            # 對入學管道欄位進行分類
            df['method_type'] = df[safe_method_col].apply(lambda x: classify_admission_method(x))
            
            # 按年份和入學管道類型分組統計
            method_type_stats = df.groupby([safe_year_col, 'method_type']).size().unstack(fill_value=0)
            
            # 確保所有入學管道類型都存在
            all_types = ['申請入學', '繁星推薦', '自然組', '社會組', '僑生', '願景', '其他']
            for method_type in all_types:
                if method_type not in method_type_stats.columns:
                    method_type_stats[method_type] = 0
            
            # 重新排序欄位
            method_type_stats = method_type_stats[all_types]
            
            # 轉換年份為字符串以確保JSON序列化
            years = sorted(method_type_stats.index.tolist())
            years = [str(year) for year in years]
            
            # 重新索引確保順序一致
            method_type_stats = method_type_stats.reindex(sorted(method_type_stats.index.tolist()), fill_value=0)
            
            # 準備返回資料
            result_data = {
                'years': years,
                'method_types': all_types,
                'data': {},
                'total_students': int(len(df)),
                'year_range': f"{min(years)} - {max(years)}" if years else "無資料"
            }
            
            # 計算每個年份的總人數和百分比
            year_totals = []
            original_years = sorted(method_type_stats.index.tolist())
            for i, year in enumerate(original_years):
                year_data = method_type_stats.loc[year]
                year_total = int(year_data.sum())
                year_totals.append(year_total)
                
                # 計算各類型的數量和百分比
                for method_type in all_types:
                    if method_type not in result_data['data']:
                        result_data['data'][method_type] = {
                            'counts': [],
                            'percentages': []
                        }
                    
                    count = int(year_data[method_type])
                    percentage = round(float(count / year_total * 100), 1) if year_total > 0 else 0.0
                    
                    result_data['data'][method_type]['counts'].append(count)
                    result_data['data'][method_type]['percentages'].append(percentage)
            
            result_data['year_totals'] = year_totals
            
            # 統計摘要
            result_data['summary'] = {
                'peak_year': str(years[year_totals.index(max(year_totals))]) if year_totals else None,
                'peak_count': int(max(year_totals)) if year_totals else 0,
                'low_year': str(years[year_totals.index(min(year_totals))]) if year_totals else None,
                'low_count': int(min(year_totals)) if year_totals else 0
            }
            
            return jsonify(result_data)
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 地理區域分類規則
REGION_MAPPING = {
    # 北台灣
    '台北市': '北台灣',
    '臺北市': '北台灣',
    '新北市': '北台灣',
    '基隆市': '北台灣',
    '宜蘭縣': '北台灣',
    '桃園市': '北台灣',
    '新竹市': '北台灣',
    '新竹縣': '北台灣',
    
    # 中台灣
    '苗栗縣': '中台灣',
    '台中市': '中台灣',
    '臺中市': '中台灣',
    '彰化縣': '中台灣',
    '南投縣': '中台灣',
    '雲林縣': '中台灣',
    
    # 南台灣
    '嘉義市': '南台灣',
    '嘉義縣': '南台灣',
    '台南市': '南台灣',
    '臺南市': '南台灣',
    '高雄市': '南台灣',
    '屏東縣': '南台灣',
    
    # 東台灣
    '花蓮縣': '東台灣',
    '台東縣': '東台灣',
    '臺東縣': '東台灣',
}

# 區域排序（用於確保圖表順序一致）
REGION_ORDER = ['北台灣', '中台灣', '南台灣', '東台灣', '其他']

@app.route('/api/geographic_stats', methods=['POST'])
def geographic_stats():
    """
    從資料庫進行地理區域分析
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        region_col = data.get('region_col')
        get_city_details = data.get('get_city_details', False)

        if not all([table_name, year_col, region_col]):
            return jsonify({'error': '缺少必要參數'}), 400

        # 檢查資料表是否存在
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return jsonify({'error': '找不到指定的資料表'}), 404

        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_region_col = region_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

        # 檢查欄位是否存在
        columns_info = inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_region_col not in available_columns:
            return jsonify({'error': f'找不到地區欄位: {region_col}'}), 400

        # 從資料庫讀取資料
        session = Session()
        try:
            query = text(f'SELECT "{safe_year_col}", "{safe_region_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            if not result:
                return jsonify({'error': '沒有有效的年份資料'}), 400
            
            # 轉換為 DataFrame
            df = pd.DataFrame(result, columns=[safe_year_col, safe_region_col])
            
            # 將地區映射到區域
            df['region'] = df[safe_region_col].apply(classify_region)

            # 轉換年度欄位
            try:
                df[safe_year_col] = pd.to_numeric(df[safe_year_col], errors='coerce')
                df = df.dropna(subset=[safe_year_col])
                df[safe_year_col] = df[safe_year_col].astype(int)
            except Exception as e:
                print(f"年度欄位轉換失敗: {e}")
                df[safe_year_col] = df[safe_year_col].astype(str)

            # 按年度和區域統計
            region_order = ['北台灣', '中台灣', '南台灣', '東台灣', '其他']
            grouped = df.groupby([safe_year_col, 'region']).size().unstack(fill_value=0)
            
            # 確保所有區域都存在
            for region in region_order:
                if region not in grouped.columns:
                    grouped[region] = 0
                    
            # 重新排序區域
            grouped = grouped[region_order]
            
            # 準備回傳資料
            years = sorted(grouped.index.tolist())
            result = {
                'years': years,
                'regions': region_order,
                'data': {region: grouped[region].tolist() for region in region_order},
                'total_students': int(grouped.sum().sum()),
                'year_range': f"{min(years)} - {max(years)}" if years else "無資料"
            }
            
            # 如果需要詳細的縣市分析
            if get_city_details:
                detailed = {}
                
                # 定義每個區域應該包含的所有縣市
                region_cities_mapping = {
                    '北台灣': ['台北市', '臺北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '宜蘭縣'],
                    '中台灣': ['苗栗縣', '台中市', '臺中市', '彰化縣', '南投縣', '雲林縣'],
                    '南台灣': ['嘉義市', '嘉義縣', '台南市', '臺南市', '高雄市', '屏東縣'],
                    '東台灣': ['花蓮縣', '台東縣', '臺東縣']
                }
                
                # 針對四個主要區域進行詳細縣市分析
                for region in ['北台灣', '中台灣', '南台灣', '東台灣']:
                    expected_cities = region_cities_mapping.get(region, [])
                    
                    city_data = []
                    for city in expected_cities:
                        # 按年度和縣市統計
                        city_df = df[df[safe_region_col] == city]
                        city_by_year = city_df.groupby(safe_year_col).size() if not city_df.empty else pd.Series()
                        
                        # 確保所有年份都有數據
                        year_data = []
                        for year in years:
                            if not city_by_year.empty and year in city_by_year.index:
                                year_data.append(int(city_by_year[year]))
                            else:
                                year_data.append(0)
                        
                        city_data.append({
                            'name': city,
                            'data': year_data
                        })
                    
                    # 只保留有意義的縣市名稱（去除重複的簡繁體）
                    unique_city_data = []
                    city_names_seen = set()
                    for city_info in city_data:
                        city_name = city_info['name']
                        base_name = city_name.replace('臺', '台')
                        if base_name not in city_names_seen:
                            city_names_seen.add(base_name)
                            city_info['name'] = base_name
                            unique_city_data.append(city_info)
                        else:
                            # 合併數據
                            for existing_city in unique_city_data:
                                if existing_city['name'] == base_name:
                                    for i in range(len(existing_city['data'])):
                                        existing_city['data'][i] = max(existing_city['data'][i], city_info['data'][i])
                                    break
                    
                    # 按總人數排序縣市
                    unique_city_data.sort(key=lambda x: sum(x['data']), reverse=True)
                    
                    detailed[region] = {
                        'cities': unique_city_data
                    }
                
                result['detailed'] = detailed
            
            return jsonify(result)
            
        finally:
            session.close()

    except Exception as e:
        print(f"[geographic_stats] Error: {str(e)}")
        return jsonify({'error': f'處理資料時發生錯誤: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
