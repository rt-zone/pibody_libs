# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
import framebuf
import math

# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)



class SSD1306:
    def __init__(self, i2c, width=128, height=64, addr=0x3c):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        # Add an extra byte to the data buffer to hold an I2C data/command byte
        # to use hardware-compatible I2C transactions.  A memoryview of the
        # buffer is used to mask this byte from the framebuffer operations
        # (without a major memory hit as memoryview doesn't copy to a separate
        # buffer).
        self.buffer = bytearray(((height // 8) * width) + 1)
        self.buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
        self.framebuf = framebuf.FrameBuffer1(memoryview(self.buffer)[1:], width, height)
        self.width = width
        self.height = height
        self.pages = self.height // 8
        # Note the subclass must initialize self.framebuf to a framebuffer.
        # This is necessary because the underlying data buffer is different
        # between I2C and SPI implementations (I2C needs an extra byte).
        for cmd in (
            SET_DISP | 0x00, # off
            # address setting
            SET_MEM_ADDR, 0x00, # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01, # column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08, # scan from COM[N] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0xf1,
            SET_VCOM_DESEL, 0x30, # 0.83*Vcc
            # display
            SET_CONTRAST, 0xff, # maximum
            SET_ENTIRE_ON, # output follows RAM contents
            SET_NORM_INV, # not inverted
            # charge pump
            SET_CHARGE_PUMP, 0x14,
            SET_DISP | 0x01): # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def write_cmd(self, cmd):
        self.temp[0] = 0x80 # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_framebuf(self):
        # Blast out the frame buffer using a single I2C transaction to support
        # hardware I2C interfaces.
        self.i2c.writeto(self.addr, self.buffer)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)
    
    
    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))


    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_framebuf()

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1, big=False):
        if not big:
            self.framebuf.text(string, x, y, col)
        else:
            display(string, x, y, col, self)
    
    def line(self, x1, y1, x2, y2, c):
        self.framebuf.line(x1, y1, x2, y2, c)

    def ellipse(self, x, y, xr, yr, c, f=False, m=15):
        self.framebuf.ellipse(x, y, xr, yr, c, f,  m)

    def draw_ellipse(self, x0, y0, xrs, yrs, c, r=0, a=360):
        a = min(a, 360)
        for xr, yr in zip(range(xrs-r, xrs), range(yrs-r, yrs)):
            for angle in range(-90, a-90, 1):
                rad = math.radians(angle)
                x = int(x0 + xr * math.cos(rad))
                y = int(y0 + yr * math.sin(rad))
                self.pixel(x, y, c)



def A(oled, x, y, col):
    oled.line(x+1,y+15,x+5,y+1,col)
    oled.line(x+5,y+1,x+10,y+15,col)
    oled.line(x+3,y+11,x+8,y+11,col)
    
def B(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+6,y+1,col)
    oled.line(x+6,y+1,x+8,y+3,col)
    oled.line(x+8,y+3,x+8,y+4,col)
    oled.line(x+8,y+4,x+6,y+7,col)
    oled.line(x+5,y+7,x+1,y+7,col)
    oled.line(x+6,y+7,x+9,y+10,col)
    oled.line(x+9,y+10,x+9,y+12,col)
    oled.line(x+9,y+12,x+6,y+15,col)
    oled.line(x+6,y+15,x+1,y+15,col)     
    
def C(oled, x, y, col):
    oled.line(x+10,y+2,x+9,y+1,col)
    oled.line(x+9,y+1,x+4,y+1,col)
    oled.line(x+4,y+1,x+2,y+3,col)
    oled.line(x+2,y+3,x+1,y+7,col)
    oled.line(x+1,y+7,x+1,y+12,col)
    oled.line(x+1,y+12,x+4,y+15,col)
    oled.line(x+4,y+15,x+8,y+15,col)
    oled.line(x+8,y+15,x+10,y+13,col)
    
def D(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+6,y+1,col)
    oled.line(x+6,y+1,x+9,y+3,col)
    oled.line(x+9,y+3,x+9,y+12,col)
    oled.line(x+9,y+12,x+6,y+15,col)
    oled.line(x+6,y+15,x+1,y+15,col)
    
def E(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+9,y+1,col)
    oled.line(x+1,y+7,x+7,y+7,col)
    oled.line(x+1,y+15,x+9,y+15,col)
    
def F(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+9,y+1,col)
    oled.line(x+1,y+7,x+6,y+7,col)
    
