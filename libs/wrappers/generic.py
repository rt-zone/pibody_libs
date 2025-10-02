from machine import Pin
from machine import ADC as _ADC
from libs.helper import get_pins_by_slot

class LED(Pin):
    def __init__(self, slot):
        _, sda, _ = get_pins_by_slot(slot)
        super().__init__(sda, Pin.OUT)
    
class ButtonLike(Pin):
    def __init__(self, slot):
        _, sda, _ = get_pins_by_slot(slot)
        super().__init__(sda, Pin.IN)

    def read(self):
        """Returns value of sensor: 0 or 1"""
        return super().value()
    
class ADC(_ADC):
    def __init__(self, slot):
        _, sda, _ = get_pins_by_slot(slot, adc=True)
        super().__init__(Pin(sda))
    
    def read(self):
        """Returns value of sensor from 0 to 1"""
        return self.read_u16() / 65536
    
