_SLOT_MAP = {
    'A': (0, 0, 1),
    'B': (1, 2, 3),
    'D': (0, 4, 5),
    'C': (None, 28, 22),
    'E': (1, 6, 7),
    'F': (1, 26, 27),
    'G': (0, 16, 17),
    'H': (1, 18, 19),
}

_ADC_SLOT_MAP = {
    'C': (None, 28, 22),
    'F': (1, 26, 27)
}

# Functions-helpers
def get_pins_by_slot(slot:str, adc=False, joystick=False):
    slot = slot.upper()[0]
    if joystick and (slot != 'F'):
        raise ValueError(f"Joystick is not supported for slot '{slot}'. Recomendation: Use slot 'F' instead.")
    elif adc and (slot not in _ADC_SLOT_MAP):
        raise ValueError(f"Invalid slot '{slot}'. Use C or F (Other slots are not ADC-compatible)")
    elif slot not in _SLOT_MAP:
        raise ValueError(f"Invalid slot '{slot}'. Use A, B, C, D, E, or F (C is not I2C-compatible)")
    bus, sda, scl = _SLOT_MAP[slot]
    return (bus, sda, scl)

