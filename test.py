turnColour = 'white'
pieceNames = {
    'N': 'knight',
    'B': 'bishop',
    'R': 'rook',
    'Q': 'queen',
    'K': 'king',
}

def conversion(input):
    components = list(input)
    castleRow = 7 if turnColour == 'white' else 0
    if input == 'O-O-O':
        return(castleRow, 4, castleRow, 2)
    elif input == 'O-O':
        return(castleRow, 4, castleRow, 6)
    if components[0] in pieceNames:
        components.pop(0)
    for letter in components:
        if letter == 'x':
            components.remove(letter)
        elif letter == '+':
            components.remove(letter)
        elif letter == '#':
            components.remove(letter)

    startRow = None
    startColumn = None
    endRow = None
    endColumn =  None

    for char in components:
        if char.isalpha():
            if endColumn == None:
                endColumn = (ord(char) - 97) # ord() converts character to unicode. 97 is unicode for lowercase 'a'
            else:
                startColumn = endColumn
                endColumn = (ord(char) - 97)
        else:
            if endRow == None:
                endRow = int(char)
            else:
                startRow = endRow
                endRow = int(char)

    return(startRow, startColumn, endRow, endColumn)

print(conversion("Be4"))
print(conversion("R1e1"))
print(conversion("Rad1"))
print(conversion("Qf7#"))