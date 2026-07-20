
import time
import gc
import os
from machine import Pin, I2S


def _wav_header(rate, bits, nch, num_samples):
    """Assemble standart 44-byte WAV-header."""
    byte_rate   = rate * nch * bits // 8
    block_align = nch * bits // 8
    data_size   = num_samples * block_align

    header = bytearray(44)
    header[0:4]   = b'RIFF'
    header[4:8]   = (36 + data_size).to_bytes(4, 'little')
    header[8:12]  = b'WAVE'
    header[12:16] = b'fmt '
    header[16:20] = (16).to_bytes(4, 'little')
    header[20:22] = (1).to_bytes(2, 'little')   # PCM
    header[22:24] = nch.to_bytes(2, 'little')
    header[24:28] = rate.to_bytes(4, 'little')
    header[28:32] = byte_rate.to_bytes(4, 'little')
    header[32:34] = block_align.to_bytes(2, 'little')
    header[34:36] = bits.to_bytes(2, 'little')
    header[36:40] = b'data'
    header[40:44] = data_size.to_bytes(4, 'little')
    return header


class AudioRecorder:

    _IDLE   = 0
    _RECORD = 1
    _STOP   = 2

    def __init__(self, sck_pin, ws_pin, sd_pin, i2s_id = 0,
                bits=16, rate=16000, nch=1, ibuf=4096,
                max_duration_ms=5000,
                on_done=None, on_error=None,
                stop_watchdog_ms=500):
        """
        on_done(filepath)   - calls after saving WAV file.
        on_error(exception) - calls on erros.
        """
        self.rate = rate
        self.bits = bits
        self.nch = nch
        self.max_duration_ms = max_duration_ms
        self.on_done = on_done
        self.on_error = on_error
        self.stop_watchdog_ms = stop_watchdog_ms

        buf_size = ibuf // 2
        self._mic_samples = bytearray(buf_size)
        self._mic_samples_mv = memoryview(self._mic_samples)
        self._num_read = 0

        self._state = self._IDLE
        self._wav_file = None
        self._filepath = None
        self._bytes_written = 0
        self._started_at = 0
        self._stop_requested_at = 0
        self._done_pending = False

        self._i2s_id = i2s_id
        self.sck=Pin(sck_pin) 
        self.ws=Pin(ws_pin)
        self.sd=Pin(sd_pin)
        self.mode=I2S.RX
        self.bits=bits
        self.format=I2S.MONO
        self.rate=rate 
        self.ibuf=ibuf
    
        self._audio = None
        self._init_i2s()

    # ---------------------------------------------------------------- I2S --
    def _init_i2s(self):
        self._audio = I2S(
            self._i2s_id,
            sck = self.sck,
            ws = self.ws,
            sd = self.sd,
            mode = self.mode,
            bits = self.bits,
            format = self.format,
            rate = self.rate,
            ibuf = self.ibuf,
        )
        self._audio.irq(self._irq)

    def _reinit_i2s(self):
        try:
            self._audio.deinit()
        except Exception:
            pass
        self._init_i2s()

    def _irq(self, arg):
        if self._state == self._RECORD:
            if self._num_read > 0:
                try:
                    self._wav_file.write(self._mic_samples_mv[:self._num_read])
                    self._bytes_written += self._num_read
                except Exception as e:
                    if self.on_error:
                        self.on_error(e)
                    self._state = self._STOP
        elif self._state == self._STOP:
            self._state = self._IDLE
            self._done_pending = True

        try:
            self._num_read = self._audio.readinto(self._mic_samples_mv)
        except Exception as e:
            self._num_read = 0
            if self.on_error:
                self.on_error(e)

    # --- Public ---
    @property
    def is_recording(self):
        return self._state == self._RECORD or self._stop_requested_at != 0

    def start(self, filepath):
        """Start recording to filepath. Returns True/False."""
        if self.is_recording:
            return False
        try:
            f = open(filepath, "wb")
            f.seek(44)
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            return False

        self._filepath = filepath
        self._wav_file = f
        self._bytes_written = 0
        self._started_at = time.ticks_ms()
        self._stop_requested_at = 0
        self._state = self._RECORD
        try:
            self._num_read = self._audio.readinto(self._mic_samples_mv)
        except Exception as e:
            if self.on_error:
                self.on_error(e)
        return True

    def stop(self):
        '''Stop record'''
        if self._state != self._RECORD:
            return
        self._state = self._STOP
        self._stop_requested_at = time.ticks_ms()

    def tick(self):
        """Calls in every loop cycle"""
        now = time.ticks_ms()

        if self._state == self._RECORD and self.max_duration_ms:
            if time.ticks_diff(now, self._started_at) >= self.max_duration_ms:
                self.stop()

        if self._stop_requested_at and self._state == self._STOP:
            if time.ticks_diff(now, self._stop_requested_at) > self.stop_watchdog_ms:
                self._state = self._IDLE
                self._done_pending = True

        if self._done_pending:
            self._done_pending = False
            self._stop_requested_at = 0
            self._finalize()

    # --- Private ---
    def _finalize(self):
        path = self._filepath
        n = self._bytes_written
        f = self._wav_file
        self._wav_file = None
        self._filepath = None

        if n <= 0:
            try:
                f.close()
            except Exception:
                pass
            try:
                os.remove(path)
            except Exception:
                pass
            self._reinit_i2s()
            return

        try:
            block_align = self.nch * self.bits // 8
            num_samples = n // block_align
            header = _wav_header(self.rate, self.bits, self.nch, num_samples)
            f.seek(0)
            f.write(header)
            f.close()
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            try:
                f.close()
            except Exception:
                pass
            self._reinit_i2s()
            return

        gc.collect()
        self._reinit_i2s()
        if self.on_done:
            self.on_done(path)


def next_indexed_path(directory, prefix="rec_", ext=".wav", pad=4):
    try:
        existing = os.listdir(directory)
    except OSError:
        os.mkdir(directory)
        existing = []

    idx_len = pad
    indices = []
    for name in existing:
        if name.startswith(prefix) and name.endswith(ext):
            middle = name[len(prefix):len(prefix) + idx_len]
            if middle.isdigit():
                indices.append(int(middle))
    n = (max(indices) + 1) if indices else 0
    return "{}/{}{:0{width}d}{}".format(directory, prefix, n, ext, width=pad)