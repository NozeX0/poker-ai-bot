#!/usr/bin/env python3
"""
Рапуск iOS приложения для реального анализа покера в реальном времени

Usage:
    python ios/run_mobile.py
"""

import sys
import os

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios.mobile_app import MobilePokerApp

if __name__ == '__main__':
    app = MobilePokerApp()
    app.run(host='0.0.0.0', port=5000, debug=True)
