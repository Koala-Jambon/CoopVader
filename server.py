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

exitProgramm = False

partyList = [{"number" : 0, "state" : None}, {"number" : 1, "state" : "one"}]

class ClientClass:
    def __init__(self, clientValue, clientAdress) -> None:
        self.clientValue = clientValue
        self.clientAdress = clientAdress
        self.currentState = "getNickname"

        print(Fore.BLUE, f'New Connection : {self.clientAdress}')

        self.handleUser()

    def handleUser(self):
        while True:
            #getNickname
            while self.currentState == "getNickname":
                try:
                    userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                except ConnectionResetError:
                    print(Fore.RED, f'Someone quit : {self.clientAdress} - getNickname')
                    self.clientValue.close()
                    return
                if len(userMsg) == 2 and userMsg[0] == "sendName" and len(userMsg[1]) <= 12:   
                    self.clientName = userMsg[1]
                    print(Fore.GREEN, f'{self.clientAdress} -> {self.clientName}')
                    self.clientValue.send('continue|Rien à dire...'.encode("utf-8"))
                    self.currentState = "mainLobby"
                    break
                else:
                    self.clientValue.send('exit|Invalid message'.encode("utf-8"))
                    self.clientValue.close()
                    return
                
            #mainLobby
            while self.currentState == "mainLobby":
                try:
                    userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                except ConnectionResetError:
                    print(Fore.RED, f'Someone quit : {self.clientAdress} | {self.clientName} - mainLobby')
                    self.clientValue.close()
                    return

                if len(userMsg) == 2 and userMsg[0] == 'button' and userMsg[1] == 'quit':
                    print(Fore.RED, f'Someone quit : {self.clientAdress} | {self.clientName} - mainLobby')
                    self.clientValue.close()
                    return
                elif len(userMsg) == 2 and userMsg[0] == 'button' and userMsg[1] == 'joinLobby':
                    self.clientValue.send(f'continue|{len(partyList)-1}'.encode("utf-8"))
                    self.currentState = "joinLobby"
                    break
                elif len(userMsg) == 2 and userMsg[0] == 'button' and userMsg[1] == 'createLobby':
                    self.clientValue.send('continue|Rien à dire...'.encode("utf-8"))
                    self.currentState = "createLobby"
                    break
                else:
                    self.clientValue.send('exit|Invalid message'.encode("utf-8"))
                    self.clientValue.close()
                    return
            
            #joinLobby
            while self.currentState == "joinLobby":
                try:
                    userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                except ConnectionResetError:
                    print(Fore.RED, f'Someone quit : {self.clientAdress} | {self.clientName} - joinLobby')
                    self.clientValue.close()
                    return
                
                if len(userMsg) != 2 or userMsg[0] not in ["requestPartyList", "button"]: return 1
                if userMsg[0] == "requestPartyList":
                    if int(userMsg[1]) >= len(partyList) - 1: userMsg[1] = len(partyList)-2
                    if int(userMsg[1]) in [0, 1]: userMsg[1] = 2
                    userMsg[1] = int(userMsg[1])
                    indexList = [x for x in range(userMsg[1]-1, userMsg[1]+2) if x > 0 and x < len(partyList)] + [0 for x in range(userMsg[1]-1, userMsg[1]+2) if x <= 0 or x >= len(partyList)]
                    self.clientValue.send(f'sendPartyList|{partyList[indexList[0]]}|{partyList[indexList[1]]}|{partyList[indexList[2]]}|{len(partyList)-1}'.encode("utf-8"))
                elif userMsg[0] == "button":
                    if userMsg[1] == "quit": 
                        self.currentState = "mainLobby"
                        break

            while self.currentState == "createLobby":
                try:
                    userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
                except ConnectionResetError:
                    print(Fore.RED, f'Someone quit : {self.clientAdress} | {self.clientName} - joinLobby')
                    self.clientValue.close()
                    return

def executeAdmin():
    global exitProgramm
    while True:
        with open('adminCommand.txt', 'r') as cmdFile:
            command = cmdFile.readline()
        if command != "" : 
            with open('adminCommand.txt', 'w') as file:
                file.truncate(0)
            
            splitedCommand = command.split(" ", 1)
            if splitedCommand[0] not in ["stop", "clear", "echo", "execas"]:
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
            elif splitedCommand[0] == "echo":
                print(Fore.WHITE, splitedCommand[1])
            elif splitedCommand[0] == "execas":
                print(Fore.CYAN, "Commin' soon!")

def main():
    while True:
        newClient, newClientAdress = sock.accept()    
        try:
            threading.Thread(target=ClientClass, args=(newClient, newClientAdress)).start()
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
