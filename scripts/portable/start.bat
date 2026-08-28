@echo off
title Counselor Workbench
cd /d "%~dp0"
set DEPLOY_RUN_PORT=5000

echo ===============================================
echo   Counselor Workbench - Portable Edition
echo   Will open http://127.0.0.1:5000
echo ===============================================
echo.

if not exist "python\python.exe" (
  echo [ERROR] Python runtime not found: python\python.exe
  echo Please re-extract the full zip archive.
  pause
  exit /b 1
)

if not exist "backend\main.py" (
  echo [ERROR] backend\main.py not found.
  echo Please make sure the archive is fully extracted.
  pause
  exit /b 1
)

echo [1/3] Starting backend service...
start "ACW-Backend" /b "%~dp0python\python.exe" "%~dp0backend\main.py"

echo [2/3] Waiting for service (up to 60 seconds)...
set /a tries=0
:loop
if %tries% geq 30 goto timeout
timeout /t 2 /nobreak >nul
set /a tries+=1
powershell -Command "(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000)" 2>nul && goto ready
echo   Waiting... attempt %tries%/30
goto loop

:timeout
echo.
echo [WARN] Service did not become ready within 60 seconds.
echo Check the backend window for error logs.
echo Press any key to open browser anyway...
pause >nul
start http://127.0.0.1:5000
exit /b 0

:ready
echo.
echo [OK] Service is ready: http://127.0.0.1:5000
echo [3/3] Opening browser...
start http://127.0.0.1:5000
echo.
echo ===============================================
echo   Service is running. Close this window to stop.
echo ===============================================
echo.

:waitloop
timeout /t 600 /nobreak >nul
goto waitloop
