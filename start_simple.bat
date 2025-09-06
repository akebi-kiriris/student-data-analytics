@echo off
REM Simple version without Chinese characters
cd /d "%~dp0"

echo Starting Flask Backend...
start "Backend" cmd /k "cd backend && python app.py"

timeout /t 3 /nobreak > nul

echo Starting Vue Frontend...  
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
pause
