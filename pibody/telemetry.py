"""Telemetry: what the program reads and writes, framed into stdout for the Artisan IDE chart.

The board has one channel back to the browser — the serial stdout the terminal shows — so samples
travel inside it, marked with \\x1e so the IDE can cut them back out before printing the rest.
\\x1e and not \\x01/\\x04: those two belong to the raw-REPL protocol and would be eaten in transit.

Off unless the IDE turns it on, and then it costs nothing while off: `start()` is what installs the
instrumentation and `stop()` removes it again, so a board running its own main.py executes not one
extra instruction. The IDE enables it by running, before the student's program:

    from pibody.telemetry import start
    start(hz=50)

Nothing else in the library knows telemetry exists: the public API here is module-level factory
functions, and `start()` swaps them for wrappers that tag the object they hand back and patch its
class once. That is also why this file is the whole feature — there is no edit anywhere else.

Wire format (mirrored in artisan-platform/src/v2/entities/telemetry/lib/telemetryFrames.ts):

    \\x1eH|<protocol>|<hz>          run start, resets the time base
    \\x1eT|<t_ms>|<slot>|<ch>|<v>   one reading, t counted from start()
    \\x1eD|<t_ms>|<count>           readings dropped to keep up
"""

import time

PROTOCOL = 1
_SEP = '\x1e'

_enabled = False
_t0 = 0
_interval_ms = 20
_last_value = {}
_last_sent = {}
_dropped = 0
_originals = {}
_patched = {}


def start(hz=50):
    """Begin a telemetry run. Called by the IDE before the student's program, never by a lesson."""
    global _enabled, _t0, _interval_ms, _last_value, _last_sent, _dropped
    _enabled = True
    _t0 = time.ticks_ms()
    # Integer division and no `max`: some builds ship neither floats nor the extra builtins.
    _interval_ms = 1000 // hz if hz else 20
    if _interval_ms < 1:
        _interval_ms = 1
    _last_value = {}
    _last_sent = {}
    _dropped = 0
    _install()
    print(_SEP + 'H|' + str(PROTOCOL) + '|' + str(hz))


def stop():
    global _enabled
    _enabled = False
    _restore()


def enabled():
    return _enabled


def sample(slot, channel, value):
    """Record one reading.

    Only changes are sent, and no faster than the configured rate. A `while` loop polling a button
    would otherwise flood the USB buffer, and once that buffer is full `print` blocks — which would
    stretch the very reaction time the lesson is there to measure.
    """
    global _dropped
    if not _enabled or slot is None:
        return

    key = (slot, channel)
    if _last_value.get(key) == value:
        return

    now = time.ticks_ms()
    previous = _last_sent.get(key)
    if previous is not None and time.ticks_diff(now, previous) < _interval_ms:
        _dropped += 1
        return

    _last_value[key] = value
    _last_sent[key] = now
    print(_SEP + 'T|' + str(time.ticks_diff(now, _t0)) + '|' + str(slot) + '|' + channel + '|' + str(value))


def flush_dropped():
    """Report what was thrown away. A thinned-out chart must not pass for a complete one."""
    global _dropped
    if _enabled and _dropped:
        print(_SEP + 'D|' + str(time.ticks_diff(time.ticks_ms(), _t0)) + '|' + str(_dropped))
        _dropped = 0


# --- instrumentation --------------------------------------------------------------------------
#
# What travels is the *channel* — the quantity — and never the module type, because the board
# cannot know it: nothing on a plain GPIO or ADC pin identifies itself, and the names are aliases
# of one another anyway (`LightSensor` and `Potentiometer` are both `ADC`, `Switch` is `Button`).
# The chart names a series by its slot, which is knowable, and spells the quantity out only when a
# slot reports more than one.
#
# 'read' methods report what they returned; 'write' methods report the constant in the table. A
# channel of None means "the channel this object was built for", which is what keeps LED and Button
# apart even though the factories hand back the very same class.
#
# Never wrap a method that the library itself calls from another method. `Pin.value` is the case
# that taught this: it is the natural place to catch `led.value(1)`, but `Pin.read` — the button's
# only method — is implemented as `return self.value()`, and Pin is the very same class for both.
# Wrapping it put the button's every read through a wrapper written for writing, and over USB the
# button stopped responding at all. `led.value(1)` therefore goes unrecorded; `on()` and `off()`
# cover what lessons actually use, and a silent gap is worth incomparably less than a dead button.

_READ = 'read'
_WRITE = 'write'
_ARG = 'arg'

