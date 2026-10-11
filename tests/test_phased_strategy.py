import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import auto_bot as bot
from challenge_reward import ChallengeRewardReader, valid_next_reward
from phased_strategy import PhasedStrategy
from settlement import SettlementReader


class StrategyTests(unittest.TestCase):
    def test_second_stage_counts_by_initial_hand(self):
        for base, wins, payout in [(200, 5, 6400), (400, 4, 6400), (700, 3, 5600),
                                   (800, 3, 6400), (1500, 2, 6000), (3000, 1, 6000)]:
            policy = PhasedStrategy(1)
            policy.start_round(base, 12800)
            self.assertEqual(policy.target_wins, wins)
            for _ in range(wins):
                self.assertEqual(policy.decide(), 'challenge')
                policy.guess_clicked()
                policy.guess_clicked()  # Repeat click / tie, not another win.
                policy.confirm_success()
                policy.confirm_success()  # Repeat success frame.
            self.assertEqual(policy.decide(), 'cashout')
            self.assertEqual(policy.expected_cash, payout)

    def test_first_and_third_continue_until_game_settlement(self):
        for stage in (0, 2):
            policy = PhasedStrategy(stage)
            policy.start_round(400, 0)
            for _ in range(8):
                policy.guess_clicked()
                policy.confirm_success()
                self.assertEqual(policy.decide(), 'challenge')
            policy.guess_clicked()
            policy.begin_settlement(False)
            policy.begin_settlement(False)
            self.assertEqual(policy.successes, 9)
            self.assertEqual(policy.stage_after_credit(policy.expected_cash), stage + 1)

    def test_failure_restarts_count_but_not_stage(self):
        policy = PhasedStrategy(1)
        policy.start_round(200, 12800)
        policy.guess_clicked()
        policy.confirm_success()
        policy.reset_round()
        self.assertEqual(policy.stage, 1)
        self.assertEqual(policy.successes, 0)
        policy.start_round(700, 12800)
        self.assertEqual(policy.target_wins, 3)

    def test_second_stage_preserves_third_round(self):
        policy = PhasedStrategy(1)
        policy.start_round(200, 14000)
        self.assertEqual(policy.target_wins, 4)
        with self.assertRaises(RuntimeError):
            PhasedStrategy(1).start_round(7000, 14000)

    def test_only_valid_stable_amounts_reach_strategy(self):
        for value in (0, 20, 80, 200, 8000, -400):
            self.assertFalse(valid_next_reward(value))
        reader = ChallengeRewardReader()
        self.assertIsNone(reader.observe(80, 0))
        self.assertIsNone(reader.observe(800, .3))
        self.assertEqual(reader.observe(800, .6), 800)
        reader.reset_prompt()
        self.assertIsNone(reader.observe(6400, 1))  # Impossible jump.
        self.assertIsNone(reader.observe(1600, 1.3))
        self.assertEqual(reader.observe(1600, 1.6), 1600)
        reader.reset_round()
        self.assertIsNone(reader.observe(400, 2))
        self.assertEqual(reader.observe(400, 2.3), 400)

    def test_invalid_ocr_times_out_without_inventing_reward(self):
        reader = ChallengeRewardReader()
        for i in range(8):
            self.assertIsNone(reader.observe(80, i))
        with self.assertRaises(RuntimeError):
            reader.observe(80, 8)

    def test_settlement_must_match_confirmed_cashout(self):
        reader = SettlementReader()
        for i in range(8):
            self.assertIsNone(reader.observe(400, i, expected=12800))
        with self.assertRaises(RuntimeError):
            reader.observe(400, 8, expected=12800)

    def test_ledger_stage_is_atomic_persistent_and_date_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'daily_coins.json'
            with patch.object(bot, 'DATA_FILE', path):
                bot.save_daily_data(12800, 3, 1)
                self.assertEqual(bot.load_daily_data(), (12800, 3))
                self.assertEqual(bot.load_daily_stage(), 1)
                bot.save_daily_data(12800, 4)  # Failure or legacy write.
                self.assertEqual(bot.load_daily_stage(), 1)
                self.assertFalse(path.with_suffix('.tmp').exists())
                data = json.loads(path.read_text())
                data['date'] = '2000-01-01'
                path.write_text(json.dumps(data))
                self.assertEqual(bot.load_daily_stage(), 0)

    def run_frames(self, frames, mode='phased', stage=0):
        frames = iter(frames)
        current = ['UNKNOWN', 0]
        clock = [0.0]
        tracking_capture = [False]
        writes, clicks = [], []
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)

        def capture():
            if tracking_capture[0]:
                tracking_capture[0] = False
                return None, 0, 0
            clock[0] += .3
            try:
                current[:] = next(frames)
                return image, 0, 0
            except StopIteration:
                bot.bot_running = False
                return None, 0, 0

        def sleep(seconds):
            if seconds == .04:
                tracking_capture[0] = True

        def read_initial(*args):
            if current[0] == 'SUCCESS':
                raise AssertionError('Ongoing reward OCR must not drive the phased strategy')
            return current[1]

        def click(img, tpl, *args, **kwargs):
            clicks.append((current[0], current[1], Path(tpl).name))
            return True

        with patch.object(bot, 'capture_game_window', side_effect=capture), \
             patch.object(bot, 'detect_game_state', side_effect=lambda _: 'ASK_CHALLENGE' if current[0] == 'SUCCESS' else current[0]), \
             patch.object(bot, 'CardRecognizer', return_value=SimpleNamespace(recognize_card=lambda *a: SimpleNamespace(card_id=20, rank='7'))), \
             patch.object(bot, 'find_all_card_rects', return_value=[(50, 400, 200, 300)]), \
             patch.object(bot, 'is_success_prompt', side_effect=lambda _: current[0] == 'SUCCESS'), \
             patch.object(bot, 'read_screen_number', side_effect=read_initial), \
             patch.object(bot, 'read_result_number', side_effect=lambda *a: current[1]), \
             patch.object(bot, 'find_and_click_icon', side_effect=click), \
             patch.object(bot, 'load_daily_data', return_value=(0, 0)), \
             patch.object(bot, 'load_daily_stage', return_value=stage), \
             patch.object(bot, 'load_daily_wins', return_value=(0, True)), \
             patch.object(bot, 'save_daily_data', side_effect=lambda *a: writes.append(a)), \
             patch.object(bot.time, 'sleep', side_effect=sleep), \
             patch.object(bot.time, 'monotonic', side_effect=lambda: clock[0]), \
             contextlib.redirect_stdout(io.StringIO()):
            bot.bot_running = True
            bot.upcoming_card_val = None
            try:
                bot.auto_play_loop(mode)
            finally:
                bot.bot_running = False
        return writes, clicks

    def test_full_three_stage_loop_and_failure_retry(self):
        frames = [('FAIL', 0), ('START_BET', 0)]
        for stage, base, wins, payout in [(0, 400, 5, 12800), (1, 700, 3, 5600), (2, 400, 5, 12800)]:
            frames.extend([('ASK_CHALLENGE', base * 2)] * 2)
            for i in range(wins):
                frames.append(('HIGH_LOW', 0))
                if i < wins - 1 or stage == 1:
                    frames.extend([('SUCCESS', 80), ('UNKNOWN', 0), ('SUCCESS', 80)])
            frames.extend([('RESULT', payout)] * 12)
            frames.extend([('UNKNOWN', 0), ('RESULT', payout), ('START_BET', 0)])
        writes, clicks = self.run_frames(frames)
        self.assertEqual(writes, [(0, 1, None, 0, True), (12800, 1, 1, 1, True),
                                  (18400, 1, 2, 2, True), (31200, 1, 3, 3, True)])
        # The two success frames may retry a cashout, but only in stage two.
        self.assertEqual([state for state, reward, tpl in clicks if tpl == 'tpl_cross.png'],
                         ['SUCCESS', 'SUCCESS'])

    def test_invalid_reward_cannot_trigger_click_in_either_mode(self):
        for mode in ('legacy', 'phased'):
            writes, clicks = self.run_frames([('ASK_CHALLENGE', 80)] * 3, mode)
            self.assertEqual((writes, clicks), ([], []))

    def test_completed_stage_does_not_start_a_fourth_round(self):
        self.assertEqual(self.run_frames([('START_BET', 0)], stage=3), ([], []))


if __name__ == '__main__':
    unittest.main()
