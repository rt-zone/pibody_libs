from libs.wrappers.generic import LED, ButtonLike, ADC
from libs.wrappers.i2c import ClimateSensor, ColorSensor, DistanceSensor, GyroAccel, OLED
from libs.wrappers.modules import Buzzer, PWM, Joystick, Encoder, SoundSensor, LEDTower
from libs.modules.Servo import Servo

from libs.Display import Display

from libs.iot.WiFi import WiFi
from libs.iot.telegram_bot import TelegramBot

display = Display()

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

