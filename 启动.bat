@echo off
chcp 936 >nul
title Air Counselor Workbench V5-g
cd /d "%~dp0"

echo ================================================
echo   Counselor Workbench V5-g (Portable)
echo   http://127.0.0.1:5000
echo   Close this window to stop server
echo ================================================
echo.

if not exist "python\python.exe" (
    echo [ERROR] python\python.exe not found
    pause
    exit /b 1
)

if not exist "data" mkdir data

echo [1/2] Opening browser in 3 seconds...
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"

echo [2/2] Starting backend server...
echo.
python\python.exe backend\main.py

echo.
echo [Server stopped]
pause
