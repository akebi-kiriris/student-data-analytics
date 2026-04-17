import os

from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

engine = None
FAKEDATA_DB_PATH = None
DATABASE_FOLDER = None
get_database_engine = None
database_repository = None


def configure_database_service(app_instance, engine_instance, fakedata_db_path, database_folder, get_database_engine_fn, repository=None):
    del app_instance
    global engine, FAKEDATA_DB_PATH, DATABASE_FOLDER, get_database_engine, database_repository
    engine = engine_instance
    FAKEDATA_DB_PATH = fakedata_db_path
    DATABASE_FOLDER = database_folder
    get_database_engine = get_database_engine_fn
    database_repository = repository


def list_database_tables_new(current_user_id):
    try:
        try:
            db_files = os.listdir(DATABASE_FOLDER)
            print(f"[DEBUG] database/ 目錄內容: {db_files}")
            print(f"[DEBUG] fakedata.db 存在: {os.path.exists(os.path.join(DATABASE_FOLDER, 'fakedata.db'))}")
        except Exception as e:
            print(f"[DEBUG] 無法列出 database/ 目錄: {e}")

        print(f"[DEBUG] JWT驗證成功，用戶ID: {current_user_id} (type: {type(current_user_id)})")

        if database_repository:
            tables = database_repository.list_main_table_names(engine)
        else:
            tables = inspect(engine).get_table_names()

        user_prefix = f"{current_user_id}_"
        user_tables = [table for table in tables if table.startswith(user_prefix)]

        table_info = []
        for table in user_tables:
            try:
                parts = table.replace(user_prefix, '', 1).rsplit('_', 1)
                if len(parts) == 2:
                    sheet_name, timestamp = parts
                    table_info.append({
                        'table_name': table,
                        'display_name': f"{sheet_name}",
                        'sheet_name': sheet_name,
                        'timestamp': timestamp,
                    })
            except Exception:
                table_info.append({
                    'table_name': table,
                    'display_name': table,
                    'filename': '',
                    'sheet_name': '',
                })

        try:
            if database_repository:
                fakedata_tables = database_repository.list_fakedata_table_names(FAKEDATA_DB_PATH)
            else:
                from sqlalchemy import create_engine as _create_engine
                fakedata_engine = _create_engine(f'sqlite:///{FAKEDATA_DB_PATH}', echo=False)
                fakedata_tables = inspect(fakedata_engine).get_table_names()

            for table in fakedata_tables:
                if not any(t['table_name'] == table for t in table_info):
                    table_info.append({
                        'table_name': table,
                        'display_name': table,
                        'sheet_name': table,
                        'timestamp': '',
                    })
        except Exception as e:
            print(f"[WARNING] inspect fakedata.db failed: {e}")

        return {'success': True, 'tables': table_info}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def get_table_columns(table_name):
    try:
        if not table_name:
            return {'error': '缺少table_name參數'}, 400

        try:
            _, current_inspector = get_database_engine(table_name)
            if database_repository:
                columns = database_repository.get_columns(current_inspector, table_name, exclude=['id'])
            else:
                columns_info = current_inspector.get_columns(table_name)
                columns = [col['name'] for col in columns_info if col['name'] != 'id']
            return {'columns': columns}, 200
        except ValueError as e:
            return {'error': str(e)}, 404

    except Exception as e:
        return {'error': str(e)}, 500


