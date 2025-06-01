# Import packages
from psychopy import core, event, gui, visual, parallel
import time
import math
import random
import csv
import os

ports_live = None # Set to None if parallel ports not plugged for coding/debugging other parts of exp

### Experiment details/parameters
# misc parameters
port_buffer_duration = 1 #needs about 0.5s buffer for port signal to reset 
iti = 3
pain_response_duration = float("inf")
response_hold_duration = 1 # How long the rating screen is left on the response (only used for Pain ratings)
TENS_trig = 128
TENS_pulse_pattern_list = {"pause": [(0.0, TENS_trig), (0.1, 0), # 3 rapid pulses followed by pause, first number specifies time in seconds, second number port send value
                                 (0.2, TENS_trig), (0.3, 0),
                                 (0.4, TENS_trig), (0.5, 0)],
                       "constant": [(0.0, TENS_trig), (0.10, 0),
                                (0.333, TENS_trig), (0.433, 0),
                                (0.666, TENS_trig), (0.766, 0)] # constant equally spaced pulses 
}

timer_precision_range = 0.01 # pulses should be accurate to within 10 milliseconds

TENS_names = ["monopolar", "bipolar"]

# interval length for TENS on/off signals (e.g. 0.1 = 0.2s per pulse)

# within experiment parameters
P_info = {"PID": ""}
info_order = ["PID"]

# Participant info input
while True:
    try:
        P_info["PID"] = input("Enter participant ID: ")
        if not P_info["PID"]:
            print("Participant ID cannot be empty.")
            continue
            
        csv_filename = P_info["PID"] + "_responses.csv"
        script_directory = os.path.dirname(os.path.abspath(__file__))  #Set the working directory to the folder the Python code is opened from
        
        #set a path to a "data" folder to save data in
        data_folder = os.path.join(script_directory, "data")
        
        # if data folder doesn"t exist, create one
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        #set file name within "data" folder
        csv_filepath = os.path.join(data_folder,csv_filename)
        
        if os.path.exists(csv_filepath):
            print(f"Data for participant {P_info['PID']} already exists. Choose a different participant ID.") ### to avoid re-writing existing data
            
        else:
            cb = int(P_info["PID"]) % 4

            if cb in [0, 2]:
                group = 1
                group_name = "consistent"
            else:
                group = 2
                group_name = "change"

            cb = int(P_info["PID"]) % 4
            
            break  # Exit the loop if the participant ID is valid
    except KeyboardInterrupt:
        print("Participant info input canceled.")
        break  # Exit the loop if the participant info input is canceled

    # get date and time of experiment start
datetime = time.strftime("%Y-%m-%d_%H.%M.%S")

TENS_outcomes = {"suboptimal": TENS_names[cb%2],
                 "optimal" : TENS_names[(cb+1)%2]
}

