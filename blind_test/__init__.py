from . import pin_test, import_test, display_test

def run():
    import_test.run()
    pin_test.run(True)
    display_test.run()
