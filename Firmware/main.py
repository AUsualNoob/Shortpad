#// libraries and stuff (for circuitpython in general)
import board
import busio
import time
import sys
import gc
import microcontroller

#// libraries and stuff (for keyboard)
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC, make_key
from kmk.modules.macros import Macros
#// libraries and stuff (for oled)
from adafruit_ssd1306 import SSD1306_I2C

#// the thingies that i gotta put here so stuff works properly (for the keyboard)
keyboard = KMKKeyboard()
macros   = Macros()
keyboard.modules.append(macros)
keyboard.matrix = KeysScanner(
    pins=[
        board.D7,
        board.D8,
        board.D9,
        board.D10,
        board.A0,
    ],
    value_when_pressed=False,
)

#// the thingies that i gotta put for stuff to work (for the oled)
oled = None
try:
    i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
    timeout = time.monotonic() + 2
    while not i2c.try_lock():
        if time.monotonic() > timeout:
            break
    i2c.unlock()
    oled = SSD1306_I2C(width=128, height=32, i2c=i2c)
except Exception:
    oled = None

#// ---- drawing helpers ----
def draw_rect(x, y, w, h, col=1):
    for i in range(w):
        oled.pixel(x + i, y, col)
        oled.pixel(x + i, y + h - 1, col)
    for i in range(h):
        oled.pixel(x, y + i, col)
        oled.pixel(x + w - 1, y + i, col)

def fill_rect(x, y, w, h, col=1):
    for fx in range(x, x + w):
        for fy in range(y, y + h):
            oled.pixel(fx, fy, col)

def hline(x, y, w, col=1):
    for i in range(w):
        oled.pixel(x + i, y, col)

_LABELS = {
    1: ("Paste",      "CTRL+V"),
    2: ("Copy",       "CTRL+C"),
    3: ("Select all", "CTRL+A"),
    4: ("Undo",       "CTRL+Z"),
}

_SHORTCUTS = {
    1: KC.LCTRL(KC.V),
    2: KC.LCTRL(KC.C),
    3: KC.LCTRL(KC.A),
    4: KC.LCTRL(KC.Z),
}

#// ---- dvd bounce idle screen ----
_DVD_W = 28
_DVD_H = 12
_dvd_x  = 10.0
_dvd_y  = 2.0
_dvd_dx = 1.5
_dvd_dy = 1.0
_last_anim_time = 0
_ANIM_INTERVAL  = 0.04

def draw_idle():
    global _dvd_x, _dvd_y, _dvd_dx, _dvd_dy
    if not oled:
        return

    _dvd_x += _dvd_dx
    _dvd_y += _dvd_dy

    if _dvd_x <= 1:
        _dvd_dx = abs(_dvd_dx)
        _dvd_x  = 1
    if _dvd_x + _DVD_W >= 127:
        _dvd_dx = -abs(_dvd_dx)
        _dvd_x  = 127 - _DVD_W
    if _dvd_y <= 1:
        _dvd_dy = abs(_dvd_dy)
        _dvd_y  = 1
    if _dvd_y + _DVD_H >= 31:
        _dvd_dy = -abs(_dvd_dy)
        _dvd_y  = 31 - _DVD_H

    bx = int(_dvd_x)
    by = int(_dvd_y)

    oled.fill(0)
    draw_rect(bx, by, _DVD_W, _DVD_H)
    oled.text("MACRO", bx + 3, by + 2, 1)
    oled.show()

#// ---- info mode: 2x2 box grid ----
def draw_info_mode(highlighted=None):
    if not oled:
        return
    oled.fill(0)

    boxes = [
        (  0,  0, 63, 15, "Paste",  "C+V", 1),
        ( 65,  0, 63, 15, "Copy",   "C+C", 2),
        (  0, 17, 63, 15, "SelAll", "C+A", 3),
        ( 65, 17, 63, 15, "Undo",   "C+Z", 4),
    ]

    for (x, y, w, h, label, shortcut, btn_num) in boxes:
        filled = (highlighted == btn_num)
        draw_rect(x, y, w, h)

        if filled:
            fill_rect(x + 1, y + 1, w - 2, h - 2)
            oled.text(label,    x + 3, y + 2, 0)
            oled.text(shortcut, x + 3, y + 8, 0)
        else:
            oled.text(label,    x + 3, y + 2, 1)
            oled.text(shortcut, x + 3, y + 8, 1)

    oled.show()

#// ---- device info: paged, one stat per screen ----
_DEV_PAGE       = 0
_DEV_PAGE_COUNT = 4
_last_page_time = 0
_PAGE_INTERVAL  = 2.0

def _get_device_stats():
    try:
        freq  = int(microcontroller.cpu.frequency / 1_000_000)
        temp  = microcontroller.cpu.temperature
        ram   = int(gc.mem_free() / 1024)
        name  = getattr(board, "board_id", "unknown").replace("_", " ")
    except Exception:
        freq  = 0
        temp  = 0.0
        ram   = 0
        name  = "unknown"
    return freq, temp, ram, name

