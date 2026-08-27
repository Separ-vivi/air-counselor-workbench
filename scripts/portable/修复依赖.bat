@echo off
chcp 65001 > nul
title 修复依赖
echo ===============================================
echo   便携版依赖修复（正常情况下无需运行）
echo ===============================================
cd /d "%~dp0"
if not exist "python\python.exe" (
  echo [错误] 未找到 python\python.exe
  pause
  exit /b 1
)
echo 正在安装 pip ...
"%~dp0python\python.exe" -c "import sys;print(sys.version)"
curl -sL "https://bootstrap.pypa.io/get-pip.py" -o "%TEMP%\get-pip.py"
"%~dp0python\python.exe" "%TEMP%\get-pip.py"
echo.
echo 正在安装依赖 ...
"%~dp0python\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo 依赖修复完成。
pause
