import time
import socket
import threading
import os
from colorama import Fore
from time import sleep

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 20101))
sock.listen()

bannedIPs = []
connectionDict = {}
exitProgramm = False

partyLists = {
              "VS"   : [{"state" : None, "players" : []}],
              "COOP" : [{"state" : None, "players" : []}]
              }

gameInfos  = {
              "VS"   : [{}],
              "COOP" : [{}]
              }

class ClientClass:
    def __init__(self, clientValue, clientAdress) -> None:
        self.gameNumber = 0
        self.gameMode = ""
        self.clientValue = clientValue
        self.clientAdress = clientAdress
        self.playerNumber = 0
        self.currentState = "getNickname"

        print(Fore.BLUE, f'New connection : {self.clientAdress}')

        self.handleUser()

    def quit(self):
        print(Fore.RED, f'Someone quit : {self.clientAdress} - {self.currentState}')
        self.clientValue.close()
        del connectionDict[f"{self.clientAdress[0]}:{self.clientAdress[1]}"]
        if self.currentState == "inGame": gameInfos[self.gameMode][self.gameNumber]["ended"] = "quit"
        if self.gameNumber != 0: partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
        exit(1)

    def handleUser(self):
        try:
            if self.currentState == "getNickname": self.getNickname()
            while True:
                if self.currentState == "mainLobby": self.mainLobby()
                if self.currentState == "joinLobby": self.joinLobby()
                if self.currentState == "createLobby": self.createLobby()
                if self.currentState == "waitGame": self.waitGame()
                if self.currentState == "inGame": getattr(self, f'inGame_{self.gameMode}')() 
        except ConnectionAbortedError:
            print(Fore.RED, f'{self.clientAdress} was kicked')
            self.clientValue.close()
            del connectionDict[f"{self.clientAdress[0]}:{self.clientAdress[1]}"]
            if self.currentState == "inGame": gameInfos[self.gameMode][self.gameNumber]["ended"] = "quit"
            if self.gameNumber != 0: partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
            
    def getNickname(self):
        while self.currentState == "getNickname":
            try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
            except ConnectionResetError: self.quit()
            if len(userMsg) == 2 and userMsg[0] == "sendName" and len(userMsg[1]) <= 12:   
                self.clientName = userMsg[1]
                print(Fore.GREEN, f'{self.clientAdress} -> {self.clientName}')
                self.clientValue.send('continue|skip'.encode("utf-8"))
                self.currentState = "mainLobby"
                break
            else: self.quit()
            
    def mainLobby(self):
        while self.currentState == "mainLobby":
            try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
            except ConnectionResetError: self.quit()
            
            if len(userMsg) != 2 or (userMsg[0] == 'button' and userMsg[1] == 'quit'): self.quit()
            elif userMsg[0] == 'button' and userMsg[1][:9] == 'joinLobby':
                self.currentState = "joinLobby"
                self.gameMode = userMsg[1][9:]
                self.clientValue.send(f'continue|{len(partyLists[self.gameMode])-1}'.encode("utf-8"))
                break
            elif userMsg[0] == 'button' and userMsg[1] == 'createLobby':
                self.clientValue.send('continue|skip'.encode("utf-8"))
                self.currentState = "createLobby"
                break
    
    def joinLobby(self):
        while self.currentState == "joinLobby":
            try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
            except ConnectionResetError: self.quit()
            
            if len(userMsg) != 2 or userMsg[0] not in ["requestPartyList", "button"]: self.quit()
            if userMsg[0] == "requestPartyList":
                if int(userMsg[1]) >= len(partyLists[self.gameMode]) - 1: userMsg[1] = len(partyLists[self.gameMode])-2
                if int(userMsg[1]) in [0, 1]: userMsg[1] = 2
                else: userMsg[1] = int(userMsg[1])
                indexList = [x for x in range(userMsg[1]-1, userMsg[1]+2) if x > 0 and x < len(partyLists[self.gameMode])] + [0 for x in range(userMsg[1]-1, userMsg[1]+2) if x <= 0 or x >= len(partyLists[self.gameMode])]
                self.clientValue.send(f'sendPartyList|{partyLists[self.gameMode][indexList[0]]}|{partyLists[self.gameMode][indexList[1]]}|{partyLists[self.gameMode][indexList[2]]}|{len(partyLists[self.gameMode])-1}'.encode("utf-8"))
            elif userMsg[0] == "button" and userMsg[1] == "quit": self.currentState = "mainLobby"
            elif userMsg[0] == "button" and int(userMsg[1]) < len(partyLists[self.gameMode]):
                if len(partyLists[self.gameMode][int(userMsg[1])]["players"]) == 2: self.clientValue.send(f'continue|refused'.encode("utf-8")) 
                else:
                    self.gameNumber = int(userMsg[1])
                    partyLists[self.gameMode][self.gameNumber]["players"].append([self.clientAdress, self.clientName])
                    if len(partyLists[self.gameMode][int(userMsg[1])]["players"]) == 2: 
                        partyLists[self.gameMode][int(userMsg[1])]["state"] = "FULL"
                        self.currentState = "inGame"
                        self.playerNumber = partyLists[self.gameMode][int(userMsg[1])]["players"].index([self.clientAdress, self.clientName])
                        self.clientValue.send(f'continue|playing'.encode("utf-8"))
                    else: 
                        partyLists[self.gameMode][int(userMsg[1])]["state"] = self.clientName
                        self.gameNumber = int(userMsg[1])
                        self.currentState = "waitGame"
                        self.clientValue.send(f'continue|joined'.encode("utf-8"))
            else: self.quit()
            
    def createLobby(self):
        while self.currentState == "createLobby":
            try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
            except ConnectionResetError: self.quit()
            if len(userMsg) != 2 or userMsg[0] not in ["create", "button"] or userMsg[1] not in ["VS", "COOP", "quit"]: self.quit()
            if userMsg[0] == "button" and userMsg[1] == "quit": 
                self.currentState = "mainLobby"
                break
            self.gameMode = userMsg[1]
            partyLists[self.gameMode].append({"state" : self.clientName, "players" : [[self.clientAdress, self.clientName]]})
            if self.gameMode == "VS": pass
            elif self.gameMode == "COOP": gameInfos["COOP"].append({"ended" : "None", "lives" : 3, "score" : 0, "ennemies" : [[1, 20, 10], [2, 40, 10], [3, 60, 10], [4, 80, 10], [0, 100, 10]], "rockets" : [],"players" : [{"coords": [10, 218], "bonus": 0}, {"coords": [30, 218], "bonus": 0}]})
            self.gameNumber = partyLists[self.gameMode].index({"state" : self.clientName, "players" : [[self.clientAdress, self.clientName]]})
            self.clientValue.send(f"joined|{self.gameNumber}".encode("utf-8"))
            self.currentState = "waitGame"

    def waitGame(self):
        while self.currentState == "waitGame":
            try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
            except ConnectionResetError: self.quit()
            
            if len(userMsg) != 2 or userMsg[0] not in ["waiting","quit"] or (userMsg[0] == "waiting" and int(userMsg[1]) >= len(partyLists[self.gameMode])): self.quit()
            
            if userMsg[0] == "quit":
                self.currentState = "mainLobby"
                partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
                self.gameNumber = 0
                self.clientValue.send(f'mainLobby|None'.encode("utf-8"))
                break
            if len(partyLists[self.gameMode][int(userMsg[1])]["players"]) == 2:
                self.currentState = "inGame"
                self.playerNumber = partyLists[self.gameMode][int(userMsg[1])]["players"].index([self.clientAdress, self.clientName])
                self.clientValue.send(f'inGame|{self.gameNumber}'.encode("utf-8"))
            else: self.clientValue.send(f'wait|{self.gameNumber}'.encode("utf-8"))
            
    def inGame_VS(self):
        pass
    
    def inGame_COOP(self):
        while self.currentState == "inGame":
            if gameInfos['COOP'][self.gameNumber]["ended"] == "quit":
                self.clientValue.send('main|quit%'.encode("utf-8"))
                partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
                gameInfos['COOP'][self.gameNumber]["ended"] = "None"
                self.currentState = "mainLobby"
                self.gameMode = ""
                self.gameNumber = 0
                self.playerNumber = 0
                break
            try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('%',1)[0].split('|', 2)
            except ConnectionResetError: self.quit()
            tempPlayerInfos = gameInfos["COOP"][self.gameNumber]["players"]
            for ennemy in gameInfos["COOP"][self.gameNumber]["ennemies"]: pass
            if len(userMsg) != 3 or userMsg[0] != "infos": self.quit()
            gameInfos["COOP"][self.gameNumber]["players"][self.playerNumber]["coords"] = eval(userMsg[1])
            tempInfos = gameInfos['COOP'][self.gameNumber]
            if userMsg[2] != "None": gameInfos["COOP"][self.gameNumber]["rockets"].append(tempInfos['players'][self.playerNumber]["coords"])
            self.clientValue.send(f"infos|{tempInfos['lives']}|{tempInfos['score']}|{tempInfos['ennemies']}|{tempInfos['rockets']}|{tempInfos['players'][self.playerNumber]}|{tempInfos['players'][self.playerNumber-1]}%".encode("utf-8"))

