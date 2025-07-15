from machine import ADC, Pin

class JoystickPlus():
    def __init__(self, pinX, pinY):
        self.X = ADC(Pin(pinX))
        self.Y = ADC(Pin(pinY))

    def read(self):
        x = self.X.read_u16()
        y = self.Y.read_u16()
        return (x, y)