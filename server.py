import time
import socket
import threading
import os
from colorama import Fore, Style

# Initialisation du serveur sur le port `20101`
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 20101))
sock.listen()

class ClientClass:
    def __init__(self, clientValue, clientAdress) -> None:
        self.clientValue = clientValue
        self.clientAdress = clientAdress

        print(Fore.BLUE, f'New Connection : {self.clientAdress}', Style.RESET_ALL)

        self.getUserNickname()

    def getUserNickname(self):
        while True:
            userMsg = self.clientValue.recv(1024).decode("utf-8").split('|', 1)
            if len(userMsg) == 2 and userMsg[0] == "sendName" and len(userMsg[1]) <= 12:   
                self.clientName = userMsg[1]
                print(Fore.GREEN, f'{self.clientAdress} -> {self.clientName}', Style.RESET_ALL)
                self.clientValue.send('continue|Rien à dire...'.encode("utf-8"))
            else:
                self.clientValue.send('exit|Invalid message'.encode("utf-8"))
                self.clientValue.close()
                return
            
    def mainLobby(self):
        while True:
            pass

if os.name == "posix":
    os.system("clear")
else:
    os.system("cls")

print(Fore.RED, "Server Started", Style.RESET_ALL)

while True:
    newClient, newClientAdress = sock.accept()    
    try:
        threading.Thread(target=ClientClass, args=(newClient, newClientAdress)).start()
    except:
        newClient.close()
