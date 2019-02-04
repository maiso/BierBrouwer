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
from StepperMotor import StepperMotor

databaseName = 'BierBrouwer.db'

class MaischerServer():
    def __init__(self):
        self.TemperatureSetPoint = float(0.0)
        self.Temperature = 0.0
        self.StepsPerRevolution = 0

        self.brewageId = None
        self.db = DatabaseInterface(databaseName)

        # self.db.createDefaultConfiguration()
        # self.db.createDefaultMashing()
        # self.db.createDefaultBrewage()

        self.P = 10
        self.I = 1
        self.D = 1

        self.PID_Output = 0
        self.outputPV = 0
        self.regelaarActive = False
        self.prevOutputPV = 0
        self.pid = PID.PID(self.P, self.I, self.D)
        self.pid.setSampleTime(1)

        self.motor = StepperMotor()

        self.thread = threading.Thread(target=self.run, args=())
        self.runGetTempThread = True
        self.thread.start() # Start the execution
    
    def __del__(self):
        self.runGetTempThread = False

    def ReadDS18B20(self, sensorid):
        temp = 0
        try:
            tfile = open("/sys/bus/w1/devices/"+ sensorid +"/w1_slave") #RPi 2,3 met nieuwe kernel.
            text = tfile.read()
            tfile.close()
        
            secondline = text.split("\n")[1]
            temperaturedata = secondline.split(" ")[9]
            temperature = float(temperaturedata[2:])
            temp = temperature / 1000
        except IOError:
            temp = 0
        return temp

    def run(self):
        prevOutputPv = -1
        dbInterface = DatabaseInterface(databaseName)

        while(self.runGetTempThread):
            self.Temperature = self.ReadDS18B20("28-000008717fea")
            #self.Temperature = self.Temperature +1
            #if self.Temperature > self.TemperatureSetPoint:
            #    self.Temperature = 0
            if self.regelaarActive == True:
                self.pid.setKp (self.P)
                self.pid.setKi (self.I)
                self.pid.setKd (self.D)                
                self.pid.SetPoint = self.TemperatureSetPoint

                self.pid.update(float(self.Temperature))

                self.PID_Output = self.pid.output
                self.outputPV  = max(min( int(self.PID_Output), 100 ),0)

                if self.prevOutputPV != self.outputPV:
                    self.motor.setOutput(self.outputPV) # Only change motor when changed

                dbInterface.insertMeasurement(self.brewageId,self.TemperatureSetPoint,self.Temperature,self.outputPV)
                self.prevOutputPV = self.outputPV 
