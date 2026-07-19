@echo off
chcp 936 >nul
title Air Counselor Workbench V5-g
cd /d "%~dp0"

echo ================================================
echo   Counselor Workbench V5-g (Portable)
echo   http://127.0.0.1:5000
echo ================================================
echo.

if not exist "python\python.exe" (
echo [ERROR] python\python.exe not found
pause
exit /b 1
)

if not exist "data" mkdir data

echo [1/3] Starting backend server...
start "Counselor-Backend" python\python.exe backend\main.py

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
echo [WARN] Server may not be ready, opening browser anyway...
goto openbrowser

:ready
echo [OK] Server is ready!

:openbrowser
echo [3/3] Opening browser...
start http://127.0.0.1:5000
echo.
echo Server is running.
echo Close the "Counselor-Backend" window to stop.
echo.
pause
