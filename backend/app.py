from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
import re


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
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# === PostgreSQL 設定 ===
# 請將下方連線字串改成你的 PostgreSQL 設定
DATABASE_URL = 'postgresql+psycopg2://postgres:asd138012@localhost:5432/excel_db'
engine = create_engine(DATABASE_URL)
metadata = MetaData()


# 動態建立表格（每個 Excel 檔案對應一個資料表，表名為 excel_data_檔名）
def create_excel_table(table_name, columns):
    inspector = inspect(engine)
    # 若表格已存在則先清除 metadata 中的定義，再重建
    if inspector.has_table(table_name):
        # 清除 metadata 中的舊定義
        if table_name in metadata.tables:
            metadata.remove(metadata.tables[table_name])
        # 刪除舊表
        metadata.reflect(bind=engine, only=[table_name])
        old_table = metadata.tables[table_name]
        old_table.drop(engine)
        metadata.remove(old_table)
    
    # 建立新表
    cols = [Column('id', Integer, primary_key=True, autoincrement=True)]
    for col in columns:
        cols.append(Column(col, String(255)))
    table = Table(table_name, metadata, *cols)
    metadata.create_all(engine)
    return table

Session = sessionmaker(bind=engine)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 使用 pandas 讀取 Excel
        df = pd.read_excel(filepath)
        columns = df.columns.tolist()

        # 以檔名建立資料表（去除副檔名與特殊字元）
        base_name = os.path.splitext(file.filename)[0]
        safe_table_name = f"excel_data_{base_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')}"

        # 建立資料表（若已存在則不重建）
        table = create_excel_table(safe_table_name, columns)
        # 將資料寫入資料庫
        session = Session()
        data_dicts = df.astype(str).to_dict(orient='records')
        session.execute(table.insert(), data_dicts)
        session.commit()
        session.close()

        return jsonify({
            "success": True,
            "filename": file.filename,
            "columns": columns
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/files', methods=['GET'])
def list_uploaded_files():
    try:
        files = [
            f for f in os.listdir(app.config['UPLOAD_FOLDER'])
            if f.endswith('.xlsx') or f.endswith('.xls')
        ]
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
            columns = df.columns.tolist()
            data = df.to_dict(orient='records')
            return jsonify({'columns': columns, 'data': data})
    except Exception as e:
        print(f"[get_excel_data_get] {e}")
        return jsonify({'error': str(e)}), 500

# 新增 API：根據欄位計算指定檔案的統計數據
@app.route('/api/column_stats', methods=['POST'])
def column_stats():
    """
    前端傳入 { filename: 檔案名稱, column: 欄位名稱 }
    回傳該欄位的平均數、變異數、最大、最小、筆數
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        sheet = data.get('sheet')
        column = data.get('column')
        if not filename or not column:
            return jsonify({'error': '缺少 filename 或 欄位名稱'}), 400
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '找不到檔案'}), 404
        if sheet:
            df = pd.read_excel(filepath, sheet_name=sheet)
        else:
            df = pd.read_excel(filepath)
        if column not in df.columns:
            return jsonify({'error': '找不到該欄位'}), 400

        # 找到第一個空值的位置
        first_empty = None
        for idx, value in enumerate(df[column]):
            if pd.isna(value) or str(value).strip() == '':
                first_empty = idx
                break
        
        # 如果找到空值，只取到那之前的資料
        if first_empty is not None:
            df = df.iloc[:first_empty].copy()
        
        # 處理數據
        raw_values = df[column].tolist()
        values = []
        skipped = 0
        for v in raw_values:
            try:
                v_str = str(v).strip().replace('，', '').replace(',', '')
                if v_str == '' or v_str.lower() == 'nan':
                    skipped += 1
                    continue
                values.append(float(v_str))
            except Exception:
                skipped += 1
        
        import numpy as np
        stats = {
            'mean': np.mean(values) if values else None,
            'std': np.std(values, ddof=1) if len(values) > 1 else 0,
            'min': min(values) if values else None,
            'max': max(values) if values else None,
            'count': len(values),
            'skipped': skipped
        }
        if not values:
            return jsonify({'error': '該欄位無有效數值可統計'}), 400
            
        # 將原始數據也發送回前端
        return jsonify({
            'column': column, 
            'stats': stats,
            'raw_data': raw_values  # 添加原始數據
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multi_subject_stats', methods=['POST'])
def multi_subject_stats():
    """
    前端傳入 { filename, sheet, subjects: [科目1, 科目2, ...], year_col: '入學年度' }
    回傳：
    {
      'years': [2018, 2019, ...],
      'subjects': [科目1, 科目2, ...],
      'data': { 科目1: [各年度平均], 科目2: [各年度平均], ... }
    }
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        sheet = data.get('sheet')
        subjects = data.get('subjects')
        year_col = data.get('year_col', '入學年度')
        if not filename or not subjects or not year_col:
            return jsonify({'error': '缺少 filename、subjects 或 year_col'}), 400
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '找不到檔案'}), 404
        if sheet:
            df = pd.read_excel(filepath, sheet_name=sheet)
        else:
            df = pd.read_excel(filepath)
        
        # 修正：去除欄位名稱前後空白，避免比對失敗
        df.columns = [str(c).strip() for c in df.columns]
        year_col = str(year_col).strip()
        subjects = [str(s).strip() for s in subjects]
        
        if year_col not in df.columns:
            return jsonify({'error': f'找不到入學年度欄位: {year_col}，實際欄位有: {df.columns.tolist()}'}), 400
        for subj in subjects:
            if subj not in df.columns:
                return jsonify({'error': f'找不到科目欄位: {subj}，實際欄位有: {df.columns.tolist()}'}), 400

        # 找到第一個年度為空的位置
        first_empty_year = None
        for idx, row in df.iterrows():
            if pd.isna(row[year_col]) or str(row[year_col]).strip() == '':
                first_empty_year = idx
                break
        
        # 如果找到空白年度，只取到那之前的資料
        if first_empty_year is not None:
            df = df.iloc[:first_empty_year].copy()
        
        # 只取有選的欄位
        sub_df = df[[year_col] + subjects].copy()
        # 年度欄位統一型別（轉字串或 int，視需求）
        # 先去除空值與異常值
        sub_df = sub_df.dropna(subset=[year_col])
        # 嘗試轉成 int，若失敗則轉成 str
        try:
            sub_df[year_col] = sub_df[year_col].astype(int)
        except Exception as e:
            print(f"[multi_subject_stats] 年度欄位無法轉 int，將轉為 str: {e}")
            sub_df[year_col] = sub_df[year_col].astype(str)

        # 轉成數值欄位
        for subj in subjects:
            sub_df[subj] = pd.to_numeric(sub_df[subj], errors='coerce')

        # 依年度分組計算各科平均
        try:
            grouped = sub_df.groupby(year_col)
            years = list(grouped.groups.keys())
            years_sorted = sorted(years)
            result = {subj: [] for subj in subjects}
            for year in years_sorted:
                try:
                    group = grouped.get_group(year)
                except Exception as e:
                    print(f"[multi_subject_stats] get_group({year}) 失敗: {e}")
                    for subj in subjects:
                        result[subj].append(None)
                    continue
                for subj in subjects:
                    vals = group[subj].dropna().tolist()
                    avg = sum(vals)/len(vals) if vals else None
                    result[subj].append(avg)
            return jsonify({'years': years_sorted, 'subjects': subjects, 'data': result})
        except Exception as e:
            print(f"[multi_subject_stats] groupby 或計算失敗: {e}")
            return jsonify({'error': f'groupby 或計算失敗: {e}', 'debug': sub_df.head(10).to_dict()}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 每年入學生數量分析（包含性別統計）
@app.route('/api/yearly_admission_stats', methods=['POST'])
def yearly_admission_stats():
    try:
        data = request.get_json()
        filename = data.get('filename')
        sheet = data.get('sheet')
        year_col = data.get('year_col')
        gender_col = data.get('gender_col')  # 新增性別欄位

        if not filename or not year_col:
            return jsonify({'error': '缺少 filename 或 year_col'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '找不到檔案'}), 404

        if sheet:
            df = pd.read_excel(filepath, sheet_name=sheet)
        else:
            df = pd.read_excel(filepath)

        # 修正：去除欄位名稱前後空白
        df.columns = [str(c).strip() for c in df.columns]
        year_col = str(year_col).strip()

        if year_col not in df.columns:
            return jsonify({'error': f'找不到年份欄位: {year_col}，實際欄位有: {df.columns.tolist()}'}), 400

        # 找到第一個年度為空的位置
        first_empty_year = None
        for idx, row in df.iterrows():
            if pd.isna(row[year_col]) or str(row[year_col]).strip() == '':
                first_empty_year = idx
                break
        
        # 如果找到空白年度，只取到那之前的資料
        if first_empty_year is not None:
            df = df.iloc[:first_empty_year].copy()

        # 準備分析用的欄位
        analysis_cols = [year_col]
        if gender_col and str(gender_col).strip() in df.columns:
            gender_col = str(gender_col).strip()
            analysis_cols.append(gender_col)
            has_gender = True
        else:
            has_gender = False

        # 取得需要的欄位
        df = df[analysis_cols].copy()
        
        # 嘗試轉成 int，若失敗則轉成 str
        try:
            df[year_col] = df[year_col].astype(int)
        except Exception as e:
            print(f"[yearly_admission_stats] 年度欄位無法轉 int，將轉為 str: {e}")
            df[year_col] = df[year_col].astype(str)

        # 計算每年入學生數量
        try:
            if has_gender:
                # 有性別欄位，進行性別統計
                # 先統一性別欄位的值
                df[gender_col] = df[gender_col].astype(str).str.strip().str.upper()
                
                # 將常見的性別表示法統一
                gender_mapping = {
                    'M': '男', 'MALE': '男', '男性': '男', '1': '男',
                    'F': '女', 'FEMALE': '女', '女性': '女', '2': '女'
                }
                df[gender_col] = df[gender_col].replace(gender_mapping)
                
                # 按年份和性別分組統計
                gender_year_counts = df.groupby([year_col, gender_col]).size().unstack(fill_value=0)
                years = sorted(gender_year_counts.index.tolist())
                
                # 確保有男女兩列
                if '男' not in gender_year_counts.columns:
                    gender_year_counts['男'] = 0
                if '女' not in gender_year_counts.columns:
                    gender_year_counts['女'] = 0
                
                # 重新排序確保年份順序
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
                year_counts = df[year_col].value_counts().sort_index()
                years = year_counts.index.tolist()
                counts = year_counts.values.tolist()
                
                return jsonify({
                    'years': years, 
                    'total_counts': counts,
                    'total_students': int(year_counts.sum()),
                    'year_range': f"{min(years)} - {max(years)}" if years else "無資料",
                    'has_gender': False
                })
                
        except Exception as e:
            print(f"[yearly_admission_stats] 計算失敗: {e}")
            return jsonify({'error': f'計算失敗: {e}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/school_source_stats', methods=['POST'])
def school_source_stats():
    """
    統計每年入學生的學校來源類型分布
    """
    try:
        data = request.json
        filename = data.get('filename')
        sheet = data.get('sheet')
        year_col = data.get('year_col')
        school_col = data.get('school_col')  # 學校名稱欄位
        
        if not filename or not sheet or not year_col or not school_col:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 檢查檔案
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': '檔案不存在'}), 404
        
        # 從Excel檔案讀取資料（支援多工作表）
        try:
            if sheet:
                df = pd.read_excel(file_path, sheet_name=sheet)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            return jsonify({'error': f'讀取Excel檔案失敗: {e}'}), 500
        
        if df.empty:
            return jsonify({'error': '沒有資料'}), 400
        
        # 找到第一個年度為空的位置
        first_empty_year = None
        for idx, row in df.iterrows():
            if pd.isna(row[year_col]) or str(row[year_col]).strip() == '':
                first_empty_year = idx
                break
        
        # 如果找到空白年度，只取到那之前的資料
        if first_empty_year is not None:
            df = df.iloc[:first_empty_year].copy()
        
        # 將空的學校欄位填入空字串（這樣可以被 classify_school_type 處理為「其他」）
        df[school_col] = df[school_col].fillna('')
        
        # 只篩選有效的年份（學校欄位的空值已經被填入空字串）
        valid_df = df.dropna(subset=[year_col]).copy()
        
        if valid_df.empty:
            return jsonify({'error': '沒有有效的年份資料'}), 400
        
        try:
            # 對每一筆資料進行學校類型分類
            valid_df['school_type'] = valid_df[school_col].apply(classify_school_type)
            
            # 按年份和學校類型分組統計
            school_type_stats = valid_df.groupby([year_col, 'school_type']).size().unstack(fill_value=0)
            
            # 確保所有學校類型都存在
            all_types = ['國立', '市立', '縣立', '私立', '財團', '國大轉', '私大轉', '科大轉', '僑生', '其他']
            for school_type in all_types:
                if school_type not in school_type_stats.columns:
                    school_type_stats[school_type] = 0
            
            # 重新排序欄位
            school_type_stats = school_type_stats[all_types]
            
            years = sorted(school_type_stats.index.tolist())
            # 轉換年份為字符串以確保JSON序列化
            years = [str(year) for year in years]
            school_type_stats = school_type_stats.reindex(sorted(school_type_stats.index.tolist()), fill_value=0)
            
            # 準備返回資料
            result_data = {
                'years': years,
                'school_types': all_types,
                'data': {},
                'total_students': int(len(valid_df)),  # 轉換為Python int
                'year_range': f"{min(years)} - {max(years)}" if years else "無資料"
            }
            
            # 計算每個年份的總人數和百分比
            year_totals = []
            original_years = sorted(school_type_stats.index.tolist())  # 保持原始年份用於索引
            for i, year in enumerate(original_years):
                year_data = school_type_stats.loc[year]
                year_total = int(year_data.sum())  # 轉換為Python int
                year_totals.append(year_total)
                
                # 計算各類型的數量和百分比
                for school_type in all_types:
                    if school_type not in result_data['data']:
                        result_data['data'][school_type] = {
                            'counts': [],
                            'percentages': []
                        }
                    
                    count = int(year_data[school_type])  # 轉換為Python int
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
            
        except Exception as e:
            print(f"[school_source_stats] 計算失敗: {e}")
            return jsonify({'error': f'計算失敗: {e}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admission_method_stats', methods=['POST'])
def admission_method_stats():
    try:
        data = request.get_json()
        filename = data['filename']
        sheet = data.get('sheet', None)  # 可選參數
        year_col = data['year_col']
        method_col = data['method_col']
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 讀取Excel檔案
        try:
            if sheet:
                df = pd.read_excel(file_path, sheet_name=sheet)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            return jsonify({'error': f'讀取Excel檔案失敗: {e}'}), 500
        
        if df.empty:
            return jsonify({'error': '沒有資料'}), 400
        
        # 找到第一個年度為空的位置
        first_empty_year = None
        for idx, row in df.iterrows():
            if pd.isna(row[year_col]) or str(row[year_col]).strip() == '':
                first_empty_year = idx
                break
        
        # 如果找到空白年度，只取到那之前的資料
        if first_empty_year is not None:
            valid_df = df.iloc[:first_empty_year].copy()
        else:
            valid_df = df.copy()
        
        try:
            # 先對入學管道欄位進行分類，保留 NaN 和空值
            valid_df['method_type'] = valid_df[method_col].apply(lambda x: classify_admission_method(x))
            
            # 按年份和入學管道類型分組統計
            method_type_stats = valid_df.groupby([year_col, 'method_type']).size().unstack(fill_value=0)
            
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
                'total_students': int(len(valid_df)),
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
            
        except Exception as e:
            print(f"[admission_method_stats] 計算失敗: {e}")
            return jsonify({'error': f'計算失敗: {e}'}), 500
            
    except Exception as e:
        print(f"[admission_method_stats] 處理請求失敗: {e}")
        return jsonify({'error': f'處理請求失敗: {e}'}), 500

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
    try:
        data = request.get_json()
        filename = data.get('filename')
        sheet = data.get('sheet')
        year_col = data.get('year_col')
        region_col = data.get('region_col')
        get_city_details = data.get('get_city_details', False)  # 新增參數，控制是否回傳縣市詳細資料

        if not all([filename, year_col, region_col]):
            return jsonify({'error': '缺少必要參數'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '找不到檔案'}), 404

        # 讀取 Excel
        if sheet:
            df = pd.read_excel(filepath, sheet_name=sheet)
        else:
            df = pd.read_excel(filepath)

        # 清理欄位名稱
        df.columns = [str(c).strip() for c in df.columns]
        year_col = str(year_col).strip()
        region_col = str(region_col).strip()

        if year_col not in df.columns or region_col not in df.columns:
            return jsonify({'error': f'找不到必要欄位，需要的欄位：{year_col}, {region_col}'}), 400

        # 找到第一個年度為空的位置
        first_empty_year = None
        for idx, row in df.iterrows():
            if pd.isna(row[year_col]) or str(row[year_col]).strip() == '':
                first_empty_year = idx
                break
        
        # 如果找到空白年度，只取到那之前的資料
        if first_empty_year is not None:
            df = df.iloc[:first_empty_year].copy()

        # 清理並轉換資料
        df = df[[year_col, region_col]].copy()
        
        # 將地區映射到區域
        df['region'] = df[region_col].apply(classify_region)

        # 嘗試轉換年度為數字
        try:
            df[year_col] = df[year_col].astype(int)
        except Exception as e:
            print(f"[geographic_stats] 年度欄位無法轉 int，將轉為 str: {e}")
            df[year_col] = df[year_col].astype(str)

        # 按年度和區域統計
        region_order = ['北台灣', '中台灣', '南台灣', '東台灣', '其他']
        grouped = df.groupby([year_col, 'region']).size().unstack(fill_value=0)
        
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
            
            # 定義每個區域應該包含的所有縣市（無論是否有數據）
            region_cities_mapping = {
                '北台灣': ['台北市', '臺北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '宜蘭縣'],
                '中台灣': ['苗栗縣', '台中市', '臺中市', '彰化縣', '南投縣', '雲林縣'],
                '南台灣': ['嘉義市', '嘉義縣', '台南市', '臺南市', '高雄市', '屏東縣'],
                '東台灣': ['花蓮縣', '台東縣', '臺東縣']
            }
            
            # 針對四個主要區域進行詳細縣市分析
            for region in ['北台灣', '中台灣', '南台灣', '東台灣']:
                # 獲取該區域應該包含的所有縣市
                expected_cities = region_cities_mapping.get(region, [])
                
                # 為每個縣市準備數據
                city_data = []
                for city in expected_cities:
                    # 按年度和縣市統計
                    city_df = df[df[region_col] == city]
                    city_by_year = city_df.groupby(year_col).size() if not city_df.empty else pd.Series()
                    
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
                    # 簡化名稱檢查邏輯
                    base_name = city_name.replace('臺', '台')
                    if base_name not in city_names_seen:
                        city_names_seen.add(base_name)
                        # 使用標準化的名稱
                        city_info['name'] = base_name
                        unique_city_data.append(city_info)
                    else:
                        # 如果已經有這個城市，合併數據
                        for existing_city in unique_city_data:
                            if existing_city['name'] == base_name:
                                # 合併數據（取最大值）
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

    except Exception as e:
        print(f"[geographic_stats] Error: {str(e)}")
        return jsonify({'error': f'處理資料時發生錯誤: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