#                print ( "Target: %.1f C | Current: %.1f C | OutputPV: %d" % (self.TemperatureSetPoint, self.Temperature, self.outputPV))
            time.sleep(1)

    @asyncio.coroutine
    def wsServer(self, websocket, path):
        json_string = yield from websocket.recv()
        print ('Received JSON:' + json_string)

        parsed_json = json.loads(json_string)

        commandHandlers = {
            'GetActiveBrew'    : self.handleGetActiveBrew,
            'GetAvailableSettings' : self.handleGetAvailableSettings,
            'OpenBrewage'      : self.handleOpenBrewage,
            'NewBrewage'       : self.handleNewBrewage,
            'GetConfiguration' : self.handleGetConfiguration,
            'SetConfiguration' : self.handleSetConfiguration,
            'GetMeasurement'   : self.handleGetMeasurement,
            'GetAllMeasurements' : self.handleGetAllMeasurements,
            'ControllerMode'   : self.handleControllerMode,
            'SetTemperature'   : self.handleSetTemperature,
            'SetMotorAngle'    : self.handleSetMotorAngle,
            'GetMotorAngle'    : self.handleGetMotorAngle,
            'ZeroMotorAngle'   : self.handleZeroMotorAngle,
            'MaxMotorAngle'    : self.handleMaxMotorAngle,
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


    def commandErrorJson(self, command, error):
        jsonDict = { "Command" : command,
                     "Result"  : 'Error',
                     "Message" : error }
        return jsonDict        
    
    def handleGetActiveBrew(self,parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        
        self.brewageId = self.db.getActiveBrew()
        if self.brewageId != None:
            jsonDict['Brewage'] = self.db.getBrewageNameById(self.brewageId)
            jsonDict["ControllerMode"] = self.db.getControllerModeById(self.brewageId)
            jsonDict['Measurments'] = self.db.getMeasurements(self.brewageId)
        else:
            jsonDict['Brewage'] = None
        return jsonDict

    def handleGetAvailableSettings(self, parsed_json):
        brewages = self.db.getAllBrewages()
        jsonDict = self.commandOkJson(parsed_json['Command'])
        brewagesList = []
        for row in brewages:
            brewagesList.append(row["BrewName"])
        jsonDict["Brewages"] = brewagesList

        #Get all configruations
        configurations = self.db.getAllConfigurations()
        configurationList = []
        for row in configurations:
            configurationList.append(row["ConfigurationName"])
        jsonDict["Configurations"] = configurationList

        return jsonDict

    def handleNewBrewage(self,parsed_json):
        newBrewage = parsed_json['Brewage']
        configId = self.db.getConfigurationIdByName(newBrewage['ConfigurationName'])
        self.db.insertBrewage(newBrewage['BrewName'],str(datetime.datetime.now()),"NotStarted",None,None,None,None,configId,None)
        jsonDict = self.commandOkJson(parsed_json['Command'])
        jsonDict['BrewName'] = newBrewage['BrewName']
        return jsonDict

    def handleOpenBrewage(self, parsed_json):
        brewages = self.db.getBrewage(parsed_json['Brewage'])
        self.brewageId = brewages['BrewageId']
        self.brewName = brewages['BrewName']
        #if self.regelaarActive == False:
        #    self.TemperatureSetPoint = brewages['Mashing']['SetPoints'][0]['SetPoint']
        self.motor.setMotorConfig(brewages['Configuration']['StepsPerRevolution'])
        jsonDict = self.commandOkJson(parsed_json['Command'])
        jsonDict = {**jsonDict, **brewages}
        return jsonDict

    def handleSetTemperature(self, parsed_json):
        receivedSetPoint = int(parsed_json['SetPoint'])
        if receivedSetPoint < 0:
            receivedSetPoint = 0
        if receivedSetPoint > 100:
            receivedSetPoint = 100

        self.TemperatureSetPoint = receivedSetPoint
        self.pid.SetPoint = self.TemperatureSetPoint
        jsonDict = { "Command" : parsed_json['Command'],
                     "Result"  : 'Ok',
                     "SetPoint" : str(self.TemperatureSetPoint)}
        return jsonDict

    def handleGetMeasurement(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        measurement = { "ControllerMode"          : self.db.getControllerModeById(self.brewageId),
                        "TemperatureSetPoint"     : str(self.TemperatureSetPoint),
                        "TemperatureProcessValue" : str(self.Temperature),
                        "OutputPV"                : str(self.outputPV)
                   }
        jsonDict = {**jsonDict, **measurement}
        return jsonDict
    
    def handleGetAllMeasurements(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        jsonDict['Measurments'] = self.db.getMeasurements(self.brewageId)
        return jsonDict
        
    def handleGetConfiguration(self,parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        newConfig = self.db.getConfigurationByName(parsed_json['ConfigurationName'])
        jsonDict = {**jsonDict, **newConfig}
        return jsonDict

    def handleSetConfiguration(self, parsed_json):
        ConfigId        = parsed_json['Configuration']['ConfigurationId']
        ConfigName      = parsed_json['Configuration']['ConfigurationName']
        ConfigP         = parsed_json['Configuration']['P']
        ConfigI         = parsed_json['Configuration']['I']
        ConfigD         = parsed_json['Configuration']['D']
        ConfigStepsPerRevolution = parsed_json['Configuration']['StepsPerRevolution']
        if ConfigId == "":
            ConfigId = self.db.insertConfiguration(ConfigName,ConfigP,ConfigI,ConfigD,ConfigStepsPerRevolution)    
        else:
            self.db.updateConfiguration(ConfigId,ConfigName,ConfigP,ConfigI,ConfigD,ConfigStepsPerRevolution)
        self.P = float(ConfigP)
        self.I = float(ConfigI)
        self.D = float(ConfigD)
        self.StepsPerRevolution = int(ConfigStepsPerRevolution)

        jsonDict = self.commandOkJson(parsed_json['Command'])
        newConfig = self.db.getConfiguration(ConfigId)
        jsonDict = {**jsonDict, **newConfig}
        return jsonDict

    def handleControllerMode(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        if parsed_json['Mode'] == "Start":

            if self.motor.zeroHasBeenSet == True and self.motor.maxHasBeenSet == True:
                self.regelaarActive = True


                if self.db.getControllerModeById(self.brewageId) == "NotStarted":
                    self.db.insertActiveBrew(self.brewageId)
                    self.db.updateMashingStartTime(self.brewageId,str(datetime.datetime.now()))
                
                self.db.updateControllerMode(self.brewageId, "Started")
                jsonDict["ControllerMode"] = "Started"
            else:
                jsonDict = self.commandErrorJson(parsed_json['Command'],"Motor has not set zero or max")

        elif parsed_json['Mode'] == "Pauze":
            self.regelaarActive = False

            self.db.updateControllerMode(self.brewageId, "Pauzed")
            jsonDict["ControllerMode"] = "Pauzed"

        elif parsed_json['Mode'] == "Stop":
            self.regelaarActive = False

            jsonDict["ControllerMode"] = "Stopped"
            self.db.updateControllerMode(self.brewageId, "Stopped")
            self.db.deleteActiveBrew(self.brewageId)
            self.db.updateMashingStopTime(self.brewageId,str(datetime.datetime.now()))

        return jsonDict

    def handleSetMotorAngle(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        motorAngle = parsed_json['Angle']

        self.motor.angleSP = int(motorAngle)

        return jsonDict

    def handleGetMotorAngle(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        jsonDict['Angle'] = self.motor.anglePV
        return jsonDict

    def handleZeroMotorAngle(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        self.motor.zero()
        return jsonDict

    def handleMaxMotorAngle(self, parsed_json):
        jsonDict = self.commandOkJson(parsed_json['Command'])
        self.motor.max()
        return jsonDict



if __name__ == "__main__":
    MaischerServer = MaischerServer()
    start_server = websockets.serve(MaischerServer.wsServer, '0.0.0.0', 7654)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