def G(oled, x, y, col):
    oled.line(x+9,y+2,x+8,y+1,col)
    oled.line(x+8,y+1,x+4,y+1,col)
    oled.line(x+4,y+1,x+2,y+3,col)
    oled.line(x+2,y+3,x+1,y+7,col)
    oled.line(x+1,y+7,x+1,y+12,col)
    oled.line(x+1,y+12,x+4,y+15,col)
    oled.line(x+4,y+15,x+8,y+15,col)
    oled.line(x+8,y+15,x+10,y+13,col)
    oled.line(x+10,y+13,x+10,y+9,col)
    oled.line(x+10,y+9,x+6,y+9,col)    

def H(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+7,x+9,y+7,col)
    oled.line(x+9,y+15,x+9,y+1,col)

def I(oled, x, y, col):
    oled.line(x+1,y+1,x+9,y+1,col)
    oled.line(x+1,y+15,x+9,y+15,col)
    oled.line(x+5,y+15,x+5,y+1,col)

def J(oled, x, y, col):
    oled.line(x+9,y+1,x+9,y+10,col)
    oled.line(x+9,y+10,x+7,y+15,col)
    oled.line(x+7,y+15,x+3,y+15,col)
    oled.line(x+3,y+15,x+1,y+10,col)
    
def K(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+9,x+8,y+1,col)
    oled.line(x+4,y+7,x+9,y+15,col)

def L(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+15,x+9,y+15,col)
    
def M(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+5,y+7,col)
    oled.line(x+9,y+1,x+5,y+7,col)
    oled.line(x+9,y+15,x+9,y+1,col)

def N(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+9,y+15,col)
    oled.line(x+9,y+15,x+9,y+1,col)

def O(oled, x, y, col):
    oled.line(x+10,y+5,x+8,y+1,col)
    oled.line(x+8,y+1,x+4,y+1,col)
    oled.line(x+4,y+1,x+2,y+3,col)
    oled.line(x+2,y+3,x+1,y+7,col)
    oled.line(x+1,y+7,x+1,y+12,col)
    oled.line(x+1,y+12,x+4,y+15,col)
    oled.line(x+4,y+15,x+7,y+15,col)
    oled.line(x+7,y+15,x+10,y+12,col)
    oled.line(x+10,y+12,x+10,y+5,col)

def P(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+7,y+1,col)
    oled.line(x+7,y+1,x+9,y+4,col)
    oled.line(x+9,y+4,x+9,y+6,col)
    oled.line(x+9,y+6, x+6,y+9,col)
    oled.line(x+5,y+9,x+1,y+9,col)

def Q(oled, x, y, col):
    oled.line(x+10,y+5,x+8,y+1,col)
    oled.line(x+8,y+1,x+4,y+1,col)
    oled.line(x+4,y+1,x+2,y+3,col)
    oled.line(x+2,y+3,x+1,y+7,col)
    oled.line(x+1,y+7,x+1,y+12,col)
    oled.line(x+1,y+12,x+4,y+15,col)
    oled.line(x+4,y+15,x+7,y+15,col)
    oled.line(x+7,y+15,x+10,y+12,col)
    oled.line(x+10,y+12,x+10,y+5,col)
    oled.line(x+6,y+10,x+10,y+15,col)

def R(oled, x, y, col):
    oled.line(x+1,y+15,x+1,y+1,col)
    oled.line(x+1,y+1,x+7,y+1,col)
    oled.line(x+7,y+1,x+9,y+4,col)
    oled.line(x+9,y+4,x+9,y+6,col)
    oled.line(x+9,y+6, x+6,y+9,col)
    oled.line(x+5,y+9,x+1,y+9,col)
    oled.line(x+5,y+9,x+9,y+15,col)
    
def S(oled, x, y, col):
    oled.line(x+9,y+2,x+7,y+1,col)
    oled.line(x+7,y+1,x+3,y+1,col)
    oled.line(x+3,y+1,x+2,y+2,col)
    oled.line(x+3,y+1,x+2,y+2,col)    
    oled.line(x+2,y+2,x+1,y+5,col)
    oled.line(x+1,y+5,x+5,y+7,col)
    oled.line(x+5,y+7,x+9,y+8,col)
    oled.line(x+9,y+8,x+10,y+11,col)
    oled.line(x+10,y+11,x+10,y+13,col)
    oled.line(x+10,y+13,x+7,y+15,col)
    oled.line(x+7,y+15,x+4,y+15,col)
    oled.line(x+4,y+15,x+1,y+13,col)
    #oled.line((p.x)+10,(p.y)+13,(p.x)+7,(p.y)+15,col)

