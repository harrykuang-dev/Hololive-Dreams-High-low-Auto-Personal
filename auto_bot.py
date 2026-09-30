import pygetwindow as gw
import mss
import numpy as np
import cv2
import pydirectinput
import ctypes
from ctypes import wintypes
import random
import time
import os
import json
import sys
from pathlib import Path
import ddddocr

from recognizer import CardRecognizer
from poker_core import calculate_best, JOKER_ID
from settlement import SettlementReader
from reward_vision import read_challenge_number, read_result_number as read_result_digits
from challenge_reward import ChallengeRewardReader
from phased_strategy import PhasedStrategy

try:
    # Windows source-mode runs otherwise inherit a legacy console encoding and
    # crash on the existing multilingual/emoji status messages.
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 直接全局初始化 OCR 引擎
ocr = ddddocr.DdddOcr(show_ad=False)

bot_running = False
# ================= 全局配置与常量 =================
GAME_TITLE = "hololive-Dreams"
TARGET_LIMIT = 19800

# All bundled assets are resolved relative to the executable/source directory.
# The old code depended on the process working directory, so launching from a
# shortcut or another folder made every template silently disappear.
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)).resolve()
TEMPLATE_DIR = RESOURCE_DIR / "templates"
DATA_FILE = APP_DIR / "daily_coins.json"

# Icon templates and hard-coded recognition zones were captured at 1920x1080.
# Every game frame is normalized to this size before matching/recognition, and
# clicks are transformed back to the actual client size.
REFERENCE_WIDTH = 1920
REFERENCE_HEIGHT = 1080


def resource_path(*parts):
    return str(RESOURCE_DIR.joinpath(*parts))


try:
    # Must happen before Tk creates a window. It keeps Win32 coordinates,
    # PrintWindow output and SendInput coordinates in the same DPI space.
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    pass


_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32
_capture_context = None

_user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetClientRect.restype = wintypes.BOOL
_user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
_user32.ClientToScreen.restype = wintypes.BOOL
_user32.GetDC.argtypes = [wintypes.HWND]
_user32.GetDC.restype = wintypes.HDC
_user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
_user32.ReleaseDC.restype = ctypes.c_int
_user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
_user32.PrintWindow.restype = wintypes.BOOL
_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL
_user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.BringWindowToTop.argtypes = [wintypes.HWND]
_user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, wintypes.UINT]

_gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
_gdi32.CreateCompatibleDC.restype = wintypes.HDC
_gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
_gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
_gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_gdi32.SelectObject.restype = wintypes.HGDIOBJ
_gdi32.GetBitmapBits.argtypes = [wintypes.HBITMAP, wintypes.LONG, wintypes.LPVOID]
_gdi32.GetBitmapBits.restype = wintypes.LONG
_gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
_gdi32.DeleteDC.argtypes = [wintypes.HDC]

# === 动态寻框参数 ===
CARD_WIDTH = 260
# 超大搜索区，覆盖整个屏幕中段，彻底杜绝漏抓
HIGH_LOW_SEARCH_ZONE = (42, 358, 1256, 451)

# 💰 奖金黄字 OCR 识别区 (!!! 必须用 get_coords.py 重新量取你的黄色数字坐标 !!!)
REWARD_ZONE = (606, 389, 870, 253)

# 💰 结算蓝字 OCR 识别区 (已保留你量好的数据)
RESULT_REWARD_ZONE = (990, 290, 600, 150)

upcoming_card_val = None


