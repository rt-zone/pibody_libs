from machine import Pin, Timer
import neopixel
# from oled_gfx import SSD1306_I2C
# from pibody.wrappers.i2c import get_i2c
from pibody import ClimateSensor
from pibody.IOT.WebUi import App, ColorPicker, Slider, Toggle, Label, Button, TextInput, TextDisplay
from pibody import OLED

oled = OLED('A')
# ---------- Settings ----------
WIFI_SSID = "Artisan"
WIFI_PASSWORD = "Artisan2807"

NEOPIXEL_PIN = 28
NUM_PIXELS = 8
# --------------------------------

np = neopixel.NeoPixel(Pin(NEOPIXEL_PIN), NUM_PIXELS)

# i2c = get_i2c('A')
bme = ClimateSensor('B')

state = {"r": 0, "g": 150, "b": 255, "brightness": 100, "on": True}
user_text = ""


def apply_state():
    if not state["on"]:
        for i in range(NUM_PIXELS):
            np[i] = (0, 0, 0)
    else:
        scale = state["brightness"] / 100
        r = int(state["r"] * scale)
        g = int(state["g"] * scale)
        b = int(state["b"] * scale)
        for i in range(NUM_PIXELS):
            np[i] = (r, g, b)
    np.write()


def on_color(r, g, b):
    state["r"], state["g"], state["b"] = r, g, b
    apply_state()


def on_brightness(value):
    state["brightness"] = value
    apply_state()


def on_toggle(value):
    state["on"] = value
    apply_state()


def redraw_oled():
    """Перерисовывает весь экран: введённый текст + данные сенсора."""
    oled.fill(0)
    oled.text(user_text[:16] if user_text else "no text", 0, 0)
    oled.text(f"T:{sensor_temp_text}", 0, 20)
    oled.text(f"P:{sensor_pressure_text}", 0, 32)
    oled.text(f"H:{sensor_humidity_text}", 0, 44)
    oled.show()


def on_text(value):
    """Вызывается при вводе/отправке текста из веб-UI."""
    global user_text
    user_text = value
    redraw_oled()


sensor_temp_text = "--"
sensor_pressure_text = "--"
sensor_humidity_text = "--"


def read_climate():
    global sensor_temp_text, sensor_pressure_text, sensor_humidity_text
    try:
        if hasattr(bme, "values"):
            # вариант вроде bme280_float: bme.values -> (temp, pressure, humidity)
            t, p, h = bme.values
        elif hasattr(bme, "read"):
            data = bme.read()
            t, p, h = data.get("temperature"), data.get("pressure"), data.get("humidity")
        elif hasattr(bme, "temperature"):
            t = bme.temperature
            p = getattr(bme, "pressure", "--")
            h = getattr(bme, "humidity", "--")
        else:
            raise AttributeError("Неизвестный API ClimateSensor: " + str(dir(bme)))

        sensor_temp_text = str(t)
        sensor_pressure_text = str(p)
        sensor_humidity_text = str(h)
    except Exception as e:
        print("Ошибка чтения climate sensor:", e)
        sensor_temp_text = "err"
        sensor_pressure_text = "err"
        sensor_humidity_text = "err"

    redraw_oled()
    sensor_value_display.update(
        f"""
        Temperture: {sensor_temp_text}
        Presure: {sensor_pressure_text}
        Humidity: {sensor_humidity_text}
        """
    )


def on_timer(t):
    read_climate()


# --- Глобальная тема ---
theme = {
    "bg": "#0d1117",
    "card_bg": "#161b22",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "accent": "#58a6ff",
    "on_color": "#3fb950",
    "off_color": "#30363d",
    "radius": "20px",
}

app = App("NeoPixel-контроллер",
          wifi_ssid=WIFI_SSID, wifi_password=WIFI_PASSWORD,
          theme=theme)

app.add(Label("Настройки света"))
app.add(ColorPicker("Цвет", value=(0, 150, 255), on_change=on_color))
app.add(Slider("Яркость", min=0, max=100, value=100,
                on_change=on_brightness, color="#f1c40f"))
app.add(Toggle("Питание", value=True, on_change=on_toggle))

app.add(Label("Текст на дисплей"))
app.add(TextInput("Введите текст", value="", on_change=on_text))
# app.add()

app.add(Label("Данные климат-сенсора"))
sensor_value_display = TextDisplay("Температура / давление / влажность", value="T: --  P: --  H: --")
app.add(sensor_value_display)

app.add(Button("Buy coffee for me", color="#e74c3c"))

apply_state()

# Периодический опрос сенсора раз в 2 секунды
sensor_timer = Timer()
sensor_timer.init(period=2000, mode=Timer.PERIODIC, callback=on_timer)

read_climate()  # первый снимок сразу при старте
app.run()