import time
import socket
import threading
import os
from colorama import Fore

# Initialisation du serveur sur le port `20101`
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 20101))
sock.listen()

bannedIPs = []
connectionDict = {}
threadDict = {}
exitProgramm = False

gameInfos = [{}]

partyList = [{"number" : 0, "state" : None, "players" : []}]

class ClientClass:
    def __init__(self, clientValue, clientAdress) -> None:
        self.gameNumber = 0
        self.clientValue = clientValue
        self.clientAdress = clientAdress
        self.playerNumber = 0
        self.currentState = "getNickname"

        print(Fore.BLUE, f'New connection : {self.clientAdress}')

        self.handleUser()

    def quit(self):
        print(Fore.RED, f'Someone quit : {self.clientAdress} - getNickname')
        self.clientValue.close()
        exit(1)

    def handleUser(self):
        try:
            while True:
                #getNickname
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
                    
                #mainLobby
                while self.currentState == "mainLobby":
                    try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                    except ConnectionResetError: self.quit()

                    if len(userMsg) != 2 or (userMsg[0] == 'button' and userMsg[1] == 'quit'): self.quit()
                    elif userMsg[0] == 'button' and userMsg[1] == 'joinLobby':
                        self.clientValue.send(f'continue|{len(partyList)-1}'.encode("utf-8"))
                        self.currentState = "joinLobby"
                        break
                    elif userMsg[0] == 'button' and userMsg[1] == 'waitGame':
                        self.clientValue.send('continue|skip'.encode("utf-8"))
                        self.currentState = "waitGame"
                        break
                
                #joinLobby
                while self.currentState == "joinLobby":
                    try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                    except ConnectionResetError: self.quit()
                    
                    if len(userMsg) != 2 or userMsg[0] not in ["requestPartyList", "button"]: self.quit()
                    if userMsg[0] == "requestPartyList":
                        if int(userMsg[1]) >= len(partyList) - 1: userMsg[1] = len(partyList)-2
                        if int(userMsg[1]) in [0, 1]: userMsg[1] = 2
                        else: userMsg[1] = int(userMsg[1])
                        indexList = [x for x in range(userMsg[1]-1, userMsg[1]+2) if x > 0 and x < len(partyList)] + [0 for x in range(userMsg[1]-1, userMsg[1]+2) if x <= 0 or x >= len(partyList)]
                        self.clientValue.send(f'sendPartyList|{partyList[indexList[0]]}|{partyList[indexList[1]]}|{partyList[indexList[2]]}|{len(partyList)-1}'.encode("utf-8"))
                    elif userMsg[0] == "button" and userMsg[1] == "quit": self.currentState = "mainLobby"
                    elif userMsg[0] == "button" and int(userMsg[1]) < len(partyList):
                        if len(partyList[int(userMsg[1])]["players"]) == 2: self.clientValue.send(f'continue|refused'.encode("utf-8")) 
                        else:
                            partyList[int(userMsg[1])]["players"].append(f'{self.clientAdress}')
                            if len(partyList[int(userMsg[1])]["players"]) == 2: 
                                partyList[int(userMsg[1])]["state"] = "FULL"
                                self.currentState = "inGame"
                                self.playerNumber = partyList[int(userMsg[1])]["players"].index(f'{self.clientAdress}')
                                self.clientValue.send(f'continue|playing'.encode("utf-8"))
                            else: 
                                partyList[int(userMsg[1])]["state"] = self.clientName
                                self.gameNumber = userMsg[1]
                                self.currentState = "waitGame"
                                self.clientValue.send(f'continue|joined'.encode("utf-8"))
                    else: self.quit()

                while self.currentState == "waitGame":
                    try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                    except ConnectionResetError: self.quit()
                    
                    if len(userMsg) != 2 or userMsg[0] != "waiting" or int(userMsg[1]) >= len(partyList): self.quit()
                    
                    if len(partyList[int(userMsg[1])]["players"]) == 2:
                        self.currentState = "inGame"
                        self.playerNumber = partyList[int(userMsg[1])]["players"].index(f'{self.clientAdress}')
                        self.clientValue.send(f'inGame|{self.gameNumber}'.encode("utf-8"))
                    else: self.clientValue.send(f'wait|{self.gameNumber}'.encode("utf-8"))
                    
                while self.currentState == "inGame":
                    try: userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                    except ConnectionResetError: self.quit()
                    
                    if len(userMsg) != 2 or userMsg[0] != "packets": self.quit()
                    
                    userMsg = userMsg[1].split("|", 2)
                    if len(userMsg) != 3: self.quit()
                    gameInfos[self.playerNumber]["coords"][0] += self.mX
                    gameInfos[self.playerNumber]["coords"][1] += self.mY
        except ConnectionAbortedError:
            print(Fore.RED, f'{self.clientAdress} was kicked')
            self.clientValue.close()

