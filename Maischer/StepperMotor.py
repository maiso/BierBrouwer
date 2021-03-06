import threading

onPi = False
try:
	import RPi.GPIO as GPIO
	onPi = True
except ImportError:
	onPi = False

import time

class StepperMotor():
	def __init__(self):

		self.coilToPin = [14,15,23,24]
		self.steps = [ 
				[3,0] ,
				[3]   ,
				[2,3] ,
				[2]   ,
				[1,2] ,				
				[1]   ,
				[0,1] ,     #Coil 0 & 1
				[0]   ,		#Coil 0 only
				]
		self.currentStepSequence = 0
		self.anglePV = 0
		self.angleSP = 0
		self.currentStepNumber = 0
		self.maxStepNumber = None
		
		self.zeroHasBeenSet = False
		self.maxHasBeenSet  = False
		if onPi:
			GPIO.setmode(GPIO.BCM)
			GPIO.setwarnings(False)
			GPIO.setup(self.coilToPin[0],GPIO.OUT)
			GPIO.setup(self.coilToPin[1],GPIO.OUT)
			GPIO.setup(self.coilToPin[2],GPIO.OUT)
			GPIO.setup(self.coilToPin[3],GPIO.OUT)

		self.thread = threading.Thread(target=self.run, args=())
		self.runMotorControlThread = True
		self.thread.start() # Start the execution

	def __del__(self):
		self.runMotorControlThread = False

	def run(self):
		while(self.runMotorControlThread):
			if self.angleSP != self.anglePV and self.maxStepNumber != None:
				print('self.angleSP ' + str(self.angleSP) + ' self.anglePV ' + str(self.anglePV))
				if self.angleSP > self.anglePV:
					counterclockwise = False
				else:
					counterclockwise = True

				self.doStep(counterclockwise)

			else:
				time.sleep(0.2)

	def setMotorConfig(self, stepsPerRevolution):
		self.stepsPerRevolution = int(stepsPerRevolution) #((360/stepSize)*gearbox)
		self.stepsPerDegree = round(stepsPerRevolution/360)
		self.maxStepNumber = self.stepsPerRevolution * 360
		print ('self.stepsPerRevolution' + str(self.stepsPerRevolution))
		print ('self.stepsPerDegree' + str(self.stepsPerDegree))

	def zero(self):
		self.zeroHasBeenSet = True
		self.currentStepNumber = 0
		self.angleSP = 0 
		self.anglePV = 0

	def max(self):
		self.maxHasBeenSet = True
		self.maxStepNumber = self.currentStepNumber

	def setOutput(self,output):
		if output > 100:
			output = 100
		maxAngle = round(self.maxStepNumber / self.stepsPerDegree)
		self.angleSP = round((maxAngle / 100) * output)

	def doStep(self,counterclockwise):
		if counterclockwise == False:
			self.currentStepNumber = min(self.currentStepNumber + 1, self.maxStepNumber)

			self.currentStepSequence = self.currentStepSequence + 1
			if self.currentStepSequence > (len(self.steps) -1):
				self.currentStepSequence = 0
		else:
			self.currentStepNumber = max(self.currentStepNumber - 1,0)
			self.currentStepSequence = self.currentStepSequence - 1
			if self.currentStepSequence < 0:
				self.currentStepSequence =  (len(self.steps) -1)

		self.anglePV = round(self.currentStepNumber / self.stepsPerDegree)

		if onPi == True:
			pinsHigh = []
			for coils in self.steps[self.currentStepSequence]:
				ioToChange = self.coilToPin[coils]
				GPIO.output(ioToChange,GPIO.HIGH)
				pinsHigh.append(ioToChange)

			for ioPin in self.coilToPin:
				if not ioPin in pinsHigh:
					GPIO.output(ioPin,GPIO.LOW)
		time.sleep(0.003)
