stringa = "{ test | uno | due }"
lunghezza = 2

print(len(stringa.split("|")))
print("{"+"|".join(stringa[1:-1].split("|")[0:lunghezza])+"}")