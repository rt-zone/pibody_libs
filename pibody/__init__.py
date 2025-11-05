from .wrappers.generic import LED, ButtonLike, ADC
from .wrappers.i2c import ClimateSensor, ColorSensor, DistanceSensor, GyroAccel, OLED
from .wrappers.modules import Buzzer, PWM, Joystick, Encoder, SoundSensor, LEDTower
from .modules.Servo import Servo

from .iot.WiFi import WiFi
from .iot.telegram_bot import TelegramBot

from .Display import display
from .Demo import demo


# Demo

# Aliases 

# Button Likes
Button = ButtonLike
Switch = ButtonLike
TouchSensor = ButtonLike
MotionSensor = ButtonLike

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

