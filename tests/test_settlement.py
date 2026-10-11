import ast
import contextlib
import io
from pathlib import Path
import types
import unittest

from settlement import SettlementReader
from challenge_reward import ChallengeRewardReader
from daily_accounting import net_profit


class SettlementTests(unittest.TestCase):
    def replay(self, frames):
        # Execute the real accounting branches without importing Windows/OCR
        # dependencies or allowing mouse input and ledger file writes.
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'auto_bot.py').read_text(encoding='utf-8'))
        loop = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'auto_play_loop')
        reset = next(n for n in ast.walk(loop) if isinstance(n, ast.If)
                     and ast.unparse(n.test) == "current_state in ('START_BET', 'HOLD_CARDS')")
        result = next(n for n in ast.walk(loop) if isinstance(n, ast.If)
                      and ast.unparse(n.test) == "current_state == 'RESULT'")
        runner = ast.parse('for current_state, now, amount in frames:\n    pass')
        runner.body[0].body = [reset, ast.If(test=result.test, body=result.body, orelse=[])]
        writes, clicks = [], []
        env = dict(frames=frames, daily_coins=360, daily_fails=0, daily_wins=1, wins_complete=True,
                   has_tallied=False, settlement_reader=SettlementReader(),
                   reward_reader=ChallengeRewardReader(), phased=None, expected_cashout=None,
                   img=None, RESULT_REWARD_ZONE=None, TPL_CHECK=None,
                   win_left=0, win_top=0,
                   save_daily_data=lambda c, *args: writes.append(c),
                   calculate_net_profit=net_profit, emit_stats=lambda:None, emit=lambda *a,**k:None,
                   find_and_click_icon=lambda *a, **kw: clicks.append(True))
        env['read_result_number'] = lambda *a: env['amount']
        env['time'] = types.SimpleNamespace(monotonic=lambda: env['now'], sleep=lambda _: None)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(ast.fix_missing_locations(runner), '<accounting>', 'exec'), env)
        self.assertEqual(env['daily_wins'], 1+len(writes))
        if writes:
            self.assertEqual(env['net_profit'], env['daily_coins']-50*env['daily_wins'])
        return env['daily_coins'], writes, clicks

    def test_count_up_then_stable_400(self):
        frames = [('RESULT', i * .25, amount) for i, amount in enumerate(
            [20, 60, 280, 40, 400, 400, 400, 400, 400, 400, 400])]
        coins, writes, _ = self.replay(frames)
        self.assertEqual((coins, writes), (760, [760]))

    def test_zero_is_retried_and_not_clicked_away(self):
        self.assertEqual(self.replay([('RESULT', 0, 0)])[:], (360, [], []))
        frames = [('RESULT', i * .25, 0 if i < 7 else 400) for i in range(12)]
        self.assertEqual(self.replay(frames)[:2], (760, [760]))

    def test_unknown_does_not_duplicate_credit(self):
        frames = [('RESULT', i * .25, 400) for i in range(11)]
        frames += [('UNKNOWN', 3, 0), ('RESULT', 3.25, 400)]
        self.assertEqual(self.replay(frames)[:2], (760, [760]))

    def test_next_round_can_credit_again(self):
        for state in ('START_BET', 'HOLD_CARDS'):
            frames = [('RESULT', i * .25, 400) for i in range(11)]
            frames += [(state, 3, 0)]
            frames += [('RESULT', 4 + i * .25, 200) for i in range(11)]
            self.assertEqual(self.replay(frames)[:2], (960, [760, 960]))

    def test_timeout_for_zero_or_unstable_values(self):
        for values in ([0] * 33, [200, 400] * 17):
            reader = SettlementReader()
            with self.assertRaises(RuntimeError):
                for i, amount in enumerate(values):
                    self.assertIsNone(reader.observe(amount, i * .25))

    def test_animation_samples_cannot_satisfy_stability(self):
        reader = SettlementReader()
        for i in range(8):
            self.assertIsNone(reader.observe(200, i * .25))
        for now in (2, 2.25, 2.5):
            self.assertIsNone(reader.observe(400, now))
        self.assertEqual(reader.observe(400, 2.75), 400)


if __name__ == '__main__':
    unittest.main()