# === 真实点数映射表 ===
def get_real_card_value(card):
    if card.card_id == JOKER_ID:
        return 0

    raw = str(card.rank).upper().strip()
    if "." in raw:
        raw = raw.split(".")[-1]

    robust_map = {
        "2": 2, "TWO": 2,
        "3": 3, "THREE": 3,
        "4": 4, "FOUR": 4,
        "5": 5, "FIVE": 5,
        "6": 6, "SIX": 6,
        "7": 7, "SEVEN": 7,
        "8": 8, "EIGHT": 8,
        "9": 9, "NINE": 9,
        "10": 10, "TEN": 10,
        "11": 11, "J": 11, "JACK": 11,
        "12": 12, "Q": 12, "QUEEN": 12,
        "13": 13, "K": 13, "KING": 13,
        "14": 14, "A": 14, "ACE": 14, "1": 14
    }

    if raw in robust_map:
        return robust_map[raw]

    print(f"[警告] 识别器输出了无法解析的 Rank: '{raw}', ID: {card.card_id}")
    return 8


ICON_TEMPLATES = {
    "START_BET": [
        resource_path("templates", "icons", "en", "start_en.png"),
        resource_path("templates", "icons", "ja", "start_ja.png"),
        resource_path("templates", "icons", "zh", "start_zh.png"),
        resource_path("templates", "icons", "tw", "start_tw.png"),
    ],
    "HOLD_CARDS": [resource_path("templates", "icons", "tpl_replace.png")],
    "TAP_TO_PROCEED": [
        resource_path("templates", "icons", "en", "proceed_en.png"),
        resource_path("templates", "icons", "ja", "proceed_ja.png"),
        resource_path("templates", "icons", "zh", "proceed_zh.png"),
        resource_path("templates", "icons", "tw", "proceed_tw.png"),
    ],
    "HIGH_LOW": [resource_path("templates", "icons", "tpl_high.png")],
    "RESULT": [
        resource_path("templates", "icons", "en", "result_en.png"),
        resource_path("templates", "icons", "ja", "result_ja.png"),
        resource_path("templates", "icons", "zh", "result_zh.png"),
        resource_path("templates", "icons", "tw", "result_tw.png"),
    ],
    "FAIL": [
        resource_path("templates", "icons", "en", "fail_en.png"),
        resource_path("templates", "icons", "en", "toobad_en.png"),
        resource_path("templates", "icons", "ja", "fail_ja.png"),
        resource_path("templates", "icons", "ja", "toobad_ja.png"),
        resource_path("templates", "icons", "zh", "fail_zh.png"),
        resource_path("templates", "icons", "zh", "toobad_zh.png"),
        resource_path("templates", "icons", "tw", "fail_tw.png"),
        resource_path("templates", "icons", "tw", "toobad_tw.png"),
    ],
    "ASK_CHALLENGE": [
        resource_path("templates", "icons", "en", "chance_en.png"),
        resource_path("templates", "icons", "en", "success_en.png"),
        resource_path("templates", "icons", "ja", "chance_ja.png"),
        resource_path("templates", "icons", "ja", "success_ja.png"),
        resource_path("templates", "icons", "zh", "chance_zh.png"),
        resource_path("templates", "icons", "zh", "success_zh.png"),
        resource_path("templates", "icons", "tw", "chance_tw.png"),
        resource_path("templates", "icons", "tw", "success_tw.png"),
    ],
    "FULL": [
        resource_path("templates", "icons", "en", "full_en.png"),
        resource_path("templates", "icons", "ja", "full_ja.png"),
        resource_path("templates", "icons", "zh", "full_zh.png"),
        resource_path("templates", "icons", "tw", "full_tw.png"),
    ],
}

TPL_REPLACE = resource_path("templates", "icons", "tpl_replace.png")
TPL_HIGH = resource_path("templates", "icons", "tpl_high.png")
TPL_LOW = resource_path("templates", "icons", "tpl_low.png")
TPL_CHECK = resource_path("templates", "icons", "tpl_check.png")
TPL_CROSS = resource_path("templates", "icons", "tpl_cross.png")


