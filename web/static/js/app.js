document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analyzeForm');
    form.addEventListener('submit', handleAnalyze);
});

async function handleAnalyze(e) {
    e.preventDefault();

    const data = {
        my_cards: document.getElementById('myCards').value.split(),
        community_cards: document.getElementById('board').value.trim().split(/\s+/).filter(x => x),
        pot_size: parseFloat(document.getElementById('pot').value),
        bet_to_call: parseFloat(document.getElementById('bet').value),
        my_stack: parseFloat(document.getElementById('stack').value),
        position: document.getElementById('position').value,
        players_count: parseInt(document.getElementById('players').value),
        street: document.getElementById('street').value
    };

    if (!data.my_cards || data.my_cards.length !== 2) {
        alert('Введите 2 карты!');
        return;
    }

    const btn = e.target.querySelector('button');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Анализирую...';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Ошибка анализа');

        const result = await response.json();
        displayResult(result);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function displayResult(result) {
    const resultSection = document.getElementById('result');
    
    document.getElementById('action').textContent = result.action.toUpperCase();
    document.getElementById('action').style.color = getActionColor(result.action);
    
    document.getElementById('confidence').textContent = (result.confidence * 100).toFixed(1) + '%';
    document.getElementById('equity').textContent = result.equity.toFixed(1) + '%';
    document.getElementById('winRate').textContent = result.win_rate.toFixed(1) + '%';
    document.getElementById('ev').textContent = '$' + result.ev.toFixed(2);
    
    document.getElementById('reasoning').textContent = result.reasoning;
    
    if (result.suggested_bet_size) {
        document.getElementById('betSize').style.display = 'block';
        document.getElementById('betValue').textContent = '$' + result.suggested_bet_size.toFixed(2);
    } else {
        document.getElementById('betSize').style.display = 'none';
    }
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
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
