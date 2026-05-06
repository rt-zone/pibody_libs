from time import sleep, ticks_ms
from ..helper import ProjectConfig, Module
from pibody import Button, Encoder, Switch, Touch, Pot, LEDTower

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)
ORANGE = (255, 165, 0)
class ModeManager:
    def __init__(self, np, adc, encoder, n=8):
        self.np = np
        self.adc = adc
        self.encoder = encoder
        self.n = n
        self.current_mode = 0
        self.current_color = RED
        self.colors = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, WHITE, ORANGE]
        self.rainbow_offset = 0
        self.comet_direction = 1
        self.last_update = 0
        self.speed = 0
        self.max_speed = 0
        self.min_speed = 0

        self.modes = [
            ("Solid color", self.mode_solid),
            ("Rainbow", self.mode_rainbow),
            ("Comet", self.mode_comet),
            ("Blinking", self.mode_blink)
        ]

    def update_speed(self):
        if self.last_update != self.current_mode:
            if self.current_mode == 1:
                self.encoder.bound(1, 50)
                self.encoder.set(25)
                self.max_speed = 1
                self.min_speed = 50
            elif self.current_mode == 2 or self.current_mode == 3:
                self.encoder.bound(50, 200)
                self.encoder.set(120, incr=10)
                self.max_speed = 50
                self.min_speed = 200
            self.last_update = self.current_mode
        self.speed = self.max_speed + self.min_speed - self.encoder.value()

    def get_brightness(self):
        pot_value = self.adc.read_u16()
        return 0.1 + (pot_value / 65535) * 0.9

    def apply_brightness(self, color):
        bright = self.get_brightness()
        return tuple(int(c * bright) for c in color)

    def mode_solid(self):
        color = self.apply_brightness(self.current_color)
        for i in range(self.n):
            self.np[i] = color
        self.np.write()

    def mode_rainbow(self):
        self.update_speed()
        for i in range(self.n):
            pos = ((i * 256 // self.n) + self.rainbow_offset) % 256
            if pos < 85:
                r, g, b = pos * 3, 255 - pos * 3, 0
            elif pos < 170:
                pos -= 85
                r, g, b = 255 - pos * 3, 0, pos * 3
            else:
                pos -= 170
                r, g, b = 0, pos * 3, 255 - pos * 3
            self.np[i] = self.apply_brightness((r, g, b))
        self.np.write()
        self.rainbow_offset = (self.rainbow_offset + 1) % 256
        sleep(self.speed / 1000)

    def mode_comet(self):
        self.update_speed()
        color = self.apply_brightness(self.current_color)
        tail = 2
        tick = (ticks_ms() // self.speed) % (self.n * 2 - 2)
        head = tick if tick < self.n else (self.n * 2 - 2) - tick
        self.comet_direction = 1 if tick < self.n else -1

        for i in range(self.n):
            self.np[i] = (0, 0, 0)

        for i in range(tail + 1):
            pos = head - i * self.comet_direction
            if 0 <= pos < self.n:
                fade = 1.0 if i == 0 else (tail - i + 1) / (tail + 1)
                self.np[pos] = tuple(int(c * fade) for c in color)

        self.np.write()

    def mode_blink(self):
        self.update_speed()
        color = self.apply_brightness(self.current_color)
        blink_state = (ticks_ms() // (self.speed * 5)) % 2
        for i in range(self.n):
            self.np[i] = color if blink_state else (0, 0, 0)
        self.np.write()

    def mode_off(self):
        for i in range(self.n):
            self.np[i] = (0, 0, 0)
        self.np.write()

    def run_current_mode(self):
        self.modes[self.current_mode][1]()

modules={
    Module.BUTTON_BLUE : "A",
    Module.BUTTON_YELLOW : "B",
    Module.POTENTIOMETER : "C",
    Module.ENCODER : "D",
    Module.SWITCH : "E",
    Module.TOUCH_SENSOR : "F"
}

class RGBTester:

    config = ProjectConfig(
        title="RGB Tester",
        modules=modules,
        led_tower=True
    )
    def __init__(self):
        self.btn_prev = Button(modules[Module.BUTTON_BLUE])
        self.btn_next = Button(modules[Module.BUTTON_YELLOW])
        self.pot = Pot(modules[Module.POTENTIOMETER])
        self.btn_color = Touch(modules[Module.TOUCH_SENSOR])
        self.switch = Switch(modules[Module.SWITCH])
        self.encoder = Encoder(modules[Module.ENCODER])
       
        self.np = LEDTower(8)
        self.manager = ModeManager(self.np, self.pot, self.encoder, 8)

        self.last_button_press = 0
        self.debounce = 200

    def debounce_check(self):
        return ticks_ms() - self.last_button_press > self.debounce

    def handle_buttons(self):
        if not self.debounce_check():
            return

        if self.btn_prev.value() == 1:
            self.manager.current_mode = (self.manager.current_mode - 1) % len(self.manager.modes)
            print("Mode:", self.manager.modes[self.manager.current_mode][0])
            self.last_button_press = ticks_ms()
            # while self.btn_prev.value() == 1: sleep(0.001)

        if self.btn_next.value() == 1:
            self.manager.current_mode = (self.manager.current_mode + 1) % len(self.manager.modes)
            print("Mode:", self.manager.modes[self.manager.current_mode][0])
            self.last_button_press = ticks_ms()
            # while self.btn_next.value() == 1: sleep(0.001)

        if self.btn_color.value() == 1:
            idx = self.manager.colors.index(self.manager.current_color)
            self.manager.current_color = self.manager.colors[(idx + 1) % len(self.manager.colors)]
            print("Color changed to:", self.manager.current_color)
            self.last_button_press = ticks_ms()
            # while self.btn_color.value() == 1: sleep(0.001)

    def loop(self):
        self.handle_buttons()
        if self.switch.value() == 0:
            self.manager.mode_off()
            sleep(0.1)
            return
        self.manager.run_current_mode()
        sleep(0.005)
