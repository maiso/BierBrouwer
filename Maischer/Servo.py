import RPi.GPIO as GPIO

class ServoHandler():
    def __init__(self,servoPIN):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(servoPIN, GPIO.OUT)

        self.p = GPIO.PWM(servoPIN, 50) # GPIO xx for PWM with 50Hz
        self.p.start(2.5) # Initialization       
        self.setDutyCyle(1) 

    def setDutyCyle(self,cycle):
        self.p.ChangeDutyCycle(cycle)
        #time.sleep(1)
        #self.p.ChangeDutyCycle(0) #To stop the trembling

    def setAngle(self,angle):
        if angle < 0 or angle > 180:
            return False

        dutyCycle = angle / (180 / 11)
        print("setDutyCycle " + str(dutyCycle))
        self.setDutyCyle(dutyCycle)
        return True