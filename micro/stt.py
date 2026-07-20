import os
import socket
import ssl
import ujson


class SpeechRecognizerError(Exception):
    """Unsolvable problem"""
    pass


class SpeechRecognizer:
    def __init__(self, api_key: str, host="mangisoz.nu.edu.kz",
                path="/backend/api/v1/stt/transcribe", port=443,
                language="auto", response_format="json", temperature="1",
                include_raw="false", stream="false",
                retries=3, chunk_size=512, socket_timeout=20,
                retry_on_network_error=True):
        """
        api_key - stt api key (requered for work)
        host    - url (without path and endpoint).
        path    - endpoint path.
        """
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.host = host
        self.path = path
        self.port = port
        self.language = language
        self.response_format = response_format
        self.temperature = temperature
        self.include_raw = include_raw
        self.stream = stream
        self.retries = max(1, retries)
        self.chunk_size = chunk_size
        self.socket_timeout = socket_timeout
        self.retry_on_network_error = retry_on_network_error
        self.boundary = "PicoWStreamBoundary"

    def transcribe(self, file_path):
        '''Send wav file stream to stt server'''
        last_err = None
        for attempt in range(self.retries):
            try:
                return self._send(file_path)
            except OSError as e:
                # Network error
                last_err = e
                if not self.retry_on_network_error:
                    break
                continue
            except SpeechRecognizerError:
                raise
            except Exception as e:
                raise SpeechRecognizerError("STT error: {}".format(e))

        raise SpeechRecognizerError(
            "Network error after {} attempt(s): {}".format(self.retries, last_err)
        )

    # --- Private ---
    def _field(self, name, value):
        return "--{}\r\nContent-Disposition: form-data; name=\"{}\"\r\n\r\n{}\r\n".format(
            self.boundary, name, value)

    def _send(self, file_path):
        boundary = self.boundary
        file_size = os.stat(file_path)[6]

        fields = [
            self._field("language", self.language),
            self._field("response_format", self.response_format),
            self._field("temperature", self.temperature),
            self._field("include_raw", self.include_raw),
            self._field("stream", self.stream),
        ]

        file_header = (
            "--{}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"{}\"\r\n"
            "Content-Type: audio/wav\r\n\r\n"
        ).format(boundary, file_path.split("/")[-1])
        file_footer = "\r\n--{}--\r\n".format(boundary)

        content_length = sum(len(f) for f in fields) + len(file_header) + file_size + len(file_footer)

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
                "Content-Type: multipart/form-data; boundary={}\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n"
            ).format(self.path, self.host, self.api_key, boundary, content_length)

            s.write(headers.encode())
            for f in fields:
                s.write(f.encode())
            s.write(file_header.encode())

            with open(file_path, "rb") as f:
                buf = bytearray(self.chunk_size)
                while True:
                    n = f.readinto(buf)
                    if not n:
                        break
                    s.write(buf[:n])

            s.write(file_footer.encode())

            # --- status line ---
            status_line = s.readline()
            if not status_line:
                raise SpeechRecognizerError("Empty response from STT server")
            status_code = int(status_line.split()[1])

            # --- headers ---
            while True:
                line = s.readline()
                if not line or line == b"\r\n":
                    break

            # --- body ---
            body = bytearray()
            while True:
                chunk = s.read(256)
                if not chunk:
                    break
                body.extend(chunk)

            if status_code < 200 or status_code >= 300:
                raise SpeechRecognizerError(
                    "STT server returned HTTP {}: {}".format(status_code, bytes(body)[:300])
                )

            result = ujson.loads(body.decode())
            text = result.get("text", "")
            return text.strip() if text else ""

        finally:
            try:
                if s is not None:
                    s.close()
                elif raw_s is not None:
                    raw_s.close()
            except Exception:
                pass