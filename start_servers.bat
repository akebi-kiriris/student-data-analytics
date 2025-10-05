@echo off
chcp 65001 > nul
echo Starting Student Data Analytics System...
echo.

REM Set current directory to project folder
cd /d "%~dp0"

echo ========================================
echo Starting Backend Server (Flask)
echo ========================================
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python app.py"

echo Waiting for backend server to start...
timeout /t 3 /nobreak > nul

echo ========================================
echo Starting Frontend Server (Vue + Vite)
echo ========================================
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo System is starting...
echo Backend Server: http://localhost:5000
echo Frontend Server: http://localhost:5173 (usually this port)
echo.
echo Closing this window will not affect the servers
echo To stop servers, close the corresponding command prompt windows
echo.
pause
