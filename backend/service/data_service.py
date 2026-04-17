import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import Table, inspect, text
from werkzeug.utils import secure_filename

upload_folder = None
database_path = None
bucket = None
Session = None
engine = None
metadata = None
backup_database_to_gcs = None
get_database_engine = None
filter_dataframe_until_empty_row = None
validate_excel_file = None
create_excel_table = None
is_cloud_environment = None


def configure_data_service(
    upload_folder_path,
    database_path_value,
    bucket_instance,
    session_factory,
    engine_instance,
    metadata_instance,
    backup_database_to_gcs_fn,
    get_database_engine_fn,
    filter_dataframe_until_empty_row_fn,
    validate_excel_file_fn,
    create_excel_table_fn,
    is_cloud_environment_fn,
):
    global upload_folder, database_path, bucket, Session, engine, metadata
    global backup_database_to_gcs, get_database_engine, filter_dataframe_until_empty_row
    global validate_excel_file, create_excel_table, is_cloud_environment

    upload_folder = upload_folder_path
    database_path = database_path_value
    bucket = bucket_instance
    Session = session_factory
    engine = engine_instance
    metadata = metadata_instance
    backup_database_to_gcs = backup_database_to_gcs_fn
    get_database_engine = get_database_engine_fn
    filter_dataframe_until_empty_row = filter_dataframe_until_empty_row_fn
    validate_excel_file = validate_excel_file_fn
    create_excel_table = create_excel_table_fn
    is_cloud_environment = is_cloud_environment_fn


def upload_file(file, sheet_name, current_user_id):
    if file is None:
        return {"error": "No file part"}, 400

    try:
        original_filename, safe_filename, _ = validate_excel_file(file)

        if is_cloud_environment() and bucket is not None:
            return upload_to_cloud_storage(file, sheet_name, original_filename, safe_filename, current_user_id)
        return upload_to_local_storage(file, sheet_name, original_filename, safe_filename, current_user_id)
    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 500


def upload_to_cloud_storage(file, sheet_name, original_filename, safe_filename, current_user_id):
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(safe_filename)[1].lower()
    blob_name = f"uploads/{current_user_id}/{file_id}{file_extension}"

    blob = bucket.blob(blob_name)
    file.seek(0)
    blob.upload_from_file(file, content_type=file.content_type)

    if not sheet_name:
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            blob.download_to_filename(temp_file.name)
            xl = pd.ExcelFile(temp_file.name)
            sheets = xl.sheet_names
        os.unlink(temp_file.name)

        return {
            "filename": safe_filename,
            "original_filename": original_filename,
            "file_id": file_id,
            "blob_name": blob_name,
            "sheets": sheets,
            "need_sheet_selection": True,
        }, 200

    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
        blob.download_to_filename(temp_file.name)
        df = pd.read_excel(temp_file.name, sheet_name=sheet_name)
    os.unlink(temp_file.name)

    return process_excel_data(
        file=file,
        df=df,
        sheet_name=sheet_name,
        current_user_id=current_user_id,
        file_id=file_id,
        blob_name=blob_name,
        stored_filename=safe_filename,
    )


def upload_to_local_storage(file, sheet_name, original_filename, safe_filename, current_user_id):
    filepath = os.path.join(upload_folder, safe_filename)
    file.save(filepath)

    if not sheet_name:
        xl = pd.ExcelFile(filepath)
        return {
            "filename": safe_filename,
            "original_filename": original_filename,
            "sheets": xl.sheet_names,
            "need_sheet_selection": True,
        }, 200

    df = pd.read_excel(filepath, sheet_name=sheet_name)
    return process_excel_data(
        file=file,
        df=df,
        sheet_name=sheet_name,
        current_user_id=current_user_id,
        stored_filename=safe_filename,
    )


