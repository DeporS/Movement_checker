import RPi.GPIO as GPIO
import gpiozero

import time
import vlc
import threading
import subprocess

buzzer = gpiozero.Buzzer(17)


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

TIME_TO_WAIT = 20


matrix = [["1","2","3","A"],
            ["4","5","6","B"],
            ["7","8","9","C"],
            ["*","0","#","D"]]
# ===== global variables end =====

# function to update timeout state
def updateTimeoutState():
    print("TIMEOUT")
    globalState.isTimedOut = True
    return


def beep_for_ms(miliseconds):
    buzzer.on()
    time.sleep(miliseconds / 1000)
    buzzer.off()


def success_beep():
    beep_for_ms(500)

def getChar() -> str:
    while not globalState.isTimedOut:
        for i, line in enumerate([L1, L2, L3, L4]):
            GPIO.output(line, GPIO.HIGH)
            for j, row in enumerate([C1, C2, C3, C4]):
                if GPIO.input(row) == GPIO.HIGH:
                    while(GPIO.input(row) == GPIO.HIGH):
                        pass
                    GPIO.output(line, GPIO.LOW)
                    beep_for_ms(100)
                    return matrix[i][j]
            GPIO.output(line, GPIO.LOW)
        time.sleep(0.1)

    print("TIMEOUT1")
    return "%" 


def play_sound(name):
    name = "sounds/" + name
    if not name.endswith(".wav"):
        name += ".wav"
    musicPlayerLock.acquire()
    subprocess.Popen(["mplayer", name])
    time.sleep(1)
    musicPlayerLock.release()

# returns true if alarm was turned off correctly
def handleMoveOnEntry() -> str:
    keyStr = ""
    while not globalState.isTimedOut:
        print("waiting for password in handleMoveOnEntry")
        newChar = getChar()
        if globalState.isTimedOut:
            print("TIMEOUT2")
            return ""
        print(newChar)
        

        # clear input 
        if newChar == "C":
            keyStr = ""
            continue

        if newChar != "#":
            keyStr += newChar
            continue

        if newChar == "#":
            return keyStr

    # time ended
    print("time ended")
    return ""


def handleWrongPasswordInRoom(password) -> bool:
    atempts = 0
    maxAtempts = 5
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
            if len(keyStr) > len(password) + 1:
                return False
            continue
        
        # need to check if password is correct
        if keyStr == password:
            print("correct password in handleWrongPasswordInRoom")
            success_beep()
            play_sound("poprawnie_zalogowano.wav")
            return True

        # wrong password
        else:
            print("wrong password in handleWrongPasswordInRoom")
            play_sound("bledne_haslo.wav")
            atempts += 1
            if atempts >= maxAtempts:
                lockedOnTooManyAttemptsOrWrongID()
                atempts = 0
            keyStr = ""
            continue

def monitorRoomProcess():
    atempts = 0
    maxAtempts = 5

    while True:
        pir.wait_for_motion()
        print("You moved")
        if not globalState.isAlarmArmed:
            
            # wait for '*' to arm the alarm
            while not globalState.isAlarmArmed:
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
        play_sound("wykryto_ruch_prosze.wav")
        globalState.isTimedOut = False
        timer = threading.Timer(TIME_TO_WAIT, updateTimeoutState)
        timer.start()

        person_id = handleMoveOnEntry() # blocks for TIME_TO_WAIT seconds
        
        if person_id != "" and person_id.isnumeric():
            password = server.get_password_by_id(int(person_id))
            if password == "":
                print("wrong person id")
                timer.cancel()
                server.insertDate(2)
                play_sound("nie_ma_pracownika_o.wav")
                atempts += 1
                if atempts >= maxAtempts:
                    lockedOnTooManyAttemptsOrWrongID()
                    atempts = 0
                continue

            input_pass = handleMoveOnEntry() # block and wait for password
            if password == input_pass:
                timer.cancel()
                globalState.isAlarmArmed = False
                print("alarm disabled")
                server.insertDate(1, person_id)
                play_sound("poprawnie_zalogowano.wav")
                success_beep()
                atempts = 0
                continue
            else:
                print("wrong password")
                atempts += 1
                timer.cancel()
                if atempts >= maxAtempts:
                    lockedOnTooManyAttemptsOrWrongID()
                    atempts = 0

        if person_id == "" or not person_id.isnumeric():
            print("time ended")
            timer.cancel()
            atempts += 1
            if atempts >= maxAtempts:
                lockedOnTooManyAttemptsOrWrongID()
                atempts = 0
            continue
        



        # alarm was not disabled
        print("alarm was not disabled")
        play_sound("bledne_haslo.wav")
        server.insertDate(0)

        timer.cancel()
        globalState.isTimedOut = False
        globalState.isPlayerOn = True
        globalState.isAlarmSounding = True
        musicPlayerLock.acquire()
        # globalState.player.play()
        musicPlayerLock.release()

        # blocks until password is entered
        handleWrongPasswordInRoom(password)

        globalState.isPlayerOn = False
        musicPlayerLock.acquire()
        # globalState.player.pause()
        musicPlayerLock.release()
        globalState.isAlarmSounding = False
        globalState.isAlarmArmed = False



def lockedOnTooManyAttemptsOrWrongID():
    print("lockedOnTooManyAttempts")
    globalState.isTimedOut = False

    globalState.isAlarmArmed = True
    globalState.isPlayerOn = True
    globalState.isAlarmSounding = True
    musicPlayerLock.acquire()
    # globalState.player.play()
    musicPlayerLock.release()
    
    # wait for server restart
    while globalState.isAlarmSounding:
        # alarm beep
        beep_for_ms(500)
        time.sleep(0.5)

    globalState.isPlayerOn = False
    musicPlayerLock.acquire()
    # globalState.player.pause()
    musicPlayerLock.release()
    globalState.isAlarmSounding = False
    globalState.isAlarmArmed = False



def main():
    try:
        server.dropDatabase()
        server.init_db()
        print(f'start first thread')
        t1 = threading.Thread(target=server.runApp).start()
        print(f'start second thread')
        t2 = threading.Thread(target=monitorRoomProcess).start()

    except KeyboardInterrupt:
        print("\nApplication stopped!")


if __name__ == '__main__':
    main()