@echo off
chcp 65001 > nul
title 辅导员工作平台
echo ===============================================
echo   辅导员工作平台 · 便携版
echo   启动后将自动打开 http://127.0.0.1:8000
echo ===============================================
echo.
cd /d "%~dp0"
set DEPLOY_RUN_PORT=8000

if not exist "python\python.exe" (
  echo [错误] 未找到内置 Python 运行时 python\python.exe
  echo 请重新解压完整压缩包，不要只复制部分文件。
  pause
  exit /b 1
)

if not exist "backend\main.py" (
  echo [错误] 未找到 backend\main.py
  echo 请确认压缩包已完整解压。
  pause
  exit /b 1
)

echo [1/3] 正在启动后端服务...
start "ACW-Backend" /b "%~dp0python\python.exe" "%~dp0backend\main.py"

echo [2/3] 等待服务就绪（最多 60 秒）...
set /a tries=0
:loop
if %tries% geq 30 goto timeout
timeout /t 2 /nobreak >nul
set /a tries+=1
powershell -Command "(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',8000)" 2>nul && goto ready
echo   等待中... 尝试 %tries%/30
goto loop

:timeout
echo.
echo [警告] 服务在 60 秒内未就绪，请检查弹出的后端窗口日志。
echo 按任意键打开浏览器（若服务稍后启动）...
pause >nul
start http://127.0.0.1:8000
exit /b 0

:ready
echo.
echo [成功] 服务已就绪: http://127.0.0.1:8000
echo [3/3] 打开浏览器...
start http://127.0.0.1:8000
echo.
echo ===============================================
echo   服务运行中，关闭本窗口将停止服务。
echo ===============================================
echo.

:waitloop
timeout /t 600 /nobreak >nul
goto waitloop
