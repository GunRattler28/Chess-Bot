import pygame
import pygame.freetype
import math

pygame.init()
pygame.mixer.init()
pygame.key.set_repeat(300, 25)

redraw = True
windowSize = 800
positionSize = windowSize / 8
screen = pygame.display.set_mode((windowSize, windowSize))
pygame.display.set_caption("Gun's Chess Bot")
icon = pygame.image.load('images/icon.png')
pygame.display.set_icon(icon)
clock = pygame.time.Clock()
pygame.font.init()
gameFont = pygame.freetype.SysFont("dynapuffregular", 64, bold=True) 

gameOverMessage = None
promotionActive = False
activeOutline = None
activeSquare = None
moves = 0
halfmoveClock = 0
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

enPassantTarget = None

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

def getPiece(row, column):
    if not (0 <= row < 8 and 0 <= column < 8):
        return ""
    return squarePiece[row * 8 + column]


def getPieceFromBitboards(row, column):
    if not (0 <= row < 8 and 0 <= column < 8):
        return ""

    bit = 1 << (row * 8 + column)
    for piece, bitboard in piecePositions.items():
        if bitboard & bit:
            return piece
    return ""


def setPiece(row, column, piece):
    if not (0 <= row < 8 and 0 <= column < 8):
        return
    squarePiece[row * 8 + column] = piece


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

            piece = getPiece(row, column)
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
    global redraw
    global activeSquare
    global activeOutline
    global possibleMoves

    piece = getPiece(row, column)

    if piece == "" or piece[0] != turnColour:
        activeSquare = None
        activeOutline = None
        possibleMoves.clear()
        redraw = True
        return

    activeSquare = [row, column]
    possibleMoves = blockCheck(row, column)
    redraw = True

