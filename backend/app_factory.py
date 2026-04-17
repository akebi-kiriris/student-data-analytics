from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table, inspect, text, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
import re
import bcrypt
from datetime import datetime, timedelta, timezone
import tempfile
import uuid
from werkzeug.utils import secure_filename
from blueprints.auth_blueprint import create_auth_blueprint
from blueprints.database_blueprint import create_database_blueprint
from blueprints.analysis_blueprint import create_analysis_blueprint
from blueprints.data_blueprint import create_data_blueprint
from service import database_service, analysis_service, data_service
from service.auth_service import AuthService
from repository.auth_repository import AuthRepository
from repository.database_repository import DatabaseRepository

# 條件性匯入 Google Cloud Storage（僅在雲端環境）
try:
    from google.cloud import storage
    CLOUD_STORAGE_AVAILABLE = True
except ImportError:
    CLOUD_STORAGE_AVAILABLE = False
    storage = None

# 設定資料庫路徑
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXCEL_DATA_DB_PATH = os.path.join(BASE_DIR, 'excel_data.db')
FAKEDATA_DB_PATH = os.path.join(BASE_DIR, 'database', 'fakedata.db')

print(f"✅ 資料庫連線路徑鎖定: EXCEL_DATA={EXCEL_DATA_DB_PATH}, FAKEDATA={FAKEDATA_DB_PATH}")


def get_database_engine(table_name):
    """
    統一的資料庫引擎獲取函數
    優先檢查 excel_data.db，如果不存在則檢查 fakedata.db
    返回 (engine, inspector) 或拋出異常
    """
    from sqlalchemy import create_engine as _create_engine
    
    # 檢查 excel_data.db
    inspector = inspect(engine)
    if inspector.has_table(table_name):
        return engine, inspector
    
    # 檢查 fakedata.db
    fakedata_engine = _create_engine(f'sqlite:///{FAKEDATA_DB_PATH}', echo=False)
    fakedata_inspector = inspect(fakedata_engine)
    if fakedata_inspector.has_table(table_name):
        return fakedata_engine, fakedata_inspector
    
    # 都找不到
    raise ValueError(f'找不到指定的資料表: {table_name}')


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
        ('自然組', [r'^\(自然組\)$', r'自然組']),
        ('社會組', [r'^\(社會組\)$', r'社會組']),
        
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
    
    # 統一將「臺」轉換為「台」，避免兩種寫法造成的匹配問題
    region = region.replace('臺', '台')

    # 地理區域對應表
    region_mapping = {
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
        '台東縣': '東台灣'
    }

    return region_mapping.get(region, '其他')


def normalize_column_name(column_name):
    """將欄位名稱標準化，避免前後端命名格式差異。"""
    if column_name is None:
        return ''
    return str(column_name).strip().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')


def build_column_lookup(available_columns):
    """建立欄位名稱查詢索引（原名 + 標準化 + 小寫）。"""
    lookup = {}
    for col in available_columns:
        normalized = normalize_column_name(col)
        lookup[str(col)] = col
        lookup[normalized] = col
        lookup[normalized.lower()] = col
    return lookup


def resolve_column_name(requested_name, available_columns, label='欄位', candidates=None, required=True):
    """解析請求欄位名稱，支援標準化比對與候選欄位自動偵測。"""
    lookup = build_column_lookup(available_columns)

    if requested_name:
        request_key = normalize_column_name(requested_name)
        resolved = (
            lookup.get(str(requested_name))
            or lookup.get(request_key)
            or lookup.get(request_key.lower())
        )
        if resolved:
            return resolved
        if required:
            raise ValueError(f'{label} {requested_name} 不存在')

    if candidates:
        for candidate in candidates:
            candidate_key = normalize_column_name(candidate)
            resolved = (
                lookup.get(str(candidate))
                or lookup.get(candidate_key)
                or lookup.get(candidate_key.lower())
            )
            if resolved:
                return resolved

    if required:
        raise ValueError(f'找不到可用的{label}，可用欄位：{available_columns}')

    return None


