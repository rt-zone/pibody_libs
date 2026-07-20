import time

from .audio_recorder import AudioRecorder, next_indexed_path

from pibody.helper import get_pin
try:
    from pibody.helper import get_pins_by_slot
except:
    from pibody.helper import resolve_pins as get_pins_by_slot


class Microphone:
    def __init__(self, slot_sck_ws, slot_sd, i2s_id=0,
                rate=16000, bits=16, nch=1, ibuf=4096,
                max_duration_ms=5000,
                directory="/sd/recordings",
                filename_prefix="rec_",
                on_done=None, on_error=None):

        sck_pin, ws_pin = get_pins_by_slot(slot_sck_ws)
        sd_pin = get_pin(slot_sd)

        self.directory = directory
        self.filename_prefix = filename_prefix

        self._user_on_done = on_done
        self._last_path = None
        self._current_path = None
        self._blocking_done = False

        self._recorder = AudioRecorder(
            i2s_id=i2s_id,
            sck_pin=sck_pin, ws_pin=ws_pin, sd_pin=sd_pin,
            rate=rate, bits=bits, nch=nch, ibuf=ibuf,
            max_duration_ms=max_duration_ms,
            on_done=self._on_done,
            on_error=on_error,
        )

    def _on_done(self, path):
        self._last_path = path
        self._current_path = None
        self._blocking_done = True
        if self._user_on_done:
            self._user_on_done(path)

    def _make_path(self, filepath):
        if filepath is not None:
            return filepath
        return next_indexed_path(self.directory, prefix=self.filename_prefix)

    def start(self, filepath=None, max_duration_ms=None):
        if self._recorder.is_recording:
            return self._current_path

        path = self._make_path(filepath)
    
        self._recorder.max_duration_ms = max_duration_ms or 0

        ok = self._recorder.start(path)
        if not ok:
            return None

        self._current_path = path
        self._blocking_done = False
        return path

    def get_current_path(self):
        return self._current_path

    def get_last_path(self):
        return self._last_path
    
    def is_record(self):
        self._recorder.tick()
        return self._recorder.is_recording

    def stop(self, wait=True, timeout_ms=2000):
        self._recorder.stop()

        if not wait:
            self._recorder.tick()
            return

        start = time.ticks_ms()
        while self._recorder.is_recording:
            self._recorder.tick()
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                break
            time.sleep_ms(5)

    def record(self, seconds, filepath=None):
        path = self._make_path(filepath)

        old_max = self._recorder.max_duration_ms
        self._recorder.max_duration_ms = int(seconds * 1000)

        self._blocking_done = False
        self._last_path = None

        ok = self._recorder.start(path)
        if not ok:
            self._recorder.max_duration_ms = old_max
            return None

        while not self._blocking_done:
            self._recorder.tick()
            time.sleep_ms(5)

        self._recorder.max_duration_ms = old_max
        return self._last_path