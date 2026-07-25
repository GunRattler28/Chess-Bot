import pygame
import pygame.freetype
import math

pygame.init()
pygame.mixer.init()
pygame.key.set_repeat(300, 25)

windowSize = 800
positionSize = windowSize / 8
screen = pygame.display.set_mode((windowSize, windowSize))
pygame.display.set_caption("Gun's Chess Bot")
clock = pygame.time.Clock()
pygame.font.init()
gameFont = pygame.freetype.SysFont("dynapuffregular", 64, bold=True) 

gameOverMessage = None
promotionActive = False
activeOutline = None
activeSquare = None
moves = 0
turnColour = "w"
moveIndicator = []
possibleMoves = []
moveHistory = []
redoHistory = []
positionHistory = {}
squarePiece = [""] * 64
lines = []
rightClickStart = None
temporaryLine = None
strategyCircles = []

pieces = {
    "bQ": pygame.transform.scale(pygame.image.load("images/pieces/bqueen.png").convert_alpha(), (positionSize, positionSize)),
    "bK": pygame.transform.scale(pygame.image.load("images/pieces/bking.png").convert_alpha(), (positionSize, positionSize)),
    "bB": pygame.transform.scale(pygame.image.load("images/pieces/bbishop.png").convert_alpha(), (positionSize, positionSize)),
    "bH": pygame.transform.scale(pygame.image.load("images/pieces/bhorse.png").convert_alpha(), (positionSize, positionSize)),
    "bR": pygame.transform.scale(pygame.image.load("images/pieces/brook.png").convert_alpha(), (positionSize, positionSize)),
    "bP": pygame.transform.scale(pygame.image.load("images/pieces/bpawn.png").convert_alpha(), (positionSize, positionSize)),
    "wQ": pygame.transform.scale(pygame.image.load("images/pieces/wqueen.png").convert_alpha(), (positionSize, positionSize)), 
    "wK": pygame.transform.scale(pygame.image.load("images/pieces/wking.png").convert_alpha(), (positionSize, positionSize)),
    "wB": pygame.transform.scale(pygame.image.load("images/pieces/wbishop.png").convert_alpha(), (positionSize, positionSize)),
    "wH": pygame.transform.scale(pygame.image.load("images/pieces/whorse.png").convert_alpha(), (positionSize, positionSize)),
    "wR": pygame.transform.scale(pygame.image.load("images/pieces/wrook.png").convert_alpha(), (positionSize, positionSize)),
    "wP": pygame.transform.scale(pygame.image.load("images/pieces/wpawn.png").convert_alpha(), (positionSize, positionSize))
}

piecePositions = {
    "bQ": 0x0000000000000008,
    "bK": 0x0000000000000010, 
    "bB": 0x0000000000000024,
    "bH": 0x0000000000000042, 
    "bR": 0x0000000000000081, 
    "bP": 0x000000000000FF00,
    "wQ": 0x0800000000000000, 
    "wK": 0x1000000000000000, 
    "wB": 0x2400000000000000, 
    "wH": 0x4200000000000000, 
    "wR": 0x8100000000000000, 
    "wP": 0x00FF000000000000
}

castleRights = {
    "wKl": True,
    "wK": True,
    "wKr": True,
    "bKl": True,
    "bK": True,
    "bKr": True,
}

overlays = {
    "red": pygame.transform.scale(pygame.image.load("images/redOverlay.png").convert_alpha(), (positionSize, positionSize)),
    "green": pygame.transform.scale(pygame.image.load("images/greenOverlay.png").convert_alpha(), (positionSize, positionSize))
}

sounds = {
    "move": pygame.mixer.Sound("sounds/Move.mp3"),
    "capture": pygame.mixer.Sound("sounds/Capture.mp3"),
    "check": pygame.mixer.Sound("sounds/Check.mp3"),
    "checkmate": pygame.mixer.Sound("sounds/Checkmate.mp3"),
}

knightMoves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
kingMoves = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
rookDirections = [(1,0), (-1,0), (0,1), (0,-1)]
bishopDirections = [(1,1), (1,-1), (-1,1), (-1,-1)]
queenDirections = rookDirections + bishopDirections

