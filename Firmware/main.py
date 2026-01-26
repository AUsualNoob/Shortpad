#// libraries and stuff (for circuitpython in general)
import board
import digitalio
import busio
import time

#// libraries and stuff (for keyboard)
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.macros import Macros, MacroBase, Press, Tap, Release

#// libraries and stuff (for oled)
from adafruit_ssd1306 import SSD1306_I2C       
from adafruit_bus_device import i2c_device
from kmk.modules.oled import OLED

#// the thingies that i gotta put for stuff to work (for the oled)
i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
oled = SSD1306_I2C(width=128, height=32, i2c=i2c)
oled_module = OLED(oled)
keyboard.modules.append(oled_module)

#// the thingies that i gotta put here so stuff works properly (for the keyboard)
keyboard = KMKKeyboard()
macros = Macros()
keyboard.modules.append(macros)

PINS = [ board.D8, #button that checks what buttons do (OLED) its off to the side
         board.D9, #button bottom right
         board.D10, #button bottom left
         board.D11, #button top right
         board.D1  #button top left
        ]

keyboard.matrix = KeysScanner(pins=PINS, value_when_pressed=False)
timepassed = 0


#// centering function
def center(line):
    x = (128 - len(line) * 6) // 2
    y = 12    
    oled_module.oled.fill(0)
    oled_module.oled.text(line, x, y)
    oled_module.oled.show()

def center2line(line1, line2):
    x1 = (128 - len(line1) * 6) // 2
    y1 = 8
    x2 = (128 - len(line2) * 6) // 2
    y2 = 20
    oled_module.oled.fill(0)
    oled_module.oled.text(line1, x1, y1)
    oled_module.oled.text(line2, x2, y2)
    oled_module.oled.show()

#// random function so the thing can.. function
def scmacro():
    btpressed = keyboard.matrix.get_pressed_keys()
    timepassed = time.time()
    oled_module.oled.fill(0)
    center("Press any button to show what it does")
    oled_module.oled.show()
    if time.time() - timepassed > 10:
        oled_module.oled.fill(0)
        oled_module.oled.show()
    elif 0 in btpressed:
        oled_module.oled.fill(0)
        oled_module.oled.show()
    elif 1 in btpressed:
        center2line("Paste", "CTRL + V")
    elif 2 in btpressed:
        center2line("Copy", "CTRL + C")
    elif 3 in btpressed:
        center2line("Show copy history", "WIN + V")
    elif 4 in btpressed:
        center2line("Undo", "CTRL+Z")
    


#// wohoooo going onto the keymap yip yip horray
keyboard.keymap = [
    [KC.Macro(scmacro), KC.Macro(
        Press(KC.LCTRL),
        Tap(KC.V),
        Release(KC.LCTRL)
    ), KC.Macro(
        Press(KC.LCTRL),
        Tap(KC.C),
        Release(KC.LCTRL)
    ), KC.Macro(
        Tap(KC.RGUI),
        Tap(KC.V),
    ), KC.Macro(
        Press(KC.CTRL),
        Tap(KC.Z),
        Release(KC.CTRL)
    )]
]





