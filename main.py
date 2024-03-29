# Hypercube Active Filament Sensor

import gc

import board
import displayio
import terminalio
import time
import math

from adafruit_display_text import label
from adafruit_featherwing import minitft_featherwing
from adafruit_bitmap_font import bitmap_font

from digitalio import DigitalInOut, Direction, Pull

import neopixel

minitft = minitft_featherwing.MiniTFTFeatherWing()
display = minitft.display

led = neopixel.NeoPixel(board.NEOPIXEL, 1)

#---------------------------------------
black_color = 0x000000

machine_name_color = 0xFFFFFF
machine_name_y = 9

error_color = 0xFF0017
error_message_y = 71

digit_color_inactive = 0x808080
digit_color_active = 0x00FF1A
digit_color_error = error_color
digit_y = 40

label_color = 0xFFFFFF
label_text_y = 71

blink_period = 0.5
blink_duty_cycle = 0.8

#---------------------------------------
machine_defs = [ \
	[[-1, -1, -1, -1, -1, -1], 24, "------------\nNO TOOL\n------------"], \
	[[ 0,  0,  1,  0,  0, -1], 24, "V6"], \
	[[ 0,  0,  1,  0,  0, -1], 24, "Volcano"], \
	[[ 0,  0,  0,  0,  0, -1], 24, "Laser"], \
	[[ 1,  1,  1,  1,  0, -1], 24, "Kraken"], \
	[[-1, -1, -1, -1, -1,  1], 24, "Zesty"], \
	[[ 0,  0,  1,  0,  0, -1], 18, "Super Volcano"], \
	[[-1, -1, -1, -1, -1, -1], 24, "invalid\ntool id"], \
	[[ 1,  1,  1,  1,  1, -1], 18, "Diamond Color"], \
	[[-1, -1, -1, -1, -1,  1], 24, "Titan Aero"], \
	[[-1, -1, -1, -1, -1,  1], 18, "Dyze Design"], \
	[[-1, -1, -1, -1, -1, -1], 24, "invalid\ntool id"], \
	[[-1, -1, -1, -1, -1, -1], 24, "invalid\ntool id"], \
	[[-1, -1, -1, -1, -1, -1], 24, "invalid\ntool id"], \
	[[-1, -1, -1, -1, -1, -1], 24, "invalid\ntool id"], \
	[[-1, -1, -1, -1, -1, -1], 24, "Nozzle\nSetup"]]

sensor_pins = [ \
	[board.A1, "1", -2], \
	[board.A2, "2", -1], \
	[board.A3, "3", 0], \
	[board.A4, "4", 1], \
	[board.A5, "5", 2], \
	[board.A0, "Auxilary", 0]]

id_pins = [board.D10, board.RX, board.TX, board.D4]

output_pin = board.D9

#---------------------------------------

class Hideable(object):
	hidden_offset = 1000

	def center_on_x(self, center_x = display.width / 2):
		new_x = int(center_x - self.bounding_box[2] / 2)
		if self.x != new_x:
			self.x = new_x

	def hide(self):
		new_x = (self.x % self.hidden_offset) + self.hidden_offset
		if self.x != new_x:
			self.x =new_x

	def show(self):
		new_x = self.x % self.hidden_offset
		if self.x != new_x:
			self.x = new_x

	def set_hide(self, hidden):
		if hidden:
			self.hide()
		else:
			self.show()

class BetterGroup(displayio.Group, Hideable):
	pass

class BetterLabel(label.Label, Hideable):
	pass

class Digit(BetterLabel):
	def __init__(self, text="*", font=None, active=True, error=False, **kwargs):
		self.__active = active
		self.__error = error
		self.__blink = True
		super().__init__(font, text=text, max_glyphs=len(text)+1, color=self._digit_color(), **kwargs)

		self.y = 0
		bounds = self.bounding_box
		w = self.font.get_glyph(ord('0')).shift_x
		h = bounds[3]

		self.border_palette = displayio.Palette(2)
		self.border_palette[0] = black_color
		self.border_palette[1] = black_color

		border_bitmap = displayio.Bitmap(w+9, h+8, 2)
		self._fill_borders(border_bitmap, 2)
		border_sprite = displayio.TileGrid(border_bitmap, pixel_shader=self.border_palette, x=-4, y=int(-h/2-4))
		self.insert(0, border_sprite)

	def _fill_borders(self, bitmap, thickness):
		w = bitmap.width
		h = bitmap.height

		for i in range(w):
			for j in range(thickness):
				bitmap[i, j] = 1
				bitmap[i, h-1-j] = 1

		for j in range(h):
			for i in range(thickness):
				bitmap[i, j] = 1
				bitmap[w-1-i, j] = 1

	@property
	def blink(self):
		return self.__blink

	@blink.setter
	def blink(self, value):
		self.__blink = value
		self._update_color()

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

	def _digit_color(self):
		if not self.blink:
			return black_color
		elif self.__error:
			return digit_color_error
		elif self.__active:
			return digit_color_active
		else:
			return digit_color_inactive

	def _border_color(self):
		if not self.blink:
			return black_color
		elif self.__error:
			return digit_color_error
		else:
			return black_color

	def _update_color(self):
		self.color = self._digit_color()
		self.border_palette[1] = self._border_color()

