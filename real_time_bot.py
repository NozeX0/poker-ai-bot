#!/usr/bin/env python3
"""
🎮 REAL-TIME POKER AI BOT
Распознает карты с камеры и дает советы в реальном времени
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import pytesseract
import re
import json
import os
from core.game_engine import PokerEngine, GameState

# Путь к Tesseract (Windows)
try:
    pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except:
    pass

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# Инициализируем движок
engine = PokerEngine()

# История распознаваний
analysis_history = []

class CardRecognizer:
    """Распознаватель карт с камеры"""
    
    @staticmethod
    def extract_text_from_frame(frame):
        """Извлекает текст с кадра"""
        try:
            # Конвертируем в серый для лучшего распознавания
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Увеличиваем контрастность
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Распознаем текст
            text = pytesseract.image_to_string(enhanced)
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
    
    @staticmethod
    def parse_cards(text):
        """Парсит карты из текста"""
        text = text.upper()
        # Ищет паттерны AS, KH, QD, JC, TC, 9S и т.д.
        pattern = r'[AKQJT2-9][SHDC]'
        cards = re.findall(pattern, text)
        
        # Удаляем дубликаты
        seen = set()
        unique_cards = []
        for card in cards:
            if card not in seen:
                seen.add(card)
                unique_cards.append(card)
        
        return unique_cards
    
    @staticmethod
    def parse_numbers(text):
        """Парсит числа (банк, ставки, стеки)"""
        numbers = re.findall(r'\b\d+\.?\d*\b', text)
        return [float(n) for n in numbers]

class PokerAnalyzer:
    """Анализирует позицию"""
    
    def __init__(self):
        self.engine = engine
    
    def analyze_position(self, my_cards, board, pot, bet, stack, position, players):
        """Полный анализ позиции"""
        try:
            state = GameState(
                my_cards=my_cards,
                community_cards=board,
                pot_size=pot,
                bet_to_call=bet,
                my_stack=stack,
                opponent_stacks={i: 5000 for i in range(1, players)},
                position=position,
                players_count=players,
                street=self._determine_street(board)
            )
            
            recommendation = self.engine.analyze(state)
            return recommendation.to_dict()
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _determine_street(board):
        """Определяет улицу"""
        if not board:
            return 'preflop'
        elif len(board) == 3:
            return 'flop'
        elif len(board) == 4:
            return 'turn'
        else:
            return 'river'
    
    @staticmethod
    def get_possible_combinations(my_cards):
        """Возможные комбинации"""
        if len(my_cards) < 2:
            return []
        
        combinations = []
        
        # Проверяем пару
        if my_cards[0][0] == my_cards[1][0]:
            combinations.append({
                'type': 'PAIR',
                'cards': my_cards,
                'description': f'Пара {my_cards[0][0]}'
            })
        
        # Проверяем suited
        if my_cards[0][1] == my_cards[1][1]:
            combinations.append({
                'type': 'SUITED',
                'cards': my_cards,
                'description': f'Одной масти {my_cards[0][1]}'
            })
        
        # Проверяем broadway
        broadway = {'A', 'K', 'Q', 'J', 'T'}
        if my_cards[0][0] in broadway and my_cards[1][0] in broadway:
            combinations.append({
                'type': 'BROADWAY',
                'cards': my_cards,
                'description': 'Broadway карты'
            })
        
        # Проверяем connected
        ranks = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        if abs(ranks.get(my_cards[0][0], 0) - ranks.get(my_cards[1][0], 0)) == 1:
            combinations.append({
                'type': 'CONNECTED',
                'cards': my_cards,
                'description': 'Соседние карты'
            })
        
        return combinations

# ======================== ROUTES ========================

@app.route('/')
def index():
    """Главная страница"""
    return render_template('camera.html')

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Анализирует полученное изображение"""
    try:
        # Получаем изображение
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Конвертируем в OpenCV
        nparr = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        # Извлекаем текст
        text = CardRecognizer.extract_text_from_frame(frame)
        
        # Парсим данные
        cards = CardRecognizer.parse_cards(text)
        numbers = CardRecognizer.parse_numbers(text)
        
        # Если нет карт - возвращаем ошибку
        if len(cards) < 2:
            return jsonify({
                'error': 'Карты не распознаны',
                'raw_text': text,
                'cards_found': cards,
                'numbers_found': numbers
            }), 400
        
        # Разделяем карты: первые 2 - ваши, остальные - борд
        my_cards = cards[:2]
        board = cards[2:7]  # Максимум 5 карт на борде
        
        # Если нет чисел - используем значения по умолчанию
        pot = numbers[0] if len(numbers) > 0 else 100
        bet = numbers[1] if len(numbers) > 1 else 10
        stack = numbers[2] if len(numbers) > 2 else 1000
        
        # Анализируем
        analyzer = PokerAnalyzer()
        recommendation = analyzer.analyze_position(
            my_cards=my_cards,
            board=board,
            pot=pot,
            bet=bet,
            stack=stack,
            position='button',
            players=6
        )
        
        # Возможные комбинации
        combinations = analyzer.get_possible_combinations(my_cards)
        
        # Подготавливаем результат
        result = {
            'status': 'success',
            'recognized': {
                'my_cards': my_cards,
                'board': board,
                'pot': pot,
                'bet': bet,
                'stack': stack
            },
            'combinations': combinations,
            'recommendation': recommendation,
            'raw_text': text
        }
        
        # Сохраняем в историю
        analysis_history.append(result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/api/manual-analyze', methods=['POST'])
def api_manual_analyze():
    """Анализирует вручную введенные данные"""
    try:
        data = request.json
        
        analyzer = PokerAnalyzer()
        recommendation = analyzer.analyze_position(
            my_cards=data.get('my_cards', []),
            board=data.get('board', []),
            pot=float(data.get('pot', 100)),
            bet=float(data.get('bet', 10)),
            stack=float(data.get('stack', 1000)),
            position=data.get('position', 'button'),
            players=int(data.get('players', 6))
        )
        
        combinations = analyzer.get_possible_combinations(data.get('my_cards', []))
        
        return jsonify({
            'status': 'success',
            'combinations': combinations,
            'recommendation': recommendation
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Возвращает историю анализов"""
    return jsonify({
        'history': analysis_history[-10:],  # Последние 10
        'total': len(analysis_history)
    })

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Очищает историю"""
    global analysis_history
    analysis_history = []
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎮 POKER AI BOT - REAL-TIME MODE")
    print("="*70)
    print("\n📱 Откройте на телефоне:")
    print("   http://YOUR_PC_IP:5000")
    print("\n📷 Система работает:")
    print("   ✅ Распознавание карт с камеры")
    print("   ✅ Анализ в реальном времени")
    print("   ✅ Рекомендации на экране")
    print("   ✅ История анализов")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
