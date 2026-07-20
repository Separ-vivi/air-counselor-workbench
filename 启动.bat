@echo off
chcp 936 >nul
title Air Counselor Workbench V5-h
cd /d "%~dp0"

echo ================================================
echo   Counselor Workbench V5-h (Portable)
echo   http://127.0.0.1:5000
echo ================================================
echo.

if not exist "python\python.exe" (
  echo [ERROR] python\python.exe not found
  pause
  exit /b 1
)

if not exist "data" mkdir data

echo [1/3] Starting backend server (same window)...
start /b python\python.exe backend\main.py

echo [2/3] Waiting for server ready (max 60s)...
set /a tries=0
:loop
if %tries% geq 30 goto timeout
timeout /t 2 /nobreak >nul
set /a tries+=1
powershell -Command "(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000)" 2>nul && goto ready
echo   Attempt %tries%/30...
goto loop

:timeout
echo [WARN] Server may not be ready. Check logs above for errors.
echo Press any key to exit...
pause >nul
exit /b 1

:ready
echo.
echo [OK] Server is ready on http://127.0.0.1:5000
echo [3/3] Opening browser...
start http://127.0.0.1:5000
echo.
echo ================================================
echo   Server running in this window.
echo   Backend logs will appear below.
echo   Close this window to stop server.
echo ================================================
echo.

REM Keep window alive so backend logs remain visible
:waitloop
timeout /t 600 /nobreak >nul
goto waitloop
