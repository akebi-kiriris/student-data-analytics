import pandas as pd

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

get_database_engine = None
resolve_column_name = None
auto_detect_subject_columns = None
classify_school_type = None
classify_admission_method = None
classify_region = None


def configure_analysis_service(
    get_database_engine_fn,
    resolve_column_name_fn,
    auto_detect_subject_columns_fn,
    classify_school_type_fn,
    classify_admission_method_fn,
    classify_region_fn,
):
    global get_database_engine, resolve_column_name, auto_detect_subject_columns, classify_school_type, classify_admission_method, classify_region
    get_database_engine = get_database_engine_fn
    resolve_column_name = resolve_column_name_fn
    auto_detect_subject_columns = auto_detect_subject_columns_fn
    classify_school_type = classify_school_type_fn
    classify_admission_method = classify_admission_method_fn
    classify_region = classify_region_fn
def column_stats(data):
    """
    從資料庫讀取資料並計算指定欄位的統計數據
    前端傳入 { table_name: 資料表名稱, column: 欄位名稱 }
    回傳該欄位的平均數、變異數、最大、最小、筆數
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        column = data.get('column')
        
        if not table_name or not column:
            return ({'error': '缺少 table_name 或 column'}), 400
            
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
            
        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            # 安全的欄位名稱
            safe_column = column.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            
            # 檢查欄位是否存在
            columns_info = current_inspector.get_columns(table_name)
            available_columns = [col['name'] for col in columns_info]
            
            if safe_column not in available_columns:
                return ({'error': f'找不到欄位 {column}，可用欄位：{available_columns}'}), 400
            
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
                return ({'error': '該欄位無有效數值可統計'}), 400
            
            import numpy as np
            stats = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                'min': float(min(values)),
                'max': float(max(values)),
                'count': len(values),
                'skipped': skipped
            }
            
            return ({
                'column': column, 
                'stats': stats,
                'raw_data': raw_values[:100]  # 限制回傳資料量
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return ({'error': str(e)}), 500

def multi_subject_stats(data):
    """
    從資料庫讀取多科目分年平均分析
    前端傳入 { table_name, subjects: [科目1, 科目2, ...], year_col }
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        subjects = data.get('subjects') or []
        year_col = data.get('year_col')
        
        if not table_name or not subjects:
            return ({'error': '缺少 table_name 或 subjects'}), 400
            
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
            
        # 取得欄位清單並動態解析欄位
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]

        try:
            resolved_year_col = resolve_column_name(
                year_col,
                available_columns,
                label='年度欄位',
                candidates=['年度', '入學年度', '學年度', 'year']
            )
        except ValueError as e:
            return ({'error': str(e)}), 400

        resolved_subjects = []
        missing_subjects = []
        for subject in subjects:
            try:
                resolved_col = resolve_column_name(subject, available_columns, label='科目欄位')
                resolved_subjects.append((subject, resolved_col))
            except ValueError:
                missing_subjects.append(subject)

        if missing_subjects:
            return ({'error': f'找不到科目欄位: {missing_subjects}'}), 400
        if not resolved_subjects:
            return ({'error': '沒有有效的科目欄位'}), 400
        
        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            # 構建查詢語句
            selected_subject_columns = [resolved for _, resolved in resolved_subjects]
            columns_str = f'"{resolved_year_col}", ' + ', '.join([f'"{col}"' for col in selected_subject_columns])
            query = text(
                f'SELECT {columns_str} FROM "{table_name}" '
                f'WHERE "{resolved_year_col}" IS NOT NULL AND "{resolved_year_col}" != ""'
            )
            result = session.execute(query).fetchall()
            
            # 轉換為 DataFrame 進行分析
            columns = [resolved_year_col] + selected_subject_columns
            df = pd.DataFrame(result, columns=columns)
            
            # 轉換年度欄位
            try:
                df[resolved_year_col] = pd.to_numeric(df[resolved_year_col], errors='coerce')
                df = df.dropna(subset=[resolved_year_col])
                df[resolved_year_col] = df[resolved_year_col].astype(int)
            except Exception as e:
                print(f"年度欄位轉換失敗: {e}")
                df[resolved_year_col] = df[resolved_year_col].astype(str)
            
            # 轉換科目欄位為數值
            for _, resolved_col in resolved_subjects:
                df[resolved_col] = pd.to_numeric(df[resolved_col], errors='coerce')
            
            # 按年度分組計算平均
            grouped = df.groupby(resolved_year_col)
            years = sorted(grouped.groups.keys())
            result_data = {original_col: [] for original_col, _ in resolved_subjects}
            
            for year in years:
                group = grouped.get_group(year)
                for original_col, resolved_col in resolved_subjects:
                    vals = group[resolved_col].dropna().tolist()
                    avg = sum(vals)/len(vals) if vals else None
                    result_data[original_col].append(avg)
                    
            return ({
                'years': years, 
                'subjects': [original for original, _ in resolved_subjects],
                'data': result_data
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return ({'error': str(e)}), 500

# 每年入學生數量分析（包含性別統計）- 從資料庫讀取
def yearly_admission_stats(data):
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        gender_col = data.get('gender_col')  # 可選的性別欄位

        if not table_name or not year_col:
            return ({'error': '缺少 table_name 或 year_col'}), 400

        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404

        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return ({'error': f'找不到年度欄位: {year_col}'}), 400

        has_gender = False
        safe_gender_col = None
        if gender_col:
            safe_gender_col = gender_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            if safe_gender_col in available_columns:
                has_gender = True

        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
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
                
                return ({
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
                
                return ({
                    'years': years, 
                    'total_counts': counts,
                    'total_students': int(year_counts.sum()),
                    'year_range': f"{min(years)} - {max(years)}" if years else "無資料",
                    'has_gender': False
                })
                
        finally:
            session.close()
            
    except Exception as e:
        return ({'error': str(e)}), 500


def school_source_stats(data):
    """
    從資料庫統計每年入學生的學校來源類型分布
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        school_col = data.get('school_col')  # 學校名稱欄位
        
        if not table_name or not year_col or not school_col:
            return ({'error': '缺少必要參數'}), 400
        
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
        
        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_school_col = school_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return ({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_school_col not in available_columns:
            return ({'error': f'找不到學校欄位: {school_col}'}), 400
        
        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            query = text(f'SELECT "{safe_year_col}", "{safe_school_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            if not result:
                return ({'error': '沒有有效的年份資料'}), 400
            
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
            
            return (result_data)
            
        finally:
            session.close()
            
    except Exception as e:
        return ({'error': str(e)}), 500


def admission_method_stats(data):
    """
    從資料庫統計入學管道分析
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        method_col = data.get('method_col')
        
        if not table_name or not year_col or not method_col:
            return ({'error': '缺少必要參數'}), 400
        
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
        
        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_method_col = method_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return ({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_method_col not in available_columns:
            return ({'error': f'找不到入學管道欄位: {method_col}'}), 400
        
        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            query = text(f'SELECT "{safe_year_col}", "{safe_method_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            if not result:
                return ({'error': '沒有有效的年份資料'}), 400
            
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
            
            return (result_data)
            
        finally:
            session.close()
            
    except Exception as e:
        return ({'error': str(e)}), 500

# 地理區域分類規則（已棄用，改用 classify_region 函數）
# 保留此變數以防有舊代碼引用
REGION_MAPPING = {
    # 北台灣
    '台北市': '北台灣',
    '新北市': '北台灣',
    '基隆市': '北台灣',
    '宜蘭縣': '北台灣',
    '桃園市': '北台灣',
    '新竹市': '北台灣',
    '新竹縣': '北台灣',
    
    # 中台灣
    '苗栗縣': '中台灣',
    '台中市': '中台灣',
    '彰化縣': '中台灣',
    '南投縣': '中台灣',
    '雲林縣': '中台灣',
    
    # 南台灣
    '嘉義市': '南台灣',
    '嘉義縣': '南台灣',
    '台南市': '南台灣',
    '高雄市': '南台灣',
    '屏東縣': '南台灣',
    
    # 東台灣
    '花蓮縣': '東台灣',
    '台東縣': '東台灣',
}

# 區域排序（用於確保圖表順序一致）
REGION_ORDER = ['北台灣', '中台灣', '南台灣', '東台灣', '其他']

def geographic_stats(data):
    """
    從資料庫進行地理區域分析
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        region_col = data.get('region_col')
        get_city_details = data.get('get_city_details', False)

        if not all([table_name, year_col, region_col]):
            return ({'error': '缺少必要參數'}), 400

        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404

        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_region_col = region_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return ({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_region_col not in available_columns:
            return ({'error': f'找不到地區欄位: {region_col}'}), 400

        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            query = text(f'SELECT "{safe_year_col}", "{safe_region_col}" FROM "{table_name}" WHERE "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
            result = session.execute(query).fetchall()
            
            if not result:
                return ({'error': '沒有有效的年份資料'}), 400
            
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
                
                # 定義每個區域應該包含的所有縣市（統一使用「台」，因為資料已在 classify_region 中轉換）
                region_cities_mapping = {
                    '北台灣': ['台北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '宜蘭縣'],
                    '中台灣': ['苗栗縣', '台中市', '彰化縣', '南投縣', '雲林縣'],
                    '南台灣': ['嘉義市', '嘉義縣', '台南市', '高雄市', '屏東縣'],
                    '東台灣': ['花蓮縣', '台東縣']
                }
                
                # 針對四個主要區域進行詳細縣市分析
                for region in ['北台灣', '中台灣', '南台灣', '東台灣']:
                    expected_cities = region_cities_mapping.get(region, [])
                    
                    city_data = []
                    for city in expected_cities:
                        # 先將資料庫中的縣市名稱標準化（統一轉成「台」）
                        df_normalized = df.copy()
                        df_normalized[safe_region_col] = df_normalized[safe_region_col].apply(lambda x: str(x).replace('臺', '台') if pd.notna(x) else x)
                        
                        # 按年度和縣市統計
                        city_df = df_normalized[df_normalized[safe_region_col] == city]
                        city_by_year = city_df.groupby(safe_year_col).size() if not city_df.empty else pd.Series()
                        
                        # 確保所有年份都有數據
                        year_data = []
                        for year in years:
                            if not city_by_year.empty and year in city_by_year.index:
                                year_data.append(int(city_by_year[year]))
                            else:
                                year_data.append(0)
                        
                        # 只有當該城市有資料時才加入
                        if sum(year_data) > 0:
                            city_data.append({
                                'name': city,
                                'data': year_data
                            })
                    
                    # 按總人數排序縣市
                    city_data.sort(key=lambda x: sum(x['data']), reverse=True)
                    
                    detailed[region] = {
                        'cities': city_data
                    }
                
                result['detailed'] = detailed
            
            return (result)
            
        finally:
            session.close()

    except Exception as e:
        print(f"[geographic_stats] Error: {str(e)}")
        return ({'error': f'處理資料時發生錯誤: {str(e)}'}), 500


def top_schools_stats(data):
    """前20大入學高中統計 - 使用統一的資料處理方式"""
    try:
        data = data or {}
        
        # 基本參數
        table_name = data.get('table_name')
        school_col = data.get('school_col')
        year_col = data.get('year_col')  # 可選
        
        if not table_name or not school_col:
            return ({'error': '資料表名稱和學校欄位為必要參數'}), 400
        
        print(f"[top_schools_stats] 開始分析前20大入學高中")
        print(f"[top_schools_stats] table_name: {table_name}")
        print(f"[top_schools_stats] school_col: {school_col}, year_col: {year_col}")
        
        # 使用統一的資料庫引擎獲取方法
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        # 安全化欄位名稱
        safe_school_col = school_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        if safe_school_col not in available_columns:
            return ({'error': f'找不到學校欄位: {school_col}'}), 400
        
        safe_year_col = None
        if year_col:
            safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            if safe_year_col not in available_columns:
                return ({'error': f'找不到年份欄位: {year_col}'}), 400
        
        # 建立資料庫會話
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        
        try:
            # 構建查詢語句
            if safe_year_col:
                select_cols = f'"{safe_school_col}", "{safe_year_col}"'
                query = text(f'SELECT {select_cols} FROM "{table_name}" WHERE "{safe_school_col}" IS NOT NULL AND "{safe_school_col}" != "" AND "{safe_year_col}" IS NOT NULL AND "{safe_year_col}" != ""')
                result = session.execute(query).fetchall()
                df = pd.DataFrame(result, columns=[safe_school_col, safe_year_col])
            else:
                query = text(f'SELECT "{safe_school_col}" FROM "{table_name}" WHERE "{safe_school_col}" IS NOT NULL AND "{safe_school_col}" != ""')
                result = session.execute(query).fetchall()
                df = pd.DataFrame(result, columns=[safe_school_col])
            
            if df.empty:
                return ({'error': '沒有找到資料'}), 400
            
            print(f"[top_schools_stats] 資料讀取完成，共 {len(df)} 筆記錄")
            
            # 清理學校名稱資料
            df[safe_school_col] = df[safe_school_col].fillna('未知')
            df[safe_school_col] = df[safe_school_col].astype(str).str.strip()
            
            # 過濾掉無效的學校名稱
            df = df[df[safe_school_col] != '']
            df = df[df[safe_school_col] != '未知']
            df = df[df[safe_school_col] != 'nan']
            
            result_data = {}
            
            if safe_year_col:
                # 按年份分析
                df[safe_year_col] = pd.to_numeric(df[safe_year_col], errors='coerce')
                df = df.dropna(subset=[safe_year_col])
                
                # 按學校和年份統計
                yearly_stats = df.groupby([safe_school_col, safe_year_col]).size().reset_index(name='count')
                
                # 計算每個學校的總人數
                school_totals = yearly_stats.groupby(safe_school_col)['count'].sum().reset_index()
                school_totals = school_totals.sort_values('count', ascending=False)
                
                # 取前20大學校
                top20_schools = school_totals.head(20)
                
                # 獲取年份列表
                years = sorted(df[safe_year_col].unique())
                
                # 為每個學校添加年度詳細資料
                schools_data = []
                total_students = df.shape[0]
                
                for idx, (_, row) in enumerate(top20_schools.iterrows()):
                    school_name = row[safe_school_col]
                    total_count = row['count']
                    
                    school_data = {
                        'rank': idx + 1,
                        'school_name': school_name,
                        'total_count': int(total_count),
                        'percentage': round((total_count / total_students) * 100, 2)
                    }
                    
                    # 添加每年的詳細數據
                    for year in years:
                        year_count = yearly_stats[
                            (yearly_stats[safe_school_col] == school_name) & 
                            (yearly_stats[safe_year_col] == year)
                        ]['count'].sum()
                        school_data[f'year_{int(year)}'] = int(year_count)
                    
                    schools_data.append(school_data)
                
                result_data = {
                    'schools': schools_data,
                    'total_students': int(total_students),
                    'by_year': True,
                    'years': [int(year) for year in years]
                }
                
            else:
                # 不按年份分析
                school_counts = df[safe_school_col].value_counts().reset_index()
                school_counts.columns = [safe_school_col, 'count']
                
                # 取前20大學校
                top20_schools = school_counts.head(20)
                
                # 格式化結果
                schools_data = []
                total_students = df.shape[0]
                
                for idx, (_, row) in enumerate(top20_schools.iterrows()):
                    schools_data.append({
                        'rank': idx + 1,
                        'school_name': row[safe_school_col],
                        'total_count': int(row['count']),
                        'percentage': round((row['count'] / total_students) * 100, 2)
                    })
                
                result_data = {
                    'schools': schools_data,
                    'total_students': int(total_students),
                    'by_year': False
                }
            
            print(f"[top_schools_stats] 分析完成，前20大學校數據已生成")
            return (result_data)
            
        finally:
            session.close()

    except Exception as e:
        print(f"[top_schools_stats] Error: {str(e)}")
        return ({'error': f'處理資料時發生錯誤: {str(e)}'}), 500


def subject_average_stats(data):
    """大一各科平均成績分析（動態欄位版本）。"""
    session = None
    try:
        data = data or {}
        table_name = data.get('table_name')

        if not table_name:
            return ({'error': '缺少 table_name 參數'}), 400

        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404

        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]

        try:
            year_col = resolve_column_name(
                data.get('year_col'),
                available_columns,
                label='年度欄位',
                candidates=['年度', '入學年度', '學年度', 'year']
            )
        except ValueError as e:
            return ({'error': str(e)}), 400

        gender_col = resolve_column_name(
            data.get('gender_col'),
            available_columns,
            label='性別欄位',
            candidates=['性別', 'gender', 'sex'],
            required=False
        )
        school_type_col = resolve_column_name(
            data.get('school_type_col'),
            available_columns,
            label='高中類型欄位',
            candidates=['高中別', '學校類型', '學校別', 'school_type', 'school'],
            required=False
        )
        admission_col = resolve_column_name(
            data.get('admission_col'),
            available_columns,
            label='入學管道欄位',
            candidates=['入學管道', '管道', 'admission_method', 'admission'],
            required=False
        )

        requested_subjects = data.get('subjects') or []
        subject_pairs = []
        seen_subject_columns = set()

        if requested_subjects:
            for subject in requested_subjects:
                try:
                    resolved_col = resolve_column_name(subject, available_columns, label='科目欄位')
                    if resolved_col not in seen_subject_columns:
                        subject_pairs.append((subject, resolved_col))
                        seen_subject_columns.add(resolved_col)
                except ValueError:
                    continue
        else:
            preferred_subjects = [
                '會計學', '計算機概論', '微積分', '基礎程式設計',
                '統計1', '經濟學', '程式設計', '管理學', '統計2'
            ]
            for subject in preferred_subjects:
                resolved_col = resolve_column_name(subject, available_columns, label='科目欄位', required=False)
                if resolved_col and resolved_col not in seen_subject_columns:
                    subject_pairs.append((subject, resolved_col))
                    seen_subject_columns.add(resolved_col)

        if not subject_pairs:
            auto_subjects = auto_detect_subject_columns(
                available_columns,
                excluded_columns=[year_col, gender_col, school_type_col, admission_col]
            )
            for subject in auto_subjects:
                if subject not in seen_subject_columns:
                    subject_pairs.append((subject, subject))
                    seen_subject_columns.add(subject)

        if not subject_pairs:
            return ({'error': '找不到可分析的科目欄位，請在請求中指定 subjects'}), 400

        selected_subject_columns = [resolved for _, resolved in subject_pairs]
        selected_subject_labels = {resolved: original for original, resolved in subject_pairs}

        select_columns = [year_col]
        if gender_col:
            select_columns.append(gender_col)
        if school_type_col:
            select_columns.append(school_type_col)
        if admission_col:
            select_columns.append(admission_col)
        select_columns.extend(selected_subject_columns)

        # 依序去重，避免欄位重複出現在 SELECT
        select_columns = list(dict.fromkeys(select_columns))

        select_clause = ', '.join([f'"{col}"' for col in select_columns])
        query = text(
            f'SELECT {select_clause} FROM "{table_name}" '
            f'WHERE "{year_col}" IS NOT NULL AND "{year_col}" != ""'
        )

        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        result_rows = session.execute(query).fetchall()

        complete_df = pd.DataFrame(result_rows, columns=select_columns)
        if complete_df.empty:
            return ({'error': '沒有找到相關資料'}), 404

        complete_df[year_col] = pd.to_numeric(complete_df[year_col], errors='coerce')
        complete_df = complete_df.dropna(subset=[year_col])
        if complete_df.empty:
            return ({'error': '年度欄位沒有可用資料'}), 400
        complete_df[year_col] = complete_df[year_col].astype(int)

        for subject_col in selected_subject_columns:
            complete_df[subject_col] = pd.to_numeric(complete_df[subject_col], errors='coerce')

        # 僅保留至少有一筆有效分數的科目
        valid_subject_columns = [col for col in selected_subject_columns if complete_df[col].notna().any()]
        if not valid_subject_columns:
            return ({'error': '所選科目欄位皆無有效數值資料'}), 400

        selected_subject_columns = valid_subject_columns
        subject_labels = [selected_subject_labels[col] for col in selected_subject_columns]

        school_types = ['國立', '私立', '財團', '市立', '其他', '私大轉', '科大轉', '國大轉', '僑生']
        admission_types = ['申請入學', '繁星推薦', '自然組', '社會組', '僑生', '願景', '其他']

        years = sorted(complete_df[year_col].unique())
        yearly_averages = []

        for year in years:
            year_data = complete_df[complete_df[year_col] == year].copy()
            year_avg = {'年度': int(year), '總人數': int(len(year_data))}

            # 性別統計
            if gender_col and gender_col in year_data.columns:
                normalized_gender = year_data[gender_col].astype(str).str.strip().str.upper().replace({
                    'M': '男', 'MALE': '男', '男生': '男', '1': '男',
                    'F': '女', 'FEMALE': '女', '女生': '女', '2': '女'
                })
                year_avg['男性人數'] = int((normalized_gender == '男').sum())
                year_avg['女性人數'] = int((normalized_gender == '女').sum())
            else:
                year_avg['男性人數'] = 0
                year_avg['女性人數'] = 0

            # 高中類型統計
            school_type_counts = {}
            if school_type_col and school_type_col in year_data.columns:
                classified_school_types = year_data[school_type_col].apply(classify_school_type)
                school_type_counts = classified_school_types.value_counts().to_dict()
            for school_type in school_types:
                year_avg[f'{school_type}人數'] = int(school_type_counts.get(school_type, 0))

            # 入學管道統計
            admission_counts = {}
            if admission_col and admission_col in year_data.columns:
                classified_admission = year_data[admission_col].apply(classify_admission_method)
                admission_counts = classified_admission.value_counts().to_dict()
            for admission_type in admission_types:
                year_avg[f'{admission_type}人數'] = int(admission_counts.get(admission_type, 0))

            # 科目平均成績
            for subject_col in selected_subject_columns:
                label = selected_subject_labels[subject_col]
                valid_scores = year_data[subject_col].dropna()
                year_avg[label] = round(float(valid_scores.mean()), 2) if len(valid_scores) > 0 else None

            yearly_averages.append(year_avg)

        overall_stats = {}
        for subject_col in selected_subject_columns:
            label = selected_subject_labels[subject_col]
            valid_scores = complete_df[subject_col].dropna()
            if len(valid_scores) > 0:
                overall_stats[label] = {
                    'overall_average': round(float(valid_scores.mean()), 2),
                    'min_score': round(float(valid_scores.min()), 2),
                    'max_score': round(float(valid_scores.max()), 2),
                    'std_dev': round(float(valid_scores.std()), 2) if len(valid_scores) > 1 else 0.0,
                    'total_students': int(len(valid_scores))
                }
            else:
                overall_stats[label] = {
                    'overall_average': None,
                    'min_score': None,
                    'max_score': None,
                    'std_dev': None,
                    'total_students': 0
                }

        subject_averages = [
            (subject, stats['overall_average'])
            for subject, stats in overall_stats.items()
            if stats['overall_average'] is not None
        ]
        highest_subject = max(subject_averages, key=lambda x: x[1]) if subject_averages else None
        lowest_subject = min(subject_averages, key=lambda x: x[1]) if subject_averages else None

        gender_summary = {'男性': 0, '女性': 0}
        if gender_col and gender_col in complete_df.columns:
            normalized_gender = complete_df[gender_col].astype(str).str.strip().str.upper().replace({
                'M': '男', 'MALE': '男', '男生': '男', '1': '男',
                'F': '女', 'FEMALE': '女', '女生': '女', '2': '女'
            })
            gender_summary = {
                '男性': int((normalized_gender == '男').sum()),
                '女性': int((normalized_gender == '女').sum())
            }

        school_type_summary = {}
        if school_type_col and school_type_col in complete_df.columns:
            school_type_summary = {
                k: int(v)
                for k, v in complete_df[school_type_col].apply(classify_school_type).value_counts().to_dict().items()
            }

        admission_summary = {}
        if admission_col and admission_col in complete_df.columns:
            admission_summary = {
                k: int(v)
                for k, v in complete_df[admission_col].apply(classify_admission_method).value_counts().to_dict().items()
            }

        result = {
            'yearly_data': yearly_averages,
            'overall_stats': overall_stats,
            'subjects': subject_labels,
            'years': [int(year) for year in years],
            'year_range': f"{int(min(years))}-{int(max(years))}",
            'total_students': int(len(complete_df)),
            'gender_summary': gender_summary,
            'school_type_summary': school_type_summary,
            'admission_summary': admission_summary,
            'school_types': school_types,
            'admission_types': admission_types,
            'highest_subject': {
                'subject': highest_subject[0],
                'average': highest_subject[1]
            } if highest_subject else None,
            'lowest_subject': {
                'subject': lowest_subject[0],
                'average': lowest_subject[1]
            } if lowest_subject else None,
            'column_name': '大一各科平均成績',
            'resolved_columns': {
                'year_col': year_col,
                'gender_col': gender_col,
                'school_type_col': school_type_col,
                'admission_col': admission_col,
                'subject_cols': selected_subject_columns
            }
        }

        print(f"[subject_average_stats] 分析完成，涵蓋 {len(years)} 年度、{len(subject_labels)} 科目")
        return (result)

    except Exception as e:
        print(f"[subject_average_stats] Error: {str(e)}")
        return ({'error': f'處理資料時發生錯誤: {str(e)}'}), 500

    finally:
        if session is not None:
            session.close()


def gender_subject_analysis(data):
    """
    性別科目成績分析 API
    支援多科目選擇，分析男女生在各科目間的成績差異
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        gender_col = data.get('gender_col')
        subject_cols = data.get('subjects', [])
        years_filter = data.get('years', [])
        enable_grouping = data.get('enable_grouping', False)
        subject_groups = data.get('subject_groups', [])
        analysis_mode = data.get('analysis_mode', 'yearly')  # 'yearly' 或 'overall'
        
        print(f"[gender_subject_analysis] 開始分析，表格: {table_name}")
        print(f"[gender_subject_analysis] 年度欄位: {year_col}, 性別欄位: {gender_col}")
        print(f"[gender_subject_analysis] 科目欄位: {subject_cols}")
        print(f"[gender_subject_analysis] 年份篩選: {years_filter}")
        print(f"[gender_subject_analysis] 啟用分組: {enable_grouping}")
        print(f"[gender_subject_analysis] 科目分組: {subject_groups}")
        print(f"[gender_subject_analysis] 分析模式: {analysis_mode}")
        
        if not all([table_name, year_col, gender_col, subject_cols]):
            return ({'error': '缺少必要參數'}), 400
        
        if not isinstance(subject_cols, list) or len(subject_cols) == 0:
            return ({'error': '請至少選擇一個科目'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
        
        Session = sessionmaker(bind=current_engine)
        session = Session()
        
        # 獲取表格欄位資訊
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        print(f"[gender_subject_analysis] 可用欄位: {available_columns}")
        
        # 安全化欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_gender_col = gender_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_subject_cols = []
        
        for col in subject_cols:
            safe_col = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            if safe_col in available_columns:
                safe_subject_cols.append({'original': col, 'safe': safe_col})
            else:
                print(f"[gender_subject_analysis] 警告：科目欄位 '{col}' 不存在")
        
        if not safe_subject_cols:
            return ({'error': '沒有找到有效的科目欄位'}), 400
        
        # 檢查必要欄位是否存在
        if safe_year_col not in available_columns:
            return ({'error': f'年度欄位 {year_col} 不存在'}), 400
        if safe_gender_col not in available_columns:
            return ({'error': f'性別欄位 {gender_col} 不存在'}), 400
        
        # 建構 SQL 查詢 - 包含年度、性別和所有科目欄位
        select_cols = [f'"{safe_year_col}"', f'"{safe_gender_col}"']
        select_cols.extend([f'"{subject["safe"]}"' for subject in safe_subject_cols])
        
        # 建構 WHERE 條件
        where_conditions = [
            f'"{safe_year_col}" IS NOT NULL',
            f'"{safe_year_col}" != ""',
            f'"{safe_gender_col}" IS NOT NULL',
            f'"{safe_gender_col}" != ""'
        ]
        
        # 如果有年份篩選，添加年份條件
        if years_filter and len(years_filter) > 0:
            years_str = ', '.join([str(year) for year in years_filter])
            where_conditions.append(f'"{safe_year_col}" IN ({years_str})')
        
        query = text(f'''
            SELECT {", ".join(select_cols)}
            FROM "{table_name}" 
            WHERE {" AND ".join(where_conditions)}
        ''')
        
        print(f"[gender_subject_analysis] 執行查詢: {query}")
        result = session.execute(query)
        
        # 建立 DataFrame
        column_names = [safe_year_col, safe_gender_col] + [subject['safe'] for subject in safe_subject_cols]
        df = pd.DataFrame(result.fetchall(), columns=column_names)
        
        if df.empty:
            return ({'error': '沒有找到符合條件的資料'}), 404
        
        print(f"[gender_subject_analysis] 查詢到 {len(df)} 筆資料")
        
        # 資料清理和標準化
        df[safe_year_col] = pd.to_numeric(df[safe_year_col], errors='coerce')
        df = df.dropna(subset=[safe_year_col])
        
        # 性別資料標準化
        df[safe_gender_col] = df[safe_gender_col].astype(str).str.strip().str.upper()
        gender_mapping = {
            'M': '男', 'MALE': '男', '男': '男', '男生': '男', '1': '男',
            'F': '女', 'FEMALE': '女', '女': '女', '女生': '女', '0': '女'
        }
        df[safe_gender_col] = df[safe_gender_col].replace(gender_mapping)
        
        # 只保留有效的性別資料
        df = df[df[safe_gender_col].isin(['男', '女'])]
        
        if df.empty:
            return ({'error': '沒有找到有效的性別資料'}), 404
        
        # 科目成績資料轉為數值
        for subject in safe_subject_cols:
            df[subject['safe']] = pd.to_numeric(df[subject['safe']], errors='coerce')
        
        # 處理科目分組
        final_subjects = []
        if enable_grouping and subject_groups:
            print(f"[gender_subject_analysis] 處理科目分組")
            # 處理分組科目
            for group in subject_groups:
                group_name = group.get('name', '').strip()
                group_subjects = group.get('subjects', [])
                
                if not group_name or not group_subjects:
                    continue
                    
                # 找到分組中的有效科目欄位
                valid_group_subjects = []
                for subj in group_subjects:
                    for safe_subj in safe_subject_cols:
                        if safe_subj['original'] == subj:
                            valid_group_subjects.append(safe_subj['safe'])
                            break
                
                if valid_group_subjects:
                    # 計算分組平均（多科目的平均）
                    group_col = f"group_{len(final_subjects)}"
                    df[group_col] = df[valid_group_subjects].mean(axis=1)
                    final_subjects.append({'original': group_name, 'safe': group_col, 'is_group': True})
                    print(f"[gender_subject_analysis] 建立分組 '{group_name}'，包含科目: {group_subjects}")
        else:
            # 不分組，使用原始科目
            final_subjects = [{'original': subj['original'], 'safe': subj['safe'], 'is_group': False} for subj in safe_subject_cols]
        
        # 分析結果結構
        analysis_results = {
            'subjects': [subject['original'] for subject in final_subjects],
            'year_range': f"{df[safe_year_col].min()}-{df[safe_year_col].max()}",
            'total_records': len(df),
            'subject_details': {},
            'overall_summary': {},
            'enable_grouping': enable_grouping,
            'analysis_mode': analysis_mode
        }
        
        # 整體男女平均成績
        overall_male_scores = []
        overall_female_scores = []
        
        # 逐科目分析
        for subject in final_subjects:
            subject_name = subject['original']
            subject_col = subject['safe']
            
            # 過濾有效成績
            subject_df = df[[safe_year_col, safe_gender_col, subject_col]].dropna()
            
            if subject_df.empty:
                continue
            
            # 年度分組分析
            yearly_stats = []
            years = sorted(subject_df[safe_year_col].unique())
            
            for year in years:
                year_data = subject_df[subject_df[safe_year_col] == year]
                
                male_data = year_data[year_data[safe_gender_col] == '男'][subject_col]
                female_data = year_data[year_data[safe_gender_col] == '女'][subject_col]
                
                male_avg = male_data.mean() if len(male_data) > 0 else None
                female_avg = female_data.mean() if len(female_data) > 0 else None
                
                yearly_stats.append({
                    'year': int(year),
                    'male_avg': round(male_avg, 2) if male_avg is not None else None,
                    'female_avg': round(female_avg, 2) if female_avg is not None else None,
                    'male_count': len(male_data),
                    'female_count': len(female_data),
                    'difference': round(male_avg - female_avg, 2) if male_avg is not None and female_avg is not None else None
                })
                
                # 收集整體統計用的資料
                if male_avg is not None:
                    overall_male_scores.extend(male_data.tolist())
                if female_avg is not None:
                    overall_female_scores.extend(female_data.tolist())
            
            analysis_results['subject_details'][subject_name] = yearly_stats
        
        # 計算整體統計
        if overall_male_scores and overall_female_scores:
            analysis_results['overall_summary'] = {
                'male_avg': round(sum(overall_male_scores) / len(overall_male_scores), 2),
                'female_avg': round(sum(overall_female_scores) / len(overall_female_scores), 2),
                'total_male_records': len(overall_male_scores),
                'total_female_records': len(overall_female_scores)
            }
            
            # 計算整體差異
            overall_diff = analysis_results['overall_summary']['male_avg'] - analysis_results['overall_summary']['female_avg']
            analysis_results['overall_summary']['difference'] = round(overall_diff, 2)
        
        # 如果是整體平均分析模式，添加科目對比數據
        if analysis_mode == 'overall':
            subject_comparison = []
            
            for subject in final_subjects:
                subject_name = subject['original']
                subject_col = subject['safe']
                
                # 過濾有效成績
                subject_df = df[[safe_year_col, safe_gender_col, subject_col]].dropna()
                
                if subject_df.empty:
                    continue
                
                # 計算整體男女平均（所有年份合併）
                male_data = subject_df[subject_df[safe_gender_col] == '男'][subject_col]
                female_data = subject_df[subject_df[safe_gender_col] == '女'][subject_col]
                
                male_avg = male_data.mean() if len(male_data) > 0 else None
                female_avg = female_data.mean() if len(female_data) > 0 else None
                
                if male_avg is not None and female_avg is not None:
                    difference = round(male_avg - female_avg, 2)
                    subject_comparison.append({
                        'subject': subject_name,
                        'male_avg': round(male_avg, 2),
                        'female_avg': round(female_avg, 2),
                        'difference': difference,
                        'male_count': len(male_data),
                        'female_count': len(female_data)
                    })
            
            analysis_results['subject_comparison'] = subject_comparison
            print(f"[gender_subject_analysis] 整體平均分析模式，處理了 {len(subject_comparison)} 個科目對比")
        
        print(f"[gender_subject_analysis] 分析完成，涵蓋 {len(final_subjects)} 科目，模式: {analysis_mode}")
        return (analysis_results)
        
    except Exception as e:
        print(f"[gender_subject_analysis] Error: {str(e)}")
        return ({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


def admission_subject_analysis(data):
    """
    入學管道科目成績分析 API
    支援多科目選擇，分析不同入學管道學生在各科目間的成績差異
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        admission_col = data.get('admission_col')
        subject_cols = data.get('subjects', [])
        years_filter = data.get('years', [])
        enable_grouping = data.get('enable_grouping', False)
        admission_groups = data.get('admission_groups', [])
        
        print(f"[admission_subject_analysis] 開始分析，表格: {table_name}")
        print(f"[admission_subject_analysis] 年度欄位: {year_col}, 入學管道欄位: {admission_col}")
        print(f"[admission_subject_analysis] 科目欄位: {subject_cols}")
        print(f"[admission_subject_analysis] 年份篩選: {years_filter}")
        print(f"[admission_subject_analysis] 啟用分組: {enable_grouping}")
        print(f"[admission_subject_analysis] 入學管道分組: {admission_groups}")
        
        if not all([table_name, year_col, admission_col, subject_cols]):
            return ({'error': '缺少必要參數'}), 400
        
        if not isinstance(subject_cols, list) or len(subject_cols) == 0:
            return ({'error': '請至少選擇一個科目'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
        
        Session = sessionmaker(bind=current_engine)
        session = Session()
        
        # 獲取表格欄位資訊
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        print(f"[admission_subject_analysis] 可用欄位: {available_columns}")
        
        # 安全化欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_admission_col = admission_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_subject_cols = []
        
        for col in subject_cols:
            safe_col = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            if safe_col in available_columns:
                safe_subject_cols.append({'original': col, 'safe': safe_col})
            else:
                print(f"[admission_subject_analysis] 警告：科目欄位 '{col}' 不存在")
        
        if not safe_subject_cols:
            return ({'error': '沒有找到有效的科目欄位'}), 400
        
        # 檢查必要欄位是否存在
        if safe_year_col not in available_columns:
            return ({'error': f'年度欄位 {year_col} 不存在'}), 400
        if safe_admission_col not in available_columns:
            return ({'error': f'入學管道欄位 {admission_col} 不存在'}), 400
        
        # 建構 SQL 查詢 - 包含年度、入學管道和所有科目欄位
        select_cols = [f'"{safe_year_col}"', f'"{safe_admission_col}"']
        select_cols.extend([f'"{subject["safe"]}"' for subject in safe_subject_cols])
        
        # 建構 WHERE 條件
        where_conditions = [
            f'"{safe_year_col}" IS NOT NULL',
            f'"{safe_year_col}" != ""',
            f'"{safe_admission_col}" IS NOT NULL',
            f'"{safe_admission_col}" != ""'
        ]
        
        # 如果有年份篩選，添加年份條件
        if years_filter and len(years_filter) > 0:
            years_str = ', '.join([str(year) for year in years_filter])
            where_conditions.append(f'"{safe_year_col}" IN ({years_str})')
        
        query = text(f'''
            SELECT {", ".join(select_cols)}
            FROM "{table_name}" 
            WHERE {" AND ".join(where_conditions)}
        ''')
        
        print(f"[admission_subject_analysis] 執行查詢: {query}")
        result = session.execute(query)
        
        # 讀取資料並轉換為 DataFrame
        df = pd.DataFrame(result.fetchall(), columns=[safe_year_col, safe_admission_col] + [subject["safe"] for subject in safe_subject_cols])
        
        if df.empty:
            return ({'error': '查詢結果為空，請檢查篩選條件'}), 404
        
        print(f"[admission_subject_analysis] 讀取到 {len(df)} 筆資料")
        
        # 使用入學管道分類函數對資料進行分類
        df['classified_admission'] = df[safe_admission_col].apply(classify_admission_method)
        
        # 獲取所有可用的年份，過濾空值和空字串
        all_years = sorted([year for year in df[safe_year_col].unique().tolist() if str(year).strip() != ''])
        
        # 獲取所有入學管道類別
        all_admission_methods = sorted(df['classified_admission'].unique().tolist())
        
        # 處理入學管道過濾 - 如果啟用了分組，只包含分組中指定的入學管道
        final_admission_methods = all_admission_methods
        if enable_grouping and admission_groups:
            grouped_methods = set()
            for group in admission_groups:
                group_methods = group.get('methods', [])
                if group_methods:
                    grouped_methods.update(group_methods)
            # 只保留在分組中指定的入學管道
            final_admission_methods = [method for method in all_admission_methods if method in grouped_methods]
        
        print(f"[admission_subject_analysis] 最終入學管道: {final_admission_methods}")
        
        # 處理科目（這裡不需要分組，直接使用選中的科目）
        final_subjects = []
        for subject in safe_subject_cols:
            final_subjects.append({
                'name': subject['original'],
                'type': 'single',
                'subjects': [subject['original']]
            })
        
        # 準備分析結果
        analysis_results = {
            'years': all_years,
            'admission_methods': final_admission_methods,  # 使用過濾後的入學管道
            'subjects': [subject['name'] for subject in final_subjects],
            'method_details': {}
        }
        
        # 對每個最終入學管道進行分析
        for method in final_admission_methods:
            method_data = df[df['classified_admission'] == method].copy()
            yearly_data = []
            
            for year in all_years:
                year_data = method_data[method_data[safe_year_col] == year]
                
                if not year_data.empty:
                    year_result = {'year': year, 'subjects': {}}
                    
                    for subject_info in final_subjects:
                        subject_name = subject_info['name']
                        subject_type = subject_info['type']
                        subject_cols_list = subject_info['subjects']
                        
                        if subject_type == 'group':
                            # 科目分組：計算多個科目的平均分
                            valid_scores = []
                            for subject_col in subject_cols_list:
                                # 找到對應的安全欄位名稱
                                safe_col = None
                                for safe_subject in safe_subject_cols:
                                    if safe_subject['original'] == subject_col:
                                        safe_col = safe_subject['safe']
                                        break
                                
                                if safe_col and safe_col in year_data.columns:
                                    scores = pd.to_numeric(year_data[safe_col], errors='coerce').dropna()
                                    valid_scores.extend(scores.tolist())
                            
                            if valid_scores:
                                group_avg = round(sum(valid_scores) / len(valid_scores), 2)
                                year_result['subjects'][subject_name] = group_avg
                        else:
                            # 單一科目：直接計算該科目的平均分
                            subject_col = subject_cols_list[0]
                            safe_col = None
                            for safe_subject in safe_subject_cols:
                                if safe_subject['original'] == subject_col:
                                    safe_col = safe_subject['safe']
                                    break
                            
                            if safe_col and safe_col in year_data.columns:
                                scores = pd.to_numeric(year_data[safe_col], errors='coerce').dropna()
                                if len(scores) > 0:
                                    subject_avg = round(scores.mean(), 2)
                                    year_result['subjects'][subject_name] = subject_avg
                    
                    yearly_data.append(year_result)
            
            analysis_results['method_details'][method] = yearly_data
        
        print(f"[admission_subject_analysis] 分析完成，涵蓋 {len(final_subjects)} 科目，{len(all_admission_methods)} 個入學管道")
        return (analysis_results)
        
    except Exception as e:
        print(f"[admission_subject_analysis] Error: {str(e)}")
        return ({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


def school_type_subject_analysis(data):
    """
    高中類型科目成績分析 API
    支援多科目選擇，分析不同高中類型學生在各科目間的成績差異
    """
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        school_type_col = data.get('school_type_col')
        subject_cols = data.get('subjects', [])
        years_filter = data.get('years', [])
        enable_grouping = data.get('enable_grouping', False)
        school_type_groups = data.get('school_type_groups', [])
        
        print(f"[school_type_subject_analysis] 開始分析，表格: {table_name}")
        print(f"[school_type_subject_analysis] 年度欄位: {year_col}, 高中類型欄位: {school_type_col}")
        print(f"[school_type_subject_analysis] 科目欄位: {subject_cols}")
        print(f"[school_type_subject_analysis] 年份篩選: {years_filter}")
        print(f"[school_type_subject_analysis] 啟用分組: {enable_grouping}")
        print(f"[school_type_subject_analysis] 高中類型分組: {school_type_groups}")
        
        if not all([table_name, year_col, school_type_col, subject_cols]):
            return ({'error': '缺少必要參數'}), 400
        
        if not isinstance(subject_cols, list) or len(subject_cols) == 0:
            return ({'error': '請至少選擇一個科目'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 404
        
        Session = sessionmaker(bind=current_engine)
        session = Session()
        
        # 檢查表格是否存在 - 這裡不需要，因為 get_database_engine 已經檢查過了
        
        # 獲取表格欄位資訊
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        print(f"[school_type_subject_analysis] 可用欄位: {available_columns}")
        
        # 安全化欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_school_type_col = school_type_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_subject_cols = []
        
        for col in subject_cols:
            safe_col = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            if safe_col in available_columns:
                safe_subject_cols.append({'original': col, 'safe': safe_col})
            else:
                print(f"[school_type_subject_analysis] 警告：科目欄位 '{col}' 不存在")
        
        if not safe_subject_cols:
            return ({'error': '沒有找到有效的科目欄位'}), 400
        
        # 檢查必要欄位是否存在
        if safe_year_col not in available_columns:
            return ({'error': f'年度欄位 {year_col} 不存在'}), 400
        if safe_school_type_col not in available_columns:
            return ({'error': f'高中類型欄位 {school_type_col} 不存在'}), 400
        
        # 建構 SQL 查詢 - 包含年度、高中類型和所有科目欄位
        select_cols = [f'"{safe_year_col}"', f'"{safe_school_type_col}"']
        select_cols.extend([f'"{subject["safe"]}"' for subject in safe_subject_cols])
        
        # 建構 WHERE 條件
        where_conditions = [
            f'"{safe_year_col}" IS NOT NULL',
            f'"{safe_year_col}" != ""',
            f'"{safe_school_type_col}" IS NOT NULL',
            f'"{safe_school_type_col}" != ""'
        ]
        
        # 如果有年份篩選，添加年份條件
        if years_filter and len(years_filter) > 0:
            years_str = ', '.join([str(year) for year in years_filter])
            where_conditions.append(f'"{safe_year_col}" IN ({years_str})')
        
        query = text(f'''
            SELECT {", ".join(select_cols)}
            FROM "{table_name}" 
            WHERE {" AND ".join(where_conditions)}
        ''')
        
        print(f"[school_type_subject_analysis] 執行查詢: {query}")
        result = session.execute(query)
        
        # 讀取資料並轉換為 DataFrame
        df = pd.DataFrame(result.fetchall(), columns=[safe_year_col, safe_school_type_col] + [subject["safe"] for subject in safe_subject_cols])
        
        if df.empty:
            return ({'error': '查詢結果為空，請檢查篩選條件'}), 404
        
        print(f"[school_type_subject_analysis] 讀取到 {len(df)} 筆資料")
        
        # 使用高中類型分類函數對資料進行分類
        df['classified_school_type'] = df[safe_school_type_col].apply(classify_school_type)
        
        # 獲取所有可用的年份，過濾空值和空字串
        all_years = sorted([year for year in df[safe_year_col].unique().tolist() if str(year).strip() != ''])
        
        # 獲取所有高中類型類別
        all_school_types = sorted(df['classified_school_type'].unique().tolist())
        
        # 處理高中類型過濾 - 如果啟用了分組，只包含分組中指定的高中類型
        final_school_types = all_school_types
        if enable_grouping and school_type_groups:
            grouped_types = set()
            for group in school_type_groups:
                group_types = group.get('types', [])
                if group_types:
                    grouped_types.update(group_types)
            # 只保留在分組中指定的高中類型
            final_school_types = [school_type for school_type in all_school_types if school_type in grouped_types]
        
        print(f"[school_type_subject_analysis] 最終高中類型: {final_school_types}")
        
        # 處理科目（這裡不需要分組，直接使用選中的科目）
        final_subjects = []
        for subject in safe_subject_cols:
            final_subjects.append({
                'name': subject['original'],
                'type': 'single',
                'subjects': [subject['original']]
            })
        
        # 準備分析結果
        analysis_results = {
            'years': all_years,
            'school_types': final_school_types,  # 使用過濾後的高中類型
            'subjects': [subject['name'] for subject in final_subjects],
            'type_details': {}
        }
        
        # 對每個最終高中類型進行分析
        for school_type in final_school_types:
            type_data = df[df['classified_school_type'] == school_type].copy()
            yearly_data = []
            
            for year in all_years:
                year_data = type_data[type_data[safe_year_col] == year]
                
                if not year_data.empty:
                    year_result = {'year': year, 'subjects': {}}
                    
                    for subject_info in final_subjects:
                        subject_name = subject_info['name']
                        subject_type = subject_info['type']
                        subject_cols_list = subject_info['subjects']
                        
                        if subject_type == 'group':
                            # 科目分組：計算多個科目的平均分
                            valid_scores = []
                            for subject_col in subject_cols_list:
                                # 找到對應的安全欄位名稱
                                safe_col = None
                                for safe_subject in safe_subject_cols:
                                    if safe_subject['original'] == subject_col:
                                        safe_col = safe_subject['safe']
                                        break
                                
                                if safe_col and safe_col in year_data.columns:
                                    scores = pd.to_numeric(year_data[safe_col], errors='coerce').dropna()
                                    valid_scores.extend(scores.tolist())
                            
                            if valid_scores:
                                group_avg = round(sum(valid_scores) / len(valid_scores), 2)
                                year_result['subjects'][subject_name] = group_avg
                        else:
                            # 單一科目：直接計算該科目的平均分
                            subject_col = subject_cols_list[0]
                            safe_col = None
                            for safe_subject in safe_subject_cols:
                                if safe_subject['original'] == subject_col:
                                    safe_col = safe_subject['safe']
                                    break
                            
                            if safe_col and safe_col in year_data.columns:
                                scores = pd.to_numeric(year_data[safe_col], errors='coerce').dropna()
                                if len(scores) > 0:
                                    subject_avg = round(scores.mean(), 2)
                                    year_result['subjects'][subject_name] = subject_avg
                    
                    yearly_data.append(year_result)
            
            analysis_results['type_details'][school_type] = yearly_data
        
        print(f"[school_type_subject_analysis] 分析完成，涵蓋 {len(final_subjects)} 科目，{len(final_school_types)} 個高中類型")
        return (analysis_results)
        
    except Exception as e:
        print(f"[school_type_subject_analysis] Error: {str(e)}")
        return ({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


def region_subject_analysis(data):
    """地區科目成績分析API"""
    session = None
    try:
        data = data or {}
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        region_col = data.get('region_col')
        subject_cols = data.get('subjects', [])
        years_filter = data.get('years', [])
        enable_grouping = data.get('enable_grouping', False)
        region_groups = data.get('region_groups', [])
        
        print(f"[region_subject_analysis] 開始分析，表格: {table_name}")
        print(f"[region_subject_analysis] 年度欄位: {year_col}, 地區欄位: {region_col}")
        print(f"[region_subject_analysis] 科目欄位: {subject_cols}")
        print(f"[region_subject_analysis] 年份篩選: {years_filter}")
        print(f"[region_subject_analysis] 啟用分組: {enable_grouping}")
        print(f"[region_subject_analysis] 地區分組: {region_groups}")
        
        if not all([table_name, year_col, region_col]):
            return ({'error': '缺少必要參數：table_name, year_col, region_col'}), 400
            
        if not subject_cols:
            return ({'error': '必須至少選擇一個科目欄位'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return ({'error': str(e)}), 400

        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()

        # 檢查欄位是否存在並進行動態解析
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        print(f"[region_subject_analysis] 可用欄位: {available_columns}")

        try:
            resolved_year_col = resolve_column_name(
                year_col,
                available_columns,
                label='年度欄位',
                candidates=['年度', '入學年度', '學年度', 'year']
            )
            resolved_region_col = resolve_column_name(
                region_col,
                available_columns,
                label='地區欄位',
                candidates=['地區', '縣市', '城市', 'region', 'city']
            )
        except ValueError as e:
            return ({'error': str(e)}), 400

        valid_subject_pairs = []
        for col in subject_cols:
            try:
                resolved_col = resolve_column_name(col, available_columns, label='科目欄位')
                valid_subject_pairs.append((col, resolved_col))
            except ValueError:
                print(f"[region_subject_analysis] 警告：科目欄位 '{col}' 不存在")
        
        if not valid_subject_pairs:
            return ({'error': '所有科目欄位都不存在'}), 400

        display_subjects = [original for original, _ in valid_subject_pairs]
        resolved_subject_cols = [resolved for _, resolved in valid_subject_pairs]
        
        # 構建查詢
        select_columns = [resolved_year_col, resolved_region_col] + resolved_subject_cols
        columns_str = ', '.join([f'"{col}"' for col in select_columns])
        query_params = {}
        
        # 基本查詢
        query = f'''
        SELECT {columns_str}
        FROM "{table_name}"
        WHERE "{resolved_year_col}" IS NOT NULL 
        AND "{resolved_year_col}" != ""
        AND "{resolved_region_col}" IS NOT NULL
        AND "{resolved_region_col}" != ""
        '''
        
        # 添加年份篩選條件
        if years_filter and len(years_filter) > 0:
            year_placeholders = []
            for idx, year in enumerate(years_filter):
                key = f'year_{idx}'
                year_placeholders.append(f':{key}')
                query_params[key] = str(year)
            query += f' AND "{resolved_year_col}" IN ({", ".join(year_placeholders)})'
        
        # 添加科目欄位非空條件
        subject_conditions = []
        for col in resolved_subject_cols:
            subject_conditions.append(f'"{col}" IS NOT NULL')
        if subject_conditions:
            query += ' AND (' + ' OR '.join(subject_conditions) + ')'
        
        print(f"[region_subject_analysis] 執行查詢: {query}")
        
        # 執行查詢
        with current_engine.connect() as conn:
            result = conn.execute(text(query), query_params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        print(f"[region_subject_analysis] 讀取到 {len(df)} 筆資料")
        
        if df.empty:
            return ({'error': '沒有找到符合條件的資料'}), 400
        
        # 標準化地區名稱：將所有「臺」轉換為「台」
        df[resolved_region_col] = df[resolved_region_col].apply(lambda x: str(x).replace('臺', '台') if pd.notna(x) else x)
        
        # 獲取可用的年份和地區，過濾空值和空字串
        available_years = sorted([year for year in df[resolved_year_col].dropna().unique().tolist() if str(year).strip() != ''])
        available_regions = sorted([region for region in df[resolved_region_col].dropna().unique().tolist() if str(region).strip() != ''])
        
        # 處理地區過濾 - 如果啟用了分組，只包含分組中指定的地區
        final_regions = available_regions
        if enable_grouping and region_groups:
            grouped_regions = set()
            for group in region_groups:
                group_regions = group.get('regions', [])
                if group_regions:
                    grouped_regions.update(group_regions)
            # 只保留在分組中指定的地區
            final_regions = [region for region in available_regions if region in grouped_regions]
        
        print(f"[region_subject_analysis] 最終地區: {final_regions}")
        
        # 分析結果
        result_data = {
            'years': available_years,
            'subjects': display_subjects,
            'regions': final_regions,
            'enable_grouping': enable_grouping,
            'region_details': {}
        }
        
        # 對每個最終地區進行分析
        for region in final_regions:
            region_data = df[df[resolved_region_col] == region].copy()
            yearly_data = []
            
            for year in available_years:
                year_data_filtered = region_data[region_data[resolved_year_col] == year]
                
                if not year_data_filtered.empty:
                    year_result = {'year': year, 'subjects': {}}
                    
                    for original_subject, resolved_subject in valid_subject_pairs:
                        if resolved_subject in year_data_filtered.columns:
                            subject_values = pd.to_numeric(year_data_filtered[resolved_subject], errors='coerce').dropna()
                            if len(subject_values) > 0:
                                avg_score = round(subject_values.mean(), 1)
                                year_result['subjects'][original_subject] = avg_score
                            else:
                                year_result['subjects'][original_subject] = None
                        else:
                            year_result['subjects'][original_subject] = None
                    
                    yearly_data.append(year_result)
                else:
                    # 如果該年度沒有數據，仍要添加空記錄
                    year_result = {'year': year, 'subjects': {}}
                    for original_subject, _ in valid_subject_pairs:
                        year_result['subjects'][original_subject] = None
                    yearly_data.append(year_result)
            
            result_data['region_details'][region] = yearly_data
        
        # 篩選出實際有數據的科目
        final_subjects = []
        for subject in display_subjects:
            has_data = False
            for region_detail in result_data['region_details'].values():
                for year_data in region_detail:
                    if year_data['subjects'].get(subject) is not None:
                        has_data = True
                        break
                if has_data:
                    break
            if has_data:
                final_subjects.append(subject)
        
        result_data['subjects'] = final_subjects
        
        print(f"[region_subject_analysis] 分析完成，涵蓋 {len(final_subjects)} 科目，{len(final_regions)} 個地區")
        
        return (result_data)
    
    except Exception as e:
        print(f"[region_subject_analysis] Error: {str(e)}")
        return ({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if session is not None:
            session.close()

