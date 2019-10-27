# Hypercube Active Filament Sensor

import gc

import board
import displayio
import terminalio
import time

from adafruit_display_text import label
from adafruit_featherwing import minitft_featherwing
from adafruit_bitmap_font import bitmap_font

from digitalio import DigitalInOut, Direction, Pull

minitft = minitft_featherwing.MiniTFTFeatherWing()
display = minitft.display

#---------------------------------------
black_color = 0x000000

machine_name_color = 0xFFFFFF
machine_name_y = 13

error_color = 0xFFFFFF
error_message_y = 67

digit_color_inactive = 0x808080
digit_color_active = 0x00FF00
digit_color_error = error_color
digit_y = 47
digit_offset = -7

label_color = 0xE0E0E0
label_text_y 67

#---------------------------------------
machine_defs = [ \
    [[ 0,  0,  0,  0,  0, -1], "** NO TOOL **"], \
    [[ 0,  0,  1,  0,  0, -1], "V6"], \
    [[ 0,  0,  1,  0,  0, -1], "Volcano"], \
    [[ 0,  0,  0,  0,  0, -1], "Laser"], \
    [[ 1,  1,  1,  1,  0, -1], "Kraken"], \
    [[-1, -1, -1, -1, -1,  1], "Zesty"], \
    [[ 0,  0,  1,  0,  0, -1], "Super Volcano"], \
    [[-1, -1, -1, -1, -1, -1], "invalid"], \
    [[ 1,  1,  1,  1,  1, -1], "Diamond Fullcolor"], \
    [[-1, -1, -1, -1, -1,  1], "Titan Aero"], \
    [[-1, -1, -1, -1, -1,  1], "Dyze Design"], \
    [[-1, -1, -1, -1, -1, -1], "invalid"], \
    [[-1, -1, -1, -1, -1, -1], "invalid"], \
    [[-1, -1, -1, -1, -1, -1], "invalid"], \
    [[-1, -1, -1, -1, -1, -1], "invalid"], \
    [[-1, -1, -1, -1, -1, -1], "Nozzle Setup"]]

sensor_pins = [ \
    [board.A0, "1", -2], \
    [board.A1, "2", -1], \
    [board.A2, "3", 0], \
    [board.A3, "4", 1], \
    [board.A4, "5", 2], \
    [board.A5, "Auxilary", 0]]

id_pins = [board.MI, board.RX, board.TX, board.D4]

output_pin = board.D2

#---------------------------------------
hidden_offset = 1000

class BetterGroup(displayio.Group):
    def __init__(self, hidden=False, **kwargs):
        self.__hidden = False
        super().__init__(**kwargs)
        self.hidden = hidden

    @property
    def hidden(self):
        return self.__hidden

    @hidden.setter
    def hidden(self, value):
        if value != self.__hidden:
            self.__hidden = value
            self.x = self.x

    def _hide_offset(self):
        if self.__hidden:
            return hidden_offset
        else:
            return 0

    @property
    def x(self):
        return super(BetterGroup,self).x % hidden_offset

    @x.setter
    def x(self, value):
        super(BetterGroup, self.__class__).x.fset(self, (value % hidden_offset) + self._hide_offset())

class BetterLabel(label.Label):
    def __init__(self, hidden=False, **kwargs):
        self.__hidden = False
        super().__init__(**kwargs)
        self.hidden = hidden
		self.center_on_x(display.width//2)

	def center_on_x(self, center_x):
		x, y, w, h = self.bounding_box()
		self.x = center_x - w // 2;

    @property
    def hidden(self):
        return self.__hidden

    @hidden.setter
    def hidden(self, value):
        if value != self.__hidden:
            self.__hidden = value
            self.x = self.x

    def _hide_offset(self):
        if self.__hidden:
            return hidden_offset
        else:
            return 0

    @property
    def x(self):
        return super(BetterLabel, self).x % hidden_offset

    @x.setter
    def x(self, value):
        super(BetterLabel, self.__class__).x.fset(self, (value % hidden_offset) + self._hide_offset())

    def bounding_box(self):
        x, y, w, h = super().bounding_box()
        w -= 2 * x
        return x, y, w, h

class Digit(BetterLabel):
    def __init__(self, text="*", active=True, error=False, **kwargs):
        self.__active = active
        self.__error = error
        super().__init__(text, max_glyphs=len(text)+1, color=self._current_color(), **kwargs)

        x, y, w, h = self.bounding_box()

        self.border_palette = displayio.Palette(2)
        self.border_palette[0] = black_color
        self.border_palette[1] = self._border_color()

        border_bitmap = FrameBitmap(w+6, h+6, thickness=2)
        border_sprite = displayio.TileGrid(border_bitmap, pixel_shader=self.border_palette, x=-3, y=-3)
        self.append(border_sprite)

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value):
        self.__active = value
        self._update_color()

    @property
    def error(self):
        return self.__error

    @error.setter
    def error(self, value):
        self.__error = value
        self._update_color()

    def _current_color(self):
        if self.__error:
            return digit_color_error
        elif self.__active:
            return digit_color_active
        else:
            return digit_color_inactive

    def _border_color(self):
        if self.__error:
            return digit_color_error
        else:
            return black_color

    def _update_color(self):
        self.color = self._current_color()
        self.border_palette[1] = self._border_color()

