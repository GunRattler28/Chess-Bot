from engine.constants import knightMoves, kingMoves, rookDirections, bishopDirections, queenDirections, knightAtk, kingAtk, sounds

gameOverMessage = None
moves = 0
halfmoveClock = 0
turnColour = "w"
moveHistory = []
redoHistory = []
positionHistory = []
squarePiece = [""] * 64
enPassantTarget = None

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

def getPiece(row, column):
    if not (0 <= row < 8 and 0 <= column < 8): return ""
    return squarePiece[row * 8 + column]

def setPiece(row, column, piece):
    if not (0 <= row < 8 and 0 <= column < 8): return
    squarePiece[row * 8 + column] = piece

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

def getOccupied():
    whiteOccupied, blackOccupied = 0, 0
    for name, bitboard in piecePositions.items():
        if name[0] == "w": whiteOccupied |= bitboard
        else: blackOccupied |= bitboard
    return (whiteOccupied, blackOccupied, whiteOccupied | blackOccupied)

def hashBoard():
    return hash((tuple(piecePositions.values()), turnColour, tuple(castleRights.values()), enPassantTarget))

def createAttackTables(offset):
    table = [0] * 64
    for square in range(64):
        row, column = square // 8, square % 8
        mask = 0
        for rowChange, columnChange in offset:
            newRow, newColumn = row + rowChange, column + columnChange
            if 0 <= newRow < 8 and 0 <= newColumn < 8:
                mask |= 1 << (newRow * 8 + newColumn)
        table[square] = mask
    return table

knightAtk = createAttackTables(knightMoves)
kingAtk = createAttackTables(kingMoves)