def createAttackTables(offset):
    table = [0] * 64
    for square in range(64):
        row = square // 8
        column = square % 8
        mask = 0
        for rowChange, columnChange in offset:
            newRow = row + rowChange
            newColumn = column + columnChange
            if 0 <= newRow < 8 and 0 <= newColumn < 8:
                mask |= 1 << (newRow * 8 + newColumn)
        table[square] = mask
    return table

knightAtk = createAttackTables(knightMoves)
kingAtk = createAttackTables(kingMoves)

def getOccupied():
    whiteOccupied = 0
    blackOccupied = 0
    for name, bitboard in piecePositions.items():
        if name[0] == "w":
            whiteOccupied |= bitboard
        else:
            blackOccupied |= bitboard
    occupied = whiteOccupied | blackOccupied
    return (whiteOccupied, blackOccupied, occupied)

def drawBoard():
    for column in range(0, 8):
        for row in range(0, 8):
            if ((row + column) % 2 == 0):
                pygame.draw.rect(screen, "#ffffff", (column * positionSize, row * positionSize, positionSize, positionSize))
            else:
                pygame.draw.rect(screen, "#0088ff", (column * positionSize, row * positionSize, positionSize, positionSize))

            piece = squarePiece[row * 8 + column]
            if (piece != ""):
                screen.blit(pieces[piece], (column * positionSize, row * positionSize))

