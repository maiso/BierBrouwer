import glob, os
import json
import threading
import time
import sqlite3

#ID, NAME, BrewDate, CalibrationId,MaischSchematicId
class DatabaseInterface():
    def __init__(self, databaseName):
        self.conn = sqlite3.connect(databaseName)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        # lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])

        self.createTables()

    def getAllBrewages(self):
        self.c.execute('''
            SELECT * FROM Brewages
            ''')
        self.rows = self.c.fetchall()

        print (self.rows)
        #print (self.rows[0]['NAME'])
        print([dict(row) for row in self.rows])
        jsonRet = json.dumps([dict(row) for row in self.rows])
        print (jsonRet)   
        return jsonRet

    def newBrewages(self, name, date, CalibrationId,MaischSchematic):
        self.c.execute('''
            INSERT INTO Brewages(
               NAME,
               BrewDate,
               CalibrationId,
               MaischSchematicId
            ) 
            VALUES(?,?,?,?);
            ''', (name,date,CalibrationId,MaischSchematic))
        self.conn.commit()

    def getCalibration(self,BrewageId):
        t = (BrewageId,)
        self.c.execute('''
            SELECT P, I, D, MinServoAngel, MaxServoAngel, NrOfSteps, MaxStepSpeed, DegreesPerStep
            FROM Brewages
            LEFT JOIN Calibration ON Brewage.CalibrationId = Calibration.ID;
            WHERE Brewages.ID=?
            ''', t)
        data = self.c.fetchone()
        jsonRet = json.dumps(data)
        print (jsonRet)
        return jsonRet

    def createTables(self):
        self.createCalibrationTable()
        self.createSetpointsTable()
        self.createHopMomentsTable()
        self.createMaischSchematicTable()
        self.createBrewagesTable()
        self.createMeasurementsTable()

    def createCalibrationTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Calibration(
               ID    INTEGER PRIMARY KEY AUTOINCREMENT,
               NAME  TEXT  NOT NULL,               
               P  REAL  ,
               I  REAL  ,
               D  REAL  ,
               MinServoAngel  REAL,
               MaxServoAngel  REAL,
               NrOfSteps      REAL,
               MaxStepSpeed   REAL,
               DegreesPerStep REAL
            );
            ''')

    def createSetpointsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Setpoints(
               ID         INTEGER PRIMARY KEY AUTOINCREMENT,
               StartTime  TEXT  NOT NULL,               
               SetPoint   REAL
            );
            ''')

    def createHopMomentsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS HopMoments(
               ID             INTEGER PRIMARY KEY AUTOINCREMENT,
               StartTime      TEXT  NOT NULL,               
               HOPNAME        TEXT  NOT NULL,
               AmountInGrams  REAL
            );
            ''')

    def createMaischSchematicTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS MaischSchematic(
               ID    INTEGER PRIMARY KEY AUTOINCREMENT,
               NAME  TEXT  NOT NULL,               
               SetpointsId INT,
               HopMomentsId INT,
               FOREIGN KEY(SetpointsId) REFERENCES Setpoints(ID),
               FOREIGN KEY(HopMomentsId) REFERENCES HopMoments(ID)
            );
            ''')

    def createBrewagesTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Brewages(
               ID        INTEGER PRIMARY KEY AUTOINCREMENT,
               NAME      TEXT  NOT NULL UNIQUE,
               BrewDate  TEXT  NOT NULL UNIQUE,
               CalibrationId INT,
               MaischSchematicId INT,
               FOREIGN KEY(CalibrationId) REFERENCES Calibration(ID),
               FOREIGN KEY(MaischSchematicId) REFERENCES MaischSchematic(ID)
            );
            ''')
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

if __name__ == "__main__":
    print ("starting...")
    dateTime = time.strftime("%Y%m%d%H%M")
    print ('Today is: %s', dateTime)
    databaseName = 'BierBrouwer.db'
    dbInterface = None
    #try:
    dbInterface = DatabaseInterface(databaseName)
    jsonRet = dbInterface.getAllBrewages()
    print (jsonRet) 
    dbInterface.newBrewages("TestBrew2",dateTime,None,None)        
    #except Exception as e:
    #    print (str(e))
    
    time.sleep(5)


