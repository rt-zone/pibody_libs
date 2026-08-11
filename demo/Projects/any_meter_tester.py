from demo.helper import ProjectConfig, Module
from pibody import ClimateSensor, ColorSensor, DistanceSensor, Sound, Touch, LEDTower, display

modules={
    Module.CLIMATE_SENSOR: 'A',
    Module.COLOR_SENSOR: 'B',
    Module.SOUND_SENSOR: 'C',
    Module.DISTANCE_SENSOR: 'E'
}

def get_color_gradient(value, min_value, max_value, min_color, max_color):
    if value > max_value:
        return max_color
    if value < min_value:
        return min_color
    ratio = (value - min_value) / (max_value - min_value)
    
    color = list(min_color)
    for i in range(3):
        diff = int((max_color[i] - min_color[i]) * ratio)
        color[i] += diff
    
    return display.color(*color)
    
class AnyMeterTester:
    config = ProjectConfig(
        title="Any Meter",
        modules=modules)

    def __init__(self):
        pass
        
    def start(self):
        self.sound_sensor = Sound(modules[Module.SOUND_SENSOR])
        self.distance_sensor = DistanceSensor(modules[Module.DISTANCE_SENSOR])
        self.climate_sensor = ClimateSensor(modules[Module.CLIMATE_SENSOR])
        self.color_sensor = ColorSensor(modules[Module.COLOR_SENSOR])
    
    def bar(self, line, title, value, min_value, max_value, color, gradient_max_color=None, comment=None):
        value = max(min(value, max_value), min_value)
        x, y = 10, 10 + line * 60 
        display.text(title, x, y)
        if gradient_max_color:
            color = get_color_gradient(value, min_value, max_value, color, gradient_max_color)
        display.linear_bar(x, y+22, value=value, min_value=min_value, max_value=max_value, length=200, height=12, border=True, color=color)
        if comment:
            display.text(comment, x, y+31)

        
    max_deviation = 0
    def loop(self):
        temp = self.climate_sensor.read_temperature()
        temp_min, temp_max = 20, 30
        self.bar(0,"Climate Sensor", temp, temp_min, temp_max, (255,255,0),(255,0,0), f"Temperature: {temp} C")
        

        distance = self.distance_sensor.read()
        min_dist, max_dist = 50, 300
        self.bar(1,"Distance Sensor", distance, min_dist, max_dist, (255,0,0), (0,255,0),f"Distance: {distance}/{max_dist} mm")


        mic_value = self.sound_sensor.read_analog()
        mic_value = abs(mic_value - 0.5) * 2
        self.bar(2, "Sound Sensor", mic_value, 0, 1, display.YELLOW,comment=f"Loudness: {mic_value:.3f}/1")

        r, g, b = self.color_sensor.readRGB()
        self.bar(3, "Color Sensor", 1, 0, 1, display.color(r,g,b))


  
if __name__ == "__main__":
    project = AnyMeterTester()
    project.start()
    while True:
        project.loop()