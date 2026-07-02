#!/bin/bash

echo ""
echo "======================================================================"
echo "🤖 GTO MIND AI - Complete Mobile Solution"
echo "======================================================================"
echo ""

echo "⏳ Установка зависимостей..."
echo ""

pip install -r requirements.txt
pip install flask-socketio python-socketio python-engineio

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ОШИБКА!"
    exit 1
fi

echo ""
echo "✅ Окей!"
echo ""
echo "Запустите:"
echo ""
echo "  python3 complete_mobile_app.py"
echo ""
echo "На iPhone откройте:"
echo ""
echo "  http://YOUR_IP:5000"
echo ""
echo "======================================================================"
echo ""
