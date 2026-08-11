@echo off
chcp 65001 >nul
echo ============================================
echo  心理健康项目 - 启动 Django 服务
echo ============================================
echo.

:: 激活虚拟环境
call venv38\Scripts\activate.bat

echo 服务启动中...
echo 管理后台: http://localhost:8080/admin/dist/index.html
echo 用户端H5: http://localhost:8080/front/index.html
echo.
echo 按 Ctrl+C 停止服务
echo ============================================

python manage.py runserver --insecure 0.0.0.0:8080 --noreload
pause
