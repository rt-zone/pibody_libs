from machine import Pin

class Button(Pin):
    def __init__(self, pin):
        super().__init__(pin, Pin.IN)

    def read(self):
        """Returns value of sensor: 0 or 1"""
        return self.value()