def T(oled, x, y, col):
    oled.line(x+5,y+15,x+5,y+1,col)
    oled.line(x+1,y+1,x+9,y+1,col)
    
def U(oled, x, y, col):
    oled.line(x+1,y+1,x+1,y+13,col)
    oled.line(x+1,y+13,x+3,y+15,col)
    oled.line(x+3,y+15,x+7,y+15,col)
    oled.line(x+7,y+15,x+9,y+13,col)
    oled.line(x+9,y+13,x+9,y+1,col)

def V(oled, x, y, col):
    oled.line(x+1,y+1,x+5,y+15,col)
    oled.line(x+5,y+15,x+9,y+1,col)

def W(oled, x, y, col):
    oled.line(x+1,y+1,x+3,y+15,col)
    oled.line(x+3,y+15,x+5,y+8,col)
    oled.line(x+5,y+8,x+8,y+15,col)
    oled.line(x+8,y+15,x+10,y+1,col)

def X(oled, x, y, col):
    oled.line(x+1,y+1,x+9,y+15,col)
    oled.line(x+9,y+1,x+1,y+15,col)

def Y(oled, x, y, col):
    oled.line(x+5,y+15,x+5,y+7,col)
    oled.line(x+5,y+7,x+1,y+1,col)
    oled.line(x+5,y+7,x+10,y+1,col)

def Z(oled, x, y, col):
    oled.line(x+1,y+1,x+9,y+1,col)
    oled.line(x+1,y+15,x+9,y+1,col)
    oled.line(x+1,y+15,x+9,y+15,col)

def period(oled, x, y, col):
    oled.line(x+1,y+14,x+2,y+14,col)
    oled.line(x+1,y+15,x+2,y+15,col)

def exclam(oled, x, y, col):
    oled.line(x+1,y+14,x+1,y+15,col)
    oled.line(x+1,y+1,x+1,y+10,col)

def plus(oled, x, y, col):
    oled.line(x+5,y+5,x+5,y+11,col)
    oled.line(x+2,y+8,x+8,y+8,col)
    
def minus(oled, x, y, col):
    oled.line(x+2,y+8,x+8,y+8,col)

def equal(oled, x, y, col):
    oled.line(x+2,y+6,x+8,y+6,col)
    oled.line(x+2,y+9,x+8,y+9,col)

def comma(oled, x, y, col):
    oled.line(x+1,y+13,x+1,y+14,col)
    oled.line(x+2,y+13,x+2,y+17,col)
    oled.line(x+1,y+17,x+2,y+17,col)

def colon(oled, x, y, col):
    oled.line(x+1,y+14,x+2,y+14,col)
    oled.line(x+1,y+15,x+2,y+15,col)
    oled.line(x+1,y+6,x+2,y+6,col)
    oled.line(x+1,y+5,x+2,y+5,col)

def slash(oled, x, y, col):
    oled.line(x+9,y+1,x+1,y+15,col)
    
def question(oled, x, y, col):
    oled.line(x+5,y+14,x+6,y+14,col)
    oled.line(x+5,y+15,x+6,y+15,col)
    oled.line(x+5,y+10,x+5,y+8,col)
    oled.line(x+5,y+8,x+8,y+6,col)
    oled.line(x+8,y+6,x+9,y+2,col)
    oled.line(x+8,y+1,x+4,y+1,col)

def amp(oled, x, y, col):
    #&
    oled.line(x+4,y+7,x+2,y+5,col)
    oled.line(x+2,y+5,x+2,y+3,col)
    oled.line(x+2,y+3,x+3,y+2,col)
    oled.line(x+3,y+2,x+4,y+1,col)
    oled.line(x+4,y+1,x+6,y+1,col)
    oled.line(x+6,y+1,x+7,y+2,col)
    oled.line(x+7,y+2,x+8,y+3,col)
    oled.line(x+8,y+3,x+8,y+4,col)
    oled.line(x+8,y+4,x+6,y+6,col)
    oled.line(x+6,y+6,x+1,y+10,col)
    oled.line(x+1,y+10,x+1,y+13,col)
    oled.line(x+1,y+13,x+3,y+15,col)
    oled.line(x+3,y+15,x+6,y+15,col)
    oled.line(x+6,y+15,x+9,y+9,col)
    oled.line(x+4,y+8,x+10,y+15,col)

