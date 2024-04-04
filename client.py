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
                    print(Fore.RED, f'{self.clientAdress} quit the hard way (ALT+F4)')
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
                    print(Fore.RED, f'{self.clientAdress} / {self.clientName} quit the hard way (ALT+F4)')
                    self.clientValue.close()
                    return

                if len(userMsg) == 2 and userMsg[0] == 'button' and userMsg[1] == 'quit':
                    self.clientValue.close()
                    return
                elif len(userMsg) == 2 and userMsg[0] == 'button' and userMsg[1] == 'joinLobby':
                    self.clientValue.send('lobbyList|Rien à dire...'.encode("utf-8"))
                    break
                elif len(userMsg) == 2 and userMsg[0] == 'button' and userMsg[1] == 'createLobby':
                    self.clientValue.send('continue|Rien à dire...'.encode("utf-8"))
                    break
                else:
                    self.clientValue.send('exit|Invalid message'.encode("utf-8"))
                    self.clientValue.close()
                    return

if os.name == "posix":
    os.system("clear")
else:
    os.system("cls")

print(Fore.RED, "Server Started")

while True:
    newClient, newClientAdress = sock.accept()    
    try:
        threading.Thread(target=ClientClass, args=(newClient, newClientAdress)).start()
    except:
        newClient.close()
