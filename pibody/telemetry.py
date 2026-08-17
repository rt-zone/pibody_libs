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

    # Rounded before the comparison, or an analog reading would count as changed on every poll:
    # a resting potentiometer wobbles in the last digits and would flood the channel at full rate.
    if isinstance(value, float):
        value = round(value, 3)

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
    # A driver that answers True/False would otherwise reach the wire as "True", which the host
    # reads as not-a-number and drops the whole frame.
    if value is True:
        value = 1
    elif value is False:
        value = 0
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
# Wrapping happens per object, never per class — see `_hook` for why that is not a preference but
# a hard requirement. It also keeps modules that share a class from sharing wrappers: `LED` and
# `Button` are both a `Pin`, and each instance now carries only what its own kind reports.

_READ = 'read'        # method -> channel; reports what it returned
_SCALED = 'scaled'    # method -> (channel, divisor); the raw *_u16 twins of a read
_WRITE = 'write'      # method -> constant, or (channel, constant) when it is not the object's own
_ARG = 'arg'          # method -> channel; reports the argument it was given
_SCALED_ARG = 'sarg'  # method -> (channel, divisor); the raw *_u16 twin of an argument
_AFTER = 'after'      # method -> (channel, getter); reports the state left behind

_SPECS = {
    # Lamp and button share PinExt.Pin, so both get the whole surface of it — `value` in either
    # direction, `on`/`off`/`high`/`low`, `toggle`, `read`. A method the firmware does not have is
    # skipped rather than fatal, so listing `high`/`low` costs nothing where they are absent.
    'LED': {
        'channel': 'on',
        _WRITE: {'on': 1, 'off': 0, 'high': 1, 'low': 0},
        _ARG: {'value': None},
        _AFTER: {'toggle': (None, 'value')},
        _READ: {'read': None},
    },
    'Button': {'channel': 'state', _READ: {'read': None, 'value': None}},
    # `read()` is `read_u16() / 65535`; scaling the raw twin keeps one number on the chart whichever
    # of the two a lesson calls.
    'ADC': {'channel': 'value', _READ: {'read': None}, _SCALED: {'read_u16': (None, 65535)}},
    'DistanceSensor': {'channel': 'distance', _READ: {'read': None}},
    'ClimateSensor': {_READ: {'read_temperature': 'temperature', 'read_humidity': 'humidity', 'read_pressure': 'pressure'}},
    # Every other colour path — `read`, `readHSV`, `detectColor` — goes through `readRGB`.
    'ColorSensor': {_READ: {'readRGB': ('r', 'g', 'b'), 'lux': 'lux'}},
    # `read()` returns both axes by calling these two.
    'Joystick': {_READ: {'read_x': 'x', 'read_y': 'y'}},
    # `read()` is an alias for `value()`; `set_value`/`reset` move the count without any read at all,
    # so they report it themselves or the chart would lag behind the program.
    'Encoder': {'channel': 'position', _READ: {'value': None}, _ARG: {'set_value': None}, _WRITE: {'reset': 0}},
    # Both drivers expose accel and gyro and both return a triple; MPU6050.read() calls them,
    # LSM6DS3.read_accel() goes the other way round. Temperature is MPU6050's alone and the step
    # counter is the LSM6DS3's — each is skipped on the driver that lacks it.
    'GyroAccel': {
        _READ: {
            'read_accel': ('ax', 'ay', 'az'),
            'read_gyro': ('gx', 'gy', 'gz'),
            'read_temperature': 'temperature',
            'get_step_count': 'steps',
        }
    },
    # Outputs whose value is the argument, not the return: a servo told to go to 90° answers
    # nothing. `Servo.__call__` routes through `angle`, so one hook covers both.
    'Servo': {'channel': 'angle', _ARG: {'angle': None}, _WRITE: {'on': ('on', 1), 'off': ('on', 0)}},
    # `duty` takes 0..1 and `duty_u16` the raw 16 bits; both land on the same channel in the same
    # units. `freq` matters for a buzzer and is dropped for a lamp, which declares no such channel.
    'PWM': {'channel': 'brightness', _ARG: {'duty': None, 'freq': 'freq'}, _SCALED_ARG: {'duty_u16': (None, 65535)}},
    # `beep`, `boop` and `__call__` all route through `make_sound`, whose first argument is the
    # frequency. `on`/`off` are mute and unmute — a different quantity, hence the explicit channel.
    'Buzzer': {
        'channel': 'freq',
        _ARG: {'make_sound': None, 'freq': None, 'volume': 'volume'},
        _WRITE: {'on': ('on', 1), 'off': ('on', 0)},
    },
    # The tower is driven through `__call__(color)`, which calls the inherited native `fill`.
    # Both are hooked: `__call__` on the class, because special methods are looked up there, and
    # `fill` on the instance for a lesson that calls it directly.
    'LEDTower': {_ARG: {'__call__': ('r', 'g', 'b'), 'fill': ('r', 'g', 'b')}},
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


def _emit_many(obj, channels, values):
    try:
        for i in range(len(channels)):
            _emit(obj, channels[i], values[i])
    except Exception:
        pass


def _reader(obj, call, channel):
    def method(*args, **kwargs):
        result = call(*args, **kwargs)
        if isinstance(channel, tuple):
            _emit_many(obj, channel, result)
        elif result is not None:
            _emit(obj, channel, result)
        return result

    return method


def _scaled(obj, call, spec):
    channel, divisor = spec

    def method(*args, **kwargs):
        result = call(*args, **kwargs)
        if result is not None:
            _emit(obj, channel, result / divisor)
        return result

    return method


def _writer(obj, call, spec):
    # A bare constant reports on the object's own channel; a pair names a different one, which is
    # how a buzzer's mute lands on `on` while its readings stay on `freq`.
    channel, const = spec if isinstance(spec, tuple) else (None, spec)

    def method(*args, **kwargs):
        result = call(*args, **kwargs)
        _emit(obj, channel, const)
        return result

    return method


def _argument(obj, call, channel):
    def method(*args, **kwargs):
        result = call(*args, **kwargs)
        if args:
            if isinstance(channel, tuple):
                _emit_many(obj, channel, args[0])
            else:
                _emit(obj, channel, args[0])
        return result

    return method


def _scaled_argument(obj, call, spec):
    channel, divisor = spec

    def method(*args, **kwargs):
        result = call(*args, **kwargs)
        if args:
            _emit(obj, channel, args[0] / divisor)
        return result

    return method


def _after(obj, call, spec):
    def method(*args, **kwargs):
        result = call(*args, **kwargs)
        # `toggle()` returns nothing and takes nothing; the interesting value is where the pin
        # ended up, so it is read back. No recursion: the getter is the `_ARG` wrapper, which
        # stays silent when called without an argument.
        try:
            _emit(obj, spec[0], getattr(obj, spec[1])())
        except Exception:
            pass
        return result

    return method


def _hook(obj, name, make, arg):
    """Wrap one method of one object.

    On the instance, never on the class. A class-level wrapper has to call the method it replaced,
    and reaching that method through `getattr(cls, name)` returns it unbound — which for anything
    inherited from a native type (`Pin.on` and `Pin.off` come from `machine.Pin`) is not callable
    with a subclass instance. MicroPython answers that with a hard crash; on the board it silently
    misfired instead, and a second LED simply never lit. `getattr(obj, name)` hands back a method
    already bound to this object, and an instance attribute shadows the class for every later call.
    """
    call = getattr(obj, name, None)
    if call is None:
        return
    try:
        setattr(obj, name, make(obj, call, arg))
    except Exception:
        pass


def _hook_call(obj, channel):
    """`__call__` is the exception: special methods are looked up on the type, so the instance
    cannot shadow them. Only the LED tower needs it, and its `__call__` is defined in Python
    (NeoPixelExt), so replacing it on the class and calling the original with an explicit self is
    safe here in a way it never is for an inherited native."""
    cls = type(obj)
    if (cls, '__call__') in _patched:
        return
    original = getattr(cls, '__call__', None)
    if original is None:
        return
    _patched[(cls, '__call__')] = True

    def method(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if args:
            _emit_many(self, channel, args[0])
        return result

    try:
        setattr(cls, '__call__', method)
    except Exception:
        del _patched[(cls, '__call__')]


def _instrument(obj, spec):
    for name in spec.get(_READ, {}):
        _hook(obj, name, _reader, spec[_READ][name])
    for name in spec.get(_SCALED, {}):
        _hook(obj, name, _scaled, spec[_SCALED][name])
    for name in spec.get(_WRITE, {}):
        _hook(obj, name, _writer, spec[_WRITE][name])
    for name in spec.get(_SCALED_ARG, {}):
        _hook(obj, name, _scaled_argument, spec[_SCALED_ARG][name])
    for name in spec.get(_AFTER, {}):
        _hook(obj, name, _after, spec[_AFTER][name])
    for name in spec.get(_ARG, {}):
        if name == '__call__':
            _hook_call(obj, spec[_ARG][name])
        else:
            _hook(obj, name, _argument, spec[_ARG][name])


def _factory(original, spec):
    def build(slot, *args, **kwargs):
        obj = original(slot, *args, **kwargs)
        try:
            obj._tm_slot = slot
            obj._tm_channel = spec.get('channel')
            _instrument(obj, spec)
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
