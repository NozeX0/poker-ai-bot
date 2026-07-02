#!/usr/bin/env python3
"""
iOS Mobile App с интеграцией AI анализа и live overlay
Полностью автоматическое распознавание и рекомендации
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime
import base64
import cv2
import numpy as np

from ios.vision_engine import VisionEngine, PokerTableState
from core.game_engine import PokerEngine, GameState, Recommendation

class MobilePokerApp:
    """iOS приложение для покера с live анализом"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                         template_folder='ios/templates',
                         static_folder='ios/static')
        CORS(self.app)
        
        self.vision_engine = VisionEngine(use_gpu=True)
        self.poker_engine = PokerEngine()
        
        self.current_recommendation: dict = {}
        self.current_frame = None
        self.is_analyzing = False
        
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.route('/')
        def index():
            """Главная страница"""
            return render_template('mobile.html')
        
        @self.app.route('/api/start-vision', methods=['POST'])
        def start_vision():
            """Запустить распознавание карт"""
            if not self.is_analyzing:
                self.is_analyzing = True
                
                # Запускаем анализ в отдельном потоке
                analysis_thread = threading.Thread(
                    target=self._vision_analysis_loop,
                    daemon=True
                )
                analysis_thread.start()
                
                return jsonify({'status': 'started'})
            return jsonify({'status': 'already_running'})
        
        @self.app.route('/api/stop-vision', methods=['POST'])
        def stop_vision():
            """Остановить распознавание"""
            self.is_analyzing = False
            self.vision_engine.stop_stream_analysis()
            return jsonify({'status': 'stopped'})
        
        @self.app.route('/api/stream')
        def stream_video():
            """Видео поток с overlay рекомендаций"""
            return Response(
                self._generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/api/recommendation')
        def get_recommendation():
            """Получить текущую рекомендацию"""
            return jsonify(self.current_recommendation)
        
        @self.app.route('/api/analyze-frame', methods=['POST'])
        def analyze_frame():
            """Анализировать отправленный кадр"""
            try:
                data = request.json
                frame_base64 = data.get('frame')
                
                # Декодируем base64
                frame_data = base64.b64decode(frame_base64)
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Анализируем кадр
                detected_cards = self.vision_engine.detect_cards_in_frame(frame)
                
                # Создаём рекомендацию
                if len(detected_cards) >= 2:
                    my_cards = [f"{c.rank}{c.suit}" for c in detected_cards[:2]]
                    community_cards = [f"{c.rank}{c.suit}" for c in detected_cards[2:]]
                    
                    # Анализируем через AI
                    recommendation = self._get_ai_recommendation(
                        my_cards,
                        community_cards,
                        data.get('pot', 1000),
                        data.get('bet', 0),
                        data.get('stack', 5000),
                        data.get('position', 'button')
                    )
                    
                    self.current_recommendation = recommendation
                    
                    return jsonify({
                        'status': 'success',
                        'cards_detected': len(detected_cards),
                        'recommendation': recommendation
                    })
                
                return jsonify({
                    'status': 'error',
                    'message': 'Not enough cards detected'
                }), 400
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/quick-analysis', methods=['POST'])
        def quick_analysis():
            """Быстрый анализ без распознавания"""
            try:
                data = request.json
                
                recommendation = self._get_ai_recommendation(
                    data.get('my_cards', []),
                    data.get('community_cards', []),
                    data.get('pot', 1000),
                    data.get('bet', 0),
                    data.get('stack', 5000),
                    data.get('position', 'button')
                )
                
                return jsonify(recommendation)
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
    
    def _get_ai_recommendation(self, my_cards, community_cards, pot, bet, stack, position):
        """
        Получить AI рекомендацию
        
        Args:
            my_cards: Список ['AS', 'KH', ...]
            community_cards: Список карт на столе
            pot: Размер банка
            bet: Текущая ставка
            stack: Мой стек
            position: Позиция за столом
        
        Returns:
            Словарь с рекомендацией
        """
        try:
            # Создаём состояние игры
            state = GameState(
                my_cards=my_cards,
                community_cards=community_cards,
                pot_size=float(pot),
                bet_to_call=float(bet),
                my_stack=float(stack),
                opponent_stacks={i: 5000 for i in range(1, 6)},
                position=position,
                players_count=6,
                street=self._detect_street(len(community_cards))
            )
            
            # Анализируем
            recommendation = self.poker_engine.analyze(state)
            
            return {
                'status': 'success',
                'action': recommendation.action,
                'confidence': recommendation.confidence,
                'equity': recommendation.equity,
                'ev': recommendation.ev,
                'bet_size': recommendation.suggested_bet_size,
                'reason': recommendation.reasoning,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _vision_analysis_loop(self):
        """Основной цикл анализа"""
        def on_frame_analyzed(state: PokerTableState, frame):
            # Получаем рекомендацию
            if state.my_cards and len(state.my_cards) >= 2:
                my_cards = [f"{c.rank}{c.suit}" for c in state.my_cards[:2]]
                community_cards = [f"{c.rank}{c.suit}" for c in state.community_cards]
                
                self.current_recommendation = self._get_ai_recommendation(
                    my_cards,
                    community_cards,
                    state.pot_size,
                    state.current_bet,
                    5000,  # Default stack
                    state.position
                )
                
                self.current_frame = frame
        
        # Запускаем видеопоток
        self.vision_engine.start_stream_analysis(camera_source=0, callback=on_frame_analyzed)
    
    def _generate_frames(self):
        """Генерировать видео фреймы с overlay"""
        while self.is_analyzing:
            if self.current_frame is not None:
                frame = self.current_frame.copy()
                
                # Добавляем overlay с рекомендацией
                frame = self._draw_recommendation_overlay(frame)
                
                # Кодируем в JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                       frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    def _draw_recommendation_overlay(self, frame):
        """
        Рисовать overlay с рекомендацией на видео
        
        Args:
            frame: Видео кадр
        
        Returns:
            Кадр с overlay
        """
        if not self.current_recommendation or self.current_recommendation.get('status') != 'success':
            return frame
        
        rec = self.current_recommendation
        h, w = frame.shape[:2]
        
        # Фон для информации
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (w-10, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Цвет в зависимости от действия
        action_color = {
            'FOLD': (0, 0, 255),      # Красный
            'CALL': (0, 165, 255),    # Оранжевый
            'RAISE': (0, 255, 0),     # Зелёный
            'CHECK': (255, 255, 0),   # Голубой
            'BET': (0, 255, 0)        # Зелёный
        }
        
        action = rec.get('action', 'UNKNOWN')
        color = action_color.get(action, (255, 255, 255))
        
        # Основное действие (большой текст)
        cv2.putText(frame, f"Action: {action}", (20, 50),
                    cv2.FONT_HERSHEY_BOLD, 1.5, color, 3)
        
        # Доп информация
        confidence = int(rec.get('confidence', 0) * 100)
        cv2.putText(frame, f"Confidence: {confidence}%", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        equity = f"{rec.get('equity', 0):.1f}%"
        cv2.putText(frame, f"Equity: {equity}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        ev = f"${rec.get('ev', 0):.2f}"
        cv2.putText(frame, f"EV: {ev}", (20, 135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Причина (внизу)
        reason = rec.get('reason', 'No reason')[:50]  # Первые 50 символов
        cv2.putText(frame, f"Reason: {reason}", (10, h-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame
    
    def _detect_street(self, community_cards_count: int) -> str:
        """Определить улицу по количеству карт"""
        if community_cards_count == 0:
            return 'preflop'
        elif community_cards_count == 3:
            return 'flop'
        elif community_cards_count == 4:
            return 'turn'
        else:
            return 'river'
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Запустить приложение"""
        print("\n" + "="*70)
        print("🤖 POKER AI BOT - iOS Real-Time Vision Edition")
        print("="*70)
        print(f"\n✅ Сервер запущен на http://{host}:{port}")
        print(f"📱 Откройте на мобильном: http://YOUR_IP:{port}")
        print("\n💡 Функции:")
        print("   ✓ Real-time card detection")
        print("   ✓ Live AI recommendations")
        print("   ✓ Instant overlay with best moves")
        print("   ✓ Automatic stake suggestions")
        print("\n" + "="*70 + "\n")
        
        self.app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    mobile_app = MobilePokerApp()
    mobile_app.run()
