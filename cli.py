#!/usr/bin/env python3
"""CLI for Poker AI Bot"""

import click
from core.game_engine import PokerEngine, GameState


@click.group()
def cli():
    """🤖 Poker AI Bot - CLI"""
    pass


@cli.command()
@click.option('--my-cards', required=True, help='Ваши карты (AS KH)')
@click.option('--board', default='', help='Борд (QD JC 9H)')
@click.option('--pot', type=float, required=True, help='Банк')
@click.option('--bet', type=float, required=True, help='Ставка')
@click.option('--stack', type=float, required=True, help='Стек')
@click.option('--position', default='button', help='Позиция')
@click.option('--players', type=int, default=6, help='Игроков')
def analyze(my_cards, board, pot, bet, stack, position, players):
    """Анализировать руку"""
    try:
        engine = PokerEngine()
        state = GameState(
            my_cards=my_cards.split(),
            community_cards=board.split() if board else [],
            pot_size=pot,
            bet_to_call=bet,
            my_stack=stack,
            opponent_stacks={i: 5000 for i in range(1, players)},
            position=position,
            players_count=players,
            street='flop' if board and len(board.split()) >= 3 else 'preflop'
        )
        
        rec = engine.analyze(state)
        data = rec.to_dict()
        
        click.echo("\n" + "="*60)
        click.echo("✅ РЕКОМЕНДАЦИЯ")
        click.echo("="*60)
        click.echo(f"\n🎯 Действие: {data['action'].upper()}")
        click.echo(f"📊 Уверенность: {data['confidence']*100:.1f}%")
        click.echo(f"💰 EV: ${data['ev']:.2f}")
        click.echo(f"🎯 Equity: {data['equity']:.1f}%")
        click.echo(f"💡 Причина: {data['reasoning']}")
        click.echo("\n" + "="*60)
    except Exception as e:
        click.echo(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    cli()
