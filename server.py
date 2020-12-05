import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json
import requests

URL = "https://3fxdttozv0.execute-api.us-east-2.amazonaws.com/default/getPlayerInfo"

clients_lock = threading.Lock()
connected = 0

clients = {}
players = {}
gameID = 0

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
         elif 'playerConnect' in data:
            uniqueID = json.loads(data[2:-1])['id']
            players[uniqueID] = {}
            players[uniqueID]['name'] = json.loads(data[2:-1])['name']
            #print("ID Name: " + players[uniqueID]['name'])
            GetPlayerData(uniqueID)
            if len(players) >= 3:
               CreateGame(sock, addr)
      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            message = {"cmd": 0, "id":str(addr)}
            m = json.dumps(message)
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))

def CreateGame(sock, addr):
   #print(str(len(players)) + " players have joined")
   range = 50
   gameCreated = False

   gameDetails = {}

   while not gameCreated:
      for p, v in players.items():
         if gameCreated:
            break
         gameDetails.clear()
         gameDetails = {gameID:{}}
         for pl, va in players.items():
            if p == pl:
               continue
            else:
               if len(gameDetails[gameID]) < 2:
                  if abs(int(v['rating']) - int(va['rating'])) <= range:
                     gameDetails[gameID]['player1'] = p
                     gameDetails[gameID]['player2'] = pl
               else:
                  if (max(int(gameDetails[gameID]['player1']), int(gameDetails[gameID]['player2'])) - int(va['rating']) <= range or
                        int(va['rating']) - min(int(gameDetails[gameID]['player1']), int(gameDetails[gameID]['player2'])) <= range):
                     gameDetails[gameID]['player3'] = pl
                     gameCreated = True
                     break
      range += 30

   message = {"gameID":gameID, gameDetails[gameID]['player1']:players[gameDetails[gameID]['player1']], gameDetails[gameID]['player2']:players[gameDetails[gameID]['player2']], gameDetails[gameID]['player3']:players[gameDetails[gameID]['player3']]}
   m = json.dumps(message)
   sock.sendto(bytes(m, 'utf8'), addr)
   
   gameID += 1

   del players.[gameDetails[gameID]['player1']]
   del players.[gameDetails[gameID]['player2']]
   del players.[gameDetails[gameID]['player3']]

def GetPlayerData(playerID):
   PARAMS = {'player_id':playerID}
   r = requests.get(url = URL, params = PARAMS)
   data = r.json()
   players[playerID]['rating'] = data['rating']

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         player['id'] = str(c)
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients, (s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
