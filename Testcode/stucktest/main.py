#Last Update 2022/07/31
#Author : Toshiki Fukui

import RPi.GPIO as GPIO
from cansat import Cansat
import time

state = 9

cansat = Cansat(state)
cansat.setup()

try:
    while True:
        cansat.sensor()
        time.sleep(0.03)
        cansat.sequence()
        if cansat.state >= 10:
            print("Finished")
            cansat.keyboardinterrupt()
            GPIO.cleanup()
            break
    
except KeyboardInterrupt:
    print("Finished")
    cansat.keyboardinterrupt()
    GPIO.cleanup()