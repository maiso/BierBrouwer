import glob, os
import json
import threading
import datetime
import sqlite3

#ID, Name, BrewDate, CalibrationId,MashingId
class DatabaseInterface():
    def __init__(self, databaseName):
        self.conn = sqlite3.connect(databaseName)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        # lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])

        self.createTables()

    def getCalibration(self,BrewageId):
        t = (BrewageId,)
        self.c.execute('''
            SELECT P, I, D, MinServoAngle, MaxServoAngle, NrOfSteps, MaxStepSpeed, DegreesPerStep
            FROM Brewages
            LEFT JOIN Calibration ON Brewage.CalibrationId = Calibration.ID;
            WHERE Brewages.ID=?
            ''', t)
        data = self.c.fetchone()
        jsonRet = json.dumps(data)
        #print (jsonRet)
        return jsonRet

    def createTables(self):
        self.createCalibrationTable()
        self.createMashingTable()
        self.createSetpointsTable()
        self.createBoilingTable()
        self.createHopMomentsTable()
        self.createBrewagesTable()
        self.createMeasurementsTable()

        self.createDefaultConfiguration()
        self.createDefaultBrewage()

    def createDefaultConfiguration(self):
        self.insertConfiguration("DefaultCalibration",10,1,1,0,0,0,0,0)    

    def createDefaultBrewage(self):
        self.insertBrewage("TestBrew",str(datetime.datetime.now()),0,0,0,0,1,None)

#########################################################################
### Calibration
#########################################################################
    def createCalibrationTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Calibration(
               ID    INTEGER PRIMARY KEY AUTOINCREMENT,
               CalibrationName  TEXT  NOT NULL,               
               P  REAL  ,
               I  REAL  ,
               D  REAL  ,
               MinServoAngle  REAL,
               MaxServoAngle  REAL,
               NrOfSteps      REAL,
               MaxStepSpeed   REAL,
               DegreesPerStep REAL
            );
            ''')

    def insertConfiguration(self,CalibrationName,P,I,D,MinServoAngle,MaxServoAngle,NrOfSteps,MaxStepSpeed, DegreesPerStep):
        self.c.execute('''
            INSERT INTO Calibration(
               CalibrationName,               
               P  ,
               I  ,
               D  ,
               MinServoAngle  ,
               MaxServoAngle  ,
               NrOfSteps      ,
               MaxStepSpeed   ,
               DegreesPerStep 
            ) 
            VALUES(?,?,?,?,?,?,?,?,?);
            ''', (CalibrationName,               
                  P  ,
                  I  ,
                  D  ,
                  MinServoAngle  ,
                  MaxServoAngle  ,
                  NrOfSteps      ,
                  MaxStepSpeed   ,
                  DegreesPerStep ))
        self.conn.commit()  
#########################################################################
### Mashing
#########################################################################
    def createMashingTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Mashing(
               ID    INTEGER PRIMARY KEY AUTOINCREMENT,
               MashName  TEXT  NOT NULL          
            );
            ''')

    def newMashing(self, MashName):
        self.c.execute('''
            INSERT INTO Mashing(
               MashName
            ) 
            VALUES(?);
            ''', (MashName))
        self.conn.commit()

### SetPoints
    def createSetpointsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Setpoints(
               ID         INTEGER PRIMARY KEY AUTOINCREMENT,
               StartTime  TEXT  NOT NULL,               
               SetPoint   REAL ,
               MashingId INT NOT NULL,
               FOREIGN KEY(MashingId) REFERENCES Mashing(ID)
            );
            ''')

    def newSetpoint(self, StartTime, SetPoint, MashingId):
        self.c.execute('''
            INSERT INTO Setpoints(
               StartTime,
               SetPoint,
               MashingId
            ) 
            VALUES(?,?,?);
            ''', (StartTime, SetPoint, MashingId))
        self.conn.commit()

#########################################################################
### Boiling
#########################################################################
    def createBoilingTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Boiling(
               ID                 INTEGER PRIMARY KEY AUTOINCREMENT,
               BoilingTime        INTEGER,
               BoilingTemperature INTEGER
            );
            ''')

    def newBoiling(self, BoilingTime,BoilingTemperature ):
        self.c.execute('''
            INSERT INTO Brewages(
               BoilingTime,
               BoilingTemperature
            ) 
            VALUES(?,?);
            ''', (BoilingTime,BoilingTemperature))
        self.conn.commit()