def zero(oled, x, y, col):
    oled.line(x+10,y+5,x+8,y+1,col)
    oled.line(x+8,y+1,x+4,y+1,col)
    oled.line(x+4,y+1,x+2,y+3,col)
    oled.line(x+2,y+3,x+1,y+7,col)
    oled.line(x+1,y+7,x+1,y+12,col)
    oled.line(x+1,y+12,x+4,y+15,col)
    oled.line(x+4,y+15,x+7,y+15,col)
    oled.line(x+7,y+15,x+10,y+12,col)
    oled.line(x+10,y+12,x+10,y+5,col)
    oled.line(x+9,y+4,x+2,y+12,col)

def one(oled, x, y, col):
    oled.line(x+5,y+15,x+5,y+1,col)
    oled.line(x+5,y+1,x+2,y+3,col)

def two(oled, x, y, col):
    oled.line(x+1,y+3,x+2,y+1,col)
    oled.line(x+2,y+1,x+7,y+1,col)    
    oled.line(x+7,y+1,x+9,y+3,col)
    oled.line(x+9,y+3,x+9,y+6,col)
    oled.line(x+9,y+6,x+2,y+13,col)
    oled.line(x+2,y+13,x+1,y+15,col)
    oled.line(x+1,y+15,x+10,y+15,col) 

def three(oled, x, y, col):
    oled.line(x+1,y+3,x+2,y+1,col)
    oled.line(x+2,y+1,x+7,y+1,col)    
    oled.line(x+7,y+1,x+9,y+3,col)
    oled.line(x+9,y+3,x+9,y+5,col)
    oled.line(x+9,y+5,x+7,y+7,col)
    oled.line(x+7,y+7,x+4,y+7,col)    
    oled.line(x+7,y+8,x+9,y+9,col)
    oled.line(x+9,y+9,x+9,y+12,col)
    oled.line(x+9,y+12,x+7,y+15,col)
    oled.line(x+7,y+15,x+3,y+15,col)
    oled.line(x+3,y+15,x+1,y+13,col)    

def four(oled, x, y, col):
    oled.line(x+8,y+1,x+8,y+15,col)
    oled.line(x+1,y+1,x+1,y+7,col)
    oled.line(x+1,y+7,x+9,y+7,col)

def five(oled, x, y, col):
    oled.line(x+9,y+1,x+1,y+1,col)
    oled.line(x+1,y+1,x+1,y+7,col)
    oled.line(x+7,y+7,x+1,y+7,col)    
    oled.line(x+7,y+8,x+9,y+9,col)
    oled.line(x+9,y+9,x+9,y+12,col)
    oled.line(x+9,y+12,x+7,y+15,col)
    oled.line(x+7,y+15,x+3,y+15,col)
    oled.line(x+3,y+15,x+1,y+13,col)

def six(oled, x, y, col):
    oled.line(x+10,y+3,x+8,y+1,col)
    oled.line(x+8,y+1,x+4,y+1,col)
    oled.line(x+4,y+1,x+2,y+3,col)
    oled.line(x+2,y+3,x+1,y+7,col)
    oled.line(x+1,y+7,x+1,y+12,col)
    oled.line(x+1,y+12,x+4,y+15,col)
    oled.line(x+4,y+15,x+7,y+15,col)
    oled.line(x+7,y+15,x+10,y+13,col)
    oled.line(x+10,y+13,x+10,y+9,col)
    oled.line(x+10,y+9,x+8,y+7,col)
    oled.line(x+8,y+7,x+4,y+7,col)
    oled.line(x+4,y+7,x+2,y+9,col)

def seven(oled, x, y, col):
    oled.line(x+1,y+1,x+10,y+1,col)
    oled.line(x+10,y+1,x+3,y+15,col)
    
def eight(oled, x, y, col):
    oled.line(x+4,y+7,x+2,y+5,col)
    oled.line(x+2,y+5,x+2,y+3,col)
    oled.line(x+2,y+3,x+3,y+2,col)
    oled.line(x+3,y+2,x+4,y+1,col)
    oled.line(x+4,y+1,x+6,y+1,col)
    oled.line(x+6,y+1,x+7,y+2,col)
    oled.line(x+7,y+2,x+8,y+3,col)
    oled.line(x+8,y+3,x+8,y+5,col)
    oled.line(x+8,y+5,x+6,y+7,col)
    oled.line(x+1,y+10,x+1,y+13,col)
    oled.line(x+1,y+13,x+3,y+15,col)
    oled.line(x+3,y+15,x+7,y+15,col)
    oled.line(x+7,y+15,x+9,y+13,col)
    oled.line(x+9,y+13,x+9,y+10,col)
    oled.line(x+9,y+10,x+6,y+7,col)
    oled.line(x+6,y+7,x+4,y+7,col)
    oled.line(x+4,y+7,x+2,y+9,col)