def auto_detect_subject_columns(available_columns, excluded_columns=None):
    """自動偵測可能是成績科目的欄位。"""
    excluded_columns = excluded_columns or []
    excluded_keys = {normalize_column_name(col).lower() for col in excluded_columns if col}

    auto_subjects = []
    for col in available_columns:
        normalized = normalize_column_name(col).lower()

        if normalized in {'id', 'user_id'}:
            continue
        if normalized in excluded_keys:
            continue

        # 排除常見維度欄位，保留可能是分數的欄位
        if any(keyword in normalized for keyword in ['年度', 'year', '性別', 'gender', 'school', '高中', '地區', 'region', '管道', 'method']):
            continue

        auto_subjects.append(col)

    return auto_subjects


ALLOWED_EXCEL_EXTENSIONS = {'.xlsx', '.xls'}


def validate_excel_file(file):
    """驗證上傳檔案格式並回傳安全檔名資訊。"""
    original_filename = (file.filename or '').strip()
    safe_filename = secure_filename(original_filename)

    if not original_filename:
        raise ValueError('No selected file')
    if not safe_filename:
        raise ValueError('檔名無效，請重新命名後上傳')

    file_extension = os.path.splitext(safe_filename)[1].lower()
    if file_extension not in ALLOWED_EXCEL_EXTENSIONS:
        raise ValueError('僅支援 .xlsx 或 .xls 檔案')

    return original_filename, safe_filename, file_extension


app = Flask(__name__)
CORS(app, 
     supports_credentials=True, 
     allow_headers=['Content-Type', 'Authorization'],
     origins=[
         'https://student-analytics-prod.web.app',
         'https://student-analytics-prod.firebaseapp.com',
         'http://localhost:5173',  # Vite 開發伺服器
         'http://localhost:3000',  # 其他可能的開發環境
         'http://127.0.0.1:5173'   # 本地測試
     ])  # 明確允許的來源

# JWT 配置
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    jwt_secret = uuid.uuid4().hex
    print('[WARNING] 未設定 JWT_SECRET_KEY，已使用暫時隨機密鑰（重啟後 Token 會失效）')
app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Token 24小時過期
app.config['JWT_ALGORITHM'] = 'HS256'

# 初始化 JWT
jwt = JWTManager(app)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 限制 100MB

# Google Cloud Storage 配置（僅在雲端環境）
def is_cloud_environment():
    """檢測是否為雲端環境"""
    return os.getenv('GOOGLE_CLOUD_PROJECT') is not None and CLOUD_STORAGE_AVAILABLE

IS_PRODUCTION = is_cloud_environment()

# 初始化 Cloud Storage（僅在雲端環境）
storage_client = None
bucket = None
if is_cloud_environment():
    try:
        storage_client = storage.Client()
        BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'student-analytics-files')
        bucket = storage_client.bucket(BUCKET_NAME)
        print("[INFO] 雲端環境：已啟用 Cloud Storage")
    except Exception as e:
        print(f"[WARNING] Cloud Storage 初始化失敗: {e}")
        storage_client = None
        bucket = None
else:
    if not CLOUD_STORAGE_AVAILABLE:
        print("[INFO] 本地環境：google-cloud-storage 未安裝，使用本地檔案儲存")
    else:
        print("[INFO] 本地環境：使用本地檔案儲存")
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['DATABASE_FOLDER'] = os.path.join(BASE_DIR, 'database')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

# === 資料庫配置 ===
def get_database_url():
    """使用 SQLite 資料庫"""
    print("[INFO] 使用本地 SQLite 資料庫")
    db_path = os.path.join(app.config['DATABASE_FOLDER'], 'excel_data.db')
    return f'sqlite:///{db_path}'

# 從 Cloud Storage 下載資料庫（如果存在）
def download_database_from_gcs():
    """啟動時從 Cloud Storage 下載資料庫"""
    if not IS_PRODUCTION or not CLOUD_STORAGE_AVAILABLE or storage_client is None:
        print("[INFO] 跳過資料庫下載（本地環境或 Storage 不可用）")
        return
    
    try:
        db_bucket_name = os.getenv('GCS_DB_BUCKET', 'student-analytics-db-backup')
        db_bucket = storage_client.bucket(db_bucket_name)
        
        # 下載 excel_data.db
        blob = db_bucket.blob('excel_data.db')
        if blob.exists():
            db_path = os.path.join(app.config['DATABASE_FOLDER'], 'excel_data.db')
            blob.download_to_filename(db_path)
            print(f"[INFO] ✓ 從 gs://{db_bucket_name}/excel_data.db 下載資料庫成功")
        else:
            print(f"[INFO] Cloud Storage 中無 excel_data.db，將建立新資料庫")
        
        # 下載 fakedata.db
        fake_blob = db_bucket.blob('fakedata.db')
        if fake_blob.exists():
            fake_db_path = os.path.join(app.config['DATABASE_FOLDER'], 'fakedata.db')
            fake_blob.download_to_filename(fake_db_path)
            print(f"[INFO] ✓ 從 gs://{db_bucket_name}/fakedata.db 下載假資料庫成功")
        else:
            print(f"[INFO] Cloud Storage 中無 fakedata.db，將使用本地假資料庫")
    except Exception as e:
        print(f"[WARNING] 資料庫下載失敗: {e}，將使用空資料庫")

