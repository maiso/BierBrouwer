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

    def createTables(self):
        self.createConfigurationTable()
        self.createMashingTable()
        self.createSetpointsTable()
        self.createBoilingTable()
        self.createHopMomentsTable()
        self.createBrewagesTable()
        self.createMeasurementsTable()
        self.createActiveBrewTable()

    def createDefaultConfiguration(self):
        self.insertConfiguration("DefaultConfiguration",10,1,1,4096)    

    def createDefaultBrewage(self):
        self.insertBrewage("TestBrew",str(datetime.datetime.now()),"NotStarted",None,None,None,None,1,1)

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
               ConfigurationName  TEXT  NOT NULL UNIQUE,               
               P  REAL  ,
               I  REAL  ,
               D  REAL  ,
               StepsPerRevolution  REAL
            );
            ''')

    def insertConfiguration(self,ConfigurationName,P,I,D,StepsPerRevolution):
        self.c.execute('''
            INSERT INTO Configuration(
               ConfigurationName,               
               P  ,
               I  ,
               D  ,
               StepsPerRevolution
            ) 
            VALUES(?,?,?,?,?);
            ''', (ConfigurationName,               
                  P  ,
                  I  ,
                  D  ,
                  StepsPerRevolution ))
        self.conn.commit()  
        self.c.execute('''SELECT ConfigurationId FROM Configuration WHERE ConfigurationName = ?''',(ConfigurationName,))
        return self.c.fetchone()['ConfigurationId']

    def updateConfiguration(self, ConfigurationId,ConfigurationName,P,I,D,StepsPerRevolution):
        self.c.execute(
          ''' UPDATE Configuration
              SET ConfigurationName = ? ,
                  P = ? ,
                  I = ? ,
                  D = ? ,
                  StepsPerRevolution = ?
              WHERE ConfigurationId = ?''', 
                (ConfigurationName,               
                  P  ,
                  I  ,
                  D  ,
                  StepsPerRevolution,
                  ConfigurationId))
        self.conn.commit()

    def getConfiguration(self, ConfigurationId):
        self.c.execute('''SELECT * FROM Configuration WHERE ConfigurationId = ?''',(ConfigurationId,))
        return self.c.fetchone()
    
    def getConfigurationByName(self, ConfigurationName):
        self.c.execute('''SELECT * FROM Configuration WHERE ConfigurationName = ?''',(ConfigurationName,))
        return self.c.fetchone()


    def getConfigurationIdByName(self, ConfigurationName):
        self.c.execute('''SELECT ConfigurationId FROM Configuration WHERE ConfigurationName = ?''',(ConfigurationName,))
        return self.c.fetchone()['ConfigurationId']

    def getAllConfigurations(self):
        self.c.execute('''SELECT * FROM Configuration''')
        self.rows = self.c.fetchall()
        return [dict(row) for row in self.rows]

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
### ActiveBrew
#########################################################################
    def createActiveBrewTable(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS ActiveBrew(
               BrewageId          INT,
               FOREIGN KEY(BrewageId) REFERENCES Brewages(BrewageId)
            );
            ''')
    def getActiveBrew(self):
        self.c.execute('''SELECT * FROM ActiveBrew''')
        activeBrew = None
        try:
          return self.c.fetchone()['BrewageId']
        except:
          return None
         

    def insertActiveBrew(self, BrewageId ):
        self.c.execute('''
            INSERT INTO ActiveBrew(BrewageId) VALUES(?);''', (BrewageId,))
        self.conn.commit()      

    def deleteActiveBrew(self, BrewageId ):
        self.c.execute('''
            DELETE FROM ActiveBrew WHERE BrewageId = ?;''', (BrewageId,))
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
               ControllerMode     TEXT,
               MashingStartTime   TEXT,
               MashingStopTime    TEXT,
               BoilingStartTime   TEXT,
               BoilingStopTime    TEXT,
               ConfigurationId    INT,
               MashingId INT,
               FOREIGN KEY(ConfigurationId) REFERENCES Configuration(ConfigurationId),
               FOREIGN KEY(MashingId) REFERENCES Mashing(MashingId)
            );
            ''')
    def insertBrewage(self, BrewName, BrewDate, ControllerMode, MashingStartTime, MashingStopTime,BoilingStartTime, BoilingStopTime, ConfigurationId, MashingId):
        self.c.execute('''
            INSERT INTO Brewages(
               BrewName           ,
               BrewDate           ,
               ControllerMode     ,
               MashingStartTime   ,
               MashingStopTime    ,
               BoilingStartTime   ,
               BoilingStopTime    ,
               ConfigurationId      ,
               MashingId
            )
            VALUES(?,?,?,?,?,?,?,?,?);
            ''', (BrewName,
                BrewDate,
                ControllerMode,
                MashingStartTime,
                MashingStopTime,
                BoilingStartTime,
                BoilingStopTime,
                ConfigurationId,
                MashingId))
        self.conn.commit()

        self.c.execute('''SELECT BrewageId FROM Brewages WHERE BrewName = ?''',(BrewName,))
        return self.c.fetchone()['BrewageId']

    def updateControllerMode(self,BrewageId, ControllerMode):
        self.c.execute( ''' UPDATE Brewages SET ControllerMode = ? WHERE BrewageId = ?''', 
                            (ControllerMode,BrewageId)
                      )
        self.conn.commit()

    def getControllerModeById(self, BrewageId):
        self.c.execute('''SELECT ControllerMode FROM Brewages WHERE BrewageId = ?''',(BrewageId,))
        return self.c.fetchone()['ControllerMode']

    def updateMashingStartTime(self,BrewageId, MashingStartTime):
        self.c.execute( ''' UPDATE Brewages SET MashingStartTime = ? WHERE BrewageId = ?''', 
                            (MashingStartTime,BrewageId)
                      )
        self.conn.commit()

    def updateMashingStopTime(self,BrewageId, MashingStopTime):
        self.c.execute( ''' UPDATE Brewages SET MashingStopTime = ? WHERE BrewageId = ?''', 
                            (MashingStopTime,BrewageId)
                      )
        self.conn.commit()

    def getBrewageNameById(self, BrewageId):
        self.c.execute('''SELECT BrewName FROM Brewages WHERE BrewageId = ?''',(BrewageId,))
        return self.c.fetchone()['BrewName']

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
        # print('self.getMashing')
        # mashing = self.getMashing(brewage['MashingId'])
        # print('self.getSetPoints')
        # setpoints = self.getSetPoints(mashing['MashingId'])
        # setpoints = [dict(row) for row in setpoints]
        print (brewage)
        brewage = dict(brewage)
        print (brewage)
        del brewage['ConfigurationId']
        # print (brewage)
        # del brewage['MashingId']
        print (brewage)
        brewage['Configuration'] = dict(configuration)
        print (brewage)
        # brewage['Mashing'] = dict(mashing)
        # print (brewage)

        # print (brewage['Mashing'])        
        # print (setpoints)
        # brewage['Mashing']['SetPoints'] = setpoints
        # print ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        # print (brewage)

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

    def insertMeasurement(self, BrewageId, SetPoint, Temperature, PIDOutput):
        self.c.execute('''
          INSERT INTO Measurements(
             BrewageId,
             MeasurementTime,
             SetPoint,
             Temperature,
             PIDOutput
          ) 
          VALUES(?,?,?,?,?);
          ''', (BrewageId, str(datetime.datetime.now()), float(SetPoint), float(Temperature),float(PIDOutput)))
        self.conn.commit()

    def getMeasurements(self, BrewageId):
        self.c.execute('''SELECT *
          FROM Measurements 
          WHERE Measurements.BrewageId = ?
          ''',(BrewageId,))

        measurements = self.c.fetchall()
        return  [dict(row) for row in measurements]


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



