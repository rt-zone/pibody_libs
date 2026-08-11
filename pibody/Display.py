from DisplayBase import DisplayBase #Firmware site display. Contains only minimal code.  
import math

# TODO: Make a UI class
class Display(DisplayBase):
    """This class expands functionality of built-in Display class by providing methods for UI elements"""
    def __init__(self):
        super().__init__()
        self._current_line = 0
        self._vssa = 0

    def linear_bar(self, 
            x, y, 
            value, min_value, max_value, 
            length=100, height=5, border=False, 
            color=DisplayBase.GREEN, 
            border_color=DisplayBase.WHITE, 
            background_color=DisplayBase.BLACK):
        
        even = 1 - height % 2
        half_height = height // 2
        
        value = max(min_value, min(max_value, value))
        ratio = (value - min_value) / (max_value - min_value)
        fill_length = int(length * ratio)

        self.fill_rect(x, y-half_height, fill_length, height, color) # Filler

        if border:
            self.rect(x-1, y-half_height - 1 , length+2, height+2, border_color) # Border
            self.fill_rect(x + fill_length, y-half_height, length - fill_length, height, background_color) # UnFiller
        else:
            self.fill_rect(x-2, y-half_height, 2, height, border_color) # Border Left
            self.fill_rect(x+length, y-half_height, 2, height, border_color) #Border Right
            
            self.fill_rect(x + fill_length, y-half_height, length - fill_length, half_height - even, background_color) # Unfiller TOP
            self.fill_rect(x + fill_length, y + 1, length - fill_length, half_height - even, background_color) # Unfiller BOTTOM

            self.fill_rect(x + fill_length, y - 1 + height % 2, length - fill_length, 1 + even , border_color) # Central Line

    def arc(self, center_x, center_y, r, color=DisplayBase.WHITE, width=1, start_angle=0, end_angle=360):
        r2 = r + width
        for r in range(r, r2):
            for i in range(start_angle, end_angle):
                dx = center_x + r * math.cos(math.pi/180*i)
                dy = center_y + r * math.sin(math.pi/180*i)
                super().pixel(round(dx), round(dy), color)

    def circular_bar(self, center_x, center_y, r, value, min_value, max_value, width=2, color=DisplayBase.GREEN, background_color=DisplayBase.WHITE):
        # Get angle from value
        value = max(min_value, min(max_value, value))
        ratio = (value - min_value) / (max_value - min_value)
        angle = ratio * 360

        # Draw progress bar
        self.arc(center_x, center_y, r, background_color, width=width, start_angle=int(angle)-90, end_angle=270)
        self.arc(center_x, center_y, r, color, width=width, start_angle=-90, end_angle=int(angle)-90)

        
    crosshair_last_x = 0
    crosshair_last_y = 0
    
    def crosshair(self, 
                  x, y, r, 
                  x_center, y_center, crosshair_radius, 
                  color=DisplayBase.RED, border_color=DisplayBase.WHITE, background_color=DisplayBase.BLACK):
        """
            Renders a ball at the center of crosshair. 
            x, y cords are relative. and ranged from -1 to 1, where 0 is the middle of the crosshair
        """
        self.circle(x_center, y_center, crosshair_radius, border_color)

        x_cord = round(x * crosshair_radius) + x_center
        y_cord = round(y * crosshair_radius) + y_center

        if x_cord == self.crosshair_last_x and y_cord == self.crosshair_last_y:
            return
        
        self.fill_circle(self.crosshair_last_x, self.crosshair_last_y, r, background_color)
        self.fill_circle(x_cord, y_cord, r, color)

        self.crosshair_last_x = x_cord
        self.crosshair_last_y = y_cord



    def draw_polygon(self, center_x, center_y, r, n, bump=1.0, angle_offset=None, color=DisplayBase.WHITE, fill=False):
        buf = []
        angle = 0
        angle_step = 360 / n
        if angle_offset is None:
            angle_offset = angle_step / 2 if n % 2 == 0 else 90
        for i in range(n + 1):
            dx = center_x + r * math.cos(math.pi/180*(angle-angle_offset))
            dy = center_y + r * math.sin(math.pi/180*(angle-angle_offset))
            angle += angle_step
            ddx = center_x + r * math.cos(math.pi/180*(angle-angle_offset))
            ddy = center_y + r * math.sin(math.pi/180*(angle-angle_offset))

            mid_x = dx + (ddx - dx) / 2
            mid_y = dy + (ddy - dy) / 2

            bdx = center_x + (mid_x - center_x) * bump
            bdy = center_y + (mid_y - center_y) * bump

            buf.append((round(dx), round(dy)))
            buf.append((round(bdx), round(bdy)))

        if fill:
            self.fill_polygon(buf, 0, 0, color)
        else:
            self.polygon(buf, 0, 0, color)

    def logo(self, x=120, y=100, r=80):
        super().fill(DisplayBase.WHITE)
        self.draw_polygon(x, y, r, 8, bump=0.7, fill=True, color=DisplayBase.BLACK)
        self.draw_polygon(x, y, r * 0.7, 4, bump=0.3, fill=True, color=DisplayBase.WHITE, angle_offset=0)
        self.text("Artisan", x - r, y + r, font=DisplayBase.font_bold, fg=DisplayBase.BLACK, bg=DisplayBase.WHITE)
        self.text("Education", x - r, y + r + 32, font=DisplayBase.font_bold, fg=DisplayBase.BLACK, bg=DisplayBase.WHITE)
        self.text("artisan.education", 100, 300, fg=DisplayBase.BLACK, bg=DisplayBase.WHITE)


    # TODO: Add font support.Fix Text appearing at the top bug. Add word wrapping support.
    def print(self, *args, font=DisplayBase.font_medium, color=DisplayBase.WHITE):
        max_chars = self.width // font.WIDTH
        msg = (">> " + " ".join(str(a) for a in args))
        
        line = ""
        for char in msg:
            if char == '\n' or len(line) >= max_chars:
                self._print_line(line, font, color)
                line = "" if char == '\n' else char
            else:
                line += char
            
        if line:
            self._print_line(line, font, color)

    
    def _print_line(self, msg, font, color):
        max_lines = self.height // font.HEIGHT
        line_height = font.HEIGHT
        if self._vssa - line_height < 0:
            self._vssa = 320
        self._vssa = (self._vssa - line_height) % self.height
        self.vscsad(self._vssa)

        y = (self._current_line * line_height) % self.height
        self.fill_rect(0, y, 240, line_height, 0)  
        self.text(msg, 0, y, font=font, fg=color)
        

        self._current_line += 1
        if self._current_line >= max_lines:
            self._current_line = 0

    def clear(self):
        super().clear()
        # Clear console and reset hardware scroll
        self._current_line = 0
        self._vssa = 0
        self.vscsad(self._vssa)
