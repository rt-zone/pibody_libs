def run():
    from pibody import display
    # from pibody import Display
    # display = Display()

    display.print("Hello")
    display.logo()
    display.clear()
    display.linear_bar(10, 10, 20, 0, 100, border=True)
    display.arc(100, 100, 10, start_angle=20, end_angle=250)
    display.circular_bar(150, 150, 20, 20, 0, 100, 2)
    display.text("Hello", 10, 200)
    display.hsv(100, 1, 1)
    # Rest methods are implied to be working, since they are used by the methods above and stored in cmodules by russ hughes and aren't subject to change
    print("Display test is over successfully, given that what you see on the screen is reasonable")
    return 1