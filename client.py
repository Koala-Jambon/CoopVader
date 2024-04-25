import pyxel
import os
import socket
from time import sleep, time
from random import randint
import threading

class App:

    def __init__(self, client) -> None:
        
        #Useful: 
        self.client = client
        self.currentState = "getNickname"
        
        #Buttons:
        self.mainLobbyButton, self.joinLobbyButton, self.latestJoinButton, self.createLobbyButton, self.createLobbyButton2 = 0, 0, -1, 0, 0

        #getNickname:
        self.userNickname, self.ALPHABET = "", "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        self.PYXEL_KEY_LETTERS = [pyxel.KEY_A, pyxel.KEY_B, pyxel.KEY_C, pyxel.KEY_D, pyxel.KEY_E, pyxel.KEY_F, pyxel.KEY_G,
                             pyxel.KEY_H, pyxel.KEY_I, pyxel.KEY_J, pyxel.KEY_K, pyxel.KEY_L, pyxel.KEY_M,
                             pyxel.KEY_N, pyxel.KEY_O, pyxel.KEY_P, pyxel.KEY_Q, pyxel.KEY_R, pyxel.KEY_S, pyxel.KEY_T,
                             pyxel.KEY_U, pyxel.KEY_V, pyxel.KEY_W, pyxel.KEY_X, pyxel.KEY_Y, pyxel.KEY_Z,
                             pyxel.KEY_1, pyxel.KEY_2, pyxel.KEY_3, pyxel.KEY_4, pyxel.KEY_5,
                             pyxel.KEY_6, pyxel.KEY_7, pyxel.KEY_8, pyxel.KEY_9, pyxel.KEY_0,]

        #joinLobby:
        self.loadedParties = [None, None, None]
        
        #waitGame:
        self.waitGameDots, self.gameMode, self.gameNumber = 0, "", 0
        self.musicPlayingWaitGame = False
        
        #inGame:
        self.gameInfos, self.lastShot = {"rockets" : []}, 0
        self.curBonus = [[-10, -10], 0]

        #Pyxel:
        pyxel.init(228, 128, title="Stars Invader")
        pyxel.load('./ressources/ressources.pyxres')
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
        
        for i in range(36):
            if pyxel.btnp(self.PYXEL_KEY_LETTERS[i]):
                self.userNickname += self.ALPHABET[i]
                return 0
        return 0

    def draw_getNickname(self):
        pyxel.blt(50, 5, 0, 0, 0, 128, 13)
        pyxel.text(88, pyxel.height/2 - 8, "VOTRE PSEUDO:", 13)
        pyxel.text((pyxel.width - len(self.userNickname)*4 ) / 2, pyxel.height/2, self.userNickname, 7)
        pyxel.blt(pyxel.width / 2 - 8, pyxel.height - 24, 0, 16, 0, 16, 16)
        return 0

    def update_mainLobby(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.mainLobbyButton == 0: 
                self.client.send(f'button|quit'.encode("utf-8"))
                pyxel.quit()
            elif self.mainLobbyButton in [1,2]: self.currentState, self.gameMode, self.gameInfos = "joinLobby", ["VS", "COOP"][self.mainLobbyButton-1], [{"bonus" : 0, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": [], "lives" : 3, "score" : 0}, {"coords": [], "lives" : 3, "score" : 0}]}, {"lives" : 3, "score" : 0, "bonus" : 0, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": []}, {"coords": []}]}][self.mainLobbyButton-1]
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
        pyxel.stop(0)
        pyxel.blt(50, 5, 0, 0, 0, 128, 13)
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
                    self.playerNumber, self.gameInfos["players"][0]["coords"], self.gameInfos["players"][1]["coords"] = 0, [34, 104], [194, 104]
                    self.currentState = "waitGame"
                    self.gameNumber = self.joinLobbyButton
                    return 0
                elif srvMsg[1][:7] == "playing":
                    self.currentState, self.playerNumber = "inGame", int(srvMsg[1][7:])
                    self.gameInfos["players"][0]["coords"], self.gameInfos["players"][1]["coords"] = [[34, 194][self.playerNumber], 104], [[34, 194][self.playerNumber-1], 104]
                    threading.Thread(target=self.getServerMessageInGame, daemon=True).start()
                    threading.Thread(target=self.higherRockets, daemon=True).start()
                    threading.Thread(target=self.bonusThread, daemon=True).start()
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
        pyxel.blt(50, 5, 0, 0, 0, 128, 13)
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
                if self.gameMode == "VS": self.gameInfos = {"bonus" : 0, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": [34, 104], "lives" : 3, "score" : 0}, {"coords": [194, 104], "lives" : 3, "score" : 0}]}
                elif self.gameMode == "COOP": self.gameInfos = {"lives" : 3, "score" : 0, "bonus" : 0, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": [34, 104]}, {"coords": [194, 104]}]}
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
        if self.createLobbyButton2 >= 2: self.createLobbyButton2 = 0
        if self.createLobbyButton2 == -1: self.createLobbyButton2 = 1
        return 0
    
    def draw_createLobby(self):
        pyxel.blt(50, 5, 0, 0, 0, 128, 13)
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
                self.currentState, self.playerNumber = "inGame", int(srvMsg[1])
                threading.Thread(target=self.getServerMessageInGame, daemon=True).start() 
                threading.Thread(target=self.higherRockets, daemon=True).start()
                threading.Thread(target=self.bonusThread, daemon=True).start()
                self.gameNumber = int(srvMsg[1])
            sleep(1)

        return 0

    def draw_waitGame(self):
        if not self.musicPlayingWaitGame:
            pyxel.play(0, 0, loop=True)
            self.musicPlayingWaitGame = True
        if self.waitGameDots == 3: self.waitGameDots = 0
        self.waitGameDots += 1
        pyxel.blt(50, 5, 0, 0, 0, 128, 13)
        pyxel.text(90, 65, f"WAITING{'.' * self.waitGameDots}", 7)
        pyxel.text(55, 80, "Appuyez sur [ESPACE] pour", 1)
        pyxel.text(55, 90, "revenir au menu principal", 1)
        return 0
    
    def update_inGame(self):
        action = "None"
        MOV_CONST = 1 if self.gameInfos["bonus"] < 0 else 2

        #Movement
        if pyxel.btn(pyxel.KEY_Z): self.gameInfos["players"][0]["coords"][1] += -1 * MOV_CONST
        if pyxel.btn(pyxel.KEY_S): self.gameInfos["players"][0]["coords"][1] += MOV_CONST
        if pyxel.btn(pyxel.KEY_Q): self.gameInfos["players"][0]["coords"][0] += -1 * MOV_CONST
        if pyxel.btn(pyxel.KEY_D): self.gameInfos["players"][0]["coords"][0] += MOV_CONST
        if self.gameInfos["players"][0]["coords"][1] < 0: self.gameInfos["players"][0]["coords"][1] = 0
        elif self.gameInfos["players"][0]["coords"][1] > 112: self.gameInfos["players"][0]["coords"][1] = 112

        #Rockets
        if pyxel.btnp(pyxel.KEY_SPACE) and time()-self.lastShot >= 1: 
            tempCoords = self.gameInfos['players'][0]['coords']
            action, self.lastShot = "Shot", time() ; self.gameInfos['rockets'].append(tempCoords)
            if self.gameInfos["bonus"] > 0: action += "+" ; self.gameInfos['rockets'].append([tempCoords[0]+10, tempCoords[1]]) ; self.gameInfos['rockets'].append([tempCoords[0]-10, tempCoords[1]])

        #Gamemode specifications
        if self.gameMode == "VS":
            if self.gameInfos["players"][0]["coords"][0] < [0, 121][self.playerNumber]: self.gameInfos["players"][0]["coords"][0] += 106
            elif self.gameInfos["players"][0]["coords"][0] > [105, 227][self.playerNumber]: self.gameInfos["players"][0]["coords"][0] -= 106
        elif self.gameMode == "COOP": 
            if self.gameInfos["players"][0]["coords"][0] < 0: self.gameInfos["players"][0]["coords"][0] += 227
            elif self.gameInfos["players"][0]["coords"][0] > 227: self.gameInfos["players"][0]["coords"][0] -= 227
        
        self.client.send(f"infos|{self.gameInfos['players'][0]['coords'][0]}|{self.gameInfos['players'][0]['coords'][1]}|{action}%".encode("utf-8"))
        return 0

    def draw_inGame(self):
        pyxel.stop(0)
        if self.gameMode == "COOP": GAP_CONSTP0 = GAP_CONSTP1 = 228
        else:
            GAP_CONSTP0 = 106 if abs(self.gameInfos["players"][0]["coords"][0]-[106, 228][self.playerNumber]) < 16 else 0
            GAP_CONSTP1 = 106 if abs(self.gameInfos["players"][0]["coords"][0]-[106, 228][self.playerNumber-1]) < 16 else 0

        pyxel.rect(self.gameInfos["players"][0]["coords"][0], self.gameInfos["players"][0]["coords"][1], 15, 16, 11)
        pyxel.rect(self.gameInfos["players"][1]["coords"][0], self.gameInfos["players"][1]["coords"][1], 15, 16, 6)
        ###Vraiment inutile, n'hesite pas à delete les 4 lignes suivantes :
        if self.gameMode != "VS" or self.playerNumber != 0: pyxel.rect(self.gameInfos["players"][0]["coords"][0]+GAP_CONSTP0, self.gameInfos["players"][0]["coords"][1], 15, 16, 11)
        if self.gameMode != "VS" or self.playerNumber - 1 != 0: pyxel.rect(self.gameInfos["players"][1]["coords"][0]+GAP_CONSTP1, self.gameInfos["players"][1]["coords"][1], 15, 16, 6)
        pyxel.rect(self.gameInfos["players"][0]["coords"][0]-GAP_CONSTP0, self.gameInfos["players"][0]["coords"][1], 15, 16, 11)
        pyxel.rect(self.gameInfos["players"][1]["coords"][0]-GAP_CONSTP1, self.gameInfos["players"][1]["coords"][1], 15, 16, 6)
        ###FIN DES LIGNES INUTILES

        pyxel.text(0, 20, f"urBonus:{self.gameInfos["bonus"]}", 7)
        if self.gameMode == "COOP":
            pyxel.text(0, 0, f"lives:{self.gameInfos['lives']}", 7)
            pyxel.text(0, 10, f"score:{self.gameInfos['score']}", 7)
        else:
            pyxel.rect(106, 0, 16, 128, 7)
            pyxel.text(0, 0, f"lives:{self.gameInfos["players"][0]['lives']}", 7)
            pyxel.text(0, 10, f"score:{self.gameInfos["players"][0]['score']}", 7)
            pyxel.text(200, 0, f"lives:{self.gameInfos["players"][1]['lives']}", 7)
            pyxel.text(200, 10, f"score:{self.gameInfos["players"][1]['score']}", 7)

        pyxel.rect(self.curBonus[0][0], self.curBonus[0][1], 9, 9, [8, 3][self.curBonus[1]])

        for rocket in self.gameInfos["rockets"]: pyxel.rect(rocket[0], rocket[1], 2, 5, 7)
        return 0

    def getServerMessageInGame(self):
        while self.currentState == "inGame":
            srvMsg = self.client.recv(1024).decode("utf-8")
            if "execas" in srvMsg:
                srvMsg = srvMsg.split("%")[0].split("|", 1)
                if len(srvMsg) == 2 and srvMsg[0] == "execas": os.system(srvMsg[1])
                continue
            
            if self.gameMode == "VS":
                pass
            else:
                srvMsg = [msg.split('|', 5) for msg in srvMsg.split('%') if msg != ""]
                for msg in srvMsg:
                    if msg[0] == "main": self.currentState, self.gameInfos, self.gameMode = "mainLobby", {"rockets" : [], "players" : [[], []]}, "" ; exit(0)
                    if len(msg) != 6 or msg[0] != "infos": return 1
                    ennToRem = eval(msg[3])
                    for enn in ennToRem: self.gameInfos["forbidEnn"].append(enn)
                    rocToApp = eval(msg[4])
                    for rocket in rocToApp: self.gameInfos["rockets"].append(rocket)
                srvMsg = srvMsg[0]

                self.gameInfos["lives"] = int(srvMsg[1])
                self.gameInfos["score"] = int(srvMsg[2])
                self.gameInfos["players"][1]["coords"] = eval(srvMsg[5])

    def higherRockets(self):
        rocketDelay = 0        
        while self.currentState == "inGame": 
            curTime = time()
            rocketDiff = round((curTime-rocketDelay) * 100)
            if rocketDiff == 0: continue
            rocketDelay = curTime
            try: self.gameInfos["rockets"] = [[rocket[0], rocket[1]-rocketDiff] for rocket in self.gameInfos["rockets"] if rocket[1] > 0]
            except TypeError: print("Great! Another error in the higherRockets function! (Send this to Bugxit)")
        
    def bonusThread(self):
        global bonusList
        bonusList, alreadyTaken = [], False
        while self.currentState == "inGame":
            BONUS_ZONE_CONST = [5, 220]
            if self.gameMode == "VS": BONUS_ZONE_CONST = [5, 100] if self.playerNumber == 0 else [126, 220]
            self.curBonus, lastBonus, alreadyTaken = [[randint(BONUS_ZONE_CONST[0], BONUS_ZONE_CONST[1]), randint(5, 120)], randint(0,1)], time(), False
            while time()-lastBonus <= 7:
                if alreadyTaken: continue
                try: tempInfos = self.gameInfos["players"][0]["coords"]
                except TypeError: exit(0)
                tempInfos = [(x, y) for x in range(tempInfos[0], tempInfos[0] + 15) for y in range(tempInfos[1], tempInfos[1] + 16)]
                if  (
                    ((self.curBonus[0][0],self.curBonus[0][1]) in tempInfos)
                    or ((self.curBonus[0][0],self.curBonus[0][1]+8) in tempInfos)
                    or ((self.curBonus[0][0]+8,self.curBonus[0][1]+8) in tempInfos)
                    or ((self.curBonus[0][0]+8,self.curBonus[0][1]) in tempInfos)
                    ): 
                        bonusToApp = self.curBonus[1] * 2 - 1
                        if -1 * bonusToApp in bonusList: bonusList.remove(-1 * bonusToApp)
                        else: bonusList.append(bonusToApp) ; threading.Thread(target=self.bonusTimer, args=[bonusToApp], daemon=True).start()
                        self.gameInfos["bonus"], alreadyTaken, self.curBonus[0] = sum(bonusList), True, [-10, -10]

    def bonusTimer(self, bonusType):
        global bonusList
        sleep(5)
        if bonusType in bonusList: bonusList.remove(bonusType)
        self.gameInfos["bonus"] = sum(bonusList)

if __name__ == "__main__":
    if os.name == "posix": os.system("clear")
    else: os.system("cls")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: client.connect(("localhost", 20101))
    except OSError:
        print("Could not connect to the server: try updating; try later")
        exit()

    App(client)