def get_table_row_count(table_name):
    try:
        try:
            current_engine, _ = get_database_engine(table_name)
        except ValueError as e:
            return {'success': False, 'error': str(e)}, 404

        with current_engine.connect() as connection:
            result = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
            count = result.scalar()

        return {'success': True, 'count': count}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def get_table_data(table_name, current_user_id, page=1, limit=50, search=''):
    try:
        try:
            current_engine, current_inspector = get_database_engine(table_name)
            current_db_path = os.path.abspath(str(current_engine.url.database or ''))
            is_fakedata = (current_db_path == os.path.abspath(FAKEDATA_DB_PATH))
        except ValueError as e:
            return {'success': False, 'error': str(e)}, 404

        offset = (page - 1) * limit

        if database_repository:
            columns = database_repository.get_columns(current_inspector, table_name, exclude=['id'])
        else:
            columns_info = current_inspector.get_columns(table_name)
            columns = [col['name'] for col in columns_info if col['name'] != 'id']

        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            if is_fakedata:
                if search:
                    search_conditions = [f'`{col}` LIKE :search' for col in columns]
                    search_query = f"SELECT * FROM `{table_name}` WHERE ({' OR '.join(search_conditions)}) ORDER BY id LIMIT :limit OFFSET :offset"
                    count_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE ({' OR '.join(search_conditions)})"
                    result = session.execute(text(search_query), {'search': f'%{search}%', 'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(count_query), {'search': f'%{search}%'}).scalar()
                else:
                    result = session.execute(text(f"SELECT * FROM `{table_name}` ORDER BY id LIMIT :limit OFFSET :offset"), {'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()
            else:
                if search:
                    search_conditions = [f'`{col}` LIKE :search' for col in columns]
                    search_query = f"SELECT * FROM `{table_name}` WHERE user_id = :user_id AND ({' OR '.join(search_conditions)}) ORDER BY id LIMIT :limit OFFSET :offset"
                    count_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE user_id = :user_id AND ({' OR '.join(search_conditions)})"
                    result = session.execute(text(search_query), {'user_id': current_user_id, 'search': f'%{search}%', 'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(count_query), {'user_id': current_user_id, 'search': f'%{search}%'}).scalar()
                else:
                    result = session.execute(text(f"SELECT * FROM `{table_name}` WHERE user_id = :user_id ORDER BY id LIMIT :limit OFFSET :offset"), {'user_id': current_user_id, 'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(f"SELECT COUNT(*) FROM `{table_name}` WHERE user_id = :user_id"), {'user_id': current_user_id}).scalar()

            rows = [dict(zip(['id'] + columns, row)) for row in result]
            total_pages = (total + limit - 1) // limit

            return {
                'success': True,
                'data': rows,
                'columns': ['id'] + columns,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total,
                    'limit': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1,
                },
            }, 200
        finally:
            session.close()
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def create_table_row(table_name, current_user_id, payload):
    try:
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return {'success': False, 'error': str(e)}, 404

        data = payload or {}
        if not data:
            return {'success': False, 'error': '缺少資料內容'}, 400

        if database_repository:
            columns = database_repository.get_columns(current_inspector, table_name, exclude=['id'])
        else:
            columns_info = current_inspector.get_columns(table_name)
            columns = [col['name'] for col in columns_info if col['name'] != 'id']

        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            placeholders = ', '.join([f':{col}' for col in columns])
            columns_str = ', '.join([f'`{col}`' for col in columns])
            insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"

            insert_data = {}
            for col in columns:
                insert_data[col] = current_user_id if col == 'user_id' else data.get(col, '')

            result = session.execute(text(insert_query), insert_data)
            session.commit()
            return {'success': True, 'message': '資料新增成功', 'inserted_id': result.lastrowid}, 200
        finally:
            session.close()
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def update_table_row(table_name, row_id, current_user_id, payload):
    try:
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return {'success': False, 'error': str(e)}, 404

        data = payload or {}
        if not data:
            return {'success': False, 'error': '缺少資料內容'}, 400

        if database_repository:
            columns = database_repository.get_columns(current_inspector, table_name, exclude=['id', 'user_id'])
        else:
            columns_info = current_inspector.get_columns(table_name)
            columns = [col['name'] for col in columns_info if col['name'] not in ['id', 'user_id']]

        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            check_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE id = :row_id AND user_id = :user_id"
            exists = session.execute(text(check_query), {'row_id': row_id, 'user_id': current_user_id}).scalar()
            if not exists:
                return {'success': False, 'error': '找不到指定的資料或無權限修改'}, 404

            set_clauses = [f'`{col}` = :{col}' for col in columns if col in data]
            if not set_clauses:
                return {'success': False, 'error': '沒有可更新的欄位'}, 400

            update_query = f"UPDATE `{table_name}` SET {', '.join(set_clauses)} WHERE id = :row_id"
            update_data = {'row_id': row_id}
            for col in columns:
                if col in data:
                    update_data[col] = data[col]

            session.execute(text(update_query), update_data)
            session.commit()
            return {'success': True, 'message': '資料更新成功'}, 200
        finally:
            session.close()
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


def delete_table_row(table_name, row_id, current_user_id):
    try:
        try:
            current_engine, _ = get_database_engine(table_name)
        except ValueError as e:
            return {'success': False, 'error': str(e)}, 404

        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            check_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE id = :row_id AND user_id = :user_id"
            exists = session.execute(text(check_query), {'row_id': row_id, 'user_id': current_user_id}).scalar()
            if not exists:
                return {'success': False, 'error': '找不到指定的資料或無權限刪除'}, 404

            delete_query = f"DELETE FROM `{table_name}` WHERE id = :row_id AND user_id = :user_id"
            session.execute(text(delete_query), {'row_id': row_id, 'user_id': current_user_id})
            session.commit()
            return {'success': True, 'message': '資料刪除成功'}, 200
        finally:
            session.close()
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500