from pibody import LED, Button, ADC, PWM, LEDTower, Buzzer, Servo
from pibody import Encoder, Joystick, SoundSensor
from pibody import Switch, TouchSensor, Motion, MotionSensor, LightSensor,Potentiometer, Touch, Motion, Light, Pot, Sound
read_modules = [
    Button, Encoder, Switch, TouchSensor, Motion, MotionSensor, Touch, Motion
]

adc_modules = [
    ADC, SoundSensor, LightSensor, Potentiometer, Light, Pot, Sound, Joystick,
]

write_modules = [LED, PWM, LEDTower, Buzzer, Servo]

slots = ["A", "B", "C", "D", "E", "F", "G", "H"]

def read_check(modules, slots, expected_types, verbose):
    for module in modules:
        for slot in slots:    
            m = module(slot)
            val = m.read() # Perform read function on every module, on every slot
            if verbose:
                print(module.__name__, slot, val)
            if type(val) not in expected_types:
                raise TypeError
    
def write_check(verbose):
    for slot in slots:
        led = LED(slot)
        led.on()
        led.off()
        led.toggle()
        led.value(0)
        led(1)
        led(0)
        if verbose:
            print("LED", slot)

    for slot in slots:
        pwm = PWM(slot)
        pwm.freq(100)
        pwm.duty(0.5)
        if verbose:
            print("PWM", slot)

    for slot in slots:
        led_tower = LEDTower(slot)
        led_tower.fill((10, 10, 10))
        led_tower[2] = (20, 0, 0)
        led_tower.write()
        led_tower((10, 0, 30))
        led_tower.write()
        if verbose:
            print("LED Tower", slot)
    
    for slot in slots:
        buz = Buzzer(slot)
        buz.beep()
        buz.boop()
        buz.make_sound(440, 1, 0.01)
        buz.volume()
        buz.volume(0.5)
        buz.off()
        buz.on()
        if verbose:
            print("Buzzer", slot)
    
    for pin in [8, 9, 12]:
        servo = Servo(pin)
        servo(90)
        servo.angle(180)
        servo.off()
    print("Write check is went successfully")


def run(verbose = False):
    read_check(read_modules, slots, [int], verbose)                
    read_check(adc_modules, ["C", "F"], [float, tuple], verbose)
    write_check(verbose)


    print("Pin test confirmed successfully")
    return 1