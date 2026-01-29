from machine import Pin
from machine import ADC as _ADC
from pibody.helper import resolve_pins, get_i2c

from BME280 import BME280
from MPU6050 import MPU6050
from LSM6DS3 import LSM6DS3
from VEML6040 import VEML6040
from VL53L0X import VL53L0X
from SSD1306 import SSD1306

from .modules.Buzzer import Buzzer as _Buzzer
from .modules.PWM import PWM as _PWM
from .modules.Joystick import Joystick as _Joystick
from .modules.SoundSensor import SoundSensor as _SoundSensor
from .modules.LEDTower import LEDTower as _LEDTower
from RotaryEncoder import RotaryEncoder



class LED(Pin):
    def __init__(self, slot):
        pin = resolve_pins(slot)[0]
        super().__init__(pin, Pin.OUT)
    
class Button(Pin):
    def __init__(self, slot):
        pin = resolve_pins(slot)[0]
        super().__init__(pin, Pin.IN)

    def read(self):
        """Returns value of sensor: 0 or 1"""
        return super().value()
    
class ADC(_ADC):
    def __init__(self, slot):
        pin = resolve_pins(slot)[0]
        super().__init__(Pin(pin))
    
    def read(self):
        """Returns value of sensor from 0 to 1"""
        return self.read_u16() / 65535
    


class ClimateSensor(BME280):
    def __init__(self, slot, hard_i2c=False):
        super().__init__(get_i2c(slot, hard_i2c))


def GyroAccel(slot, hard_i2c=False):
    i2c = get_i2c(slot, hard_i2c)
    if 0x68 in i2c.scan():
        return MPU6050(i2c)
    elif 0x6A in i2c.scan():
        return LSM6DS3(i2c)
    else:
        raise ValueError(f"Invalid i2c address '{i2c.scan()}' for slot '{slot}'")  

class ColorSensor(VEML6040):
    def __init__(self, slot, hard_i2c=False):
        super().__init__(get_i2c(slot, hard_i2c))

class DistanceSensor(VL53L0X):
    def __init__(self, slot, hard_i2c=False):
        super().__init__(get_i2c(slot, hard_i2c))

class OLED(SSD1306):
    def __init__(self, slot, hard_i2c=False, width=128, height=64):
        super().__init__(get_i2c(slot, hard_i2c), width=width, height=height)

class Buzzer(_Buzzer):
    def __init__(self, slot : int):
        super().__init__(resolve_pins(slot)[0])

class PWM(_PWM):
    def __init__(self, slot : int):
        super().__init__(resolve_pins(slot)[0])

class LEDTower(_LEDTower):
    def __init__(self, slot : int = 8):
        super().__init__(resolve_pins(slot)[0])

class Joystick(_Joystick):
    def __init__(self, slot : str | tuple):
        super().__init__(*resolve_pins(slot))

class Encoder(RotaryEncoder):
    def __init__(self, slot : str | tuple):
        super().__init__(*resolve_pins(slot))

class SoundSensor(_SoundSensor):
    def __init__(self, slot):
        super().__init__(*resolve_pins(slot))