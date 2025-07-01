import network, socket, ssl, json, time, machine

WIFI_SSID     = "NU"
WIFI_PASSWORD = "1234512345"
TG_TOKEN      = "8007396055:AAG0B54py1ASPmz8RLgfeJPNmCfg48pzScI"
TG_CHAT_ID    = "-1002402631866"

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
            if time.ticks_diff(time.ticks_ms(), start) < self.timeout * 1000:
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