def executeAdmin():
    instruction = {"ban" : f"{Fore.WHITE} MAN BAN - Kicks then bans an IP; example : '$>ban 127.0.0.1'",
                   "banlist" : f"{Fore.WHITE} MAN BANLIST - Returns the list of banned IPs",
                   "clear" : f"{Fore.WHITE} MAN CLEAR - Clears the server log shell",
                   "cls" : f"{Fore.WHITE} MAN CLS - Clears the server command shell",
                   "echo" : f"{Fore.WHITE} MAN ECHO - Writes anything to the server log shell",
                   "execas" : f"{Fore.WHITE} MAN EXECAS - ... Empty ... For now!",
                   "kick" : f"{Fore.WHITE} MAN KICK - Kicks an IP;PORT; example : '$>kick 127.0.0.1;20201'",
                   "list" : f"{Fore.WHITE} MAN LIST - Returns the list of connected IPs",
                   "man" : f"{Fore.WHITE} MAN MAN - RTFM",
                   "pardon" : f"{Fore.WHITE} MAN PARDON - Pardons an IP; example : '$>pardon 127.0.0.1'",
                   "stop" : f"{Fore.WHITE} MAN STOP - Stops the server..."}
    commandList = list(instruction.keys())
    global exitProgramm
    while True:
        with open('adminCommand.txt', 'r') as cmdFile:
            command = cmdFile.readline()
        if command != "" : 
            with open('adminCommand.txt', 'w') as file:
                file.truncate(0)
            splitedCommand = command.split(" ", 1)
            if splitedCommand[0] not in commandList:
                print(Fore.CYAN, f'Command keyword "{splitedCommand[0]}" not reckognised')
                continue
            if splitedCommand[0] == "stop":
                exitProgramm = True
                exit(0)
            elif splitedCommand[0] == "clear":
                if os.name == "posix":
                    os.system("clear")
                else:
                    os.system("cls")
                print(Fore.RED, "Server Started")
            elif splitedCommand[0] == "man":
                if len(splitedCommand) == 1:
                    print(Fore.CYAN, "Here is the list of available commands :")
                    for command in commandList: print(f"    -{command}")
                elif splitedCommand[1] in commandList: print(instruction[splitedCommand[1]])
                else: print(Fore.CYAN, f'Man keyword "{splitedCommand[1]}" not reckognised')
            elif splitedCommand[0] == "echo":
                print(Fore.WHITE, splitedCommand[1])
            elif splitedCommand[0] == "list":
                print(Fore.CYAN, "Here is a list of connected IPs :", list(connectionDict.keys()))
            elif splitedCommand[0] == "kick":
                if splitedCommand[1] not in list(connectionDict.keys()): 
                    print(Fore.CYAN, f"'{splitedCommand[1]}' cannot be kicked")
                    continue
                connectionDict[f'{splitedCommand[1]}'].close()
            elif splitedCommand[0] == "ban":
                if splitedCommand[1] in bannedIPs: continue
                for key in list(connectionDict.keys()):
                    if key.split(";", 1)[0] == splitedCommand[1]: connectionDict[f'{key}'].close()
                bannedIPs.append(splitedCommand[1])
                print(Fore.BLUE, f'{splitedCommand[1]} was banned')
            elif splitedCommand[0] == "pardon":
                if splitedCommand[1] in bannedIPs: 
                    bannedIPs.remove(splitedCommand[1])
                    print(Fore.BLUE, f'{splitedCommand[1]} was pardoned')
                else: print(Fore.BLUE, f'{splitedCommand[1]} is not banned')
            elif splitedCommand[0] == "banlist":
                print(Fore.CYAN, "Here is a list of banned IPs :", bannedIPs)
            elif splitedCommand[0] == "execas":
                print(Fore.CYAN, "Commin' soon!")

def main():
    while True:
        newClient, newClientAdress = sock.accept()    
        try:
            if newClientAdress[0] in bannedIPs: 
                print(Fore.BLUE, f'{newClientAdress}(banned) tried to reconnect')
                exit(0)
            connectionDict[f"{newClientAdress[0]};{newClientAdress[1]}"] = newClient
            threadDict[f"{newClientAdress[0]};{newClientAdress[1]}"] = threading.Thread(target=ClientClass, args=(newClient, newClientAdress), daemon=True)
            threadDict[f"{newClientAdress[0]};{newClientAdress[1]}"].start()
        except:
            newClient.close()

if os.name == "posix":
    os.system("clear")
else:
    os.system("cls")

print(Fore.RED, "Server Started")

threading.Thread(target=executeAdmin, daemon=True).start()
threading.Thread(target=main, daemon=True).start()

while not exitProgramm:
    pass

print(Fore.RED, "Server stopped", Fore.RESET)
exit(0)
