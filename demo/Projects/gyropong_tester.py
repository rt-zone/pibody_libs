from demo.helper import ProjectConfig, Module
from pibody import display, LED, Buzzer, GyroAccel
import time


red_color = display.color(255, 0, 0)
yellow_color = display.color(255, 255, 0)
green_color = display.color(0, 255, 0)
dim_red_color = display.color(100, 0, 0)
dim_yellow_color = display.color(100, 100, 0)
dim_green_color = display.color(0, 100, 0)
color_map = [red_color, yellow_color, green_color]
dim_color_map = [dim_red_color, dim_yellow_color, dim_green_color]

x = 50
y = 100
r = 15

freq_map = [
    440,  # A4  
    330,  # E4
    220,  # C4
]
        
modules = {
    Module.LED_R : "A",
    Module.LED_Y : "B",
    Module.LED_G : "C",
    Module.BUZZER : "D",
    Module.GYRO_ACCEL : "E"
}

class GyroPongTester:

    config = ProjectConfig(
        title = "GyroPong",
        modules = modules
    )

    def __init__(self):
        pass
    
    def update_leds(self, index):
        for i in range(len(self.leds)):
            self.leds[i].value(i==index)
            color = color_map[i] if i == index else dim_color_map[i]
            display.fill_circle(x, y + i * 40, r, color)        

    def start(self):
        self.led_r = LED(modules[Module.LED_R])
        self.led_y = LED(modules[Module.LED_Y])
        self.led_g = LED(modules[Module.LED_G])
        self.buzzer = Buzzer(modules[Module.BUZZER])
        self.gyro_accel = GyroAccel(modules[Module.GYRO_ACCEL])

        self.leds = [self.led_r, self.led_y, self.led_g]
        self.buzzer.freq(440)

        self._threshold = 0.3 
        self._led_index = 0
        self._last_index = 0
        self._last_time = 0
        self.buzzer.beep()
        for led in self.leds:
            led.on()
        time.sleep_ms(100) 
        for led in self.leds:
            led.off()

    def loop(self):
        x, y, z = self.gyro_accel.read_accel()
        
        display.crosshair(-y, -x, 5, 150, 150, 60)

        if (time.ticks_diff(time.ticks_ms(), self._last_time) > 250):
            self._last_time = time.ticks_ms()

            if x > self._threshold:
                self._led_index += -1
            elif x < -self._threshold:
                self._led_index += 1
            self._led_index = min(max(self._led_index, 0), len(freq_map) - 1)
            
            if self._last_index != self._led_index:
                self.buzzer.make_sound(freq_map[self._led_index], 0.1, 0.05)
                self._last_index = self._led_index

        self.update_leds(self._led_index)
        time.sleep(0.05)


if __name__ == "__main__":
    project = GyroPongTester()
    project.start()
    while True:
        project.loop()