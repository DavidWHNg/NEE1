
from psychopy import core, event, gui, visual, parallel, prefs
pport = parallel.ParallelPort(address=0xDFD8)
TENS_pulse_int = 0.1 # interval length for TENS on/off signals (e.g. 0.1 = 0.2s per pulse) NOTE; likely only 1 decimal place precision

win = visual.Window(
    size=(1920, 1080), fullscr= True, screen=0,
    allowGUI=False, allowStencil=False,
    monitor="testMonitor", color=[0, 0, 0], colorSpace="rgb1",
    blendMode="avg", useFBO=True,
    units="pix")

visual.TextStim(win,
                text="Please let the experimenter know when you begin to feel the TENS",
                color="white",
                height=25,
                pos=(0, 0),
                wrapWidth=600
                ).draw()

win.flip()

calib_finish = False
countdown_timer = core.CountdownTimer(300)
TENS_timer = countdown_timer.getTime() + TENS_pulse_int

while calib_finish == False:
    keys_pressed = event.getKeys()  
    if 'space' in keys_pressed:  # Check for "spacebar" to end calibration
        calib_finish = True
    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
        pport.setData(128)
    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
        pport.setData(0)
        TENS_timer = countdown_timer.getTime() 

pport.setData(0)
core.quit()