"""Card Analysis Module"""
from typing import List, Tuple, Dict
from enum import Enum


class HandRank(Enum):
    """Poker hand ranks"""
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


class CardAnalyzer:
    """Analyzes poker cards and hands"""

    RANK_VALUES = {
        'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
        '9': 9, '8': 8, '7': 7, '6': 6, '5': 5,
        '4': 4, '3': 3, '2': 2
    }

    @staticmethod
    def parse_cards(card_strings: List[str]) -> List[Tuple[str, str]]:
        """Parse cards from strings"""
        cards = []
        for card_str in card_strings:
            if len(card_str) == 2:
                cards.append((card_str[0], card_str[1]))
        return cards

    @staticmethod
    def get_hand_category(hole_cards: List[str]) -> str:
        """Get hand category like AA, AKs, AKo"""
        if len(hole_cards) != 2:
            return "INVALID"
        
        card1, card2 = hole_cards
        rank1 = card1[0]
        rank2 = card2[0]
        suit1 = card1[1]
        suit2 = card2[1]
        
        ranks = sorted([rank1, rank2], key=lambda x: CardAnalyzer.RANK_VALUES[x], reverse=True)
        
        if rank1 == rank2:
            return f"{ranks[0]}{ranks[0]}"
        elif suit1 == suit2:
            return f"{ranks[0]}{ranks[1]}s"
        else:
            return f"{ranks[0]}{ranks[1]}o"

    @staticmethod
    def is_pocket_pair(hole_cards: List[str]) -> bool:
        """Check if pocket pair"""
        if len(hole_cards) != 2:
            return False
        return hole_cards[0][0] == hole_cards[1][0]

    @staticmethod
    def is_suited(hole_cards: List[str]) -> bool:
        """Check if suited"""
        if len(hole_cards) != 2:
            return False
        return hole_cards[0][1] == hole_cards[1][1]

    @staticmethod
    def is_broadway(hole_cards: List[str]) -> bool:
        """Check if broadway (T, J, Q, K, A)"""
        broadway_ranks = {'T', 'J', 'Q', 'K', 'A'}
        return all(card[0] in broadway_ranks for card in hole_cards)

    @staticmethod
    def calculate_hand_strength(hole_cards: List[str], board: List[str]) -> float:
        """Calculate hand strength 0-1"""
        if len(board) == 0:
            category = CardAnalyzer.get_hand_category(hole_cards)
            preflop_strength = {
                'AA': 0.95, 'KK': 0.92, 'QQ': 0.88, 'JJ': 0.84, 'TT': 0.80, '99': 0.76,
                'AKs': 0.85, 'AQs': 0.75, 'AJs': 0.70, 'ATs': 0.65,
                'AKo': 0.75, 'AQo': 0.65, 'AJo': 0.60, 'ATo': 0.55,
                'KQs': 0.70, 'KJs': 0.65, 'QJs': 0.60,
            }
            return preflop_strength.get(category, 0.5)
        return 0.5

    @staticmethod
    def calculate_pot_odds(pot_size: float, bet_to_call: float) -> float:
        """Calculate pot odds percentage"""
        if bet_to_call == 0:
            return 0
        return (pot_size / (pot_size + bet_to_call)) * 100
