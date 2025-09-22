from machine import Pin, ADC, I2C, SoftI2C

from BME280 import BME280
from MPU6050 import MPU6050
from LSM6DS3 import LSM6DS3
from VEML6040 import VEML6040
from VL53L0X import VL53L0X
from SSD1306 import SSD1306

from libs.general.RotaryEncoder import RotaryEncoder
from libs.general.NeoPixelPlus import NeoPixelPlus
from libs.general.BuzzerPlus import BuzzerPlus
from libs.general.ServoPlus import ServoPlus
from libs.general.JoystickPlus import JoystickPlus
from libs.general.PWMPlus import PWMPlus
from libs.DisplayPlus import DisplayPlus
from libs.iot.WiFi import WiFi
from libs.iot.telegram_bot import TelegramBot

_SLOT_MAP = {
    'A': (0, 0, 1),
    'B': (1, 2, 3),
    'D': (0, 4, 5),
    'C': (None, 28, 22),
    'E': (1, 6, 7),
    'F': (1, 26, 27),
    'G': (0, 16, 17),
    'H': (1, 18, 19),
}

_ADC_SLOT_MAP = {
    'C': (None, 28, 22),
    'F': (1, 26, 27)
}

# Functions-helpers
def get_slot_pins(slot, adc=False, joystick=False):
    slot = slot.upper()[0]
    if joystick and (slot != 'F'):
        raise ValueError(f"Joystick is not supported for slot '{slot}'. Recomendation: Use slot 'F' instead.")
    elif adc and (slot not in _ADC_SLOT_MAP):
        raise ValueError(f"Invalid slot '{slot}'. Use C or F (Other slots are not ADC-compatible)")
    elif slot not in _SLOT_MAP:
        raise ValueError(f"Invalid slot '{slot}'. Use A, B, C, D, E, or F (C is not I2C-compatible)")
    bus, sda, scl = _SLOT_MAP[slot]
    return (bus, sda, scl)

def get_i2c(slot, hard_i2c=False):
    if type(slot) == I2C or type(slot) == SoftI2C:
        return slot
    bus, sda, scl = get_slot_pins(slot)
    if hard_i2c:
        return I2C(bus, scl=Pin(scl), sda=Pin(sda))
    else:
        return SoftI2C(scl=Pin(scl), sda=Pin(sda))


# i2c modules
class ClimateSensor(BME280):
    def __init__(self, slot, hard_i2c=False):
        super().__init__(get_i2c(slot, hard_i2c))


def GyroAxel(slot, hard_i2c=False):
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


# displays 
class OLED(SSD1306):
    def __init__(self, slot, hard_i2c=False, width=128, height=64):
        super().__init__(get_i2c(slot, hard_i2c), width=width, height=height)

class Display(DisplayPlus):
    def __init__(self):
        super().__init__()

class LEDTower(NeoPixelPlus):
    def __init__(self, pin=8, led_num=8):
        super().__init__(pin=pin, led_num=led_num)

# general modules
class Encoder(RotaryEncoder):
    def __init__(self, slot):
        _, sda, scl = get_slot_pins(slot)
        super().__init__(clk=sda, dt=scl)
        
class Buzzer(BuzzerPlus):
    def __init__(self, slot):
        _, sda, _ = get_slot_pins(slot)
        super().__init__(pin=sda)

class Servo(ServoPlus):
    def __init__(self, pin, freq=50):
        super().__init__(pin=pin, freq=freq)

class LED(Pin):
    def __init__(self, slot):
        _, sda, _ = get_slot_pins(slot)
        super().__init__(sda, Pin.OUT)
    
class ButtonLike(Pin):
    def __init__(self, slot):
        _, sda, _ = get_slot_pins(slot)
        super().__init__(sda, Pin.IN)
    def read(self):
        """
            Returns 0 or 1
        """
        return super().value()
    
class Button(ButtonLike):
    def __init__(self, slot):
        super().__init__(slot)

class Switch(ButtonLike):
    def __init__(self, slot):
        super().__init__(slot)

class TouchSensor(ButtonLike):
    def __init__(self, slot):
        super().__init__(slot)

class MotionSensor(ButtonLike):
    def __init__(self, slot):
        super().__init__(slot)

class AnalogLike(ADC):
    def __init__(self, slot):
        _, sda, _ = get_slot_pins(slot, adc=True)
        super().__init__(Pin(sda))
    
    def read(self):
        """
            Returns value of sensor from 0 to 1
        """
        return self.read_u16() / 65536

class LightSensor(AnalogLike):
    def __init__(self, slot):
        super().__init__(slot)

class Potentiometer(AnalogLike):
    def __init__(self, slot):
        super().__init__(slot)

def SoundSensor(slot, analog=False):
    return AnalogLike(slot) if analog else ButtonLike(slot)

class Joystick(JoystickPlus):
    def __init__(self, slot):
        _, sda, scl = get_slot_pins(slot, joystick=True)
        super().__init__(pinX=sda, pinY=scl)

class PWM(PWMPlus):
    def __init__(self, slot):
        _, sda, _ = get_slot_pins(slot)
        super().__init__(sda)


# Aliases 
Climate = ClimateSensor
Color = ColorSensor
Distance = DistanceSensor
Touch = TouchSensor
Motion = MotionSensor
Light = LightSensor
Pot = Potentiometer
Sound = SoundSensor
