from pibody.helper import resolve_pins, get_i2c


def LED(slot):
    from machine import Pin
    pin = resolve_pins(slot)[0]
    return Pin(pin, Pin.OUT)
    
def Button(slot):
    from machine import Pin
    class RuntimePin(Pin):
        def __init__(self, slot):
            pin = resolve_pins(slot)[0]
            super().__init__(pin, Pin.IN)

        def read(self):
            """Returns value of sensor: 0 or 1"""
            return super().value()
    
    return RuntimePin(slot)
        
def ADC(slot):
    from machine import ADC as _ADC
    class RuntimeADC(_ADC):
        def __init__(self, slot):
            pin = resolve_pins(slot)[0]
            super().__init__(Pin(pin))
        
        def read(self):
            """Returns value of sensor from 0 to 1"""
            return self.read_u16() / 65535
    return RuntimeADC(slot)    


def ClimateSensor(slot, hard_i2c=False):
    from BME280 import BME280
    return BME280(get_i2c(slot, hard_i2c))
    

def GyroAccel(slot, hard_i2c=False):
    i2c = get_i2c(slot, hard_i2c)
    if 0x68 in i2c.scan():
        from MPU6050 import MPU6050
        return MPU6050(i2c)
    if 0x6A in i2c.scan():
        from LSM6DS3 import LSM6DS3
        return LSM6DS3(i2c)
    
    raise ValueError(f"Invalid i2c address '{i2c.scan()}' for slot '{slot}'")  

def ColorSensor(slot, hard_i2c=False):
    from VEML6040 import VEML6040
    return VEML6040(get_i2c(slot, hard_i2c))

def DistanceSensor(slot, hard_i2c=False):
    from VL53L0X import VL53L0X
    return VL53L0X(get_i2c(slot, hard_i2c))

def OLED(slot, hard_i2c=False):
    from SSD1306 import SSD1306
    return SSD1306(get_i2c(slot, hard_i2c), width=128, height=64)

def Buzzer(slot):
    from .modules.Buzzer import Buzzer as _Buzzer
    return _Buzzer(resolve_pins(slot)[0])

def PWM(slot):
    from .modules.PWM import PWM as _PWM
    return _PWM(resolve_pins(slot)[0])

def LEDTower(slot = 8):
    from .modules.LEDTower import LEDTower as _LEDTower
    return _LEDTower(resolve_pins(slot)[0])

def Servo(slot : str | tuple):
    from .modules.Servo import Servo
    return Servo(resolve_pins(slot)[0])

def Joystick(slot : str | tuple):
    from .modules.Joystick import Joystick as _Joystick
    return _Joystick(*resolve_pins(slot))

def Encoder(slot : str | tuple):
    from RotaryEncoder import RotaryEncoder
    return RotaryEncoder(*resolve_pins(slot))

def SoundSensor(slot : str | tuple):
    from .modules.SoundSensor import SoundSensor as _SoundSensor
    _SoundSensor(*resolve_pins(slot))

def WiFi():
    from .iot.WiFi import WiFi
    return WiFi()

def TelegramBot(token):
    from .iot.TelegramBot import TelegramBot as TGB
    return TGB(token)

# Button Likes
Switch = Button
TouchSensor = Button
MotionSensor = Button

# Analog Likes
LightSensor = ADC
Potentiometer = ADC

# Sensors
Climate = ClimateSensor
Color = ColorSensor
Distance = DistanceSensor
Touch = TouchSensor
Motion = MotionSensor
Light = LightSensor
Pot = Potentiometer
Sound = SoundSensor

#Other
GyroAxel = GyroAccel

def __getattr__(name):
    if name == "display":
        from .modules.Display import Display
        return Display()