class SolidBitmap(object):
    def __init__(self, width=display.width, height=display.height):
        self.width = width
        self.height = height
        self.value_count = 1

	def __getitem__(self, key):
		return 0

class FrameBitmap(object):
    def __init__(self, width=1, height=1, thickness=2):
        self.width = width
        self.height = height
        self.thickness = thickness
        self.value_count = 2

    def get_value(x, y):
        if x < thickness or x >= width-thickness or y < thickness or y >= height-thickness:
            return 1
        else:
            return 0

	def __getitem__(self, key):
		if isinstance(key, int):
            return self.get_value(key % self.width, key // self.width)
		elif isinstance(key, tuple) and len(key) == 2:
			return self.get_value(key[0], key[1])
		else:
			return 0

#---------------------------------------
if __name__ == '__main__':
    id_inputs = []
    for pin in id_pins:
        new_input = DigitalInOut(pin)
        new_input.direction = Direction.INPUT
        new_input.pull = Pull.UP
        id_inputs.append(new_input)

    output = DigitalInOut(output_pin)
	output.switchToOutput();

    # Make the display context
    context = displayio.Group(max_size=10)

    #fonts
    font9 = bitmap_font.load_font("/fonts/HelveticaNeue-9.bdf")
    font18 = bitmap_font.load_font("/fonts/HelveticaNeue-18.bdf")
    font24 = bitmap_font.load_font("/fonts/HelveticaNeue-Bold-24.bdf")

    # background
    background_bitmap = SolidBitmap()
    background_palette = displayio.Palette(1)
    background_palette[0] = black_color
    background_sprite = displayio.TileGrid(background_bitmap, pixel_shader=background_palette)

    context.append(background_sprite)

    sensors = []
    sensor_digits = displayio.Group(max_size=len(sensor_pins), y=digit_y)
    digit_width = 0

    for pin in sensor_pins:
        new_sensor = DigitalInOut(pin[0])
        new_sensor.direction = Direction.INPUT
        new_sensor.pull = Pull.UP
        sensors.append(new_sensor)

        digit = Digit(font=font24, text=pin[1])
        if digit_width == 0:
			x, y, w, h = digit.get_bounding_box()
            digit_width = w
		digit.center_on_x((display.width/2) + pin[2] * digit_width)
        sensor_digits.append(digit)

    context.append(sensor_digits)

    error_message = BetterLabel(font=font18, text="Filament Out!", color=error_color, y=error_message_y, hidden=True)
    context.append(error_message)

    label_text = BetterLabel(font=font9, text="filament sensors", color=label_color, y=label_text_y, hidden=True)
    context.append(label_text)

    machine_id = None
    machine_name = None
    sensors_in_use = None
    current_states = [False, False, False, False, False]
    filament_out = False
	context_shown = False
	active_sensor_count = 0

    while True:
        current_id = (id_inputs[0].value) | (id_inputs[1].value << 1) | (id_inputs[2].value << 2) | (id_inputs[3].value << 3)

        if current_id != machine_id:
            machine_id = current_id
            machine = machine_defs[machine_id]
            sensors_in_use = machine[0]

            if machine_name:
                context.remove(machine_name)

            machine_name = BetterLabel(font=font18, text=machine[1], color=machine_name_color, y=machine_name_y)
            context.append(machine_name)

			active_sensor_count = 0
            for uses_sensor, digit in zip(sensors_in_use, digits):
                digit.active = uses_sensor == 1
				digit.hidden = uses_sensor == -1

				if digit.active:
					active_sensor_count++

        new_states = []
        for uses_sensor, sensor in zip(sensors_in_use, sensors):
            new_states.append(sensor.value and (uses_sensor == 1))

        if new_states != current_states:
            for state, digit in zip(new_states, digits):
                digit.error = state
            current_states = new_states

        new_filament_out = True in current_states

        if new_filament_out != filament_out:
            filament_out = new_filament_out
            output.value = filament_out
			error_message.hidden = not filament_out
			sensor_digits.y = digit_offset if filament_out else 0
			label_text.hidden = filament_out or active_sensor_count == 0

		if not context_shown:
		    display.show(context)
			context_shown = True

        time.sleep(0.01)
