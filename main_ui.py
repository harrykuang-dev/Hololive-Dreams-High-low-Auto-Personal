import ctypes

# Configure DPI before Tk or any capture/input library creates a window. This
# keeps template coordinates aligned on scaled and multi-monitor desktops.
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    pass

import tkinter as tk
from tkinter import ttk
import threading
import sys
import os
import json
import time
import re
from PIL import Image, ImageTk
import keyboard

import auto_bot

# 🚀 必须在窗口创建前执行：通知 Windows 这是一个独立应用，强制任务栏绑定自身图标
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("hololive.dreams.autobot.v1")
except Exception:
    pass

# ================= 多语言翻译字典 =================
TRANSLATIONS = {
    "zh": {
        "title": "Hololive Dreams 自动猜高低",
        "lang_label": "界面语言",
        "hotkey_label": "停止快捷键",
        "status_idle": "状态：等待启动",
        "coins_prefix": "金币：{coins} / 20000",
        "btn_exit": "退出",
        "btn_start": "启动挂机",
        "btn_stop": "停止挂机",
        "btn_bg": "切换背景",
        "btn_running": "运行中..."
    },
    "tw": {
        "title": "Hololive Dreams 自動猜高低",
        "lang_label": "介面語言",
        "hotkey_label": "停止快捷鍵",
        "status_idle": "狀態：等待啟動",
        "coins_prefix": "金幣：{coins} / 20000",
        "btn_exit": "退出",
        "btn_start": "啟動掛機",
        "btn_stop": "停止掛機",
        "btn_bg": "切換背景",
        "btn_running": "運行中..."
    },
    "en": {
        "title": "Hololive Dreams Auto Bot",
        "lang_label": "Language",
        "hotkey_label": "Stop Hotkey",
        "status_idle": "Status: Waiting",
        "coins_prefix": "Coins: {coins} / 20000",
        "btn_exit": "Exit",
        "btn_start": "Start Bot",
        "btn_stop": "Stop Bot",
        "btn_bg": "Toggle BG",
        "btn_running": "Running..."
    },
    "ja": {
        "title": "Hololive Dreams 自動Bot",
        "lang_label": "言語",
        "hotkey_label": "停止ショートカット",
        "status_idle": "ステータス: 待機中",
        "coins_prefix": "コイン: {coins} / 20000",
        "btn_exit": "終了",
        "btn_start": "起動",
        "btn_stop": "停止",
        "btn_bg": "背景切替",
        "btn_running": "実行中..."
    }
}


STRATEGY_LABELS = {
    'zh': ('1.0.1 原版', '三阶段：最大 → 计次 → 最大'),
    'tw': ('1.0.1 原版', '三階段：最大 → 計次 → 最大'),
    'en': ('1.0.1 Legacy', '3 stages: Max → Win count → Max'),
    'ja': ('1.0.1 従来モード', '3段階：最大 → 成功回数 → 最大'),
}


def get_local_data():
    if auto_bot.DATA_FILE.exists():
        try:
            with auto_bot.DATA_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == time.strftime("%Y-%m-%d"):
                    c = data.get("coins", 0)
                    fl = data.get("fails", 0)
                    return c, fl, c - (fl * 50)
        except:
            pass
    return 0, 0, 0


# ================= 拦截底层输出，虚拟滚动核心引擎 =================
class RedirectText:
    def __init__(self, ui):
        self.ui = ui
        self.raw_text = ""

    def write(self, string):
        self.ui.after(0, self._write, string)

    def _write(self, string):
        if not string: return
        self.raw_text += string

        if "今日净利润:" in string:
            m_profit = re.search(r"今日净利润:\s*([+-]?\d+)", string)
            m_fails = re.search(r"累计失败:\s*(\d+)", string)
            m_coins = re.search(r"当前总金币:\s*(\d+)", string) or re.search(r"当日累计代币:\s*(\d+)", string)

            coins = int(m_coins.group(1)) if m_coins else self.ui.current_coins
            fails = int(m_fails.group(1)) if m_fails else self.ui.current_fails
            profit = int(m_profit.group(1)) if m_profit else self.ui.current_profit

            self.ui.update_stats_display(coins, fails, profit)

        if len(self.raw_text) > 15000:
            self.raw_text = self.raw_text[-15000:]
            newline_idx = self.raw_text.find('\n')
            if newline_idx != -1:
                self.raw_text = self.raw_text[newline_idx + 1:]

        self.ui.log_lines = self.raw_text.split('\n')
        self.ui.log_view_start = max(0, len(self.ui.log_lines) - self.ui.log_max_lines)
        self.ui.update_log_view()

    def flush(self):
        pass

    def clear(self):
        self.raw_text = ""
        self.ui.log_lines = []
        self.ui.log_view_start = 0
        self.ui.update_log_view()


class HololiveBotUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.bot_thread = None
        self.is_running = False
        self.current_lang = "zh"
        self.show_bg = True

        self.current_coins, self.current_fails, self.current_profit = get_local_data()

        self.title(TRANSLATIONS[self.current_lang]["title"])
        # 🚀 替换这里的两行：优先加载 PNG 图标，任务栏永不退化为白纸
        try:
            transparent_icon = auto_bot.RESOURCE_DIR / "icon_transparent.png"
            png_icon = auto_bot.RESOURCE_DIR / "icon.png"
            ico_icon = auto_bot.RESOURCE_DIR / "icon.ico"
            if transparent_icon.exists():
                self._app_icon = ImageTk.PhotoImage(file=str(transparent_icon))
                self.iconphoto(True, self._app_icon)
            elif png_icon.exists():
                self._app_icon = ImageTk.PhotoImage(file=str(png_icon))
                self.iconphoto(True, self._app_icon)
            elif ico_icon.exists():
                self.iconbitmap(str(ico_icon))
        except Exception as e:
            print(f"[警告] 图标加载失败: {e}")

        self.geometry("450x800")
        self.minsize(360, 640)

        self.last_w = 450
        self.last_h = 800

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_image_path = auto_bot.RESOURCE_DIR / "background.png"
        if self.bg_image_path.exists():
            self.original_bg = Image.open(self.bg_image_path)
        else:
            self.original_bg = Image.new('RGB', (450, 800), color='#F0F0F0')
            self.show_bg = False

        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        font_title = ("Microsoft YaHei", 16, "bold")
        font_normal = ("Microsoft YaHei", 12, "bold")
        font_log = ("Microsoft YaHei", 12, "bold")

        self.title_id = self.canvas.create_text(0, 0, font=font_title, fill="#111111")

        self.lang_label_id = self.canvas.create_text(0, 0, font=font_normal, fill="#111111", anchor="w")
        self.lang_keys = ["zh", "tw", "en", "ja"]
        self.combo_lang = ttk.Combobox(self, values=["简体中文", "繁體中文", "English", "日本語"], state="readonly")
        self.combo_lang.current(0)
        self.combo_lang.bind("<<ComboboxSelected>>", self.change_language)
        self.combo_window = self.canvas.create_window(0, 0, window=self.combo_lang, anchor="e")

        self.hotkey_label_id = self.canvas.create_text(0, 0, font=font_normal, fill="#111111", anchor="w")
        self.current_hotkey = "INSERT"
        self.is_listening = False

        self.btn_hotkey = ttk.Button(self, text=self.current_hotkey, command=self.start_listen_hotkey)
        self.hotkey_window = self.canvas.create_window(0, 0, window=self.btn_hotkey, anchor="e")

        keyboard.add_hotkey(self.current_hotkey, lambda: self.after(0, self.stop_bot))

        self.status_id = self.canvas.create_text(0, 0, font=font_normal, fill="#111111", anchor="w")
        self.coins_id = self.canvas.create_text(0, 0, font=font_normal, fill="#111111", anchor="w")

        self.log_text_id = self.canvas.create_text(0, 0, font=font_log, fill="#000000", anchor="nw", justify="left")
        self.log_lines = []
        # 🚀 修改 1：因为长文字折行后会占用两行的空间，把最大行数稍微调小（从 16 降到 13），防止底部文字被截断
        self.log_max_lines = 13
        self.log_view_start = 0

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.scroll_log)
        self.scrollbar_win = self.canvas.create_window(0, 0, window=self.scrollbar, anchor="ne")
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        self.btn_next = ttk.Button(self, command=self.start_bot)
        self.btn_stop = ttk.Button(self, command=self.stop_bot, state="disabled")
        self.btn_bg = ttk.Button(self, command=self.toggle_bg)
        self.btn_exit = ttk.Button(self, command=self.destroy)

        self.btn_next_win = self.canvas.create_window(0, 0, window=self.btn_next)
        self.btn_stop_win = self.canvas.create_window(0, 0, window=self.btn_stop)
        self.btn_bg_win = self.canvas.create_window(0, 0, window=self.btn_bg)
        self.btn_exit_win = self.canvas.create_window(0, 0, window=self.btn_exit)

        self.combo_strategy = ttk.Combobox(self, state='readonly',
                                           values=STRATEGY_LABELS[self.current_lang])
        self.combo_strategy.current(0)
        self.strategy_window = self.canvas.create_window(0, 0, window=self.combo_strategy, anchor='nw')
        self.active_mode = 'legacy'

        self.sys_redirector = RedirectText(self)
        self.original_stdout = sys.stdout
        sys.stdout = self.sys_redirector

        self.canvas.bind("<Configure>", self.on_resize)
        self.resize_after_id = None

        self.refresh_texts()

    def start_listen_hotkey(self):
        if self.is_listening or self.is_running:
            return

        self.is_listening = True
        self.btn_hotkey.configure(text="[按键...]")
        print("\n[系统] 请点击键盘上想要切换的键...")

        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        time.sleep(0.1)
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                key = event.name.upper()
                break

        self.after(0, self._apply_new_hotkey, key)

    def _apply_new_hotkey(self, new_key):
        self.is_listening = False
        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except:
            pass

        self.current_hotkey = new_key
        try:
            keyboard.add_hotkey(self.current_hotkey, lambda: self.after(0, self.stop_bot))
            self.btn_hotkey.configure(text=self.current_hotkey)
            print(f"[系统] 停止快捷键已成功更换为: {self.current_hotkey}\n")
        except Exception as e:
            print(f"[系统] 无法绑定按键 '{new_key}'，已自动恢复默认 F11\n")
            self.current_hotkey = "F11"
            keyboard.add_hotkey(self.current_hotkey, lambda: self.after(0, self.stop_bot))
            self.btn_hotkey.configure(text=self.current_hotkey)

    def on_mouse_wheel(self, event):
        direction = -1 if event.delta > 0 else 1
        self.scroll_log('scroll', direction * 3)

    def scroll_log(self, *args):
        if not self.log_lines: return

        if args[0] == 'moveto':
            fraction = float(args[1])
            self.log_view_start = int(fraction * len(self.log_lines))
        elif args[0] == 'scroll':
            self.log_view_start += int(args[1])

        max_start = max(0, len(self.log_lines) - self.log_max_lines)
        self.log_view_start = max(0, min(self.log_view_start, max_start))
        self.update_log_view()

    def update_log_view(self):
        max_start = max(0, len(self.log_lines) - self.log_max_lines)
        if len(self.log_lines) == 0:
            self.scrollbar.set(0.0, 1.0)
            visible = []
        else:
            fraction = self.log_view_start / max(1, len(self.log_lines))
            fraction_end = (self.log_view_start + self.log_max_lines) / max(1, len(self.log_lines))
            self.scrollbar.set(fraction, fraction_end)
            visible = self.log_lines[self.log_view_start: self.log_view_start + self.log_max_lines]

        self.canvas.itemconfig(self.log_text_id, text='\n'.join(visible))

    def on_resize(self, event):
        if event.widget != self.canvas: return
        w, h = event.width, event.height
        if w <= 10 or h <= 10: return

        target_h = int(w * 16 / 9)
        target_w = int(h * 9 / 16)

        if abs(h - target_h) <= 2:
            self.last_w, self.last_h = w, h
            self.draw_ui(w, h)
            return

        delta_w = abs(w - self.last_w)
        delta_h = abs(h - self.last_h)

        if delta_w > delta_h / (16 / 9):
            new_w = w
            new_h = target_h
        else:
            new_w = target_w
            new_h = h

        if self.resize_after_id:
            self.after_cancel(self.resize_after_id)
        self.resize_after_id = self.after(20, lambda: self.geometry(f"{new_w}x{new_h}"))

    def draw_ui(self, w, h):
        if self.show_bg:
            img = self.original_bg.resize((w, h), Image.Resampling.LANCZOS)
        else:
            img = Image.new('RGB', (w, h), color='#FFFFFF')

        self.bg_photo = ImageTk.PhotoImage(img)
        self.canvas.itemconfig(self.bg_id, image=self.bg_photo)

        self.canvas.coords(self.title_id, w / 2, h * 0.05)

        self.canvas.coords(self.lang_label_id, w * 0.08, h * 0.10)
        self.canvas.coords(self.combo_window, w * 0.92, h * 0.10)
        self.canvas.itemconfig(self.combo_window, width=w * 0.25)

        self.canvas.coords(self.hotkey_label_id, w * 0.08, h * 0.15)
        self.canvas.coords(self.hotkey_window, w * 0.92, h * 0.15)
        self.canvas.itemconfig(self.hotkey_window, width=w * 0.25)

        self.canvas.coords(self.status_id, w * 0.08, h * 0.21)
        self.canvas.coords(self.coins_id, w * 0.08, h * 0.27)

        btn_w = w * 0.38
        btn_h = h * 0.045

        self.canvas.coords(self.btn_next_win, w * 0.28, h * 0.34)
        self.canvas.itemconfig(self.btn_next_win, width=btn_w, height=btn_h)
        self.canvas.coords(self.btn_stop_win, w * 0.72, h * 0.34)
        self.canvas.itemconfig(self.btn_stop_win, width=btn_w, height=btn_h)

        self.canvas.coords(self.btn_bg_win, w * 0.28, h * 0.40)
        self.canvas.itemconfig(self.btn_bg_win, width=btn_w, height=btn_h)
        self.canvas.coords(self.btn_exit_win, w * 0.72, h * 0.40)
        self.canvas.itemconfig(self.btn_exit_win, width=btn_w, height=btn_h)

        log_x = w * 0.06
        self.canvas.coords(self.strategy_window, w * .06, h * .445)
        self.canvas.itemconfig(self.strategy_window, width=w * .88)
        log_y = h * 0.50
        self.canvas.coords(self.log_text_id, log_x, log_y)

        # 🚀 修改 2：给日志文字设定最大物理宽度。当碰到距离右侧 15% 的边界时，强行折行！
        self.canvas.itemconfig(self.log_text_id, width=w * 0.85)

        self.canvas.coords(self.scrollbar_win, w * 0.98, log_y)
        self.canvas.itemconfig(self.scrollbar_win, height=h * 0.45)

    def toggle_bg(self):
        self.show_bg = not self.show_bg
        self.draw_ui(self.winfo_width(), self.winfo_height())

    def update_stats_display(self, coins=None, fails=None, profit=None):
        if coins is not None: self.current_coins = coins
        if fails is not None: self.current_fails = fails
        if profit is not None: self.current_profit = profit

        t = TRANSLATIONS[self.current_lang]
        base_text = t["coins_prefix"].replace("{coins}", str(self.current_coins))
        display_str = f"{base_text}\n净利: {self.current_profit:+d} | 失败: {self.current_fails}"
        self.canvas.itemconfig(self.coins_id, text=display_str)

    def refresh_texts(self):
        t = TRANSLATIONS[self.current_lang]
        selected_strategy = self.combo_strategy.current()
        self.combo_strategy.configure(values=STRATEGY_LABELS[self.current_lang],
                                      state='disabled' if self.is_running else 'readonly')
        self.combo_strategy.current(max(0, selected_strategy))
        self.title(t["title"])
        self.canvas.itemconfig(self.title_id, text=t["title"])
        self.canvas.itemconfig(self.lang_label_id, text=t["lang_label"])
        self.canvas.itemconfig(self.hotkey_label_id, text=t["hotkey_label"])

        self.btn_bg.configure(text=t["btn_bg"])
        self.btn_exit.configure(text=t["btn_exit"])

        self.update_stats_display()

        if not self.is_running:
            self.canvas.itemconfig(self.status_id, text=t["status_idle"], fill="#111111")
            self.btn_next.configure(text=t["btn_start"], state="normal")
            self.btn_stop.configure(text=t["btn_stop"], state="disabled")
            self.btn_hotkey.configure(state="normal")
        else:
            self.btn_next.configure(text=t["btn_running"], state="disabled")
            self.btn_stop.configure(text=t["btn_stop"], state="normal")
            self.btn_hotkey.configure(state="disabled")

    def change_language(self, event=None):
        idx = self.combo_lang.current()
        self.current_lang = self.lang_keys[idx]
        self.refresh_texts()

    def start_bot(self):
        self.active_mode = 'phased' if self.combo_strategy.current() == 1 else 'legacy'
        self.is_running = True
        self.refresh_texts()
        self.canvas.itemconfig(self.status_id,
                               text="状态：运行中..." if self.current_lang in ["zh", "tw"] else "Status: Running...",
                               fill="green")

        self.sys_redirector.clear()

        auto_bot.bot_running = True
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        if not self.is_running: return

        print(f"\n[系统] 收到停止指令 (或按下了快捷键)，正在等待当前动作完成并安全退出...")
        auto_bot.bot_running = False
        self.btn_stop.configure(state="disabled")
        self.canvas.itemconfig(self.status_id,
                               text="状态：正在停止..." if self.current_lang in ["zh", "tw"] else "Status: Stopping...",
                               fill="orange")

    def run_bot(self):
        try:
            auto_bot.auto_play_loop(self.active_mode)
        except Exception as e:
            print(f"崩溃异常: {e}")
            self.canvas.itemconfig(self.status_id, text="状态：崩溃异常", fill="red")
        finally:
            self.is_running = False
            auto_bot.bot_running = False
            self.refresh_texts()
            print("\n[系统] 挂机已完全停止。")

    def destroy(self):
        sys.stdout = self.original_stdout
        keyboard.unhook_all()
        super().destroy()


if __name__ == "__main__":
    app = HololiveBotUI()
    app.mainloop()
