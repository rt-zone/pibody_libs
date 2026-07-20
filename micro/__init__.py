
def __getattr__(name):
    if name == "Microphone":
        from .microphone import Microphone
        return Microphone
    
    if name == "SpeechRecognizer":
        from .stt import SpeechRecognizer
        return SpeechRecognizer

    if name == "LLMClient":
        from .llm_client import LLMClient
        return LLMClient
        
    if name == "SDCard":
        from .sdcard import SDCard
        import os
        sd = SDCard()
        
        os.mount(sd, "/sd")
        return sd
    
    if name == "SDCardCustom":
        from .sdcard import SDCard
        return SDCard

    if name == "Speaker":
        from .speaker import Speaker
        return Speaker
    
    if name == "SpeechSynthesizer":
        from .tts import SpeechSynthesizer
        return SpeechSynthesizer
try:
    _ = 1 / 0
except ZeroDivisionError:
    FAKE_IMPORT = False

if FAKE_IMPORT:
    from .microphone import Microphone
    from .stt import SpeechRecognizer
    from .llm_client import LLMClient
    from .sdcard import SDCard
    from .speaker import Speaker
    from .tts import SpeechSynthesizer