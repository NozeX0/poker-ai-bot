# 📹 GTO MIND AI - Real-Time Vision Edition

## Что это?

Полностью автоматическое приложение для анализа покера в реальном времени:

✅ **Распознавание карт** - Определяет ваши карты и борд через камеру  
✅ **Live AI Analysis** - Анализирует в реальном времени  
✅ **Instant Overlay** - Выводит рекомендации поверх видео  
✅ **Полная автоматизация** - Вам больше ничего не нужно вводить  

## Установка

### 1️⃣ Требования

```bash
pip install -r requirements-ios.txt
```

### 2️⃣ Подготовка (один раз)

Установите Tesseract OCR:

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Загрузите отсюда: https://github.com/UB-Mannheim/tesseract/wiki

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 3️⃣ Запуск

```bash
python ios/run_mobile.py
```

Откройте **http://localhost:5000** на вашем устройстве (или http://ВАШ_IP:5000)

## Как использовать

### 🔴 LIVE MODE (Автоматический)

1. Нажимаем **"СТАРТ"**
2. Направляем камеру на покер-стол
3. AI автоматически:
   - Распознает ваши карты
   - Анализирует ситуацию
   - Выводит рекомендацию

### 📊 MANUAL MODE (Ручной ввод)

1. Нажимаем **"РУЧНОЙ ВВОД"**
2. Вводим карты (AS KH)
3. Вводим борд (QD JC 9H)
4. Вводим банк, ставку, стек
5. Нажимаем **"АНАЛИЗ"**

## Что выводит?

```
┌──────────────────────────────────────┐
│  ✅ RAISE                            │
├──────────────────────────────────────┤
│ Confidence: 92%   Equity: 65.3%     │
│ EV: +$150.50      Bet Size: $300    │
├──────────────────────────────────────┤
│ 💡 Reason:                           │
│ Strong hand, aggressive position     │
│ Build pot for value                  │
└──────────────────────────────────────┘
```

## Архитектура

```
📱 iPhone/iPad
    ↓
📹 Camera Feed
    ↓
🧠 Vision Engine (OpenCV + Tesseract)
    ├─ Card Detection
    ├─ Board Recognition
    └─ Table Analysis
    ↓
🤖 Poker AI Engine
    ├─ Hand Strength
    ├─ Equity Calculation
    ├─ Pot Odds
    └─ GTO Analysis
    ↓
📊 Live Overlay
    ├─ Action (FOLD/CALL/RAISE)
    ├─ Confidence Level
    ├─ Equity %
    ├─ EV Value
    └─ Reasoning
```

## Файлы

```
ios/
├── vision_engine.py      # Компьютерное зрение
├── mobile_app.py         # Мобильное приложение
├── templates/
│   └── mobile.html       # UI для мобильных
├── static/
│   └── styles.css        # Стили iOS
└── run_mobile.py         # Точка входа
```

## API Endpoints

### Запуск анализа
```
POST /api/start-vision
```

### Остановка
```
POST /api/stop-vision
```

### Видеопоток
```
GET /api/stream
Returns: MJPEG stream with overlay
```

### Текущая рекомендация
```
GET /api/recommendation
Returns: JSON с текущим анализом
```

### Анализ кадра
```
POST /api/analyze-frame
Body: { "frame": "base64_encoded_image" }
Returns: JSON с обнаруженными картами и рекомендацией
```

### Быстрый анализ
```
POST /api/quick-analysis
Body: {
  "my_cards": ["AS", "KH"],
  "community_cards": ["QD", "JC", "9H"],
  "pot": 1000,
  "bet": 100,
  "stack": 5000,
  "position": "button"
}
Returns: JSON с рекомендацией
```

## Производительность

- **Card Detection:** ~50-100ms
- **AI Analysis:** ~30-50ms
- **Total Latency:** ~80-150ms
- **FPS:** ~30fps

## Рекомендуемые покер-сайты

Проверьте разрешение использования AI-помощников на:
- PokerStars (некоторые игры)
- GGPoker
- Unibet
- Partypoker

⚠️ На некоторых сайтах использование AI-ботов запрещено!

## Советы по использованию

1. **Освещение** - Убедитесь что стол хорошо освещён
2. **Угол камеры** - Снимайте примерно под углом 45°
3. **Расстояние** - Держите камеру на расстоянии 30-50см
4. **Сети** - Убедитесь что ПК и телефон в одной сети

## Кастомизация

### Изменить порт

В `run_mobile.py`:
```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

### Включить GPU

В `mobile_app.py`:
```python
vision_engine = VisionEngine(use_gpu=True)
```

## Troubleshooting

### Camera not detected
```bash
# Windows
python -c "import cv2; print(cv2.getBuildInformation())"

# macOS/Linux
ls /dev/video*
```

### Tesseract not found
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
```

### Port already in use
```python
# Используйте другой порт
app.run(host='0.0.0.0', port=5001)
```

## Лицензия

MIT - Используйте на свой риск!

## Поддержка

Если что-то не работает:
1. Проверьте версию Python: `python --version` (нужен 3.8+)
2. Переустановите зависимости: `pip install -r requirements-ios.txt --upgrade`
3. Проверьте освещение и угол камеры
4. Очистите кэш браузера

---

**Made with ❤️ for poker players**
