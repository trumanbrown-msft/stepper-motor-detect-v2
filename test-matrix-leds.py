import re
import time

from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT

fonts = {
    "CP437_FONT": proportional(CP437_FONT),
    "TINY_FONT": proportional(TINY_FONT),
    "SINCLAIR_FONT": proportional(SINCLAIR_FONT),
    "LCD_FONT": proportional(LCD_FONT)
}

serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=4, block_orientation=-90, rotate=0, blocks_arranged_in_reverse_order=False)
print("Created device")


def hello_world(msg):
    # create matrix device
    # start demo
    print(msg)
    show_message(device, msg, fill="white", font=proportional(CP437_FONT))
    time.sleep(1)

    msg = "Hello World!"
    print(msg)
    show_message(device, msg, fill="white", font=proportional(LCD_FONT), scroll_delay=0.1)

    time.sleep(5)
    device.cleanup()

def display_fonts(msg):
    # Display each font
    for font_name, font in fonts.items():
        with canvas(device) as draw:
            text(draw, (0, 0), font_name, fill="white")  # Show font name
        time.sleep(2)

        msg = "Hello!"
        for i in range(8):  # Scroll through the font display
            with canvas(device) as draw:
                text(draw, (0 - i * 8, 0), msg, fill="white", font=font)
            time.sleep(0.2)
    time.sleep(2)

def pop_msg(msg):
    for intensity in range(0, 16):  # 16 brightness levels
        device.contrast(intensity * 16)
        with canvas(device) as draw:
            text(draw, (0, 0), msg, fill="white", font=proportional(LCD_FONT))
        time.sleep(0.1)


hello_world("MAX7219 LED Matrix Demo")
# display_fonts("MAX7219 LED Matrix Demo")
# pop_msg("MAX7219 LED Matrix Demo")