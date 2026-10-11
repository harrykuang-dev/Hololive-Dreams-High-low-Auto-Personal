"""Render the real Tk widgets, with gameplay and global input replaced."""
import tempfile
import time
import tkinter as tk
import unittest
import json
from datetime import datetime
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
        for pending in self.root.tk.splitlist(self.root.tk.call('after','info')):
            self.root.after_cancel(pending)
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
            self.assertEqual(self.app.language_label.cget('text'),
                             dict(en='Language',tw='語言/Language',ja='言語/Language',
                                  ko='언어/Language',id='Bahasa/Language',zh='语言/Language')[code])
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
        self.app.strategy_buttons[1].invoke()
        self.app.save_settings()
        self.assertEqual(main_ui.HololiveBotUI.load_settings()['strategy'],1)
        self.assertEqual(main_ui.HololiveBotUI.load_settings()['language'],'English')
        self.assertEqual(sorted(p.name for p in Path(self.temp.name).iterdir()),['settings.json'])

    def test_minimum_layout_fits_longest_language(self):
        self.root.deiconify()
        self.root.update()
        for width,height in ((360,640),(450,800),(600,900)):
            self.root.geometry(f'{self.app.px(width)}x{self.app.px(height)}')
            for name in LANGUAGES:
                self.app.language.set(name)
                self.app.apply_language()
                self.root.update()
                for widget in (self.app.start_entry,self.app.stop_entry,self.app.start_button,
                               self.app.stop_button,self.app.reset_button,self.app.strategy_help,
                               self.app.game_logo,self.app.title_label,self.app.coins_label,
                               self.app.profit_label,self.app.counts_label,*self.app.strategy_buttons):
                    x=widget.winfo_rootx()-self.root.winfo_rootx()
                    y=widget.winfo_rooty()-self.root.winfo_rooty()
                    self.assertGreaterEqual(x,0)
                    self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+widget.winfo_width(),self.root.winfo_width())
                    self.assertLessEqual(y+widget.winfo_height(),self.root.winfo_height())
                self.assertGreaterEqual(self.app.start_entry.winfo_width(),self.app.px(130))
                self.assertGreater(self.app.log.winfo_height(),self.app.px(20))
        self.root.withdraw()

    def test_resize_burst_coalesces_and_unchanged_layout_is_not_reconfigured(self):
        self.root.deiconify()
        self.root.update()
        event=SimpleNamespace(width=self.app.main.winfo_width(),height=self.app.main.winfo_height())
        with patch.object(self.app,'resize_text',wraps=self.app.resize_text) as resize:
            for _ in range(100): self.app.schedule_resize(event)
            self.root.update_idletasks()
            self.assertEqual(resize.call_count,1)
        with patch.object(self.app.instructions,'configure',wraps=self.app.instructions.configure) as label:
            for _ in range(100): self.app.resize_text(event)
            self.assertEqual(label.call_count,0)
        self.root.geometry(f'{self.app.px(360)}x{self.app.px(640)}')
        self.root.update()
        self.assertTrue(self.app.compact)
        self.assertEqual(int(self.app.instructions.cget('wraplength')),self.app.px(328))
        with patch.object(self.app.strategy_buttons[1],'grid_configure') as grid:
            row=self.app.strategy_buttons[0].master
            for _ in range(100): self.app.layout_strategies(SimpleNamespace(width=row.winfo_width()))
            self.assertEqual(grid.call_count,0)

    def test_help_dialog_tracks_program_position_and_stays_on_screen(self):
        self.root.deiconify()
        self.root.geometry(f'{self.app.px(450)}x{self.app.px(800)}+600+60')
        self.root.update()
        self.app.show_strategy_help()
        self.root.update()
        dialog=self.app.help_dialog
        def centre(widget):
            return (widget.winfo_rootx()+widget.winfo_width()/2,
                    widget.winfo_rooty()+widget.winfo_height()/2)
        for actual,expected in zip(centre(dialog),centre(self.root)):
            self.assertLess(abs(actual-expected),self.app.px(24))
        self.app.close_strategy_help()
        self.root.geometry('+0+0')
        self.root.update()
        self.app.show_strategy_help()
        self.root.update()
        self.assertGreaterEqual(self.app.help_dialog.winfo_rootx(),0)
        self.assertGreaterEqual(self.app.help_dialog.winfo_rooty(),0)

    def test_reset_confirmation_cancel_preserves_file_and_blocks_hotkey_start(self):
        auto_bot.save_daily_data(6400,2,2,3,True)
        original=auto_bot.DATA_FILE.read_bytes()
        def cancel(*args,**kwargs):
            self.assertEqual(kwargs['default'],'no')
            self.assertFalse(self.app.start_hotkey.enabled)
            self.assertFalse(self.app.stop_hotkey.enabled)
            self.app.start()
            self.assertFalse(self.app.running)
            return False
        with patch.object(main_ui.messagebox,'askyesno',side_effect=cancel):
            self.app.reset_daily_stats()
        self.assertEqual(auto_bot.DATA_FILE.read_bytes(),original)
        self.assertTrue(self.app.start_hotkey.enabled)

    def test_confirmed_reset_clears_all_stats_and_stage_and_is_disabled_while_running(self):
        auto_bot.save_daily_data(6400,2,2,3,True)
        with patch.object(main_ui.messagebox,'askyesno',return_value=True) as ask:
            self.app.reset_daily_stats()
            self.assertEqual(auto_bot.load_daily_data(),(0,0))
            self.assertEqual(auto_bot.load_daily_wins(),(0,True))
            self.assertEqual(auto_bot.load_daily_stage(),0)
            self.assertEqual(self.app.stats['profit'],0)
            self.app.start()
            self.assertEqual(str(self.app.reset_button.cget('state')),'disabled')
            self.app.reset_daily_stats()
            self.assertEqual(ask.call_count,1)

    def test_idle_window_rolls_over_at_four_without_restarting(self):
        with patch('daily_accounting.datetime') as clock:
            clock.now.return_value=datetime(2026,10,11,3,59,59)
            auto_bot.save_daily_data(12800,3,2,2,True)
            self.app.stats=self.app.read_stats()
            self.app.ledger_day=self.app.stats['day']
            self.app.poll()
            self.assertEqual(self.app.stats['coins'],12800)
            clock.now.return_value=datetime(2026,10,11,4)
            self.app.poll()
            self.assertEqual(self.app.stats['coins'],0)
            self.assertEqual(self.app.stats['wins'],0)
            self.assertEqual(self.app.stats['fails'],0)
            self.assertEqual(auto_bot.load_daily_stage(),0)
            self.assertEqual(json.loads(auto_bot.DATA_FILE.read_text())['date'],'2026-10-11')

    def test_shortcut_fields_are_white_and_multisize_card_icon_is_loaded(self):
        self.assertEqual(self.app.start_entry.cget('readonlybackground'),'white')
        self.assertEqual(self.app.stop_entry.cget('readonlybackground'),'white')
        self.assertEqual([(image.width(),image.height()) for image in self.app._app_icons],
                         [(256,256),(48,48),(32,32),(16,16)])
        for entry in (self.app.start_entry,self.app.stop_entry):
            self.assertEqual(entry.cget('borderwidth'),0)
            self.assertEqual(entry.cget('highlightthickness'),0)
        for name,code in LANGUAGES.items():
            self.app.language.set(name)
            self.app.apply_language()
            self.assertNotIn('\n',self.app.instructions.cget('text'))

    def test_strategy_help_translates_preserves_selection_and_keeps_stop_available(self):
        self.app.strategy_buttons[1].invoke()
        for name,code in LANGUAGES.items():
            self.app.language.set(name)
            self.app.apply_language()
            self.app.show_strategy_help()
            self.root.update_idletasks()
            dialog=self.app.help_dialog
            self.assertEqual(dialog.title(),TEXT[code]['strategy_help'])
            def label_texts(widget):
                labels=[widget.cget('text')] if 'text' in widget.keys() else []
                for child in widget.winfo_children(): labels.extend(label_texts(child))
                return labels
            labels=label_texts(dialog.winfo_children()[0])
            self.assertIn(TEXT[code]['legacy_help'],labels)
            self.assertIn(TEXT[code]['phased_help'],labels)
            self.assertEqual(self.app.strategy.get(),1)
            self.assertFalse(self.app.start_hotkey.enabled)
            self.assertTrue(self.app.stop_hotkey.enabled)
            self.app.start()
            self.assertFalse(self.app.running)
            self.app.close_strategy_help()
            self.assertTrue(self.app.start_hotkey.enabled)
        self.app.start()
        self.app.show_strategy_help()
        self.app.post('stop_hotkey',generation=self.app.generation)
        self.app.poll()
        self.app.worker.join(1)
        self.app.poll()
        self.assertFalse(self.app.running)
        self.assertEqual(self.calls,['phased'])

    def test_radio_selection_survives_language_change_and_cannot_change_during_play(self):
        self.assertEqual(self.app.strategy.get(),0)
        self.app.strategy_buttons[1].invoke()
        self.assertEqual(main_ui.HololiveBotUI.load_settings()['strategy'],1)
        for name,code in LANGUAGES.items():
            self.app.language.set(name)
            self.app.change_language()
            self.assertEqual(self.app.strategy.get(),1)
            self.assertEqual([button.cget('text') for button in self.app.strategy_buttons],
                             [TEXT[code]['legacy'],TEXT[code]['phased']])
        self.app.start()
        self.assertTrue(all(button.instate(['disabled']) for button in self.app.strategy_buttons))
        self.app.strategy_buttons[0].invoke()
        self.assertEqual(self.app.strategy.get(),1)
        self.assertEqual(self.calls,['phased'])

    def test_accounting_error_is_actionable_and_translates(self):
        self.app.post('error',detail='结算金额未能稳定确认，已停止且未将此笔入账。')
        self.app.poll()
        self.assertEqual(self.app.history[-1][0],'error_settlement')
        for name,code in LANGUAGES.items():
            self.app.language.set(name)
            self.app.apply_language()
            self.assertIn(TEXT[code]['error_settlement'],self.app.log.get('1.0','end'))