# ================= 1. 核心算法：高低记牌器 =================
class HighLowCounter:
    def __init__(self):
        self.deck = {i: 4 for i in range(2, 15)}

    def reset(self):
        self.deck = {i: 4 for i in range(2, 15)}

    def remove_cards(self, cards_list):
        for card_val in cards_list:
            if self.deck.get(card_val, 0) > 0:
                self.deck[card_val] -= 1

    def get_best_choice_and_rate(self, current_card):
        high_count = sum(count for val, count in self.deck.items() if val > current_card)
        low_count = sum(count for val, count in self.deck.items() if val < current_card)

        total_valid_cards = high_count + low_count
        if total_valid_cards == 0:
            return "high", 0.5

        high_rate = high_count / total_valid_cards
        low_rate = low_count / total_valid_cards

        if high_rate >= low_rate:
            return "high", high_rate
        else:
            return "low", low_rate


# ================= 2. 视觉识别与控制 =================
def find_game_window():
    """Return the real game window using an exact title match.

    ``getWindowsWithTitle`` performs a substring search.  A browser tab or
    Explorer window containing the repository name therefore used to win the
    race and get captured instead of the game.  Compare every returned window
    title exactly and prefer the largest exact match.
    """
    expected = GAME_TITLE.casefold().strip()
    matches = [
        win for win in gw.getAllWindows()
        if win.title.casefold().strip() == expected and getattr(win, "_hWnd", None)
    ]
    if not matches:
        return None
    return max(matches, key=lambda win: max(0, win.width) * max(0, win.height))


def _get_client_geometry(hwnd):
    rect = wintypes.RECT()
    origin = wintypes.POINT(0, 0)
    if not _user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError()
    if not _user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise ctypes.WinError()
    return origin.x, origin.y, rect.right - rect.left, rect.bottom - rect.top


def _capture_client_with_printwindow(hwnd, width, height):
    """Capture a client area even when another window covers the game."""
    window_dc = _user32.GetDC(hwnd)
    memory_dc = bitmap = old_bitmap = None
    try:
        if not window_dc:
            raise ctypes.WinError()
        memory_dc = _gdi32.CreateCompatibleDC(window_dc)
        bitmap = _gdi32.CreateCompatibleBitmap(window_dc, width, height)
        if not memory_dc or not bitmap:
            raise ctypes.WinError()
        old_bitmap = _gdi32.SelectObject(memory_dc, bitmap)

        # PW_CLIENTONLY | PW_RENDERFULLCONTENT. This works for the game's
        # Chromium/DirectX-backed window and avoids desktop occlusion.
        if not _user32.PrintWindow(hwnd, memory_dc, 0x00000001 | 0x00000002):
            raise RuntimeError("PrintWindow failed")

        byte_count = width * height * 4
        buffer = ctypes.create_string_buffer(byte_count)
        if _gdi32.GetBitmapBits(bitmap, byte_count, buffer) != byte_count:
            raise RuntimeError("GetBitmapBits returned an incomplete frame")
        frame = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
        frame = frame[:, :, :3].copy()  # BGRA -> BGR by dropping alpha.
        if frame.size == 0 or float(frame.mean()) < 1.0:
            raise RuntimeError("PrintWindow returned a blank frame")
        return frame
    finally:
        if old_bitmap and memory_dc:
            _gdi32.SelectObject(memory_dc, old_bitmap)
        if bitmap:
            _gdi32.DeleteObject(bitmap)
        if memory_dc:
            _gdi32.DeleteDC(memory_dc)
        if window_dc:
            _user32.ReleaseDC(hwnd, window_dc)


