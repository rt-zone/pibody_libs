import time
from demo.helper import ProjectConfig, Module
from pibody import display, PWM, Motion, Light


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
        pass

    def start(self):
        self.color = display.color(0, 0, 0)
        self.led = PWM(modules[Module.LED_R])
        self.motion = Motion(modules[Module.MOTION_SENSOR])
        self.light = Light(modules[Module.LIGHT_SENSOR])
        self.led.freq(1000)

        
    def fade_to(self, brightness, step=20, delay=0.01):
        current = self.led.duty()
        increment = (brightness - current) / step
        for _ in range(step):
            self.led.duty(self.led.duty() + increment)
            time.sleep(delay)
            
        self.led.duty(brightness)
    
    def loop(self):
        light_value = round(self.light.read(), 3)
        x, y = 10, 32

        display.text("Light Sensor is working   ", x, y - 22)
        display.text(f"Light value: {light_value:.3f}/1", x, y + 9)
        display.linear_bar(x, y, value=round(light_value * 100), min_value=0, max_value=100,length=200, height=9, border=True, color=self.color)

        circle_color = display.YELLOW if self.motion() else display.color(88, 88, 0)
        display.fill_circle(120, 100, 20, circle_color)

        if light_value > 0.5:
            self.color = display.color(64, 64, 64)
            self.fade_to(0)
            return

        if self.motion.value():
            self.color = display.color(255, 255, 0)
            self.fade_to(1)
        else:
            self.color = display.color(88, 88, 0)
            self.fade_to(0.05)



if __name__ == "__main__":
    project = DimmingTester()
    project.start()
    while True:
        project.loop()