if (cb // 2) % 2 == 0:
    TENS1_name = TENS_outcomes["suboptimal"] #e.g. monopolar
    TENS2_name = TENS_outcomes["optimal"] #e.g. bipolar
    TENS1_type = "suboptimal"
    TENS2_type = "optimal"
else:
    TENS1_name = TENS_outcomes["optimal"]
    TENS2_name = TENS_outcomes["suboptimal"]
    TENS1_type = "optimal"
    TENS2_type = "suboptimal"


# Assign pulse pattern lists
TENS_pulse_patterns = {
    TENS1_name: TENS_pulse_pattern_list["pause"],
    TENS2_name: TENS_pulse_pattern_list["constant"]
}

# Store pulse pattern names for saving
TENS_pulse_patterns_names = {
    TENS1_type: "pause",
    TENS2_type: "constant"
}

# external equipment connected via parallel ports
shock_levels = 10

shock_trig = {"high": 1, 
              "low": 11, 
              "medium": 21} #byte values start on lowest levels

stim_trig = {"TENS": 128, "control": 0} #Pin 8 TENS in AD instrument

if ports_live == True:
    pport = parallel.ParallelPort(address=0x3ff8) #Get from device Manager
    pport.setData(0)
    
elif ports_live == None:
    pport = None #Get from device Manager

# set up screen
win = visual.Window(
    size=(1920, 1080), fullscr= True, screen=0,
    allowGUI=False, allowStencil=False,
    monitor="testMonitor", color=[0, 0, 0], colorSpace="rgb1",
    blendMode="avg", useFBO=True,
    units="pix")

# fixation stimulus
fix_stim = visual.TextStim(win,
                            text = "x",
                            color = "white",
                            height = 50,
                            font = "Roboto Mono Medium")


#define waiting function so experiment doesn't freeze as it does with core.wait()
def wait(time):
    countdown_timer = core.CountdownTimer(time)
    while countdown_timer.getTime() > 0:
        termination_check()
        
#create instruction trials
def instruction_trial(instructions,holdtime): 
    termination_check()
    visual.TextStim(win,
                    text = instructions,
                    height = 35,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    win.flip()
    wait(holdtime)
    visual.TextStim(win,
                    text = instructions,
                    height = 35,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    visual.TextStim(win,
                    text = instructions_text["continue"],
                    height = 35,
                    color = "white",
                    pos = (0,-400)
                    ).draw()
    win.flip()
    event.waitKeys(keyList=["space"])
    win.flip()
    
    wait(iti)
    
# Create functions
    # Save responses to a CSV file
def save_data(data):
    
    for trial in trial_order:
        trial['datetime'] = datetime
        trial["PID"] = P_info["PID"]
        trial["group"] = group
        trial["group_name"] = group_name
        trial["cb"] = cb
        trial["optimalTENS_name"] = TENS_outcomes["optimal"]
        trial["optimalTENS_pattern"] = TENS_pulse_patterns_names["optimal"]
        trial["shock_level_high"] = shock_trig["high"]


    trial_order.extend(calib_trial_order)
    # Extract column names from the keys in the first trial dictionary
    colnames = list(trial_order[0].keys())

    # Open the CSV file for writing
    with open(csv_filepath, mode="w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=colnames)
        
        # Write the header row
        writer.writeheader()
        
        # Write each trial"s data to the CSV file
        for trial in data:
            writer.writerow(trial)
    
def exit_screen(instructions):
    win.flip()
    visual.TextStim(win,
            text = instructions,
            height = 35,
            color = "white",
            pos = (0,0)).draw()
    win.flip()
    event.waitKeys()
    win.close()
    
def termination_check(): #insert throughout experiment so participants can end at any point.
    keys_pressed = event.getKeys(keyList=["escape"])  # Check for "escape" key during countdown
    if "escape" in keys_pressed:
        if ports_live:
            pport.setData(0) # Set all pins to 0 to shut off TENS, shock etc.
        # Save participant information

        save_data(trial_order)
        exit_screen(instructions_text["termination"])
        core.quit()
        
#define choice function for TENS trials

def outcome_randomise(outcome1,outcome2,rft_schedule):
    return random.choices(
        [outcome1,outcome2],
        weights = [rft_schedule,1-rft_schedule],
    k=1
    )[0]

# Define trials
# Calibration trials
calib_trial_order = []
for i in range(1,shock_levels+1):
    temp_trial_order = []
    trial = {
        "phase": "calibration",
        "blocknum": "calibration",
        "stimulus": None,
        "choicetrial": False,
        "choice1": None,
        "choice2": None,
        "outcome" : "high",
        "trialtype": "calibration",
        "pain_response": None
        } 
    temp_trial_order.append(trial)
    calib_trial_order.extend(temp_trial_order)
    

# Setting conditioning trial order
# Number of trials
trial_order = []

#### 4 x blocks (2 TENS + low shock, 2 control + high shock)
num_blocks_conditioning = 10
num_blocks_extinction = 10
num_trials_block = {
        "conditioning": {
            "TENS": {
                "num":4,
                "stimulus": "TENS",
                "choicetrial": True,
                "choice1": TENS_outcomes["optimal"],
                "choice2": TENS_outcomes["suboptimal"],
                "outcome": None,
            },
            "control": {
                "num":1,
                "stimulus": None, 
                "choicetrial": False,
                "choice1": None,
                "choice2": None,
                "outcome": "low",
            }
        },
        "extinction": {
            "monopolar": {
                "num":1,
                "stimulus": "TENS",
                "choicetrial": False,
                "choice1": None,
                "choice2": None,
                "outcome": "low",
            },
            "bipolar": {
                "num":1,
                "stimulus": "TENS",
                "choicetrial": False,
                "choice1": None,
                "choice2": None,
                "outcome": "low",
            },
            "control": {
                "num":1,
                "stimulus": None,
                "choicetrial": False,
                "choice1": None,
                "choice2": None,
                "outcome": "low",
            }
        }
}

if group_name == "consistent":
    rft_schedule_blocks = {
        "conditioning": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "extinction": [1] * num_blocks_extinction
    }
else:
    rft_schedule_blocks = {
        "conditioning": [1, 1, 0.75, 0.75, 0.5, 0.5, 0.25, 0.25, 0, 0],
        "extinction": [1] * num_blocks_extinction
    }
    
for phase, trials in num_trials_block.items():
    if phase == "conditioning":
        num_blocks = num_blocks_conditioning 
    else: 
        num_blocks = num_blocks_extinction
    
    for block in range(num_blocks):
        temp_trial_order = []

        for trial_type, trial_info in trials.items():
            for num in range(trial_info["num"]):
                trial = {
                    "phase": phase,
                    "trialtype": trial_type,
                    "stimulus": trial_info["stimulus"],
                    "choice1": trial_info["choice1"],
                    "choice2": trial_info["choice2"],
                    "choicetrial": trial_info["choicetrial"],
                    "rft_schedule": rft_schedule_blocks[phase][block],
                    "outcome": trial_info["outcome"],
                    "choice_response": None,
                    "exp_response": None,
                    "pain_response": None
                }
                if phase == "conditioning":
                    trial["blocknum"] = (block//2) + 1
                else:
                    trial["blocknum"] = block
                    
                temp_trial_order.append(trial)

        random.shuffle(temp_trial_order)
        trial_order.extend(temp_trial_order)
    
# Assign trial numbers
for trialnum, trial in enumerate(trial_order, start=1):
    trial["trialnum"] = trialnum
    
#Test questions
rating_stim = { "Calibration": visual.Slider(win,
                                    pos = (0,-200),
                                    ticks=[0,50,100],
                                    labels=(1,5,10),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
                "Pain": visual.Slider(win,
                                    pos = (0,-200),
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
                "Expectancy": visual.Slider(win,
                                    pos = (0,-200),
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30)}

rating_stim["Pain"].marker.size = (30,30)
rating_stim["Pain"].marker.color = "yellow"
rating_stim["Pain"].validArea.size = (660,100)

rating_stim["Calibration"].marker.size = (30,30)
rating_stim["Calibration"].marker.color = "yellow"
rating_stim["Calibration"].validArea.size = (660,100)

rating_stim["Expectancy"].marker.size = (30,30)
rating_stim["Expectancy"].marker.color = "yellow"
rating_stim["Expectancy"].validArea.size = (660,100)


pain_rating = rating_stim["Pain"]
calib_rating = rating_stim["Calibration"]
exp_rating = rating_stim["Expectancy"]

# text stimuli
instructions_text = {
    "welcome": "Welcome to the experiment! Please read the following instructions carefully.", 
    "TENS_introduction": "This experiment aims to investigate the effects of Transcutaneous Electrical Nerve Stimulation (TENS) on pain sensitivity. Different frequencies of TENS may be able to increase pain sensitivity by amplifying the pain signals that travel up your arm and into your brain.\n\n\
        The TENS itself is not painful, but you will feel a small sensation when it is turned on. Today we are testing the effects of monopolar and bipolar frequencies.",
    "calibration" : "Firstly, we are going to calibrate the pain intensity for the shocks you will receive in the experiment without TENS. As this is a study about pain, we want you to feel a moderate bit of pain, but nothing unbearable. \
The machine will start low, and then will gradually work up. We want to get to a level which is painful but tolerable, so roughly at a rating of around 7 out of 10, where 1 is not painful and 10 is very painful.\n\n\
After each shock you will be asked if that level was ok, and you will be given the option to either try the next level or set the current shock level for the experiment. You can always come back down if it becomes too uncomfortable!\n\n\
Please ask the experimenter if you have any questions at anytime.",
    "calibration_finish": "Thank you for completing the calibration, your maximum shock intensity has now been set.",
    "experiment" : "We can now begin the experiment. \n\n\
You will now receive a series of electrical shocks and your task is to rate the intensity of the pain caused by each shock on a rating scale. \
This rating scale ranges from NOT PAINFUL to VERY PAINFUL. \n\n\
All shocks will be signaled by a 10 second countdown. The shock will occur when an X appears, similarly as in the calibration procedure. \
On TENS trials, you will be given the choice between receiving monopolar or bipolar frequencies of TENS. Please use your mouse to select your choice. \
As you are waiting for the shock during the countdown, you will also be asked to rate how painful you expect the following shock to be. After each trial there will be a brief interval to allow you to rest between shocks. The task should take roughly 20 minutes. \n\n\
Please ask the experimenter if you have any questions now before proceeding.",
    "continue" : "\n\nPress spacebar to continue",
    "end" : "This concludes the experiment. Please ask the experimenter to help remove the devices.",
    "termination" : "The experiment has been terminated. Please ask the experimenter to help remove the devices."
}

cue_demo_text = "When you are completely relaxed, press any key to start the next block..."

response_instructions = {
    "Pain": "How painful was the shock?",
    "Expectancy": "How painful do you expect the next shock to be?",
    "Shock": "Press spacebar to activate the shock",
    "Shock_check": "Would you like to try the previous level of shock again?",
    "Check": "Please indicate whether you would like to try the next level of shock, stay at this level, or go back to the previous level for the experiment.",
    "Check_lvl1": "Please indicate whether you would like to try the next level of shock or stay at this level",
    "Check_max": "Note that this is the maximum level of shock.\n\n\
 Would you like to stay at this level or go down a level?",
    "Choice": "Please choose which frequency of TENS you want to receive on this trial."
                         }

pain_text = visual.TextStim(win,
            text=response_instructions["Pain"],
            height = 35,
            pos = (0,-100),
            )

exp_text = visual.TextStim(win,
            text=response_instructions["Expectancy"],
            height = 35,
            pos = (0,-100)
            ) 
# pre-draw countdown stimuli (numbers 10-1)
countdown_text = {}
for i in range(0,11):
    countdown_text[str(i)] = visual.TextStim(win, 
                            color="white", 
                            height = 50,
                            text=str(i))
    
# Define button_text and buttons dictionaries
button_text = {
    "calibration": {
    "Next": visual.TextStim(win,
                            text="Try the next shock level",
                            color="white",
                            height=25,
                            pos=(400, -300),
                            wrapWidth=300
                            ),                            
    "Stay": visual.TextStim(win,
                            text="Stay at this shock level",
                            color="white",
                            height=25,
                            pos=(0, -300),
                            wrapWidth=300),
    "Previous": visual.TextStim(win,
                            text="Set the previous shock level",
                            color="white",
                            height=25,
                            pos=(-400, -300),
                            wrapWidth=300),
        },
    "TENS": {
        TENS1_name: visual.TextStim(win,
                    text=TENS1_name,
                    color="white",
                    height=25,
                    pos=(400, -300),
                    wrapWidth=300   
                    ),            
        TENS2_name: visual.TextStim(win,
                    text=TENS2_name,
                    color="white",
                    height=25,
                    pos=(-400, -300),
                    wrapWidth=300   
                    ),        
    },
    "confirm": {    
        "Yes": visual.TextStim(win,
                    text="Yes",
                    color="white",
                    height=25,
                    pos=(400, -300),
                    wrapWidth=300   
                    ),     
        "No": visual.TextStim(win,
                        text="No",
                        color="white",
                        height=25,
                        pos=(-400, -300),
                        wrapWidth=300) 
    }
}

buttons = {
    "calibration": {
            "Next": visual.Rect(win,
                        width=300,
                        height=80,
                        fillColor="black",
                        lineColor="white",
                        pos=(400, -300)),
            "Stay": visual.Rect(win,
                                width=300,
                                height=80,
                                fillColor="black",
                                lineColor="white",
                                pos=(0, -300)),
            "Previous": visual.Rect(win,
                            width=300,
                            height=80,
                            fillColor="black",
                            lineColor="white",
                            pos=(-400, -300)),
    },
    "TENS": {
        "left": visual.Rect(win,
                    width=300,
                    height=80,
                    fillColor="black",
                    lineColor="white",
                    pos=(400, -300)),  
        "right": visual.Rect(win,
                    width=300,
                    height=80,
                    fillColor="black",
                    lineColor="white",
                    pos=(-400, -300)),
    },
    "confirm": {
                "Yes": visual.Rect(win,
                        width=300,
                        height=80,
                        fillColor="black",
                        lineColor="white",
                        pos=(400, -300)), 
        "No": visual.Rect(win,
                        width=300,
                        height=80,
                        fillColor="black",
                        lineColor="white",
                        pos=(-400, -300)),
        }

}

calib_finish = False

#### Make trial functions
    # calibration trials
def show_calib_trial(trial_order):
    trial_index = 0
    global calib_finish
    previous_trial = False
    termination_check()

    while 0 <= trial_index < len(calib_trial_order) and not calib_finish:
        current_trial = trial_order[trial_index]
        if previous_trial == True:
            visual.TextStim(win,
                text=response_instructions["Shock_check"],
                height = 35,
                pos = (0,0),
                wrapWidth= 800
                ).draw()
            buttons_keylist = ["Yes", "No"]
            for button_name in buttons_keylist:
                buttons["confirm"][button_name].draw()
                button_text["confirm"][button_name].draw()
            mouse = event.Mouse()
            mouse.clickReset()
            win.flip()
            
            choice_finish = False
            termination_check()
            mouse.clickReset()
            
            while choice_finish == False:
                for button_name in buttons_keylist:
                        if mouse.isPressedIn(buttons["confirm"][button_name]):
                            if button_name == "Yes":
                                choice_finish = True
                                previous_trial = False
                                wait(iti)
                                break
                            elif button_name == "No":
                                choice_finish = True
                                calib_finish = True
                                wait(iti)
                                return
            
        # Wait for participant to ready up for shock
        visual.TextStim(win,
            text=response_instructions["Shock"],
            height = 35,
            pos = (0,0),
            wrapWidth= 800
            ).draw()
        
        win.flip()
        event.waitKeys(keyList = ["space"])
        
        # show fixation stimulus + deliver shock
        if pport != None:
            pport.setData(0)

        fix_stim.draw()
        win.flip()
        
        if pport != None:
            pport.setData(shock_trig["high"])
            wait(port_buffer_duration)
            pport.setData(0)
        
        # Get pain rating
        while calib_rating.getRating() is None: # while mouse unclicked
            termination_check()
            pain_text.draw()
            calib_rating.draw()
            win.flip()
            
        pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
        
        while core.getTime() < pain_response_end_time:
            termination_check()
            pain_text.draw()
            calib_rating.draw()
            win.flip()

        current_trial["pain_response"] = calib_rating.getRating()
        calib_rating.reset()
        win.flip()
        wait(iti)

        # Feedback text
        if shock_trig["high"] == 1:
            text = response_instructions["Check_lvl1"]
        elif shock_trig["high"] < 10:
            text = response_instructions["Check"]
        else:
            text = response_instructions["Check_max"]

        visual.TextStim(win, text=text, height=35, pos=(0, 0)).draw()

        # Draw buttons and text
        if shock_trig["high"] == 1:
            buttons_keylist = ["Next", "Stay"]
        elif shock_trig["high"] == 10:
            buttons_keylist = ["Previous", "Stay"]
        else:
            buttons_keylist = buttons["calibration"].keys()

        for button_name in buttons_keylist:
            buttons["calibration"][button_name].draw()
            button_text["calibration"][button_name].draw()

        win.flip()
        
        # Wait for a mouse click
        trial_finish = False
        mouse = event.Mouse()
        mouse.clickReset()
        
        while trial_finish == False:
            for button_name, button_rect in buttons["calibration"].items():
                if mouse.isPressedIn(button_rect):
                    if button_name == "Next":
                        shock_trig["high"] += 1
                        shock_trig["low"] += 1
                        shock_trig["medium"] += 1
                        trial_index += 1
                        
                    elif button_name == "Stay":
                        calib_finish = True
                        
                    elif button_name == "Previous":
                        shock_trig["high"] -= 1
                        shock_trig["low"] -= 1
                        shock_trig["medium"] -= 1
                        trial_index -= 1
                        previous_trial = True
    
                    trial_finish = True
                    mouse.clickReset()                        
        win.flip()
        wait(iti)

def show_trial(current_trial):
    if pport != None:
        pport.setData(0)
        
    win.flip()
    
    #If TENS trial, ask for choice:
    
    if current_trial["choicetrial"] == True:
        buttons["TENS"]["left"].draw()
        buttons["TENS"]["right"].draw()
        buttons_keylist = TENS_names
        for button_name in buttons_keylist:
            button_text["TENS"][button_name].draw()
        visual.TextStim(win,
                text=response_instructions["Choice"],
                height = 35,
                pos = (0,0),
                ).draw()
        
        win.flip()

        choice_finish = False
        mouse = event.Mouse()

        while choice_finish == False:
            termination_check()
            for button_name, button_rect in buttons["TENS"].items():
                if mouse.isPressedIn(button_rect):
                    if button_name == TENS_outcomes["optimal"]:
                        current_trial["stimulus"] = "TENS"
                        current_trial["choice_response"] = TENS_outcomes["optimal"]
                        current_trial["outcome"] = "medium"
                        choice_finish = True
                    elif button_name == TENS_outcomes["suboptimal"]:
                        current_trial["stimulus"] = "TENS"
                        current_trial["choice_response"] = TENS_outcomes["suboptimal"]
                        current_trial["outcome"] = outcome_randomise(
                            "high",
                            "low",
                            current_trial["rft_schedule"])
                        choice_finish = True

        
    # Start countdown to shock
    
    # Make a count-down screen
    countdown_timer = core.CountdownTimer(10)  # Set the initial countdown time to 10 seconds
  
    while countdown_timer.getTime() > 8:
        termination_check()
        countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
        win.flip()
        
    while countdown_timer.getTime() < 8 and countdown_timer.getTime() > 7: #turn on TENS at 8 seconds
        termination_check()
        if pport != None and current_trial["choicetrial"] == True:
            termination_check()
            for time, port in TENS_pulse_patterns[current_trial["choice_response"]]:
                if abs(countdown_timer.getTime() - math.floor(countdown_timer.getTime()) - time) < timer_precision_range:
                    pport.setData(port)
        countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
        win.flip()

    while countdown_timer.getTime() < 7 and countdown_timer.getTime() > 0: #ask for expectancy at 7 seconds
        if pport != None and current_trial["choicetrial"] == True:
            termination_check()
            for time, port in TENS_pulse_patterns[current_trial["choice_response"]]:
                if abs(countdown_timer.getTime() - math.floor(countdown_timer.getTime()) - time) < timer_precision_range:
                    pport.setData(port)

        countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
        
        # Ask for expectancy rating
        exp_text.draw() 
        exp_rating.draw()
        win.flip()    

    current_trial["exp_response"] = exp_rating.getRating() #saves the expectancy response for that trial
    exp_rating.reset() #resets the expectancy slider for subsequent trials
        
    # deliver shock
    if pport != None:
        pport.setData(0)
    fix_stim.draw()
    win.flip()
    
    if pport != None:
        pport.setData(shock_trig[current_trial["outcome"]])
        
    wait(port_buffer_duration)

    if pport != None:
        pport.setData(0)

    # Get pain rating
    while pain_rating.getRating() is None: # while mouse unclicked
        termination_check()
        pain_rating.draw()
        pain_text.draw()
        win.flip()
            
            
    pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
    
    while core.getTime() < pain_response_end_time:
        termination_check()
        pain_text.draw()
        pain_rating.draw()
        win.flip()
        
    current_trial["pain_response"] = pain_rating.getRating()
    pain_rating.reset()

    win.flip()
    
    wait(iti)

exp_finish = False


# Run experiment
while not exp_finish:
    termination_check()
    #display welcome and calibration instructions
    # instruction_trial(instructions_text["welcome"],3)
    # instruction_trial(instructions_text["TENS_introduction"],3)
    # instruction_trial(instructions_text["calibration"],8)
    
    # show_calib_trial(calib_trial_order)
    
    # instruction_trial(instructions_text["calibration_finish"],3)
    
    # #display main experiment phase
    instruction_trial(instructions_text["experiment"],10)
    for trial in trial_order:
        show_trial(trial)

    pport.setData(0) # Set all pins to 0 to shut off TENS, shock etc.    
    # # save trial data
    save_data(trial_order)
    exit_screen(instructions_text["end"])
    
    exp_finish = True
    
win.close()