def process_excel_data(file, df, sheet_name, current_user_id, file_id=None, blob_name=None, stored_filename=None):
    df = filter_dataframe_until_empty_row(df)
    if df.empty:
        return {"error": "工作表中沒有有效資料"}, 400

    columns = df.columns.tolist()
    safe_sheet_name = sheet_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')
    table_name = f"{current_user_id}_{safe_sheet_name}_{timestamp}"

    table = create_excel_table(table_name, columns)
    session = Session()

    try:
        data_dicts = []
        for _, row in df.iterrows():
            row_dict = {'user_id': current_user_id}
            for i, col in enumerate(columns):
                safe_col_name = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                row_dict[safe_col_name] = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ''
            data_dicts.append(row_dict)

        session.execute(table.insert(), data_dicts)
        session.commit()

        if file_id and blob_name:
            current_time = datetime.utcnow()
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO uploaded_files (file_id, user_id, original_filename, blob_name, upload_time, sheet_name, table_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (file_id, current_user_id, file.filename, blob_name, current_time.isoformat(), sheet_name, table_name),
                )
                conn.commit()

        response_data = {
            "success": True,
            "filename": stored_filename or file.filename,
            "sheet_name": sheet_name,
            "table_name": table_name,
            "columns": columns,
            "rows_inserted": len(data_dicts),
        }

        if file_id:
            response_data["file_id"] = file_id

        backup_database_to_gcs()
        return response_data, 200
    except Exception as e:
        session.rollback()
        return {"error": str(e)}, 500
    finally:
        session.close()


def list_excel_sheets(filename):
    if not filename:
        return {'error': '缺少 filename'}, 400

    safe_filename = secure_filename(str(filename))
    if not safe_filename:
        return {'error': '檔名格式無效'}, 400

    filepath = os.path.join(upload_folder, safe_filename)
    if not os.path.exists(filepath):
        return {'error': '找不到檔案'}, 404

    try:
        xl = pd.ExcelFile(filepath)
        return {'sheets': xl.sheet_names}, 200
    except Exception as e:
        return {'error': str(e)}, 500


def read_columns_from_file(filename, sheet=None):
    if not filename:
        return {'error': '缺少 filename'}, 400

    safe_filename = secure_filename(str(filename))
    if not safe_filename:
        return {'error': '檔名格式無效'}, 400

    filepath = os.path.join(upload_folder, safe_filename)
    if not os.path.exists(filepath):
        return {'error': '找不到檔案'}, 404

    try:
        df = pd.read_excel(filepath, sheet_name=sheet) if sheet else pd.read_excel(filepath)
        return {'columns': df.columns.tolist()}, 200
    except Exception as e:
        print(f"[read_columns_from_file] {e}")
        return {'error': str(e)}, 500


def get_excel_data_post(filename):
    try:
        if not filename:
            return {'error': '缺少 filename'}, 400

        safe_filename = secure_filename(str(filename))
        if not safe_filename:
            return {'error': '檔名格式無效'}, 400

        base_name = os.path.splitext(safe_filename)[0]
        safe_table_name = f"excel_data_{base_name.replace('-', '_').replace(' ', '_')}"

        inspector = inspect(engine)
        if not inspector.has_table(safe_table_name):
            return {'error': '尚未上傳該檔案的資料'}, 400

        table = Table(safe_table_name, metadata, autoload_with=engine)
        session = Session()
        result = session.execute(table.select()).fetchall()
        session.close()

        columns = table.columns.keys()
        rows = [dict(zip(columns, row)) for row in result]
        return {'columns': columns, 'data': rows}, 200
    except Exception as e:
        return {'error': str(e)}, 500