_SPECS = {
    'LED': {'channel': 'on', _WRITE: {'on': 1, 'off': 0}},
    'Button': {'channel': 'state', _READ: {'read': None}},
    'ADC': {'channel': 'value', _READ: {'read': None}},
    'DistanceSensor': {'channel': 'distance', _READ: {'read': None}},
    'ClimateSensor': {_READ: {'read_temperature': 'temperature', 'read_humidity': 'humidity', 'read_pressure': 'pressure'}},
    'ColorSensor': {_READ: {'readRGB': ('r', 'g', 'b')}},
    'Joystick': {_READ: {'read_x': 'x', 'read_y': 'y'}},
    # RotaryEncoder.read() is an alias for value(), so value() is the one that catches both. Safe to
    # wrap here where Pin.value was not: this one is a plain Python method, not a native inherited.
    'Encoder': {'channel': 'position', _READ: {'value': None}},
    # Both drivers expose these two and both return a triple; MPU6050.read() calls them internally,
    # LSM6DS3.read_accel() goes the other way round — wrapping the pair covers either.
    'GyroAccel': {_READ: {'read_accel': ('ax', 'ay', 'az'), 'read_gyro': ('gx', 'gy', 'gz')}},
    # Outputs whose value is the argument, not the return: a servo told to go to 90° answers
    # nothing. `Servo.__call__` and `Buzzer.beep`/`boop`/`__call__` all route through the wrapped
    # method, so one hook each covers every way a lesson drives them.
    'Servo': {'channel': 'angle', _ARG: {'angle': None}},
    # PWMExt.duty takes 0..1 and calls the native duty_u16 underneath, so the hook goes on duty.
    # freq is left alone: a lesson sets it once, and it is an inherited native — the combination
    # that killed the button.
    'PWM': {'channel': 'brightness', _ARG: {'duty': None}},
    'Buzzer': {'channel': 'freq', _ARG: {'make_sound': None}},
    # The tower is driven only through `__call__(color)`, which then calls the native `fill` — so
    # `__call__` is the one to wrap; `fill` is inherited, and wrapping inherited natives is what
    # once killed the button.
    'LEDTower': {_ARG: {'__call__': ('r', 'g', 'b')}},
    'SoundSensor': {_READ: {'read_analog': 'value', 'read_digital': 'state'}},
}

# Every public name that resolves to one of the specs above. They are separate module attributes
# bound at import time, so each has to be swapped in its own right.
_ALIASES = (
    ('LED', 'LED'),
    ('Button', 'Button'),
    ('Switch', 'Button'),
    ('TouchSensor', 'Button'),
    ('MotionSensor', 'Button'),
    ('Touch', 'Button'),
    ('Motion', 'Button'),
    ('ADC', 'ADC'),
    ('LightSensor', 'ADC'),
    ('Potentiometer', 'ADC'),
    ('Light', 'ADC'),
    ('Pot', 'ADC'),
    ('DistanceSensor', 'DistanceSensor'),
    ('Distance', 'DistanceSensor'),
    ('ClimateSensor', 'ClimateSensor'),
    ('Climate', 'ClimateSensor'),
    ('ColorSensor', 'ColorSensor'),
    ('Color', 'ColorSensor'),
    ('Joystick', 'Joystick'),
    ('Encoder', 'Encoder'),
    ('GyroAccel', 'GyroAccel'),
    ('GyroAxel', 'GyroAccel'),
    ('Servo', 'Servo'),
    ('PWM', 'PWM'),
    ('Buzzer', 'Buzzer'),
    ('LEDTower', 'LEDTower'),
    ('SoundSensor', 'SoundSensor'),
    ('Sound', 'SoundSensor'),
)


def _emit(obj, channel, value):
    # Telemetry must never cost a student their lesson, so a fault here is swallowed rather than
    # raised through code the student wrote.
    try:
        sample(getattr(obj, '_tm_slot', None), channel or getattr(obj, '_tm_channel', None), value)
    except Exception:
        pass


def _reader(original, channel):
    def method(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if isinstance(channel, tuple):
            for i in range(len(channel)):
                _emit(self, channel[i], result[i])
        elif result is not None:
            _emit(self, channel, result)
        return result

    return method


def _argument(original, channel):
    def method(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if args:
            try:
                if isinstance(channel, tuple):
                    for i in range(len(channel)):
                        _emit(self, channel[i], args[0][i])
                else:
                    _emit(self, channel, args[0])
            except Exception:
                pass
        return result

    return method


def _writer(original, const):
    def method(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        _emit(self, None, const)
        return result

    return method


def _patch_class(cls, spec):
    """Wrap the methods of the class an instance came from — once per method, however many objects.

    Marked per (class, method) rather than per class, because different factories hand back the
    same class: `LED` and `Button` are both a Pin, and marking the class done after the first of
    them would leave the other's methods bare.

    A method the class does not have is skipped rather than fatal: drivers differ between kit
    revisions, and one missing `read_*` must not cost the module its other channels.
    """
    for kind, wrap in ((_READ, _reader), (_WRITE, _writer), (_ARG, _argument)):
        for name in spec.get(kind, {}):
            if (cls, name) in _patched:
                continue
            original = getattr(cls, name, None)
            if original is None:
                continue
            _patched[(cls, name)] = True
            setattr(cls, name, wrap(original, spec[kind][name]))


def _factory(original, spec):
    def build(slot, *args, **kwargs):
        obj = original(slot, *args, **kwargs)
        try:
            obj._tm_slot = slot
            obj._tm_channel = spec.get('channel')
            _patch_class(type(obj), spec)
        except Exception:
            pass
        return obj

    return build


def _install():
    import pibody

    for name, key in _ALIASES:
        original = getattr(pibody, name, None)
        if original is None or name in _originals:
            continue
        _originals[name] = original
        setattr(pibody, name, _factory(original, _SPECS[key]))


def report():
    """Print what the instrumentation managed to install. Diagnostic only — safe to call anywhere."""
    print('telemetry enabled:', _enabled)
    print('factories wrapped:', list(_originals))
    print('methods wrapped:', [name for (_cls, name) in _patched])


def _restore():
    import pibody

    for name in _originals:
        setattr(pibody, name, _originals[name])
    _originals.clear()
    # The classes stay wrapped: their methods check `_enabled` through `sample`, so they go quiet
    # by themselves, and unwrapping them would have to undo patches other objects still hold.