# 上傳資料庫到 Cloud Storage
def backup_database_to_gcs():
    """備份資料庫到 Cloud Storage"""
    if not IS_PRODUCTION or not CLOUD_STORAGE_AVAILABLE or storage_client is None:
        return {"success": False, "message": "非生產環境或 Storage 不可用"}
    
    try:
        db_bucket_name = os.getenv('GCS_DB_BUCKET', 'student-analytics-db-backup')
        db_bucket = storage_client.bucket(db_bucket_name)
        
        # 備份 excel_data.db
        db_path = os.path.join(app.config['DATABASE_FOLDER'], 'excel_data.db')
        if os.path.exists(db_path):
            blob = db_bucket.blob('excel_data.db')
            blob.upload_from_filename(db_path)
            print(f"[INFO] ✓ 資料庫已備份到 gs://{db_bucket_name}/excel_data.db")
        else:
            print(f"[WARNING] excel_data.db 不存在，跳過備份")
        
        # 備份 fakedata.db
        fake_db_path = os.path.join(app.config['DATABASE_FOLDER'], 'fakedata.db')
        if os.path.exists(fake_db_path):
            fake_blob = db_bucket.blob('fakedata.db')
            fake_blob.upload_from_filename(fake_db_path)
            print(f"[INFO] ✓ 假資料庫已備份到 gs://{db_bucket_name}/fakedata.db")
        else:
            print(f"[WARNING] fakedata.db 不存在，跳過備份")
        
        return {"success": True, "message": "備份成功"}
    except Exception as e:
        print(f"[ERROR] 資料庫備份失敗: {e}")
        return {"success": False, "message": str(e)}

DATABASE_URL = get_database_url()
DATABASE_PATH = os.path.join(app.config['DATABASE_FOLDER'], 'excel_data.db')  # SQLite 路徑（本地用）

# 啟動時下載資料庫
download_database_from_gcs()

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
    
    # 清理 SQLAlchemy metadata 快取
    if table_name in metadata.tables:
        metadata.remove(metadata.tables[table_name])
    
    # 若表格已存在則先刪除
    if inspector.has_table(table_name):
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.commit()
    
    # 建立新表（添加 user_id 欄位用於多租戶隔離）
    cols = [
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', String(50), nullable=False, index=True)  # 多租戶欄位
    ]
    for col in columns:
        # SQLite 相容的欄位名稱處理
        safe_col_name = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        cols.append(Column(safe_col_name, String))
    
    # 使用 extend_existing=True 避免重複定義錯誤
    table = Table(table_name, metadata, *cols, extend_existing=True)
    metadata.create_all(engine)
    return table

# === 使用者認證相關的資料表定義 ===
users_table = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('username', String(50), unique=True, nullable=False),
    Column('email', String(100), unique=True, nullable=False),
    Column('password_hash', String(255), nullable=False),
    Column('full_name', String(100)),
    Column('role', String(20), default='user'),  # 'admin', 'user', 'viewer'
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('last_login', DateTime)
)

# === 檔案上傳記錄表格 ===
uploaded_files_table = Table(
    'uploaded_files', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('file_id', String(50), unique=True, nullable=False),
    Column('user_id', String(50), nullable=False),
    Column('original_filename', String(255), nullable=False),
    Column('blob_name', String(500), nullable=False),  # Cloud Storage blob 路徑
    Column('upload_time', DateTime, default=datetime.utcnow),
    Column('sheet_name', String(100)),
    Column('table_name', String(100))
)

