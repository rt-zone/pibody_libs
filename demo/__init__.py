from demo.Projects import get_next_project
from demo.drawer import Drawer
from machine import Pin
import gc 

start_button = Pin(20, Pin.IN) 
select_button = Pin(21, Pin.IN)

drawer = Drawer()

def start_project(project):
    drawer.tester_is_running(project.config.title)
    print("Starting project:", project.config.title)
    try:
        project.start()
        while not select_button():
            gc.collect()
            project.loop()
    except Exception as e:
        print("Error occurred: ", e)
        drawer.show_error(str(e))

def run():
    print("Demo started")
    
    drawer.draw_startup()
    while select_button.value() == 0 and start_button.value() == 0: pass
    current_project = get_next_project()
    drawer.draw_project(current_project.config)
    while select_button.value() or start_button.value(): pass

    while True:
        if select_button.value():
            current_project = get_next_project()
            drawer.draw_project(current_project.config)
            while select_button.value() == 1: pass

        if start_button.value():
            start_project(current_project)
                
            
if __name__ == "__main__":
    run()