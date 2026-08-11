from time import sleep, ticks_ms
from demo.helper import ProjectConfig, Module
from pibody import Button, Encoder, Switch, Touch, Pot, LEDTower, display

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
        self.mode_index = 0
        self.current_color = WHITE
        self.colors = [WHITE, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, ORANGE]
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
        self.mode_index = 0
        self.current_mode = self.modes[self.mode_index][1]
        
        self.encoder.bound(1, 10)
        self.encoder.set(5)
    
    def update_speed(self):
        self.speed = self.encoder._min_val + self.encoder._max_val - self.encoder.value()
        
        
    def apply_brightness(self, color):
        bright = 0.1 + self.adc.read() * 0.9
        return tuple(int(c * bright) for c in color)

    def mode_solid(self):
        color = self.apply_brightness(self.current_color)
        self.np.fill(color)
        self.np.write()

    def mode_rainbow(self):
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
        color = self.apply_brightness(self.current_color)
        tail = 2
        tick = (ticks_ms() // (self.speed * 15)) % (self.n * 2 - 2)
        head = tick if tick < self.n else (self.n * 2 - 2) - tick
        self.comet_direction = 1 if tick < self.n else -1

        self.np.fill((0,0,0))
        for i in range(tail + 1):
            pos = head - i * self.comet_direction
            if 0 <= pos < self.n:
                fade = 1.0 if i == 0 else (tail - i + 1) / (tail + 1)
                self.np[pos] = tuple(int(c * fade) for c in color)

        self.np.write()

    def mode_blink(self):
        color = self.apply_brightness(self.current_color)
        blink_state = (ticks_ms() // (self.speed * 100)) % 2
        self.np.fill(color if blink_state else (0,0,0))
        self.np.write()

    def mode_off(self):
        self.np.fill((0,0,0))
        self.np.write()

    def rotate_color(self):
        idx = self.colors.index(self.current_color)
        self.current_color = self.colors[(idx + 1) % len(self.colors)]
        print("Color changed to:", self.current_color)

    
    def _rotate_mode(self, direction):
        self.mode_index += direction
        self.mode_index %= len(self.modes)
        mode = self.modes[self.mode_index]
        self.current_mode = mode[1]
        print("Mode:", mode[0])
    def next_mode(self):
        self._rotate_mode(1)
    def prev_mode(self):
        self._rotate_mode(-1)        


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
        pass
    
    def start(self):
        self.btn_prev = Button(modules[Module.BUTTON_BLUE])
        self.btn_next = Button(modules[Module.BUTTON_YELLOW])
        self.pot = Pot(modules[Module.POTENTIOMETER])
        self.btn_color = Touch(modules[Module.TOUCH_SENSOR])
        self.switch = Switch(modules[Module.SWITCH])
        self.encoder = Encoder(modules[Module.ENCODER])
       
        self.np = LEDTower(8)
        self.manager = ModeManager(self.np, self.pot, self.encoder, 8)
        self.last_button_press = 0

    def handle_buttons(self):
        #Debounce
        if ticks_ms() - self.last_button_press < 200: return
    
        if self.btn_next.value():
            self.manager.next_mode()
            self.last_button_press = ticks_ms()
        
        if self.btn_prev.value():
            self.manager.prev_mode()
            self.last_button_press = ticks_ms()

        if self.btn_color.value():
            self.manager.rotate_color()
            self.last_button_press = ticks_ms()

        self.manager.current_mode()

    def render_button_states(self):
        display.fill_circle(50, 50, 20, display.BLUE if self.btn_prev.value() else display.color(0,0,50))
        display.fill_circle(50, 120, 20, display.YELLOW if self.btn_next.value() else display.color(50, 50, 0))
        brightness = int((0.1 + self.pot.read() * 0.9) * 255)
        color = display.color(brightness, brightness, brightness)
        display.fill_circle(50, 190, 20, color)
        display.text(f"{self.encoder.value():2}", 150, 40, display.font_large)
        display.fill_rect(150, 100, 40, 40, display.WHITE if self.switch() else display.color(50,50,50))
        
        color = display.color(*self.manager.current_color) 
        fg = color * (1 - self.btn_color())
        bg = color * self.btn_color()
        display.text("Touch", 150, 190, display.font_large,fg,bg)

  
    
    
    def loop(self):
        self.render_button_states()
        self.manager.update_speed()
        if self.switch.value() == 0:
            self.manager.mode_off()
            return
        
        self.handle_buttons()
        self.manager.current_mode()
        
        sleep(0.005)


if __name__ == "__main__":
    project = RGBTester()
    project.start()
    while True:
        project.loop()

        
