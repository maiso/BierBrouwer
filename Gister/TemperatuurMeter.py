import sqlite3
from threading import Timer
from time import sleep
import sys
import time
import datetime

class RepeatedTimer(object):
    def __init__(self, interval, function):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
        
class TemperatuurMeter():
    def __init__(self, dbName):
        self.conn = sqlite3.connect(databaseName)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE biermeting (date text, BinnenTemp REAL, BuitenTemp REAL)''')

        #self.rt = RepeatedTimer(1, self.GetTempAndStore) # it auto-starts, no need of rt.start()
    def __del__(self):
        self.rt.stop() # better in a try/finally block to make sure the program ends!
        self.conn.close()

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

    def GetTempAndStore(self):
        BinnenTemp = self.ReadDS18B20("28-0000039a3a87")
        BuitenTemp = self.ReadDS18B20("28-0117c0732dff")
        
        self.StoreTemperatureInDB(BinnenTemp,BuitenTemp)

    def StoreTemperatureInDB(self,BinnenTemp,BuitenTemp):
        print 'Inserting into DB'
        self.c.execute('''INSERT INTO biermeting (date,BinnenTemp,BuitenTemp) VALUES (?,?,?)''',(str(datetime.datetime.now()),float(BinnenTemp),float(BuitenTemp)))
        self.conn.commit()

if __name__ == "__main__":
    print "starting..."
    dateTime = time.strftime("%Y%m%d%H%M")
    print 'Today is: %s', dateTime
    databaseName = 'biermeting'+dateTime+'.db'
    tempMeter = None
    try:
        tempMeter = TemperatuurMeter(databaseName)
    except Exception as e:
        print str(e)
    
    while(True):
        tempMeter.GetTempAndStore()
        sleep(5)

