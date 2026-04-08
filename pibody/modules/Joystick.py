from Extensions.ADCExt import ADC 
# TODO: Allow ports other than "F" but call warnings
class Joystick():
    def __init__(self, pinX, pinY):
            self.X = ADC(pinX)
            self.Y = ADC(pinY)

    def read(self):
        """Returns value of Joystick for X and Y axis. Value range: from 0 to 1."""
        return (self.read_x(), self.read_y())
    
    def read_x(self):
         """Returns x-axis position value of joystick. Value range: from 0 to 1"""
         return self.X.read()
    
    
    def read_y(self):
         """Returns y-axis position value of joystick. Value range: from 0 to 1"""
         return self.Y.read()