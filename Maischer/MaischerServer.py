import asyncio
import websockets
import glob, os
import json
import sqlite3
import threading
import time
import datetime
#import RPi.GPIO as GPIO

from sqlite3 import Error
import random
import PID
from DatabaseInterface import DatabaseInterface
from stepperMotor import stepperMotor

databaseName = 'BierBrouwer.db'

#class ServoHandler():
    # def __init__(self,servoPIN):
    #     GPIO.setmode(GPIO.BCM)
    #     GPIO.setup(servoPIN, GPIO.OUT)

    #     self.p = GPIO.PWM(servoPIN, 50) # GPIO xx for PWM with 50Hz
    #     self.p.start(2.5) # Initialization       
    #     self.setDutyCyle(1) 

    # def setDutyCyle(self,cycle):
    #     self.p.ChangeDutyCycle(cycle)
    #     #time.sleep(1)
    #     #self.p.ChangeDutyCycle(0) #To stop the trembling

    # def setAngle(self,angle):
    #     if angle < 0 or angle > 180:
    #         return False

    #     dutyCycle = angle / (180 / 11)
    #     print("setDutyCycle " + str(dutyCycle))
    #     self.setDutyCyle(dutyCycle)
    #     return True

class MaischerServer():
    def __init__(self):
        self.setPoint = float(0.0)
        self.Temperature = 0.0
        self.servoAngle = 0

        #self.config = self.Configuration()

        self.db = DatabaseInterface(databaseName)

        self.PID_Output = 0
        self.outputPV = 0
        self.regelaarActive = False

        #self.servo = ServoHandler(23) # Pin number

        #self.pid = PID.PID(self.P, self.I, self.D)
        #self.pid.SetPoint = self.setPoint
        #self.pid.setSampleTime(1)

        #self.thread = threading.Thread(target=self.run, args=())
        #self.runGetTempThread = True
        #self.thread.start() # Start the execution
    
    def __del__(self):
        self.runGetTempThread = False

    class Configuration():
        def __init__(self):
            self.Servo = self.Servo()
            self.PID = self.PID()
            self.DS18B20 = "28-000008717fea"

        class PID():
            def __init__(self):
                self.P = 10
                self.I = 1
                self.D = 1
        class StepperMotor():
            def __init__(self):
                self.MaxNrOfSteps = 0

    class Measurement():
        def __init__(self):
            self.Date
            self.Temperature
            self.SetPoint
            self.PidOutput

    def setOutput(self,output):
        step = float(self.MaxOutputAngle) - float(self.MinOutputAngle) 
        step = step / 100
        self.servoAngle = self.MinOutputAngle + (step * output)
        valid = self.servo.setAngle(self.servoAngle) 

    def ReadDS18B20(self, sensorid):
        tfile = open("/sys/bus/w1/devices/"+ sensorid +"/w1_slave") #RPi 2,3 met nieuwe kernel.
        text = tfile.read()
        tfile.close()
     
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        temp = temperature / 1000

        return temp   

    def run(self):
        prevOutputPv = -1
        while(self.runGetTempThread):
            self.Temperature = self.ReadDS18B20("28-000008717fea")
            if self.regelaarActive == True:
                self.pid.update(float(self.Temperature))

                self.PID_Output = self.pid.output
                self.outputPV  = max(min( int(self.PID_Output), 100 ),0)
                if self.outputPV != prevOutputPv:
                    self.setOutput(self.outputPV)
                else:
                    self.servo.setAngle(0) # if it hasn't changed stop the trembling of the servo

                prevOutputPv = self.outputPV
#                print ( "Target: %.1f C | Current: %.1f C | OutputPV: %d" % (self.setPoint, self.Temperature, self.outputPV))
            time.sleep(1)

    @asyncio.coroutine
    def wsServer(self, websocket, path):
        json_string = yield from websocket.recv()
        print ('Received JSON:' + json_string)

        parsed_json = json.loads(json_string)

        commandHandlers = {
            'GetBrewages'      : self.handleGetBrewages,
            'OpenBrewage'      : self.handleOpenBrewage,
            'SetTemperature'   : self.handleSetTemperature,
            'SetConfiguration' : self.handleSetConfiguration,
            'GetMeasurement'   : self.handleGetMeasurement,
            'StartStop'        : self.handleStartStop,
        }
        #try:
        result_json = commandHandlers[parsed_json['Command']](parsed_json)
        print("Sending to client: " + str(result_json))
        yield from websocket.send(json.dumps(result_json))
     #   except Exception as e:
      #      print('Exception :' + str(e))

    def commandOkJson(self, command):
        jsonDict = { "Command" : command,
                     "Result"  : 'Ok'}
        return jsonDict
    
    def handleGetBrewages(self, parsed_json):
        brewages = self.db.getAllBrewages()
        jsonDict = self.commandOkJson(parsed_json['Command'])
        brewagesList = []
        for row in brewages:
            brewagesList.append(row["BrewName"])
        jsonDict["Brewages"] = brewagesList
        return jsonDict

    def handleOpenBrewage(self, parsed_json):
        brewages = self.db.getBrewage(parsed_json['Brewage'])
        jsonDict = self.commandOkJson(parsed_json['Command'])
        jsonDict = {**jsonDict, **brewages}

        return jsonDict

    def handleSetTemperature(self, parsed_json):
        receivedSetPoint = float(command.split(' ')[1])
        if receivedSetPoint < 0:
            receivedSetPoint = 0
        if receivedSetPoint > 100:
            receivedSetPoint = 100

        self.setPoint = receivedSetPoint
        self.pid.SetPoint = self.setPoint
        jsonDict = { "Command" : command,
                     "Result"  : 'Ok',
                     "SetPoint" : str(self.setPoint)}
        return jsonDict

    def handleGetMeasurement(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        jsonDict += { "Temperature" : str(self.Temperature),
                     "ServoAngle" : str(self.servoAngle),
                     "OutputPV" : str(self.outputPV)
                   }
        return jsonDict

    def handleSetConfiguration(self, parsed_json):
        ConfigId = parsed_json['Configuration']['ConfigurationId']
        ConfigName = parsed_json['Configuration']['ConfigurationName']
        ConfigP = parsed_json['Configuration']['P']
        ConfigI = parsed_json['Configuration']['I']
        ConfigD = parsed_json['Configuration']['D']
        ConfigNrOfSteps = parsed_json['Configuration']['NrOfSteps']

        self.db.updateConfiguration(ConfigId,ConfigName,ConfigP,ConfigI,ConfigD,ConfigNrOfSteps)
        self.P = float(ConfigP)
        self.I = float(ConfigI)
        self.D = float(ConfigD)

        #self.pid.setKp (self.P)
        #self.pid.setKi (self.I)
        #self.pid.setKd (self.D)

        jsonDict = self.commandOkJson(parsed_json['Command'])
        newConfig = self.db.getConfiguration(ConfigId)
        jsonDict = {**jsonDict, **newConfig}
        return jsonDict

    def handleCalibration(self,parsed_json):
        valid = self.servo.setAngle(self.servoAngle)
        jsonDict = { "Command" : command,
                     "Valid"   : str(valid),
                     "ServoAngle" : str(self.servoAngle)}
        return jsonDict

    def handleStartStop(self, parsed_json):
        self.regelaarActive = parsed_json['Start']
        jsonDict = { "Command" : command,
                     "Start"   : self.regelaarActive }
        return jsonDict

if __name__ == "__main__":
    MaischerServer = MaischerServer()
    start_server = websockets.serve(MaischerServer.wsServer, '0.0.0.0', 7654)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