#---------------------------------------
if __name__ == '__main__':
	led.brightness = 0.005
	led[0] = black_color

	id_inputs = []
	for pin in id_pins:
		new_input = DigitalInOut(pin)
		new_input.direction = Direction.INPUT
		new_input.pull = Pull.UP
		id_inputs.append(new_input)

	output = DigitalInOut(output_pin)
	output.switch_to_output();

	# Make the display context
	context = displayio.Group(max_size=10)

	#fonts
	font12 = bitmap_font.load_font("/fonts/HelveticaNeue-Bold-12.bdf")
	font18 = bitmap_font.load_font("/fonts/HelveticaNeue-Bold-18.bdf")
	font24 = bitmap_font.load_font("/fonts/HelveticaNeue-Bold-24.bdf")
	font36 = bitmap_font.load_font("/fonts/HelveticaNeue-Bold-36.bdf")

	font_bin = { 12: font12, 18: font18, 24: font24, 36: font36 }

	sensors = []
	sensor_digits = displayio.Group(max_size=len(sensor_pins), y=digit_y)
	digit_width = 0

	for pin in sensor_pins:
		new_sensor = DigitalInOut(pin[0])
		new_sensor.direction = Direction.INPUT
		new_sensor.pull = Pull.UP
		sensors.append(new_sensor)

		digit = Digit(font=font36, text=pin[1])
		if digit_width == 0:
			digit_width = digit.bounding_box[2]
		digit.center_on_x((display.width/2) + pin[2] * (digit_width+20))
		sensor_digits.append(digit)

	context.append(sensor_digits)

	error_message = BetterLabel(font=font24, text="Filament Out!", color=error_color, y=error_message_y)
	error_message.center_on_x();
	error_message.hide()
	context.append(error_message)

	label_text = BetterLabel(font=font12, text="filament sensors", color=label_color, y=label_text_y)
	label_text.center_on_x();
	context.append(label_text)

	machine_id = None
	machine_name = None
	sensors_in_use = None
	current_states = [False, False, False, False, False]
	filament_out = -1
	context_shown = False
	active_sensor_count = 0
	blink_state = True
	blink_time = 0

	while True:
		current_id = 0
		for input, bit in zip(id_inputs, [1, 2, 4, 8]):
			if input.value == 0:
				current_id += bit

		if current_id != machine_id:
			machine_id = current_id
			machine = machine_defs[machine_id]
			sensors_in_use = machine[0]

			if machine_name:
				context.remove(machine_name)

			machine_name = BetterLabel(font=font_bin[machine[1]], text=machine[2], color=machine_name_color, y=machine_name_y)
			machine_name.center_on_x(display.width/2);
			machine_name.y = int((machine_name.bounding_box[3] + 1) / 2)
			context.append(machine_name)

			active_sensor_count = 0
			shown_sensor_count = 0
			for uses_sensor, digit in zip(sensors_in_use, sensor_digits):
				digit.active = uses_sensor == 1
				digit.set_hide(uses_sensor == -1)

				if uses_sensor == 1:
					active_sensor_count += 1
				if uses_sensor != -1:
					shown_sensor_count += 1

			filament_out = -1

		new_states = []
		for uses_sensor, sensor in zip(sensors_in_use, sensors):
			new_states.append(uses_sensor == 1 and sensor.value == 0)

		if new_states != current_states:
			for state, digit in zip(new_states, sensor_digits):
				digit.error = state
			current_states = new_states

		new_filament_out = True in current_states

		if new_filament_out != filament_out:
			filament_out = new_filament_out
			output.value = filament_out
			error_message.set_hide(not filament_out)
			led[0] = digit_color_error if filament_out else digit_color_active
			label_text.set_hide(filament_out or active_sensor_count == 0 or shown_sensor_count == 1)
			for digit in sensor_digits:
				digit.blink = True
			blink_time = time.monotonic()
			blink_state = True

		if filament_out:
			new_blink = math.fmod(time.monotonic()-blink_time, blink_period) / blink_period < blink_duty_cycle
			if new_blink != blink_state:
				blink_state = new_blink;
				for digit in sensor_digits:
					if digit.error:
						digit.blink = blink_state

		if not context_shown:
			display.show(context)
			context_shown = True

		time.sleep(0.01)
