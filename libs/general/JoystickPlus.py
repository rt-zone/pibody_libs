from machine import ADC, Pin

class JoystickPlus():
    def __init__(self, pinX, pinY):
            self.X = ADC(Pin(pinX))
            self.Y = ADC(Pin(pinY))

    def read(self):
        """
            Returns value of Joystick for X and Y axis. Value range: from 0 to 1.
        """
        x = self.X.read_u16() / 65536
        y = self.Y.read_u16() / 65536
        return (x, y)