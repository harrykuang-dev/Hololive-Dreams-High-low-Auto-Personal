"""Regression against actual Sep 30 game screenshots, not generated glyphs."""
from pathlib import Path
import unittest
import cv2
import ddddocr
from reward_vision import read_challenge_number, read_result_number
from settlement import SettlementReader

class LiveRewardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ocr = ddddocr.DdddOcr(show_ad=False)

    def frame(self, name):
        image = cv2.imread(str(Path(__file__).parent/'fixtures'/name))
        self.assertIsNotNone(image)
        if image.shape[:2] == (1080,1920):
            return image
        return cv2.resize(image[30:],(1920,1080),interpolation=cv2.INTER_CUBIC)

    def test_challenge_800_is_next_reward(self):
        self.assertEqual(read_challenge_number(self.frame('challenge-800.jpg'),
                                              (606,389,870,253),self.ocr),800)

    def test_result_400_survives_caption_and_character_animation(self):
        for name in ('result-400-a.jpg','result-400-b.jpg'):
            with self.subTest(name=name):
                self.assertEqual(read_result_number(self.frame(name),
                                                   (990,290,600,150),self.ocr),400)

    def test_actual_12800_preserves_leading_digits_in_both_paths(self):
        self.assertEqual(read_challenge_number(self.frame('challenge-12800.png'),
                                              (606,389,870,253),self.ocr),12800)
        self.assertEqual(read_result_number(self.frame('result-12800.png'),
                                           (990,290,600,150),self.ocr),12800)

    def test_actual_animation_80_is_not_a_400_settlement(self):
        amount = read_result_number(self.frame('result-animation-80.png'),
                                    (990,290,600,150),self.ocr)
        self.assertEqual(amount,80)
        reader = SettlementReader()
        for t in (0,.7,1.6,2.4):
            self.assertIsNone(reader.observe(amount,t,expected=400))
        for t in (3.0,3.7):
            self.assertIsNone(reader.observe(400,t,expected=400))
        self.assertEqual(reader.observe(400,4.4,expected=400),400)

if __name__ == '__main__':
    unittest.main()
