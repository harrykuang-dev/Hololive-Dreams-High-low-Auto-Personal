"""Render the real Tk widgets, with gameplay and global input replaced."""
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import auto_bot
import main_ui
from app_locale import LANGUAGES, TEXT


class FakeHotkey:
    def __init__(self,callback,report,value='F8'):
        self.callback,self.value,self.enabled=callback,value,True
    def start(self): pass
    def configure(self,value=None,enabled=None):
        if value is not None: self.value=value
        if enabled is not None: self.enabled=enabled
    def close(self): self.enabled=False


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        folder=Path(self.temp.name)
        self.patches=[patch.object(main_ui,'SETTINGS_FILE',folder/'settings.json'),
                      patch.object(auto_bot,'DATA_FILE',folder/'daily_coins.json')]
        for p in self.patches: p.start()
        self.root=tk.Tk()
        self.root.withdraw()
        def runner(mode,notify):
            self.calls.append(mode)
            while auto_bot.bot_running: time.sleep(.005)
        self.calls=[]
        self.app=main_ui.HololiveBotUI(self.root,hotkey_factory=FakeHotkey,runner=runner)

    def tearDown(self):
        auto_bot.bot_running=False
        if self.app.worker: self.app.worker.join(1)
        self.app.closing=True
        self.root.destroy()
        for p in reversed(self.patches): p.stop()
        self.temp.cleanup()

    def test_all_languages_render_without_missing_or_mixed_labels(self):
        expected=set(TEXT['en'])
        for name,code in LANGUAGES.items():
            self.assertEqual(set(TEXT[code]),expected)
            self.app.language.set(name)
            self.app.apply_language()
            self.root.update_idletasks()
            self.assertIn(TEXT[code]['game'],self.root.title())
            self.assertEqual(self.app.start_button.cget('text'),TEXT[code]['start'])
            self.assertIn(TEXT[code]['currency'],self.app.coins_label.cget('text'))
        self.assertFalse(hasattr(self.app,'btn_bg'))
        self.assertFalse(hasattr(self.app,'diagnostics'))

    def test_capture_num_lock_plain_and_real_alt_and_duplicate(self):
        self.app.begin_capture('start')
        self.app.capture_key(SimpleNamespace(keysym='q',state=0x8,keycode=0x51))
        self.assertEqual(self.app.start_key,'Q')
        self.app.begin_capture('stop')
        self.app.capture_key(SimpleNamespace(keysym='q',state=0x20008,keycode=0x51))
        self.assertEqual(self.app.stop_key,'Alt+Q')
        self.app.begin_capture('stop')
        self.app.capture_key(SimpleNamespace(keysym='q',state=0x8,keycode=0x51))
        self.assertEqual(self.app.stop_key,'Alt+Q')
        self.assertEqual(self.app.capture_target,'stop')
        self.assertEqual(self.app.history[-1][0],'duplicate')
        self.app.end_capture()
        self.assertTrue(self.app.start_hotkey.enabled)

    def test_start_stop_and_stale_capture_events(self):
        generation=self.app.generation
        self.app.begin_capture('start')
        self.app.post('start_hotkey',generation=generation)
        self.app.poll()
        self.assertFalse(self.app.running)
        self.app.end_capture()
        self.app.post('start_hotkey',generation=self.app.generation)
        self.app.poll()
        self.assertTrue(self.app.running)
        self.assertFalse(self.app.start_hotkey.enabled)
        self.assertTrue(self.app.stop_hotkey.enabled)
        self.app.start()
        self.assertEqual(self.calls,['legacy'])
        self.app.post('stop_hotkey',generation=self.app.generation)
        self.app.poll()
        self.app.worker.join(1)
        self.app.poll()
        self.assertFalse(self.app.running)
        self.assertTrue(self.app.start_hotkey.enabled)

    def test_stats_and_bounded_history_and_settings_survive_restart(self):
        self.app.post('stats',coins=31200,fails=26,wins=7,profit=29550,complete=True)
        self.app.poll()
        self.assertIn('29,550',self.app.profit_label.cget('text'))
        for i in range(120): self.app.record('credit',amount=i)
        self.assertEqual(len(self.app.history),100)
        self.app.language.set('English')
        self.app.strategy_choice.current(1)
        self.app.save_settings()
        self.assertEqual(main_ui.HololiveBotUI.load_settings()['strategy'],1)
        self.assertEqual(main_ui.HololiveBotUI.load_settings()['language'],'English')
        self.assertEqual(sorted(p.name for p in Path(self.temp.name).iterdir()),['settings.json'])

    def test_minimum_layout_fits_longest_language(self):
        self.root.geometry(f'{self.app.px(550)}x{self.app.px(660)}')
        self.root.deiconify()
        for name in LANGUAGES:
            self.app.language.set(name)
            self.app.apply_language()
            self.root.update_idletasks()
            for widget in (self.app.start_entry,self.app.stop_entry,self.app.start_button,
                           self.app.stop_button,self.app.footer):
                x=widget.winfo_rootx()-self.root.winfo_rootx()
                y=widget.winfo_rooty()-self.root.winfo_rooty()
                self.assertGreaterEqual(x,0)
                self.assertGreaterEqual(y,0)
                self.assertLessEqual(x+widget.winfo_width(),self.root.winfo_width())
                self.assertLessEqual(y+widget.winfo_height(),self.root.winfo_height())
            self.assertGreaterEqual(self.app.start_entry.winfo_width(),self.app.px(130))
        self.root.withdraw()

    def test_accounting_error_is_actionable_and_translates(self):
        self.app.post('error',detail='结算金额未能稳定确认，已停止且未将此笔入账。')
        self.app.poll()
        self.assertEqual(self.app.history[-1][0],'error_settlement')
        for name,code in LANGUAGES.items():
            self.app.language.set(name)
            self.app.apply_language()
            self.assertIn(TEXT[code]['error_settlement'],self.app.log.get('1.0','end'))
