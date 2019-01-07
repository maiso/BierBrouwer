import asyncio
import websockets
import glob, os
import json
import sqlite3
import threading
import time
import RPi.GPIO as GPIO
from sqlite3 import Error

class ServoHandler():
    def __init__(self,servoPIN):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(servoPIN, GPIO.OUT)

        self.p = GPIO.PWM(servoPIN, 50) # GPIO xx for PWM with 50Hz
        self.p.start(2.5) # Initialization       
        self.setDutyCyle(1) 

    def setDutyCyle(self,cycle):
        self.p.ChangeDutyCycle(cycle)
        time.sleep(0.1)
        self.p.ChangeDutyCycle(0) #To stop the trembling

    def setAngle(self,angle):
        if angle < 0 or angle > 180:
            return False

        dutyCycle = angle / (180 / 12.5)
        self.setDutyCyle(dutyCycle)
        return True

class MaischerServer():
    def __init__(self):
        self.setPoint = 0.0
        self.processValue = 0.0
        self.servoPosition = 0.0

        self.servo = ServoHandler(23) # Pin number

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start() # Start the execution
    
    def run(self):
        print ('Get the temperatuur')
        time.sleep(1)

    @asyncio.coroutine
    def wsServer(self, websocket, path):
        command = yield from websocket.recv()
        print ('Received command:' + command)
        if command == 'GetSetPoint':
            jsonDict = { "Command" : command,
                         "SetPoint" : str(self.setPoint)}
            yield from websocket.send(json.dumps(jsonDict))
        elif 'SetSetPoint' in command:
            self.setPoint = float(command.split(' ')[1])
            jsonDict = { "Command" : command,
                         "SetPoint" : str(self.setPoint)}
            yield from websocket.send(json.dumps(jsonDict))
        elif command == 'GetProcessValue':
            self.setPoint = float(command.split(' ')[1])
            jsonDict = { "Command" : command,
                         "SetPoint" : str(self.setPoint)}
            yield from websocket.send(json.dumps(jsonDict))
        elif 'SetServoAngle' in command:
            self.servoPosition = float(command.split(' ')[1])
            valid = self.servo.setAngle(self.servoPosition)

            jsonDict = { "Command" : command,
                         "Valid"   : str(valid),
                         "ServoAngle" : str(self.servoPosition)}
            yield from websocket.send(json.dumps(jsonDict))            

if __name__ == "__main__":
    MaischerServer = MaischerServer()
    start_server = websockets.serve(MaischerServer.wsServer, '0.0.0.0', 7654)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
