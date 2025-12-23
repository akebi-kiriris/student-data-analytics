from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
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
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here-change-in-production'  # 使用固定密鑰
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
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE_FOLDER'] = 'database'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

# === 資料庫配置 ===
def get_database_url():
    """使用 SQLite 資料庫"""
    print("[INFO] 使用本地 SQLite 資料庫")
    db_path = os.path.join(BASE_DIR, app.config['DATABASE_FOLDER'], 'excel_data.db')
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
    """建立預設管理員帳號"""
    session = Session()
    try:
        # 檢查是否已存在 admin 用戶
        admin_exists = session.execute(
            text("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        ).scalar()
        
        if admin_exists == 0:
            # 建立預設 admin 帳號
            password_hash = hash_password('admin123')
            session.execute(
                text("""
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (:username, :email, :password_hash, :full_name, :role, :is_active)
                """),
                {
                    'username': 'admin',
                    'email': 'admin@system.local',
                    'password_hash': password_hash,
                    'full_name': '系統管理員',
                    'role': 'admin',
                    'is_active': True
                }
            )
            session.commit()
            print("預設管理員帳號已建立: admin / admin123")
        
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

# === 認證相關 API ===
@app.route('/api/auth/register', methods=['POST'])
def register():
    """使用者註冊"""
    try:
        data = request.get_json()
        
        # 驗證必要欄位
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必要欄位: {field}'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']
        full_name = data.get('full_name', '').strip()
        
        # 基本驗證
        if len(username) < 3:
            return jsonify({'error': '使用者名稱至少需要3個字元'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '密碼至少需要6個字元'}), 400
        
        session = Session()
        try:
            # 檢查使用者名稱是否已存在
            existing_user = session.execute(
                text("SELECT COUNT(*) FROM users WHERE username = :username OR email = :email"),
                {'username': username, 'email': email}
            ).scalar()
            
            if existing_user > 0:
                return jsonify({'error': '使用者名稱或 Email 已存在'}), 400
            
            # 建立新使用者
            password_hash = hash_password(password)
            session.execute(
                text("""
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (:username, :email, :password_hash, :full_name, :role, :is_active)
                """),
                {
                    'username': username,
                    'email': email,
                    'password_hash': password_hash,
                    'full_name': full_name,
                    'role': 'user',  # 新註冊用戶預設為 user
                    'is_active': True
                }
            )
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '註冊成功',
                'user': {
                    'username': username,
                    'email': email,
                    'full_name': full_name,
                    'role': 'user'
                }
            }), 201
            
        except Exception as e:
            session.rollback()
            return jsonify({'error': f'註冊失敗: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'請求處理失敗: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """使用者登入"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': '請輸入使用者名稱和密碼'}), 400
        
        session = Session()
        try:
            # 查詢使用者
            user_data = session.execute(
                text("""
                SELECT id, username, email, password_hash, full_name, role, is_active
                FROM users 
                WHERE username = :username AND is_active = 1
                """),
                {'username': username}
            ).fetchone()
            
            if not user_data:
                return jsonify({'error': '使用者名稱或密碼錯誤'}), 401
            
            # 驗證密碼
            if not check_password(password, user_data.password_hash):
                return jsonify({'error': '使用者名稱或密碼錯誤'}), 401
            
            # 更新最後登入時間
            session.execute(
                text("UPDATE users SET last_login = :now WHERE id = :user_id"),
                {'now': datetime.now(timezone.utc), 'user_id': user_data.id}
            )
            session.commit()
            
            # 建立 JWT token
            access_token = create_access_token(
                identity=str(user_data.id),  # 轉換為字符串
                additional_claims={
                    'username': user_data.username,
                    'role': user_data.role
                }
            )
            
            return jsonify({
                'success': True,
                'message': '登入成功',
                'access_token': access_token,
                'user': {
                    'id': user_data.id,
                    'username': user_data.username,
                    'email': user_data.email,
                    'full_name': user_data.full_name,
                    'role': user_data.role
                }
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'登入失敗: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """獲取當前用戶資料"""
    try:
        user_id = int(get_jwt_identity())  # 轉換回整數
        
        session = Session()
        try:
            user_data = session.execute(
                text("""
                SELECT id, username, email, full_name, role, created_at, last_login
                FROM users 
                WHERE id = :user_id AND is_active = 1
                """),
                {'user_id': user_id}
            ).fetchone()
            
            if not user_data:
                return jsonify({'error': '用戶不存在'}), 404
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user_data.id,
                    'username': user_data.username,
                    'email': user_data.email,
                    'full_name': user_data.full_name,
                    'role': user_data.role,
                    'created_at': user_data.created_at.isoformat() if user_data.created_at else None,
                    'last_login': user_data.last_login.isoformat() if user_data.last_login else None
                }
            }), 200
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'獲取用戶資料失敗: {str(e)}'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """使用者登出"""
    # 在 JWT 中，登出主要由前端處理（刪除 token）
    # 這裡可以記錄登出日誌或其他處理
    return jsonify({'success': True, 'message': '登出成功'}), 200


@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """
    上傳 Excel 檔案並將指定工作表的資料存入 SQLite 資料庫
    - 雲端環境：儲存到 Cloud Storage
    - 本地環境：儲存到本地檔案夾
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    sheet_name = request.form.get('sheet_name', None)  # 工作表名稱
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # 根據環境選擇儲存方式
        if is_cloud_environment() and bucket is not None:
            # 雲端環境：使用 Cloud Storage
            return upload_to_cloud_storage(file, sheet_name)
        else:
            # 本地環境：使用本地儲存
            return upload_to_local_storage(file, sheet_name)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def upload_to_cloud_storage(file, sheet_name):
    """雲端儲存邏輯"""
    # 生成唯一檔案名
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    blob_name = f"uploads/{get_jwt_identity()}/{file_id}{file_extension}"
    
    # 上傳檔案到 Cloud Storage
    blob = bucket.blob(blob_name)
    file.seek(0)  # 重置檔案指標
    blob.upload_from_file(file, content_type=file.content_type)
    
    # 如果沒有指定工作表，先回傳所有工作表名稱讓前端選擇
    if not sheet_name:
        # 從 Cloud Storage 下載檔案到臨時位置讀取工作表
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            blob.download_to_filename(temp_file.name)
            xl = pd.ExcelFile(temp_file.name)
            sheets = xl.sheet_names
        
        # 清理臨時檔案
        os.unlink(temp_file.name)
        
        return jsonify({
            "filename": file.filename,
            "file_id": file_id,
            "blob_name": blob_name,
            "sheets": sheets,
            "need_sheet_selection": True
        }), 200

    # 從 Cloud Storage 讀取指定工作表
    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
        blob.download_to_filename(temp_file.name)
        df = pd.read_excel(temp_file.name, sheet_name=sheet_name)
    
    # 清理臨時檔案
    os.unlink(temp_file.name)
    
    # 處理資料並存入資料庫
    return process_excel_data(file, df, sheet_name, file_id=file_id, blob_name=blob_name)


def upload_to_local_storage(file, sheet_name):
    """本地儲存邏輯（原有邏輯）"""
    # 儲存檔案到本地
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
    
    # 處理資料並存入資料庫
    return process_excel_data(file, df, sheet_name)


def process_excel_data(file, df, sheet_name, file_id=None, blob_name=None):
    """
    共用的 Excel 資料處理邏輯
    自動添加 user_id 實現多租戶資料隔離
    """
    # 取得當前使用者 ID
    current_user_id = get_jwt_identity()
    
    # 過濾資料：在遇到空白行時停止讀取
    df = filter_dataframe_until_empty_row(df)
    
    if df.empty:
        return jsonify({"error": "工作表中沒有有效資料"}), 400
        
    columns = df.columns.tolist()

    # 建立資料表名稱：{user_id}_{工作表名稱}_{日期時間}
    # 格式：1_整理後總表_120704091107（年月日時分秒，去掉前兩位年份）
    safe_sheet_name = sheet_name.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')  # 120704091107 格式
    table_name = f"{current_user_id}_{safe_sheet_name}_{timestamp}"

    # 建立資料表
    table = create_excel_table(table_name, columns)
    
    # 將資料寫入資料庫
    session = Session()
    try:
        # 轉換資料並插入（自動添加 user_id）
        data_dicts = []
        for _, row in df.iterrows():
            row_dict = {'user_id': current_user_id}  # 多租戶：記錄上傳者
            for i, col in enumerate(columns):
                safe_col_name = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                row_dict[safe_col_name] = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ''
            data_dicts.append(row_dict)
        
        session.execute(table.insert(), data_dicts)
        session.commit()
        
        # 記錄檔案資訊（僅雲端環境需要）
        if file_id and blob_name:
            current_time = datetime.utcnow()
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO uploaded_files (file_id, user_id, original_filename, blob_name, upload_time, sheet_name, table_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (file_id, get_jwt_identity(), file.filename, blob_name, current_time.isoformat(), sheet_name, table_name))
                conn.commit()
        
        response_data = {
            "success": True,
            "filename": file.filename,
            "sheet_name": sheet_name,
            "table_name": table_name,
            "columns": columns,
            "rows_inserted": len(data_dicts)
        }
        
        if file_id:
            response_data["file_id"] = file_id
        
        # 上傳成功後自動備份資料庫
        backup_database_to_gcs()
            
        return jsonify(response_data), 200
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
    



@app.route('/api/database/tables', methods=['GET'])
@jwt_required()
def list_database_tables_new():
    # DEBUG: 檢查 database/ 目錄內容
    try:
        db_files = os.listdir('database')
        print(f"[DEBUG] database/ 目錄內容: {db_files}")
        print(f"[DEBUG] fakedata.db 存在: {os.path.exists('database/fakedata.db')}")
    except Exception as e:
        print(f"[DEBUG] 無法列出 database/ 目錄: {e}")
    """
    取得資料庫中所有已存入的表格清單（新格式API）
    """
    try:
        # 添加調試信息
        current_user_id = get_jwt_identity()
        print(f"[DEBUG] JWT驗證成功，用戶ID: {current_user_id} (type: {type(current_user_id)})")
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 只回傳屬於當前用戶的表格（表名格式：{user_id}_{sheet}_{timestamp}）
        user_prefix = f"{current_user_id}_"
        user_tables = [table for table in tables if table.startswith(user_prefix)]

        # 解析表格名稱，提取工作表名
        table_info = []
        for table in user_tables:
            try:
                # 格式：{user_id}_{工作表名}_{時間戳}
                parts = table.replace(user_prefix, '', 1).rsplit('_', 1)
                if len(parts) == 2:
                    sheet_name = parts[0]
                    timestamp = parts[1]
                    table_info.append({
                        'table_name': table,
                        'display_name': f"{sheet_name}",
                        'sheet_name': sheet_name,
                        'timestamp': timestamp
                    })
            except Exception as e:
                # 如果解析失敗，就直接顯示表格名稱
                table_info.append({
                    'table_name': table,
                    'display_name': table,
                    'filename': '',
                    'sheet_name': ''
                })

        # 加入 fakedata.db 的所有表格（不重複）
        from sqlalchemy import create_engine as _create_engine
        try:
            fakedata_engine = _create_engine('sqlite:///database/fakedata.db', echo=False)
            fakedata_inspector = inspect(fakedata_engine)
            fakedata_tables = fakedata_inspector.get_table_names()
            for table in fakedata_tables:
                # 避免重複
                if not any(t['table_name'] == table for t in table_info):
                    table_info.append({
                        'table_name': table,
                        'display_name': table,
                        'sheet_name': table,
                        'timestamp': ''
                    })
        except Exception as e:
            print(f"[WARNING] inspect fakedata.db failed: {e}")

        # 移除：不再手動加上 fakedata，因為上面已經從 fakedata.db 添加了所有表格

        return jsonify({'success': True, 'tables': table_info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/table_columns', methods=['POST'])
@jwt_required()
def get_table_columns():
    """
    取得指定表格的欄位清單
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({'error': '缺少table_name參數'}), 400
        
        # 先查主資料庫（excel_data.db）
        try:
            current_engine, current_inspector = get_database_engine(table_name)
            columns_info = current_inspector.get_columns(table_name)
            columns = [col['name'] for col in columns_info if col['name'] != 'id']
            return jsonify({'columns': columns})
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            app.logger.error(f"[WARNING] 查詢 fakedata.db 欄位失敗: {e}")

        return jsonify({'error': '找不到指定的資料表'}), 404
        
    except Exception as e:
        app.logger.error(f"Error getting table columns: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/tables/<table_name>/count', methods=['GET'])
@jwt_required()
def get_table_row_count(table_name):
    """
    取得指定資料表的行數統計
    """
    try:
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        
        # 執行計數查詢
        with current_engine.connect() as connection:
            result = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
            count = result.scalar()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# === 數據 CRUD API ===

@app.route('/api/database/tables/<table_name>/data', methods=['GET'])
@jwt_required()
def get_table_data(table_name):
    """
    分頁查詢表格數據（只顯示當前用戶的資料）
    """
    try:
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
            is_fakedata = (current_engine.url.database == FAKEDATA_DB_PATH)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        
        # 取得當前使用者 ID
        current_user_id = get_jwt_identity()
        
        # 取得查詢參數
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '')
        
        # 計算偏移量
        offset = (page - 1) * limit
        
        # 取得表格欄位資訊
        columns_info = current_inspector.get_columns(table_name)
        columns = [col['name'] for col in columns_info if col['name'] != 'id']
        
        # 建立綁定到正確資料庫的 Session
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            # 構建基礎查詢
            if is_fakedata:
                # fakedata 不需要 user_id 過濾
                if search:
                    # 添加搜尋功能 - 在所有文字欄位中搜尋
                    search_conditions = []
                    for col in columns:
                        search_conditions.append(f'`{col}` LIKE :search')
                    search_query = f"SELECT * FROM `{table_name}` WHERE ({' OR '.join(search_conditions)}) ORDER BY id LIMIT :limit OFFSET :offset"
                    count_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE ({' OR '.join(search_conditions)})"
                    
                    result = session.execute(text(search_query), {'search': f'%{search}%', 'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(count_query), {'search': f'%{search}%'}).scalar()
                else:
                    result = session.execute(text(f"SELECT * FROM `{table_name}` ORDER BY id LIMIT :limit OFFSET :offset"), {'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()
            else:
                # excel_data 需要 user_id 過濾
                if search:
                    # 添加搜尋功能 - 在所有文字欄位中搜尋
                    search_conditions = []
                    for col in columns:
                        search_conditions.append(f'`{col}` LIKE :search')
                    search_query = f"SELECT * FROM `{table_name}` WHERE user_id = :user_id AND ({' OR '.join(search_conditions)}) ORDER BY id LIMIT :limit OFFSET :offset"
                    count_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE user_id = :user_id AND ({' OR '.join(search_conditions)})"
                    
                    result = session.execute(text(search_query), {'user_id': current_user_id, 'search': f'%{search}%', 'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(count_query), {'user_id': current_user_id, 'search': f'%{search}%'}).scalar()
                else:
                    result = session.execute(text(f"SELECT * FROM `{table_name}` WHERE user_id = :user_id ORDER BY id LIMIT :limit OFFSET :offset"), {'user_id': current_user_id, 'limit': limit, 'offset': offset}).fetchall()
                    total = session.execute(text(f"SELECT COUNT(*) FROM `{table_name}` WHERE user_id = :user_id")).scalar()
            
            # 轉換結果為字典列表
            data = []
            for row in result:
                row_dict = dict(zip(['id'] + columns, row))
                data.append(row_dict)
            
            # 計算總頁數
            total_pages = (total + limit - 1) // limit
            
            return jsonify({
                'success': True,
                'data': data,
                'columns': ['id'] + columns,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total,
                    'limit': limit,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/tables/<table_name>/data', methods=['POST'])
@jwt_required()
def create_table_row(table_name):
    """
    新增單筆資料（自動添加當前用戶的 user_id）
    """
    try:
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        
        # 取得當前使用者 ID
        current_user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少資料內容'}), 400
        
        # 取得表格欄位資訊（排除 id）
        columns_info = current_inspector.get_columns(table_name)
        columns = [col['name'] for col in columns_info if col['name'] != 'id']
        
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            # 構建插入語句
            placeholders = ', '.join([f':{col}' for col in columns])
            columns_str = ', '.join([f'`{col}`' for col in columns])
            insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
            
            # 準備插入資料，只保留表格中存在的欄位
            insert_data = {}
            for col in columns:
                # user_id 使用當前登入用戶的 ID
                if col == 'user_id':
                    insert_data[col] = current_user_id
                else:
                    insert_data[col] = data.get(col, '')
            
            result = session.execute(text(insert_query), insert_data)
            session.commit()
            
            return jsonify({
                'success': True, 
                'message': '資料新增成功',
                'inserted_id': result.lastrowid
            })
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/tables/<table_name>/data/<int:row_id>', methods=['PUT'])
@jwt_required()
def update_table_row(table_name, row_id):
    """
    更新指定資料（只能更新自己的資料）
    """
    try:
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        
        # 取得當前使用者 ID
        current_user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少資料內容'}), 400
        
        # 取得表格欄位資訊（排除 id 和 user_id）
        columns_info = current_inspector.get_columns(table_name)
        columns = [col['name'] for col in columns_info if col['name'] not in ['id', 'user_id']]
        
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            # 檢查資料是否存在且屬於當前用戶
            check_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE id = :row_id AND user_id = :user_id"
            exists = session.execute(text(check_query), {'row_id': row_id, 'user_id': current_user_id}).scalar()
            
            if not exists:
                return jsonify({'success': False, 'error': '找不到指定的資料或無權限修改'}), 404
            
            # 構建更新語句
            set_clauses = [f'`{col}` = :{col}' for col in columns if col in data]
            if not set_clauses:
                return jsonify({'success': False, 'error': '沒有可更新的欄位'}), 400
            
            update_query = f"UPDATE `{table_name}` SET {', '.join(set_clauses)} WHERE id = :row_id"
            
            # 準備更新資料
            update_data = {'row_id': row_id}
            for col in columns:
                if col in data:
                    update_data[col] = data[col]
            
            session.execute(text(update_query), update_data)
            session.commit()
            
            return jsonify({'success': True, 'message': '資料更新成功'})
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/tables/<table_name>/data/<int:row_id>', methods=['DELETE'])
@jwt_required()
def delete_table_row(table_name, row_id):
    """
    刪除指定資料（只能刪除自己的資料）
    """
    try:
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        
        # 取得當前使用者 ID
        current_user_id = get_jwt_identity()
        
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
        try:
            # 檢查資料是否存在且屬於當前用戶
            check_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE id = :row_id AND user_id = :user_id"
            exists = session.execute(text(check_query), {'row_id': row_id, 'user_id': current_user_id}).scalar()
            
            if not exists:
                return jsonify({'success': False, 'error': '找不到指定的資料或無權限刪除'}), 404
            
            # 執行刪除（添加 user_id 檢查）
            delete_query = f"DELETE FROM `{table_name}` WHERE id = :row_id AND user_id = :user_id"
            session.execute(text(delete_query), {'row_id': row_id, 'user_id': current_user_id})
            session.commit()
            
            return jsonify({'success': True, 'message': '資料刪除成功'})
            
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sheets', methods=['POST'])
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
        
        try:
            current_engine, current_inspector = get_database_engine(safe_table_name)
            # 從資料庫讀取
            table = Table(safe_table_name, metadata, autoload_with=current_engine)
            session = Session()
            result = session.execute(table.select()).fetchall()
            session.close()
            columns = [col.name for col in table.columns if col.name != 'id']
            data = [dict(zip(columns, row[1:])) for row in result]  # 跳過 id 欄位
            return jsonify({'columns': columns, 'data': data})
        except ValueError:
            # 資料庫中沒有這個表，直接從檔案讀取
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
@jwt_required()
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
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
            
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
@jwt_required()
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
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
            
        # 取得欄位清單並轉換為安全名稱
        columns_info = current_inspector.get_columns(table_name)
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
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
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
@jwt_required()
def yearly_admission_stats():
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        gender_col = data.get('gender_col')  # 可選的性別欄位

        if not table_name or not year_col:
            return jsonify({'error': '缺少 table_name 或 year_col'}), 400

        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404

        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
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
@jwt_required()
def school_source_stats():
    """
    從資料庫統計每年入學生的學校來源類型分布
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        year_col = data.get('year_col')
        school_col = data.get('school_col')  # 學校名稱欄位
        
        if not table_name or not year_col or not school_col:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        
        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_school_col = school_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_school_col not in available_columns:
            return jsonify({'error': f'找不到學校欄位: {school_col}'}), 400
        
        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
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
@jwt_required()
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
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        
        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_method_col = method_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        
        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_method_col not in available_columns:
            return jsonify({'error': f'找不到入學管道欄位: {method_col}'}), 400
        
        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
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

@app.route('/api/geographic_stats', methods=['POST'])
@jwt_required()
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
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404

        # 轉換為安全欄位名稱
        safe_year_col = year_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        safe_region_col = region_col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

        # 檢查欄位是否存在
        columns_info = current_inspector.get_columns(table_name)
        available_columns = [col['name'] for col in columns_info]
        
        if safe_year_col not in available_columns:
            return jsonify({'error': f'找不到年度欄位: {year_col}'}), 400
        if safe_region_col not in available_columns:
            return jsonify({'error': f'找不到地區欄位: {region_col}'}), 400

        # 從資料庫讀取資料
        SessionLocal = sessionmaker(bind=current_engine)
        session = SessionLocal()
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
            
            return jsonify(result)
            
        finally:
            session.close()

    except Exception as e:
        print(f"[geographic_stats] Error: {str(e)}")
        return jsonify({'error': f'處理資料時發生錯誤: {str(e)}'}), 500


@app.route('/api/top_schools_stats', methods=['POST'])
@jwt_required()
def top_schools_stats():
    """前20大入學高中統計"""
    try:
        data = request.get_json()
        
        # 基本參數
        filename = data.get('filename')
        sheet = data.get('sheet', '')
        school_col = data.get('school_col')
        year_col = data.get('year_col')  # 可選
        
        if not filename or not school_col:
            return jsonify({'error': '檔案名稱和學校欄位為必要參數'}), 400
        
        print(f"[top_schools_stats] 開始分析前20大入學高中")
        print(f"[top_schools_stats] filename: {filename}, sheet: {sheet}")
        print(f"[top_schools_stats] school_col: {school_col}, year_col: {year_col}")
        
        # 使用全域資料庫連接
        session = Session()
        
        try:
            # 讀取資料
            if sheet:
                # 從檔案讀取
                df = pd.read_excel(f'uploads/{filename}', sheet_name=sheet)
                df = filter_dataframe_until_empty_row(df)
            else:
                # 從資料庫讀取
                table_name = filename.replace('.xlsx', '').replace('.xls', '')
                
                try:
                    current_engine, current_inspector = get_database_engine(table_name)
                except ValueError as e:
                    return jsonify({'error': str(e)}), 404
                
                df = pd.read_sql_table(table_name, current_engine)
            
            if df.empty:
                return jsonify({'error': '沒有找到資料'}), 400
            
            print(f"[top_schools_stats] 資料讀取完成，共 {len(df)} 筆記錄")
            
            # 檢查欄位是否存在
            if school_col not in df.columns:
                return jsonify({'error': f'找不到學校欄位: {school_col}'}), 400
            
            if year_col and year_col not in df.columns:
                return jsonify({'error': f'找不到年份欄位: {year_col}'}), 400
            
            # 清理學校名稱資料
            df[school_col] = df[school_col].fillna('未知')
            df[school_col] = df[school_col].astype(str).str.strip()
            
            # 過濾掉無效的學校名稱
            df = df[df[school_col] != '']
            df = df[df[school_col] != '未知']
            df = df[df[school_col] != 'nan']
            
            result = {}
            
            if year_col:
                # 按年份分析
                df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
                df = df.dropna(subset=[year_col])
                
                # 按學校和年份統計
                yearly_stats = df.groupby([school_col, year_col]).size().reset_index(name='count')
                
                # 計算每個學校的總人數
                school_totals = yearly_stats.groupby(school_col)['count'].sum().reset_index()
                school_totals = school_totals.sort_values('count', ascending=False)
                
                # 取前20大學校
                top20_schools = school_totals.head(20)
                
                # 獲取年份列表
                years = sorted(df[year_col].unique())
                
                # 為每個學校添加年度詳細資料
                schools_data = []
                total_students = df.shape[0]
                
                for idx, (_, row) in enumerate(top20_schools.iterrows()):
                    school_name = row[school_col]
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
                            (yearly_stats[school_col] == school_name) & 
                            (yearly_stats[year_col] == year)
                        ]['count'].sum()
                        school_data[f'year_{int(year)}'] = int(year_count)
                    
                    schools_data.append(school_data)
                
                result = {
                    'schools': schools_data,
                    'total_students': int(total_students),
                    'by_year': True,
                    'years': [int(year) for year in years]
                }
                
            else:
                # 不按年份分析
                school_counts = df[school_col].value_counts().reset_index()
                school_counts.columns = [school_col, 'count']
                
                # 取前20大學校
                top20_schools = school_counts.head(20)
                
                # 格式化結果
                schools_data = []
                total_students = df.shape[0]
                
                for idx, (_, row) in enumerate(top20_schools.iterrows()):
                    schools_data.append({
                        'rank': idx + 1,
                        'school_name': row[school_col],
                        'total_count': int(row['count']),
                        'percentage': round((row['count'] / total_students) * 100, 2)
                    })
                
                result = {
                    'schools': schools_data,
                    'total_students': int(total_students),
                    'by_year': False
                }
            
            print(f"[top_schools_stats] 分析完成，前20大學校數據已生成")
            return jsonify(result)
            
        finally:
            session.close()

    except Exception as e:
        print(f"[top_schools_stats] Error: {str(e)}")
        return jsonify({'error': f'處理資料時發生錯誤: {str(e)}'}), 500


@app.route('/api/subject_average_stats', methods=['POST'])
@jwt_required()
def subject_average_stats():
    """大一各科平均成績分析"""
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({'error': '缺少必要參數'}), 400
        
        # 定義科目欄位
        subjects = [
            '會計學', '計算機概論', '微積分', '基礎程式設計', 
            '統計1', '經濟學', '程式設計', '管理學', '統計2'
        ]
        
        # 從資料庫取得資料
        
        # 檢查資料表是否存在
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        
        # 初始化資料庫會話
        Session = sessionmaker(bind=current_engine)
        session = Session()
        
        print(f"[subject_average_stats] 開始處理大一各科平均成績分析")
        
        query = f"""
        SELECT 年度, {', '.join([f'`{subject}`' for subject in subjects])}
        FROM `{table_name}` 
        WHERE 年度 IS NOT NULL
        """
        
        try:
            df = pd.read_sql_query(query, session.bind)
            print(f"[subject_average_stats] 成功讀取 {len(df)} 筆資料")
        except Exception as e:
            print(f"[subject_average_stats] 資料庫讀取失敗: {str(e)}")
            return jsonify({'error': f'資料庫讀取失敗: {str(e)}'}), 500
        
        if df.empty:
            return jsonify({'error': '沒有找到相關資料'}), 404
        
        # 處理年度欄位，確保為數字
        df['年度'] = pd.to_numeric(df['年度'], errors='coerce')
        df = df.dropna(subset=['年度'])
        
        # 將科目成績轉為數字，並處理無效值
        for subject in subjects:
            df[subject] = pd.to_numeric(df[subject], errors='coerce')
        
        # 獲取完整資料包含性別、高中別、入學管道
        complete_query = f"""
        SELECT 年度, 性別, 高中別, 入學管道, {', '.join([f'`{subject}`' for subject in subjects])}
        FROM `{table_name}` 
        WHERE 年度 IS NOT NULL
        """
        
        try:
            complete_df = pd.read_sql_query(complete_query, session.bind)
            print(f"[subject_average_stats] 成功讀取完整資料 {len(complete_df)} 筆")
        except Exception as e:
            print(f"[subject_average_stats] 完整資料讀取失敗: {str(e)}")
            complete_df = df  # 使用原始資料作為備用
        
        # 處理年度欄位，確保為數字
        complete_df['年度'] = pd.to_numeric(complete_df['年度'], errors='coerce')
        complete_df = complete_df.dropna(subset=['年度'])
        
        # 將科目成績轉為數字，並處理無效值
        for subject in subjects:
            complete_df[subject] = pd.to_numeric(complete_df[subject], errors='coerce')
        
        # 定義分類對應
        school_type_mapping = {
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
        
        admission_types = ['申請入學', '繁星推薦', '自然組', '社會組', '僑生', '願景', '其他']
        
        # 計算每年每科的平均成績及其他統計
        yearly_averages = []
        years = sorted(complete_df['年度'].unique())
        
        for year in years:
            year_data = complete_df[complete_df['年度'] == year]
            year_avg = {'年度': int(year)}
            
            # 基本統計
            year_avg['總人數'] = len(year_data)
            
            # 性別統計
            gender_stats = year_data['性別'].value_counts()
            year_avg['男性人數'] = int(gender_stats.get('男', 0))
            year_avg['女性人數'] = int(gender_stats.get('女', 0))
            
            # 高中別統計 - 使用優先級匹配避免重複
            school_type_stats = {}
            processed_indices = set()
            
            # 按優先級順序處理，避免重複計算
            priority_mapping = [
                ('國立', '國立'),
                ('私立', '私立'),
                ('財團法人', '財團'),  
                ('市立', '市立'),
                ('大陸台商', '其他'),
                ('私大轉', '私大轉'),
                ('科大轉', '科大轉'),
                ('國大轉', '國大轉'),
                ('僑生', '僑生')
            ]
            
            for original_type, mapped_type in priority_mapping:
                mask = year_data['高中別'].astype(str).str.contains(original_type, na=False)
                # 只計算尚未被處理的資料
                available_mask = mask & ~year_data.index.isin(processed_indices)
                count = available_mask.sum()
                
                if count > 0:
                    school_type_stats[mapped_type] = int(count)
                    # 標記已處理的索引
                    processed_indices.update(year_data[available_mask].index)
            
            # 將高中別統計加入結果
            for school_type in ['國立', '私立', '財團', '市立', '其他', '私大轉', '科大轉', '國大轉', '僑生']:
                year_avg[f'{school_type}人數'] = school_type_stats.get(school_type, 0)
            
            # 入學管道統計 - 使用分類函數
            year_data['入學管道分類'] = year_data['入學管道'].apply(classify_admission_method)
            admission_classified_stats = year_data['入學管道分類'].value_counts()
            for admission_type in admission_types:
                year_avg[f'{admission_type}人數'] = int(admission_classified_stats.get(admission_type, 0))
            
            # 科目平均成績
            for subject in subjects:
                # 計算該年該科目的平均成績（排除 NaN 值）
                valid_scores = year_data[subject].dropna()
                if len(valid_scores) > 0:
                    avg_score = valid_scores.mean()
                    year_avg[subject] = round(avg_score, 2)
                else:
                    year_avg[subject] = None
            
            yearly_averages.append(year_avg)
        
        # 計算整體統計
        overall_stats = {}
        for subject in subjects:
            valid_scores = df[subject].dropna()
            if len(valid_scores) > 0:
                overall_stats[subject] = {
                    'overall_average': round(valid_scores.mean(), 2),
                    'min_score': round(valid_scores.min(), 2),
                    'max_score': round(valid_scores.max(), 2),
                    'std_dev': round(valid_scores.std(), 2),
                    'total_students': len(valid_scores)
                }
            else:
                overall_stats[subject] = {
                    'overall_average': None,
                    'min_score': None,
                    'max_score': None,
                    'std_dev': None,
                    'total_students': 0
                }
        
        # 找出最高和最低平均成績的科目
        subject_averages = [(subject, stats['overall_average']) 
                          for subject, stats in overall_stats.items() 
                          if stats['overall_average'] is not None]
        
        highest_subject = max(subject_averages, key=lambda x: x[1]) if subject_averages else None
        lowest_subject = min(subject_averages, key=lambda x: x[1]) if subject_averages else None
        
        # 計算整體統計摘要
        total_students_all_years = len(complete_df)
        gender_summary = complete_df['性別'].value_counts()
        
        # 整體高中別統計 - 避免重複計算
        school_type_summary = {}
        processed_indices_overall = set()
        
        for original_type, mapped_type in priority_mapping:
            mask = complete_df['高中別'].astype(str).str.contains(original_type, na=False)
            available_mask = mask & ~complete_df.index.isin(processed_indices_overall)
            count = available_mask.sum()
            
            if count > 0:
                school_type_summary[mapped_type] = int(count)
                processed_indices_overall.update(complete_df[available_mask].index)
        
        # 整體入學管道統計 - 使用分類函數
        complete_df['入學管道分類'] = complete_df['入學管道'].apply(classify_admission_method)
        admission_summary = complete_df['入學管道分類'].value_counts()
        
        result = {
            'yearly_data': yearly_averages,
            'overall_stats': overall_stats,
            'subjects': subjects,
            'years': [int(year) for year in years],
            'year_range': f"{int(min(years))}-{int(max(years))}",
            'total_students': total_students_all_years,
            'gender_summary': {
                '男性': int(gender_summary.get('男', 0)),
                '女性': int(gender_summary.get('女', 0))
            },
            'school_type_summary': school_type_summary,
            'admission_summary': {k: int(v) for k, v in admission_summary.items()},
            'school_types': ['國立', '私立', '財團', '市立', '其他', '私大轉', '科大轉', '國大轉', '僑生'],
            'admission_types': admission_types,
            'highest_subject': {
                'subject': highest_subject[0],
                'average': highest_subject[1]
            } if highest_subject else None,
            'lowest_subject': {
                'subject': lowest_subject[0],
                'average': lowest_subject[1]
            } if lowest_subject else None,
            'column_name': '大一各科平均成績'
        }
        
        print(f"[subject_average_stats] 分析完成，涵蓋 {len(years)} 年度、{len(subjects)} 科目")
        return jsonify(result)
        
    except Exception as e:
        print(f"[subject_average_stats] Error: {str(e)}")
        return jsonify({'error': f'處理資料時發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


@app.route('/api/analysis/gender-subject', methods=['POST'])
@jwt_required()
def gender_subject_analysis():
    """
    性別科目成績分析 API
    支援多科目選擇，分析男女生在各科目間的成績差異
    """
    try:
        data = request.get_json()
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
            return jsonify({'error': '缺少必要參數'}), 400
        
        if not isinstance(subject_cols, list) or len(subject_cols) == 0:
            return jsonify({'error': '請至少選擇一個科目'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        
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
            return jsonify({'error': '沒有找到有效的科目欄位'}), 400
        
        # 檢查必要欄位是否存在
        if safe_year_col not in available_columns:
            return jsonify({'error': f'年度欄位 {year_col} 不存在'}), 400
        if safe_gender_col not in available_columns:
            return jsonify({'error': f'性別欄位 {gender_col} 不存在'}), 400
        
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
            return jsonify({'error': '沒有找到符合條件的資料'}), 404
        
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
            return jsonify({'error': '沒有找到有效的性別資料'}), 404
        
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
        return jsonify(analysis_results)
        
    except Exception as e:
        print(f"[gender_subject_analysis] Error: {str(e)}")
        return jsonify({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


@app.route('/api/analysis/admission-subject', methods=['POST'])
@jwt_required()
def admission_subject_analysis():
    """
    入學管道科目成績分析 API
    支援多科目選擇，分析不同入學管道學生在各科目間的成績差異
    """
    try:
        data = request.get_json()
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
            return jsonify({'error': '缺少必要參數'}), 400
        
        if not isinstance(subject_cols, list) or len(subject_cols) == 0:
            return jsonify({'error': '請至少選擇一個科目'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        
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
            return jsonify({'error': '沒有找到有效的科目欄位'}), 400
        
        # 檢查必要欄位是否存在
        if safe_year_col not in available_columns:
            return jsonify({'error': f'年度欄位 {year_col} 不存在'}), 400
        if safe_admission_col not in available_columns:
            return jsonify({'error': f'入學管道欄位 {admission_col} 不存在'}), 400
        
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
            return jsonify({'error': '查詢結果為空，請檢查篩選條件'}), 404
        
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
        return jsonify(analysis_results)
        
    except Exception as e:
        print(f"[admission_subject_analysis] Error: {str(e)}")
        return jsonify({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


@app.route('/api/analysis/school-type-subject', methods=['POST'])
@jwt_required()
def school_type_subject_analysis():
    """
    高中類型科目成績分析 API
    支援多科目選擇，分析不同高中類型學生在各科目間的成績差異
    """
    try:
        data = request.get_json()
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
            return jsonify({'error': '缺少必要參數'}), 400
        
        if not isinstance(subject_cols, list) or len(subject_cols) == 0:
            return jsonify({'error': '請至少選擇一個科目'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        
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
            return jsonify({'error': '沒有找到有效的科目欄位'}), 400
        
        # 檢查必要欄位是否存在
        if safe_year_col not in available_columns:
            return jsonify({'error': f'年度欄位 {year_col} 不存在'}), 400
        if safe_school_type_col not in available_columns:
            return jsonify({'error': f'高中類型欄位 {school_type_col} 不存在'}), 400
        
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
            return jsonify({'error': '查詢結果為空，請檢查篩選條件'}), 404
        
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
        return jsonify(analysis_results)
        
    except Exception as e:
        print(f"[school_type_subject_analysis] Error: {str(e)}")
        return jsonify({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


@app.route('/api/analysis/region-subject', methods=['POST'])
def region_subject_analysis():
    """地區科目成績分析API"""
    session = None
    try:
        data = request.get_json()
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
            return jsonify({'error': '缺少必要參數：table_name, year_col, region_col'}), 400
            
        if not subject_cols:
            return jsonify({'error': '必須至少選擇一個科目欄位'}), 400
        
        # 建立資料庫連接
        try:
            current_engine, current_inspector = get_database_engine(table_name)  # current_inspector 目前未使用，之後可考慮統一檢查欄位的方法
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        Session = sessionmaker(bind=current_engine)
        session = Session()
        
        # 檢查欄位是否存在
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=current_engine)
        available_columns = [col.name for col in table.columns]
        
        print(f"[region_subject_analysis] 可用欄位: {available_columns}")
        
        # 檢查年度和地區欄位
        if year_col not in available_columns:
            return jsonify({'error': f'年度欄位 {year_col} 不存在'}), 400
        if region_col not in available_columns:
            return jsonify({'error': f'地區欄位 {region_col} 不存在'}), 400
            
        # 檢查科目欄位
        valid_subject_cols = []
        for col in subject_cols:
            if col in available_columns:
                valid_subject_cols.append(col)
            else:
                print(f"[region_subject_analysis] 警告：科目欄位 '{col}' 不存在")
        
        if not valid_subject_cols:
            return jsonify({'error': '所有科目欄位都不存在'}), 400
        
        # 構建查詢
        select_columns = [year_col, region_col] + valid_subject_cols
        columns_str = ', '.join([f'"{col}"' for col in select_columns])
        
        # 基本查詢
        query = f'''
        SELECT {columns_str}
        FROM "{table_name}"
        WHERE "{year_col}" IS NOT NULL 
        AND "{region_col}" IS NOT NULL
        '''
        
        # 添加年份篩選條件
        if years_filter and len(years_filter) > 0:
            years_str = ', '.join([f"'{year}'" for year in years_filter])
            query += f' AND "{year_col}" IN ({years_str})'
        
        # 添加科目欄位非空條件
        subject_conditions = []
        for col in valid_subject_cols:
            subject_conditions.append(f'"{col}" IS NOT NULL')
        if subject_conditions:
            query += ' AND (' + ' OR '.join(subject_conditions) + ')'
        
        print(f"[region_subject_analysis] 執行查詢: {query}")
        
        # 執行查詢
        with current_engine.connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        print(f"[region_subject_analysis] 讀取到 {len(df)} 筆資料")
        
        if df.empty:
            return jsonify({'error': '沒有找到符合條件的資料'}), 400
        
        # 標準化地區名稱：將所有「臺」轉換為「台」
        df[region_col] = df[region_col].apply(lambda x: str(x).replace('臺', '台') if pd.notna(x) else x)
        
        # 獲取可用的年份和地區，過濾空值和空字串
        available_years = sorted([year for year in df[year_col].dropna().unique().tolist() if str(year).strip() != ''])
        available_regions = sorted([region for region in df[region_col].dropna().unique().tolist() if str(region).strip() != ''])
        
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
            'subjects': valid_subject_cols,
            'regions': final_regions,
            'enable_grouping': enable_grouping,
            'region_details': {}
        }
        
        # 對每個最終地區進行分析
        for region in final_regions:
            region_data = df[df[region_col] == region].copy()
            yearly_data = []
            
            for year in available_years:
                year_data_filtered = region_data[region_data[year_col] == year]
                
                if not year_data_filtered.empty:
                    year_result = {'year': year, 'subjects': {}}
                    
                    for subject in valid_subject_cols:
                        if subject in year_data_filtered.columns:
                            subject_values = pd.to_numeric(year_data_filtered[subject], errors='coerce').dropna()
                            if len(subject_values) > 0:
                                avg_score = round(subject_values.mean(), 1)
                                year_result['subjects'][subject] = avg_score
                            else:
                                year_result['subjects'][subject] = None
                        else:
                            year_result['subjects'][subject] = None
                    
                    yearly_data.append(year_result)
                else:
                    # 如果該年度沒有數據，仍要添加空記錄
                    year_result = {'year': year, 'subjects': {}}
                    for subject in valid_subject_cols:
                        year_result['subjects'][subject] = None
                    yearly_data.append(year_result)
            
            result_data['region_details'][region] = yearly_data
        
        # 篩選出實際有數據的科目
        final_subjects = []
        for subject in valid_subject_cols:
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
        
        return jsonify(result_data)
    
    except Exception as e:
        print(f"[region_subject_analysis] Error: {str(e)}")
        return jsonify({'error': f'分析過程發生錯誤: {str(e)}'}), 500
    
    finally:
        if 'session' in locals():
            session.close()


# === 檔案管理 API ===

@app.route('/api/files', methods=['GET'])
@jwt_required()
def list_user_files():
    """取得當前用戶的檔案清單"""
    try:
        user_id = get_jwt_identity()
        
        # 檢查是否有檔案記錄表
        inspector = inspect(engine)
        if not inspector.has_table('uploaded_files'):
            return jsonify({'success': True, 'files': []}), 200
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_id, original_filename, upload_time, sheet_name, table_name
                FROM uploaded_files 
                WHERE user_id = ? 
                ORDER BY upload_time DESC
            """, (user_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'file_id': row[0],
                    'filename': row[1],
                    'upload_time': row[2],
                    'sheet_name': row[3],
                    'table_name': row[4]
                })
        
        return jsonify({'success': True, 'files': files}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files/<file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """下載檔案"""
    try:
        user_id = get_jwt_identity()
        
        # 檢查檔案是否存在且屬於當前用戶
        inspector = inspect(engine)
        if not inspector.has_table('uploaded_files'):
            return jsonify({'success': False, 'error': '無檔案記錄'}), 404
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_filename, blob_name 
                FROM uploaded_files 
                WHERE file_id = ? AND user_id = ?
            """, (file_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': '檔案不存在或無權限'}), 404
            
            original_filename, blob_name = result
        
        if is_cloud_environment() and bucket is not None:
            # 雲端環境：從 Cloud Storage 生成簽署 URL
            blob = bucket.blob(blob_name)
            
            # 生成 1 小時有效的簽署 URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            
            return jsonify({
                'success': True,
                'download_url': url,
                'filename': original_filename
            }), 200
        else:
            # 本地環境：檢查檔案是否存在於 uploads 目錄
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            if os.path.exists(local_path):
                return send_from_directory(app.config['UPLOAD_FOLDER'], original_filename)
            else:
                return jsonify({'success': False, 'error': '檔案不存在'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/files/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """刪除檔案"""
    try:
        user_id = get_jwt_identity()
        
        # 檢查檔案是否存在且屬於當前用戶
        inspector = inspect(engine)
        if not inspector.has_table('uploaded_files'):
            return jsonify({'success': False, 'error': '無檔案記錄'}), 404
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT original_filename, blob_name, table_name
                FROM uploaded_files 
                WHERE file_id = ? AND user_id = ?
            """, (file_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': '檔案不存在或無權限'}), 404
            
            original_filename, blob_name, table_name = result
            
            # 刪除 Cloud Storage 中的檔案（如果在雲端環境）
            if is_cloud_environment() and bucket is not None and blob_name:
                try:
                    blob = bucket.blob(blob_name)
                    blob.delete()
                except Exception as e:
                    print(f"[WARNING] Cloud Storage 檔案刪除失敗: {e}")
            
            # 刪除本地檔案（如果在本地環境）
            if not is_cloud_environment():
                local_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except Exception as e:
                        print(f"[WARNING] 本地檔案刪除失敗: {e}")
            
            # 刪除資料庫記錄
            cursor.execute("DELETE FROM uploaded_files WHERE file_id = ? AND user_id = ?", (file_id, user_id))
            
            # 可選：刪除對應的資料表
            if table_name:
                try:
                    session = Session()
                    session.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                    session.commit()
                    session.close()
                except Exception as e:
                    print(f"[WARNING] 資料表刪除失敗: {e}")
            
            conn.commit()
        
        # 刪除後自動備份資料庫
        backup_database_to_gcs()
        
        return jsonify({'success': True, 'message': '檔案已刪除'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backup', methods=['POST'])
@jwt_required()
def manual_backup():
    """手動備份資料庫到 Cloud Storage"""
    try:
        result = backup_database_to_gcs()
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # 支援 Cloud Run 環境變數
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
