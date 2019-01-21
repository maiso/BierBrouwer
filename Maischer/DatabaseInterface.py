import glob, os
import json
import threading
import datetime
import sqlite3

#ID, Name, BrewDate, ConfigurationId,MashingId
class DatabaseInterface():
    def __init__(self, databaseName):
        self.conn = sqlite3.connect(databaseName)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        # lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])

        self.createTables()

    # def getConfiguration(self,BrewageId):
    #     t = (BrewageId,)
    #     self.c.execute('''
    #         SELECT P, I, D, MinServoAngle, MaxServoAngle, NrOfSteps, MaxStepSpeed, DegreesPerStep
    #         FROM Brewages
    #         LEFT JOIN Configuration ON Brewage.ConfigurationId = Configuration.ID;
    #         WHERE Brewages.ID=?
    #         ''', t)
    #     data = self.c.fetchone()
    #     jsonRet = json.dumps(data)
    #     #print (jsonRet)
    #     return jsonRet

    def createTables(self):
        self.createConfigurationTable()
        self.createMashingTable()
        self.createSetpointsTable()
        self.createBoilingTable()
        self.createHopMomentsTable()
        self.createBrewagesTable()
        self.createMeasurementsTable()

        self.createDefaultConfiguration()
        self.createDefaultMashing()
        self.createDefaultBrewage()

    def createDefaultConfiguration(self):
        self.insertConfiguration("DefaultConfiguration",10,1,1,4096)    

    def createDefaultBrewage(self):
        self.insertBrewage("TestBrew",str(datetime.datetime.now()),0,0,0,0,1,1)

    def createDefaultMashing(self):
      self.insertMashing("Amerikaanse IPA")
      self.insterSetpoint("Amerikaanse IPA", 0, 60, 65)


#########################################################################
### Configuration
#########################################################################
    def createConfigurationTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Configuration(
               ConfigurationId    INTEGER PRIMARY KEY AUTOINCREMENT,
               ConfigurationName  TEXT  NOT NULL,               
               P  REAL  ,
               I  REAL  ,
               D  REAL  ,
               NrOfSteps      REAL
            );
            ''')

    def insertConfiguration(self,ConfigurationName,P,I,D,NrOfSteps):
        self.c.execute('''
            INSERT INTO Configuration(
               ConfigurationName,               
               P  ,
               I  ,
               D  ,
               NrOfSteps
            ) 
            VALUES(?,?,?,?,?);
            ''', (ConfigurationName,               
                  P  ,
                  I  ,
                  D  ,
                  NrOfSteps ))
        self.conn.commit()  

    def updateConfiguration(self, ConfigurationId,ConfigurationName,P,I,D,NrOfSteps):
        self.c.execute(
          ''' UPDATE Configuration
              SET ConfigurationName = ? ,
                  P = ? ,
                  I = ? ,
                  D = ? ,
                  NrOfSteps = ?
              WHERE ConfigurationId = ?''', 
                (ConfigurationName,               
                  P  ,
                  I  ,
                  D  ,
                  NrOfSteps,
                  ConfigurationId ))
        self.conn.commit()

    def getConfiguration(self, ConfigurationId):
        self.c.execute('''SELECT * FROM Configuration WHERE ConfigurationId = ?''',(ConfigurationId,))
        return self.c.fetchone()

#########################################################################
### Mashing
#########################################################################
    def createMashingTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Mashing(
               MashingId    INTEGER PRIMARY KEY AUTOINCREMENT,
               MashName  TEXT  NOT NULL          
            );
            ''')

    def insertMashing(self, MashName):
        self.c.execute('''
            INSERT INTO Mashing(
               MashName
            )
            VALUES(?);
            ''', (MashName,))
        self.conn.commit()
        return self.getMashingId(MashName)
    
    def getMashing(self, MashingId):
        self.c.execute('''SELECT *
          FROM Mashing 
          WHERE Mashing.MashingId = ?
          ''',(MashingId,))
        return self.c.fetchone()

    def getMashingId(self, MashName):
        self.c.execute('''SELECT MashingId FROM Mashing WHERE MashName = ?''',(MashName,))
        return self.c.fetchone()['MashingId']

