import network, time, socket, struct
NTP_HOST = 'pool.ntp.org'

class WiFi:
    def __init__(self, ssid: str, password: str, timeout: int = 10):
        self.ssid = ssid
        self.password = password
        self.timeout = timeout
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self):
        if self.wlan.isconnected():
            print("Already connected.")
            return self.wlan.ifconfig()

        print(f"Connecting to {self.ssid}...")
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)

        start = time.ticks_ms()
        while not self.wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > (self.timeout * 1000):
                raise RuntimeError("Wi-Fi connection timed out.")
            time.sleep(0.5)

        print("Connected!")
        print("IP address:", self.wlan.ifconfig()[0])
        return self.wlan.ifconfig()

    def disconnect(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("Disconnected from Wi-Fi.")

    def is_connected(self):
        return self.wlan.isconnected()

    def ip(self):
        return self.wlan.ifconfig()[0] if self.is_connected() else None
    
    def get_time(self, gmt=5):
        NTP_DELTA = 2208988800
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        gmt_offset = gmt * 3600
        addr = socket.getaddrinfo(NTP_HOST, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        ntp_time = struct.unpack("!I", msg[40:44])[0]
        return time.gmtime(ntp_time - NTP_DELTA + gmt_offset)

