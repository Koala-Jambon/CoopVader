
import time
import rich
import json
import random
from colorama import Fore, Style
import socket
import threading

import utils

# Initialisation du serveur sur le port `20101`
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 20101))
sock.listen()

# Création du lobby et du tableau des parties
lobby = {}
party = {}


def client_init(client_jouer: socket.socket, client_address: tuple):
    try:
        handle_client(client_jouer, client_address)
    except OSError or KeyError or ValueError:
        print(Fore.RED + "Un client nous a quitté...")
        print(Style.RESET_ALL)
        if client_address in lobby:
            # On vérifie qu'il n'est pas dans une partie
            if lobby[client_address]["partie_id"]:
                print("Suppression d'un client d'une PARTIE")
                party[lobby[client_address]["partie_id"]]["joueurs"].remove(client_address)
            lobby.pop(client_address)
        client_jouer.close()


def handle_client(client_jouer: socket.socket, client_address):
    print(Fore.BLUE + f"Client : {client_address}")
    message = None
    while message != "/quit":
        data = client_jouer.recv(1024).decode("utf-8")
        print(Fore.BLUE + f"Message de {client_address} : {data}")
        print(Style.RESET_ALL)
        if data == "":
            print("Message vide")
            client_jouer.close()
            message = "/quit"
            continue

        data = data.split()

        print(data[0])
        
    print("Fermeture d'un client")
    raise OSError


def fin_partie(game, client_in_end, client_address):
    client_in_end.send(json.dumps({"message": "/endgame", "board": game.board}).encode("utf-8"))
    party[lobby[client_address]["partie_id"]]["joueurs"].remove(client_address)
    print("On a sortie un joueur de la partie")
    lobby[client_address]["status"] = "disponible"
    lobby[client_address]["partie_id"] = None
    handle_client(client_in_end, client_address)

   
error = False
while not error:
    print(Fore.GREEN + "Boucle en attente d'un client...")
    print(Style.RESET_ALL)
    client, client_address_while = sock.accept()
    try:
        threading.Thread(target=client_init, args=(client, client_address_while)).start()
    except OSError or IndexError as e:
        print(utils.error_log(e))
        client.close()
        print(Fore.RED + "Un thread nous a quitté")
        print(Style.RESET_ALL)

    print("Le thread a été lancé")

   