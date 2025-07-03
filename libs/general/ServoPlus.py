from machine import PWM, Pin

class ServoPlus:
    def __init__(self, pin: int, freq=50):
        self.servo = PWM(Pin(pin))

        self.freq = freq
        self.servo.freq(self.freq)
        self.angle = None

    def set_angle(self, angle):
        self.angle = angle
        proportion = angle / 180
        pulse_width = proportion * 2 + 0.5
        duty = int(pulse_width * 65535 / (1 / self.freq * 1000))
        self.servo.duty_u16(duty)

    def get_angle(self):
        return self.angle
