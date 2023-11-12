import RPi.GPIO as GPIO
import gpiozero

import time
import vlc
import threading

# our server impl
import server

# ===== global variables =====
from State import * 

# ===== keypad setup =====
L1 = 5
L2 = 6
L3 = 13
L4 = 19

C1 = 12
C2 = 16
C3 = 20
C4 = 21

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# ===== keypad setup end =====


pir = gpiozero.MotionSensor(4)

TIME_TO_WAIT = 10


matrix = [["1","2","3","A"],
            ["4","5","6","B"],
            ["7","8","9","C"],
            ["*","0","#","D"]]
# ===== global variables end =====

# function to update timeout state
def updateTimeoutState():
    print("TIMEOUUUUUT")
    time.sleep(5)
    globalState.isTimedOut = True
    return


def getChar() -> str:
    while not globalState.isTimedOut:
        for i, line in enumerate([L1, L2, L3, L4]):
            GPIO.output(line, GPIO.HIGH)
            for j, row in enumerate([C1, C2, C3, C4]):
                if GPIO.input(row) == GPIO.HIGH:
                    while(GPIO.input(row) == GPIO.HIGH):
                        pass
                    GPIO.output(line, GPIO.LOW)
                    return matrix[i][j]
            GPIO.output(line, GPIO.LOW)
        time.sleep(0.1)

    print("TIMEOUT1")
    return "%" 

# returns true if alarm was turned off correctly
def handleMoveOnEntry() -> bool:
    keyStr = ""
    while not globalState.isTimedOut:
        print("waiting for password in handleMoveOnEntry")
        newChar = getChar()
        if globalState.isTimedOut:
            print("TIMEOUT2")
            time.sleep(5)
            return False
        print(newChar)
        

        # clear input 
        if newChar == "C":
            keyStr = ""
            continue

        if newChar != "#":
            print("here")
            keyStr += newChar
            if len(keyStr) > len(globalState.password) + 1:
                return False
            continue

        # need to check if password is correct
        if keyStr == globalState.password:
            print("correct password")
            return True

        # wrong password
        else:
            return False

    # time ended
    print("time ended")
    return False

def handleWrongPasswordInRoom() -> bool:
    keyStr = ""
    while globalState.isAlarmSounding:
        newChar = getChar()
        print(newChar)
        
        # clear input 
        if newChar == "C":
            keyStr = ""
            continue

        if newChar != "#":
            keyStr += newChar
            if len(keyStr) > len(globalState.password) + 1:
                return False
            continue
        
        # need to check if password is correct
        if keyStr == globalState.password:
            print("correct password in handleWrongPasswordInRoom")
            return True

        # wrong password
        else:
            print("wrong password in handleWrongPasswordInRoom")
            keyStr = ""
            continue

def monitorRoomProcess():
    while True:
        pir.wait_for_motion()
        print("You moved")
        if not globalState.isAlarmArmed:
            
            # wait for '*' to arm the alarm
            while True:
                print("waiting for *")
                newChar = getChar()
                print(newChar)
                if newChar == "*":
                    globalState.isAlarmArmed = True
                    break
            
            # 5 seconds to leave the room
            print("Alarm armed in 5 seconds")
            time.sleep(5)
            continue

        
        # start timer 
        globalState.isTimedOut = False
        timer = threading.Timer(TIME_TO_WAIT, updateTimeoutState)
        timer.start()

        wasDisabled = False
        wasDisabled = handleMoveOnEntry() # blocks for TIME_TO_WAIT seconds
        
        if wasDisabled and not globalState.isTimedOut:
            timer.cancel()
            globalState.isAlarmArmed = False
            print("alarm disabled")
            server.insertDate(1)
            continue
    
        # alarm was not disabled
        print("alarm was not disabled")
        server.insertDate(0)

        timer.cancel()
        globalState.isTimedOut = False
        globalState.isPlayerOn = True
        globalState.isAlarmSounding = True
        globalState.player.play()
        
        # blocks until password is entered
        handleWrongPasswordInRoom()

        globalState.isPlayerOn = False
        globalState.player.pause()
        globalState.isAlarmSounding = False
        globalState.isAlarmArmed = False


def main():
    try:
        server.dropDatabase()
        print(f'start first thread')
        t1 = threading.Thread(target=server.runApp).start()
        print(f'start second thread')
        t2 = threading.Thread(target=monitorRoomProcess).start()

    except KeyboardInterrupt:
        print("\nApplication stopped!")


if __name__ == '__main__':
    main()