### HopMoments
    def createHopMomentsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS HopMoments(
               ID             INTEGER PRIMARY KEY AUTOINCREMENT,
               StartTime      TEXT  NOT NULL,               
               HopName        TEXT  NOT NULL,
               AmountInGrams  REAL,
               BoilingId INT NOT NULL,
               FOREIGN KEY(BoilingId) REFERENCES Boiling(ID)
            );
            ''')

    def newHopMoments(self, StartTime, HopName, AmountInGrams, BoilingId):
        self.c.execute('''
            INSERT INTO HopMoments(
               StartTime,
               HopName,
               AmountInGrams,
               BoilingId
            )
            VALUES(?,?,?);
            ''', (StartTime, HopName, AmountInGrams, BoilingId))
        self.conn.commit()

#########################################################################
### Brewages
#########################################################################
    def createBrewagesTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Brewages(
               ID                 INTEGER PRIMARY KEY AUTOINCREMENT,
               BrewName           TEXT  NOT NULL UNIQUE,
               BrewDate           TEXT  NOT NULL UNIQUE,
               MashingStartTime   TEXT,
               MashingStopTime    TEXT,
               BoilingStartTime   TEXT,
               BoilingStopTime    TEXT,
               CalibrationId      INT,
               MashingId INT,
               FOREIGN KEY(CalibrationId) REFERENCES Calibration(ID),
               FOREIGN KEY(MashingId) REFERENCES Mashing(ID)
            );
            ''')
    def insertBrewage(self, BrewName, BrewDate, MashingStartTime, MashingStopTime,BoilingStartTime, BoilingStopTime, CalibrationId, MashingId):
        self.c.execute('''
            INSERT INTO Brewages(
               BrewName           ,
               BrewDate           ,
               MashingStartTime   ,
               MashingStopTime    ,
               BoilingStartTime   ,
               BoilingStopTime    ,
               CalibrationId      ,
               MashingId
            )
            VALUES(?,?,?,?,?,?,?,?);
            ''', (BrewName,
                BrewDate,
                MashingStartTime,
                MashingStopTime,
                BoilingStartTime,
                BoilingStopTime,
                CalibrationId,
                MashingId))
        self.conn.commit()

        self.c.execute('''SELECT ID FROM Brewages WHERE BrewName = ?''',(BrewName,))
        return self.c.fetchone()['ID']


    def getAllBrewages(self):
        self.c.execute('''SELECT BrewName FROM Brewages''')
        self.rows = self.c.fetchall()

        #print (self.rows)
        #print (self.rows[0]['Name'])
        #print([dict(row) for row in self.rows])
        #jsonRet = json.dumps([dict(row) for row in self.rows])
        #print (jsonRet)   
        return [dict(row) for row in self.rows]


    def getBrewage(self, brewageName):
        self.c.execute('''SELECT * 
          FROM Brewages 
          LEFT JOIN Calibration ON Brewages.CalibrationId = Calibration.ID
          WHERE BrewName = ?''',(brewageName,))
        self.rows = self.c.fetchall()

        #print (self.rows)
        #print (self.rows[0]['Name'])
        #print([dict(row) for row in self.rows])
        #jsonRet = json.dumps([dict(row) for row in self.rows])
        #print (jsonRet)   
        return [dict(row) for row in self.rows]


#########################################################################
### Measurements
#########################################################################
    def createMeasurementsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Measurements(
               ID               INTEGER PRIMARY KEY AUTOINCREMENT,
               BrewageId        INT   NOT NULL,
               MeasurementTime  TEXT  NOT NULL,               
               SetPoint         REAL,
               Temperature      REAL,
               PIDOutput        REAL,
               FOREIGN KEY(BrewageId) REFERENCES Brewages(ID)
            );
            ''')

# if __Name__ == "__main__":
#     print ("starting...")
#     dateTime = time.strftime("%Y%m%d%H%M")
#     print ('Today is: %s', dateTime)
#     databaseName = 'BierBrouwer.db'
#     dbInterface = None
#     #try:
#     dbInterface = DatabaseInterface(databaseName)
#     jsonRet = dbInterface.getAllBrewages()
#     print (jsonRet) 
#     newId = dbInterface.insertBrewage(dateTime,dateTime,None,None)        
#     print ("newId " + str(newId))
#     #except Exception as e:
#     #    print (str(e))
    
#     time.sleep(5)


