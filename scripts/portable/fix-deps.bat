@echo off
title Fix Dependencies
cd /d "%~dp0"

echo ===============================================
echo   Portable Dependencies Repair
echo   (Only run this if the app fails to start)
echo ===============================================
echo.

if not exist "python\python.exe" (
  echo [ERROR] python\python.exe not found
  pause
  exit /b 1
)

echo Installing pip...
"%~dp0python\python.exe" -c "import sys;print(sys.version)"
curl -sL "https://bootstrap.pypa.io/get-pip.py" -o "%TEMP%\get-pip.py"
"%~dp0python\python.exe" "%TEMP%\get-pip.py"
echo.
echo Installing dependencies...
"%~dp0python\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo Dependencies repair complete.
pause
