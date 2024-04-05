from os import system, name

if name == "posix":
    system("clear")
else:
    system("cls")

print("Welcome to shell-invader!")

while True:
    commandInput = input("$>")
    if commandInput == "cls":
        if name == "posix":
            system("clear")
        else:
            system("cls")
        print("Welcome to shell-invader!")
        continue
    with open('adminCommand.txt', 'w') as file:
        file.write(commandInput)
