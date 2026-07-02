#!/usr/bin/env python3
"""Flask Web Application for Poker AI Bot"""

from flask import Flask, render_template, request, jsonify
import json
import os
from core.game_engine import PokerEngine, GameState

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
engine = PokerEngine()


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API for hand analysis"""
    try:
        data = request.json
        
        state = GameState(
            my_cards=data.get('my_cards', []),
            community_cards=data.get('community_cards', []),
            pot_size=float(data.get('pot_size', 0)),
            bet_to_call=float(data.get('bet_to_call', 0)),
            my_stack=float(data.get('my_stack', 0)),
            opponent_stacks={i: 5000 for i in range(1, int(data.get('players_count', 6)))},
            position=data.get('position', 'button'),
            players_count=int(data.get('players_count', 6)),
            street=data.get('street', 'preflop')
        )
        
        recommendation = engine.analyze(state)
        return jsonify(recommendation.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/config', methods=['GET'])
def api_config():
    """Get configuration"""
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return jsonify(json.load(f))
    return jsonify({})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 POKER AI BOT - Web Interface")
    print("="*60)
    print("\n✅ Сервер запущен!")
    print("\n📱 Откройте в браузере: http://localhost:5000")
    print("\n📱 На мобильном: http://ВАШ_IP:5000")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
