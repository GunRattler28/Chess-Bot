import tkinter as tk
import pygame
import numpy

root = tk.Tk()
root.title("Gun's Chess Bot")

windowSize = 800
positionSize = windowSize / 8
root.geometry(f"{windowSize}x{windowSize}+100+100")
root.resizable(False, False)
canvas = tk.Canvas(root, width=windowSize, height=windowSize, bg="white")
pygame.mixer.init()
activeOutline = None
activeSquare = None
moves = 0
turnColour = "w"
totalPieces = None
moveIndicator = []
possibleMoves = []
moveHistory = []
redoHistory = []

pieces = {
    "bQ": tk.PhotoImage(file="images/pieces/bqueen.png"),
    "bK": tk.PhotoImage(file="images/pieces/bking.png"),
    "bB": tk.PhotoImage(file="images/pieces/bbishop.png"),
    "bH": tk.PhotoImage(file="images/pieces/bhorse.png"),
    "bR": tk.PhotoImage(file="images/pieces/brook.png"),
    "bP": tk.PhotoImage(file="images/pieces/bpawn.png"),
    "wQ": tk.PhotoImage(file="images/pieces/wqueen.png"), 
    "wK": tk.PhotoImage(file="images/pieces/wking.png"),
    "wB": tk.PhotoImage(file="images/pieces/wbishop.png"),
    "wH": tk.PhotoImage(file="images/pieces/whorse.png"),
    "wR": tk.PhotoImage(file="images/pieces/wrook.png"),
    "wP": tk.PhotoImage(file="images/pieces/wpawn.png")
}

piecePositions = {
    "bQ": numpy.uint64(0x0000000000000008),
    "bK": numpy.uint64(0x0000000000000010), 
    "bB": numpy.uint64(0x0000000000000024),
    "bH": numpy.uint64(0x0000000000000042), 
    "bR": numpy.uint64(0x0000000000000081), 
    "bP": numpy.uint64(0x000000000000FF00),
    "wQ": numpy.uint64(0x0800000000000000), 
    "wK": numpy.uint64(0x1000000000000000), 
    "wB": numpy.uint64(0x2400000000000000), 
    "wH": numpy.uint64(0x4200000000000000), 
    "wR": numpy.uint64(0x8100000000000000), 
    "wP": numpy.uint64(0x00FF000000000000)
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
    "red": tk.PhotoImage(file="images/redOverlay.png"),
    "green": tk.PhotoImage(file="images/greenOverlay.png")
}

sounds = {
    "move": pygame.mixer.Sound("sounds/Move.mp3"),
    "capture": pygame.mixer.Sound("sounds/Capture.mp3"),
    "check": pygame.mixer.Sound("sounds/Check.mp3"),
    "checkmate": pygame.mixer.Sound("sounds/Checkmate.mp3"),
}

def drawBoard():
    for column in range(0, 8):
        for row in range(0, 8):
            if ((row + column) % 2 == 0):
                canvas.create_rectangle(column * positionSize, row * positionSize, (column + 1) * positionSize, (row + 1) * positionSize, fill="#ffffff")
            else:
                canvas.create_rectangle(column * positionSize, row * positionSize, (column + 1) * positionSize, (row + 1) * positionSize, fill="#0088ff")

            piece = getPiece(row, column)
            if (piece != ""):
                canvas.create_image(column * positionSize + positionSize / 2, row * positionSize + positionSize / 2, image= pieces[piece])

def calculateTotalPieces():
    global totalPieces
    totalPieces = numpy.uint64(0)
    for each in piecePositions.values():
        totalPieces |= each

def getPiece(row, column):
    position = numpy.uint64(1) << numpy.uint64(row * 8 + column)
    if not (totalPieces & position):                                   # efficient. Brother would be proud
        return ""
    
    for pieceBoard, bitBoard in piecePositions.items():
        if (bitBoard & position):
            return pieceBoard
        
    return ""