def capture_game_window():
    global _capture_context
    win = find_game_window()
    if win is None:
        _capture_context = None
        return None, 0, 0

    if win.isMinimized:
        win.restore()
        time.sleep(0.5)

    hwnd = win._hWnd
    try:
        left, top, width, height = _get_client_geometry(hwnd)
        if width < 640 or height < 360:
            raise RuntimeError(f"游戏客户区尺寸异常: {width}x{height}")
        img = _capture_client_with_printwindow(hwnd, width, height)
    except Exception as exc:
        # Fallback for Windows versions/drivers where PrintWindow is disabled.
        # Bring the exact game window forward before using a desktop capture.
        print(f"[警告] 后台窗口截图失败，切换到前台截图: {exc}")
        _bring_game_to_front(hwnd)
        time.sleep(0.2)
        left, top, width, height = _get_client_geometry(hwnd)
        monitor = {"top": top, "left": left, "width": width, "height": height}
        with mss.MSS() as sct:
            img = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)

    _capture_context = {
        "hwnd": hwnd,
        "width": width,
        "height": height,
    }
    normalized = cv2.resize(img, (REFERENCE_WIDTH, REFERENCE_HEIGHT), interpolation=cv2.INTER_CUBIC)
    return normalized, left, top


def _bring_game_to_front(hwnd):
    if not hwnd or not _user32.IsWindow(hwnd):
        return False
    _user32.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
    _user32.BringWindowToTop(hwnd)
    _user32.SetForegroundWindow(hwnd)
    # A short topmost -> non-topmost transition also handles windows that were
    # visually above the foreground window on multi-monitor setups.
    flags = 0x0001 | 0x0002 | 0x0040  # NOSIZE | NOMOVE | SHOWWINDOW
    _user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, flags)
    _user32.SetWindowPos(hwnd, wintypes.HWND(-2), 0, 0, 0, 0, flags)
    return True


def safe_click(rel_x, rel_y, win_left, win_top):
    if not _capture_context:
        print("[警告] 尚未取得有效游戏窗口，取消点击。")
        return False

    hwnd = _capture_context["hwnd"]
    if not _bring_game_to_front(hwnd):
        print("[警告] 游戏窗口已失效，取消点击。")
        return False

    # Match coordinates are in the normalized 1920x1080 frame. Transform them
    # back to the current client size, then query the current screen origin in
    # case the user moved the game window since the frame was captured.
    try:
        client_left, client_top, client_width, client_height = _get_client_geometry(hwnd)
    except Exception as exc:
        print(f"[警告] 无法读取游戏窗口坐标，取消点击: {exc}")
        return False

    offset_x = random.randint(-4, 4)
    offset_y = random.randint(-4, 4)

    target_x = client_left + round(rel_x * client_width / REFERENCE_WIDTH) + offset_x
    target_y = client_top + round(rel_y * client_height / REFERENCE_HEIGHT) + offset_y

    pydirectinput.moveTo(target_x, target_y)
    time.sleep(random.uniform(0.02, 0.05))

    pydirectinput.mouseDown()
    time.sleep(random.uniform(0.05, 0.08))
    pydirectinput.mouseUp()

    time.sleep(random.uniform(0.05, 0.1))
    return True


