#!/usr/bin/env python3
"""
📱 GTO MIND AI - Complete Mobile Solution
Полностью работающее решение для iOS/Android
Поддерживает основные и реальные столы
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import json
import os
from datetime import datetime
import uuid
import base64
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

# Import poker engine
from core.game_engine import PokerEngine, GameState

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'gto-mind-ai-secret-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

poker_engine = PokerEngine()

# Store active sessions
active_sessions = {}
analysis_history = {}

class PokerAISession:
    """Сессия анализа покера"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.is_active = False
        self.current_recommendation = None
        self.history = []
        self.stats = {
            'total_hands': 0,
            'folds': 0,
            'calls': 0,
            'raises': 0,
            'checks': 0,
            'bets': 0,
            'avg_confidence': 0,
            'avg_equity': 0
        }
        self.created_at = datetime.now()
        self.last_update = datetime.now()
    
    def add_recommendation(self, rec):
        """Добавить рекомендацию в историю"""
        if rec:
            self.history.append(rec)
            self.current_recommendation = rec
            self.last_update = datetime.now()
            
            # Обновляем статистику
            action = rec.get('action', '').lower()
            self.stats['total_hands'] += 1
            if action == 'fold':
                self.stats['folds'] += 1
            elif action == 'call':
                self.stats['calls'] += 1
            elif action == 'raise':
                self.stats['raises'] += 1
            elif action == 'check':
                self.stats['checks'] += 1
            elif action == 'bet':
                self.stats['bets'] += 1
            
            # Средние значения
            confidences = [r.get('confidence', 0) for r in self.history]
            equities = [r.get('equity', 0) for r in self.history]
            self.stats['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0
            self.stats['avg_equity'] = sum(equities) / len(equities) if equities else 0
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'is_active': self.is_active,
            'current_recommendation': self.current_recommendation,
            'history_count': len(self.history),
            'stats': self.stats,
            'created_at': self.created_at.isoformat(),
            'last_update': self.last_update.isoformat()
        }

# Routes

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Панель управления"""
    return render_template('dashboard.html')

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Создать новую сессию анализа"""
    session_id = str(uuid.uuid4())
    session = PokerAISession(session_id)
    active_sessions[session_id] = session
    analysis_history[session_id] = []
    
    return jsonify({
        'status': 'created',
        'session_id': session_id,
        'data': session.to_dict()
    })

@app.route('/api/session/<session_id>/analyze', methods=['POST'])
def analyze_hand(session_id):
    """Анализировать руку"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = request.json
        
        # Парсим карты
        my_cards = data.get('my_cards', [])[:2]
        community_cards = data.get('community_cards', [])
        pot = float(data.get('pot', 0))
        bet = float(data.get('bet', 0))
        stack = float(data.get('stack', 5000))
        position = data.get('position', 'button')
        players = int(data.get('players_count', 6))
        
        # Определяем улицу
        if len(community_cards) == 0:
            street = 'preflop'
        elif len(community_cards) == 3:
            street = 'flop'
        elif len(community_cards) == 4:
            street = 'turn'
        else:
            street = 'river'
        
        # Создаем состояние игры
        state = GameState(
            my_cards=my_cards,
            community_cards=community_cards,
            pot_size=pot,
            bet_to_call=bet,
            my_stack=stack,
            opponent_stacks={i: 5000 for i in range(1, players)},
            position=position,
            players_count=players,
            street=street
        )
        
        # Анализируем
        recommendation = poker_engine.analyze(state)
        
        rec_dict = {
            'action': recommendation.action.upper(),
            'confidence': float(recommendation.confidence),
            'equity': float(recommendation.equity),
            'ev': float(recommendation.ev),
            'win_rate': float(recommendation.win_rate),
            'pot_odds': float(recommendation.pot_odds),
            'reasoning': recommendation.reasoning,
            'bet_size': float(recommendation.suggested_bet_size) if recommendation.suggested_bet_size else None,
            'timestamp': datetime.now().isoformat(),
            'my_cards': my_cards,
            'community_cards': community_cards,
            'street': street,
            'pot': pot,
            'position': position
        }
        
        # Сохраняем в сессию
        session = active_sessions[session_id]
        session.add_recommendation(rec_dict)
        analysis_history[session_id].append(rec_dict)
        
        return jsonify({
            'status': 'success',
            'recommendation': rec_dict,
            'session': session.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/session/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """Получить историю анализов"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'status': 'success',
        'history': analysis_history.get(session_id, []),
        'session': active_sessions[session_id].to_dict()
    })