def onClick(event):
    global activeOutline
    global activeSquare
    global moves
    global turnColour
    global moveIndicator
    global possibleMoves

    x = event.x
    y = event.y

    row = int(y // positionSize)
    column = int(x // positionSize)

    if activeOutline != None:
        canvas.delete(activeOutline)
        activeOutline = None

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

    piece = getPiece(row, column)

    if piece == "" or piece[0] != turnColour:
        activeSquare = None
        activeOutline = None
        clearPossibleMoves()
        return

    activeSquare = [row, column]
    activeOutline = canvas.create_rectangle(column * positionSize, row * positionSize, (column + 1) * positionSize, (row + 1) * positionSize, outline="#00ff00", width=4,)
    possibleMoves = blockCheck(row, column)
    showLegalMoves(possibleMoves)

def makeMove(startRow, startColumn, endRow, endColumn):
    global turnColour
    global activeSquare
    global moves
    global redoHistory

    movingPiece = getPiece(startRow, startColumn)
    target = getPiece(endRow, endColumn)
    targetPos = numpy.uint64(1) << numpy.uint64(endRow * 8 + endColumn)

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
            
    clearPossibleMoves()

    saveMove(movingPiece, startRow, startColumn, endRow, endColumn, target, turnColour, moves)
    redoHistory.clear()

    if target != "":
        piecePositions[target] &= ~targetPos
        sounds["capture"].play()
    else:
        sounds["move"].play()

    piecePositions[movingPiece] &= ~(numpy.uint64(1) << numpy.uint64(startRow * 8 + startColumn))
    piecePositions[movingPiece] |= targetPos
    moveHistory[-1]["castleRightsAfter"] = castleRights.copy()
    turnColour = "b" if turnColour == "w" else "w"
    activeSquare = None
    moves += 1
    redrawBoard()

def redrawBoard():
    global activeOutline
    activeOutline = None
    calculateTotalPieces()
    canvas.delete("all")
    moveIndicator.clear()
    possibleMoves.clear()
    drawBoard()

def gameState():
    global turnColour
    if not kingCheck(turnColour):
        return

    king = findKing(turnColour)
    canvas.create_image(king[1] * positionSize + positionSize / 2, king[0] * positionSize + positionSize / 2, image=overlays["red"])
    if not legalMoves(turnColour):
        canvas.create_text(windowSize / 2, windowSize / 2, text=f"Checkmate!\n{("Black" if turnColour == "w" else "White")} wins!", fill="#FF0000", font=("dynapuff", 64, "bold"), justify="center", tags="gameover")
        sounds["checkmate"].play()
    else:
        sounds["check"].play()

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
    piece = getPiece(row, column)
    if piece == "":
        print('Something has gone wrong... calculateLegalMoves() got "" from getPiece()')
        return []

    pieceType = piece[-1]
    pieceColour = piece[0]

    knightMoves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    kingMoves = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
    rookDirections = [(1,0), (-1,0), (0,1), (0,-1)]
    bishopDirections = [(1,1), (1,-1), (-1,1), (-1,-1)]
    queenDirections = rookDirections + bishopDirections

    if pieceType == "H":
        instaMoves(knightMoves, row, column, pieceColour, possibleMoves)

    elif pieceType == "K":
        instaMoves(kingMoves, row, column, pieceColour, possibleMoves)

        if includeCastling:
            addCastleMoves(pieceColour, possibleMoves)

    elif pieceType == "R":
        slidingMoves(row, column, rookDirections, pieceColour, possibleMoves)

    elif pieceType == "B":
        slidingMoves(row, column, bishopDirections, pieceColour, possibleMoves)

    elif pieceType == "Q":
        slidingMoves(row, column, queenDirections, pieceColour, possibleMoves)

    elif pieceType == "P":
        if pieceColour == "w":
            direction = -1
        else:
            direction = 1

        potRow = row + direction

        if 0 <= potRow < 8:
            if getPiece(potRow, column) == "":
                possibleMoves.append((potRow, column))

                if pieceColour == "w" and row == 6:
                    if getPiece(potRow - 1, column) == "":
                        possibleMoves.append((potRow - 1, column))

                if pieceColour == "b" and row == 1:
                    if getPiece(potRow + 1, column) == "":
                        possibleMoves.append((potRow + 1, column))

        for columnChange in [-1, 1]:
            
            potRow = row + direction
            potColumn = column + columnChange

            if potRow >= 0 and potRow < 8 and potColumn >= 0 and potColumn < 8:
                target = getPiece(potRow, potColumn)
                if target != "" and target[0] != pieceColour:
                    possibleMoves.append((potRow, potColumn))

    return possibleMoves

def showLegalMoves(possibleMoves):
    global moveIndicator
    
    for indicator in moveIndicator:
        canvas.delete(indicator)

    moveIndicator.clear()

    for moveRow, moveColumn in possibleMoves:
        x = moveColumn * positionSize + positionSize / 2
        y = moveRow * positionSize + positionSize / 2

        if getPiece(moveRow, moveColumn) != "":
            cirColour = overlays["red"]
        else:
            cirColour = overlays["green"]

        moveIndicator.append(canvas.create_image(x, y, image=cirColour))

def slidingMoves(row, column, movements, colour, possibleMoves):
    for rowChange, columnChange in movements:
        potRow = row + rowChange
        potColumn = column + columnChange
        while potRow >= 0 and potRow < 8 and potColumn >= 0 and potColumn < 8:
            target = getPiece(potRow, potColumn)
            if target == "":
                possibleMoves.append((potRow, potColumn))
            else:
                if target[0] != colour:
                    possibleMoves.append((potRow, potColumn))
                break

            potRow += rowChange
            potColumn += columnChange

def instaMoves(moveset, row, column, pieceColour, possibleMoves):
    for rowChange, columnChange in moveset:
        potRow = row + rowChange
        potColumn = column + columnChange

        if potRow >= 0 and potRow < 8 and potColumn >= 0 and potColumn < 8:
            target = getPiece(potRow, potColumn)
            if target == "" or target[0] != pieceColour:
                possibleMoves.append((potRow, potColumn))

def clearPossibleMoves():
    global moveIndicator
    global possibleMoves

    for indicator in moveIndicator:
        canvas.delete(indicator)

    moveIndicator.clear()
    possibleMoves.clear()

def isSquareAttacked(row, column, atkColour):
    for piece, bitboard in piecePositions.items():
        if piece[0] == atkColour:
            board = int(bitboard)
            while board > 0:
                lsb = board & -board
                index = lsb.bit_length() - 1
                pieceRow = index // 8
                pieceColumn = index % 8
                moves = calculateLegalMoves(pieceRow, pieceColumn, False)
                if (row, column) in moves:
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
    piece = getPiece(row, column)
    if piece == "":
        return []

    colour = piece[0]
    anyMoves = calculateLegalMoves(row, column, True)
    validMoves = []

    currentBoard = piecePositions.copy()

    for endRow, endColumn in anyMoves:
        startPosition = numpy.uint64(1) << numpy.uint64(row * 8 + column)
        targetPiece = getPiece(endRow, endColumn)
        targetPosition = numpy.uint64(1) << numpy.uint64(endRow * 8 + endColumn)
        moveCastleRook(piece, (row, column), (endRow, endColumn))
        if targetPiece != "":
            piecePositions[targetPiece] &= ~targetPosition
        piecePositions[piece] &= ~startPosition
        piecePositions[piece] |= targetPosition
        calculateTotalPieces()

        if not kingCheck(colour):
            validMoves.append((endRow, endColumn))

        piecePositions.update(currentBoard)
        calculateTotalPieces()

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
        "castleRightsBefore": castleRights.copy()
    }
    moveHistory.append(state)

def previousMove(event): # Need event as variable so that it can be bound to root. Event isn't used
    global moveHistory
    global redoHistory
    global piecePositions
    global turnColour
    global moves

    if len(moveHistory) == 0:
        return

    previousPos = moveHistory.pop()
    piece = previousPos["piece"]
    start = previousPos["start"]
    end = previousPos["end"]
    capturedPiece = previousPos["capturedPiece"]
    turnColour = previousPos["turnColour"]
    moves = previousPos["moves"]
    startPos = numpy.uint64(1) << numpy.uint64(start[0] * 8 + start[1])
    endPos = numpy.uint64(1) << numpy.uint64(end[0] * 8 + end[1])
    castleRights.clear()
    castleRights.update(previousPos["castleRightsBefore"])

    piecePositions[piece] &= ~endPos
    piecePositions[piece] |= startPos

    if capturedPiece != "":
        piecePositions[capturedPiece] |= endPos

    moveCastleRook(piece, start, end, undo=True)
    
    sounds["move"].play()
    redoHistory.append(previousPos)
    redrawBoard()

def redoMove(event): # Again event isn't used
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

    startPos = numpy.uint64(1) << numpy.uint64(start[0] * 8 + start[1])
    endPos = numpy.uint64(1) << numpy.uint64(end[0] * 8 + end[1])

    if capturedPiece != "":
        piecePositions[capturedPiece] &= ~endPos

    moveCastleRook(piece, start, end)

    piecePositions[piece] &= numpy.uint64(~startPos)
    piecePositions[piece] |= endPos
    moveHistory.append(move)
    sounds["move"].play()
    redrawBoard()
    gameState()

def addCastleMoves(pieceColour, possibleMoves):
    row = 7 if pieceColour == "w" else 0
    enemy = "b" if pieceColour == "w" else "w"

    if (castleRights[pieceColour + "Kr"] and getPiece(row, 5) == "" and getPiece(row, 6) == "" and not kingCheck(pieceColour) and not isSquareAttacked(row, 5, enemy) and not isSquareAttacked(row, 6, enemy) and getPiece(row,7) == pieceColour + "R"):
        possibleMoves.append((row, 6))

    if (castleRights[pieceColour + "Kl"] and getPiece(row, 1) == "" and getPiece(row, 2) == "" and getPiece(row, 3) == "" and not kingCheck(pieceColour) and not isSquareAttacked(row, 3, enemy) and not isSquareAttacked(row, 2, enemy) and getPiece(row,0) == pieceColour + "R"):
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

    startBit = numpy.uint64(1) << numpy.uint64(rookStart[0] * 8 + rookStart[1])
    endBit = numpy.uint64(1) << numpy.uint64(rookEnd[0] * 8 + rookEnd[1])
    piecePositions[piece[0] + "R"] &= ~startBit
    piecePositions[piece[0] + "R"] |= endBit

redrawBoard()
canvas.bind("<Button-1>", onClick)
root.bind("<Left>", previousMove)
root.bind("<Right>", redoMove)
canvas.pack()
root.mainloop()