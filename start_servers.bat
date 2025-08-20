@echo off
echo 正在啟動學生數據分析系統...
echo.

REM 設定當前目錄為 project 資料夾
cd /d "%~dp0"

echo ========================================
echo 啟動後端服務器 (Flask)
echo ========================================
start "後端服務器" cmd /k "cd backend && python app.py"

echo 等待後端服務器啟動...
timeout /t 3 /nobreak > nul

echo ========================================
echo 啟動前端服務器 (Vue + Vite)
echo ========================================
start "前端服務器" cmd /k "cd frontend && npm run dev"

echo.
echo 系統正在啟動中...
echo 後端服務器: http://localhost:5000
echo 前端服務器: http://localhost:5173 (通常是這個端口)
echo.
echo 關閉此視窗不會影響服務器運行
echo 要停止服務器，請關閉對應的命令提示字元視窗
echo.
pause
