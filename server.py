import time
import socket
import threading
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

        print(Fore.BLUE, f'Nouveau client : {self.clientAdress}')

while True:
    newClient, newClientAdress = sock.accept()    
    try:
        threading.Thread(target=ClientClass, args=(newClient, newClientAdress)).start()
    except:
        newClient.close()
