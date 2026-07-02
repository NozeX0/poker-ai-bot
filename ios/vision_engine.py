#!/usr/bin/env python3
"""
iOS Real-Time Vision Engine for Poker Card Recognition
Автоматическое распознавание карт в реальном времени
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import pytesseract
from dataclasses import dataclass
import threading
import time

@dataclass
class DetectedCard:
    """Обнаруженная карта"""
    rank: str  # A, 2-9, T, J, Q, K
    suit: str  # ♠ ♥ ♦ ♣
    confidence: float
    position: Tuple[int, int, int, int]  # x1, y1, x2, y2

@dataclass
class PokerTableState:
    """Состояние покер-стола"""
    my_cards: List[DetectedCard]
    community_cards: List[DetectedCard]
    player_stacks: Dict[int, float]
    pot_size: float
    current_bet: float
    position: str
    street: str  # preflop, flop, turn, river
    timestamp: float

class VisionEngine:
    """Двигатель компьютерного зрения для распознавания покера"""
    
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.cascade_classifier = None
        self.card_templates = {}
        self.initialize_templates()
        self.capture = None
        self.is_running = False
        self.latest_state: Optional[PokerTableState] = None
        
    def initialize_templates(self):
        """Инициализация шаблонов карт"""
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
        suits = ['s', 'h', 'd', 'c']  # spades, hearts, diamonds, clubs
        
        for rank in ranks:
            for suit in suits:
                card_name = f"{rank}{suit}"
                self.card_templates[card_name] = self._create_card_template(rank, suit)
    
    def _create_card_template(self, rank: str, suit: str) -> np.ndarray:
        """Создание шаблона карты"""
        template = np.zeros((80, 50, 3), dtype=np.uint8)
        # Добавляем ранг и масть
        cv2.putText(template, rank, (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        suit_char = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}.get(suit, '♠')
        cv2.putText(template, suit_char, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return template
    
    def detect_cards_in_frame(self, frame: np.ndarray) -> List[DetectedCard]:
        """
        Распознавание карт в кадре
        
        Args:
            frame: Видео кадр
            
        Returns:
            Список обнаруженных карт
        """
        detected_cards = []
        
        # Преобразуем в серое изображение
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Находим контуры карт
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Фильтруем контуры по размеру (карты имеют определённый размер)
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Размер карты должен быть в определённом диапазоне
            if 2000 < area < 50000:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Извлекаем область карты
                card_roi = frame[y:y+h, x:x+w]
                
                # Распознаём ранг и масть
                rank, suit, confidence = self._recognize_card(card_roi)
                
                if confidence > 0.6:
                    detected_cards.append(DetectedCard(
                        rank=rank,
                        suit=suit,
                        confidence=confidence,
                        position=(x, y, x+w, y+h)
                    ))
        
        return detected_cards
    
    def _recognize_card(self, card_roi: np.ndarray) -> Tuple[str, str, float]:
        """
        Распознавание ранга и масти карты
        
        Returns:
            (rank, suit, confidence)
        """
        # Используем OCR для распознавания
        text = pytesseract.image_to_string(card_roi, config='--psm 6')
        
        # Парсим результаты
        text = text.upper().strip()
        
        if len(text) >= 2:
            rank = text[0] if text[0] in 'A23456789TJQK' else 'A'
            
            # Определяем масть по цвету
            suit = self._detect_suit_by_color(card_roi)
            
            confidence = 0.85
            return rank, suit, confidence
        
        return 'A', 's', 0.3
    
    def _detect_suit_by_color(self, card_roi: np.ndarray) -> str:
        """
        Определение масти по цвету карты
        
        Returns:
            Масть: 's' (чёрная), 'h' или 'd' (красная), 'c' (чёрная)
        """
        hsv = cv2.cvtColor(card_roi, cv2.COLOR_BGR2HSV)
        
        # Подсчитываем красные пиксели
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        red_pixels = np.sum(mask_red > 0)
        
        if red_pixels > card_roi.size * 0.1:  # Если более 10% красных пиксельв
            # Определяем красные масти (черви или бубны)
            # По оттенку: черви ≈ 0°, бубны ≈ 30°
            red_hue = np.mean(hsv[mask_red > 0, 0])
            return 'h' if red_hue < 15 else 'd'
        else:
            # Чёрные масти (пики или трефы)
            # По форме символа: пики остроконечные, трефы округлые
            return 's'  # Упрощённо
    
    def detect_table_regions(self, frame: np.ndarray) -> Dict[str, Tuple]:
        """
        Определение регионов стола
        
        Returns:
            Словарь с координатами регионов:
            - 'my_cards': координаты моих карт
            - 'community_cards': координаты кармана на столе
            - 'stacks': координаты стеков игроков
            - 'pot': координаты размера банка
        """
        h, w = frame.shape[:2]
        
        regions = {
            'my_cards': (w*0.1, h*0.75, w*0.4, h*0.95),  # Нижняя левая часть
            'community_cards': (w*0.25, h*0.3, w*0.75, h*0.5),  # Центр
            'stacks': (0, 0, w, h*0.2),  # Верхняя часть
            'pot': (w*0.4, h*0.4, w*0.6, h*0.6)  # Центр
        }
        
        return regions
    
    def detect_ocr_text(self, frame: np.ndarray, region: Tuple) -> str:
        """
        Распознавание текста OCR в определённом регионе
        
        Args:
            frame: Видео кадр
            region: (x1, y1, x2, y2)
            
        Returns:
            Распознанный текст
        """
        x1, y1, x2, y2 = region
        roi = frame[int(y1):int(y2), int(x1):int(x2)]
        
        text = pytesseract.image_to_string(roi, config='--psm 6')
        return text.strip()
    
    def start_stream_analysis(self, camera_source: int = 0, callback=None):
        """
        Начать анализ видеопотока
        
        Args:
            camera_source: Источник камеры (0 для встроенной)
            callback: Функция обратного вызова для каждого кадра
        """
        self.capture = cv2.VideoCapture(camera_source)
        self.is_running = True
        
        analysis_thread = threading.Thread(
            target=self._analysis_loop,
            args=(callback,),
            daemon=True
        )
        analysis_thread.start()
    
    def _analysis_loop(self, callback):
        """Основной цикл анализа"""
        while self.is_running and self.capture.isOpened():
            ret, frame = self.capture.read()
            
            if not ret:
                break
            
            # Изменяем размер для быстрой обработки
            frame = cv2.resize(frame, (640, 480))
            
            # Детектируем карты
            my_cards = self.detect_cards_in_frame(frame)
            
            # Определяем регионы
            regions = self.detect_table_regions(frame)
            
            # Извлекаем информацию из регионов
            community_cards_text = self.detect_ocr_text(frame, regions['community_cards'])
            pot_text = self.detect_ocr_text(frame, regions['pot'])
            
            # Создаём состояние
            state = PokerTableState(
                my_cards=my_cards[:2],  # Максимум 2 карты
                community_cards=my_cards[2:],  # Остальные - на столе
                player_stacks={},
                pot_size=self._parse_amount(pot_text),
                current_bet=0,
                position='button',
                street=self._detect_street(len(my_cards) - 2),
                timestamp=time.time()
            )
            
            self.latest_state = state
            
            if callback:
                callback(state, frame)
            
            # Ограничиваем FPS
            time.sleep(0.033)  # ~30 FPS
    
    def _parse_amount(self, text: str) -> float:
        """Парсить сумму из текста"""
        import re
        match = re.search(r'\d+(?:[.,]\d+)?', text)
        if match:
            return float(match.group().replace(',', '.'))
        return 0.0
    
    def _detect_street(self, community_cards_count: int) -> str:
        """Определить улицу по количеству карт на столе"""
        if community_cards_count == 0:
            return 'preflop'
        elif community_cards_count == 3:
            return 'flop'
        elif community_cards_count == 4:
            return 'turn'
        else:
            return 'river'
    
    def stop_stream_analysis(self):
        """Остановить анализ видеопотока"""
        self.is_running = False
        if self.capture:
            self.capture.release()
    
    def get_latest_state(self) -> Optional[PokerTableState]:
        """Получить последнее обнаруженное состояние"""
        return self.latest_state
