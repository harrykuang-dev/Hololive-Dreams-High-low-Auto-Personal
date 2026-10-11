"""Display-only accounting; gross rewards remain the strategy's input."""
import json
from datetime import datetime, timedelta

ENTRY_COST = 50
DAY_START_HOUR = 4


def record_day(now=None):
    """The computer's local record day starts at 04:00."""
    now = datetime.now() if now is None else now
    return (now - timedelta(hours=DAY_START_HOUR)).date().isoformat()


def empty_record(day=None):
    return dict(date=record_day() if day is None else day, day_start_hour=DAY_START_HOUR,
                coins=0, fails=0, wins=0, wins_complete=True, phased_stage=0)


def read_record(path, today=None, now=None):
    now = datetime.now() if now is None else now
    today = record_day(now) if today is None else today
    if not path.exists():
        return empty_record(today)
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Invalid saved daily record')
    saved_day = data.get('date')
    # Midnight-based records saved between midnight and 04:00 belong to the
    # preceding record day. Preserve their amounts and accounting completeness.
    if (data.get('day_start_hour') != DAY_START_HOUR and now.hour < DAY_START_HOUR
            and saved_day == now.date().isoformat()):
        saved_day = record_day(now)
    if saved_day != today:
        return empty_record(today)
    return dict(data, date=today, day_start_hour=DAY_START_HOUR)


def write_record(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def load_wins(path, today=None):
    data = read_record(path, today)
    wins = data.get('wins', 0)
    if type(wins) is not int or wins < 0:
        raise ValueError('Invalid saved win count')
    complete = data.get('wins_complete', 'wins' in data or data.get('coins', 0) == 0)
    if type(complete) is not bool:
        raise ValueError('Invalid saved accounting completeness')
    return wins, complete


def net_profit(coins, fails, wins, complete=True):
    return coins - ENTRY_COST * (fails + wins) if complete else None
