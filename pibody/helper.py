from machine import I2C, SoftI2C, Pin

# Slot Name: (Main Pin, Secondary Pin)

_SLOT_MAP = {
    'A': ('A1', 'A2'),
    'B': ('B1', 'B2'),
    'C': ('C1', 'C2'),
    'D': ('D1', 'D2'),
    'E': ('E1', 'E2'),
    'F': ('F1', 'F2'),
    'G': ('G1', 'G2'),
    'H': ('H1', 'H2'),
}

_I2C_MAP = {
    'A': 0,
    'B': 1,
    'C': None,
    'D': 0,
    'E': 1,
    'F': 1,
    'G': 0,
    'H': 1,
}

def resolve_pins(slot):
    """
        Resolves slot (str), pin (int), or manual pins (tuple) into a tuple of pins.
        Returns: tuple of (pin_a, pin_b) or (pin_a,)
    """
    if isinstance(slot, int):
        return (slot, None)

    if isinstance(slot, tuple):
        return slot

    if isinstance(slot, str):
        if slot in _SLOT_MAP:
            return _SLOT_MAP[slot]
        else:
            return (slot, None) # In case if user tries to provide string value of Pin like "LED", "BUTTON_LEFT", "A1", etc.
        
    raise TypeError(f"Unsupported slot type: {type(slot).__name__}")

def get_pin(slot):
    return resolve_pins(slot)[0]

def get_i2c(slot, hard_i2c=False):
    if isinstance(slot, (I2C, SoftI2C)):
        return slot

    sda, scl = resolve_pins(slot)
    if hard_i2c:
        return I2C(id=_I2C_MAP[slot], scl=Pin(scl), sda=Pin(sda))
    else: 
        return SoftI2C(scl=Pin(scl), sda=Pin(sda))


