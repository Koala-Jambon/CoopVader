import pyxel

class App:

    def __init__(self) -> None:
        self.userNickname =  ""
        self.ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.PYXEL_KEY_LETTERS = [pyxel.KEY_A, pyxel.KEY_B, pyxel.KEY_C, pyxel.KEY_D, pyxel.KEY_E, pyxel.KEY_F, pyxel.KEY_G,
                             pyxel.KEY_H, pyxel.KEY_I, pyxel.KEY_J, pyxel.KEY_K, pyxel.KEY_L, pyxel.KEY_M,
                             pyxel.KEY_N, pyxel.KEY_O, pyxel.KEY_P, pyxel.KEY_Q, pyxel.KEY_R, pyxel.KEY_S, pyxel.KEY_T,
                             pyxel.KEY_U, pyxel.KEY_V, pyxel.KEY_W, pyxel.KEY_X, pyxel.KEY_Y, pyxel.KEY_Z]
        self.currentStage = "getNickname"
        pyxel.init(128, 128, title="Invasion de l'espace")
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
        if len(self.userNickname) >= 12:    return 0

        if pyxel.btnp(pyxel.KEY_RETURN):
            #Here connect to server
            self.currentStage = "mainLobby"
            return 0
        
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.userNickname = self.userNickname[:-1]
            return 0
        for i in range(26):
            if pyxel.btnp(self.PYXEL_KEY_LETTERS[i]):
                self.userNickname += self.ALPHABET[i]
                return 0
        return 0

    def draw_getNickname(self):
        pyxel.text(0, 0, self.userNickname, 7)
        return 0

App()