# 建立所有表格（延遲初始化，避免啟動時連接失敗）
def init_database():
    """初始化資料庫，只在第一次請求時執行"""
    try:
        metadata.create_all(engine)
        return True
    except Exception as e:
        print(f"[WARNING] 資料庫初始化失敗: {e}")
        return False

# 使用 Flask 的 before_first_request 確保資料庫已初始化
_db_initialized = False

@app.before_request
def ensure_database_initialized():
    global _db_initialized
    if not _db_initialized:
        init_database()
        create_default_admin()
        _db_initialized = True

Session = sessionmaker(bind=engine)

# === 輔助函數 ===
def hash_password(password):
    """密碼雜湊"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """驗證密碼"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def create_default_admin():
    """依環境變數建立預設管理員帳號。"""
    default_admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
    if not default_admin_password:
        print('[INFO] 未設定 DEFAULT_ADMIN_PASSWORD，跳過建立預設管理員帳號')
        return

    default_admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin').strip() or 'admin'
    default_admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@system.local').strip() or 'admin@system.local'
    default_admin_full_name = os.getenv('DEFAULT_ADMIN_FULL_NAME', '系統管理員').strip() or '系統管理員'

    session = Session()
    try:
        # 檢查是否已存在 admin 用戶
        admin_exists = session.execute(
            text("SELECT COUNT(*) FROM users WHERE username = :username"),
            {'username': default_admin_username}
        ).scalar()
        
        if admin_exists == 0:
            # 建立預設 admin 帳號
            password_hash = hash_password(default_admin_password)
            session.execute(
                text("""
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (:username, :email, :password_hash, :full_name, :role, :is_active)
                """),
                {
                    'username': default_admin_username,
                    'email': default_admin_email,
                    'password_hash': password_hash,
                    'full_name': default_admin_full_name,
                    'role': 'admin',
                    'is_active': True
                }
            )
            session.commit()
            print(f"預設管理員帳號已建立: {default_admin_username}")
        
    except Exception as e:
        session.rollback()
        print(f"建立預設管理員失敗: {e}")
    finally:
        session.close()

# === JWT 錯誤處理 ===
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"[DEBUG] Token過期: {jwt_payload}")
    return jsonify({'error': 'Token 已過期', 'code': 'token_expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"[DEBUG] Token無效: {error}")
    return jsonify({'error': 'Token 無效', 'code': 'invalid_token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"[DEBUG] 缺少Token: {error}")
    return jsonify({'error': '需要登入', 'code': 'authorization_required'}), 401

# === 認證相關 API（Blueprint + Service + Repository） ===
auth_repository = AuthRepository(Session)
auth_service = AuthService(
    repository=auth_repository,
    hash_password_fn=hash_password,
    check_password_fn=check_password,
    token_factory=create_access_token,
)
app.register_blueprint(create_auth_blueprint(auth_service))

database_repository = DatabaseRepository()
database_service.configure_database_service(
    app_instance=app,
    engine_instance=engine,
    fakedata_db_path=FAKEDATA_DB_PATH,
    database_folder=app.config['DATABASE_FOLDER'],
    get_database_engine_fn=get_database_engine,
    repository=database_repository,
)
analysis_service.configure_analysis_service(
    get_database_engine_fn=get_database_engine,
    resolve_column_name_fn=resolve_column_name,
    auto_detect_subject_columns_fn=auto_detect_subject_columns,
    classify_school_type_fn=classify_school_type,
    classify_admission_method_fn=classify_admission_method,
    classify_region_fn=classify_region,
)

app.register_blueprint(create_database_blueprint())
app.register_blueprint(create_analysis_blueprint())
data_service.configure_data_service(
    upload_folder_path=app.config['UPLOAD_FOLDER'],
    database_path_value=DATABASE_PATH,
    bucket_instance=bucket,
    session_factory=Session,
    engine_instance=engine,
    metadata_instance=metadata,
    backup_database_to_gcs_fn=backup_database_to_gcs,
    get_database_engine_fn=get_database_engine,
    filter_dataframe_until_empty_row_fn=filter_dataframe_until_empty_row,
    validate_excel_file_fn=validate_excel_file,
    create_excel_table_fn=create_excel_table,
    is_cloud_environment_fn=is_cloud_environment,
)
app.register_blueprint(create_data_blueprint())


def create_app():
    return app