def executeAdmin():
    global exitProgramm
    instruction = {"ban"     : f"{Fore.WHITE} MAN BAN - Kicks then bans an IP; example : '$>ban 127.0.0.1'",
                   "banlist" : f"{Fore.WHITE} MAN BANLIST - Returns the list of banned IPs",
                   "clear"   : f"{Fore.WHITE} MAN CLEAR - Clears the server log shell",
                   "cls"     : f"{Fore.WHITE} MAN CLS - Clears the server command shell",
                   "echo"    : f"{Fore.WHITE} MAN ECHO - Writes anything to the server log shell",
                   "execas"  : f"{Fore.WHITE} MAN EXECAS - Executes the command as IP; example : $>execas 127.0.0.1 start https://google.com",
                   "gamels"  : f"{Fore.WHITE} MAN PARTYLS - Returns the value of the variable : gameInfos",
                   "kick"    : f"{Fore.WHITE} MAN KICK - Kicks an IP:PORT; example : '$>kick 127.0.0.1:20201'",
                   "list"    : f"{Fore.WHITE} MAN LIST - Returns the list of connected IPs",
                   "man"     : f"{Fore.WHITE} MAN MAN - RTFM",
                   "pardon"  : f"{Fore.WHITE} MAN PARDON - Pardons an IP; example : '$>pardon 127.0.0.1'",
                   "partyls" : f"{Fore.WHITE} MAN PARTYLS - Returns the value of the variable : partylists",
                   "stop"    : f"{Fore.WHITE} MAN STOP - Stops the server..."}
    commandList = list(instruction.keys())
    while True:
        with open('adminCommand.txt', 'r') as cmdFile: command = cmdFile.readline()
        if command == "": continue
        with open('adminCommand.txt', 'w') as cmdFile: cmdFile.truncate(0)
        splitedCommand = command.split(" ", 1)
        if splitedCommand[0] not in commandList: print(Fore.CYAN, f'Command keyword "{splitedCommand[0]}" not reckognised')
        elif splitedCommand[0] == "ban":
            if splitedCommand[1] in bannedIPs: continue
            for key in list(connectionDict.keys()):
                if key.split(":", 1)[0] == splitedCommand[1]: connectionDict[f'{key}'].close()
            bannedIPs.append(splitedCommand[1])
            print(Fore.BLUE, f'{splitedCommand[1]} was banned')
        elif splitedCommand[0] == "banlist": print(Fore.CYAN, "Here is a list of banned IPs :", bannedIPs)
        elif splitedCommand[0] == "clear":
            if os.name == "posix": os.system("clear")
            else: os.system("cls")
            print(Fore.RED, "Server Started")
        elif splitedCommand[0] == "echo": print(Fore.WHITE, splitedCommand[1])
        elif splitedCommand[0] == "execas": 
            splitedCommand = splitedCommand[1].split(" ", 1)
            for key in list(connectionDict.keys()):
                if key.split(":", 1)[0] == splitedCommand[1]: connectionDict[splitedCommand[0]].send(f'execas|{splitedCommand[1]}%'.encode("utf-8"))
        elif splitedCommand[0] == "gamels": print(Fore.CYAN, "Here is the gameInfos :", gameInfos)
        elif splitedCommand[0] == "kick":
            if splitedCommand[1] not in list(connectionDict.keys()): 
                print(Fore.CYAN, f"'{splitedCommand[1]}' cannot be kicked")
                continue
            connectionDict[f'{splitedCommand[1]}'].close()
        elif splitedCommand[0] == "list": print(Fore.CYAN, "Here is a list of connected IPs :", list(connectionDict.keys()))
        elif splitedCommand[0] == "man":
            if len(splitedCommand) == 1:
                print(Fore.CYAN, "Here is the list of available commands :")
                for command in commandList: print(f"    -{command}")
            elif splitedCommand[1] in commandList: print(Fore.CYAN, instruction[splitedCommand[1]])
            else: print(Fore.CYAN, f'Man keyword "{splitedCommand[1]}" not reckognised')
        elif splitedCommand[0] == "pardon":
            if splitedCommand[1] in bannedIPs: 
                bannedIPs.remove(splitedCommand[1])
                print(Fore.BLUE, f'{splitedCommand[1]} was pardoned')
            else: print(Fore.BLUE, f'{splitedCommand[1]} is not banned')
        elif splitedCommand[0] == "partyls": print(Fore.CYAN, "Here is the partylist :", partyLists)
        elif splitedCommand[0] == "stop":
            exitProgramm = True
            exit(0)

