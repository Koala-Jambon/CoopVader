import time
import socket
import threading
import os
from colorama import Fore
from time import sleep, time
from datetime import datetime

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

        write(Fore.BLUE, f'New connection : {self.clientAdress}')

        self.handleUser()

    def quit(self):
        write(Fore.RED, f'Someone quit : {self.clientAdress} - {self.currentState}')
        self.clientValue.close()
        del connectionDict[f"{self.clientAdress[0]}:{self.clientAdress[1]}"]
        if self.currentState == "inGame": gameInfos[self.gameMode][self.gameNumber]["ended"] = "quit"
        if self.gameNumber != 0: partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
        exit(1)

    def handleUser(self):
        try:
            if self.currentState == "getNickname": self.getNickname()
            while True: getattr(self, self.currentState)()
        except (ConnectionAbortedError, ConnectionResetError) as Error:
            if type(Error) == ConnectionAbortedError: write(Fore.RED, f'{self.clientAdress} was kicked')
            else: self.quit()
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
                write(Fore.GREEN, f'{self.clientAdress} -> {self.clientName}')
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
                        self.clientValue.send(f'continue|playing{self.playerNumber}'.encode("utf-8"))
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
            if self.gameMode == "VS": gameInfos["VS"].append({"ended" : "None", "ennemies" : [], "rockets" : [], "players" : [{"coords": [34, 104], "lives" : 3, "score" : 0, "newRockets" : [], "ennemiesRem" : []}, {"coords": [194, 104], "lives" : 3, "score" : 0, "newRockets" : [], "ennemiesRem" : []}]})
            elif self.gameMode == "COOP": gameInfos["COOP"].append({"ended" : "None", "lives" : 3, "score" : 0, "ennemies" : [], "rockets" : [], "players" : [{"coords": [34, 104], "newRockets" : [], "ennemiesRem" : []}, {"coords": [194, 104], "newRockets" : [], "ennemiesRem" : []}]})
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
                self.clientValue.send(f'inGame|{self.playerNumber}'.encode("utf-8"))
            else: self.clientValue.send(f'wait|{self.gameNumber}'.encode("utf-8"))
            
    def inGame(self):
        GAMEMODE_CONST = 2 if self.gameMode == "VS" else 0
        while self.currentState == "inGame":
            endedState = gameInfos[self.gameMode][self.gameNumber]["ended"]
            if endedState[:4] == "Lost" or endedState[:3] == "Won" or endedState == "quit":
                self.clientValue.send(f'main|{endedState}%'.encode("utf-8"))
                partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
                gameInfos[self.gameMode][self.gameNumber]["ended"] = "None"
                self.currentState, self.gameMode, self.gameNumber, self.playerNumber = "mainLobby", "", 0, 0
                break

            try: userMsg = self.clientValue.recv(1024).decode("utf-8")
            except ConnectionResetError: self.quit()
            if "hasEnded" in userMsg:
                userMsg = userMsg.split("%")
                for msg in userMsg: 
                    if "hasEnded" in msg: userMsg = msg.split('|', 1) ; break
                self.clientValue.send(f'main|{msg[1]}%'.encode("utf-8"))
                partyLists[self.gameMode][self.gameNumber]["players"].remove([self.clientAdress, self.clientName])
                self.currentState, self.gameMode, self.gameNumber, self.playerNumber = "mainLobby", "", 0, 0
                break
            if "Shot" in userMsg:
                userMsg = userMsg.split("%")
                for msg in userMsg: 
                    if "Shot" in msg: userMsg = msg.split('|', 3 + GAMEMODE_CONST) ; break
            else: userMsg = userMsg.split('%',1)[0].split('|', 3 + GAMEMODE_CONST)
            if len(userMsg) != 4 + GAMEMODE_CONST or userMsg[0] != "infos": self.quit()
            gameInfos[self.gameMode][self.gameNumber]["players"][self.playerNumber]["coords"] = [int(userMsg[1]), int(userMsg[2])]
            if self.gameMode == "VS": gameInfos["VS"][self.gameNumber]["players"][self.playerNumber]["lives"], gameInfos["VS"][self.gameNumber]["players"][self.playerNumber]["score"] = int(userMsg[3]), int(userMsg[4])
            tempInfos = gameInfos[self.gameMode][self.gameNumber]
            tempRock = tempInfos["players"][self.playerNumber]["newRockets"].copy()
            tempEnn = tempInfos["players"][self.playerNumber]["ennemiesRem"].copy()
            if userMsg[3 + GAMEMODE_CONST][:4] == "Shot": gameInfos[self.gameMode][self.gameNumber]["players"][self.playerNumber-1]["newRockets"].append([tempInfos['players'][self.playerNumber]['coords'][0]+7, tempInfos['players'][self.playerNumber]['coords'][1]])
            if userMsg[3 + GAMEMODE_CONST][4:] == "+": gameInfos[self.gameMode][self.gameNumber]["players"][self.playerNumber-1]["newRockets"].append([tempInfos['players'][self.playerNumber]['coords'][0]+17, tempInfos['players'][self.playerNumber]['coords'][1]]) ; gameInfos[self.gameMode][self.gameNumber]["players"][self.playerNumber-1]["newRockets"].append([tempInfos['players'][self.playerNumber]["coords"][0]-3, tempInfos['players'][self.playerNumber]["coords"][1]])
            if self.gameMode == "VS": self.clientValue.send(f"infos|{tempInfos['players'][self.playerNumber-1]['lives']}|{tempInfos['players'][self.playerNumber-1]['score']}|{tempEnn}|{tempRock}|{tempInfos['players'][self.playerNumber-1]['coords']}%".encode("utf-8"))
            else: self.clientValue.send(f"infos|{tempInfos['lives']}|{tempInfos['score']}|{tempEnn}|{tempRock}|{tempInfos['players'][self.playerNumber-1]['coords']}%".encode("utf-8"))
            for newRock in tempRock: gameInfos[self.gameMode][self.gameNumber]["players"][self.playerNumber]["newRockets"].remove(newRock)
            #for newEnn in tempRock: gameInfos[self.gameMode][self.gameNumber]["players"][self.playerNumber]["ennemiesRem"].remove(newEnn)

