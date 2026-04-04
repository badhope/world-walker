@echo off
chcp 65001 >nul
title 国家经济数据分析平台

echo ========================================
echo   国家经济数据分析平台 - 启动器
echo ========================================
echo.

REM 设置 Python 路径
set PYTHON=C:\Users\MI\AppData\Local\Programs\Python\Python312\python.exe
set PROJECT_DIR=%~dp0

REM 检查 Python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.12
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
cd /d %PROJECT_DIR%
%PYTHON% -m pip install -r requirements.txt --quiet

echo [2/3] 启动后端 API 服务...
start "NEDAP Backend" /min cmd /c "%PYTHON% -m uvicorn backend.main:app --host 127.0.0.1 --port 8001"

echo 等待后端启动...
timeout /t 3 /nobreak >nul

echo [3/3] 启动前端界面...
start "NEDAP Frontend" /min cmd /c "%PYTHON% -m streamlit run app/streamlit_app.py --server.port 8501 --server.headless true"

echo.
echo ========================================
echo   服务已启动！
echo   后端 API: http://localhost:8001
echo   前端界面: http://localhost:8501
echo ========================================
echo.
echo 按任意键打开浏览器访问前端界面...
pause >nul

start http://localhost:8501

echo.
echo 按任意键关闭所有服务...
pause >nul

REM 关闭服务
taskkill /fi "WindowTitle eq NEDAP Backend*" /f >nul 2>&1
taskkill /fi "WindowTitle eq NEDAP Frontend*" /f >nul 2>&1

echo 服务已关闭。
