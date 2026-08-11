from pibody import display
from .helper import ProjectConfig
import gc
import time

SLOTS_COORDS = {
    "A": (10, 0),
    "B": (10, 90),
    "C": (10, 180),
    "D": (150, 0),
    "E": (150, 90),
    "F": (150, 180)
}

PNG_PATH = const("demo/module_pngs/")


def safe_draw_png(path, x, y, retries=10, delay=0.1):
    for attempt in range(retries):
        try:
            gc.collect()  # clean memory before each try
            display.png(path, x, y)
            return True  # success
        except MemoryError:
            print("MemoryError — retrying ({}/{})...".format(attempt + 1, retries))
            gc.collect()
            time.sleep(delay)
    print("Failed to draw PNG after {} retries.".format(retries))
    return False

    
class Drawer():
    def __init__(self):
        display.clear()

    def draw_startup(self):
        display.logo(y=90)
        display.fill_rect(100, 300, 140, 20, display.WHITE)
        arrow_polygon_nodes = [(10, 285) ,(10, 310), (35, 310), (27, 302), (43, 286), (34, 277), (18, 293), (10, 285)]
            
        display.fill_polygon(arrow_polygon_nodes, 0, 0, display.BLACK)
        display.fill_polygon(arrow_polygon_nodes, -80, 320, display.BLACK,4.71238898038)

        display.text("start", 10, 261, fg=display.BLACK, bg=display.WHITE)
        display.text("next", 198, 261, fg=display.BLACK, bg=display.WHITE)

        display.text("Press any button", 56, 290, fg=display.BLACK, bg=display.WHITE)
        display.hline(55, 306, 129, display.BLACK)


    def tester_is_running(self, name):
        display.clear()
        text_color = display.color(120, 255, 50)  # Green color
        # display.text(f"{name}", 10, 120, display.font_bold, text_color, display.BLACK)
        display.text(name, 10, 265, display.font_bold, text_color, display.BLACK)
        display.text("is running", 10, 295, display.font_medium, text_color, display.BLACK)
        
        display.text("GP21", 204, 300, display.font_small, fg=display.CYAN)
        display.text("cancel", 154, 300, display.font_small)


    def _draw_module(self, name, slot):
        x, y = SLOTS_COORDS[slot]
        png_path = f"{PNG_PATH}{name}.png"
        safe_draw_png(png_path, x, y)

    def _draw_servo(self, servo8, servo9):
        if not(servo8 or servo9):
            return
        display.png(f"{PNG_PATH}servo.png", 90, 200)
        txt = "8" if servo8 else ""
        txt += "/" if servo8 and servo9 else ""
        txt += "9" if servo9 else ""
        display.text(font=display.font_small, text=txt, x=110, y=250, fg=display.WHITE, bg=display.BLACK)

    def _draw_controls_text(self):
        display.text("GP20", 10, 300, display.font_small, fg=display.CYAN)
        display.text("start", 44, 300, display.font_small)
        display.text("GP21", 204, 300, display.font_small, fg=display.CYAN)
        display.text("next", 170, 300, display.font_small)

    def draw_project(self, config: ProjectConfig):
        display.clear()  # Clear the screen
        
        for name, slot in config.modules.items():
            self._draw_module(name, slot)
        
        if config.led_tower:
            display.png(f"{PNG_PATH}led_tower.png", 110, 0)
        self._draw_servo(config.servo8, config.servo9)
        display.text(config.title, 10, 265, display.font_bold, display.WHITE, display.BLACK)
        self._draw_controls_text()

    def show_error(self, message):
        display.clear()
        text_color = display.color(220, 100, 20)
        
        lines = [message[i:i+28] for i in range(0, len(message), 28)]
        for i, line in enumerate(lines):
            display.text(font=display.font_small, text=line, x=10, y=20 + i * 20, fg=text_color, bg=display.BLACK)
        self._draw_controls_text()
