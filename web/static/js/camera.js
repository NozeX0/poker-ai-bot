let video = document.getElementById('video');
let canvas = document.getElementById('canvas');
let ctx = canvas.getContext('2d');
let mediaStream = null;

// ========== УПРАВЛЕНИЕ КАМЕРОЙ ==========

async function startCamera() {
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' },
            audio: false
        });
        
        video.srcObject = mediaStream;
        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        };
        
        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('captureBtn').style.display = 'block';
        document.getElementById('stopBtn').style.display = 'block';
        
        updateStatus('✅ Камера включена. Направьте на стол!', 'success');
    } catch (err) {
        updateStatus('❌ Камера недоступна. ' + err.message, 'error');
        console.error('Camera error:', err);
    }
}

function stopCamera() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }
    
    document.getElementById('startBtn').style.display = 'block';
    document.getElementById('captureBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'none';
    
    updateStatus('⏹️ Камера остановлена', 'success');
}

// ========== СНИМОК И АНАЛИЗ ==========

async function captureAndAnalyze() {
    try {
        updateStatus('📸 Снимаю...', 'loading');
        
        // Делаем снимок
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Конвертируем в blob
        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('image', blob, 'photo.jpg');
            
            updateStatus('🔍 Распознаю карты...', 'loading');
            
            // Отправляем на сервер
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                displayResults(result);
                updateStatus('✅ Анализ завершен!', 'success');
                showResults();
            } else {
                updateStatus('❌ Ошибка: ' + (result.error || 'Неизвестная ошибка'), 'error');
            }
        });
    } catch (err) {
        updateStatus('❌ Ошибка: ' + err.message, 'error');
        console.error('Capture error:', err);
    }
}

// ========== ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ==========

function displayResults(data) {
    const recognized = data.recognized || {};
    const recommendation = data.recommendation || {};
    const combinations = data.combinations || [];
    
    // Карты
    document.getElementById('myCards').textContent = (recognized.my_cards || []).join(' ');
    document.getElementById('boardCards').textContent = (recognized.board || []).join(' ');
    
    // Размеры ставок
    document.getElementById('potSize').textContent = '$' + (recognized.pot || 0);
    document.getElementById('betSize').textContent = '$' + (recognized.bet || 0);
    document.getElementById('stackSize').textContent = '$' + (recognized.stack || 0);
    
    // Комбинации
    const combinationsHtml = combinations.length > 0
        ? combinations.map(c => `
            <div class="combination-item">
                <div class="type">${c.type}</div>
                <div class="description">${c.description}</div>
            </div>
          `).join('')
        : '<p>Нет комбинаций</p>';
    document.getElementById('combinations').innerHTML = combinationsHtml;
    
    // ГЛАВНАЯ РЕКОМЕНДАЦИЯ
    document.getElementById('action').textContent = (recommendation.action || '?').toUpperCase();
    document.getElementById('action').style.color = getActionColor(recommendation.action);
    
    document.getElementById('confidence').textContent = ((recommendation.confidence || 0) * 100).toFixed(1) + '%';
    document.getElementById('equity').textContent = (recommendation.equity || 0).toFixed(1) + '%';
    document.getElementById('winRate').textContent = (recommendation.win_rate || 0).toFixed(1) + '%';
    document.getElementById('ev').textContent = '$' + (recommendation.ev || 0).toFixed(2);
    
    document.getElementById('reasoning').textContent = recommendation.reasoning || 'Нет информации';
    
    if (recommendation.suggested_bet_size) {
        document.getElementById('betSizing').style.display = 'block';
        document.getElementById('betValue').textContent = '$' + recommendation.suggested_bet_size.toFixed(2);
    } else {
        document.getElementById('betSizing').style.display = 'none';
    }
}

// ========== РУЧНОЙ АНАЛИЗ ==========

async function manualAnalyze(event) {
    event.preventDefault();
    
    const data = {
        my_cards: document.getElementById('manualCards').value.split(' '),
        board: document.getElementById('manualBoard').value.split(' ').filter(x => x),
        pot: parseFloat(document.getElementById('manualPot').value),
        bet: parseFloat(document.getElementById('manualBet').value),
        stack: parseFloat(document.getElementById('manualStack').value),
        position: 'button',
        players: 6
    };
    
    try {
        updateStatus('🤖 Анализирую...', 'loading');
        
        const response = await fetch('/api/manual-analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayResults({ ...result, recognized: data });
            updateStatus('✅ Анализ завершен!', 'success');
            showResults();
        } else {
            updateStatus('❌ Ошибка: ' + (result.error || 'Неизвестная ошибка'), 'error');
        }
    } catch (err) {
        updateStatus('❌ Ошибка: ' + err.message, 'error');
        console.error('Analysis error:', err);
    }
}

// ========== ИСТОРИЯ ==========

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.history.length === 0) {
            document.getElementById('historyList').innerHTML = '<p>История пуста</p>';
            return;
        }
        
        const html = data.history.map((item, index) => `
            <div class="history-item">
                <strong>#${index + 1}</strong><br>
                Карты: ${item.recognized.my_cards.join(' ')}<br>
                Действие: <span style="color: ${getActionColor(item.recommendation.action)}">${item.recommendation.action.toUpperCase()}</span><br>
                Equity: ${item.recommendation.equity.toFixed(1)}%
            </div>
        `).join('');
        
        document.getElementById('historyList').innerHTML = html;
    } catch (err) {
        console.error('Error loading history:', err);
    }
}

async function clearHistory() {
    if (confirm('Вы уверены? Это удалит всю историю.')) {
        await fetch('/api/clear-history', { method: 'POST' });
        loadHistory();
    }
}

// ========== УПРАВЛЕНИЕ ВКЛАДКАМИ ==========

function switchTab(event, tabName) {
    event.preventDefault();
    
    // Скрываем все табы
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
    });
    
    // Показываем выбранный таб
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
    
    // Загружаем историю если нужно
    if (tabName === 'history') {
        loadHistory();
    }
}

function showResults() {
    document.getElementById('camera-tab').style.display = 'none';
    document.getElementById('results').style.display = 'block';
}

function goBackToCamera() {
    document.getElementById('results').style.display = 'none';
    document.getElementById('camera-tab').style.display = 'block';
}

// ========== УТИЛИТЫ ==========

function updateStatus(message, type = 'info') {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = 'status ' + type;
}

function getActionColor(action) {
    const colors = {
        'raise': '#ff6b6b',
        'call': '#51cf66',
        'fold': '#ffd43b',
        'check': '#74c0fc',
        'bet': '#ff922b'
    };
    return colors[action.toLowerCase()] || '#00d4ff';
}

// При загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Poker AI Bot loaded!');
});
