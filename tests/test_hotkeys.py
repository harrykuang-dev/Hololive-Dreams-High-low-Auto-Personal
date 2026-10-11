import unittest
import ctypes
from ctypes import wintypes
import queue
import sys
import threading
from hotkey_settings import captured_hotkey, parse_stop_hotkey
from global_hotkey import GlobalHotkey, WM_HOTKEY, windows_hotkey, matches_hotkey


class ShortcutTests(unittest.TestCase):
    def test_num_lock_does_not_turn_plain_or_ctrl_keys_into_alt(self):
        for lock in (0,0x8,0x2,0x20,0x2A,0x40008):
            for sym,vk,key in (('F8',0x77,'F8'),('q',0x51,'Q'),('KP_1',0x61,'Num1')):
                self.assertEqual(captured_hotkey(sym,lock,vk),key)
                self.assertEqual(captured_hotkey(sym,lock|4,vk),'Ctrl+'+key)
                self.assertEqual(captured_hotkey(sym,lock|0x20000,vk),'Alt+'+key)
                self.assertEqual(captured_hotkey(sym,lock|0x20005,vk),'Ctrl+Alt+Shift+'+key)

    def test_physical_shift_key_and_modifier_only(self):
        self.assertEqual(captured_hotkey('exclam',0x9,0x31),'Shift+1')
        for key,vk in (('Alt_L',0x12),('Control_L',0x11),('Shift_L',0x10)):
            self.assertIsNone(captured_hotkey(key,0x2000D,vk))

    def test_registration_requires_exact_modifiers(self):
        self.assertEqual(windows_hotkey('Alt+Q'),(1,0x51))
        self.assertTrue(matches_hotkey(0,0x77,0x77<<16))
        self.assertFalse(matches_hotkey(0,0x77,(0x77<<16)|1))
        self.assertTrue(matches_hotkey(1,0x51,(0x51<<16)|1))
        self.assertFalse(matches_hotkey(1,0x51,(0x51<<16)|3))
        self.assertFalse(matches_hotkey(0,0x77,(0x77<<16)|8))

    def test_shortcut_aliases_and_invalid_keys(self):
        self.assertEqual(parse_stop_hotkey('INSERT'),((),0x2D))
        for key in ('Alt','Ctrl+','Win+Q','Ctrl+Ctrl+Q'):
            with self.assertRaises(ValueError): parse_stop_hotkey(key)

    @unittest.skipUnless(sys.platform=='win32','Windows hotkey integration')
    def test_native_registration_dispatch_rebind_and_cleanup(self):
        events=queue.Queue()
        fired=threading.Event()
        listener=GlobalHotkey(fired.set,lambda *values:events.put(values),value='F24')
        listener.start()
        try:
            value,ok,error=events.get(timeout=2)
            if not ok: self.skipTest(f'F24 reserved by another application: {error}')
            user=ctypes.WinDLL('user32',use_last_error=True)
            post=user.PostThreadMessageW
            post.argtypes=(wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM)
            post.restype=wintypes.BOOL
            mods,key=windows_hotkey('F24')
            self.assertTrue(post(listener.thread_id,WM_HOTKEY,listener.registration_id,(key<<16)|1))
            self.assertFalse(fired.wait(.05))
            self.assertTrue(post(listener.thread_id,WM_HOTKEY,listener.registration_id,key<<16))
            self.assertTrue(fired.wait(1))
            listener.configure(value='Alt+F23')
            value,ok,error=events.get(timeout=2)
            self.assertEqual(value,'Alt+F23')
            self.assertTrue(ok,error)
            fired.clear()
            mods,key=windows_hotkey(value)
            self.assertTrue(post(listener.thread_id,WM_HOTKEY,listener.registration_id,(key<<16)|mods))
            self.assertTrue(fired.wait(1))
        finally:
            listener.close()
            listener.thread.join(1)
        self.assertIsNone(listener.registration_id)
        self.assertFalse(listener.thread.is_alive())
