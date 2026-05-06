from ..helper import ProjectConfig, Module
from pibody import Joystick, Servo

modules={Module.JOYSTICK: "F"}

class JoystickTester:
    config = ProjectConfig(
        title="Joystick",
        modules=modules,
        servo8=True,
        servo9=True
    )
    def __init__(self):
        self.joystick = Joystick(modules[Module.JOYSTICK])
        self.servo8 = Servo(8)
        self.servo9 = Servo(9)

    def loop(self):
        raw_x = self.joystick.read_x()
        raw_y = self.joystick.read_y()

        self.servo8.angle(raw_x * 180)
        self.servo9.angle(raw_y * 180)


        
