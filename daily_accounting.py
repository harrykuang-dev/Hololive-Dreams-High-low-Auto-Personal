"""Display-only accounting; gross rewards remain the strategy's input."""
import json
import time

ENTRY_COST = 50


def load_wins(path, today=None):
    today = today or time.strftime('%Y-%m-%d')
    if not path.exists():
        return 0, True
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('date') != today:
        return 0, True
    wins = data.get('wins', 0)
    if type(wins) is not int or wins < 0:
        raise ValueError('Invalid saved win count')
    complete = data.get('wins_complete', 'wins' in data or data.get('coins', 0) == 0)
    if type(complete) is not bool:
        raise ValueError('Invalid saved accounting completeness')
    return wins, complete


def net_profit(coins, fails, wins, complete=True):
    return coins - ENTRY_COST * (fails + wins) if complete else None
