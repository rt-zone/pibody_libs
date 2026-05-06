from .rgb_tester import RGBTester
from .dimming_tester import DimmingTester
from .gyropong_tester import GyroPongTester
from .joystick_tester import JoystickTester
from .any_meter_tester import AnyMeterTester

projects = [
    GyroPongTester,
    DimmingTester,
    RGBTester,
    AnyMeterTester,
    JoystickTester,
]
project_index = 0
def get_next_project():
    global project_index
    current_project = projects[project_index]
    project_index += 1
    project_index %= len(projects)
    return current_project