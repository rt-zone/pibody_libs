from utime import sleep_ms

# Registers
_CONF = b'\x00'
_ENABLE = b'\xFE'
_REG_RED = 0x08
_REG_GREEN = 0x09
_REG_BLUE = 0x0A
_REG_WHITE = 0x0B

_DEFAULT_SETTINGS = b'\x00' # initialise gain:1x, integration 40ms, Green Sensitivity 0.25168, Max. Detectable Lux 16496
                            # No Trig, Auto mode, enabled.
_SHUTDOWN = b'\x01'         # Disable colour sensor
_INTEGRATION_TIME = 40      # ms
_G_SENSITIVITY = 0.25168    # lux/step

_NaN=float('NaN')

def rgb2hsv(r, g, b):
    r = float(r/65535)
    g = float(g/65535)
    b = float(b/65535)
    high = max(r, g, b)
    low = min(r, g, b)
    h,s,v = high,high,high
    d = high - low
    s = 0 if high == 0 else d/high
    if high == low:
        h = 0.0
    else:
        h = {
            r: (g - b) / d+(6 if g < b else 0),
            g: (b - r) / d+2,
            b: (r - g) / d+4,
        }[high]
        h /= 6
    return (h*360, s, v)

def hsv2rgb(h, s, v):
    """
    Convert HSV to RGB.
    h: Hue in degrees [0, 360)
    s: Saturation [0, 1]
    v: Value [0, 1]
    Returns:
    (r, g, b): Each in [0, 1]
    """
    c = v * s
    h_prime = h / 60
    x = c * (1 - abs(h_prime % 2 - 1))
    m = v - c

    if 0 <= h_prime < 1:
        r1, g1, b1 = c, x, 0
    elif 1 <= h_prime < 2:
        r1, g1, b1 = x, c, 0
    elif 2 <= h_prime < 3:
        r1, g1, b1 = 0, c, x
    elif 3 <= h_prime < 4:
        r1, g1, b1 = 0, x, c
    elif 4 <= h_prime < 5:
        r1, g1, b1 = x, 0, c
    elif 5 <= h_prime < 6:
        r1, g1, b1 = c, 0, x
    else:
        r1, g1, b1 = 0, 0, 0  # if h is out of range

    r, g, b = r1 + m, g1 + m, b1 + m
    return (r, g, b)


class VEML6040(object):
    def __init__(self, i2c, address=0x10, freq=400000):
        self.i2c = i2c
        self.address = address
        self.freq = freq

        try:
            self.i2c.writeto(self.address, _CONF + _SHUTDOWN)
            self.i2c.writeto(self.address, _CONF + _DEFAULT_SETTINGS)
            sleep_ms(100)
        except Exception as e:
            raise RuntimeError("Failed to initialize ColorSensor. Check wiring and connection.") from e
    
    # Read colours from VEML6040
    # Returns raw red, green and blue readings, ambient light [Lux] and colour temperature [K]
    def readRawData(self):
        raw_data = self.i2c.readfrom_mem(self.address, _REG_RED, 2)        # returns a bytes object   
        u16red = int.from_bytes(raw_data, 'little')
        
        raw_data = (self.i2c.readfrom_mem(self.address, _REG_GREEN, 2))    # returns a bytes object
        u16grn = int.from_bytes(raw_data, 'little')
        
        raw_data = (self.i2c.readfrom_mem(self.address, _REG_BLUE, 2))     # returns a bytes object
        u16blu = int.from_bytes(raw_data, 'little')
        
        raw_data = (self.i2c.readfrom_mem(self.address, _REG_WHITE, 2))    # returns a bytes object
        data_white_int = int.from_bytes(raw_data, 'little')
        
        # Generate the XYZ matrix based on https://www.vishay.com/docs/84331/designingveml6040.pdf
        colour_X = (-0.023249*u16red)+(0.291014*u16grn)+(-0.364880*u16blu)
        colour_Y = (-0.042799*u16red)+(0.272148*u16grn)+(-0.279591*u16blu)
        colour_Z = (-0.155901*u16red)+(0.251534*u16grn)+(-0.076240*u16blu)
        colour_total = colour_X+colour_Y+colour_Z
        if colour_total == 0:
            return {"red":0,"green":0,"blue":0,"white":0,"als":0,"cct":0}
        else:
            colour_x = colour_X / colour_total
            colour_y = colour_Y / colour_total
        
        # Use McCamy formula
        colour_n = (colour_x - 0.3320)/(0.1858 - colour_y)
        colour_CCT = 449.0*colour_n ** 3+3525.0*colour_n ** 2+6823.3*colour_n+5520.33
        
        # Calculate ambient light in Lux
        colour_ALS = u16grn*_G_SENSITIVITY
        return {"red":u16red,"green":u16grn,"blue":u16blu,"white":data_white_int,"als":colour_ALS,"cct":colour_CCT}
    
    def readHSV(self):
        r, g, b = self.readRGB()
        h, s, v = rgb2hsv(r, g, b)
        return (h, s, v)

    def readRGB(self):
        rgb = self.readRawData()
        raw_r = round(rgb['red']   / 65535 * 255)
        raw_g = round(rgb['green'] / 65535 * 255)
        raw_b = round(rgb['blue']  / 65535 * 255)

        m11, m12, m13 = 11.2575 , -7.4708 , 0.2273
        m21, m22, m23 = -0.4733 , 3.9696  , -1.9689
        m31, m32, m33 = 1.4107  , -1.8697 , 4.5144

        r = m11*raw_r + m12*raw_g + m13*raw_b
        g = m21*raw_r + m22*raw_g + m23*raw_b
        b = m31*raw_r + m32*raw_g + m33*raw_b

        r = max(0, min(round(r), 255))
        g = max(0, min(round(g), 255))
        b = max(0, min(round(b), 255))

        return (r, g, b)

    def read(self):
        r, g, b = self.readRGB()
        h, s, v = self.readHSV()
        return {'red': r, 'green': g, 'blue':b, 'hue': h, 'sat':s, 'val':v}

    # Detects the color out of list.
    def detectColor(self, hues={"red":0,"yellow":60,"green":120,"light-blue":180,"blue":240,"magenta":300}, min_brightness=0.0009):
        h, s, v = self.readHSV()
        if v > min_brightness:
            key, val = min(hues.items(), key=lambda x: min(360-abs(h - x[1]),abs(h - x[1]))) # nearest neighbour, but it wraps!
            return key
        else:
            return 'None'

     # Measures ambient light in Lux
    def lux(self):
        raw_data = self.i2c.readfrom_mem(self.address, _REG_GREEN, 2)
        green = int.from_bytes(raw_data, 'little')
        return round(green * _G_SENSITIVITY, 2)
