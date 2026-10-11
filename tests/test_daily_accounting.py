import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import auto_bot as bot
from daily_accounting import load_wins, net_profit


class AccountingTests(unittest.TestCase):
    def test_each_winning_and_losing_round_costs_50(self):
        self.assertEqual(net_profit(31200, 26, 7), 29550)
        self.assertEqual(net_profit(400, 0, 1), 350)
        self.assertEqual(net_profit(0, 1, 0), -50)

    def test_restart_preserves_win_count_and_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'daily_coins.json'
            with patch.object(bot,'DATA_FILE',path):
                bot.save_daily_data(400,0,1,1,True)
                bot.save_daily_data(400,1)
                self.assertEqual(bot.load_daily_wins(),(1,True))
                self.assertEqual(bot.load_daily_stage(),1)
                self.assertEqual(net_profit(*bot.load_daily_data(),*bot.load_daily_wins()),300)
                data=json.loads(path.read_text())
                data['date']='2000-01-01'
                path.write_text(json.dumps(data))
                self.assertEqual(bot.load_daily_wins(),(0,True))
                self.assertEqual(bot.load_daily_data(),(0,0))

    def test_old_ledger_never_invents_wins_or_an_exact_profit(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'daily_coins.json'
            with patch.object(bot,'DATA_FILE',path):
                original=dict(coins=12800,fails=3,phased_stage=1,date=bot.time.strftime('%Y-%m-%d'))
                path.write_text(json.dumps(original))
                self.assertEqual(load_wins(path),(0,False))
                self.assertIsNone(net_profit(12800,3,0,False))
                bot.save_daily_data(13200,3,2,1,False)
                self.assertEqual(bot.load_daily_wins(),(1,False))
                self.assertEqual(bot.load_daily_data(),(13200,3))
                self.assertEqual(bot.load_daily_stage(),2)

    def test_missing_or_only_failed_ledger_is_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'daily_coins.json'
            self.assertEqual(load_wins(path),(0,True))
            path.write_text(json.dumps(dict(coins=0,fails=5,date=bot.time.strftime('%Y-%m-%d'))))
            self.assertEqual(load_wins(path),(0,True))
