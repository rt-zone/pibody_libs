_demo = None

def run():
    global _demo
    if _demo is None:
        from .core import Demo
        _demo = Demo()
    _demo.run()
