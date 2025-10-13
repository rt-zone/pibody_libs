from libs.modules.Buzzer import Buzzer as _Buzzer
from libs.modules.PWM import PWM as _PWM
from libs.modules.Joystick import Joystick as _Joystick
from libs.modules.SoundSensor import SoundSensor as _SoundSensor
from libs.modules.LEDTower import LEDTower as _LEDTower
from libs.modules.RotaryEncoder import RotaryEncoder

from libs.helper import get_pins_by_slot


class Buzzer(_Buzzer):
    def __init__(self, slot):
        pin = get_pins_by_slot(slot)[1]
        super().__init__(pin)

class PWM(_PWM):
    def __init__(self, slot):
        pin = get_pins_by_slot(slot)[1]
        super().__init__(pin)

class Joystick(_Joystick):
    def __init__(self, slot):
        _, pinX, pinY = get_pins_by_slot(slot)
        super().__init__(pinX, pinY)

class Encoder(RotaryEncoder):
    def __init__(self, slot):
        _, sda, scl = get_pins_by_slot(slot)
        super().__init__(clk=sda, dt=scl)
    
    def read(self):
        return self.value()

class SoundSensor(_SoundSensor):
    def __init__(self, slot):
        _, analog_pin, digital_pin = get_pins_by_slot(slot)
        super().__init__(analog_pin, digital_pin)

class LEDTower(_LEDTower):
    def __init__(self, slot):
        if type(slot) == str:
            pin = get_pins_by_slot(slot)[1]
        elif type(slot) == int:
            pin = slot
        else:
            raise ValueError("Wrong slot type")
        
        super().__init__(pin)