def nine(oled, x, y, col):
    oled.line(x+10,y+6,x+8,y+8,col)
    oled.line(x+8,y+8,x+3,y+8,col)
    oled.line(x+3,y+8,x+1,y+5,col)
    oled.line(x+1,y+5,x+1,y+3,col)
    oled.line(x+1,y+3,x+3,y+1,col)
    oled.line(x+3,y+1,x+8,y+1,col)
    oled.line(x+8,y+1,x+10,y+3,col)
    oled.line(x+10,y+3,x+10,y+10,col)
    oled.line(x+10,y+10,x+9,y+13,col)
    oled.line(x+9,y+13,x+7,y+15,col)
    oled.line(x+7,y+15,x+3,y+15,col)
    oled.line(x+3,y+15,x+1,y+13,col)

def space(oled, x, y, col):
    pass

def display(text, x, y, col, oled):
    text = str(text)
    for i in range (len(text)):
        if text.upper()[i]=="A":
            A(oled, x + i*15, y, col)
        if text.upper()[i]=="B":
            B(oled, x + i*15, y, col)
        if text.upper()[i]=="C":
            C(oled, x + i*15, y, col)
        if text.upper()[i]=="D":
            D(oled, x + i*15, y, col)
        if text.upper()[i]=="E":
            E(oled, x + i*15, y, col)
        if text.upper()[i]=="F":
            F(oled, x + i*15, y, col)
        if text.upper()[i]=="G":
            G(oled, x + i*15, y, col)
        if text.upper()[i]=="H":
            H(oled, x + i*15, y, col)
        if text.upper()[i]=="I":
            I(oled, x + i*15, y, col)
        if text.upper()[i]=="J":
            J(oled, x + i*15, y, col)
        if text.upper()[i]=="K":
            K(oled, x + i*15, y, col)
        if text.upper()[i]=="L":
            L(oled, x + i*15, y, col)
        if text.upper()[i]=="M":
            M(oled, x + i*15, y, col)
        if text.upper()[i]=="N":
            N(oled, x + i*15, y, col)
        if text.upper()[i]=="O":
            O(oled, x + i*15, y, col)
        if text.upper()[i]=="P":
            P(oled, x + i*15, y, col)
        if text.upper()[i]=="Q":
            Q(oled, x + i*15, y, col)
        if text.upper()[i]=="R":
            R(oled, x + i*15, y, col)
        if text.upper()[i]=="S":
            S(oled, x + i*15, y, col)
        if text.upper()[i]=="T":
            T(oled, x + i*15, y, col)
        if text.upper()[i]=="U":
            U(oled, x + i*15, y, col)
        if text.upper()[i]=="V":
            V(oled, x + i*15, y, col)
        if text.upper()[i]=="W":
            W(oled, x + i*15, y, col)
        if text.upper()[i]=="X":
            X(oled, x + i*15, y, col)
        if text.upper()[i]=="Y":
            Y(oled, x + i*15, y, col)
        if text.upper()[i]=="Z":
            Z(oled, x + i*15, y, col)
        if text[i]=="0":
            zero(oled, x + i*15, y, col)
        if text[i]=="1":
            one(oled, x + i*15, y, col)
        if text[i]=="2":
            two(oled, x + i*15, y, col)
        if text[i]=="3":
            three(oled, x + i*15, y, col)
        if text[i]=="4":
            four(oled, x + i*15, y, col)
        if text[i]=="5":
            five(oled, x + i*15, y, col)
        if text[i]=="6":
            six(oled, x + i*15, y, col)
        if text[i]=="7":
            seven(oled, x + i*15, y, col)
        if text[i]=="8":
            eight(oled, x + i*15, y, col)
        if text[i]=="9":
            nine(oled, x + i*15, y, col)
        if text[i]==".":
            period(oled, x + i*15, y, col)
        if text[i]=="!":
            exclam(oled, x + i*15, y, col)
        if text[i]=="?":
            question(oled, x + i*15, y, col)
        if text[i]=="/":
            slash(oled, x + i*15, y, col)
        if text[i]==":":
            colon(oled, x + i*15, y, col)
        if text[i]==",":
            comma(oled, x + i*15, y, col)
        if text[i]=="&":
            amp(oled, x + i*15, y, col)
        if text[i]=="+":
            plus(oled, x + i*15, y, col)
        if text[i]=="-":
            minus(oled, x + i*15, y, col)
        if text[i]=="=":
            equal(oled, x + i*15, y, col)
        if text[i]==" ":
            space(oled, x + i*15, y, col)