import glob, os
import json
import threading
import time
import sqlite3

#ID, NAME, BrewDate, CalibrationId,MashingSchematicId
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
        self.createMashingSchematicTable()
        self.createSetpointsTable()
        self.createBoilingSchematicTable()
        self.createHopMomentsTable()
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

#########################################################################
### MashingSchematic
#########################################################################
    def createMashingSchematicTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS MashingSchematic(
               ID    INTEGER PRIMARY KEY AUTOINCREMENT,
               Name  TEXT  NOT NULL          
            );
            ''')

    def newMashingSchematic(self, name):
        self.c.execute('''
            INSERT INTO MashingSchematic(
               Name
            ) 
            VALUES(?);
            ''', (name))
        self.conn.commit()

### SetPoints
    def createSetpointsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Setpoints(
               ID         INTEGER PRIMARY KEY AUTOINCREMENT,
               StartTime  TEXT  NOT NULL,               
               SetPoint   REAL ,
               MashingSchematicId INT NOT NULL,
               FOREIGN KEY(MashingSchematicId) REFERENCES MashingSchematic(ID)
            );
            ''')

    def newSetpoint(self, StartTime, SetPoint, MashingSchematicId):
        self.c.execute('''
            INSERT INTO Setpoints(
               StartTime,
               SetPoint,
               MashingSchematicId
            ) 
            VALUES(?,?,?);
            ''', (StartTime, SetPoint, MashingSchematicId))
        self.conn.commit()

#########################################################################
### BoilingSchematic
#########################################################################
    def createBoilingSchematicTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS BoilingSchematic(
               ID                 INTEGER PRIMARY KEY AUTOINCREMENT,
               BoilingTime        INTEGER,
               BoilingTemperature INTEGER
            );
            ''')

    def newBoilingSchematic(self, BoilingTime,BoilingTemperature ):
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
               Hopname        TEXT  NOT NULL,
               AmountInGrams  REAL,
               BoilingSchematicId INT NOT NULL,
               FOREIGN KEY(BoilingSchematicId) REFERENCES BoilingSchematic(ID)
            );
            ''')

    def newHopMoments(self, StartTime, Hopname, AmountInGrams, BoilingSchematicId):
        self.c.execute('''
            INSERT INTO HopMoments(
               StartTime,
               Hopname,
               AmountInGrams,
               BoilingSchematicId
            )
            VALUES(?,?,?);
            ''', (StartTime, Hopname, AmountInGrams, BoilingSchematicId))
        self.conn.commit()

#########################################################################
### Brewages
#########################################################################
    def createBrewagesTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Brewages(
               ID                 INTEGER PRIMARY KEY AUTOINCREMENT,
               NAME               TEXT  NOT NULL UNIQUE,
               BrewDate           TEXT  NOT NULL UNIQUE,
               MashingStartTime   TEXT,
               MashingStopTime    TEXT,
               BoilingStartTime   TEXT,
               BoilingStopTime    TEXT,
               CalibrationId      INT,
               MashingSchematicId INT,
               FOREIGN KEY(CalibrationId) REFERENCES Calibration(ID),
               FOREIGN KEY(MashingSchematicId) REFERENCES MashingSchematic(ID)
            );
            ''')

    def getAllBrewages(self):
        self.c.execute('''SELECT * FROM Brewages''')
        self.rows = self.c.fetchall()

        print (self.rows)
        #print (self.rows[0]['NAME'])
        print([dict(row) for row in self.rows])
        jsonRet = json.dumps([dict(row) for row in self.rows])
        print (jsonRet)   
        return jsonRet

    def newBrewage(self, name, date, CalibrationId,MashingSchematic):
        self.c.execute('''
            INSERT INTO Brewages(
               NAME,
               BrewDate,
               CalibrationId,
               MashingSchematicId
            ) 
            VALUES(?,?,?,?);
            ''', (name,date,CalibrationId,MashingSchematic))
        self.conn.commit()

        self.c.execute('''SELECT ID FROM Brewages WHERE NAME = ?''',(name,))
        return self.c.fetchone()['ID']


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
    newId = dbInterface.newBrewage(dateTime,dateTime,None,None)        
    print ("newId " + str(newId))
    #except Exception as e:
    #    print (str(e))
    
    time.sleep(5)


