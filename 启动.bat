@echo off
chcp 936 >nul 2>&1
title 辅导员工作平台 V5-c
cd /d "%~dp0"

echo ================================================
echo   辅导员工作平台 - V5-c  (便携版)
echo   端口 http://127.0.0.1:5000
echo   启动后自动打开浏览器
echo   关闭本窗口即停止服务
echo ================================================
echo.

:: 先启动后端（后台）
start /B "" cmd /c "cd backend && ..\python\python.exe main.py"

:: 等待端口 5000 就绪
echo [启动] 正在等待服务就绪...
:waitloop
powershell -Command "try { $c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 5000); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto waitloop
)

echo [就绪] 服务已启动，正在打开浏览器...
timeout /t 1 /nobreak >nul
start "" http://127.0.0.1:5000

echo.
echo [运行中] 浏览器已打开，关闭本窗口即停止服务
echo.

:: 阻塞主窗口，关闭时 kill 后端
pause >nul
taskkill /F /FI "WINDOWTITLE eq 辅导员工作平台 V5-c" >nul 2>&1