def find_and_click_icon(screen_bgr, tpl_path, win_left, win_top, threshold=0.80):
    tpl_path = os.fspath(tpl_path)
    if not os.path.exists(tpl_path):
        print(f"❌ 找不到图标文件: {tpl_path}")
        return False

    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    tpl_img = cv2.imread(tpl_path, cv2.IMREAD_GRAYSCALE)
    res = cv2.matchTemplate(screen_gray, tpl_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = tpl_img.shape
        print(f"👉 成功触发点击: {os.path.basename(tpl_path)} (匹配度: {max_val:.2f} >= {threshold})")
        safe_click(max_loc[0] + w // 2, max_loc[1] + h // 2, win_left, win_top)
        return True
    else:
        return False


def is_success_prompt(screen_bgr):
    gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    for path in ICON_TEMPLATES['ASK_CHALLENGE']:
        if 'success_' not in os.path.basename(path):
            continue
        template = cv2.imdecode(np.frombuffer(Path(path).read_bytes(), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if template is not None and template.shape[0] <= gray.shape[0] and template.shape[1] <= gray.shape[1]:
            score = cv2.minMaxLoc(cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED))[1]
            if score >= .85:
                return True
    return False


def detect_game_state(screen_bgr):
    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    THRESHOLD = 0.85

    for state, tpl_paths in ICON_TEMPLATES.items():
        for tpl_path in tpl_paths:
            if not os.path.exists(tpl_path):
                continue
            tpl_img = cv2.imread(tpl_path, cv2.IMREAD_GRAYSCALE)
            res = cv2.matchTemplate(screen_gray, tpl_img, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val >= THRESHOLD:
                return state
    return "UNKNOWN"


def find_all_card_rects(img, search_zone):
    sx, sy, sw, sh = search_zone
    roi = img[sy:sy + sh, sx:sx + sw]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 提取所有纯白色区域（利用暗牌是紫黑色的特点主动忽略暗牌）
    white_mask = cv2.inRange(hsv, (0, 0, 180), (180, 60, 255))

    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # 尺寸过滤：只保留像卡牌那么大的白块
        if w > 100 and h > 150:
            rects.append((sx + x, sy + y, w, h))
    return rects


# ---------------------------------------------------------
# OCR 引擎 1：用于提取浅紫底色上的黄色数字 (加入强制纠偏机制)
# ---------------------------------------------------------
def read_screen_number(img, search_zone):
    return read_challenge_number(img, search_zone, ocr)

# ---------------------------------------------------------
# OCR 引擎 2：用于纯白底浅蓝字 (最终 RESULT 结算界面的 Coins)
# ---------------------------------------------------------
def read_result_number(img, search_zone):
    return read_result_digits(img, search_zone, ocr)


# ================= 3. 数据与主循环 =================
def load_daily_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("date") == time.strftime("%Y-%m-%d"):
                    return data.get("coins", 0), data.get("fails", 0)
        except Exception:
            pass
    return 0, 0


def load_daily_stage():
    if not Path(DATA_FILE).exists():
        return 0
    with open(DATA_FILE, encoding='utf-8') as f:
        data = json.load(f)
    stage = data.get('phased_stage', 0) if data.get('date') == time.strftime('%Y-%m-%d') else 0
    if type(stage) is not int or not 0 <= stage <= 3:
        raise ValueError('保存的策略阶段无效，请检查 daily_coins.json')
    return stage


def save_daily_data(coins, fails, stage=None):
    # Save coins and stage together; legacy mode preserves the saved stage.
    if stage is None:
        stage = load_daily_stage()
    temporary = Path(DATA_FILE).with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as f:
        json.dump({"coins": coins, "fails": fails, "date": time.strftime("%Y-%m-%d"),
                   "phased_stage": stage}, f)
    os.replace(temporary, DATA_FILE)


def auto_play_loop(mode='legacy'):
    global upcoming_card_val
    if mode not in ('legacy', 'phased'):
        raise ValueError('Unknown strategy mode')
    phased = PhasedStrategy(load_daily_stage()) if mode == 'phased' else None
    if phased is not None and phased.complete:
        print('[三阶段] 今日三个目标均已完成，停止挂机。')
        return
    counter = HighLowCounter()
    card_rec = CardRecognizer(TEMPLATE_DIR)
    daily_coins, daily_fails = load_daily_data()
    net_profit = daily_coins - (daily_fails * 50)
    print(f"开始自动挂机... 当日累计代币: {daily_coins} | 累计失败: {daily_fails} 次 | 今日净利润: {net_profit}")

    has_tallied = False
    settlement_reader = SettlementReader()
    reward_reader = ChallengeRewardReader()
    expected_cashout = None
    has_recorded_fail = False  # 防止在 FAIL 动画期间重复扣除门票

    def request_cashout(frame, left, top, cash):
        nonlocal expected_cashout
        if find_and_click_icon(frame, TPL_CROSS, left, top):
            expected_cashout = cash
            return True
        return False

    while daily_coins < 20000 and bot_running :
        img, win_left, win_top = capture_game_window()
        if img is None:
            print("未找到游戏窗口，请确保游戏没有被完全最小化...")
            time.sleep(1)
            continue

        current_state = detect_game_state(img)

        # Only a new round resets accounting; UNKNOWN may be a result flicker.
        if current_state in ("START_BET", "HOLD_CARDS"):
            has_tallied = False
            settlement_reader.reset()
            reward_reader.reset_round()
            expected_cashout = None
            if phased is not None:
                phased.reset_round()
        elif current_state in ('HIGH_LOW', 'FAIL', 'RESULT'):
            reward_reader.reset_prompt()
        if current_state != "FAIL":
            has_recorded_fail = False

        # === 实时渲染 GUI 画面 ===
        display_img = img.copy()
        cv2.putText(display_img, f"State: {current_state}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.putText(display_img, f"Coins: {daily_coins} / {TARGET_LIMIT}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (0, 255, 255), 3)
        if current_state == "UNKNOWN":
            cv2.putText(display_img, "Waiting for match...", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        #cv2.imshow("Auto Bot GUI", display_img)

        #if cv2.waitKey(1) & 0xFF == ord('q'):
            #print("收到退出指令，结束挂机。")
            #break
        # =========================

        if current_state == "UNKNOWN":
            time.sleep(0.5)
            continue

        if current_state == "START_BET":
            print("\n[状态] 初始下注")
            counter.reset()
            upcoming_card_val = None

            # 遍历尝试点击当前语言的 Start 图标
            for tpl in ICON_TEMPLATES["START_BET"]:
                if find_and_click_icon(img, tpl, win_left, win_top):
                    break
            time.sleep(1)

        elif current_state == "HOLD_CARDS":
            print("\n[状态] 留牌阶段")
            recognized_cards, rects = card_rec.recognize(img)
            if len(recognized_cards) == 5:
                hand_ids = [c.card_id for c in recognized_cards]
                card_values = [get_real_card_value(c) for c in recognized_cards if c.card_id != JOKER_ID]
                counter.remove_cards(card_values)

                best, _ = calculate_best(hand_ids, "standard")

                for idx in best.held_indices:
                    x, y, w_box, h_box = rects[idx]
                    safe_click(x + w_box // 2, y + h_box // 2, win_left, win_top)
                    time.sleep(0.15)

                time.sleep(0.3)
                find_and_click_icon(img, TPL_REPLACE, win_left, win_top)
                time.sleep(1)

        elif current_state == "TAP_TO_PROCEED":
            h, w = img.shape[:2]
            safe_click(w // 2, h // 2, win_left, win_top)
            time.sleep(0.6)








        elif current_state == "ASK_CHALLENGE":

            if phased is not None:
                if phased.base_cash is None:
                    if is_success_prompt(img):
                        raise RuntimeError('当前已在翻倍途中，无法恢复本局成功次数。请从新一局开始。')
                    real_reward = read_screen_number(img, REWARD_ZONE)
                    next_reward = reward_reader.observe(real_reward, time.monotonic())
                    if next_reward is None:
                        time.sleep(.25)
                        continue
                    phased.start_round(next_reward // 2, daily_coins)
                elif is_success_prompt(img):
                    phased.confirm_success()
                action = phased.decide()
                goal = ('游戏自动结算' if phased.target_wins is None
                        else f'{phased.target_wins} 次成功')
                print(f'[三阶段] 第 {phased.stage + 1}/3 阶段 | '
                      f'已成功 {phased.successes} 次 | 目标: {goal} | '
                      + ('收手入账' if action == 'cashout' else '继续翻倍'))
                if action == 'cashout':
                    request_cashout(img, win_left, win_top, phased.expected_cash)
                else:
                    find_and_click_icon(img, TPL_CHECK, win_left, win_top, threshold=.55)
                time.sleep(.6)
                continue

            real_reward = read_screen_number(img, REWARD_ZONE)
            next_reward = reward_reader.observe(real_reward, time.monotonic())
            if next_reward is None:
                time.sleep(.25)
                continue
            current_cashout = next_reward // 2
            print(f"\n[账房] 当前在手现金: {current_cashout} | 挑战成功后将变为: {next_reward}")

            if upcoming_card_val is not None:

                _, win_rate = counter.get_best_choice_and_rate(upcoming_card_val)

                print(f"[风控] 基于预判，下一轮真实胜率为: {win_rate:.2%}")

            else:

                win_rate = 1.0

                print("[风控] 第一轮或盲盒状态，默认直接挑战！")

            # === 终极风控：智能垫刀 / 极限冲刺 ===

            # 【规则 1：冲刺期】账户金币已达 19800，目标是实际到手现金 >= 10000

            if daily_coins >= 19800:

                if current_cashout >= 10000:

                    print(f"🎉 终极目标达成！在手奖金已达 {current_cashout} (超1w)，安全提现大丰收！")

                    request_cashout(img, win_left, win_top, current_cashout)

                else:

                    print(f"🚀 冲刺期继续追击（无视胜率，目标在手1w）！当前在手仅 {current_cashout}，冲刺 {next_reward}！")

                    find_and_click_icon(img, TPL_CHECK, win_left, win_top, threshold=0.55)


            # 【规则 2：平稳垫刀期】总金币未达到 19800，严格控分慢慢垫

            else:

                # 1. 核心修复：当前这笔在安全线内，但再翻倍就会爆破 19800 -> 立即刹车提现垫刀！

                if daily_coins + current_cashout <= 19800 and daily_coins + next_reward > 19800:

                    print(
                        f"🛑 警报：提现(+{current_cashout})在安全线内，但再翻倍(+{next_reward})总额将达 {daily_coins + next_reward} 提前破限！果断收手垫刀！")

                    request_cashout(img, win_left, win_top, current_cashout)


                # 2. 如果当前现金已经不慎超过了 19800（极端天胡开局）

                elif daily_coins + current_cashout > 19800:

                    if current_cashout >= 10000:

                        print(f"🎉 意外天胡！垫刀途中在手直接达 {current_cashout} (超1w)，直接收手大丰收！")

                        request_cashout(img, win_left, win_top, current_cashout)

                    else:

                        print(
                            f"⚠️ 提现此笔(+{current_cashout})总额将达 {daily_coins + current_cashout} 破限且未破万！拒绝提现，强行搏翻倍！")

                        find_and_click_icon(img, TPL_CHECK, win_left, win_top, threshold=0.55)


                # 3. 正常发育，胜率低见好就收

                elif win_rate < 0.60:

                    print(f"🛑 发育局胜率太低 ({win_rate:.2%})，提现 {current_cashout} 垫刀！")

                    request_cashout(img, win_left, win_top, current_cashout)


                # 4. 利润安全且下一把翻倍仍在安全线内，继续追击

                else:

                    print(f"🔥 利润安全且再翻倍不会超限，普通局继续追击翻倍！")

                    find_and_click_icon(img, TPL_CHECK, win_left, win_top, threshold=0.55)

            time.sleep(0.6)
        elif current_state == "HIGH_LOW":
            if phased is not None and phased.base_cash is None:
                raise RuntimeError('当前已在翻倍途中，无法恢复本局成功次数。请从新一局开始。')
            try:
                # 1. 用新引擎搜出所有白色卡牌
                rects = find_all_card_rects(img, HIGH_LOW_SEARCH_ZONE)

                if rects:
                    # 按 X 坐标排序，拿到最右侧的一张明牌
                    rects.sort(key=lambda r: r[0])
                    current_rect = rects[-1]

                    old_right_x = current_rect[0]

                    single_card = card_rec.recognize_card(img, current_rect)
                    if single_card.card_id != JOKER_ID:
                        current_card_val = get_real_card_value(single_card)
                        counter.remove_cards([current_card_val])
                        best_choice, rate = counter.get_best_choice_and_rate(current_card_val)

                        print(f"\n明牌: {single_card.rank}, 选: {best_choice.upper()} (胜率: {rate:.2%})")

                        if best_choice == "high":
                            guessed = find_and_click_icon(img, TPL_HIGH, win_left, win_top)
                        else:
                            guessed = find_and_click_icon(img, TPL_LOW, win_left, win_top)
                        if phased is not None and guessed:
                            phased.guess_clicked()

                        # === 2. 状态对比追踪连拍 ===
                        print("[预判] 启动多帧对比追踪...")
                        upcoming_card_val = None

                        for i in range(25):
                            time.sleep(0.04)
                            flip_img, _, _ = capture_game_window()

                            if flip_img is not None:
                                try:
                                    new_rects = find_all_card_rects(flip_img, HIGH_LOW_SEARCH_ZONE)
                                    if new_rects:
                                        # 拿到连拍画面中最右侧的白牌
                                        new_rects.sort(key=lambda r: r[0])
                                        newest_rect = new_rects[-1]

                                        # 核心判定：如果新画面最右边白牌的 X 坐标，比明牌突增了 50 个像素以上
                                        # 证明有新卡翻过来变白了
                                        if newest_rect[0] > old_right_x + 50:
                                            newest_card = card_rec.recognize_card(flip_img, newest_rect)
                                            if newest_card.card_id != JOKER_ID:
                                                upcoming_card_val = get_real_card_value(newest_card)
                                                print(
                                                    f"[预判] 第 {i + 1} 帧追踪到新卡牌！下一张将是: {newest_card.rank}")

                                                break
                                except Exception:
                                    continue

                        if upcoming_card_val is None:
                            print("[预判] 连拍追踪超时，未能看清下一张牌。")

                        time.sleep(0.6)
                else:
                    print("\n[警告] 画面中未识别到任何白色卡牌，请确认画面处于 HIGH_LOW 状态且搜索区正常。")
            except Exception as e:
                print(f"\n[异常] 猜高低逻辑崩溃: {e}")

        elif current_state == "FAIL":
            if not has_recorded_fail:
                daily_fails += 1
                net_profit = daily_coins - (daily_fails * 50)
                save_daily_data(daily_coins, daily_fails)
                print(
                    f"\n💔 对局失败！累计失败: {daily_fails} 次 (门票损失: {daily_fails * 50}) | 今日净利润: {net_profit}")
                has_recorded_fail = True

            time.sleep(0.8)
            find_and_click_icon(img, TPL_CHECK, win_left, win_top, threshold=0.55)
            time.sleep(1)

        elif current_state == "RESULT":
            if not has_tallied:
                if settlement_reader.started is None:
                    print("\n[状态] 结算界面，等待金额稳定后核对账目...")
                if phased is not None:
                    phased.begin_settlement(expected_cashout is not None)
                    if phased.expected_cash is None:
                        raise RuntimeError('缺少本局翻倍记录，无法核对入账。请手动核对后开始新一局。')
                    expected_cashout = phased.expected_cash
                amount = read_result_number(img, RESULT_REWARD_ZONE)
                earned = settlement_reader.observe(amount, time.monotonic(), expected_cashout)
                if earned is None:
                    time.sleep(.2)
                    continue
                daily_coins += earned
                net_profit = daily_coins - (daily_fails * 50)
                print(
                    f"💰 成功入账: {earned} ! 当前总金币: {daily_coins} | 累计失败: {daily_fails} 次 | 今日净利润: {net_profit}")

                if phased is not None:
                    next_stage = phased.stage_after_credit(earned)
                    save_daily_data(daily_coins, daily_fails, next_stage)
                    phased.stage = next_stage
                else:
                    save_daily_data(daily_coins, daily_fails)
                has_tallied = True

            time.sleep(0.8)
            find_and_click_icon(img, TPL_CHECK, win_left, win_top, threshold=0.55)
            time.sleep(1)
            if phased is not None and phased.complete:
                print('[三阶段] 三个目标均已成功入账，停止挂机。')
                break


if __name__ == "__main__":
    auto_play_loop()
