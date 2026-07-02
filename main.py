#!/usr/bin/env python3
"""Interactive CLI for Poker AI Bot"""

from core.game_engine import PokerEngine, GameState


def main():
    print("\n" + "="*60)
    print("🤖 POKER AI BOT - Interactive Mode")
    print("="*60)
    
    engine = PokerEngine()
    
    while True:
        print("\n" + "-"*60)
        try:
            my_cards = input("Ваши карты (AS KH): ").strip().split()
            if len(my_cards) != 2:
                print("❌ Введите ровно 2 карты!")
                continue
            
            board_str = input("Борд (QD JC 9H или пусто): ").strip()
            board = board_str.split() if board_str else []
            
            pot = float(input("Банк ($): "))
            bet = float(input("Ставка ($): "))
            stack = float(input("Ваш стек ($): "))
            
            position = input("Позиция (UTG/MP/CO/BTN/SB/BB): ").strip().upper()
            players = int(input("Игроков (по умолч 6): ") or "6")
            
            state = GameState(
                my_cards=my_cards,
                community_cards=board,
                pot_size=pot,
                bet_to_call=bet,
                my_stack=stack,
                opponent_stacks={i: 5000 for i in range(1, players)},
                position=position,
                players_count=players,
                street='flop' if len(board) >= 3 else 'preflop'
            )
            
            rec = engine.analyze(state)
            data = rec.to_dict()
            
            print("\n" + "="*60)
            print("✅ РЕКОМЕНДАЦИЯ")
            print("="*60)
            print(f"\n🎯 Действие: {data['action'].upper()}")
            print(f"📊 Уверенность: {data['confidence']*100:.1f}%")
            print(f"💰 EV: ${data['ev']:.2f}")
            print(f"🎯 Equity: {data['equity']:.1f}%")
            print(f"💡 Причина: {data['reasoning']}")
            
            if data['suggested_bet_size']:
                print(f"💵 Размер ставки: ${data['suggested_bet_size']:.2f}")
            
            print("\n" + "="*60)
            
        except ValueError:
            print("❌ Ошибка ввода! Проверьте формат.")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        if input("\nПродолжить? (да/нет): ").lower() not in ['да', 'y', 'yes']:
            break
    
    print("\n👋 До свидания!\n")


if __name__ == '__main__':
    main()