def draw_device_page(page):
    if not oled:
        return
    freq, temp, ram, name = _get_device_stats()

    oled.fill(0)

    if page == 0:
        oled.text("BOARD", 0, 0, 1)
        hline(0, 9, 128)
        oled.text(name[:10],  0, 13, 1)
        if len(name) > 10:
            oled.text(name[10:21], 0, 23, 1)

    elif page == 1:
        oled.text("CPU FREQ", 0, 0, 1)
        hline(0, 9, 128)
        val = "{}  MHz".format(freq)
        x = max(0, (128 - len(val) * 6) // 2)
        oled.text(val, x, 18, 1)

    elif page == 2:
        oled.text("CPU TEMP", 0, 0, 1)
        hline(0, 9, 128)
        val = "{:.1f} C".format(temp)
        x = max(0, (128 - len(val) * 6) // 2)
        oled.text(val, x, 18, 1)

    elif page == 3:
        oled.text("FREE RAM", 0, 0, 1)
        hline(0, 9, 128)
        val = "{}  KB".format(ram)
        x = max(0, (128 - len(val) * 6) // 2)
        oled.text(val, x, 18, 1)

    for d in range(_DEV_PAGE_COUNT):
        dx = 128 - (_DEV_PAGE_COUNT - d) * 6
        oled.pixel(dx, 31, 1)
        oled.pixel(dx + 1, 31, 1)
        if d == page:
            oled.pixel(dx, 30, 1)
            oled.pixel(dx + 1, 30, 1)

    oled.show()

def show_device_info():
    global _DEV_PAGE, _last_page_time
    _DEV_PAGE       = 0
    _last_page_time = time.monotonic()
    draw_device_page(0)

#// random function so the thing can.. function
_info_mode      = False
_IDLE_TIMEOUT   = 6
_display_until  = 0
_last_shown_btn = -1
_showing_device = False

_side_last_press  = 0
_DOUBLE_CLICK_GAP = 0.4

def on_side_press(key, keyboard, *args, **kwargs):
    global _info_mode, _side_last_press, _last_shown_btn
    global _display_until, _showing_device
    now = time.monotonic()
    gap = now - _side_last_press
    _side_last_press = now

    if gap < _DOUBLE_CLICK_GAP:
        _info_mode      = False
        _showing_device = True
        _display_until  = now + (_DEV_PAGE_COUNT * _PAGE_INTERVAL) + 1
        show_device_info()
        _last_shown_btn = -2
    else:
        _showing_device = False
        _info_mode = not _info_mode
        if _info_mode:
            draw_info_mode(None)
            _last_shown_btn = -2
        else:
            _last_shown_btn = 99
    return True

def make_action_handler(btn_index):
    def on_press(key, keyboard, *args, **kwargs):
        global _display_until, _last_shown_btn
        if _info_mode:
            draw_info_mode(highlighted=btn_index)
            _display_until  = time.monotonic() + _IDLE_TIMEOUT
            _last_shown_btn = btn_index
            return True
        else:
            keyboard.tap_key(_SHORTCUTS[btn_index])
            return True
    return on_press

def scmacro():
    global _last_shown_btn, _display_until, _last_anim_time
    global _DEV_PAGE, _last_page_time, _showing_device
    now = time.monotonic()

    if _showing_device:
        if now - _last_page_time >= _PAGE_INTERVAL:
            _last_page_time = now
            _DEV_PAGE += 1
            if _DEV_PAGE >= _DEV_PAGE_COUNT:
                _showing_device = False
                _last_shown_btn = 99
            else:
                draw_device_page(_DEV_PAGE)
        return

    if _info_mode:
        if now > _display_until and _last_shown_btn != -2:
            draw_info_mode(None)
            _last_shown_btn = -2
    else:
        if now - _last_anim_time >= _ANIM_INTERVAL:
            _last_anim_time = now
            draw_idle()

SIDE_KEY = make_key(names=("SIDE",), on_press=on_side_press)
BTN1 = make_key(names=("BTN1",), on_press=make_action_handler(1))
BTN2 = make_key(names=("BTN2",), on_press=make_action_handler(2))
BTN3 = make_key(names=("BTN3",), on_press=make_action_handler(3))
BTN4 = make_key(names=("BTN4",), on_press=make_action_handler(4))

#// wohoooo going onto the keymap yip yip horray
keyboard.keymap = [
    [
        SIDE_KEY,
        BTN1,
        BTN2,
        BTN3,
        BTN4,
    ]
]

if oled:
    draw_idle()

keyboard.before_matrix_scan = scmacro

if __name__ == "__main__":
    keyboard.go()
