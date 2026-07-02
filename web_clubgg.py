#!/usr/bin/env python3
"""
🌐 Web Interface для ClubGG AI Overlay
Добавляет веб-интерфейс для мониторинга и управления
"""

from flask import Flask, render_template, jsonify, request
from clubgg_overlay import ClubGGOverlay
import threading
import json

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

# Глобальный экземпляр overlay
overlay = None
overlay_thread = None

@app.route('/')
def index():
    """Главная страница"""
    return render_template('clubgg_dashboard.html')

@app.route('/api/status')
def get_status():
    """Получить статус"""
    if overlay:
        return jsonify({
            'running': overlay.is_running,
            'recommendation': overlay.current_recommendation,
            'active': overlay.overlay_active
        })
    return jsonify({'running': False})

@app.route('/api/start', methods=['POST'])
def start_overlay():
    """Запустить оверлей"""
    global overlay, overlay_thread
    
    if not overlay:
        overlay = ClubGGOverlay()
    
    if not overlay.is_running:
        overlay.start()
        return jsonify({'status': 'started'})
    
    return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_overlay():
    """Остановить оверлей"""
    if overlay:
        overlay.stop()
        return jsonify({'status': 'stopped'})
    
    return jsonify({'status': 'not_running'})

@app.route('/api/toggle-overlay', methods=['POST'])
def toggle_overlay():
    """Включить/выключить оверлей"""
    if overlay:
        overlay.overlay_active = not overlay.overlay_active
        return jsonify({'active': overlay.overlay_active})
    
    return jsonify({'error': 'Not running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
