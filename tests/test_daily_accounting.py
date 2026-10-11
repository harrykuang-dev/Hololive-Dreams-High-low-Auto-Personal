import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
import auto_bot as bot
from daily_accounting import load_wins, net_profit, record_day, read_record


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

    def test_day_starts_at_local_four_including_month_and_year_boundaries(self):
        for now, expected in [(datetime(2026,10,11,0),'2026-10-10'),
                              (datetime(2026,10,11,3,59,59),'2026-10-10'),
                              (datetime(2026,10,11,4),'2026-10-11'),
                              (datetime(2026,1,1,3,59),'2025-12-31'),
                              (datetime(2028,3,1,3,59),'2028-02-29')]:
            self.assertEqual(record_day(now),expected)

    def test_legacy_midnight_date_migrates_without_losing_rewards_or_inventing_wins(self):
        with tempfile.TemporaryDirectory() as folder, patch('daily_accounting.datetime') as clock:
            clock.now.return_value=datetime(2026,10,11,2)
            path=Path(folder)/'daily_coins.json'
            original=dict(date='2026-10-11',coins=12800,fails=3,phased_stage=2)
            path.write_text(json.dumps(original))
            with patch.object(bot,'DATA_FILE',path):
                bot.ensure_daily_data()
                self.assertEqual(bot.load_daily_data(),(12800,3))
                self.assertEqual(bot.load_daily_stage(),2)
                self.assertEqual(bot.load_daily_wins(),(0,False))
                migrated=json.loads(path.read_text())
                self.assertEqual(migrated['date'],'2026-10-10')
                self.assertEqual(migrated['day_start_hour'],4)
                self.assertNotIn('wins',migrated)
                clock.now.return_value=datetime(2026,10,11,4)
                bot.ensure_daily_data()
                self.assertEqual(bot.load_daily_data(),(0,0))
                self.assertEqual(bot.load_daily_stage(),0)
                self.assertEqual(bot.load_daily_wins(),(0,True))

    def test_restart_at_midnight_keeps_records_until_four_then_resets_all_fields(self):
        with tempfile.TemporaryDirectory() as folder, patch('daily_accounting.datetime') as clock:
            path=Path(folder)/'daily_coins.json'
            with patch.object(bot,'DATA_FILE',path):
                clock.now.return_value=datetime(2026,10,10,23,59)
                bot.save_daily_data(6400,2,2,3,True)
                clock.now.return_value=datetime(2026,10,11,0)
                bot.ensure_daily_data()
                self.assertEqual(bot.load_daily_data(),(6400,2))
                self.assertEqual(bot.load_daily_wins(),(3,True))
                self.assertEqual(bot.load_daily_stage(),2)
                clock.now.return_value=datetime(2026,10,11,4)
                bot.ensure_daily_data()
                data=read_record(path)
                self.assertEqual((data['coins'],data['fails'],data['wins'],data['phased_stage']),(0,0,0,0))
                self.assertTrue(data['wins_complete'])
                self.assertEqual(json.loads(path.read_text())['date'],'2026-10-11')
