@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cls

echo.
echo =====================================================================
echo 🎯 GTO MIND - ClubGG Live Poker AI Overlay
echo =====================================================================
echo.

REM Получаем IP
for /f "tokens=2 delims=: " %%A in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "IP=%%A"
)

echo ✅ IP адрес: %IP%
echo.
echo 📋 ШАГ 1: Откройте ClubGG в браузере
echo 📋 ШАГ 2: Запустите этот скрипт
echo 📋 ШАГ 3: Подождите пока приложение начнет анализировать
echo.
echo ⚠️  ВНИМАНИЕ:
echo    - Использование на реальных деньгах = БАН!
echo    - Используйте только на обучение
echo    - Нажимите CTRL+C для выхода
echo.
echo =====================================================================
echo.
echo Запускаю AI Overlay...
echo.

python clubgg_overlay.py

pause
