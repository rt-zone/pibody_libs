import os
import socket
import ssl
import struct
import ujson


class SpeechSynthesizerError(Exception):
    """Unsolvable problem"""
    pass


def _urlencode_component(s):
    """Minimal URL encoding for UTF-8 text (space -> '+')."""
    out = []
    for b in s.encode("utf-8"):
        if (48 <= b <= 57) or (65 <= b <= 90) or (97 <= b <= 122) or b in (45, 95, 46, 126):
            out.append(chr(b))
        elif b == 32:
            out.append("+")
        else:
            out.append("%{:02X}".format(b))
    return "".join(out)


class SpeechSynthesizer:
    def __init__(self, api_key: str, host="mangisoz.nu.edu.kz",
                path="/backend/api/v1/tts/audio/stream", port=443,
                lang="kk", speaker="male", chunk_chars=60,
                sample_rate=22050,
                retries=3, chunk_size=1024, socket_timeout=20,
                retry_on_network_error=True):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.host = host
        self.path = path
        self.port = port
        self.lang = lang
        self.speaker = speaker
        self.chunk_chars = chunk_chars
        self.sample_rate = sample_rate  # для WAV-заголовка и справки
        self.retries = max(1, retries)
        self.chunk_size = chunk_size
        self.socket_timeout = socket_timeout
        self.retry_on_network_error = retry_on_network_error

    # ---------------- Публичные методы ----------------

    def synthesize_to_i2s(self, text, amp, chunk_size=None):
        """
        Streams PCM directly to the I2S amplifier (MAX98357 object) without
        an intermediate file. The amp must already be configured for the
        required frequency/mono mode (sample_rate=self.sample_rate, format=MONO) —
        see the example below.
        """
        
        rate = amp.get_sample_rate()
        amp.set_sample_rate(self.sample_rate)
        last_err = None
        for attempt in range(self.retries):
            try:
                self._send(text, sink=("i2s", amp), chunk_size=chunk_size)
                return
            except OSError as e:
                last_err = e
                if not self.retry_on_network_error:
                    break
                continue
            except SpeechSynthesizerError:
                raise
            except Exception as e:
                raise SpeechSynthesizerError("TTS error: {}".format(e))
            finally:
                amp.set_sample_rate(rate)
                
        amp.set_sample_rate(rate)
        raise SpeechSynthesizerError(
            "Network error after {} attempt(s): {}".format(self.retries, last_err)
        )

    def synthesize_to_file(self, text, out_path, chunk_size=None):
        last_err = None
        for attempt in range(self.retries):
            try:
                self._send(text, sink=("file", out_path), chunk_size=chunk_size)
                return out_path
            except OSError as e:
                last_err = e
                if not self.retry_on_network_error:
                    break
                continue
            except SpeechSynthesizerError:
                raise
            except Exception as e:
                raise SpeechSynthesizerError("TTS error: {}".format(e))
        raise SpeechSynthesizerError(
            "Network error after {} attempt(s): {}".format(self.retries, last_err)
        )

    # --- Private ---

    def _build_wav_header(self, data_size, num_channels=1, bits_per_sample=16):
        byte_rate = self.sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        return struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + data_size, b"WAVE",
            b"fmt ", 16, 1, num_channels,
            self.sample_rate, byte_rate, block_align, bits_per_sample,
            b"data", data_size,
        )

    def _send(self, text, sink, chunk_size=None):
        chunk_size = chunk_size or self.chunk_size

        payload = "text={}&lang={}&speaker={}&chunk_chars={}".format(
            _urlencode_component(text),
            _urlencode_component(self.lang),
            _urlencode_component(self.speaker),
            self.chunk_chars,
        ).encode()

        raw_s = None
        s = None
        try:
            addr = socket.getaddrinfo(self.host, self.port)[0][-1]
            raw_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_s.settimeout(self.socket_timeout)
            raw_s.connect(addr)
            s = ssl.wrap_socket(raw_s, server_hostname=self.host)

            headers = (
                "POST {} HTTP/1.1\r\n"
                "Host: {}\r\n"
                "X-API-Key: {}\r\n"
                "Content-Type: application/x-www-form-urlencoded\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n"
            ).format(self.path, self.host, self.api_key, len(payload))

            s.write(headers.encode())
            s.write(payload)

            status_line = s.readline()
            if not status_line:
                raise SpeechSynthesizerError("Empty response from TTS server")
            status_code = int(status_line.split()[1])

            content_type = ""
            content_length = None
            chunked = False
            while True:
                line = s.readline()
                if not line or line == b"\r\n":
                    break
                low = line.lower()
                if low.startswith(b"content-type:"):
                    content_type = line.split(b":", 1)[1].strip().decode()
                elif low.startswith(b"content-length:"):
                    content_length = int(line.split(b":", 1)[1].strip())
                elif low.startswith(b"transfer-encoding:") and b"chunked" in low:
                    chunked = True

            if status_code < 200 or status_code >= 300:
                body = bytearray()
                while True:
                    chunk = s.read(256)
                    if not chunk:
                        break
                    body.extend(chunk)
                raise SpeechSynthesizerError(
                    "TTS server returned HTTP {}: {}".format(status_code, bytes(body)[:300])
                )

            if content_type.startswith("application/json"):
                body = bytearray()
                while True:
                    chunk = s.read(256)
                    if not chunk:
                        break
                    body.extend(chunk)
                raise SpeechSynthesizerError(
                    "TTS server returned JSON instead of audio: {}".format(bytes(body)[:300])
                )

            kind, target = sink

            if kind == "i2s":
                writer = _I2SWriter(target)
            else:
                tmp_path = target + ".tmp"
                f = open(tmp_path, "wb")
                writer = _FileWriter(f)

            try:
                if chunked:
                    total = self._pump_chunked(s, writer, chunk_size)
                elif content_length is not None:
                    total = self._pump_fixed(s, writer, content_length, chunk_size)
                else:
                    total = self._pump_until_close(s, writer, chunk_size)
                writer.flush()
            finally:
                if kind == "file":
                    f.close()

            if kind == "file":
                header = self._build_wav_header(total)
                with open(target, "wb") as out_f, open(tmp_path, "rb") as in_f:
                    out_f.write(header)
                    buf = bytearray(4096)
                    while True:
                        n = in_f.readinto(buf)
                        if not n:
                            break
                        out_f.write(buf[:n])
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        finally:
            try:
                if s is not None:
                    s.close()
                elif raw_s is not None:
                    raw_s.close()
            except Exception:
                pass

    def _pump_fixed(self, s, writer, total, chunk_size):
        remaining = total
        written = 0
        while remaining > 0:
            n = min(chunk_size, remaining)
            data = s.read(n)
            if not data:
                break
            writer.write(data)
            written += len(data)
            remaining -= len(data)
        return written

    def _pump_until_close(self, s, writer, chunk_size):
        written = 0
        while True:
            data = s.read(chunk_size)
            if not data:
                break
            writer.write(data)
            written += len(data)
        return written

    def _pump_chunked(self, s, writer, chunk_size):
        written = 0
        while True:
            size_line = s.readline()
            if not size_line:
                break
            size_line = size_line.strip()
            if not size_line:
                continue
            size_str = size_line.split(b";", 1)[0]
            try:
                size = int(size_str, 16)
            except ValueError:
                break
            if size == 0:
                while True:
                    line = s.readline()
                    if not line or line == b"\r\n":
                        break
                break
            remaining = size
            while remaining > 0:
                data = s.read(min(chunk_size, remaining))
                if not data:
                    break
                writer.write(data)
                written += len(data)
                remaining -= len(data)
            s.readline()
        return written


class _FileWriter:
    def __init__(self, f):
        self._f = f

    def write(self, data):
        self._f.write(data)

    def flush(self):
        pass


class _I2SWriter:
    def __init__(self, amp):
        self._amp = amp
        self._carry = b""

    def write(self, data):
        buf = self._carry + data
        n = len(buf)
        even = n - (n % 2)
        if even:
            self._amp.write(buf[:even])
        self._carry = buf[even:]  # 0 или 1 байт

    def flush(self):
        self._carry = b""