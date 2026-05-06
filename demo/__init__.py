from .Projects import get_next_project
from .drawer import Drawer
from machine import Pin
import gc 

start_button = Pin(20, Pin.IN) 
select_button = Pin(21, Pin.IN)


hinter = Drawer()
current_project = get_next_project()
project_index = 0

is_running = False
def start_project(project):
    global is_running
    is_running = True
    print("Starting project:", project.config.title)
    try:
        while is_running:
            gc.collect()
            project.loop()
    except Exception as e:
        print("Error occurred: ", e)
        hinter.show_error(str(e))

def cancel_handler(pin):
    global is_running
    if not is_running:
        return
    is_running = False
    print("Test cancelled")
    pin.irq(handler=None)  # Disable the cancel handler


def run():
    global current_project
    print("Demo started")
    hinter.draw_startup()

    while select_button.value() == 0 and start_button.value() == 0: pass
    hinter.draw_project(current_project.config)
    
    while True:
        if select_button.value():
            current_project = get_next_project()
            hinter.draw_project(current_project.config)
            while select_button.value() == 1: pass

            
        if start_button.value():
            project = current_project()
            hinter.tester_is_running(project.config.title)
            select_button.irq(trigger=Pin.IRQ_RISING, handler=cancel_handler) 
            start_project(project)
                
            