def get_excel_data_get(filename, sheet=None):
    try:
        if not filename:
            return {'error': '缺少 filename'}, 400

        safe_filename = secure_filename(str(filename))
        if not safe_filename:
            return {'error': '檔名格式無效'}, 400

        filepath = os.path.join(upload_folder, safe_filename)
        if not os.path.exists(filepath):
            return {'error': '找不到檔案'}, 404

        base_name = os.path.splitext(safe_filename)[0]
        safe_table_name = f"excel_data_{base_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')}"

        try:
            current_engine, _ = get_database_engine(safe_table_name)
            table = Table(safe_table_name, metadata, autoload_with=current_engine)
            session = Session()
            result = session.execute(table.select()).fetchall()
            session.close()

            columns = [col.name for col in table.columns if col.name != 'id']
            rows = [dict(zip(columns, row[1:])) for row in result]
            return {'columns': columns, 'data': rows}, 200
        except ValueError:
            df = pd.read_excel(filepath, sheet_name=sheet) if sheet else pd.read_excel(filepath)
            df = filter_dataframe_until_empty_row(df)
            return {'columns': df.columns.tolist(), 'data': df.to_dict(orient='records')}, 200
    except Exception as e:
        print(f"[get_excel_data_get] {e}")
        return {'error': str(e)}, 500


def list_user_files(user_id):
    try:
        inspector = inspect(engine)
        if not inspector.has_table('uploaded_files'):
            return {'success': True, 'files': []}, 200

        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT file_id, original_filename, upload_time, sheet_name, table_name
                FROM uploaded_files
                WHERE user_id = ?
                ORDER BY upload_time DESC
                """,
                (user_id,),
            )

            files = []
            for row in cursor.fetchall():
                files.append({
                    'file_id': row[0],
                    'filename': row[1],
                    'upload_time': row[2],
                    'sheet_name': row[3],
                    'table_name': row[4],
                })

        return {'success': True, 'files': files}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def download_file(file_id, user_id):
    try:
        inspector = inspect(engine)
        if not inspector.has_table('uploaded_files'):
            return {'success': False, 'error': '無檔案記錄'}, 404

        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT original_filename, blob_name
                FROM uploaded_files
                WHERE file_id = ? AND user_id = ?
                """,
                (file_id, user_id),
            )
            result = cursor.fetchone()

        if not result:
            return {'success': False, 'error': '檔案不存在或無權限'}, 404

        original_filename, blob_name = result

        if is_cloud_environment() and bucket is not None:
            blob = bucket.blob(blob_name)
            url = blob.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="GET")
            return {'success': True, 'download_url': url, 'filename': original_filename}, 200

        local_path = os.path.join(upload_folder, original_filename)
        if os.path.exists(local_path):
            return {
                'action': 'send_file',
                'directory': upload_folder,
                'filename': original_filename,
            }, 200
        return {'success': False, 'error': '檔案不存在'}, 404
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def delete_file(file_id, user_id):
    try:
        inspector = inspect(engine)
        if not inspector.has_table('uploaded_files'):
            return {'success': False, 'error': '無檔案記錄'}, 404

        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT original_filename, blob_name, table_name
                FROM uploaded_files
                WHERE file_id = ? AND user_id = ?
                """,
                (file_id, user_id),
            )
            result = cursor.fetchone()

            if not result:
                return {'success': False, 'error': '檔案不存在或無權限'}, 404

            original_filename, blob_name, table_name = result

            if is_cloud_environment() and bucket is not None and blob_name:
                try:
                    blob = bucket.blob(blob_name)
                    blob.delete()
                except Exception as e:
                    print(f"[WARNING] Cloud Storage 檔案刪除失敗: {e}")

            if not is_cloud_environment():
                local_path = os.path.join(upload_folder, original_filename)
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except Exception as e:
                        print(f"[WARNING] 本地檔案刪除失敗: {e}")

            cursor.execute("DELETE FROM uploaded_files WHERE file_id = ? AND user_id = ?", (file_id, user_id))
            conn.commit()

        if table_name:
            try:
                session = Session()
                session.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                session.commit()
                session.close()
            except Exception as e:
                print(f"[WARNING] 資料表刪除失敗: {e}")

        backup_database_to_gcs()
        return {'success': True, 'message': '檔案已刪除'}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def manual_backup():
    try:
        result = backup_database_to_gcs()
        return result, 200 if result.get('success') else 500
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500
