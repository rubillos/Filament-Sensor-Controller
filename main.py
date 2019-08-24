"""
This test will initialize the display using displayio and draw a solid green
background, a smaller purple rectangle, and some yellow text.
"""
import gc

import board
import displayio
import terminalio
import time

from adafruit_display_text import label
from adafruit_featherwing import minitft_featherwing
from adafruit_bitmap_font import bitmap_font

minitft = minitft_featherwing.MiniTFTFeatherWing()
display = minitft.display

# Make the display context
splash = displayio.Group(max_size=10)
display.show(splash)

color_group = displayio.Group(max_size=1, scale=40, x=0, y=0)
color_bitmap = displayio.Bitmap(4, 2, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFF1F1F

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

color_group.append(bg_sprite)
splash.append(color_group)

# Draw a smaller inner rectangle
inner_group = displayio.Group(max_size=1, scale=30, x=20, y=10)
inner_bitmap = displayio.Bitmap(4, 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0xAA0088 # Purple

inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=0, y=0)

inner_group.append(inner_sprite)
splash.append(inner_group)

# Draw a label
labelX = 10
labelY = 10
xDir = 1
yDir = 1

text_group = displayio.Group(max_size=2, scale=1, x=labelX, y=labelY)
text = "Hello World!"
font = bitmap_font.load_font("/fonts/HelveticaNeue-Bold-24.bdf")
text_area = label.Label(font, text=text, color=0xFFFFFF)
text_group.append(text_area) # Subgroup for text scaling
splash.append(text_group)

while True:
    buttons = minitft.buttons

    if buttons.right:
        print("Button RIGHT!")

    if buttons.down:
        print("Button DOWN!")

    if buttons.left:
        print("Button LEFT!")

    if buttons.up:
        print("Button UP!")

    if buttons.select:
        print("Button SELECT!")

    if buttons.a:
        print("Button A!")

    if buttons.b:
        print("Button B!")

    labelX = labelX + xDir
    labelY = labelY + yDir
    if (labelX > 150 or labelX < 10):
        xDir = -xDir
    if (labelY > 70 or labelY < 10):
        yDir = -yDir

    text_group.x = labelX
    text_group.y = labelY

    time.sleep(0.1)
    pass
