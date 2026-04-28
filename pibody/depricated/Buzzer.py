from time import sleep

from Extensions.PWMExt import PWM

MODULE_NAME = "BUZZER"

class Buzzer(PWM):
    def __init__(self, pin, volume=0.5, freq=560):
        super().__init__(pin)
        self._volume = volume
        self.freq(freq)
        self._is_muted = False

    def volume(self, volume=None):
        if volume is None:
            return self._volume
        self._volume = max(0, min(1, volume))
        self._set_duty_by_volume(volume)

    def make_sound(self, freq, volume, duration):
        self.freq(freq)
        self._set_duty_by_volume(volume)
        sleep(duration)
        self.duty(0)

    def beep(self):
        self.make_sound(1000, self._volume, 0.1)
    
    def boop(self):
        self.make_sound(500, self._volume, 0.1)
        
    def on(self):
        self._is_muted = False
        self._set_duty_by_volume(self._volume)

    def off(self):
        self._is_muted = True
        self._set_duty_by_volume(0)

    def _set_duty_by_volume(self, volume):
        volume = max(0, volume)
        volume = min(1, volume)
        volume *= int(not self._is_muted)
        self.duty((volume ** 1.25) / 2)
        return volume
