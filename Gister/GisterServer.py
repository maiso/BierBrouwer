import asyncio
import websockets
import glob, os
import json
import sqlite3
from sqlite3 import Error


class TemperatuurServer():
    def openDatabase(self,datbaseName):
        try:
            conn = sqlite3.connect(datbaseName)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM biermeting")
#            self.rows = []
            self.rows = cur.fetchall()
            #self.rows = self.rows[::12]
            print (self.rows)
            return len(self.rows),''

        except Error as e:
            return -1,str(e)

    @asyncio.coroutine
    def wsServer(self, websocket, path):
        command = yield from websocket.recv()
        print ('Received command:' + command)
        if command == 'GetDatabases':
            os.chdir("./DatabaseSync/")
            jsonDict = { "Command" : "GetDatabases",
                         "Databases" : glob.glob("*.db")}
            jsonText = json.dumps(jsonDict)
            print (jsonText)
            yield from websocket.send(jsonText)

        elif 'OpenDatabase' in command:
            print('OpeningDatabase')
            rows, error = self.openDatabase(command.split(' ')[1])
            print ('rows:' + str(rows) + ' error:' + error)
            if(rows > 0):
                yield from websocket.send(json.dumps({  "Command"      : "OpenDatabase",
                                                        "NumberOfRows" : str(rows)}))
            else:
                yield from websocket.send(json.dumps({  "Command" : "OpenDatabase",
                                                        "Error"   : error}))
        elif 'GetRows' in command:
            rowNumberStart = command.split(' ')[1]
            rowNumberEnd = command.split(' ')[2]
            yield from websocket.send(json.dumps({  "Command" : "GetRows",
                                                    "Rows"    : [dict(ix) for ix in self.rows[int(rowNumberStart):int(rowNumberEnd)]] 
                                                    }))



if __name__ == "__main__":
    tempServer = TemperatuurServer()
    start_server = websockets.serve(tempServer.wsServer, '0.0.0.0', 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
