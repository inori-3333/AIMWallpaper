@echo off
chcp 65001 >nul
title AIMWallpaper - Starting...

echo ========================================
echo   AIMWallpaper 一键启动
echo ========================================
echo.

:: 启动后端
echo [1/2] 启动后端 (FastAPI)...
start "AIMWallpaper Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 启动前端
echo [2/2] 启动前端 (Vite)...
start "AIMWallpaper Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   前后端已启动！
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo ========================================
echo.
echo 关闭此窗口不会停止服务。
echo 如需停止，请关闭对应的命令行窗口。
pause
