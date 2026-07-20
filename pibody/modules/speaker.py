import time
import math
import struct
import array
import gc
from machine import I2S, Pin

try:
    import _thread
    _HAS_THREAD = True
except ImportError:
    _HAS_THREAD = False

try:
    import mp3dec
    _HAS_MP3 = True
except ImportError:
    _HAS_MP3 = False

try:
    import vorbisdec
    _HAS_OGG = True
except ImportError:
    _HAS_OGG = False

try:
    from pibody.helper import get_pins_by_slot
except:
    from pibody.helper import resolve_pins as get_pins_by_slot

_HAS_VIPER = False
try:
    _viper_src = (
        "@micropython.viper\n"
        "def _viper_scale_volume(buf, n: int, vol_q15: int):\n"
        "    s = ptr16(buf)\n"
        "    i = 0\n"
        "    while i < n:\n"
        "        v = int(s[i])\n"
        "        if v >= 32768:\n"
        "            v -= 65536\n"
        "        val = (v * vol_q15) >> 15\n"
        "        if val > 32767:\n"
        "            val = 32767\n"
        "        elif val < -32768:\n"
        "            val = -32768\n"
        "        if val < 0:\n"
        "            val += 65536\n"
        "        s[i] = val\n"
        "        i += 1\n"
    )
    exec(_viper_src, globals())
    _HAS_VIPER = True
except Exception:
    _HAS_VIPER = False


def _fallback_scale_volume(buf, n, vol_q15):
    arr = array.array("h")
    arr.frombytes(buf[: n * 2])
    for i in range(n):
        val = (arr[i] * vol_q15) >> 15
        if val > 32767:
            val = 32767
        elif val < -32768:
            val = -32768
        arr[i] = val
    buf[: n * 2] = arr.tobytes()


