from machine import ADC, Pin

adc_pins = [26, 27, 28]

class JoystickPlus():
    def __init__(self, pinX, pinY):
        if pinX in adc_pins:
            self.X = ADC(Pin(pinX))
            self.X_adc = True
        else:
            self.X = Pin(pinX, Pin.IN)
            self.X_adc = False
        if pinY in adc_pins:
            self.Y = ADC(Pin(pinY))
            self.Y_adc = True
        else:
            self.Y = Pin(pinY, Pin.IN)
            self.Y_adc = False

    def read(self):
        x = self.X.read_u16() if self.X_adc else self.X.value()
        y = self.Y.read_u16() if self.Y_adc else self.Y.value()
        return (x, y)