### SetPoints
    def createSetpointsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Setpoints(
               MashingId  INT NOT NULL,
               SequenceNumber INT,
               Duration   TEXT  NOT NULL,
               SetPoint   REAL ,
               FOREIGN KEY(MashingId) REFERENCES Mashing(MashingId)
            );
            ''')

    def insterSetpoint(self, MashingName, SequenceNumber, Duration, SetPoint):
        self.c.execute('''
          INSERT INTO Setpoints(
             SequenceNumber,
             Duration,
             SetPoint,
             MashingId
          ) 
          VALUES(?,?,?,?);
          ''', (SequenceNumber, Duration, SetPoint, self.getMashingId(MashingName)))
        self.conn.commit()

    def getSetPoints(self, MashingId):
        self.c.execute('''SELECT *
          FROM SetPoints 
          WHERE SetPoints.MashingId = ?
          ''',(MashingId,))
        return self.c.fetchall()

#########################################################################
### Boiling
#########################################################################
    def createBoilingTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Boiling(
               BoilingId          INTEGER PRIMARY KEY AUTOINCREMENT,
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
               HopMomentId    INTEGER PRIMARY KEY AUTOINCREMENT,
               StartTime      TEXT  NOT NULL,               
               HopName        TEXT  NOT NULL,
               AmountInGrams  REAL,
               BoilingId INT NOT NULL,
               FOREIGN KEY(BoilingId) REFERENCES Boiling(BoilingId)
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
               BrewageId          INTEGER PRIMARY KEY AUTOINCREMENT,
               BrewName           TEXT  NOT NULL UNIQUE,
               BrewDate           TEXT  NOT NULL UNIQUE,
               MashingStartTime   TEXT,
               MashingStopTime    TEXT,
               BoilingStartTime   TEXT,
               BoilingStopTime    TEXT,
               ConfigurationId      INT,
               MashingId INT,
               FOREIGN KEY(ConfigurationId) REFERENCES Configuration(ConfigurationId),
               FOREIGN KEY(MashingId) REFERENCES Mashing(MashingId)
            );
            ''')
    def insertBrewage(self, BrewName, BrewDate, MashingStartTime, MashingStopTime,BoilingStartTime, BoilingStopTime, ConfigurationId, MashingId):
        self.c.execute('''
            INSERT INTO Brewages(
               BrewName           ,
               BrewDate           ,
               MashingStartTime   ,
               MashingStopTime    ,
               BoilingStartTime   ,
               BoilingStopTime    ,
               ConfigurationId      ,
               MashingId
            )
            VALUES(?,?,?,?,?,?,?,?);
            ''', (BrewName,
                BrewDate,
                MashingStartTime,
                MashingStopTime,
                BoilingStartTime,
                BoilingStopTime,
                ConfigurationId,
                MashingId))
        self.conn.commit()

        self.c.execute('''SELECT BrewageId FROM Brewages WHERE BrewName = ?''',(BrewName,))
        return self.c.fetchone()['BrewageId']

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
          WHERE BrewName = ?''',(brewageName,))
        brewage = self.c.fetchone()
        print('self.getConfiguration')
        configuration = self.getConfiguration(brewage['ConfigurationId'])
        print('self.getMashing')
        mashing = self.getMashing(brewage['MashingId'])
        print('self.getSetPoints')
        setpoints = self.getSetPoints(mashing['MashingId'])
        setpoints = [dict(row) for row in setpoints]
        print (brewage)
        brewage = dict(brewage)
        print (brewage)
        del brewage['ConfigurationId']
        print (brewage)
        del brewage['MashingId']
        print (brewage)
        brewage['Configuration'] = dict(configuration)
        print (brewage)
        brewage['Mashing'] = dict(mashing)
        print (brewage)

        print (brewage['Mashing'])        
        print (setpoints)
        brewage['Mashing']['SetPoints'] = setpoints
        print ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        print (brewage)

        #LEFT JOIN Configuration ON Brewages.ConfigurationId = Configuration.ID
        #LEFT JOIN Mashing ON Brewages.MashingId = Mashing.ID
        #LEFT JOIN Setpoints ON Brewages.MashingId = Setpoints.MashingId
        #print (self.rows)
        #print (self.rows[0]['Name'])
        #print([dict(row) for row in self.rows])
        #jsonRet = json.dumps([dict(row) for row in self.rows])
        #print (jsonRet)   
        return brewage


#########################################################################
### Measurements
#########################################################################
    def createMeasurementsTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS Measurements(
               MeasurementId    INTEGER PRIMARY KEY AUTOINCREMENT,
               BrewageId        INT   NOT NULL,
               MeasurementTime  TEXT  NOT NULL,               
               SetPoint         REAL,
               Temperature      REAL,
               PIDOutput        REAL,
               FOREIGN KEY(BrewageId) REFERENCES Brewages(BrewageId)
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



