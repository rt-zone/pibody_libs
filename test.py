
from pibody import Button, WiFi, Microphone, sdcard
import os

mic = Microphone('A', 'B')
btn = Button('C')

wifi = WiFi()
wifi.connect("Artisan", "Artisan2807")

path = ""

# --- блокирующий вариант ---
# print("Начелась запись")
# path = mic.record(5)
# print("Готово:", path)

while True:
    if btn.value() == 1:
        if not mic.is_record():
            path = mic.start()
            print("Start:", path)
    else:
        if mic.is_record():
            print("Stop record")
            mic.stop()
            break

# Speech recognization
from pibody import SpeechRecognizer
from secrets import STT_KEY
speech = SpeechRecognizer(STT_KEY)
import time
time.sleep(2)

print("Make response to stt")
speech.language = "ru"
stt_text = speech.transcribe(path)
print("Parsed: ", stt_text)


# LLM
from secrets import LLM_KEY, LLM_URL, MODEL
from pibody import LLMClient

API_KEY = LLM_KEY
URL = LLM_URL
MODEL = MODEL


llm = LLMClient(
    api_key=API_KEY,
    url=URL,
    model=MODEL,
)

code = llm.ask(stt_text)
print("LLM: ", code)

from pibody import Speaker, SpeechSynthesizer
import gc
amp = Speaker('D', 'E')
amp.set_sample_rate(sample_rate=22050)
amp.set_volume(0.5)

gc.collect()
tts = SpeechSynthesizer(api_key=STT_KEY, lang="ru")

try:
    tts.synthesize_to_i2s(code, amp)
except Exception as e:
    print("Ошибка TTS:", e)
