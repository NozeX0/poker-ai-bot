#!/bin/bash

echo ""
echo "====================================================================="
echo "🎯 GTO MIND - ClubGG Live Poker AI Overlay"
echo "====================================================================="
echo ""

# Получаем IP для macOS/Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    IP=$(ipconfig getifaddr en0)
else
    IP=$(hostname -I | awk '{print $1}')
fi

echo "✅ IP адрес: $IP"
echo ""
echo "📋 ШАГ 1: Откройте ClubGG в браузере"
echo "📋 ШАГ 2: Запустите этот скрипт"
echo "📋 ШАГ 3: Подождите пока приложение начнет анализировать"
echo ""
echo "⚠️  ВНИМАНИЕ:"
echo "   - Использование на реальных деньгах = БАН!"
echo "   - Используйте только на обучение"
echo "   - Нажимите CTRL+C для выхода"
echo ""
echo "====================================================================="
echo ""
echo "Запускаю AI Overlay..."
echo ""

python3 clubgg_overlay.py