@app.route('/api/session/<session_id>/stats', methods=['GET'])
def get_stats(session_id):
    """Получить статистику сессии"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = active_sessions[session_id]
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'stats': session.stats
    })

@app.route('/api/session/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Экспортировать сессию в JSON"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = active_sessions[session_id]
    export_data = {
        'session': session.to_dict(),
        'history': analysis_history.get(session_id, []),
        'export_date': datetime.now().isoformat()
    }
    
    return jsonify(export_data)

@app.route('/api/quick-analyze', methods=['POST'])
def quick_analyze():
    """Быстрый анализ без сессии"""
    try:
        data = request.json
        
        my_cards = data.get('my_cards', [])[:2]
        community_cards = data.get('community_cards', [])
        pot = float(data.get('pot', 0))
        bet = float(data.get('bet', 0))
        stack = float(data.get('stack', 5000))
        position = data.get('position', 'button')
        players = int(data.get('players_count', 6))
        
        if len(community_cards) == 0:
            street = 'preflop'
        elif len(community_cards) == 3:
            street = 'flop'
        elif len(community_cards) == 4:
            street = 'turn'
        else:
            street = 'river'
        
        state = GameState(
            my_cards=my_cards,
            community_cards=community_cards,
            pot_size=pot,
            bet_to_call=bet,
            my_stack=stack,
            opponent_stacks={i: 5000 for i in range(1, players)},
            position=position,
            players_count=players,
            street=street
        )
        
        recommendation = poker_engine.analyze(state)
        
        return jsonify({
            'status': 'success',
            'action': recommendation.action.upper(),
            'confidence': float(recommendation.confidence),
            'equity': float(recommendation.equity),
            'ev': float(recommendation.ev),
            'reasoning': recommendation.reasoning,
            'bet_size': float(recommendation.suggested_bet_size) if recommendation.suggested_bet_size else None
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/health', methods=['GET'])
def health():
    """Проверка здоровья сервера"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(active_sessions),
        'version': '2.0.0'
    })

# WebSocket events

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('response', {'data': 'Connected to GTO MIND AI'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('analyze')
def handle_analyze(data):
    """WebSocket анализ в реальном времени"""
    try:
        my_cards = data.get('my_cards', [])[:2]
        community_cards = data.get('community_cards', [])
        pot = float(data.get('pot', 0))
        bet = float(data.get('bet', 0))
        stack = float(data.get('stack', 5000))
        position = data.get('position', 'button')
        players = int(data.get('players_count', 6))
        
        if len(community_cards) == 0:
            street = 'preflop'
        elif len(community_cards) == 3:
            street = 'flop'
        elif len(community_cards) == 4:
            street = 'turn'
        else:
            street = 'river'
        
        state = GameState(
            my_cards=my_cards,
            community_cards=community_cards,
            pot_size=pot,
            bet_to_call=bet,
            my_stack=stack,
            opponent_stacks={i: 5000 for i in range(1, players)},
            position=position,
            players_count=players,
            street=street
        )
        
        recommendation = poker_engine.analyze(state)
        
        emit('recommendation', {
            'action': recommendation.action.upper(),
            'confidence': float(recommendation.confidence),
            'equity': float(recommendation.equity),
            'ev': float(recommendation.ev),
            'reasoning': recommendation.reasoning,
            'bet_size': float(recommendation.suggested_bet_size) if recommendation.suggested_bet_size else None,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🤖 GTO MIND AI - Complete Mobile Solution")
    print("="*70)
    print(f"\n✅ Порт: 5000")
    print(f"✅ Откройте: http://localhost:5000")
    print(f"📱 На мобильном: http://YOUR_IP:5000")
    print("\n" + "="*70 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
