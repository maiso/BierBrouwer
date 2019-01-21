onPi = False
try:
	import RPi.GPIO as GPIO
	onPi = True
except ImportError:
	onPi = False

import time

class stepperMotor():
	def __init__(self):
		self.coilToPin = [14,15,23,24]
		self.steps = [ 
				[0]   ,		#Coil 0 only
				[0,1] ,     #Coil 0 & 1
				[1]   ,
				[1,2] ,
				[2]   ,
				[2,3] ,
				[3]   ,
				[3,0] ]
		self.currentStepSequence = 0
		if onPi:
			GPIO.setmode(GPIO.BCM)
			GPIO.setwarnings(False)
			GPIO.setup(self.coilToPin[0],GPIO.OUT)
			GPIO.setup(self.coilToPin[1],GPIO.OUT)
			GPIO.setup(self.coilToPin[2],GPIO.OUT)
			GPIO.setup(self.coilToPin[3],GPIO.OUT)

	def doStep(self):
		self.currentStepSequence = self.currentStepSequence + 1
		if self.currentStepSequence > (len(self.steps) -1):
			self.currentStepSequence = 0

		pinsHigh = []
		#print ("CurrentStep: " + str(self.currentStepSequence))
		for coils in self.steps[self.currentStepSequence]:
			if onPi:
				GPIO.output(self.coilToPin[coils],GPIO.HIGH)
			pinsHigh.append(self.coilToPin[coils])

		for pin in self.coilToPin:
			if not pin in pinsHigh:
				GPIO.output(pin,GPIO.LOW)
		time.sleep(0.001)

if __name__ == "__main__":
    print ("starting...")
    dateTime = time.strftime("%Y%m%d%H%M")
    print ('Today is: %s', dateTime)
    #try:
    motor = stepperMotor()
    
    while True:
    	for x in range(0, 64):
    		motor.doStep()
    	time.sleep(0.01)

