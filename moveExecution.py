import updateBoard
import moveGeneration

def isPromotable(piece, row):
    return (piece == "wP" and row == 0) or (piece == "bP" and row == 7)

def insufficientMat():
    if (updateBoard.piecePositions["bP"] or updateBoard.piecePositions["bR"] or updateBoard.piecePositions["bQ"] or 
        updateBoard.piecePositions["wP"] or updateBoard.piecePositions["wR"] or updateBoard.piecePositions["wQ"]): 
        return False
    totKnights = updateBoard.piecePositions["bH"] | updateBoard.piecePositions["wH"]
    totBishops = updateBoard.piecePositions["bB"] | updateBoard.piecePositions["wB"]
    return (totBishops == 0 and totKnights == 0)

def moveCastleRook(piece, start, end, undo=False):
    if piece not in ("wK", "bK"):
        return

    row = 7 if piece == "wK" else 0

    if start == (row, 4) and end == (row, 6):
        rookStart, rookEnd = ((row, 5), (row, 7)) if undo else ((row, 7), (row, 5))
    elif start == (row, 4) and end == (row, 2):
        rookStart, rookEnd = ((row, 3), (row, 0)) if undo else ((row, 0), (row, 3))
    else:
        return

    startBit = 1 << (rookStart[0] * 8 + rookStart[1])
    endBit = 1 << (rookEnd[0] * 8 + rookEnd[1])
    updateBoard.piecePositions[piece[0] + "R"] &= ~startBit
    updateBoard.piecePositions[piece[0] + "R"] |= endBit
    updateBoard.setPiece(rookStart[0], rookStart[1], "")
    updateBoard.setPiece(rookEnd[0], rookEnd[1], piece[0] + "R")

def simulateMove(piece, start, end, captured, capturedSquare=None):
    startBit = 1 << (start[0] * 8 + start[1])
    endBit = 1 << (end[0] * 8 + end[1])

    if captured:
        if capturedSquare:
            capIndex = capturedSquare[0] * 8 + capturedSquare[1]
            updateBoard.piecePositions[captured] &= ~(1 << capIndex)
            updateBoard.setPiece(capturedSquare[0], capturedSquare[1], "")
        else:
            updateBoard.piecePositions[captured] &= ~endBit
            updateBoard.setPiece(end[0], end[1], "")

    updateBoard.piecePositions[piece] &= ~startBit
    updateBoard.piecePositions[piece] |= endBit
    updateBoard.setPiece(start[0], start[1], "")
    updateBoard.setPiece(end[0], end[1], piece)

    if piece in ("wK", "bK"):
        moveCastleRook(piece, start, end)

def undoMove(piece, start, end, captured, capturedSquare=None):
    import gui
    startBit = 1 << (start[0] * 8 + start[1])
    endBit = 1 << (end[0] * 8 + end[1])

    updateBoard.piecePositions[piece] &= ~endBit
    updateBoard.piecePositions[piece] |= startBit

    if captured:
        if capturedSquare:
            capIndex = capturedSquare[0] * 8 + capturedSquare[1]
            updateBoard.piecePositions[captured] |= 1 << capIndex
            updateBoard.setPiece(capturedSquare[0], capturedSquare[1], captured)
        else:
            updateBoard.piecePositions[captured] |= endBit
            updateBoard.setPiece(end[0], end[1], captured)

    updateBoard.setPiece(start[0], start[1], piece)
    if not captured or (captured and capturedSquare):
        updateBoard.setPiece(end[0], end[1], "" if captured and capturedSquare else (captured or ""))

    if piece in ("wK", "bK"):
        moveCastleRook(piece, start, end, undo=True)

    gui.redraw = True

def saveMove(piece, startRow, startColumn, endRow, endColumn, capturedPiece, turnColour, moves, halfmoveClockBefore):
    state = {
        "piece": piece,
        "start": (startRow, startColumn),
        "end": (endRow, endColumn),
        "capturedPiece": capturedPiece,
        "capturedSquare": None,
        "enPassantBefore": updateBoard.enPassantTarget,
        "turnColour": turnColour,
        "moves": moves,
        "halfmoveClockBefore": halfmoveClockBefore,
        "halfmoveClockAfter": None,
        "castleRightsBefore": updateBoard.castleRights.copy(),
        "promotion": None
    }
    updateBoard.moveHistory.append(state)