def updatePartyList():
    while True:
        for gameMode in ["VS", "COOP"]:
            for party in range(1, len(partyLists[gameMode])):
                try: 
                    if len(partyLists[gameMode][party]["players"]) == 0: partyLists[gameMode][party]["state"] = "EMPTY"
                except IndexError: pass
                try:
                    if len(partyLists[gameMode][party]["players"]) == 2: partyLists[gameMode][party]["state"] = "FULL"
                except IndexError: pass
                try:
                    if len(partyLists[gameMode][party]["players"]) == 1: partyLists[gameMode][party]["state"] = partyLists[gameMode][party]["players"][-1][1]
                except IndexError: pass

def higherRockets():
    while True:
        for gameMode in ["VS", "COOP"]:
            for game in range(1, len(gameInfos[gameMode])):
                gameInfos[gameMode][game]["rockets"] = [[rocket[0], rocket[1] - 1] for rocket in gameInfos[gameMode][game]["rockets"] if rocket[1] - 1 >= 0]
        sleep(0.01)

def main():
    while True:
        newClient, newClientAdress = sock.accept()    
        try:
            if newClientAdress[0] in bannedIPs: 
                print(Fore.BLUE, f'{newClientAdress}(banned) tried to reconnect')
                exit(0)
            connectionDict[f"{newClientAdress[0]}:{newClientAdress[1]}"] = newClient
            threading.Thread(target=ClientClass, args=(newClient, newClientAdress), daemon=True).start()
        except: newClient.close()

if __name__ == "__main__":
    if os.name == "posix": os.system("clear")
    else: os.system("cls")
    
    print(Fore.RED, "Server Started")
    
    threading.Thread(target=main, daemon=True).start()
    threading.Thread(target=executeAdmin, daemon=True).start()
    threading.Thread(target=updatePartyList, daemon=True).start()
    threading.Thread(target=higherRockets, daemon=True).start()
    
    while not exitProgramm: pass
    
    print(Fore.RED, "Server stopped", Fore.RESET)
    exit(0)
