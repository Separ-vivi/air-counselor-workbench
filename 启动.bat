@echo off
chcp 936 >nul
title Air Counselor Workbench V5-f
cd /d "%~dp0"

echo ================================================
echo   Counselor Workbench V5-f (Portable)
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

echo [1/3] Starting backend...
start /B "" "%~dp0python\python.exe" "%~dp0backend\main.py"

echo [2/3] Waiting for server ready...
set /a tries=0
:loop
if %tries% geq 30 goto timeout
timeout /t 2 /nobreak >nul
set /a tries+=1
powershell -Command "(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000)" 2>nul && goto ready
goto loop

:timeout
echo [ERROR] Server startup timeout
pause
exit /b 1

:ready
echo [3/3] Opening browser...
start "" http://127.0.0.1:5000
echo.
echo Server is running. Close this window to stop.
echo.
pause >nul
taskkill /F /FI "WINDOWTITLE eq Air Counselor Workbench V5-f" >nul 2>&1