def makeMove(startRow, startColumn, endRow, endColumn, sound=True, simulation=False):
    import gui

    movingPiece = updateBoard.getPiece(startRow, startColumn)
    target = updateBoard.getPiece(endRow, endColumn)
    targetPos = 1 << (endRow * 8 + endColumn)

    moveCastleRook(movingPiece, (startRow, startColumn), (endRow, endColumn))
    start = (startRow, startColumn)
    end = (endRow, endColumn)
    
    if movingPiece == "wK":
        updateBoard.castleRights["wK"] = updateBoard.castleRights["wKl"] = updateBoard.castleRights["wKr"] = False
    elif movingPiece == "bK":
        updateBoard.castleRights["bK"] = updateBoard.castleRights["bKl"] = updateBoard.castleRights["bKr"] = False
    elif movingPiece == "wR":
        if start == (7, 0): updateBoard.castleRights["wKl"] = False
        elif start == (7, 7): updateBoard.castleRights["wKr"] = False
    elif movingPiece == "bR":
        if start == (0, 0): updateBoard.castleRights["bKl"] = False
        elif start == (0, 7): updateBoard.castleRights["bKr"] = False

    if target == "wR":
        if end == (7, 0): updateBoard.castleRights["wKl"] = False
        elif end == (7, 7): updateBoard.castleRights["wKr"] = False
    elif target == "bR":
        if end == (0, 0): updateBoard.castleRights["bKl"] = False
        elif end == (0, 7): updateBoard.castleRights["bKr"] = False

    gui.possibleMoves.clear()
    saveMove(movingPiece, startRow, startColumn, endRow, endColumn, target, updateBoard.turnColour, updateBoard.moves, updateBoard.halfmoveClock)
    if not simulation:
        updateBoard.redoHistory.clear()

    enPassantCapture = False
    if movingPiece[-1] == "P":
        direction = -1 if movingPiece[0] == "w" else 1
        if target == "" and startColumn != endColumn and updateBoard.enPassantTarget == (endRow, endColumn):
            capturedRow, capturedCol = endRow - direction, endColumn
            capturedPiece = updateBoard.getPiece(capturedRow, capturedCol)
            if capturedPiece != "":
                capPos = 1 << (capturedRow * 8 + capturedCol)
                updateBoard.piecePositions[capturedPiece] &= ~capPos
                updateBoard.setPiece(capturedRow, capturedCol, "")
                updateBoard.moveHistory[-1]["capturedPiece"] = capturedPiece
                updateBoard.moveHistory[-1]["capturedSquare"] = (capturedRow, capturedCol)
                enPassantCapture = True
                if sound:
                    gui.sounds["capture"].play()

    if not enPassantCapture:
        if target != "":
            updateBoard.piecePositions[target] &= ~targetPos
            updateBoard.setPiece(endRow, endColumn, "")
            if sound:
                gui.sounds["capture"].play()
        else:
            if sound:
                gui.sounds["move"].play()

    updateBoard.piecePositions[movingPiece] &= ~(1 << (startRow * 8 + startColumn))
    updateBoard.piecePositions[movingPiece] |= targetPos
    updateBoard.setPiece(startRow, startColumn, "")
    updateBoard.setPiece(endRow, endColumn, movingPiece)

    if isPromotable(movingPiece, endRow) and not simulation:
        promotedPiece = gui.choosePromotion(updateBoard.turnColour)
        updateBoard.piecePositions[movingPiece] &= ~targetPos
        updateBoard.piecePositions[promotedPiece] |= targetPos
        updateBoard.setPiece(endRow, endColumn, promotedPiece)
        updateBoard.moveHistory[-1]["promotion"] = promotedPiece
    
    updateBoard.moveHistory[-1]["castleRightsAfter"] = updateBoard.castleRights.copy()
    if movingPiece[-1] == "P" and abs(endRow - startRow) == 2:
        updateBoard.enPassantTarget = ((startRow + endRow) // 2, startColumn)
    else:
        updateBoard.enPassantTarget = None
    updateBoard.moveHistory[-1]["enPassantAfter"] = updateBoard.enPassantTarget
    updateBoard.turnColour = "b" if updateBoard.turnColour == "w" else "w"    
    
    gui.activeSquare = None
    updateBoard.updateSquareTable()
    updateBoard.moves += 1
    if movingPiece[-1] == "P" or target != "" or enPassantCapture:
        updateBoard.halfmoveClock = 0
    else:
        updateBoard.halfmoveClock += 1
    updateBoard.moveHistory[-1]["halfmoveClockAfter"] = updateBoard.halfmoveClock

    newHash = updateBoard.hashBoard()
    updateBoard.positionHistory.append(newHash)
    
    gui.activeOutline = None
    gui.moveIndicator.clear()
    gui.possibleMoves.clear()
    gui.redraw = True

def gameState(sound=True):
    import gui

    currentHash = updateBoard.hashBoard()
    if updateBoard.positionHistory.count(currentHash) >= 3:
        updateBoard.gameOverMessage = "Three-fold \nRepetition!\nNobody  wins!"
        if sound:
            gui.sounds["checkmate"].play()
        return

    inCheck = moveGeneration.kingCheck(updateBoard.turnColour)

    if not moveGeneration.legalMoves(updateBoard.turnColour):
        if inCheck:
            winner = "Black" if updateBoard.turnColour == "w" else "White"
            updateBoard.gameOverMessage = f"Checkmate!\n{winner}  wins!"
            if sound:
                gui.sounds["checkmate"].play()
        else:
            updateBoard.gameOverMessage = "Stalemate!\nNobody  wins!"
            if sound:
                gui.sounds["checkmate"].play()
    elif inCheck and sound:
        gui.sounds["check"].play()
    elif updateBoard.halfmoveClock >= 100:
        updateBoard.gameOverMessage = "50-move rule\nDraw!"
        if sound:
            gui.sounds["checkmate"].play()
    elif insufficientMat():
        updateBoard.gameOverMessage = "Insufficient  Material! \n Nobody  wins"
        if sound:
            gui.sounds["checkmate"].play()
    else:
        updateBoard.gameOverMessage = None

def previousMove(sound=True, simulation=False):
    import gui
    if len(updateBoard.moveHistory) == 0:
        return

    previousPos = updateBoard.moveHistory.pop()
    if not simulation:
        updateBoard.redoHistory.append(previousPos)
    if updateBoard.positionHistory:
        updateBoard.positionHistory.pop()

    piece = previousPos["piece"]
    start = previousPos["start"]
    end = previousPos["end"]
    capturedPiece = previousPos["capturedPiece"]
    updateBoard.turnColour = previousPos["turnColour"]
    updateBoard.moves = previousPos["moves"]
    updateBoard.halfmoveClock = previousPos.get("halfmoveClockBefore", 0)
    startPos = 1 << (start[0] * 8 + start[1])
    endPos = 1 << (end[0] * 8 + end[1])
    updateBoard.castleRights.clear()
    updateBoard.castleRights.update(previousPos["castleRightsBefore"])
    updateBoard.enPassantTarget = previousPos.get("enPassantBefore", None)

    updateBoard.setPiece(end[0], end[1], "")
    updateBoard.setPiece(start[0], start[1], piece)

    if previousPos["promotion"] is not None:
        promoted = previousPos["promotion"]
        updateBoard.piecePositions[promoted] &= ~endPos
        updateBoard.piecePositions[piece] |= startPos
        updateBoard.setPiece(end[0], end[1], "")
        updateBoard.setPiece(start[0], start[1], piece)
    else:
        updateBoard.piecePositions[piece] &= ~endPos
        updateBoard.piecePositions[piece] |= startPos
        
    if capturedPiece != "":
        capSquare = previousPos.get("capturedSquare")
        if capSquare:
            capPos = 1 << (capSquare[0] * 8 + capSquare[1])
            updateBoard.piecePositions[capturedPiece] |= capPos
            updateBoard.setPiece(capSquare[0], capSquare[1], capturedPiece)
        else:
            updateBoard.piecePositions[capturedPiece] |= endPos
            updateBoard.setPiece(end[0], end[1], capturedPiece)

        if sound:
            gui.sounds["capture"].play()
    else:
        if sound:
            gui.sounds["move"].play()

    moveCastleRook(piece, start, end, undo=True)
    updateBoard.updateSquareTable()

    gui.activeSquare = None
    gui.activeOutline = None
    gui.possibleMoves.clear()
    gui.moveIndicator.clear()
    gui.lines.clear()
    gui.strategyCircles.clear()

    if not simulation:
        gameState(sound)
        gui.redraw = True

def redoMove():
    import gui
    if len(updateBoard.redoHistory) == 0:
        return

    m = updateBoard.redoHistory.pop()
    piece = m["piece"]
    start = m["start"]
    end = m["end"]
    capturedPiece = m["capturedPiece"]
    updateBoard.turnColour = "b" if m["turnColour"] == "w" else "w"
    updateBoard.moves = m["moves"] + 1
    updateBoard.halfmoveClock = m.get("halfmoveClockAfter", 0)
    updateBoard.castleRights.clear()
    updateBoard.castleRights.update(m["castleRightsAfter"])
    updateBoard.enPassantTarget = m.get("enPassantAfter", None)

    startPos = 1 << (start[0] * 8 + start[1])
    endPos = 1 << (end[0] * 8 + end[1])

    if capturedPiece != "":
        capSquare = m.get("capturedSquare")
        if capSquare:
            capPos = 1 << (capSquare[0] * 8 + capSquare[1])
            updateBoard.piecePositions[capturedPiece] &= ~capPos
            updateBoard.setPiece(capSquare[0], capSquare[1], "")
        else:
            updateBoard.piecePositions[capturedPiece] &= ~endPos
            updateBoard.setPiece(end[0], end[1], "")
        gui.sounds["capture"].play()
    else:
        gui.sounds["move"].play()

    moveCastleRook(piece, start, end)

    if m["promotion"] is not None:
        promoted = m["promotion"]
        updateBoard.piecePositions[piece] &= ~startPos
        updateBoard.piecePositions[promoted] |= endPos
        updateBoard.setPiece(start[0], start[1], "")
        updateBoard.setPiece(end[0], end[1], promoted)
    else:    
        updateBoard.piecePositions[piece] &= ~startPos
        updateBoard.piecePositions[piece] |= endPos
        updateBoard.setPiece(start[0], start[1], "")
        updateBoard.setPiece(end[0], end[1], piece)

    updateBoard.moveHistory.append(m)
    newHash = updateBoard.hashBoard()
    updateBoard.updateSquareTable()
    updateBoard.positionHistory.append(newHash)

    gui.activeSquare = None
    gui.activeOutline = None
    gui.possibleMoves.clear()
    gui.moveIndicator.clear()
    gui.lines.clear()
    gui.strategyCircles.clear()
    
    gameState()
    gui.redraw = True