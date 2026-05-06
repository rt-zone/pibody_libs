import time
from ..helper import ProjectConfig, Module
from pibody import display, PWM, Motion, Light



light_treshold = 37500  # максимальное значение для светодиода
dim_brightness = 2500   # начальная яркость светодиода
full_brightness = 35000 # максимальная яркость светодиода

x = 10
y = 32
length = 200
height = 9
border = True

def fade_to(brightness, led, step=1000, delay=0.01):
    current = led.duty_u16()
    if brightness > current:
        for i in range(current, brightness, step):
            led.duty_u16(i)
            time.sleep(delay)
    else:
        for i in range(current, brightness, -step):
            led.duty_u16(i)
            time.sleep(delay)
    led.duty_u16(brightness)

modules={
    Module.LED_R : "A",
    Module.MOTION_SENSOR : "B",
    Module.LIGHT_SENSOR : "C"
}

class DimmingTester:
    config = ProjectConfig(
        title="Dimming System",
        modules=modules
    )
    def __init__(self):
        self.color = display.color(0, 0, 0)
        self.led = PWM(modules[Module.LED_R])
        self.motion = Motion(modules[Module.MOTION_SENSOR])
        self.light = Light(modules[Module.LIGHT_SENSOR])
        self.led.freq(1000)
        
    def loop(self):
        light_value = self.light.read_u16()
        motion_value = self.motion.value()

        display.text("Light Sensor is working   ", x, y - 22)
        display.text("Light value: " + str(light_value) + "/65535", x, y + 9)
        display.linear_bar(x, y, value=light_value, min_value=0, max_value=65535,length=length, height=height, border=True, color=self.color)

        if light_value > light_treshold:
            self.color = display.color(64, 64, 64)
            fade_to(0, self.led)
            return
        if motion_value == 1:
            self.color = display.color(255, 255, 0)
            fade_to(full_brightness, self.led)
        else:
            self.color = display.color(88, 88, 0)
            fade_to(dim_brightness, self.led)

