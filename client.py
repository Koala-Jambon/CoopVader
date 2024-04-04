import pyxel
import os
import socket

class App:

    def __init__(self) -> None:
        self.mainLobbyButton = 0
        self.userNickname =  ""
        self.ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.PYXEL_KEY_LETTERS = [pyxel.KEY_A, pyxel.KEY_B, pyxel.KEY_C, pyxel.KEY_D, pyxel.KEY_E, pyxel.KEY_F, pyxel.KEY_G,
                             pyxel.KEY_H, pyxel.KEY_I, pyxel.KEY_J, pyxel.KEY_K, pyxel.KEY_L, pyxel.KEY_M,
                             pyxel.KEY_N, pyxel.KEY_O, pyxel.KEY_P, pyxel.KEY_Q, pyxel.KEY_R, pyxel.KEY_S, pyxel.KEY_T,
                             pyxel.KEY_U, pyxel.KEY_V, pyxel.KEY_W, pyxel.KEY_X, pyxel.KEY_Y, pyxel.KEY_Z]
        self.currentStage = "getNickname"
        pyxel.init(228, 128, title="Stars Invader")
        pyxel.image(1).load(0, 0, './ressources/title.png')
        pyxel.run(self.update, self.draw)

    def update(self):
        status = getattr(self, f'update_{self.currentStage}')()
        if status != 0:
            print("An error occured")
            exit(status)

    def draw(self):
        pyxel.cls(0)
        status = getattr(self, f'draw_{self.currentStage}')()
        if status != 0:
            print("An error occured")
            exit(status)

    def update_getNickname(self):
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.userNickname = self.userNickname[:-1]
            return 0
        
        if len(self.userNickname) >= 12:    return 0

        if pyxel.btnp(pyxel.KEY_RETURN):
            #Here connect to server
            self.currentStage = "mainLobby"
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
            if self.mainLobbyButton == 0: pyxel.quit()
            elif self.mainLobbyButton == 1: self.currentStage = "joinLobby"
            elif self.mainLobbyButton == 2: self.currentStage = "createLobby"

        for NAVIGATION_KEY in [pyxel.KEY_UP, pyxel.KEY_DOWN]:
            if pyxel.btnp(NAVIGATION_KEY):
                self.mainLobbyButton += [pyxel.KEY_UP, pyxel.KEY_DOWN].index(NAVIGATION_KEY) * 2 - 1
                break
        
        if self.mainLobbyButton == 3: self.mainLobbyButton = 0
        if self.mainLobbyButton == -1: self.mainLobbyButton = 2
        return 0

    def draw_mainLobby(self):
        pyxel.text(0, 0, f'{self.mainLobbyButton}', 7)
        return 0
    
if __name__ == "__main__":
    if os.name == "posix":
        os.system("clear")
    else:
        os.system("cls")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("localhost", 20101))
    except OSError:
        print("Cannot connect to the server ; Try updating ; Try later")
        exit()

    App(client)
