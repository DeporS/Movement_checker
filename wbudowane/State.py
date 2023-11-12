import threading
# import vlc

# some state for comunicating between threads
class State:
    mainThreadShouldRun = True
    # player = vlc.MediaPlayer("sound.mp3")
    isAlarmArmed = True
    isAlarmSounding = False
    isPlayerOn = False
    password = "1234"
    isTimedOut = False
    def __init__(self) -> None:
        print("init State")

# lock when accessing global state 
# except for atomic read in loop - like runMainWorker does
globalStateLock = threading.Lock() 
globalState = State()