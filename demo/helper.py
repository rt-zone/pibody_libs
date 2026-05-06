class ProjectConfig():
    def __init__(self, title, modules: dict[str, str], led_tower=False, servo8=False, servo9=False):
        self.title = title
        self.modules = modules
        self.led_tower = led_tower
        self.servo8 = servo8
        self.servo9 = servo9

class Module:
    """Enum for all available modules."""
    BUTTON_BLUE = "button_blue"
    BUTTON_YELLOW = "button_yellow"
    BUZZER = "buzzer"
    LED_G = "led_green"
    LED_R = "led_red"
    LED_Y = "led_yellow"
    MOTION_SENSOR = "motion_sensor"
    POTENTIOMETER = "potentiometer"
    SWITCH = "switch"
    TOUCH_SENSOR = "touch_sensor"
    LIGHT_SENSOR = "light_sensor"
    CLIMATE_SENSOR = "climate_sensor"
    COLOR_SENSOR = "color_sensor"
    DISTANCE_SENSOR = "distance_sensor"
    ENCODER = "encoder"
    GYRO_ACCEL = "gyro_accel"
    JOYSTICK = "joystick"
    SOUND_SENSOR = "sound_sensor"

 