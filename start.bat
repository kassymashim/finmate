@echo off
echo ============================================
echo   FinMate - AI Personal Finance Assistant
echo ============================================
echo.
echo Starting backend API server...
start "FinMate Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.api:app --host 0.0.0.0 --port 8003 --reload"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting frontend...
start "FinMate Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo Waiting for frontend to start...
timeout /t 8 /nobreak >nul

echo.
echo ============================================
echo   FinMate is ready!
echo   Open: http://localhost:3000
echo ============================================
echo.
start http://localhost:3000
pause