def makeMove(startRow, startColumn, endRow, endColumn):
    global redraw
    global turnColour
    global activeSquare
    global moves
    global halfmoveClock
    global redoHistory
    global gameOverMessage

    movingPiece = getPiece(startRow, startColumn)
    target = getPiece(endRow, endColumn)
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

    saveMove(movingPiece, startRow, startColumn, endRow, endColumn, target, turnColour, moves, halfmoveClock)
    redoHistory.clear()
    global enPassantTarget

    enPassantCapture = False
    if movingPiece[-1] == "P":
        direction = -1 if movingPiece[0] == "w" else 1
        if target == "" and startColumn != endColumn and enPassantTarget == (endRow, endColumn):
            capturedRow = endRow - direction
            capturedCol = endColumn
            capturedPiece = getPiece(capturedRow, capturedCol)
            if capturedPiece != "":
                capPos = 1 << (capturedRow * 8 + capturedCol)
                piecePositions[capturedPiece] &= ~capPos
                setPiece(capturedRow, capturedCol, "")
                moveHistory[-1]["capturedPiece"] = capturedPiece
                moveHistory[-1]["capturedSquare"] = (capturedRow, capturedCol)
                enPassantCapture = True
                sounds["capture"].play()

    if not enPassantCapture:
        if target != "":
            piecePositions[target] &= ~targetPos
            setPiece(endRow, endColumn, "")
            sounds["capture"].play()
        else:
            sounds["move"].play()

    piecePositions[movingPiece] &= ~(1 << (startRow * 8 + startColumn))
    piecePositions[movingPiece] |= targetPos
    setPiece(startRow, startColumn, "")
    setPiece(endRow, endColumn, movingPiece)

    if isPromotable(movingPiece, endRow):
        promotedPiece = choosePromotion(turnColour)
        piecePositions[movingPiece] &= ~targetPos
        piecePositions[promotedPiece] |= targetPos
        setPiece(endRow, endColumn, promotedPiece)
        moveHistory[-1]["promotion"] = promotedPiece
    
    moveHistory[-1]["castleRightsAfter"] = castleRights.copy()
    if movingPiece[-1] == "P" and abs(endRow - startRow) == 2:
        enPassantTarget = ((startRow + endRow) // 2, startColumn)
    else:
        enPassantTarget = None
    moveHistory[-1]["enPassantAfter"] = enPassantTarget
    turnColour = "b" if turnColour == "w" else "w"    
    activeSquare = None
    updateSquareTable()
    moves += 1
    if movingPiece[-1] == "P" or target != "" or enPassantCapture:
        halfmoveClock = 0
    else:
        halfmoveClock += 1
    moveHistory[-1]["halfmoveClockAfter"] = halfmoveClock
    
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
    redraw = True

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
    elif halfmoveClock >= 100:
        gameOverMessage = "50-move rule\nDraw!"
        sounds["checkmate"].play()
    elif insufficientMat():
        gameOverMessage = f"Insufficient  Material! \n Nobody  wins"
        sounds["checkmate"].play()
    else:
        gameOverMessage = None

def insufficientMat():
    if (piecePositions["bP"] or piecePositions["bR"] or piecePositions["bQ"] or piecePositions["wP"] or piecePositions["wR"] or piecePositions["wQ"]): 
        return False
    totKnights = piecePositions["bH"] | piecePositions["wH"]
    totBishops = piecePositions["bB"] | piecePositions["wB"]

    if totBishops == 0 and totKnights == 0:
        return True

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
                else:
                    global enPassantTarget
                    if enPassantTarget == (potRow, potColumn):
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
    piece = getPiece(row, column)
    if piece == "":
        return []

    colour = piece[0]
    anyMoves = calculateLegalMoves(row, column, True)
    validMoves = []

    for endRow, endColumn in anyMoves:
        targetPiece = getPiece(endRow, endColumn)
        start = (row, column)
        end = (endRow, endColumn)

        capturedSquare = None
        capturedPiece = targetPiece
        if piece[-1] == "P" and targetPiece == "" and start[1] != end[1]:
            global enPassantTarget
            if enPassantTarget == (endRow, endColumn):
                direction = -1 if piece[0] == "w" else 1
                capturedSquare = (endRow - direction, endColumn)
                capturedPiece = getPiece(capturedSquare[0], capturedSquare[1])

        simulateMove(piece, start, end, capturedPiece, capturedSquare)

        if not kingCheck(colour):
            validMoves.append(end)

        undoMove(piece, start, end, capturedPiece, capturedSquare)

    return validMoves

def simulateMove(piece, start, end, captured, capturedSquare=None):
    startIndex = start[0] * 8 + start[1]
    endIndex = end[0] * 8 + end[1]
    startBit = 1 << startIndex
    endBit = 1 << endIndex

    if captured:
        if capturedSquare:
            capIndex = capturedSquare[0] * 8 + capturedSquare[1]
            piecePositions[captured] &= ~(1 << capIndex)
            setPiece(capturedSquare[0], capturedSquare[1], "")
        else:
            piecePositions[captured] &= ~endBit
            setPiece(end[0], end[1], "")

    piecePositions[piece] &= ~startBit
    piecePositions[piece] |= endBit

    setPiece(start[0], start[1], "")
    setPiece(end[0], end[1], piece)

    if piece in ("wK", "bK"):
        moveCastleRook(piece, start, end)

def undoMove(piece, start, end, captured, capturedSquare=None):
    startIndex = start[0] * 8 + start[1]
    endIndex = end[0] * 8 + end[1]
    startBit = 1 << startIndex
    endBit = 1 << endIndex

    piecePositions[piece] &= ~endBit
    piecePositions[piece] |= startBit

    if captured:
        if capturedSquare:
            capIndex = capturedSquare[0] * 8 + capturedSquare[1]
            piecePositions[captured] |= 1 << capIndex
            setPiece(capturedSquare[0], capturedSquare[1], captured)
        else:
            piecePositions[captured] |= endBit
            setPiece(end[0], end[1], captured)

    setPiece(start[0], start[1], piece)
    if not captured or (captured and capturedSquare):
        setPiece(end[0], end[1], "" if captured and capturedSquare else (captured or ""))

    if piece in ("wK", "bK"):
        moveCastleRook(piece, start, end, undo=True)

def saveMove(piece, startRow, startColumn, endRow, endColumn, capturedPiece, turnColour, moves, halfmoveClockBefore):
    global moveHistory
    state = {
        "piece": piece,
        "start": (startRow, startColumn),
        "end": (endRow, endColumn),
        "capturedPiece": capturedPiece,
        "capturedSquare": None,
        "enPassantBefore": enPassantTarget,
        "turnColour": turnColour,
        "moves": moves,
        "halfmoveClockBefore": halfmoveClockBefore,
        "halfmoveClockAfter": None,
        "castleRightsBefore": castleRights.copy(),
        "promotion": None
    }
    moveHistory.append(state)

def previousMove():
    global redraw
    global moveHistory
    global redoHistory
    global piecePositions
    global turnColour
    global moves
    global halfmoveClock

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
    halfmoveClock = previousPos.get("halfmoveClockBefore", 0)
    startPos = 1 << (start[0] * 8 + start[1])
    endPos = 1 << (end[0] * 8 + end[1])
    castleRights.clear()
    castleRights.update(previousPos["castleRightsBefore"])
    global enPassantTarget
    enPassantTarget = previousPos.get("enPassantBefore", None)

    setPiece(end[0], end[1], "")
    setPiece(start[0], start[1], piece)

    if previousPos["promotion"] != None:
        promoted = previousPos["promotion"]
        piecePositions[promoted] &= ~endPos
        piecePositions[piece] |= startPos
        setPiece(end[0], end[1], "")
        setPiece(start[0], start[1], piece)

    else:
        piecePositions[piece] &= ~endPos
        piecePositions[piece] |= startPos
        
    if capturedPiece != "":
        capSquare = previousPos.get("capturedSquare")
        if capSquare:
            capPos = 1 << (capSquare[0] * 8 + capSquare[1])
            piecePositions[capturedPiece] |= capPos
            setPiece(capSquare[0], capSquare[1], capturedPiece)
        else:
            piecePositions[capturedPiece] |= endPos
            setPiece(end[0], end[1], capturedPiece)
        sounds["capture"].play()
    else:
        sounds["move"].play()

    moveCastleRook(piece, start, end, undo=True)
    positionHistory[currentHash] -= 1
    if positionHistory[currentHash] == 0:
        del positionHistory[currentHash]
    newHash = hashBoard()
    updateSquareTable()
    if newHash in positionHistory:
        positionHistory[newHash] += 1
    else:
        positionHistory[newHash] = 1

    gameState()
    redraw = True

def redoMove():
    global redraw
    global redoHistory
    global turnColour
    global moves
    global halfmoveClock

    if len(redoHistory) == 0:
        return

    move = redoHistory.pop()
    piece = move["piece"]
    start = move["start"]
    end = move["end"]
    capturedPiece = move["capturedPiece"]
    turnColour = "b" if move["turnColour"] == "w" else "w"
    moves = move["moves"] + 1
    halfmoveClock = move.get("halfmoveClockAfter", 0)
    castleRights.clear()
    castleRights.update(move["castleRightsAfter"])
    global enPassantTarget
    enPassantTarget = move.get("enPassantAfter", None)

    startPos = 1 << (start[0] * 8 + start[1])
    endPos = 1 << (end[0] * 8 + end[1])

    if capturedPiece != "":
        capSquare = move.get("capturedSquare")
        if capSquare:
            capPos = 1 << (capSquare[0] * 8 + capSquare[1])
            piecePositions[capturedPiece] &= ~capPos
            setPiece(capSquare[0], capSquare[1], "")
        else:
            piecePositions[capturedPiece] &= ~endPos
            setPiece(end[0], end[1], "")
        sounds["capture"].play()
    else:
        sounds["move"].play()

    moveCastleRook(piece, start, end)

    if move["promotion"] != None:
        promoted = move["promotion"]

        piecePositions[piece] &= ~startPos
        piecePositions[promoted] |= endPos

        setPiece(start[0], start[1], "")
        setPiece(end[0], end[1], promoted)

    else:    
        piecePositions[piece] &= ~startPos
        piecePositions[piece] |= endPos
        setPiece(start[0], start[1], "")
        setPiece(end[0], end[1], piece)

    moveHistory.append(move)
    newHash = hashBoard()
    updateSquareTable()
    if newHash in positionHistory:
        positionHistory[newHash] += 1
    else:
        positionHistory[newHash] = 1
    
    gameState()
    redraw = True

def addCastleMoves(pieceColour, possibleMoves):
    row = 7 if pieceColour == "w" else 0
    enemy = "b" if pieceColour == "w" else "w"

    if (castleRights[pieceColour + "Kr"] and getPiece(row, 5) == "" and getPiece(row, 6) == "" and not kingCheck(pieceColour) and not isSquareAttacked(row, 5, enemy) and not isSquareAttacked(row, 6, enemy) and getPiece(row, 7) == pieceColour + "R"):
        possibleMoves.append((row, 6))

    if (castleRights[pieceColour + "Kl"] and getPiece(row, 1) == "" and getPiece(row, 2) == "" and getPiece(row, 3) == "" and not kingCheck(pieceColour) and not isSquareAttacked(row, 3, enemy) and not isSquareAttacked(row, 2, enemy) and getPiece(row, 0) == pieceColour + "R"):
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
    setPiece(rookStart[0], rookStart[1], "")
    setPiece(rookEnd[0], rookEnd[1], piece[0] + "R")

def hashBoard(): # hash... brown??
    return hash((tuple(piecePositions.values()), turnColour, tuple(castleRights.values()), enPassantTarget))

def updateSquareTable():
    global squarePiece
    squarePiece = [""] * 64

    for piece, bitboard in piecePositions.items():
        board = int(bitboard)
        while board:
            lsb = board & -board
            index = lsb.bit_length() - 1
            squarePiece[index] = piece
            board &= board - 1

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
    global redraw
    global lines
    global strategyCircles
    strategyCircles.clear()
    lines.clear()
    redraw = True

def onRightClick(x, y):
    global rightClickStart
    if promotionActive: 
        return
    rightClickStart = (int(y // positionSize), int(x // positionSize))

def onRightDrag(x, y):
    global redraw
    global temporaryLine
    if rightClickStart:
        temporaryLine = (x, y)
    redraw = True

def onRightRelease(x, y):
    global redraw
    global rightClickStart
    global temporaryLine
    if not rightClickStart: 
        return

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
    redraw = True

def drawHighlights():
    if activeSquare:
        r, c = activeSquare
        pygame.draw.rect(screen, (0, 255, 0), (c * positionSize, r * positionSize, positionSize, positionSize), 4)

    for moveRow, moveColumn in possibleMoves:
        x, y = moveColumn * positionSize, moveRow * positionSize
        if getPiece(moveRow, moveColumn) != "":
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
    radius = thickness / 2
    
    norm_x = -dir_y
    norm_y = dir_x
    
    p_start_1 = (start[0] + norm_x * radius, start[1] + norm_y * radius)
    p_start_2 = (start[0] - norm_x * radius, start[1] - norm_y * radius)
    p_end_1 = (shaft_end[0] + norm_x * radius, shaft_end[1] + norm_y * radius)
    p_end_2 = (shaft_end[0] - norm_x * radius, shaft_end[1] - norm_y * radius)
    
    pygame.draw.circle(surface, color, start, radius)
    pygame.draw.polygon(surface, color, [p_start_1, p_end_1, p_end_2, p_start_2])
    
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

    if redraw:
        screen.fill((255, 255, 255))
        drawBoard()
        drawHighlights()
        drawArrows()
        if gameOverMessage:
            gamelines = gameOverMessage.split("\n")
            renderedLines = []
            totalHeight = 0
            
            for line in gamelines:
                surf, rect = gameFont.render(line, fgcolor=(255, 0, 0), style=pygame.freetype.STYLE_STRONG)
                renderedLines.append((surf, rect))
                totalHeight += rect.height + 8

            bgSurface = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
            bgSurface.fill((0, 0, 0, 150))
            screen.blit(bgSurface, (0, 0))

            current_y = (windowSize - totalHeight) / 2
            for surf, rect in renderedLines:
                rect.centerx = windowSize / 2
                rect.y = current_y
                screen.blit(surf, rect)
                current_y += rect.height + 8

        pygame.display.flip()

    clock.tick(60)    
pygame.quit()