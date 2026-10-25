"""Regress the reported Japanese initial prompt through recognition and play."""
import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

import cv2
import numpy as np
import auto_bot as bot
from phased_strategy import PhasedStrategy


class ChallengePromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame=cv2.imread(str(Path(__file__).parent/'fixtures/challenge-ja-1600.png'))
        if cls.frame is None:
            raise AssertionError('Missing reported Japanese challenge screenshot')

    def test_initial_japanese_caption_beats_overlapping_success_text(self):
        template=cv2.imread(bot.resource_path('templates','icons','ja','success_ja.png'),0)
        gray=cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)
        old_score=cv2.minMaxLoc(cv2.matchTemplate(gray,template,cv2.TM_CCOEFF_NORMED))[1]
        self.assertGreaterEqual(old_score,.85)
        self.assertEqual(bot.detect_game_state(self.frame),'ASK_CHALLENGE')
        self.assertFalse(bot.is_success_prompt(self.frame))

    def test_next_reward_is_1600_and_current_cash_is_800(self):
        self.assertEqual(bot.read_screen_number(self.frame,bot.REWARD_ZONE),1600)

    def test_real_prompt_enters_each_strategy_without_inventing_wins_or_credit(self):
        for mode,stage in (('legacy',0),('phased',0),('phased',1),('phased',2)):
            with self.subTest(mode=mode,stage=stage):
                clock=[0.0]
                captures=[0]
                policy=PhasedStrategy(stage)
                def capture():
                    captures[0]+=1
                    clock[0]+=.3
                    if captures[0]>3:
                        bot.bot_running=False
                        return None,0,0
                    return self.frame,0,0
                with patch.object(bot,'capture_game_window',side_effect=capture), \
                     patch.object(bot,'find_and_click_icon',return_value=True) as click, \
                     patch.object(bot,'PhasedStrategy',return_value=policy), \
                     patch.object(bot,'load_daily_data',return_value=(0,0)), \
                     patch.object(bot,'load_daily_wins',return_value=(0,True)), \
                     patch.object(bot,'load_daily_stage',return_value=stage), \
                     patch.object(bot,'save_daily_data') as save, \
                     patch.object(bot.time,'sleep'), \
                     patch.object(bot.time,'monotonic',side_effect=lambda:clock[0]), \
                     patch.object(bot,'bot_running',True), \
                     patch.object(bot,'upcoming_card_val',None), \
                     contextlib.redirect_stdout(io.StringIO()):
                    bot.auto_play_loop(mode)
                    self.assertGreater(click.call_count,0)
                    self.assertTrue(all(call.args[1]==bot.TPL_CHECK for call in click.call_args_list))
                    save.assert_not_called()
                    if mode=='phased':
                        self.assertEqual(policy.base_cash,800)
                        self.assertEqual(policy.successes,0)
                        self.assertEqual(policy.expected_cash,800)

    def test_initial_and_success_caption_competition_in_existing_game_languages(self):
        # Composite crops exercise text overlap across all bundled alphabets.
        # These are not claimed as full-game recordings in each language.
        for language in ('en','tw','ja','zh'):
            for kind in ('chance','success'):
                with self.subTest(language=language,kind=kind):
                    frame=np.full((1080,1920,3),(220,145,190),np.uint8)
                    template=cv2.imread(bot.resource_path('templates','icons',language,
                                                          f'{kind}_{language}.png'))
                    h,w=template.shape[:2]
                    frame[350:350+h,500:500+w]=template
                    self.assertEqual(bot.is_success_prompt(frame),kind=='success')


if __name__=='__main__':
    unittest.main()
