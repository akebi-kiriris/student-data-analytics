# 使用官方 Python 3.11 鏡像作為基礎
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（合併安裝 pg8000 需要的依賴）
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# 首先複製並安裝依賴
COPY requirements-cloud.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-cloud.txt && \
    rm -f requirements-cloud.txt


# 複製應用程式碼與資料庫
COPY app.py ./

# 複製資料庫目錄
COPY database/ ./database/

# build 時顯示 database/ 內容
RUN ls -l ./database || true

# 建立必要的目錄並設定權限
RUN mkdir -p uploads database
RUN chmod 755 uploads database

# 設定環境變數
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露 Cloud Run 使用的預設端口
EXPOSE 8080

# 直接使用 gunicorn 啟動，避免用戶權限問題
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "300", "--preload", "app:app"]