def executeAdmin():
    global exitProgramm
    instruction = {"ban"     : "MAN BAN - Kicks then bans an IP; example : '$>ban 127.0.0.1'",
                   "banlist" : "MAN BANLIST - Returns the list of banned IPs",
                   "clear"   : "MAN CLEAR - Clears the server log shell",
                   "cls"     : "MAN CLS - Clears the server command shell",
                   "echo"    : "MAN ECHO - Writes anything to the server log shell",
                   "execas"  : "MAN EXECAS - Executes the command as IP; example : $>execas 127.0.0.1 start https://google.com",
                   "gamels"  : "MAN PARTYLS - Returns the value of the variable : gameInfos",
                   "kick"    : "MAN KICK - Kicks an IP:PORT; example : '$>kick 127.0.0.1:20201'",
                   "list"    : "MAN LIST - Returns the list of connected IPs",
                   "man"     : "MAN MAN - RTFM",
                   "pardon"  : "MAN PARDON - Pardons an IP; example : '$>pardon 127.0.0.1'",
                   "partyls" : "MAN PARTYLS - Returns the value of the variable : partylists",
                   "stop"    : "MAN STOP - Stops the server..."}
    commandList = list(instruction.keys())
    while True:
        with open('adminCommand.txt', 'r') as cmdFile: command = cmdFile.readline()
        if command == "": continue
        with open('adminCommand.txt', 'w') as cmdFile: cmdFile.truncate(0)
        splitedCommand = command.split(" ", 1)
        match splitedCommand[0]:	
            case "ban":
                if splitedCommand[1] in bannedIPs: continue
                for key in list(connectionDict.keys()):
                    if key.split(":", 1)[0] == splitedCommand[1]: connectionDict[f'{key}'].close()
                bannedIPs.append(splitedCommand[1])
                write(Fore.BLUE, f'{splitedCommand[1]} was banned')
            case "banlist": write(Fore.CYAN, f"Here is a list of banned IPs : {bannedIPs}")
            case "clear":
                write(Fore.RESET, "Server shell cleared")
                if os.name == "posix": os.system("clear")
                else: os.system("cls")
                print(Fore.RED, "Server Started")
            case "echo": write(Fore.WHITE, splitedCommand[1])
            case "execas":
                splitedCommand = splitedCommand[1].split(" ", 1)
                for key in list(connectionDict.keys()):
                    if key.split(":", 1)[0] == splitedCommand[1]: connectionDict[splitedCommand[0]].send(f'execas|{splitedCommand[1]}%'.encode("utf-8"))
            case "gamels": write(Fore.CYAN, f"Here is the gameInfos : {gameInfos}")
            case "kick": 
                if splitedCommand[1] not in list(connectionDict.keys()): 
                    write(Fore.CYAN, f"'{splitedCommand[1]}' cannot be kicked")
                    continue
                connectionDict[f'{splitedCommand[1]}'].close()
            case "list": write(Fore.CYAN, f"Here is a list of connected IPs : {list(connectionDict.keys())}")
            case "man":
                if len(splitedCommand) == 1:
                    manMsg = "Here is the list of available commands :"
                    for command in commandList: manMsg += (f"\n    -{command}")
                    write(Fore.CYAN, manMsg)
                elif splitedCommand[1] in commandList: write(Fore.WHITE, instruction[splitedCommand[1]])
                else: write(Fore.CYAN, f'Man keyword "{splitedCommand[1]}" not reckognised')
            case "pardon":
                if splitedCommand[1] in bannedIPs: 
                    bannedIPs.remove(splitedCommand[1])
                    write(Fore.BLUE, f'{splitedCommand[1]} was pardoned')
                else: write(Fore.BLUE, f'{splitedCommand[1]} is not banned')
            case "partyls": write(Fore.CYAN, f"Here is the partylist : {partyLists}")
            case "stop": 
                exitProgramm = True
                exit(0)
            case _: write(Fore.CYAN, f'Command keyword "{splitedCommand[0]}" not reckognised')

