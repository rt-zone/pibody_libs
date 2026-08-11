from machine import ADC, Pin
import network
"""
    Readings from vsys through ADC3 is tricky. And it requires GPIO25 to be high, which is the Pin that is used by Wifi module. Turning it on will hand WiFi module. That's why before reading we have to disable (if active) wifi module, and restore Pin29 state. 
    Copied from: https://www.reddit.com/r/raspberrypipico/comments/xalach/measuring_vsys_on_pico_w/
"""
def get_vsys():
    conversion_factor = 3 * 3.3 / 65535
    wlan = network.WLAN(network.STA_IF)
    wlan_active = wlan.active()

    try:
        # Don't use the WLAN chip for a moment.
        wlan.active(False)

        # Make sure pin 25 is high.
        Pin(25, mode=Pin.OUT, pull=Pin.PULL_DOWN).high()
        
        # Reconfigure pin 29 as an input.
        Pin(29, Pin.IN)
        
        vsys = ADC(29)
        return vsys.read_u16() * conversion_factor

    finally:
        # Restore the pin state and possibly reactivate WLAN
        Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)
        wlan.active(wlan_active)