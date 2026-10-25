"""Measure real Tk client areas and exercise the version link with UI events."""
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import auto_bot
import main_ui
from app_locale import LANGUAGES, APP_VERSION
from test_gui import FakeHotkey


class WindowLayoutTests(unittest.TestCase):
    @contextmanager
    def interface(self, dpi=120, work_area=None):
        with tempfile.TemporaryDirectory() as folder:
            root=tk.Tk()
            root.withdraw()
            try:
                native=main_ui.window_work_area(root,dpi)
                bounds=work_area or native
                with patch.object(main_ui,'SETTINGS_FILE',Path(folder)/'settings.json'), \
                     patch.object(auto_bot,'DATA_FILE',Path(folder)/'daily_coins.json'), \
                     patch.object(main_ui,'window_dpi',return_value=dpi), \
                     patch.object(main_ui,'window_work_area',return_value=bounds):
                    app=main_ui.HololiveBotUI(root,hotkey_factory=FakeHotkey)
                    root.deiconify()
                    root.update()
                    yield root,app,bounds
                    app.closing=True
            finally:
                for pending in root.tk.splitlist(root.tk.call('after','info')):
                    root.after_cancel(pending)
                root.destroy()

    def test_actual_client_area_scales_and_respects_work_area(self):
        for dpi in (96,120,144,192):
            with self.subTest(dpi=dpi),self.interface(dpi) as (root,app,bounds):
                (left,top,right,bottom),frame_w,frame_h=bounds
                self.assertGreater(frame_w,0)
                self.assertGreater(frame_h,0)
                expected=(min(round(517*dpi/120),right-left-frame_w),
                          min(round(1055*dpi/120),bottom-top-frame_h))
                self.assertEqual((root.winfo_width(),root.winfo_height()),expected)
                self.assertEqual(app.scale,dpi/96)
                # Tk's geometry is the client area, independently checked via Win32.
                rect=wintypes.RECT()
                get_rect=ctypes.windll.user32.GetClientRect
                get_rect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
                self.assertTrue(get_rect(root.winfo_id(),ctypes.byref(rect)))
                self.assertEqual((rect.right,rect.bottom),expected)
                self.assertTrue(all(root.resizable()))

    def test_short_screen_preserves_font_scale_and_scrolls_to_footer(self):
        bounds=((0,0,1200,600),20,50)
        with self.interface(work_area=bounds) as (root,app,_):
            self.assertEqual((root.winfo_width(),root.winfo_height()),(517,550))
            self.assertEqual(app.scale,1.25)
            self.assertEqual(app.page_scroll.winfo_manager(),'pack')
            hwnd=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)
            outer=wintypes.RECT()
            get_outer=ctypes.windll.user32.GetWindowRect
            get_outer.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
            self.assertTrue(get_outer(hwnd,ctypes.byref(outer)))
            self.assertGreaterEqual(outer.top,0)
            self.assertLessEqual(outer.bottom,600)
            for language in LANGUAGES:
                app.language.set(language)
                app.apply_language()
                root.update()
                app.viewport.yview_moveto(0)
                app.version_label.focus_force()
                root.update()
                # Re-focusing an already focused label does not emit FocusIn.
                app.scroll_to_widget(app.version_label)
                root.update()
                top=app.version_label.winfo_rooty()-root.winfo_rooty()
                self.assertGreaterEqual(top,0)
                self.assertLessEqual(top+app.version_label.winfo_height(),root.winfo_height())
                app.viewport.yview_moveto(0)
                app.viewport.event_generate('<MouseWheel>',delta=-120)
                root.update()
                self.assertGreater(app.viewport.yview()[0],0)
            root.geometry('700x900')
            root.update()
            self.assertEqual((root.winfo_width(),root.winfo_height()),(700,900))
            self.assertEqual(app.viewport.yview(),(0.0,1.0))
            self.assertFalse(app.page_scroll.winfo_manager())

    def test_version_link_click_enter_space_in_all_six_languages(self):
        with self.interface() as (root,app,_),patch.object(main_ui.webbrowser,'open') as browser:
            for language in LANGUAGES:
                app.language.set(language)
                app.apply_language()
                root.update()
                self.assertEqual(app.version_label.cget('text'),f'v{APP_VERSION}')
                self.assertEqual(app.version_label.cget('style'),'Muted.TLabel')
                self.assertEqual(str(app.version_label.cget('cursor')),'hand2')
                self.assertTrue(int(app.version_label.cget('takefocus')))
                app.reset_button.focus_force()
                root.update()
                app.reset_button.event_generate('<Shift-Tab>')
                root.update()
                self.assertEqual(root.focus_get(),app.version_label)
                for sequence in ('<Button-1>','<Return>','<space>'):
                    browser.reset_mock()
                    app.version_label.event_generate(sequence,x=3,y=3)
                    root.update()
                    browser.assert_called_once_with(main_ui.REPOSITORY_URL)
                self.assertFalse(app.running)


if __name__=='__main__':
    unittest.main()