def updatePartyList():
    while True:
        for gameMode in ["VS", "COOP"]:
            for party in range(1, len(partyLists[gameMode])):
                try: 
                    if len(partyLists[gameMode][party]["players"]) == 0: partyLists[gameMode][party]["state"] = "EMPTY"
                    if len(partyLists[gameMode][party]["players"]) == 2: partyLists[gameMode][party]["state"] = "FULL"
                    if len(partyLists[gameMode][party]["players"]) == 1: partyLists[gameMode][party]["state"] = partyLists[gameMode][party]["players"][-1][1]
                except IndexError: pass

def higherRockets():
    rocketDelay = 0        
    while True:
        curTime = time()
        rocketDiff = round((curTime-rocketDelay) * 100)
        if rocketDiff == 0: continue
        rocketDelay = curTime
        for gameMode in ["VS", "COOP"]:
            for game in range(1, len(gameInfos[gameMode])):
                gameInfos[gameMode][game]["rockets"] = [[rocket[0], rocket[1] - rocketDiff] for rocket in gameInfos[gameMode][game]["rockets"] if rocket[1] - rocketDiff >= 0]

def write(Color, Message): 
    print(Color, Message)
    if "\n" in Message: Message = Message.split("\n") ; Message = "\n".join([Message[0]] +[" "*22+msg for msg in Message[1:]])
    with open("serverLogs.txt", "a") as logsFile: logsFile.write(f"{datetime.now().strftime('%m/%d/%Y %H:%M:%S')} - {Message}\n")

def main():
    while True:
        newClient, newClientAdress = sock.accept()    
        try:
            if newClientAdress[0] in bannedIPs: 
                write(Fore.BLUE, f'{newClientAdress}(banned) tried to reconnect')
                exit(0)
            connectionDict[f"{newClientAdress[0]}:{newClientAdress[1]}"] = newClient
            threading.Thread(target=ClientClass, args=(newClient, newClientAdress), daemon=True).start()
        except: newClient.close()

if __name__ == "__main__":
    if os.name == "posix": os.system("clear")
    else: os.system("cls")
    
    write(Fore.RED, "Server Started")
    
    threading.Thread(target=main, daemon=True).start()
    threading.Thread(target=executeAdmin, daemon=True).start()
    threading.Thread(target=updatePartyList, daemon=True).start()
    threading.Thread(target=higherRockets, daemon=True).start()
    
    try:
        while not exitProgramm: pass
    except KeyboardInterrupt: pass

    write(Fore.RED, "Server stopped")
    print(Fore.RESET)
    exit(0)
