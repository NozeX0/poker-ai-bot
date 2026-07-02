@echo off
chcp 65001 >nul
cls

echo.
echo ======================================================================
echo 🤖 GTO MIND AI - Complete Mobile Solution
echo ======================================================================
echo.

echo ⏳ Установка зависимостей...
echo.

pip install -r requirements.txt
pip install flask-socketio python-socketio python-engineio

if %errorlevel% neq 0 (
    echo.
    echo ❌ ОШИБКА!
    pause
    exit /b 1
)

echo.
echo ✅ Окей!
echo.
echo Откройте консоль и введите:
echo.
echo   python complete_mobile_app.py
echo.
echo На iPhone откройте:
echo.
echo   http://YOUR_IP:5000
echo.
echo ======================================================================
echo.
pause
