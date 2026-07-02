"""Main Poker Game Engine with AI"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json
import os
from .card_analyzer import CardAnalyzer


@dataclass
class GameState:
    """Current game state"""
    my_cards: List[str]
    community_cards: List[str]
    pot_size: float
    bet_to_call: float
    my_stack: float
    opponent_stacks: Dict
    position: str
    players_count: int
    street: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Recommendation:
    """AI Recommendation"""
    action: str
    confidence: float
    ev: float
    reasoning: str
    alternative_actions: List[Dict]
    win_rate: float
    pot_odds: float
    equity: float
    suggested_bet_size: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'action': self.action,
            'confidence': round(self.confidence, 4),
            'ev': round(self.ev, 4),
            'reasoning': self.reasoning,
            'win_rate': round(self.win_rate, 4),
            'pot_odds': round(self.pot_odds, 4),
            'equity': round(self.equity, 4),
            'suggested_bet_size': round(self.suggested_bet_size, 2) if self.suggested_bet_size else None,
            'alternative_actions': [
                {
                    'action': alt['action'],
                    'ev': round(alt['ev'], 4),
                    'confidence': round(alt['confidence'], 4)
                } for alt in self.alternative_actions
            ]
        }


class PokerEngine:
    """Main AI Engine"""

    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        self.analyzer = CardAnalyzer()

    @staticmethod
    def _load_config(path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {'ai': {'aggression_level': 0.7}}

    def analyze(self, state: GameState) -> Recommendation:
        """Analyze poker situation"""
        try:
            hand_strength = self._calculate_hand_strength(state.my_cards, state.community_cards)
            equity = self._calculate_equity(state.my_cards, state.community_cards, state.players_count)
            pot_odds = self.analyzer.calculate_pot_odds(state.pot_size, state.bet_to_call)

            if state.bet_to_call == 0:
                return self._analyze_check_bet(state, hand_strength, equity)
            else:
                return self._analyze_call_fold(state, hand_strength, equity, pot_odds)
        except:
            return self._default_recommendation()

    def _analyze_call_fold(self, state: GameState, hand_strength: float, equity: float, pot_odds: float) -> Recommendation:
        """Analyze call/fold"""
        ev = (equity / 100 * state.pot_size) - (state.bet_to_call * (1 - equity / 100))

        if equity > pot_odds:
            confidence = min(0.95, equity / 100)
            action = 'call'
            reasoning = f"Equity ({equity:.1f}%) > Pot odds ({pot_odds:.1f}%). Positive EV: ${ev:.2f}"
            alternatives = [
                {'action': 'raise', 'ev': ev * 0.8, 'confidence': 0.3},
                {'action': 'fold', 'ev': -state.bet_to_call, 'confidence': 0.1}
            ]
        else:
            confidence = min(0.95, 1 - equity / 100)
            action = 'fold'
            reasoning = f"Equity ({equity:.1f}%) < Pot odds ({pot_odds:.1f}%). Negative EV: ${ev:.2f}"
            alternatives = [{'action': 'call', 'ev': ev, 'confidence': 0.2}]

        return Recommendation(
            action=action,
            confidence=confidence,
            ev=ev,
            reasoning=reasoning,
            alternative_actions=alternatives,
            win_rate=equity,
            pot_odds=pot_odds,
            equity=equity
        )

    def _analyze_check_bet(self, state: GameState, hand_strength: float, equity: float) -> Recommendation:
        """Analyze check/bet"""
        
        if hand_strength > 0.7:
            bet_size = state.pot_size * 0.5
            ev = state.pot_size * (equity / 100)
            confidence = min(0.95, hand_strength)
            action = 'bet'
            reasoning = f"Strong hand (strength: {hand_strength:.2f}). Betting to build pot."
            alternatives = [{'action': 'check', 'ev': 0, 'confidence': 0.2}]
        elif hand_strength > 0.4:
            action = 'check'
            ev = 0
            confidence = 0.5
            reasoning = f"Medium hand (strength: {hand_strength:.2f}). Checking to see next card."
            alternatives = [{'action': 'bet', 'ev': ev * 1.5, 'confidence': 0.4}]
            bet_size = None
        else:
            action = 'check'
            ev = 0
            confidence = 0.7
            reasoning = f"Weak hand (strength: {hand_strength:.2f}). Check and fold to aggression."
            alternatives = []
            bet_size = None

        return Recommendation(
            action=action,
            confidence=confidence,
            ev=ev,
            reasoning=reasoning,
            alternative_actions=alternatives,
            win_rate=equity,
            pot_odds=50,
            equity=equity,
            suggested_bet_size=bet_size if action == 'bet' else None
        )

    def _calculate_hand_strength(self, my_cards: List[str], community: List[str]) -> float:
        """Calculate hand strength"""
        return self.analyzer.calculate_hand_strength(my_cards, community)

    def _calculate_equity(self, my_cards: List[str], community: List[str], players: int) -> float:
        """Calculate equity"""
        hand_strength = self._calculate_hand_strength(my_cards, community)
        opponent_factor = 1.0 / (1.0 + players * 0.2)
        return hand_strength * opponent_factor * 100

    def _default_recommendation(self) -> Recommendation:
        """Default recommendation on error"""
        return Recommendation(
            action='check',
            confidence=0.0,
            ev=0.0,
            reasoning='Error in analysis',
            alternative_actions=[],
            win_rate=50.0,
            pot_odds=50.0,
            equity=50.0
        )
