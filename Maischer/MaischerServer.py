import asyncio
import websockets
import glob, os
import json
import sqlite3
import threading
import time
import RPi.GPIO as GPIO
from sqlite3 import Error
import random

class ServoHandler():
    def __init__(self,servoPIN):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(servoPIN, GPIO.OUT)

        self.p = GPIO.PWM(servoPIN, 50) # GPIO xx for PWM with 50Hz
        self.p.start(2.5) # Initialization       
        self.setDutyCyle(1) 

    def setDutyCyle(self,cycle):
        self.p.ChangeDutyCycle(cycle)
        time.sleep(1)
        self.p.ChangeDutyCycle(0) #To stop the trembling

    def setAngle(self,angle):
        if angle < 0 or angle > 180:
            return False

        dutyCycle = angle / (180 / 11)
        print("setDutyCycle " + str(dutyCycle))
        self.setDutyCyle(dutyCycle)
        return True

class MaischerServer():
    def __init__(self):
        self.setPoint = 0.0
        self.Temperatuur = 0.0
        self.servoAngle = 0
        self.MinOutputAngle = 1
        self.MaxOutputAngle = 180
        self.servo = ServoHandler(23) # Pin number

        self.thread = threading.Thread(target=self.run, args=())
        self.runGetTempThread = True
        self.thread.start() # Start the execution
    
    def __del__(self):
        self.runGetTempThread = False

    def ReadDS18B20(self, sensorid):
        tfile = open("/sys/bus/w1/devices/"+ sensorid +"/w1_slave") #RPi 2,3 met nieuwe kernel.
        text = tfile.read()
        tfile.close()
     
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        temp = temperature / 1000

        print "sensor", sensorid, "=", temp, "graden."
        return temp   

    def run(self):
        while(self.runGetTempThread):
            averageTemp = 0.0
            for _ in range(10):
                averageTemp += self.ReadDS18B20("28-000008717fea")
                time.sleep(0.1)

            self.Temperatuur = averageTemp / 10

    @asyncio.coroutine
    def wsServer(self, websocket, path):
        command = yield from websocket.recv()
        print ('Received command:' + command)
        if command == 'GetSetPoint':
            jsonDict = { "Command" : command,
                         "SetPoint" : str(self.setPoint)}
            yield from websocket.send(json.dumps(jsonDict))
        elif 'SetTemperatuur' in command:
            receivedSetPoint = float(command.split(' ')[1])
            if receivedSetPoint < 0:
                receivedSetPoint = 0
            if receivedSetPoint > 100:
                receivedSetPoint = 100

            self.setPoint = receivedSetPoint
            jsonDict = { "Command" : command,
                         "SetPoint" : str(self.setPoint)}
            yield from websocket.send(json.dumps(jsonDict))

        ####################################################
        ## Process Value
        elif command == 'GetTemperatuur':
            jsonDict = { "Command" : command,
                         "ProcessValue" : str(self.Temperatuur)}
            yield from websocket.send(json.dumps(jsonDict))

        ####################################################
        ## Servo Angle
        elif 'GetServoAngle' in command:
            jsonDict = { "Command" : command,
                         "ServoAngle" : str(self.servoAngle)}
            yield from websocket.send(json.dumps(jsonDict))

        elif 'SetServoAngle' in command:
            self.servoAngle = float(command.split(' ')[1])
            valid = self.servo.setAngle(self.servoAngle)

            jsonDict = { "Command" : command,
                         "Valid"   : str(valid),
                         "ServoAngle" : str(self.servoAngle)}
            yield from websocket.send(json.dumps(jsonDict))            
        ####################################################
        ## Output
        elif 'SetMinOutputAngle' in command:
            self.MinOutputAngle = float(command.split(' ')[1])
            jsonDict = { "Command" : command,
                         "MinOutputAngle" : str(self.MinOutputAngle)}
            yield from websocket.send(json.dumps(jsonDict))
        
        elif 'SetMaxOutputAngle' in command:
            self.MaxOutputAngle = float(command.split(' ')[1])
            jsonDict = { "Command" : command,
                         "MaxOutputAngle" : str(self.MaxOutputAngle)}
            yield from websocket.send(json.dumps(jsonDict))

        elif 'SetOutput' in command:
            output = float(command.split(' ')[1])
            if output < 0:
                output = 0
            if output > 100:
                output = 100

            self.output = output

            step = float(self.MaxOutputAngle) - float(self.MinOutputAngle) 
            step = step / 100
            outputServoAngle = self.MinOutputAngle + (step * output)
            valid = self.servo.setAngle(outputServoAngle)            

            jsonDict = { "Command" : command,
                         "Output" : str(self.output)}
            yield from websocket.send(json.dumps(jsonDict))

if __name__ == "__main__":
    MaischerServer = MaischerServer()
    start_server = websockets.serve(MaischerServer.wsServer, '0.0.0.0', 7654)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
