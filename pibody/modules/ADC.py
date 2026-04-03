from machine import Pin, ADC as _ADC

# TODO: Make so that ADC can accept not only pin values but ADC ids as well
class ADC(_ADC):
    def __init__(self, pin):
        super().__init__(Pin(pin))
    
    def read(self):
        """Returns value of sensor from 0 to 1"""
        return self.read_u16() / 65535