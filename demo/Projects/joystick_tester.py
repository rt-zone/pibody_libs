from demo.helper import ProjectConfig, Module
from pibody import Joystick, Servo, display

modules={Module.JOYSTICK: "F"}

class JoystickTester:
    config = ProjectConfig(
        title="Joystick",
        modules=modules,
        servo8=True,
        servo9=True
    )
    def __init__(self):
        pass

    def start(self):
        self.joystick = Joystick(modules[Module.JOYSTICK])
        self.servo8 = Servo(8)
        self.servo9 = Servo(9)
    
    def loop(self):
        raw_x = self.joystick.read_x()
        raw_y = self.joystick.read_y()
        
        display.crosshair(raw_x * 2 - 1, -raw_y * 2 + 1, 10, 120, 120, 60)

        self.servo8.angle(raw_x * 180)
        self.servo9.angle(raw_y * 180)

if __name__ == "__main__":
    project = JoystickTester()
    project.start()
    while True:
        project.loop()

        
