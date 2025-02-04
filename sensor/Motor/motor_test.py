import motor
import RPi.GPIO as GPIO
import time 

GPIO.setwarnings(False)
Motor1 = motor.motor(6,5,13)
Motor2 = motor.motor(20,16,12)

try:
    print("motor run") 
#     Motor1.go(100)
#     Motor2.go(100)
#     Motor1.back(80)
#     Motor2.go(80)
#     time.sleep(0.5)

    for i in range(5,11):
        Motor1.go(i*10)
        Motor2.go(i*10-(3*i/7))
        time.sleep(0.5)

    time.sleep(5)

    for i in [10,9,8,7,6,5]:
        Motor1.go(i*10)
        Motor2.go(i*10-(3*i/7))
        time.sleep(0.5)
    Motor1.stop()
    Motor2.stop()
#     Motor2.go(100-(3*10/7))
#     time.sleep(10)

    #Motor.back(100)
    #time.sleep(3)
    print("motor stop")
    time.sleep(1)
except KeyboardInterrupt:
    Motor1.stop()
    Motor2.stop()
    time.sleep(1)
    GPIO.cleanup()
    

GPIO.cleanup()

