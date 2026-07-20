import network
import socket
import time


DEFAULT_THEME = {
    "bg": "#111111",        # page background
    "card_bg": "#1c1c1c",   # card background
    "text": "#eeeeee",      # main text
    "muted": "#aaaaaa",     # captions/secondary text
    "accent": "#3498db",    # accent color (sliders, action buttons)
    "on_color": "#2ecc71",  # toggle color (on state)
    "off_color": "#444444", # toggle color (off state)
    "input_bg": "#2a2a2a",  # text input / text display background
    "radius": "16px",       # card corner radius
}


def _css_var_name(key):
    return "--" + key.replace("_", "-")


def _style_attr(**overrides):
    parts = []
    for key, value in overrides.items():
        if value:
            parts.append("{}: {}".format(_css_var_name(key), value))
    if not parts:
        return ""
    return ' style="{}"'.format("; ".join(parts))


def _url_decode(s):
    # Minimal percent-decoder (no urllib.parse on MicroPython).
    if "%" not in s:
        return s.replace("+", " ")
    result = bytearray()
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "%" and i + 2 < n:
            try:
                result.append(int(s[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        elif c == "+":
            result.append(0x20)
            i += 1
            continue
        else:
            result.append(ord(c))
        i += 1
    return bytes(result).decode("utf-8")


def _html_escape(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


class Component:
    _counter = 0

    def __init__(self, label):
        self.label = label
        self.id = "c{}".format(Component._counter)
        Component._counter += 1

    def render_html(self):
        raise NotImplementedError

    def handle(self, raw_value):
        pass


class Slider(Component):
    def __init__(self, label, min=0, max=100, value=50, step=1, on_change=None, color=None):
        super().__init__(label)
        self.min = min
        self.max = max
        self.value = value
        self.step = step
        self.on_change = on_change
        self.color = color

    def render_html(self):
        style = _style_attr(accent=self.color)
        return """
        <div class="field"{style}>
            <label>{label}: <span id="{id}_val">{value}</span></label>
            <input type="range" id="{id}" min="{min}" max="{max}" step="{step}" value="{value}"
                oninput="document.getElementById('{id}_val').textContent=this.value; sendUpdate('{id}', this.value)">
        </div>
        """.format(label=self.label, id=self.id, value=self.value,
                    min=self.min, max=self.max, step=self.step, style=style)

    def handle(self, raw_value):
        self.value = int(raw_value) if self.step == 1 else float(raw_value)
        if self.on_change:
            self.on_change(self.value)


class Toggle(Component):
    """iOS / Material Design 3 style sliding switch."""

    def __init__(self, label, value=False, on_change=None, on_color=None, off_color=None):
        super().__init__(label)
        self.value = value
        self.on_change = on_change
        self.on_color = on_color
        self.off_color = off_color

    def render_html(self):
        cls = "on" if self.value else "off"
        style = _style_attr(**{"on_color": self.on_color, "off_color": self.off_color})
        return """
        <div class="field toggle-row"{style}>
            <label>{label}</label>
            <div class="switch" id="{id}" role="switch" aria-checked="{checked}"
                onclick="toggleBtn('{id}')">
                <div class="switch-track {cls}">
                    <div class="switch-thumb"></div>
                </div>
            </div>
        </div>
        """.format(label=self.label, id=self.id, cls=cls, style=style,
                    checked="true" if self.value else "false")

    def handle(self, raw_value):
        self.value = raw_value == "1"
        if self.on_change:
            self.on_change(self.value)


class ColorPicker(Component):
    def __init__(self, label, value=(255, 255, 255), on_change=None):
        super().__init__(label)
        self.value = value
        self.on_change = on_change

    def render_html(self):
        hexcolor = "#{:02x}{:02x}{:02x}".format(*self.value)
        return """
        <div class="field">
            <label>{label}</label>
            <input type="color" id="{id}" value="{hexcolor}" oninput="sendColor('{id}', this.value)">
        </div>
        """.format(label=self.label, id=self.id, hexcolor=hexcolor)

    def handle(self, raw_value):
        r = int(raw_value[0:2], 16)
        g = int(raw_value[2:4], 16)
        b = int(raw_value[4:6], 16)
        self.value = (r, g, b)
        if self.on_change:
            self.on_change(r, g, b)


class Button(Component):
    def __init__(self, label, on_click=None, color=None):
        super().__init__(label)
        self.on_click = on_click
        self.color = color

    def render_html(self):
        style = _style_attr(accent=self.color)
        return """
        <div class="field"{style}>
            <button id="{id}" class="action-btn" onclick="sendUpdate('{id}', '1')">{label}</button>
        </div>
        """.format(id=self.id, label=self.label, style=style)

    def handle(self, raw_value):
        if self.on_click:
            self.on_click()


class Label(Component):
    def __init__(self, label, color=None):
        super().__init__(label)
        self.color = color

    def render_html(self):
        style = _style_attr(muted=self.color)
        return '<h2 class="section-label"{style}>{label}</h2>'.format(
            label=self.label, style=style)


class TextDisplay(Component):
    """
    Read-only text/value display in a rounded, padded frame.
    Update it from your code with `.update(new_value)`; the page polls
    the server periodically and refreshes the displayed value on its own,
    with no need to reload the page.
    """

    def __init__(self, label, value="", color=None, poll_interval=None):
        super().__init__(label)
        self.value = value
        self.color = color
        self.poll_interval = poll_interval  # ms override for this widget, optional

    def render_html(self):
        style = _style_attr(accent=self.color)
        return """
        <div class="field"{style}>
            <label>{label}</label>
            <div class="text-display" id="{id}" data-live="1">{value}</div>
        </div>
        """.format(label=self.label, id=self.id, style=style,
                    value=_html_escape(self.value))

    def update(self, value):
        """Call this server-side to change what the widget shows in the browser."""
        self.value = value.strip()

    def handle(self, raw_value):
        # Read-only by default: nothing to do when the client posts to it.
        pass


class TextInput(Component):
    """
    Free-form text (or any string-encoded data) entry field.
    Sends its value to the server when the user presses Enter or the
    field loses focus.
    """

    def __init__(self, label, value="", placeholder="", on_change=None, color=None):
        super().__init__(label)
        self.value = value
        self.placeholder = placeholder
        self.on_change = on_change
        self.color = color

    def render_html(self):
        style = _style_attr(accent=self.color)
        return """
        <div class="field"{style}>
            <label>{label}</label>
            <input type="text" id="{id}" class="text-input" value="{value}" placeholder="{placeholder}"
                onchange="sendText('{id}', this.value)"
                onkeydown="if(event.key==='Enter'){{ this.blur(); }}">
        </div>
        """.format(label=self.label, id=self.id, style=style,
                    value=_html_escape(self.value), placeholder=_html_escape(self.placeholder))

    def handle(self, raw_value):
        self.value = _url_decode(raw_value)
        if self.on_change:
            self.on_change(self.value)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg: {bg};
    --card-bg: {card_bg};
    --text: {text};
    --muted: {muted};
    --accent: {accent};
    --on-color: {on_color};
    --off-color: {off_color};
    --input-bg: {input_bg};
    --radius: {radius};
  }}
  body {{ font-family: -apple-system, Arial, sans-serif; background:var(--bg); color:var(--text);
          display:flex; flex-direction:column; align-items:center; padding:24px; margin:0; }}
  h1 {{ font-size:20px; margin-bottom:20px; }}
  .card {{ background:var(--card-bg); border-radius:var(--radius); padding:24px; width:100%;
           max-width:360px; box-shadow:0 4px 20px rgba(0,0,0,.4); }}
  .field {{ margin-bottom:18px; }}
  label {{ display:block; margin-bottom:6px; font-size:14px; color:var(--muted); }}
  input[type=range] {{ width:100%; accent-color: var(--accent); }}
  input[type=color] {{ width:100%; height:46px; border:none; border-radius:10px; }}
  button {{ width:100%; padding:12px; border:none; border-radius:10px; font-size:15px;
            font-weight:600; cursor:pointer; }}
  .action-btn {{ background:var(--accent); color:#fff; }}
  .section-label {{ align-self:flex-start; font-size:14px; color:var(--muted); margin:20px 0 4px; }}

  /* --- iOS / Material 3 style toggle switch --- */
  .toggle-row {{ display:flex; align-items:center; justify-content:space-between; }}
  .toggle-row label {{ margin-bottom:0; }}
  .switch {{ position:relative; width:52px; height:30px; flex-shrink:0; cursor:pointer; }}
  .switch-track {{ position:absolute; inset:0; background:var(--off-color); border-radius:999px;
                    transition:background-color .2s ease; }}
  .switch-track.on {{ background:var(--on-color); }}
  .switch-thumb {{ position:absolute; top:3px; left:3px; width:24px; height:24px; border-radius:50%;
                    background:#ffffff; box-shadow:0 1px 3px rgba(0,0,0,.35);
                    transition:transform .2s ease; }}
  .switch-track.on .switch-thumb {{ transform:translateX(22px); }}

  /* --- Rounded, padded text display (updatable) --- */
  .text-display {{ background:var(--input-bg); border-radius:12px; padding:12px 16px;
                    font-size:15px; word-wrap:break-word; min-height:20px; 
                    white-space: pre-line; }}

  /* --- Text / data input field --- */
  .text-input {{ width:100%; box-sizing:border-box; background:var(--input-bg); color:var(--text);
                  border:none; border-radius:12px; padding:12px 16px; font-size:15px; }}
  .text-input:focus {{ outline:2px solid var(--accent); }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="card">
{body}
</div>
<script>
function sendUpdate(id, value) {{
  fetch('/set?id=' + id + '&value=' + encodeURIComponent(value));
}}
function sendText(id, text) {{
  fetch('/set?id=' + id + '&value=' + encodeURIComponent(text));
}}
function sendColor(id, hex) {{
  sendUpdate(id, hex.substring(1));
}}
function toggleBtn(id) {{
  const el = document.getElementById(id);
  const track = el.querySelector('.switch-track');
  const isOn = track.classList.contains('on');
  track.classList.toggle('on', !isOn);
  track.classList.toggle('off', isOn);
  el.setAttribute('aria-checked', !isOn ? 'true' : 'false');
  sendUpdate(id, !isOn ? '1' : '0');
}}
function pollLive() {{
  document.querySelectorAll('[data-live="1"]').forEach(function (el) {{
    fetch('/get?id=' + el.id)
      .then(function (r) {{ return r.text(); }})
      .then(function (v) {{ if (document.activeElement !== el) el.textContent = v; }})
      .catch(function () {{}});
  }});
}}
setInterval(pollLive, 2000);
</script>
</body>
</html>
"""


class App:
    def __init__(self, title="Pico Web UI", wifi_ssid=None, wifi_password=None, theme=None):
        self.title = title
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.components = {}
        self._order = []

        self.theme = dict(DEFAULT_THEME)
        if theme:
            self.theme.update(theme)

    def add(self, component):
        self.components[component.id] = component
        self._order.append(component)
        return component

    def render_page(self):
        body = "\n".join(c.render_html() for c in self._order)
        page_vars = dict(self.theme)
        page_vars["title"] = self.title
        page_vars["body"] = body
        return PAGE_TEMPLATE.format(**page_vars)

    def connect_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.wifi_ssid, self.wifi_password)
        print("Connecting to Wi-Fi", end="")
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        if not wlan.isconnected():
            raise RuntimeError("Can't connect to Wi-Fi")
        ip = wlan.ifconfig()[0]
        print("\nConnected! IP address:", ip)
        return ip

    def _parse_query(self, path):
        params = {}
        if "?" in path:
            query = path.split("?", 1)[1]
            for pair in query.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v
                else:
                    params[pair] = ""
        return params

    def _handle_request(self, path):
        if path.startswith("/set"):
            params = self._parse_query(path)
            cid = params.get("id")
            value = params.get("value", "")
            comp = self.components.get(cid)
            if comp:
                comp.handle(value)
            return "OK", "text/plain"

        if path.startswith("/get"):
            params = self._parse_query(path)
            cid = params.get("id")
            comp = self.components.get(cid)
            value = getattr(comp, "value", "") if comp else ""
            return str(value), "text/plain"

        return self.render_page(), "text/html"

    def run(self, port=80):
        if self.wifi_ssid:
            self.connect_wifi()

        addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(2)
        print("Web server runs on", addr)

        while True:
            cl = None
            try:
                cl, _ = s.accept()
                request = cl.recv(1024).decode()
                request_line = request.split("\r\n", 1)[0]
                path = request_line.split(" ")[1]
                body, content_type = self._handle_request(path)
                response = (
                    "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nConnection: close\r\n\r\n{}"
                ).format(content_type, body)
                cl.send(response)
            except Exception as e:
                print("Request error:", e)
            finally:
                if cl:
                    cl.close()


class WebUi(App):
    Label = Label
    Slider = Slider
    Toggle = Toggle
    ColorPicker = ColorPicker
    Button = Button
    TextInput = TextInput
    TextDisplay = TextDisplay

    _WIDGET_NAMES = {"Label", "Slider", "Toggle", "ColorPicker",
                    "Button", "TextInput", "TextDisplay"}

    def __getattribute__(self, name):
        if name in WebUI._WIDGET_NAMES:
            raise AttributeError(
                f"'{name}' Accessible only like WebUI.{name}(), "
                f"not like (web.{name})"
            )
        return object.__getattribute__(self, name)