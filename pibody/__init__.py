from pibody.helper import resolve_pins, get_i2c, get_pin
from pibody import helper
# This Libs correspond to the firmware PiBody v1.1, on Micropython v1.28.0. Other version might be incompatible. Check your REPL banner to make sure that versions are the same
# 3 Pin
def LED(slot):
    from PinExt import Pin
    pin = helper.get_pin(slot)
    return Pin(pin, Pin.OUT)
    
def Button(slot):
    from PinExt import Pin
    pin = helper.get_pin(slot)
    return Pin(pin, Pin.IN)
        
def ADC(slot):
    from ADCExt import ADC
    pin = helper.get_pin(slot)
    return ADC(pin)

def PWM(slot):
    from PWMExt import PWM
    pin = helper.get_pin(slot)
    return PWM(pin)

def LEDTower(slot):
    from NeoPixelExt import NeoPixel
    pin = helper.get_pin(slot)
    return NeoPixel(pin)

def Buzzer(slot):
    from Generic.Buzzer import Buzzer as _Buzzer
    pin = helper.get_pin(slot)
    return _Buzzer(pin)

def Servo(pin : int):
    from Generic.Servo import Servo
    return Servo(pin)

# I2C
def GyroAccel(slot, hard_i2c=False):
    i2c = get_i2c(slot, hard_i2c)
    i2c_address = i2c.scan()
    if 0x68 in i2c_address:
        from I2C.MPU6050 import MPU6050
        return MPU6050(i2c)
    if 0x6A in i2c_address:
        from I2C.LSM6DS3 import LSM6DS3
        return LSM6DS3(i2c)
    
    raise ValueError(f"Invalid i2c address '{i2c.scan()}' for slot '{slot}'")  

def ClimateSensor(slot, hard_i2c=False):
    from I2C.BME280 import BME280
    return BME280(get_i2c(slot, hard_i2c))
    

def ColorSensor(slot, hard_i2c=False):
    from I2C.VEML6040 import VEML6040
    return VEML6040(get_i2c(slot, hard_i2c))

def DistanceSensor(slot, hard_i2c=False):
    from I2C.VL53L0X import VL53L0X
    return VL53L0X(get_i2c(slot, hard_i2c))

def OLED(slot, hard_i2c=False):
    from I2C.SSD1306 import SSD1306
    return SSD1306(get_i2c(slot, hard_i2c), width=128, height=64)

# 4 Pin
def Encoder(slot : str | tuple):
    from RotaryEncoder import RotaryEncoder
    return RotaryEncoder(*resolve_pins(slot))

def Joystick(slot : str | tuple):
    from Generic.Joystick import Joystick as _Joystick
    return _Joystick(*resolve_pins(slot))

def SoundSensor(slot : str | tuple):
    from Generic.SoundSensor import SoundSensor as _SoundSensor
    return _SoundSensor(*resolve_pins(slot))

# IOT
def WiFi():
    from .IOT.WiFi import WiFi
    return WiFi()

def TelegramBot(token):
    from .IOT.TelegramBot import TelegramBot as TGB
    return TGB(token)

def SDCard(*args):
        from .modules.sdcard import SDCard
        return SDCard(*args)

def Microphone(*args):
        from .modules.microphone import Microphone as _Microphone
        return _Microphone(*args)
# Display
def __getattr__(name):
    if name == "display":
        from .Display import Display as _Display
        return _Display()
    
    if name == "WebUi":
        from .IOT.WebUi import WebUi as _WebUi
        return _WebUi
    
    if name == "SpeechRecognizer":
        from .modules.stt import SpeechRecognizer
        return SpeechRecognizer
    if name == "LLMClient":
        from .modules.llm_client import LLMClient
        return LLMClient
    if name == "sdcard":
        from .modules.sdcard import SDCard
        import os
        sd = SDCard()
        os.mount(sd, "/sd")
        return sd
    if name == "Speaker":
        from .modules.speaker import Speaker
        return Speaker
    if name == "SpeechSynthesizer":
        from .modules.tts import SpeechSynthesizer
        return SpeechSynthesizer
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Aliases
# Button
Switch          = Button
TouchSensor     = Button
MotionSensor    = Button

# ADC
LightSensor     = ADC
Potentiometer   = ADC

# Sensors
Climate         = ClimateSensor
Color           = ColorSensor
Distance        = DistanceSensor
Sound           = SoundSensor
Touch           = TouchSensor
Motion          = MotionSensor
Light           = LightSensor
Pot             = Potentiometer

#Legacy support
GyroAxel        = GyroAccel

try:
    _ = 1 / 0
except ZeroDivisionError:
    FAKE_IMPORT = False

if FAKE_IMPORT:
    from .IOT.WebUi import WebUi

    from modules.microphone import Microphone
    from modules.stt import SpeechRecognizer
    from modules.llm_client import LLMClient
    from modules.sdcard import SDCard
    from modules.sdcard import SDCard as sdcard
    from modules.speaker import Speaker
    from modules.tts import SpeechSynthesizer