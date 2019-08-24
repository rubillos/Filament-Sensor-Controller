# Itsy Bitsy M0 Express IO demo
# Welcome to CircuitPython 2.2 :)

# CircuitPython IO demo #1 - General Purpose I/O
import time
import board
from digitalio import DigitalInOut, Direction, Pull

led = DigitalInOut(board.D13)
led.direction = Direction.OUTPUT

state = True

while True:
    state = not state
    led.value = state

    time.sleep(0.5)