def onClick(x, y):
    global activeOutline
    global activeSquare
    global moves
    global turnColour
    global moveIndicator
    global possibleMoves
    global promotionActive
    global lines
    global strategyCircles

    if promotionActive:
        return

    if len(lines) > 0 or len(strategyCircles):
        clearArrows()

    row = int(y // positionSize)
    column = int(x // positionSize)

    if activeSquare == None:
        handleSelection(row, column)
        return

    startRow = activeSquare[0]
    startColumn = activeSquare[1]

    if (row, column) in possibleMoves:
        makeMove(startRow, startColumn, row, column)
        gameState()
        print(moves)

    else:
        handleSelection(row, column)

def handleSelection(row, column):
    global activeSquare
    global activeOutline
    global possibleMoves

    piece = squarePiece[row * 8 + column]

    if piece == "" or piece[0] != turnColour:
        activeSquare = None
        activeOutline = None
        possibleMoves.clear()
        return

    activeSquare = [row, column]
    possibleMoves = blockCheck(row, column)

def makeMove(startRow, startColumn, endRow, endColumn):
    global turnColour
    global activeSquare
    global moves
    global redoHistory
    global gameOverMessage

    movingPiece = squarePiece[startRow * 8 + startColumn]
    target = squarePiece[endRow * 8 + endColumn]
    targetPos = 1 << (endRow * 8 + endColumn)

    moveCastleRook(movingPiece, (startRow, startColumn), (endRow, endColumn))
    start = startRow, startColumn
    end = endRow, endColumn
    if movingPiece == "wK":
        castleRights["wK"] = False
        castleRights["wKl"] = False
        castleRights["wKr"] = False

    elif movingPiece == "bK":
        castleRights["bK"] = False
        castleRights["bKl"] = False
        castleRights["bKr"] = False

    elif movingPiece == "wR":
        if start == (7, 0):
            castleRights["wKl"] = False
        elif start == (7, 7):
            castleRights["wKr"] = False

    elif movingPiece == "bR":
        if start == (0, 0):
            castleRights["bKl"] = False
        elif start == (0, 7):
            castleRights["bKr"] = False

    if target == "wR":
        if end == (7, 0):
            castleRights["wKl"] = False
        elif end == (7, 7):
            castleRights["wKr"] = False

    elif target == "bR":
        if end == (0, 0):
            castleRights["bKl"] = False
        elif end == (0, 7):
            castleRights["bKr"] = False

    possibleMoves.clear()

    saveMove(movingPiece, startRow, startColumn, endRow, endColumn, target, turnColour, moves)
    redoHistory.clear()

    if target != "":
        piecePositions[target] &= ~targetPos
        squarePiece[endRow * 8 + endColumn] = ""
        sounds["capture"].play()
    else:
        sounds["move"].play()

    piecePositions[movingPiece] &= ~(1 << (startRow * 8 + startColumn))
    piecePositions[movingPiece] |= targetPos
    squarePiece[startRow * 8 + startColumn] = ""
    squarePiece[endRow * 8 + endColumn] = movingPiece

    if isPromotable(movingPiece, endRow):
        promotedPiece = choosePromotion(turnColour)
        piecePositions[movingPiece] &= ~targetPos
        piecePositions[promotedPiece] |= targetPos
        squarePiece[endRow * 8 + endColumn] = promotedPiece
        moveHistory[-1]["promotion"] = promotedPiece
    
    moveHistory[-1]["castleRightsAfter"] = castleRights.copy()
    turnColour = "b" if turnColour == "w" else "w"    
    activeSquare = None
    moves += 1
    
    newHash = hashBoard()
    if newHash in positionHistory:
        positionHistory[newHash] += 1
    else:
        positionHistory[newHash] = 1
    if positionHistory[newHash] >= 3:
        gameOverMessage = f"Three-fold \nRepetition!\nNobody  wins!"
    global activeOutline
    activeOutline = None
    moveIndicator.clear()
    possibleMoves.clear()
    drawBoard()

def gameState():
    global turnColour
    global gameOverMessage
    inCheck = kingCheck(turnColour)

    if not legalMoves(turnColour):
        if inCheck:
            winner = "Black" if turnColour == "w" else "White"
            gameOverMessage = f"Checkmate!\n{winner}  wins!"
            sounds["checkmate"].play()
        else:
            gameOverMessage = f"Stalemate!\nNobody  wins!"
            sounds["checkmate"].play()
    elif inCheck:
        sounds["check"].play()
    else:
        gameOverMessage = None

def legalMoves(colour):
    for piece, bitboard in piecePositions.items():
        if piece[0] == colour:    
            board = int(bitboard)
            while board:
                lsb = board & -board
                index = lsb.bit_length() - 1

                row = index // 8
                column = index % 8

                if blockCheck(row, column):
                    return True

                board &= board - 1

    return False

def calculateLegalMoves(row, column, includeCastling):
    possibleMoves = []
    piece = squarePiece[row * 8 + column]
    if piece == "":
        return []

    pieceType = piece[-1]
    pieceColour = piece[0]
    whiteOccupied, blackOccupied, occupied = getOccupied()
    friendlyOccupied = whiteOccupied if pieceColour == "w" else blackOccupied

    if pieceType == "H":
        instaMoves(knightAtk[row * 8 + column], friendlyOccupied, possibleMoves)

    elif pieceType == "K":
        instaMoves(kingAtk[row * 8 + column], friendlyOccupied, possibleMoves)

        if includeCastling:
            addCastleMoves(pieceColour, possibleMoves)

    elif pieceType == "R":
        slidingMoves(row, column, rookDirections, friendlyOccupied, occupied, possibleMoves)

    elif pieceType == "B":
        slidingMoves(row, column, bishopDirections, friendlyOccupied, occupied, possibleMoves)

    elif pieceType == "Q":
        slidingMoves(row, column, queenDirections, friendlyOccupied, occupied, possibleMoves)

    elif pieceType == "P":
        if pieceColour == "w":
            direction = -1
        else:
            direction = 1

        potRow = row + direction

        if 0 <= potRow < 8:
            if squarePiece[potRow * 8+ column] == "":
                possibleMoves.append((potRow, column))

                if pieceColour == "w" and row == 6:
                    if squarePiece[(potRow - 1) * 8 + column] == "":
                        possibleMoves.append((potRow - 1, column))

                if pieceColour == "b" and row == 1:
                    if squarePiece[(potRow + 1) * 8 + column] == "":
                        possibleMoves.append((potRow + 1, column))

        for columnChange in [-1, 1]:
            
            potRow = row + direction
            potColumn = column + columnChange

            if potRow >= 0 and potRow < 8 and potColumn >= 0 and potColumn < 8:
                target = squarePiece[potRow * 8 + potColumn]
                if target != "" and target[0] != pieceColour:
                    possibleMoves.append((potRow, potColumn))

    return possibleMoves

def slidingMoves(row, column, movements, friendlyOccupied, occupied, possibleMoves):
    for rowChange, columnChange in movements:
        potRow = row + rowChange
        potColumn = column + columnChange
        while potRow >= 0 and potRow < 8 and potColumn >= 0 and potColumn < 8:
            targetIndex = potRow * 8 + potColumn
            targetBit = 1 << targetIndex

            if targetBit & friendlyOccupied:
                break

            possibleMoves.append((potRow, potColumn))

            if targetBit & occupied:
                break

            potRow += rowChange
            potColumn += columnChange

def instaMoves(atkMask, friendOccupied, possibleMoves):
    legalMask = atkMask & ~friendOccupied
    while legalMask:
        lsb = legalMask & -legalMask
        index = lsb.bit_length() - 1
        possibleMoves.append((index // 8, index % 8))
        legalMask &= legalMask - 1

def isSquareAttacked(row, column, atkColour):
    whiteOccupied, blackOccupied, occupied = getOccupied()
    friendlyOccupied = whiteOccupied if atkColour == "w" else blackOccupied
    for piece, bitboard in piecePositions.items():
        if piece[0] == atkColour:
            board = int(bitboard)
            pieceType = piece[1]
            while board > 0:
                lsb = board & -board
                index = lsb.bit_length() - 1
                pieceRow = index // 8
                pieceColumn = index % 8
                pieceMoves = []
                if pieceType == "H":
                    instaMoves(knightAtk[index], friendlyOccupied, pieceMoves)
                elif pieceType == "K":
                    instaMoves(kingAtk[index], friendlyOccupied, pieceMoves)
                elif pieceType == "R":
                    slidingMoves(pieceRow, pieceColumn, rookDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "B":
                    slidingMoves(pieceRow, pieceColumn, bishopDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "Q":
                    slidingMoves(pieceRow, pieceColumn, queenDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "P":
                    pDir = -1 if atkColour == "w" else 1
                    for dc in [-1, 1]:
                        r, c = pieceRow + pDir, pieceColumn + dc
                        if 0 <= r < 8 and 0 <= c < 8:
                            pieceMoves.append((r, c))

                if (row, column) in pieceMoves:
                    return True
                
                board = board & ~(1 << index)
    return False

def findKing(colour):
    kingBoard = int(piecePositions[colour + "K"])
    if kingBoard == 0:
        return None
    index = kingBoard.bit_length() - 1
    row = index // 8
    column = index % 8
    return(row, column) 

def kingCheck(colour):
    atkColour = "w" if colour == "b" else "b"
    king = findKing(colour)
    if king == None:
        return False
    return isSquareAttacked(king[0], king[1], atkColour)

def blockCheck(row, column):
    global squarePiece
    piece = squarePiece[row * 8 + column]
    if piece == "":
        return []

    colour = piece[0]
    anyMoves = calculateLegalMoves(row, column, True)
    validMoves = []

    currentBoard = piecePositions.copy()
    currentCastleRights = castleRights.copy()
    for endRow, endColumn in anyMoves:
        currentSquarePiece = squarePiece.copy()
        startPosition = 1 << (row * 8 + column)
        targetPiece = squarePiece[endRow * 8 + endColumn]
        targetPosition = 1 << (endRow * 8 + endColumn)
        moveCastleRook(piece, (row, column), (endRow, endColumn))
        if targetPiece != "":
            piecePositions[targetPiece] &= ~targetPosition
        piecePositions[piece] &= ~startPosition
        piecePositions[piece] |= targetPosition
        squarePiece[row * 8 + column] = ""
        squarePiece[endRow * 8 + endColumn] = piece

        if not kingCheck(colour):
            validMoves.append((endRow, endColumn))

        piecePositions.update(currentBoard)
        castleRights.update(currentCastleRights)
        squarePiece = currentSquarePiece.copy()

    return validMoves

def saveMove(piece, startRow, startColumn, endRow, endColumn, capturedPiece, turnColour, moves):
    global moveHistory
    state = {
        "piece": piece,
        "start": (startRow, startColumn),
        "end": (endRow, endColumn),
        "capturedPiece": capturedPiece,
        "turnColour": turnColour,
        "moves": moves,
        "castleRightsBefore": castleRights.copy(),
        "promotion": None
    }
    moveHistory.append(state)

def previousMove():
    global moveHistory
    global redoHistory
    global piecePositions
    global turnColour
    global moves

    if len(moveHistory) == 0:
        return

    previousPos = moveHistory.pop()
    redoHistory.append(previousPos)
    currentHash = hashBoard()
    piece = previousPos["piece"]
    start = previousPos["start"]
    end = previousPos["end"]
    capturedPiece = previousPos["capturedPiece"]
    turnColour = previousPos["turnColour"]
    moves = previousPos["moves"]
    startPos = 1 << (start[0] * 8 + start[1])
    endPos = 1 << (end[0] * 8 + end[1])
    castleRights.clear()
    castleRights.update(previousPos["castleRightsBefore"])

    squarePiece[end[0] * 8 + end[1]] = ""
    squarePiece[start[0] * 8 + start[1]] = piece

    if previousPos["promotion"] != None:
        promoted = previousPos["promotion"]
        piecePositions[promoted] &= ~endPos
        piecePositions[piece] |= startPos
        squarePiece[end[0] * 8 + end[1]] = ""
        squarePiece[start[0] * 8 + start[1]] = piece

    else:
        piecePositions[piece] &= ~endPos
        piecePositions[piece] |= startPos
        
    if capturedPiece != "":
        piecePositions[capturedPiece] |= endPos
        squarePiece[end[0] * 8 + end[1]] = capturedPiece
        sounds["capture"].play()
    else:
        sounds["move"].play()

    moveCastleRook(piece, start, end, undo=True)
    positionHistory[currentHash] -= 1
    if positionHistory[currentHash] == 0:
        del positionHistory[currentHash]
    newHash = hashBoard()
    if newHash in positionHistory:
        positionHistory[newHash] += 1
    else:
        positionHistory[newHash] = 1

def redoMove():
    global redoHistory
    global turnColour
    global moves

    if len(redoHistory) == 0:
        return

    move = redoHistory.pop()
    piece = move["piece"]
    start = move["start"]
    end = move["end"]
    capturedPiece = move["capturedPiece"]
    turnColour = "b" if move["turnColour"] == "w" else "w"
    moves = move["moves"] + 1
    castleRights.clear()
    castleRights.update(move["castleRightsAfter"])

    startPos = 1 << (start[0] * 8 + start[1])
    endPos = 1 << (end[0] * 8 + end[1])

    if capturedPiece != "":
        piecePositions[capturedPiece] &= ~endPos
        squarePiece[end[0] * 8 + end[1]] = ""
        sounds["capture"].play()
    else:
        sounds["move"].play()

    moveCastleRook(piece, start, end)

    if move["promotion"] != None:
        promoted = move["promotion"]

        piecePositions[piece] &= ~startPos
        piecePositions[promoted] |= endPos

        squarePiece[start[0] * 8 + start[1]] = ""
        squarePiece[end[0] * 8 + end[1]] = promoted

    else:    
        piecePositions[piece] &= ~startPos
        piecePositions[piece] |= endPos
        squarePiece[start[0] * 8 + start[1]] = ""
        squarePiece[end[0] * 8 + end[1]] = piece

    moveHistory.append(move)
    newHash = hashBoard()
    if newHash in positionHistory:
        positionHistory[newHash] += 1
    else:
        positionHistory[newHash] = 1
    
    gameState()

def addCastleMoves(pieceColour, possibleMoves):
    row = 7 if pieceColour == "w" else 0
    enemy = "b" if pieceColour == "w" else "w"

    if (castleRights[pieceColour + "Kr"] and squarePiece[row * 8 + 5] == "" and squarePiece[row * 8 + 6] == "" and not kingCheck(pieceColour) and not isSquareAttacked(row, 5, enemy) and not isSquareAttacked(row, 6, enemy) and squarePiece[row * 8 + 7] == pieceColour + "R"):
        possibleMoves.append((row, 6))

    if (castleRights[pieceColour + "Kl"] and squarePiece[row * 8 + 1] == "" and squarePiece[row * 8 + 2] == "" and squarePiece[row * 8 + 3] == "" and not kingCheck(pieceColour) and not isSquareAttacked(row, 3, enemy) and not isSquareAttacked(row, 2, enemy) and squarePiece[row * 8 + 0] == pieceColour + "R"):
        possibleMoves.append((row, 2))

def moveCastleRook(piece, start, end, undo=False):
    if piece not in ("wK", "bK"):
        return

    if piece == "wK":
        row = 7
    else:
        row = 0

    if start == (row, 4) and end == (row, 6):
        if undo:
            rookStart = (row, 5)
            rookEnd = (row, 7)
        else:
            rookStart = (row, 7)
            rookEnd = (row, 5)

    elif start == (row, 4) and end == (row, 2):
        if undo:
            rookStart = (row, 3)
            rookEnd = (row, 0)
        else:
            rookStart = (row, 0)
            rookEnd = (row, 3)

    else:
        return

    startBit = 1 << (rookStart[0] * 8 + rookStart[1])
    endBit = 1 << (rookEnd[0] * 8 + rookEnd[1])
    piecePositions[piece[0] + "R"] &= ~startBit
    piecePositions[piece[0] + "R"] |= endBit
    squarePiece[rookStart[0] * 8 + rookStart[1]] = ""
    squarePiece[rookEnd[0] * 8 + rookEnd[1]] = piece[0] + "R"

def hashBoard(): # hash... brown??
    return hash((tuple(piecePositions.values()), turnColour, tuple(castleRights.values())))

def updateSquareTable():
    global squarePiece
    squarePiece = [""] * 64

    for piece, bitboard in piecePositions.items():
        while bitboard:
            lsb = bitboard & -bitboard
            index = lsb.bit_length() - 1
            squarePiece[index] = piece
            bitboard &= bitboard - 1

def isPromotable(piece, row):
    if piece == "wP" and row == 0:
        return True
    elif piece == "bP" and row == 7:
        return True
    return False

def choosePromotion(colour):
    global promotionActive
    promotionActive = True
    piecesToChoose = ["Q", "H", "R", "B"]
    
    menuWidth = positionSize * 4
    menuX = (windowSize - menuWidth) // 2
    menuY = (windowSize - positionSize) // 2
    
    chosenPiece = None
    
    while promotionActive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouseX, mouseY = event.pos
                if menuY <= mouseY <= menuY + positionSize:
                    if menuX <= mouseX <= menuX + menuWidth:
                        index = int((mouseX - menuX) // positionSize)
                        chosenPiece = colour + piecesToChoose[index]
                        promotionActive = False

        pygame.draw.rect(screen, (255, 255, 255), (menuX, menuY, menuWidth, positionSize))
        pygame.draw.rect(screen, (0, 0, 0), (menuX, menuY, menuWidth, positionSize), 4)
        
        for i, piece in enumerate(piecesToChoose):
            screen.blit(pieces[colour + piece], (menuX + (i * positionSize), menuY))
            
        pygame.display.flip()
        clock.tick(60)
        
    return chosenPiece

def clearArrows():
    global lines, strategyCircles
    strategyCircles.clear()
    lines.clear()

def onRightClick(x, y):
    global rightClickStart
    if promotionActive: 
        return
    rightClickStart = (int(y // positionSize), int(x // positionSize))

def onRightDrag(x, y):
    global temporaryLine
    if rightClickStart:
        temporaryLine = (x, y) # Just store the current mouse coordinates

def onRightRelease(x, y):
    global rightClickStart, temporaryLine
    if not rightClickStart: return

    endRow, endColumn = int(y // positionSize), int(x // positionSize)
    startRow, startColumn = rightClickStart
    
    if 0 <= endRow < 8 and 0 <= endColumn < 8:
        if (startRow, startColumn) == (endRow, endColumn):
            if (startRow, startColumn) in strategyCircles:
                strategyCircles.remove((endRow, endColumn))
            else:
                strategyCircles.append((endRow, endColumn))
        else:
            lines.append(((startRow, startColumn), (endRow, endColumn)))

    rightClickStart = None
    temporaryLine = None

def drawHighlights():
    if activeSquare:
        r, c = activeSquare
        pygame.draw.rect(screen, (0, 255, 0), (c * positionSize, r * positionSize, positionSize, positionSize), 4)

    for moveRow, moveColumn in possibleMoves:
        x, y = moveColumn * positionSize, moveRow * positionSize
        if squarePiece[moveRow * 8 + moveColumn] != "":
            screen.blit(overlays["red"], (x, y))
        else:
            screen.blit(overlays["green"], (x, y))

    if kingCheck(turnColour):
        king = findKing(turnColour)
        if king:
            screen.blit(overlays["red"], (king[1] * positionSize, king[0] * positionSize))

def drawArrow(surface, color, start, end, thickness=25, arrowSize=50):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    dir_x = dx / length
    dir_y = dy / length
    shaft_end = (end[0] - dir_x * (arrowSize * 0.6), end[1] - dir_y * (arrowSize * 0.6))
    radius = thickness // 2
    pygame.draw.circle(surface, color, start, radius)
    pygame.draw.line(surface, color, start, shaft_end, thickness)
    rotation = math.atan2(dy, dx)
    p1 = (end[0] - arrowSize * math.cos(rotation + math.pi / 4), end[1] - arrowSize * math.sin(rotation + math.pi / 4))
    p2 = (end[0] - arrowSize * math.cos(rotation - math.pi / 4), end[1] - arrowSize * math.sin(rotation - math.pi / 4))
    pygame.draw.polygon(surface, color, [end, p1, p2])

def drawArrows():
    for row, column in strategyCircles:
        screen.blit(overlays["green"], (column * positionSize, row * positionSize))

    arrowSurf = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
    arrowColor = (0, 255, 0, 150) 
    
    for (startR, startC), (endR, endC) in lines:
        startX = startC * positionSize + positionSize / 2
        startY = startR * positionSize + positionSize / 2
        endX = endC * positionSize + positionSize / 2
        endY = endR * positionSize + positionSize / 2
        drawArrow(arrowSurf, arrowColor, (startX, startY), (endX, endY))

    if rightClickStart and temporaryLine:
        startR, startC = rightClickStart
        startX = startC * positionSize + positionSize / 2
        startY = startR * positionSize + positionSize / 2
        drawArrow(arrowSurf, (0, 187, 0, 150), (startX, startY), temporaryLine)
        
    screen.blit(arrowSurf, (0, 0))

updateSquareTable()
startHash = hashBoard()
positionHistory[startHash] = 1

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                onClick(event.pos[0], event.pos[1]) 
            elif event.button == 3:
                onRightClick(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEMOTION:
            if rightClickStart:
                onRightDrag(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                onRightRelease(event.pos[0], event.pos[1])
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                previousMove()
            elif event.key == pygame.K_RIGHT:
                redoMove()

    screen.fill((255, 255, 255))
    drawBoard()
    drawHighlights()
    drawArrows()
    if gameOverMessage:
        gamelines = gameOverMessage.split("\n")
        rendered_lines = []
        total_height = 0
        
        for line in gamelines:
            surf, rect = gameFont.render(line, fgcolor=(255, 0, 0), style=pygame.freetype.STYLE_STRONG)
            rendered_lines.append((surf, rect))
            total_height += rect.height + 8

        bgSurface = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
        bgSurface.fill((0, 0, 0, 150))
        screen.blit(bgSurface, (0, 0))

        current_y = (windowSize - total_height) / 2
        for surf, rect in rendered_lines:
            rect.centerx = windowSize / 2
            rect.y = current_y
            screen.blit(surf, rect)
            current_y += rect.height + 8

    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()