class Speaker:
    def __init__(self, slot_sck_ws, slot_sd, i2s_id=1,
                sample_rate=44100, bits=16, format=I2S.MONO,
                ibuf=16000):
        """
        i2s_id      — hardware I2S block number (0 or 1 on ESP32)
        sck         — BCLK pin
        ws          — LRC (WS) pin
        sd          — DIN (data) pin
        sample_rate — sample rate
        bits        — bit depth (MAX98357A supports 16-bit)
        format      — I2S.STEREO or I2S.MONO
        ibuf        — internal DMA buffer size in bytes.
                    Increased by default to 16000 (previously 8000) —
                    a small ibuf leaves little time to "pick up the slack"
                    if the next data chunk is delayed
                    (e.g., due to slow SD card reading),
                    which also manifests as stuttering.
        """
        slot_1 = get_pins_by_slot(slot_sck_ws)
        slot_2 = get_pins_by_slot(slot_sd)


        self._id = i2s_id
        self._sck = slot_1[0]
        self._ws = slot_1[1]
        self._sd = slot_2[0]
        self._rate = sample_rate
        self._bits = bits
        self._format = format
        self._ibuf = ibuf
        self._volume = 1.0
        self._vol_q15 = 32768  # 1.0 in Q15 fixed-point (2**15)
        self._audio_out = None
        self._scratch = bytearray()
        self._open()
        
        
    def _open(self):
        self._audio_out = I2S(
            self._id,
            sck=Pin(self._sck),
            ws=Pin(self._ws),
            sd=Pin(self._sd),
            mode=I2S.TX,
            bits=self._bits,
            format=self._format,
            rate=self._rate,
            ibuf=self._ibuf,
        )

    def deinit(self):
        if self._audio_out:
            self._audio_out.deinit()
            self._audio_out = None

    def set_sample_rate(self, sample_rate):
        self.deinit()
        self._rate = sample_rate
        self._open()

    def get_sample_rate(self):
        return self._rate
    
    def set_format(self, format):
        self.deinit()
        self._format = format
        self._open()

    def set_volume(self, volume):
        if volume < 0.0:
            volume = 0.0
        if volume > 4.0:
            volume = 4.0
        self._volume = volume
        self._vol_q15 = int(round(volume * 32768))

    def get_volume(self):
        return self._volume

    def _apply_volume_inplace(self, buf, nbytes):
        if self._vol_q15 == 32768:
            return
        n = nbytes // 2
        if n <= 0:
            return
        if _HAS_VIPER:
            _viper_scale_volume(buf, n, self._vol_q15)
        else:
            _fallback_scale_volume(buf, n, self._vol_q15)

    def write(self, buf):
        if self._vol_q15 != 32768:
            if isinstance(buf, bytearray):
                self._apply_volume_inplace(buf, len(buf))
                data = buf
            elif isinstance(buf, memoryview):
                # memoryview поверх bytearray можно менять на месте
                self._apply_volume_inplace(buf, len(buf))
                data = buf
            else:
                # bytes — неизменяемый тип, нужна одна копия
                data = bytearray(buf)
                self._apply_volume_inplace(data, len(data))
        else:
            data = buf

        mv = memoryview(data)
        written = 0
        total = len(mv)
        while written < total:
            written += self._audio_out.write(mv[written:])

    def silence(self, ms):
        frames = int(self._rate * ms / 1000)
        channels = 2 if self._format == I2S.STEREO else 1
        chunk_frames = 256
        chunk = bytearray(chunk_frames * channels * 2)  # уже нули
        done = 0
        while done < frames:
            n = min(chunk_frames, frames - done)
            self._audio_out.write(chunk[: n * channels * 2])
            done += n

    def play_tone(self, freq_hz, duration_ms, amplitude=0.5):
        if amplitude < 0.0:
            amplitude = 0.0
        if amplitude > 1.0:
            amplitude = 1.0

        channels = 2 if self._format == I2S.STEREO else 1
        total_frames = int(self._rate * duration_ms / 1000)
        chunk_frames = 256
        amp = int(amplitude * 32767)
        phase = 0.0
        phase_inc = 2.0 * math.pi * freq_hz / self._rate

        buf = bytearray(chunk_frames * channels * 2)

        done = 0
        while done < total_frames:
            n = min(chunk_frames, total_frames - done)
            for i in range(n):
                s = int(math.sin(phase) * amp)
                if channels == 2:
                    struct.pack_into("<hh", buf, i * 4, s, s)
                else:
                    struct.pack_into("<h", buf, i * 2, s)
                phase += phase_inc
                if phase > 2.0 * math.pi:
                    phase -= 2.0 * math.pi
            chunk = buf[: n * channels * 2]
            self.write(chunk)
            done += n

    def _parse_wav_header(self, f):
        riff = f.read(12)
        if len(riff) < 12 or riff[0:4] != b"RIFF" or riff[8:12] != b"WAVE":
            raise ValueError("Not WAV-file (there no RIFF/WAVE header)")

        fmt = None
        data_size = None

        while True:
            chunk_hdr = f.read(8)
            if len(chunk_hdr) < 8:
                break
            chunk_id = chunk_hdr[0:4]
            chunk_size = struct.unpack("<I", chunk_hdr[4:8])[0]

            if chunk_id == b"fmt ":
                fmt_data = f.read(chunk_size)
                (audio_format, num_channels, sample_rate,
                 byte_rate, block_align, bits_per_sample) = struct.unpack(
                    "<HHIIHH", fmt_data[:16]
                )
                if audio_format != 1:
                    raise ValueError("Support only not compressed audio (PCM)")
                fmt = {
                    "num_channels": num_channels,
                    "sample_rate": sample_rate,
                    "bits_per_sample": bits_per_sample,
                }
            elif chunk_id == b"data":
                data_size = chunk_size
                break
            else:
                f.read(chunk_size)

        if fmt is None or data_size is None:
            raise ValueError("Некорректный WAV-файл (нет fmt/data чанка)")

        fmt["data_size"] = data_size
        return fmt

    def play_wav(self, path, chunk_size=16384):
        """
        Play a WAV file (PCM 16-bit, mono/stereo) from the file system
        (e.g., from flash or SD mounted via os.mount).
        """
        # Pre-allocated buffer + readinto() instead of f.read() — fewer
        # allocations in the loop means less frequent GC activity and a lower risk
        # of audio "stuttering" caused by a garbage collection pause.
        buf = bytearray(chunk_size)
        mv = memoryview(buf)

        gc.collect()

        with open(path, "rb") as f:
            info = self._parse_wav_header(f)

            if info["bits_per_sample"] != 16:
                raise ValueError("Support only 16 bit per sample")

            need_format = I2S.STEREO if info["num_channels"] == 2 else I2S.MONO
            if info["sample_rate"] != self._rate or need_format != self._format:
                self.deinit()
                self._rate = info["sample_rate"]
                self._format = need_format
                self._open()

            remaining = info["data_size"]
            while remaining > 0:
                to_read = min(chunk_size, remaining)
                n = f.readinto(mv[:to_read])
                if not n:
                    break
                self.write(mv[:n])
                remaining -= n

    def play_wav_buffered(self, path, chunk_size=16384, queue_depth=6):
        if not _HAS_THREAD:
            raise RuntimeError(
                "The _thread module is not available in this firmware — "
                "play_wav_buffered() requires threading support. "
                "Use play_wav() and increase ibuf/chunk_size."
            )

        gc.collect()

        with open(path, "rb") as f:
            info = self._parse_wav_header(f)

            if info["bits_per_sample"] != 16:
                raise ValueError("Support only 16 bit per sample")

            need_format = I2S.STEREO if info["num_channels"] == 2 else I2S.MONO
            if info["sample_rate"] != self._rate or need_format != self._format:
                self.deinit()
                self._rate = info["sample_rate"]
                self._format = need_format
                self._open()

            remaining = [info["data_size"]]
            queue = []
            lock = _thread.allocate_lock()
            done = [False]
            error = [None]

            def reader():
                try:
                    while True:
                        with lock:
                            rem = remaining[0]
                            qlen = len(queue)
                        if rem <= 0:
                            break
                        if qlen >= queue_depth:
                            time.sleep_ms(2)
                            continue
                        to_read = min(chunk_size, rem)
                        data = f.read(to_read)
                        if not data:
                            break
                        with lock:
                            queue.append(data)
                            remaining[0] -= len(data)
                except Exception as e:  # noqa: BLE001
                    error[0] = e
                finally:
                    done[0] = True

            _thread.start_new_thread(reader, ())

            while True:
                with lock:
                    chunk = queue.pop(0) if queue else None
                    finished = done[0] and not queue
                if chunk is not None:
                    self.write(chunk)
                elif finished:
                    break
                else:
                    time.sleep_ms(1)

            if error[0] is not None:
                raise error[0]

    def _play_compressed(self, path, decoder_module, has_decoder,
                        format_name, read_chunk=4096):
        if not has_decoder:
            raise RuntimeError(
                "{fmt} playback is not available: the MicroPython firmware "
                "lacks the native decoder module '{mod}'.\n"
                "Possible solutions:\n"
                "  1) build a custom MicroPython firmware with a built-in "
                "C decoder module for {fmt} (e.g., for MP3, based on "
                "https://github.com/lieff/minimp3);\n"
                "  2) convert the file to WAV beforehand, e.g.:\n"
                "     ffmpeg -i music.mp3 -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 44100 -ac 1 -acodec pcm_s16le output.wav\n"
                "     and play it using play_wav();\n"
                "  3) use an external hardware decoder (VS1053B, "
                "DFPlayer Mini, etc.) that performs the decoding itself, "
                "while the ESP32 simply controls it via SPI/UART.".format(
                    fmt=format_name,
                    mod="mp3dec" if format_name == "MP3" else "vorbisdec",
                    ext="mp3" if format_name == "MP3" else "ogg",
                )
            )

        dec = decoder_module.Decoder()
        cur_channels = None
        cur_rate = None
        pending = b""

        with open(path, "rb") as f:
            while True:
                chunk = f.read(read_chunk)
                eof = not chunk
                data_in = pending + chunk if chunk else pending

                if not data_in:
                    if eof:
                        break
                    continue

                pcm, channels, rate, consumed = dec.decode(data_in)

                pending = data_in[consumed:] if consumed < len(data_in) else b""

                if pcm:
                    need_format = I2S.STEREO if channels == 2 else I2S.MONO
                    if rate != self._rate or need_format != self._format:
                        self.deinit()
                        self._rate = rate
                        self._format = need_format
                        self._open()
                    self.write(pcm)

                if eof and not pending:
                    break

    def play_mp3(self, path, read_chunk=4096):
        self._play_compressed(path, mp3dec if _HAS_MP3 else None,
                                _HAS_MP3, "MP3", read_chunk)

    def play_ogg(self, path, read_chunk=4096):

        self._play_compressed(path, vorbisdec if _HAS_OGG else None,
                                _HAS_OGG, "OGG/Vorbis", read_chunk)