def slidingMoves(row, column, movements, friendlyOccupied, occupied, possibleMoves):
    for rowChange, columnChange in movements:
        potRow, potColumn = row + rowChange, column + columnChange
        while 0 <= potRow < 8 and 0 <= potColumn < 8:
            targetBit = 1 << (potRow * 8 + potColumn)
            if targetBit & friendlyOccupied: break
            possibleMoves.append((potRow, potColumn))
            if targetBit & occupied: break
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
            b = int(bitboard)
            pieceType = piece[1]
            while b > 0:
                lsb = b & -b
                index = lsb.bit_length() - 1
                pieceRow, pieceColumn = index // 8, index % 8
                pieceMoves = []
                
                if pieceType == "H": instaMoves(knightAtk[index], friendlyOccupied, pieceMoves)
                elif pieceType == "K": instaMoves(kingAtk[index], friendlyOccupied, pieceMoves)
                elif pieceType == "R": slidingMoves(pieceRow, pieceColumn, rookDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "B": slidingMoves(pieceRow, pieceColumn, bishopDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "Q": slidingMoves(pieceRow, pieceColumn, queenDirections, friendlyOccupied, occupied, pieceMoves)
                elif pieceType == "P":
                    pDir = -1 if atkColour == "w" else 1
                    for dc in [-1, 1]:
                        r, c = pieceRow + pDir, pieceColumn + dc
                        if 0 <= r < 8 and 0 <= c < 8: pieceMoves.append((r, c))

                if (row, column) in pieceMoves: return True
                b &= ~(1 << index)
    return False

def findKing(colour):
    kingBoard = int(piecePositions[colour + "K"])
    if kingBoard == 0: return None
    index = kingBoard.bit_length() - 1
    return (index // 8, index % 8)

def kingCheck(colour):
    king = findKing(colour)
    if king is None: return False
    return isSquareAttacked(king[0], king[1], "w" if colour == "b" else "b")

def addCastleMoves(pieceColour, possibleMoves):
    row = 7 if pieceColour == "w" else 0
    enemy = "b" if pieceColour == "w" else "w"

    if (castleRights[pieceColour + "Kr"] and getPiece(row, 5) == "" and getPiece(row, 6) == "" and 
        not kingCheck(pieceColour) and not isSquareAttacked(row, 5, enemy) and not isSquareAttacked(row, 6, enemy) and 
        getPiece(row, 7) == pieceColour + "R"):
        possibleMoves.append((row, 6))

    if (castleRights[pieceColour + "Kl"] and getPiece(row, 1) == "" and getPiece(row, 2) == "" and getPiece(row, 3) == "" and 
        not kingCheck(pieceColour) and not isSquareAttacked(row, 3, enemy) and not isSquareAttacked(row, 2, enemy) and 
        getPiece(row, 0) == pieceColour + "R"):
        possibleMoves.append((row, 2))

def calculateLegalMoves(row, column, includeCastling):
    possibleMoves = []
    piece = getPiece(row, column)
    if piece == "": return []

    pieceType, pieceColour = piece[-1], piece[0]
    whiteOccupied, blackOccupied, occupied = getOccupied()
    friendlyOccupied = whiteOccupied if pieceColour == "w" else blackOccupied

    if pieceType == "H": instaMoves(knightAtk[row * 8 + column], friendlyOccupied, possibleMoves)
    elif pieceType == "K":
        instaMoves(kingAtk[row * 8 + column], friendlyOccupied, possibleMoves)
        if includeCastling: addCastleMoves(pieceColour, possibleMoves)
    elif pieceType == "R": slidingMoves(row, column, rookDirections, friendlyOccupied, occupied, possibleMoves)
    elif pieceType == "B": slidingMoves(row, column, bishopDirections, friendlyOccupied, occupied, possibleMoves)
    elif pieceType == "Q": slidingMoves(row, column, queenDirections, friendlyOccupied, occupied, possibleMoves)
    elif pieceType == "P":
        direction = -1 if pieceColour == "w" else 1
        potRow = row + direction
        if 0 <= potRow < 8:
            if getPiece(potRow, column) == "":
                possibleMoves.append((potRow, column))
                if pieceColour == "w" and row == 6 and getPiece(potRow - 1, column) == "": possibleMoves.append((potRow - 1, column))
                elif pieceColour == "b" and row == 1 and getPiece(potRow + 1, column) == "": possibleMoves.append((potRow + 1, column))

        for columnChange in [-1, 1]:
            potRow, potColumn = row + direction, column + columnChange
            if 0 <= potRow < 8 and 0 <= potColumn < 8:
                target = getPiece(potRow, potColumn)
                if target != "" and target[0] != pieceColour: possibleMoves.append((potRow, potColumn))
                elif enPassantTarget == (potRow, potColumn): possibleMoves.append((potRow, potColumn))

    return possibleMoves

def blockCheck(row, column):
    piece = getPiece(row, column)
    if piece == "": return []
    validMoves = []
    
    for endRow, endColumn in calculateLegalMoves(row, column, True):
        targetPiece = getPiece(endRow, endColumn)
        capturedSquare = None
        capturedPiece = targetPiece

        if piece[-1] == "P" and targetPiece == "" and column != endColumn:
            if enPassantTarget == (endRow, endColumn):
                capturedSquare = (endRow - (-1 if piece[0] == "w" else 1), endColumn)
                capturedPiece = getPiece(capturedSquare[0], capturedSquare[1])

        simulateMove(piece, (row, column), (endRow, endColumn), capturedPiece, capturedSquare)
        if not kingCheck(piece[0]): validMoves.append((endRow, endColumn))
        undoMove(piece, (row, column), (endRow, endColumn), capturedPiece, capturedSquare)

    return validMoves

def legalMoves(colour):
    for piece, bitboard in piecePositions.items():
        if piece[0] == colour:
            b = int(bitboard)
            while b:
                lsb = b & -b
                index = lsb.bit_length() - 1
                if blockCheck(index // 8, index % 8): return True
                b &= b - 1
    return False

def isPromotable(piece, row):
    return (piece == "wP" and row == 0) or (piece == "bP" and row == 7)

def insufficientMat():
    if (piecePositions["bP"] or piecePositions["bR"] or piecePositions["bQ"] or 
        piecePositions["wP"] or piecePositions["wR"] or piecePositions["wQ"]): return False
    totKnights = piecePositions["bH"] | piecePositions["wH"]
    totBishops = piecePositions["bB"] | piecePositions["wB"]
    return (totBishops == 0 and totKnights == 0)

def moveCastleRook(piece, start, end, undo=False):
    if piece not in ("wK", "bK"): return
    row = 7 if piece == "wK" else 0

    if start == (row, 4) and end == (row, 6): rookStart, rookEnd = ((row, 5), (row, 7)) if undo else ((row, 7), (row, 5))
    elif start == (row, 4) and end == (row, 2): rookStart, rookEnd = ((row, 3), (row, 0)) if undo else ((row, 0), (row, 3))
    else: return

    piecePositions[piece[0] + "R"] &= ~(1 << (rookStart[0] * 8 + rookStart[1]))
    piecePositions[piece[0] + "R"] |= 1 << (rookEnd[0] * 8 + rookEnd[1])
    setPiece(rookStart[0], rookStart[1], "")
    setPiece(rookEnd[0], rookEnd[1], piece[0] + "R")

def simulateMove(piece, start, end, captured, capturedSquare=None):
    if captured:
        if capturedSquare:
            piecePositions[captured] &= ~(1 << (capturedSquare[0] * 8 + capturedSquare[1]))
            setPiece(capturedSquare[0], capturedSquare[1], "")
        else:
            piecePositions[captured] &= ~(1 << (end[0] * 8 + end[1]))
            setPiece(end[0], end[1], "")

    piecePositions[piece] &= ~(1 << (start[0] * 8 + start[1]))
    piecePositions[piece] |= 1 << (end[0] * 8 + end[1])
    setPiece(start[0], start[1], "")
    setPiece(end[0], end[1], piece)

    if piece in ("wK", "bK"): moveCastleRook(piece, start, end)

def undoMove(piece, start, end, captured, capturedSquare=None):
    from engine import visuals
    piecePositions[piece] &= ~(1 << (end[0] * 8 + end[1]))
    piecePositions[piece] |= (1 << (start[0] * 8 + start[1]))

    if captured:
        if capturedSquare:
            piecePositions[captured] |= 1 << (capturedSquare[0] * 8 + capturedSquare[1])
            setPiece(capturedSquare[0], capturedSquare[1], captured)
        else:
            piecePositions[captured] |= (1 << (end[0] * 8 + end[1]))
            setPiece(end[0], end[1], captured)

    setPiece(start[0], start[1], piece)
    if not captured or (captured and capturedSquare):
        setPiece(end[0], end[1], "" if captured and capturedSquare else (captured or ""))

    if piece in ("wK", "bK"): moveCastleRook(piece, start, end, undo=True)
    visuals.redraw = True

def makeMove(startRow, startColumn, endRow, endColumn, sound=True, simulation=False):
    global turnColour, enPassantTarget, moves, halfmoveClock
    from engine import visuals
    
    movingPiece = getPiece(startRow, startColumn)
    target = getPiece(endRow, endColumn)
    targetPos = 1 << (endRow * 8 + endColumn)
    start, end = (startRow, startColumn), (endRow, endColumn)

    moveCastleRook(movingPiece, start, end)
    
    if movingPiece == "wK": castleRights["wK"] = castleRights["wKl"] = castleRights["wKr"] = False
    elif movingPiece == "bK": castleRights["bK"] = castleRights["bKl"] = castleRights["bKr"] = False
    elif movingPiece == "wR":
        if start == (7, 0): castleRights["wKl"] = False
        elif start == (7, 7): castleRights["wKr"] = False
    elif movingPiece == "bR":
        if start == (0, 0): castleRights["bKl"] = False
        elif start == (0, 7): castleRights["bKr"] = False

    if target == "wR":
        if end == (7, 0): castleRights["wKl"] = False
        elif end == (7, 7): castleRights["wKr"] = False
    elif target == "bR":
        if end == (0, 0): castleRights["bKl"] = False
        elif end == (0, 7): castleRights["bKr"] = False

    visuals.possibleMoves.clear()
    moveHistory.append({
        "piece": movingPiece, "start": start, "end": end, "capturedPiece": target, 
        "capturedSquare": None, "enPassantBefore": enPassantTarget, "turnColour": turnColour, 
        "moves": moves, "halfmoveClockBefore": halfmoveClock, "halfmoveClockAfter": None, 
        "castleRightsBefore": castleRights.copy(), "promotion": None
    })
    
    if not simulation: redoHistory.clear()

    enPassantCapture = False
    if movingPiece[-1] == "P" and target == "" and startColumn != endColumn and enPassantTarget == (endRow, endColumn):
        capturedRow = endRow - (-1 if movingPiece[0] == "w" else 1)
        capturedPiece = getPiece(capturedRow, endColumn)
        if capturedPiece != "":
            piecePositions[capturedPiece] &= ~(1 << (capturedRow * 8 + endColumn))
            setPiece(capturedRow, endColumn, "")
            moveHistory[-1]["capturedPiece"] = capturedPiece
            moveHistory[-1]["capturedSquare"] = (capturedRow, endColumn)
            enPassantCapture = True
            if sound: sounds["capture"].play()

    if not enPassantCapture:
        if target != "":
            piecePositions[target] &= ~targetPos
            setPiece(endRow, endColumn, "")
            if sound: sounds["capture"].play()
        else:
            if sound: sounds["move"].play()

    piecePositions[movingPiece] &= ~(1 << (startRow * 8 + startColumn))
    piecePositions[movingPiece] |= targetPos
    setPiece(startRow, startColumn, "")
    setPiece(endRow, endColumn, movingPiece)

    if isPromotable(movingPiece, endRow) and not simulation:
        promotedPiece = visuals.choosePromotion(turnColour)
        piecePositions[movingPiece] &= ~targetPos
        piecePositions[promotedPiece] |= targetPos
        setPiece(endRow, endColumn, promotedPiece)
        moveHistory[-1]["promotion"] = promotedPiece
    
    moveHistory[-1]["castleRightsAfter"] = castleRights.copy()
    enPassantTarget = ((startRow + endRow) // 2, startColumn) if movingPiece[-1] == "P" and abs(endRow - startRow) == 2 else None
    moveHistory[-1]["enPassantAfter"] = enPassantTarget
    turnColour = "b" if turnColour == "w" else "w"    
    
    visuals.activeSquare = None
    updateSquareTable()
    moves += 1
    halfmoveClock = 0 if movingPiece[-1] == "P" or target != "" or enPassantCapture else halfmoveClock + 1
    moveHistory[-1]["halfmoveClockAfter"] = halfmoveClock
    positionHistory.append(hashBoard())
    
    visuals.activeOutline = None
    visuals.moveIndicator.clear()
    visuals.possibleMoves.clear()
    visuals.redraw = True

def gameState(sound=True):
    global gameOverMessage
    from engine import visuals
    
    if positionHistory.count(hashBoard()) >= 3:
        gameOverMessage = "Three-fold \nRepetition!\nNobody  wins!"
        if sound: sounds["checkmate"].play()
        return

    inCheck = kingCheck(turnColour)
    if not legalMoves(turnColour):
        if inCheck:
            winner = "Black" if turnColour == "w" else "White"
            gameOverMessage = f"Checkmate!\n{winner}  wins!"
            if sound: sounds["checkmate"].play()
        else:
            gameOverMessage = "Stalemate!\nNobody  wins!"
            if sound: sounds["checkmate"].play()
    elif inCheck and sound: sounds["check"].play()
    elif halfmoveClock >= 100:
        gameOverMessage = "50-move rule\nDraw!"
        if sound: sounds["checkmate"].play()
    elif insufficientMat():
        gameOverMessage = "Insufficient  Material! \n Nobody  wins"
        if sound: sounds["checkmate"].play()
    else: gameOverMessage = None

def previousMove(sound=True, simulation=False):
    global turnColour, moves, halfmoveClock, enPassantTarget
    from engine import visuals
    if not moveHistory: return

    p = moveHistory.pop()
    if not simulation: redoHistory.append(p)
    if positionHistory: positionHistory.pop()

    turnColour, moves, halfmoveClock = p["turnColour"], p["moves"], p.get("halfmoveClockBefore", 0)
    castleRights.clear()
    castleRights.update(p["castleRightsBefore"])
    enPassantTarget = p.get("enPassantBefore", None)

    startPos, endPos = 1 << (p["start"][0] * 8 + p["start"][1]), 1 << (p["end"][0] * 8 + p["end"][1])
    setPiece(p["end"][0], p["end"][1], "")
    setPiece(p["start"][0], p["start"][1], p["piece"])

    if p["promotion"] is not None:
        piecePositions[p["promotion"]] &= ~endPos
        piecePositions[p["piece"]] |= startPos
    else:
        piecePositions[p["piece"]] &= ~endPos
        piecePositions[p["piece"]] |= startPos
        
    if p["capturedPiece"] != "":
        if p.get("capturedSquare"):
            piecePositions[p["capturedPiece"]] |= 1 << (p["capturedSquare"][0] * 8 + p["capturedSquare"][1])
            setPiece(p["capturedSquare"][0], p["capturedSquare"][1], p["capturedPiece"])
        else:
            piecePositions[p["capturedPiece"]] |= endPos
            setPiece(p["end"][0], p["end"][1], p["capturedPiece"])
        if sound: sounds["capture"].play()
    else:
        if sound: sounds["move"].play()

    moveCastleRook(p["piece"], p["start"], p["end"], undo=True)
    updateSquareTable()
    visuals.activeSquare = visuals.activeOutline = None
    visuals.possibleMoves.clear()
    visuals.moveIndicator.clear()
    visuals.lines.clear()
    visuals.strategyCircles.clear()

    if not simulation:
        gameState(sound)
        visuals.redraw = True

def redoMove():
    global turnColour, moves, halfmoveClock, enPassantTarget
    from engine import visuals
    if not redoHistory: return

    m = redoHistory.pop()
    turnColour = "b" if m["turnColour"] == "w" else "w"
    moves = m["moves"] + 1
    halfmoveClock = m.get("halfmoveClockAfter", 0)
    castleRights.clear()
    castleRights.update(m["castleRightsAfter"])
    enPassantTarget = m.get("enPassantAfter", None)

    startPos, endPos = 1 << (m["start"][0] * 8 + m["start"][1]), 1 << (m["end"][0] * 8 + m["end"][1])

    if m["capturedPiece"] != "":
        if m.get("capturedSquare"):
            piecePositions[m["capturedPiece"]] &= ~(1 << (m["capturedSquare"][0] * 8 + m["capturedSquare"][1]))
            setPiece(m["capturedSquare"][0], m["capturedSquare"][1], "")
        else:
            piecePositions[m["capturedPiece"]] &= ~endPos
            setPiece(m["end"][0], m["end"][1], "")
        sounds["capture"].play()
    else: sounds["move"].play()

    moveCastleRook(m["piece"], m["start"], m["end"])

    if m["promotion"] is not None:
        piecePositions[m["piece"]] &= ~startPos
        piecePositions[m["promotion"]] |= endPos
        setPiece(m["start"][0], m["start"][1], "")
        setPiece(m["end"][0], m["end"][1], m["promotion"])
    else:    
        piecePositions[m["piece"]] &= ~startPos
        piecePositions[m["piece"]] |= endPos
        setPiece(m["start"][0], m["start"][1], "")
        setPiece(m["end"][0], m["end"][1], m["piece"])

    moveHistory.append(m)
    updateSquareTable()
    positionHistory.append(hashBoard())

    visuals.activeSquare = visuals.activeOutline = None
    visuals.possibleMoves.clear()
    visuals.moveIndicator.clear()
    visuals.lines.clear()
    visuals.strategyCircles.clear()
    
    gameState()
    visuals.redraw = True