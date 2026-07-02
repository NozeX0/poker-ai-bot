@echo off
chcp 65001 >nul

cls

echo.
echo =====================================================================
echo 📦 GTO MIND - ClubGG Installation
echo =====================================================================
echo.

echo ⏳ Установка Python зависимостей...
echo.

pip install -r requirements-clubgg.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ ОШИБКА при установке зависимостей!
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Зависимости установлены!
echo.
echo =====================================================================
echo.
echo 🎯 Следующий шаг: Установите Tesseract OCR
echo.
echo Windows:
  echo   1. Скачайте: https://github.com/UB-Mannheim/tesseract/wiki
  echo   2. Установите tesseract-ocr-w64-v5.x.exe
  echo   3. Нажмите Install (по умолчанию)
  echo   4. Перезагрузитесь
echo.
echo Когда установите Tesseract - запустите:
  echo   python clubgg_overlay.py
echo.
echo =====================================================================
echo.
pause
