"""
Equity Calculator - Расчет эквити в покере
"""

import random
from typing import List, Tuple
from .card_analyzer import Card, CardAnalyzer


class EquityCalculator:
    """Расчитывает equity различных комбинаций"""

    @staticmethod
    def monte_carlo_equity(
        player1_cards: List[Card],
        player2_cards: List[Card],
        community_cards: List[Card],
        simulations: int = 10000
    ) -> Tuple[float, float]:
        """
        Расчитывает equity методом Монте-Карло
        Returns: (player1_equity, player2_equity)
        """
        analyzer = CardAnalyzer()
        
        # Все карты в игре
        used_cards = set(player1_cards + player2_cards + community_cards)
        
        # Все оставшиеся карты в колоде
        all_ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        all_suits = ['S', 'H', 'D', 'C']
        remaining_cards = []
        
        for rank in all_ranks:
            for suit in all_suits:
                card_str = rank + suit
                card = Card(card_str)
                if card not in used_cards:
                    remaining_cards.append(card)

        # Нужно определить, сколько карт осталось раздать
        cards_needed = 5 - len(community_cards)

        player1_wins = 0
        player2_wins = 0
        ties = 0

        for _ in range(simulations):
            # Случайно выбираем оставшиеся карты
            new_cards = random.sample(remaining_cards, cards_needed)
            final_board = community_cards + new_cards

            # Расчитываем лучшие руки
            p1_rank, p1_hand = analyzer.calculate_hand_strength(player1_cards, final_board)
            p2_rank, p2_hand = analyzer.calculate_hand_strength(player2_cards, final_board)

            # Оцениваем руки
            _, p1_value = analyzer._evaluate_five_cards(p1_hand)
            _, p2_value = analyzer._evaluate_five_cards(p2_hand)

            if p1_value > p2_value:
                player1_wins += 1
            elif p2_value > p1_value:
                player2_wins += 1
            else:
                ties += 1

        total = simulations
        p1_equity = ((player1_wins + ties * 0.5) / total) * 100
        p2_equity = ((player2_wins + ties * 0.5) / total) * 100

        return p1_equity, p2_equity

    @staticmethod
    def calculate_equity_vs_range(
        my_cards: List[Card],
        community_cards: List[Card],
        opponent_ranges: List[List[Card]],
        simulations: int = 1000
    ) -> float:
        """
        Расчитывает equity против диапазона противника
        """
        analyzer = CardAnalyzer()
        
        if not opponent_ranges:
            return 50.0

        total_equity = 0
        
        for opponent_cards in opponent_ranges:
            eq1, eq2 = EquityCalculator.monte_carlo_equity(
                my_cards,
                opponent_cards,
                community_cards,
                simulations
            )
            total_equity += eq1

        return total_equity / len(opponent_ranges)

    @staticmethod
    def calculate_implied_odds(
        pot_size: float,
        bet_to_call: float,
        estimated_future_pot: float
    ) -> float:
        """
        Расчитывает имплайд оддсы
        Учитывает потенциальные выигрыши в будущем
        """
        if bet_to_call == 0:
            return 0
        
        total_possible_pot = pot_size + estimated_future_pot
        return (total_possible_pot / (total_possible_pot + bet_to_call)) * 100

    @staticmethod
    def calculate_reverse_implied_odds(
        pot_size: float,
        bet_to_call: float,
        potential_loss: float
    ) -> float:
        """
        Расчитывает обратные имплайд оддсы
        Когда улучшение руки может привести к потерям
        """
        if bet_to_call == 0:
            return 100
        
        return ((pot_size - potential_loss) / (pot_size + bet_to_call)) * 100

    @staticmethod
    def estimate_opponent_range(
        position: str,
        action: str,
        board: List[Card],
        stack_depth: float
    ) -> List[str]:
        """
        Оценивает диапазон противника на основе позиции и действия
        Returns: список возможных комбинаций карт
        """
        # Это упрощенная версия
        # В реальном боте это будет намного более сложной
        
        # GTO диапазоны для открытия
        opening_ranges = {
            'early': ['AA', 'KK', 'QQ', 'AK'],
            'middle': ['AA', 'KK', 'QQ', 'JJ', 'AK', 'AQ'],
            'late': ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AK', 'AQ', 'KQ'],
            'button': ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AK', 'AQ', 'KQ', 'AJ'],
        }

        # Диапазоны для 3-бета
        threeraise_ranges = {
            'early': ['AA', 'KK', 'QQ', 'AK'],
            'middle': ['AA', 'KK', 'QQ', 'AK'],
            'late': ['AA', 'KK', 'QQ', 'JJ', 'AK', 'AQ'],
        }

        if action == '3bet':
            return threeraise_ranges.get(position, [])
        
        return opening_ranges.get(position, [])

    @staticmethod
    def calculate_cbet_equity_threshold(
        position: str,
        board_texture: str,
        stack_depth: float
    ) -> float:
        """
        Расчитывает минимальное equity для c-bet
        """
        # Текстура влияет на threshold
        texture_modifier = {
            'dry': 1.0,      # На сухом борде меньше equity нужно
            'wet': 1.3,      # На мокром борде больше equity нужно
            'paired': 1.1,   # На спаренном борде немного больше
        }

        position_modifier = {
            'early': 1.2,    # Из ранней позиции нужно более сильная рука
            'middle': 1.0,
            'late': 0.85,    # Из поздней позиции можно c-bet более широко
        }

        base_threshold = 40  # 40% equity
        
        modifier = texture_modifier.get(board_texture, 1.0) * position_modifier.get(position, 1.0)
        
        return base_threshold * modifier

    @staticmethod
    def showdown_equity(
        hand1: List[Card],
        hand2: List[Card],
        board: List[Card]
    ) -> Tuple[float, float]:
        """
        Расчитывает equity на showdown
        """
        analyzer = CardAnalyzer()
        
        rank1, cards1 = analyzer.calculate_hand_strength(hand1, board)
        rank2, cards2 = analyzer.calculate_hand_strength(hand2, board)
        
        _, value1 = analyzer._evaluate_five_cards(cards1)
        _, value2 = analyzer._evaluate_five_cards(cards2)
        
        if value1 > value2:
            return 100.0, 0.0
        elif value2 > value1:
            return 0.0, 100.0
        else:
            return 50.0, 50.0
