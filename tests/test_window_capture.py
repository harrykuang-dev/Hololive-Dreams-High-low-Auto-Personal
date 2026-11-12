from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import auto_bot


class WindowCaptureTests(unittest.TestCase):
    def setUp(self):
        self.window = SimpleNamespace(_hWnd=31, restore=Mock())
        self.user32 = Mock()
        self.user32.IsWindowVisible.return_value = True
        self.user32.IsIconic.return_value = False
        self.user32.GetForegroundWindow.return_value = self.window._hWnd
        self.enterContext(patch.object(auto_bot, '_user32', self.user32))
        self.enterContext(patch.object(auto_bot, '_capture_context', {'hwnd': 31}))
        self.enterContext(patch.object(auto_bot, 'find_game_window', return_value=self.window))
        self.geometry = self.enterContext(patch.object(
            auto_bot, '_get_client_geometry', return_value=(100, 150, 1600, 900)))
        self.capture = self.enterContext(patch.object(auto_bot, '_capture_client_with_printwindow'))

    def test_capture_waits_while_minimized_and_resumes_after_restore(self):
        self.user32.IsIconic.return_value = True
        self.assertEqual(auto_bot.capture_game_window(), (None, 0, 0))
        self.assertIsNone(auto_bot._capture_context)
        self.capture.assert_not_called()
        self.window.restore.assert_not_called()
        self.user32.SetForegroundWindow.assert_not_called()

        self.user32.IsIconic.return_value = False
        with patch.object(auto_bot.cv2, 'resize', return_value='frame'):
            self.assertEqual(auto_bot.capture_game_window(), ('frame', 100, 150))
        self.assertEqual(auto_bot._capture_context, {'hwnd': 31, 'width': 1600, 'height': 900})

    def test_title_only_window_is_neither_captured_nor_activated(self):
        self.geometry.return_value = (-31991, -31962, 181, 0)
        self.assertEqual(auto_bot.capture_game_window(), (None, 0, 0))
        self.assertFalse(auto_bot._bring_game_to_front(self.window._hWnd))
        self.capture.assert_not_called()
        self.user32.SetForegroundWindow.assert_not_called()
        self.assertIsNone(auto_bot._capture_context)

    def test_minimizing_during_failed_capture_never_triggers_foreground_fallback(self):
        def minimize(*_):
            self.user32.IsIconic.return_value = True
            raise RuntimeError('Capture interrupted')

        self.capture.side_effect = minimize
        with patch.object(auto_bot.mss, 'MSS') as screen:
            self.assertEqual(auto_bot.capture_game_window(), (None, 0, 0))
            screen.assert_not_called()
        self.user32.SetForegroundWindow.assert_not_called()
        self.assertIsNone(auto_bot._capture_context)
